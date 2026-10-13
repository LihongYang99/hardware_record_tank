#!/usr/bin/env python3
"""Calibrate Node 2's Atlas EZO-EC (K 10 probe) and EZO-pH from a Jetson terminal; the control page uses the same code.

Each step sends one command over MQTT (account pump-operator, payload cmd=EC:<command> / cmd=PH:<command>) and waits
for the node's own OPERATOR_DONE record. The firmware allows exactly the commands built here (AtlasParse.h
atlasOperatorCommand). Every change is a SPEC §41 calibration record in operator_event: UTC time, operator, sensor
(EC:/PH: prefix), calibration type and value (the command), standard (--note), and the pre/post response: the reading
in the standard just before, and the reading, Cal,? and K,? / Slope,? the EZO reports after it re-initialises.
"""
import argparse
import getpass
import math
import sqlite3
import time

from pump_ctl import DEVICES, ROOT, execute, fields, latest, operator_name, rows_after, wait_for

READING = {'ec': 'EC_uS_cm', 'ph': 'pH'}
# action -> (command, allowed value range or None). The K 10 probe range starts at 10 uS/cm (Atlas EZO-EC datasheet).
STEPS = {
    'ec': {'k10': ('K,10', None), 'dry': ('Cal,dry', None), 'low': ('Cal,low,{}', (10, 500000)),
           'high': ('Cal,high,{}', (10, 500000)), 'single': ('Cal,{}', (10, 500000)), 'clear': ('Cal,clear', None)},
    'ph': {'mid': ('Cal,mid,{}', (6.5, 7.5)), 'low': ('Cal,low,{}', (1, 6)), 'high': ('Cal,high,{}', (8, 13)),
           'clear': ('Cal,clear', None)},
}
QUERIES = {'ec': {'cal': 'Cal,?', 'k': 'K,?', 't': 'T,?'}, 'ph': {'cal': 'Cal,?', 'slope': 'Slope,?', 't': 'T,?'}}
POST = {'ec': ('Cal,?', 'K,?'), 'ph': ('Cal,?', 'Slope,?')}
# Order from the Atlas datasheets: EC K,10 -> Cal,dry -> low -> high (or dry -> single point); pH mid first, then low/high.
REFUSAL = {'K_NOT_10': '探头是 K10，先运行 k10 把电极常数设成 10。',
           'DRY_FIRST': '先做干校准 dry（探头擦干、放在空气中）。',
           'LOW_FIRST': '先做低点 low，再做高点 high。',
           'MID_FIRST': '先做中点 mid 7.00：中点必须第一个做，而且会清除其他点。',
           'NO_READING': '数据库里还没有这支探头的读数，先确认 Node 2 在线。'}


def command(device, action, value=None):
    """The whitelisted command for one step; ValueError for anything else."""
    if action not in STEPS[device]:
        raise ValueError('Unknown step')
    template, limits = STEPS[device][action]
    if limits is None:
        if value not in (None, ''):
            raise ValueError('This step takes no value')
        return template
    number = float(value)
    if isinstance(value, bool) or not math.isfinite(number) or not limits[0] <= number <= limits[1]:
        raise ValueError(f'Value must be between {limits[0]} and {limits[1]}')
    text = f'{number:.2f}'
    return template.format(text if device == 'ph' else text.rstrip('0').rstrip('.'))


def state(db, d):
    """Last reading the node reported for this sensor, with the K and Cal,? it was labelled with."""
    row_id, line = latest(db, f'% sensor={d["sensor_id"]} %COMM=OK%', d['node_id'])
    f = fields(line) if line else {}
    return {'id': row_id, 'reading': f.get(READING[d['id']]), 'calibration_reply': f.get('calibration_reply'), 'K': f.get('K')}


def last_change(db, d):
    """The last K / calibration command this EZO accepted, e.g. 'Cal,dry'."""
    for cmd, line in db.execute('SELECT command, result_line FROM operator_event WHERE node_id=? AND command LIKE ? ORDER BY id DESC',
                                (d['node_id'], d['prefix'] + ':%')):
        cmd = cmd.split(':', 1)[1]
        if '?' not in cmd and fields(line or '').get('result') == 'OK':
            return cmd
    return None


def refusal(db, d, action):
    """Why this step is out of order, or None."""
    now = state(db, d)
    if d['id'] == 'ec' and action in ('dry', 'low', 'high', 'single'):
        if now['K'] is None:
            return 'NO_READING'
        if abs(float(now['K']) - 10) > 1e-4:
            return 'K_NOT_10'
        need = {'low': ('Cal,dry', 'Cal,low,'), 'single': ('Cal,dry',), 'high': ('Cal,low,', 'Cal,high,')}.get(action)
        if need and not (last_change(db, d) or '').startswith(need):
            return 'DRY_FIRST' if action != 'high' else 'LOW_FIRST'
    if d['id'] == 'ph' and action in ('low', 'high'):
        if now['calibration_reply'] is None:
            return 'NO_READING'
        if now['calibration_reply'].upper() == '?CAL,0':
            return 'MID_FIRST'
    return None


def wait_reading(db, d, after, timeout=10):
    """First reading stored after row id `after`."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rows = rows_after(db, after, f'% sensor={d["sensor_id"]} %COMM=OK%', d['node_id'])
        if rows:
            return fields(rows[0][1]).get(READING[d['id']])
        time.sleep(0.3)
    return None


def run(db, conn, device, action, cmd, operator, note, timeout=20):
    """Send one step. A K / calibration change waits for the node to re-read the EZO, asks for the new state and
    stores pre/post in that command's operator_event note. Returns the result dict shown to the operator."""
    d = dict(DEVICES[device], id=device)
    query = '?' in cmd
    if not query:
        why = refusal(db, d, action)
        if why:
            return {'result': why}
    pre = state(db, d)
    cmd_id, done_id, f = execute(db, conn, f'{d["prefix"]}:{cmd}', operator, note, timeout, d['node_id'], d['topic'])
    if not f:
        return {'result': 'NO_REPLY'}
    out = {'result': f.get('result'), 'reply': f.get('reply')}
    if query or out['result'] != 'OK':
        return out
    ready_id, _ = wait_for(db, done_id, f'% sensor={d["sensor_id"]} %', ('READY',), 15, d['node_id'])
    post = {}
    if ready_id:
        for q in POST[device]:
            r = execute(db, conn, f'{d["prefix"]}:{q}', operator, f'post-check of {cmd}', timeout, d['node_id'], d['topic'])[2]
            post[q] = r.get('reply') if r and r.get('result') == 'OK' else None
        post['reading'] = wait_reading(db, d, ready_id)
    label = READING[device]
    record = (f'{note} | pre: {label}={pre["reading"]} cal={pre["calibration_reply"]}' + (f' K={pre["K"]}' if device == 'ec' else '')
              + ' | post: ' + (' '.join(f'{k}={v}' for k, v in post.items()) if ready_id else 'NO_READY_AFTER_CHANGE'))
    with db:
        db.execute('UPDATE operator_event SET note=? WHERE cmd_id=?', (record, cmd_id))
    out.update(pre=pre['reading'], post=post)
    return out


def show(db, device, n=15):
    """Latest reading, its labels, and how much the last n readings (4 s apart, about one minute) moved."""
    d = dict(DEVICES[device], id=device)
    rows = db.execute('SELECT received_utc, line FROM raw_log WHERE node_id=? AND line LIKE ? ORDER BY id DESC LIMIT ?',
                      (d['node_id'], f'% sensor={d["sensor_id"]} %COMM=OK%', n)).fetchall()
    if not rows:
        print(f'还没有 {d["name"]} 的读数。')
        return
    values = [float(fields(line)[READING[device]]) for _, line in rows if READING[device] in fields(line)]
    f = fields(rows[0][1])
    spread = max(values) - min(values)
    relative = f'（{100 * spread / abs(sum(values) / len(values)):.1f}%）' if device == 'ec' and any(values) else ''
    print(f'{rows[0][0]}  {d["name"]} = {values[0]}  校准 {f.get("calibration_reply")}' + (f'  K={f.get("K")}' if device == 'ec' else '')
          + f'  最近 {len(values)} 个读数波动 {spread:.3g}{relative}  QC={f.get("QC")}')


def main():
    parser = argparse.ArgumentParser(description='校准 Node 2 的 EC（K10）和 pH。顺序：EC = k10 → dry → low → high；pH = mid → low → high。')
    parser.add_argument('sensor', choices=STEPS)
    parser.add_argument('action', help='show | watch | query <cal|k|slope|t> | EC: k10 dry low high single clear | pH: mid low high clear')
    parser.add_argument('value', nargs='?', help='校准点数值：EC 用 µS/cm（如 12880），pH 用 pH（如 7.00）；query 时写查询项')
    parser.add_argument('--note', default='', help='必填（改设置/校准时）：标准液名称、批号、液温，例如 "Atlas 12,880 µS/cm lot 123, 22.4 °C"')
    parser.add_argument('--operator', default=getpass.getuser())
    parser.add_argument('--db', default=str(ROOT / 'data/measurements.sqlite3'))
    parser.add_argument('--credentials', default=str(ROOT / 'data/mqtt/credentials.json'))
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=1883)
    parser.add_argument('--timeout', type=float, default=20)
    args = parser.parse_args()
    db = sqlite3.connect(args.db, timeout=15)
    if args.action in ('show', 'watch'):
        while True:
            show(db, args.sensor)
            if args.action == 'show':
                return
            time.sleep(4)
    try:
        cmd = QUERIES[args.sensor][args.value] if args.action == 'query' else command(args.sensor, args.action, args.value)
    except (KeyError, ValueError, TypeError) as error:
        raise SystemExit(f'不接受这个步骤：{error}。可用：{", ".join(STEPS[args.sensor])}；查询：{", ".join(QUERIES[args.sensor])}')
    if '?' not in cmd and not args.note.strip():
        raise SystemExit('改设置或校准必须用 --note 写明标准液、批号和液温（SPEC §41 校准记录）。')
    print(f'发送 {args.sensor.upper()}:{cmd}，等待 Node 2 回复…（校准步骤约 15 秒：节点会重新读取 K 和校准状态）')
    try:
        out = run(db, args, args.sensor, args.action, cmd, operator_name(args.operator), args.note.strip(), args.timeout)
    except (OSError, ConnectionError):
        raise SystemExit('命令没能发到 MQTT broker（run_mqtt.py 在运行吗？）。')
    result = out['result']
    meaning = {'OK': 'EZO 已接受', 'ER': 'EZO 拒绝了这条命令', 'NO_REPLY': '节点没有回复：可能离线，先用 show 确认',
               'SENSOR_NOT_READY': '这支探头还没初始化好，稍后再试', 'ANOTHER_COMMAND_PENDING': '上一条命令还没完成',
               'NOT_ALLOWED': '固件不接受这条命令', 'DUPLICATE_ID': '重复编号，已忽略'}
    print(f'结果：{result}（{REFUSAL.get(result) or meaning.get(result, "见日志")}）  回复：{out.get("reply")}')
    if 'post' in out:
        print(f'校准前读数 {out["pre"]} → 之后：' + '  '.join(f'{k} {v}' for k, v in out['post'].items()))
    if result != 'OK':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
