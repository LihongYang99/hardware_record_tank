#!/usr/bin/env python3
"""Operator control of 泵 1 / pump 1 (pump-node-1, shrimp-node04) from a Jetson terminal, and the
login-protected device control page used by server.py --pump-control.

Each call sends one whitelisted command over MQTT (account pump-operator) and waits for the node's
own OPERATOR_* record in SQLite, so what is printed is what the pump actually answered. The node uses
a clean MQTT session: a command sent while it is offline is dropped, never executed later.
"""
import argparse
import getpass
import hashlib
import hmac
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT.parents[1] / '.codex-build' / 'runtime'
if importlib.util.find_spec('paho') is None:
    sys.path.insert(0, str(RUNTIME / 'usr/lib/python3/dist-packages'))
import paho.mqtt.client as mqtt
from server import fields, utc

NODE = 'shrimp-node04'
TOPIC = f'shrimp/lab/{NODE}/cmd'
USERS_FILE = ROOT / 'data' / 'pump_web_users.json'
# Devices on the control page. A new controllable device needs its own node firmware whitelist, an ACL line
# for pump-operator on its cmd topic (prepare_mqtt.py COMMAND_NODES) and an entry here; node_id/sensor_id
# tie the page to the stored data. Only the 'pump' kind exists so far.
DEVICES = {
    'pump1': {'name': '泵 1', 'name_en': 'Pump 1', 'kind': 'pump',
              'description': '旁路蠕动泵 · Atlas EZO-PMP · 泵节点 1（总 Node 4）',
              'description_en': 'Bypass peristaltic pump · Atlas EZO-PMP · pump node 1 (overall Node 4)',
              'node_id': NODE, 'sensor_id': 'PUMP_ATLAS_PMP', 'topic': TOPIC},
}
QUERIES = {'state': 'D,?', 'maxrate': 'DC,?', 'cal': 'Cal,?', 'volume': 'TV,?', 'voltage': 'PV,?', 'status': 'Status'}


def amount(low, high):
    def parse(text):
        value = float(text)
        if not math.isfinite(value) or not low <= value <= high:
            raise argparse.ArgumentTypeError(f'必须在 {low} 到 {high} 之间')
        return f'{value:.2f}'
    return parse


def pump_command(args):
    """The same whitelist the firmware enforces; anything else never leaves this script."""
    return {'start': lambda: f'DC,{args.rate},*', 'stop': lambda: 'X',
            'dispense': lambda: f'D,{args.ml}' + (f',{args.minutes}' if args.minutes else ''),
            'calibrate': lambda: f'Cal,{args.ml}', 'cal-clear': lambda: 'Cal,clear',
            'query': lambda: QUERIES[args.what]}[args.action]()


def operator_name(name):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name)[:24] or 'unknown'


def rows_after(db, after, pattern, node=NODE):
    return db.execute('SELECT id, line FROM raw_log WHERE node_id=? AND id>? AND line LIKE ? ORDER BY id',
                      (node, after, pattern)).fetchall()


def wait_for(db, after, pattern, events, timeout, node=NODE):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for row_id, line in rows_after(db, after, pattern, node):
            if any(f'event={e} ' in line for e in events):
                return row_id, line
        time.sleep(0.3)
    return None, None


def latest(db, pattern, node=NODE):
    row = db.execute('SELECT id, line FROM raw_log WHERE node_id=? AND line LIKE ? ORDER BY id DESC LIMIT 1',
                     (node, pattern)).fetchone()
    return row or (0, None)


def last_dispense(db):
    """Cal,<mL> only means something right after a completed dispense of the same pump power-up."""
    done_id, done = latest(db, '%event=OPERATOR_DONE %')
    if not done or not fields(done).get('command', '').startswith('D,') or fields(done).get('result') != 'OK':
        return None
    finished = rows_after(db, done_id, '%event=DISPENSE_DONE %')
    reset = rows_after(db, done_id, '%event=BOOT %') + rows_after(db, done_id, '%event=PUMP_RESET %') + rows_after(db, done_id, '%event=PUMP_BOOT_READY %')
    if not finished or (reset and min(r[0] for r in reset) < finished[0][0]):
        return None
    return fields(done)['command']


def show(db):
    _, line = latest(db, '% pump_on=%')
    _, ready = latest(db, '%event=READY %')
    if not line:
        print('数据库里还没有泵 1 的状态记录。')
        return
    f = fields(line)
    state = {'1': '运行中（控制器报告）', '0': '已停止'}.get(f.get('pump_on'), f.get('COMM', '?'))
    print(f"泵 1：{state}  设定 {f.get('target_mL_min', '—')} mL/min  电机电压 {f.get('motor_V', '—')} V  "
          f"本次上电累计 {f.get('total_volume_mL', '—')} mL  QC={f.get('QC')}")
    if ready:
        r = fields(ready)
        print(f"校准状态 {r.get('calibration_reply')}  最大恒定流量 {r.get('max_rate_reply')}")


def publish(args, payload, topic=TOPIC):
    credentials = json.loads(Path(args.credentials).read_text())
    client = mqtt.Client(client_id=f'pump-operator-{time.time_ns()}', clean_session=True)
    client.username_pw_set('pump-operator', credentials['pump-operator'])
    client.connect(args.host, args.port, keepalive=20)
    client.loop_start()
    try:
        info = client.publish(topic, payload, qos=1, retain=False)
        deadline = time.monotonic() + 10
        while not info.is_published():
            if time.monotonic() > deadline:
                raise ConnectionError('MQTT broker did not confirm the publish')
            time.sleep(0.05)
    finally:
        client.disconnect()
        client.loop_stop()


def execute(db, conn, command, operator, note, timeout, node=NODE, topic=TOPIC):
    """Send one command and wait for the node's answer. Returns (cmd_id, done_row_id, reply fields or None)."""
    cmd_id = str(time.time_ns())
    before = db.execute('SELECT COALESCE(MAX(id), 0) FROM raw_log').fetchone()[0]
    with db:
        db.execute('CREATE TABLE IF NOT EXISTS operator_event(id INTEGER PRIMARY KEY, sent_utc TEXT NOT NULL, node_id TEXT NOT NULL, '
                   'cmd_id TEXT NOT NULL UNIQUE, operator TEXT NOT NULL, command TEXT NOT NULL, note TEXT, result_line TEXT)')
        db.execute('INSERT INTO operator_event(sent_utc,node_id,cmd_id,operator,command,note) VALUES(?,?,?,?,?,?)',
                   (utc(), node, cmd_id, operator, command, note))
    try:
        publish(conn, f'id={cmd_id} operator={operator} cmd={command}', topic)
    except (OSError, ConnectionError):
        with db:
            db.execute('UPDATE operator_event SET result_line=? WHERE cmd_id=?', ('BROKER_UNAVAILABLE', cmd_id))
        raise
    done_id, line = wait_for(db, before, f'%cmd_id={cmd_id} %', ('OPERATOR_DONE', 'OPERATOR_REJECTED'), timeout, node)
    with db:
        db.execute('UPDATE operator_event SET result_line=? WHERE cmd_id=?', (line or 'NO_REPLY', cmd_id))
    return cmd_id, done_id, fields(line) if line else None


def hash_password(password, salt, iterations):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations).hex()


def load_users(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def save_users(path, users):
    old = os.umask(0o077)
    try:
        Path(path).write_text(json.dumps(users))
    finally:
        os.umask(old)
    Path(path).chmod(0o600)


def add_user(path, name, password):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,20}', name) or len(password) < 8:
        raise ValueError('Account: 1-20 of A-Z a-z 0-9 _ . -; password at least 8 characters')
    salt = secrets.token_bytes(16)
    users = load_users(path)
    users[name] = {'salt': salt.hex(), 'iterations': 200000, 'hash': hash_password(password, salt, 200000)}
    save_users(path, users)


class WebControl:
    """Login-protected device control page; the monitoring page stays public and read-only.

    Accounts are salted PBKDF2 hashes (managed with `pump_ctl.py web-user`). Five wrong passwords lock
    that account name for 60 s. Sessions are random tokens kept in memory, sent as an HttpOnly,
    SameSite=Strict cookie, and expire after 30 minutes without use or when the account is removed.
    The page is plain HTTP on the lab LAN, the same exposure as the lab MQTT. One pump command at a time.
    """
    IDLE_S, LOCK_S, MAX_FAILURES = 1800, 60, 5

    def __init__(self, db_path, conn, users_file=USERS_FILE, timeout=20):
        self.db_path, self.conn, self.users_file, self.timeout = str(db_path), conn, Path(users_file), timeout
        self.lock, self.busy = threading.Lock(), threading.Lock()
        self.sessions, self.failures, self.max_rate = {}, {}, {}

    def status(self):
        enabled = bool(load_users(self.users_file))
        return {'enabled': enabled, 'reason': None if enabled else 'NO_USERS'}

    def devices(self):
        """Public description of each device, plus the pump's own reported maximum rate (cached 60 s)."""
        now, out = time.monotonic(), []
        for device_id, d in DEVICES.items():
            cached = self.max_rate.get(device_id, (0.0, None))
            if now - cached[0] > 60:
                value = None
                try:
                    with sqlite3.connect(f'file:{self.db_path}?mode=ro', uri=True, timeout=5) as db:
                        _, ready = latest(db, '%event=READY %', d['node_id'])
                    reply = fields(ready).get('max_rate_reply', '') if ready else ''
                    value = float(reply.split(',')[1]) if reply.upper().startswith('?MAXRATE,') else None
                except (sqlite3.Error, ValueError, IndexError):
                    pass
                cached = self.max_rate[device_id] = (now, value)
            out.append({'id': device_id, 'name': d['name'], 'name_en': d['name_en'], 'kind': d['kind'],
                        'description': d['description'], 'description_en': d['description_en'],
                        'node_id': d['node_id'], 'sensor_id': d['sensor_id'], 'max_rate_mL_min': cached[1]})
        return out

    def login(self, name, password):
        with self.lock:
            now = time.monotonic()
            count, until = self.failures.get(name, (0, 0.0))
            if now < until:
                return 'LOCKED', None
            users = load_users(self.users_file)
            if not users:
                return 'NO_USERS', None
            record = users.get(name) or next(iter(users.values()))  # same hashing cost for unknown names
            match = hmac.compare_digest(hash_password(password, bytes.fromhex(record['salt']), record['iterations']), record['hash'])
            if not (match and name in users):
                if len(self.failures) > 1000:
                    self.failures.clear()
                count += 1
                self.failures[name] = (0, now + self.LOCK_S) if count >= self.MAX_FAILURES else (count, 0.0)
                return 'WRONG', None
            self.failures.pop(name, None)
            token = secrets.token_urlsafe(32)
            self.sessions[token] = [name, now]
            return 'OK', token

    def user(self, token):
        with self.lock:
            session = self.sessions.get(token or '')
            if not session:
                return None
            now = time.monotonic()
            if now - session[1] > self.IDLE_S or session[0] not in load_users(self.users_file):
                self.sessions.pop(token, None)
                return None
            session[1] = now
            return session[0]

    def logout(self, token):
        with self.lock:
            self.sessions.pop(token or '', None)

    def events(self, limit=15):
        ids = {d['node_id']: device_id for device_id, d in DEVICES.items()}
        try:
            with sqlite3.connect(f'file:{self.db_path}?mode=ro', uri=True, timeout=5) as db:
                rows = db.execute('SELECT sent_utc, node_id, operator, command, result_line FROM operator_event ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        except sqlite3.Error:
            return []
        out = []
        for sent, node, operator, command, line in rows:
            f = fields(line or '')
            out.append({'sent_utc': sent, 'device_id': ids.get(node), 'node_id': node, 'operator': operator, 'command': command,
                        'result': f.get('result') or line or 'PENDING', 'reply': f.get('reply')})
        return out

    def kind(self, device_id):
        return DEVICES.get(device_id, {}).get('kind')

    def run(self, device_id, command, name):
        if not self.busy.acquire(blocking=False):
            return {'result': 'BUSY'}
        try:
            db = sqlite3.connect(self.db_path, timeout=15)
            try:
                d = DEVICES[device_id]
                reply = execute(db, self.conn, command, 'web-' + name, 'web control page', self.timeout, d['node_id'], d['topic'])[2]
            finally:
                db.close()
        except (OSError, ConnectionError, sqlite3.Error):
            return {'result': 'BROKER_UNAVAILABLE'}
        finally:
            self.busy.release()
        if not reply:
            return {'result': 'NO_REPLY'}
        return {'result': reply.get('result'), 'reply': reply.get('reply'), 'target_mL_min': reply.get('target_mL_min')}


def main():
    parser = argparse.ArgumentParser(description='控制泵 1（旁路泵，pump-node-1）。每次只发一条命令，并显示泵的实际回复。')
    parser.add_argument('--operator', default=getpass.getuser(), help='操作人（记入日志）')
    parser.add_argument('--note', default='', help='备注；校准时写明量具和水，例如 "10mL量筒 淡水 气泡已排"')
    parser.add_argument('--db', default=str(ROOT / 'data/measurements.sqlite3'))
    parser.add_argument('--credentials', default=str(ROOT / 'data/mqtt/credentials.json'))
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=1883)
    parser.add_argument('--timeout', type=float, default=20)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('show', help='显示最新状态（不发命令）')
    sub.add_parser('start', help='以恒定流量启动 DC,<rate>,*').add_argument('rate', type=amount(0.5, 105), help='mL/min')
    sub.add_parser('stop', help='停止 X')
    d = sub.add_parser('dispense', help='输送一定体积 D,<mL>[,<min>]（校准用）')
    d.add_argument('ml', type=amount(0.5, 1000))
    d.add_argument('--minutes', type=amount(0.01, 1440), help='在这么多分钟内输送完（按时间校准）')
    sub.add_parser('calibrate', help='写入实测体积 Cal,<mL>').add_argument('ml', type=amount(0.01, 1000), help='实际量到的 mL')
    sub.add_parser('cal-clear', help='清除校准 Cal,clear')
    sub.add_parser('query', help='只读查询').add_argument('what', choices=QUERIES)
    w = sub.add_parser('web-user', help='管理控制页 /control 的操作员账号（只存加盐哈希）')
    w.add_argument('op', choices=('add', 'remove', 'list'))
    w.add_argument('name', nargs='?', help='账号：1–20 位字母、数字、_ . -')
    args = parser.parse_args()

    if args.action == 'web-user':
        users = load_users(USERS_FILE)
        if args.op == 'list':
            print('\n'.join(sorted(users)) or '还没有账号。')
        elif not args.name:
            raise SystemExit('请写账号名，例如：web-user add lihongyang')
        elif args.op == 'remove':
            if users.pop(args.name, None) is None:
                raise SystemExit(f'没有账号 {args.name}。')
            save_users(USERS_FILE, users)
            print(f'已删除 {args.name}；该账号已登录的会话在下一次请求时失效。')
        else:
            password = getpass.getpass(f'{args.name} 的密码（至少 8 位，输入不显示）：')
            if password != getpass.getpass('再输入一次：'):
                raise SystemExit('两次不一致，未保存。')
            try:
                add_user(USERS_FILE, args.name, password)
            except ValueError as error:
                raise SystemExit(f'未保存：{error}')
            print(f'已保存 {args.name}（{USERS_FILE}，只含哈希）。控制页：http://192.168.88.249:8080/control（网页服务需带 --pump-control）')
        return
    db = sqlite3.connect(args.db, timeout=15)
    if args.action == 'show':
        show(db)
        return
    if args.action in ('calibrate', 'cal-clear') and not args.note.strip():
        raise SystemExit('校准必须用 --note 写明量具、用水和操作条件（SPEC §41 校准记录）。')
    command = pump_command(args)
    dispensed = last_dispense(db) if args.action == 'calibrate' else None
    if args.action == 'calibrate' and not dispensed:
        raise SystemExit('上一条操作不是已完成的 dispense，泵会拒绝校准。先接好 12 V，运行 dispense 10，'
                         '等泵停下（show 显示已停止）并量好体积，再 calibrate。')
    _, ready = latest(db, '%event=READY %')
    pre = fields(ready).get('calibration_reply') if ready else None
    print(f'发送 {command}，等待泵的回复…')
    try:
        cmd_id, done_id, f = execute(db, args, command, operator_name(args.operator), args.note, args.timeout)
    except (OSError, ConnectionError):
        raise SystemExit('命令没能发到 MQTT broker（run_mqtt.py 在运行吗？）。')
    if not f:
        raise SystemExit(f'{args.timeout:.0f} 秒内没有收到节点回复：节点可能离线。用 show 查看当前状态，不要重复发送前先确认。')
    note = args.note
    if args.action == 'calibrate' and f.get('result') == 'OK':
        _, after = wait_for(db, done_id, '%event=READY %', ('READY',), 15)
        post = fields(after) if after else {}
        note = f"{args.note} | dispensed={dispensed} pre={pre} post={post.get('calibration_reply')} max_rate={post.get('max_rate_reply')}"
        print(f"校准前 {pre} → 校准后 {post.get('calibration_reply')}，最大恒定流量 {post.get('max_rate_reply')}")
    with db:
        db.execute('UPDATE operator_event SET note=? WHERE cmd_id=?', (note, cmd_id))
    meaning = {'OK': '泵已接受', 'ER': '泵拒绝了这条命令', 'PUMP_NOT_READY': '泵还没初始化好，稍后再试',
               'ANOTHER_COMMAND_PENDING': '上一条命令还没完成', 'DUPLICATE_ID': '重复编号，已忽略'}
    result = f.get('result', '?')
    print(f"结果：{result}（{meaning.get(result, '见日志')}）  泵回复：{f.get('reply')}  当前设定 {f.get('target_mL_min')} mL/min")
    if result == 'ER' and f.get('reply', '').startswith('*UV,PUMPPWR'):
        print('提示：泵报告电机电源欠压，12 V 没接或没电。')
    if result == 'ER' and f.get('reply') == '*TOOFAST':
        print('提示：超过泵的最大恒定流量，先用 query maxrate 查上限。')
    time.sleep(4.5)  # one 4 s poll later, the state line reflects the command
    show(db)
    if result != 'OK':
        sys.exit(1)


if __name__ == '__main__':
    main()
