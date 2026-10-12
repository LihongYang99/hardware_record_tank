#!/usr/bin/env python3
"""Lab dashboard. Standard-library HTTP/SQLite; optional system GStreamer."""
import argparse
import csv
from contextlib import contextmanager
import io
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
NODES = {
    'shrimp-node01': {'name': 'Node 1 · DO / ORP', 'ip': '192.168.88.252', 'mac': '44:b1:76:ce:d1:a8'},
    'shrimp-node02': {'name': 'Node 2 · EC / pH', 'ip': '192.168.88.251', 'mac': '44:b1:76:cc:d4:84'},
    'shrimp-node04': {'name': 'Pump 1 · 泵 1', 'ip': '192.168.88.248', 'mac': '7c:4f:ad:b5:33:38'},
    'shrimp-node05': {'name': 'Pump 2 · 泵 2', 'ip': '192.168.88.247', 'mac': '7c:4f:ad:b5:1c:d4'},
    'shrimp-node06': {'name': 'Node 6 · 浊度', 'ip': '192.168.88.246', 'mac': '44:b1:76:ce:d8:6c'},
    'shrimp-node07': {'name': 'Node 7 · 加热器', 'ip': None, 'mac': None},
}
PUMP_PARAMETERS = [('pump_on', '运行状态', ''), ('target_mL_min', '设定流量', 'mL/min'),
                   ('motor_V', '电机电压', 'V'), ('total_volume_mL', '本次上电累计体积', 'mL')]
SENSORS = {
    'DO_SEN0681': ('shrimp-node01', 'DFRobot SEN0681', [('DO_mg_L', 'DO', 'mg/L'), ('saturation_pct', '饱和度', '%'), ('temperature_C', 'DO 温度', '°C')]),
    'ORP_SEN0709': ('shrimp-node01', 'DFRobot SEN0709', [('ORP_mV', 'ORP', 'mV'), ('temperature_C', 'ORP 温度', '°C')]),
    'EC_ATLAS_EZO': ('shrimp-node02', 'Atlas EZO-EC', [('EC_uS_cm', 'EC', 'µS/cm'), ('salinity_PSU', '盐度', 'PSU')]),
    'PH_ATLAS_EZO': ('shrimp-node02', 'Atlas EZO-pH', [('pH', 'pH', 'pH')]),
    # Turbidity is reported as NTU only; it is not eTSS until a site gravimetric calibration exists.
    # relay_on is the node's own GPIO/relay command state, not a measured heater current or water temperature.
    'HEATER_RELAY': ('shrimp-node07', 'IoT AC relay CH1', [('relay_on', '加热器继电器', '')]),
    'TURB_SEN0710': ('shrimp-node06', 'DFRobot SEN0710', [('turbidity_NTU', '浊度', 'NTU'), ('temperature_C', '浊度探头温度', '°C')]),
    # pump_on is the controller's own report (D,?), not proof of water flow.
    'PUMP_ATLAS_PMP': ('shrimp-node04', 'Atlas EZO-PMP', PUMP_PARAMETERS),
    'PUMP2_ATLAS_PMP': ('shrimp-node05', 'Atlas EZO-PMP', PUMP_PARAMETERS),
}


def utc(epoch=None):
    moment = datetime.now(timezone.utc) if epoch is None else datetime.fromtimestamp(epoch, timezone.utc)
    return moment.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


# Data recording switch per node (control page; setting key 'recording:<node>'). Rows received while a node's
# switch is off are deleted once older than RECENT_ONLY_S; rows received while it is on are kept.
# Without a stored setting a node records. The bare 'recording' key is the pre-per-node global switch.
RECENT_ONLY_S = 12 * 3600
KEEP = "COALESCE((SELECT value FROM setting WHERE key='recording:' || ?), (SELECT value FROM setting WHERE key='recording'), 1)"
OPERATOR_EVENT_DDL = ('CREATE TABLE IF NOT EXISTS operator_event(id INTEGER PRIMARY KEY, sent_utc TEXT NOT NULL, node_id TEXT NOT NULL, '
                      'cmd_id TEXT NOT NULL UNIQUE, operator TEXT NOT NULL, command TEXT NOT NULL, note TEXT, result_line TEXT)')


def fields(line):
    return dict(re.findall(r'(\w+)=([^\s]*)', line))


class Store:
    def __init__(self, path):
        self.path = str(path)
        # The receiver and the web server open the same file at start. BEGIN IMMEDIATE takes the write lock
        # before any read, so a second process waits (timeout) instead of failing with "database is locked"
        # while the first one migrates; the whole schema change is one transaction.
        db = sqlite3.connect(self.path, timeout=120, isolation_level=None)
        try:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS raw_log (
                    id INTEGER PRIMARY KEY, received_utc TEXT NOT NULL,
                    received_epoch REAL NOT NULL, node_id TEXT NOT NULL,
                    transport TEXT NOT NULL, line TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS measurement (
                    id INTEGER PRIMARY KEY, raw_id INTEGER NOT NULL,
                    received_utc TEXT NOT NULL, received_epoch REAL NOT NULL,
                    sample_timestamp_utc TEXT, clock_sync_status TEXT NOT NULL,
                    node_id TEXT NOT NULL, sensor_id TEXT NOT NULL, sensor_model TEXT NOT NULL,
                    boot_id TEXT NOT NULL, sequence_number INTEGER NOT NULL,
                    parameter TEXT NOT NULL, value REAL, unit TEXT NOT NULL,
                    qc_flag TEXT NOT NULL, metadata TEXT NOT NULL,
                    tank_id TEXT, experiment_id TEXT, location TEXT,
                    UNIQUE(node_id, sensor_id, boot_id, sequence_number, parameter));
                CREATE INDEX IF NOT EXISTS measurement_history ON measurement(sensor_id, parameter, id);
                CREATE TABLE IF NOT EXISTS issue (
                    id INTEGER PRIMARY KEY, received_utc TEXT NOT NULL, node_id TEXT NOT NULL,
                    sensor_id TEXT, kind TEXT NOT NULL, details TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
            ''')
            db.execute(OPERATOR_EVENT_DDL)
            for table in ('raw_log', 'issue'):
                if 'keep' not in [row[1] for row in db.execute(f'PRAGMA table_info({table})')]:
                    # Rows stored before the switch existed were all recorded on purpose: keep them.
                    db.execute(f'ALTER TABLE {table} ADD COLUMN keep INTEGER NOT NULL DEFAULT 1')
            db.execute('CREATE INDEX IF NOT EXISTS raw_log_purge ON raw_log(keep, received_epoch)')
            db.execute('CREATE INDEX IF NOT EXISTS measurement_raw ON measurement(raw_id)')
            db.execute('COMMIT')
        finally:
            db.close()  # an exception before COMMIT rolls the whole migration back

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def ingest(self, node, line, transport='local_bridge'):
        if node not in NODES or not isinstance(line, str) or len(line.encode('utf-8')) > 8192:
            raise ValueError('Invalid node or oversized line')
        f = fields(line)
        if f.get('node_id', node) != node:
            raise ValueError('Node identity mismatch')
        sensor = f.get('sensor')
        if sensor in SENSORS and SENSORS[sensor][0] != node:
            raise ValueError('Sensor identity mismatch')
        now, stamp = time.time(), utc()
        count = 0
        with self.connect() as db:
            raw_id = db.execute(f'INSERT INTO raw_log(received_utc,received_epoch,node_id,transport,line,keep) VALUES(?,?,?,?,?,{KEEP})',
                                (stamp, now, node, transport, line, node)).lastrowid
            issue = lambda kind, details: db.execute(
                f'INSERT INTO issue(received_utc,node_id,sensor_id,kind,details,keep) VALUES(?,?,?,?,?,{KEEP})', (stamp, node, sensor, kind, details, node))
            # Health, RX and TX lines remain raw records; only completed measurement reports are parsed.
            if sensor not in SENSORS or 'QC' not in f or 'COMM' not in f:
                return 0
            if not f.get('boot_id') or not f.get('seq', '').isdigit():
                issue('UNPARSED_MEASUREMENT', str(raw_id))
                return 0
            seq = int(f['seq'])
            if seq > 4294967295:
                raise ValueError('Sequence out of range')
            previous = db.execute('SELECT MAX(sequence_number) AS seq FROM measurement WHERE node_id=? AND sensor_id=? AND boot_id=?',
                                  (node, sensor, f['boot_id'])).fetchone()['seq']
            if previous is not None and seq > previous + 1:
                issue('SEQUENCE_GAP', json.dumps({'after': previous, 'before': seq}))
            elif previous is not None and seq <= previous:
                issue('DUPLICATE_OR_OUT_OF_ORDER', json.dumps({'previous': previous, 'received': seq}))
            f['delivery_order'] = 'OUT_OF_ORDER' if previous is not None and seq < previous else 'IN_ORDER'
            for parameter, _, unit in SENSORS[sensor][2]:
                value, qc = None, f['QC']
                if f['COMM'] == 'OK' and parameter in f:
                    try:
                        value = float(f[parameter])
                        if not math.isfinite(value):
                            value, qc = None, 'SENSOR_FAULT'
                    except ValueError:
                        qc = 'SENSOR_FAULT'
                if value is None and qc in ('OK', 'UNVALIDATED'):
                    qc = 'MISSING_VALUE'
                # Current bench format has no validated sample UTC, even if a sender changes UTC text.
                cursor = db.execute('''INSERT OR IGNORE INTO measurement
                    (raw_id,received_utc,received_epoch,sample_timestamp_utc,clock_sync_status,
                     node_id,sensor_id,sensor_model,boot_id,sequence_number,parameter,value,unit,qc_flag,
                     metadata,tank_id,experiment_id,location) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (raw_id, stamp, now, None, 'UNSYNCED', node, sensor, SENSORS[sensor][1], f['boot_id'],
                     seq, parameter, value, unit, qc, json.dumps(f, ensure_ascii=False),
                     os.getenv('TANK_ID') or None, os.getenv('EXPERIMENT_ID') or None, os.getenv('SENSOR_LOCATION') or None))
                count += cursor.rowcount
        return count

    def latest(self):
        with self.connect() as db:
            # One indexed lookup per known series (measurement_history), so this stays fast as history grows.
            rows = [db.execute('''SELECT * FROM measurement WHERE sensor_id=? AND parameter=?
                AND json_extract(metadata, '$.delivery_order') != 'OUT_OF_ORDER' ORDER BY id DESC LIMIT 1''', (sensor, p[0])).fetchone()
                    for sensor, data in SENSORS.items() for p in data[2]]
            latest = [dict(row) for row in rows if row]
            stats = {'measurements': db.execute('SELECT COUNT(*) FROM measurement').fetchone()[0],
                     'last_received_utc': (db.execute('SELECT received_utc FROM measurement ORDER BY id DESC LIMIT 1').fetchone() or [None])[0]}
            stats['raw_records'] = db.execute('SELECT COUNT(*) FROM raw_log').fetchone()[0]
            stats['issues'] = db.execute('SELECT COUNT(*) FROM issue').fetchone()[0]
        return latest, stats

    def recording(self):
        """{node: True if rows received from it now are kept}."""
        with self.connect() as db:
            return {node: bool(db.execute(f'SELECT {KEEP}', (node,)).fetchone()[0]) for node in NODES}

    def settings(self):
        with self.connect() as db:
            return dict(db.execute('SELECT key, value FROM setting').fetchall())

    def put_setting(self, key, value, node, operator, command, note='control page'):
        with self.connect() as db:
            db.execute('INSERT INTO setting(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, value))
            self.log_event(node, operator, command, note, 'result=OK', db)

    def log_event(self, node, operator, command, note, result, db=None):
        if db is None:
            with self.connect() as db:
                return self.log_event(node, operator, command, note, result, db)
        db.execute('INSERT INTO operator_event(sent_utc,node_id,cmd_id,operator,command,note,result_line) VALUES(?,?,?,?,?,?,?)',
                   (utc(), node, f'{time.time_ns()}-{node}', operator, command, note, result))

    def set_recording(self, on, operator, nodes):
        if not nodes or any(node not in NODES for node in nodes):
            raise ValueError('Unknown node')
        for node in nodes:
            self.put_setting('recording:' + node, int(on), node, operator, 'RECORDING_ON' if on else 'RECORDING_OFF')

    def purge(self, max_age=RECENT_ONLY_S, batch=5000):
        """Delete rows received while recording was off, once older than max_age. Kept rows are never touched.
        Short batches keep each write lock brief so the receiver is not blocked."""
        cutoff, removed = time.time() - max_age, 0
        while True:
            with self.connect() as db:
                ids = [row[0] for row in db.execute('SELECT id FROM raw_log WHERE keep=0 AND received_epoch<? LIMIT ?', (cutoff, batch))]
                if not ids:
                    db.execute('DELETE FROM issue WHERE keep=0 AND received_utc<?', (utc(cutoff),))
                    return removed
                marks = ','.join('?' * len(ids))
                db.execute(f'DELETE FROM measurement WHERE raw_id IN ({marks})', ids)
                db.execute(f'DELETE FROM raw_log WHERE id IN ({marks})', ids)
                removed += len(ids)

    def export(self, output, sensor='', every=60):
        """CSV of measurements with their raw lines; every=60 keeps one real sample per node/sensor/parameter per
        gateway-received minute (the first valid one, else the first), never an average, plus samples_in_minute."""
        if (sensor and sensor not in SENSORS) or every not in (0, 60):
            raise ValueError('Unknown export')
        where, args = ('WHERE m.sensor_id=?', (sensor,)) if sensor else ('', ())
        sql = f'SELECT m.*, r.line AS raw_line FROM measurement m JOIN raw_log r ON r.id=m.raw_id {where} ORDER BY m.id'
        if every:
            sql = f'''SELECT * FROM (SELECT m.*, r.line AS raw_line, COUNT(*) OVER w AS samples_in_minute,
                      ROW_NUMBER() OVER (w ORDER BY m.value IS NULL, m.id) AS pick
                      FROM measurement m JOIN raw_log r ON r.id=m.raw_id {where}
                      WINDOW w AS (PARTITION BY m.node_id, m.sensor_id, m.parameter, CAST(m.received_epoch / 60 AS INTEGER)))
                      WHERE pick=1 ORDER BY id'''
        # One transaction gives a consistent export while acquisition continues.
        with self.connect() as db:
            cursor = db.execute(sql, args)
            columns = [i for i, c in enumerate(cursor.description) if c[0] != 'pick']
            writer = csv.writer(output)
            writer.writerow([cursor.description[i][0] for i in columns])
            for row in cursor:
                writer.writerow(["'" + x if isinstance(x, str) and x.startswith(('=', '+', '-', '@')) else x for x in (row[i] for i in columns)])

    def history(self, sensor, parameter, limit=300):
        if sensor not in SENSORS or parameter not in [p[0] for p in SENSORS[sensor][2]]:
            raise ValueError('Unknown series')
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM measurement WHERE sensor_id=? AND parameter=? ORDER BY id DESC LIMIT ?',
                                                    (sensor, parameter, limit)).fetchall()][::-1]


class Camera:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame = None
        self.last_frame = 0
        self.state, self.code = '视频待验证', 'NOT_CONFIGURED'  # code: language-neutral for other pages
        self.configured = bool(os.getenv('CAMERA_RTSP_URI'))

    def save_frame(self, folder):
        """Write the current frame, only if fresh (<10 s), to folder/<UTC date>/<HHMMSS>Z.jpg named by the Jetson
        time the frame was decoded (the camera's own clock is ~6 months off). Returns the path or None."""
        with self.lock:
            frame, taken = self.frame, self.last_frame
        if not frame or time.time() - taken >= 10:
            return None
        stamp = datetime.fromtimestamp(taken, timezone.utc)
        path = Path(folder) / stamp.strftime('%Y-%m-%d') / stamp.strftime('%H%M%SZ.jpg')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.with_suffix('.tmp').write_bytes(frame)
        os.replace(path.with_suffix('.tmp'), path)  # never leave a half-written image
        return path

    def snapshot(self):
        with self.lock:
            age = time.time() - self.last_frame if self.last_frame else None
            return {'configured': self.configured, 'state': self.state, 'code': self.code,
                    'live': age is not None and age < 10, 'last_frame_age_seconds': age}

    def run(self):
        if not self.configured:
            return
        try:
            import gi
            gi.require_version('Gst', '1.0')
            from gi.repository import Gst
            Gst.init(None)
        except (ImportError, ValueError):
            self.state, self.code = 'GStreamer 不可用', 'NO_GSTREAMER'
            return
        # URI comes only from a private server-side environment file, never an API response.
        while True:
            pipeline = None
            try:
                # Explicit H.264 chain: uridecodebin picks nvv4l2decoder on Jetson, whose NVMM output
                # cannot link to videoconvert. ONVIF reports H264 for this camera (2026-09-27).
                if Gst.ElementFactory.find('nvv4l2decoder') and Gst.ElementFactory.find('nvvidconv'):
                    decode = 'nvv4l2decoder ! nvvidconv ! video/x-raw,format=I420'
                else:
                    decode = 'avdec_h264 ! videoconvert'
                pipeline = Gst.parse_launch(
                    'rtspsrc name=src protocols=tcp latency=200 ! rtph264depay ! h264parse ! ' + decode +
                    ' ! videoscale ! videorate ! video/x-raw,pixel-aspect-ratio=1/1,framerate=5/1'
                    ' ! jpegenc quality=75 ! appsink name=sink max-buffers=1 drop=true sync=false')
                pipeline.get_by_name('src').set_property('location', os.environ['CAMERA_RTSP_URI'])
                sink = pipeline.get_by_name('sink')
                pipeline.set_state(Gst.State.PLAYING)
                self.state, self.code = '正在连接视频', 'CONNECTING'
                bus = pipeline.get_bus()
                last = time.monotonic()
                while True:
                    sample = sink.emit('try-pull-sample', Gst.SECOND)
                    if sample:
                        buffer = sample.get_buffer()
                        content = buffer.extract_dup(0, buffer.get_size())
                        with self.lock:
                            self.frame, self.last_frame = content, time.time()
                            self.state, self.code = '视频已解码', 'LIVE'
                        last = time.monotonic()
                    if bus.pop_filtered(Gst.MessageType.ERROR | Gst.MessageType.EOS) or time.monotonic() - last > 20:
                        break
            except Exception:
                pass  # Do not log decoder errors containing credentials or private URIs.
            finally:
                if pipeline is not None:
                    pipeline.set_state(Gst.State.NULL)
                with self.lock:
                    self.frame, self.last_frame = None, 0
                    self.state, self.code = '视频连接失败，等待重试', 'RETRYING'
            time.sleep(5)


class Network:
    def __init__(self, interface):
        self.interface = interface
        self.states = {}
        self.lock = threading.Lock()

    def run(self):
        while True:
            for node, config in NODES.items():
                if not config['ip']:
                    continue
                reachable = False
                identity = False
                try:
                    ping = subprocess.run(['ping', '-I', self.interface, '-c', '1', '-W', '1', config['ip']], capture_output=True, timeout=3)
                    neighbor = subprocess.run(['ip', 'neigh', 'show', config['ip'], 'dev', self.interface], capture_output=True, text=True, timeout=3)
                    reachable = ping.returncode == 0
                    identity = config['mac'] in neighbor.stdout.lower()
                except (OSError, subprocess.TimeoutExpired):
                    pass
                with self.lock:
                    self.states[node] = {'reachable': reachable, 'identity_verified': identity, 'checked_utc': utc()}
            time.sleep(10)

    def snapshot(self):
        with self.lock:
            return dict(self.states)


def handler_for(store, camera, network, ingest_only=False, pump=None, heater=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def send(self, content, kind='application/json; charset=utf-8', status=200, cookie=None):
            if not isinstance(content, bytes):
                content = json.dumps(content, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            if cookie is not None:
                # Session cookie for the /control page only; never readable by page scripts or sent cross-site.
                self.send_header('Set-Cookie', f'pump_session={cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age={43200 if cookie else 0}')
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def session_token(self):
            try:
                morsel = SimpleCookie(self.headers.get('Cookie', '')).get('pump_session')
            except CookieError:
                return None
            return morsel.value if morsel else None

        def json_body(self):
            # JSON only: a cross-site HTML form cannot send it without a CORS preflight, which this server never grants.
            if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                raise TypeError('JSON required')
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024:
                raise ValueError('Invalid body length')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError('Expected object')
            return body

        def control_post(self):
            if pump is None:
                return self.send({'error': 'NOT_ENABLED'}, status=403)
            try:
                body = self.json_body()
            except TypeError:
                return self.send({'error': 'JSON required'}, status=415)
            except ValueError:
                return self.send({'error': 'Invalid request'}, status=400)
            if self.path == '/api/logout':
                pump.logout(self.session_token())
                return self.send({'user': None}, cookie='')
            if self.path == '/api/login':
                name, password = body.get('username'), body.get('password')
                if not isinstance(name, str) or not isinstance(password, str) or not 0 < len(name) <= 20 or len(password) > 128:
                    return self.send({'error': 'Invalid request'}, status=400)
                verdict, token = pump.login(name, password)
                if verdict != 'OK':
                    return self.send({'error': verdict}, status={'LOCKED': 429, 'NO_USERS': 403}.get(verdict, 401))
                return self.send({'user': name}, cookie=token)
            user = pump.user(self.session_token())
            if not user:
                return self.send({'error': 'LOGIN_REQUIRED'}, status=401)
            if self.path == '/api/recording':
                nodes = body.get('nodes')
                try:
                    if not isinstance(body.get('on'), bool) or not isinstance(nodes, list) or not all(isinstance(n, str) for n in nodes):
                        raise ValueError('Invalid request')
                    store.set_recording(body['on'], 'web-' + user, nodes)
                except ValueError:
                    return self.send({'error': 'Invalid request'}, status=400)
                return self.send({'recording': store.recording()})
            if self.path == '/api/heater':
                import heater_ctl
                enabled, setpoint = body.get('enabled'), body.get('setpoint')
                try:
                    if heater is None or (enabled is None and setpoint is None) or (enabled is not None and not isinstance(enabled, bool)):
                        raise ValueError('Invalid request')
                    if setpoint is not None:
                        setpoint = float(setpoint)
                        low, high = heater_ctl.SETPOINT_RANGE
                        if isinstance(body['setpoint'], bool) or not math.isfinite(setpoint) or not low <= setpoint <= high:
                            raise ValueError('Setpoint out of range')
                        store.put_setting('heater:setpoint', round(setpoint, 1), heater_ctl.NODE, 'web-' + user, f'HEATER_SETPOINT,{setpoint:.1f}')
                    if enabled is not None:
                        if enabled and store.settings().get('heater:setpoint') is None:
                            raise ValueError('Set a temperature first')
                        store.put_setting('heater:enabled', int(enabled), heater_ctl.NODE, 'web-' + user, 'HEATER_AUTO_ON' if enabled else 'HEATER_AUTO_OFF')
                except (ValueError, TypeError):
                    return self.send({'error': 'Invalid request'}, status=400)
                heater.wake.set()  # apply within a moment instead of at the next 10 s step
                return self.send({'heater': store.settings()})
            device, action = body.get('device'), body.get('action')
            try:
                if not isinstance(device, str) or pump.kind(device) != 'pump':
                    raise ValueError('Unknown device')
                if action == 'start':
                    rate = float(body['rate'])
                    if not math.isfinite(rate) or not 0.5 <= rate <= 105:
                        raise ValueError('Rate out of range')
                    command = f'DC,{rate:.2f},*'
                elif action == 'stop':
                    command = 'X'
                else:
                    raise ValueError('Unknown action')
            except (ValueError, TypeError, KeyError):
                return self.send({'error': 'Invalid request'}, status=400)
            result = pump.run(device, command, user)
            status = {'BUSY': 409, 'BROKER_UNAVAILABLE': 503, 'NO_REPLY': 504}.get(result['result'], 200)
            return self.send(dict(result, device=device, command=command), status=status)

        def do_POST(self):
            if not ingest_only and self.path in ('/api/login', '/api/logout', '/api/control', '/api/recording', '/api/heater'):
                return self.control_post()
            if not ingest_only or self.path != '/ingest':
                return self.send({'error': 'Read-only dashboard'}, status=405)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16384:
                    raise ValueError('Invalid body length')
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError('Expected object')
                result = store.ingest(payload.get('node_id'), payload.get('line'))
                self.send({'stored_measurements': result})
            except (ValueError, TypeError, KeyError):
                self.send({'error': 'Invalid record'}, status=400)
            except sqlite3.Error:
                self.send({'error': 'Storage failure; retry required'}, status=503)

        def do_GET(self):
            if ingest_only:
                return self.send({'error': 'Ingestion only'}, status=404)
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query)
            try:
                if parsed.path == '/api/status':
                    latest, stats = store.latest()
                    for row in latest:
                        row['metadata'] = json.loads(row['metadata'])
                        age = row['metadata'].get('transport_age_ms', '0')
                        age_seconds = int(age) / 1000 if str(age).isdigit() else float('inf')
                        row['stale'] = time.time() - row['received_epoch'] + age_seconds > 15
                    return self.send({'gateway_utc': utc(), 'latest': latest, 'stats': stats,
                                      'network': network.snapshot(), 'nodes': NODES, 'camera': camera.snapshot(),
                                      'metadata_configured': bool(os.getenv('TANK_ID') and os.getenv('EXPERIMENT_ID')),
                                      'recording': store.recording(),
                                      'heater': heater.snapshot() if heater else None,
                                      'series': [{'sensor': sensor, 'parameter': p, 'label': label, 'unit': unit, 'node': data[0]}
                                                 for sensor, data in SENSORS.items() for p, label, unit in data[2]]})
                if parsed.path == '/api/session':
                    if not pump:
                        return self.send({'enabled': False, 'reason': 'NOT_ENABLED', 'user': None, 'devices': []})
                    return self.send(dict(pump.status(), user=pump.user(self.session_token()), devices=pump.devices()))
                if parsed.path == '/api/control/events':
                    if not (pump and pump.user(self.session_token())):
                        return self.send({'error': 'LOGIN_REQUIRED'}, status=401)
                    return self.send(pump.events())
                if parsed.path == '/api/history':
                    return self.send(store.history(query.get('sensor', [''])[0], query.get('parameter', [''])[0]))
                if parsed.path == '/camera.jpg':
                    with camera.lock:
                        frame = camera.frame if time.time() - camera.last_frame < 10 else None
                    if frame:
                        return self.send(frame, 'image/jpeg')
                    return self.send({'error': 'Video unavailable'}, status=503)
                if parsed.path == '/export.csv':
                    # ?sensor=<id> for one sensor; ?every=0 for every 4 s sample (default: one per minute).
                    sensor, every = query.get('sensor', [''])[0], query.get('every', ['60'])[0]
                    if every not in ('0', '60'):
                        raise ValueError('Unknown export')
                    import tempfile  # spool to disk so a large history never sits in RAM
                    with tempfile.TemporaryFile(mode='w+', encoding='utf-8', newline='') as output:
                        store.export(output, sensor, int(every))
                        output.seek(0)
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/csv; charset=utf-8')
                        self.send_header('Content-Disposition', f'attachment; filename="{sensor or "all"}_{"1min" if every == "60" else "all"}.csv"')
                        self.end_headers()
                        while chunk := output.read(65536):
                            self.wfile.write(chunk.encode())
                    return
                if parsed.path == '/api/issues':
                    with store.connect() as db:
                        return self.send([dict(row) for row in db.execute('SELECT * FROM issue ORDER BY id DESC LIMIT 100')])
                files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css'),
                         '/en': ('en.html', 'text/html; charset=utf-8'), '/app_en.js': ('app_en.js', 'text/javascript'),
                         '/control': ('control.html', 'text/html; charset=utf-8'), '/control/en': ('control_en.html', 'text/html; charset=utf-8'),
                         '/control.js': ('control.js', 'text/javascript')}
                if parsed.path in files:
                    name, kind = files[parsed.path]
                    return self.send((ROOT / 'static' / name).read_bytes(), kind)
                self.send({'error': 'Not found'}, status=404)
            except ValueError:
                self.send({'error': 'Invalid query'}, status=400)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except sqlite3.Error:
                self.send({'error': 'Storage failure'}, status=503)
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', default='127.0.0.1', help='Bind only to the lab Ethernet IPv4 for LAN access')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--ingest-port', type=int, default=8766)
    parser.add_argument('--interface', default='enP8p1s0')
    parser.add_argument('--db', default=str(ROOT / 'data' / 'measurements.sqlite3'))
    parser.add_argument('--frames-dir', default=str(ROOT.parents[1] / 'Raw_data' / 'Node-3-Camera'),
                        help='Where one camera frame per minute is kept; empty string disables saving')
    parser.add_argument('--pump-control', action='store_true',
                        help='Enable the login-protected device control page /control (production only; commands reach real devices)')
    args = parser.parse_args()
    os.umask(0o077)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    store, camera, network = Store(args.db), Camera(), Network(args.interface)
    pump = None
    if args.pump_control:
        import pump_ctl
        pump = pump_ctl.WebControl(args.db, argparse.Namespace(credentials=str(ROOT / 'data/mqtt/credentials.json'), host='127.0.0.1', port=1883))
    heater = None
    if pump:  # the thermostat publishes with the same pump-operator account; without --pump-control the heater stays off
        import heater_ctl, pump_ctl
        heater = heater_ctl.Thermostat(store, pump.conn, pump_ctl.publish)
        threading.Thread(target=heater.run, daemon=True).start()
    public = ThreadingHTTPServer((args.bind, args.port), handler_for(store, camera, network, pump=pump, heater=heater))
    local = ThreadingHTTPServer(('127.0.0.1', args.ingest_port), handler_for(store, camera, network, True))
    (Path(args.db).parent / 'server.pid').write_text(str(os.getpid()) + '\n')
    def purge_forever():
        while True:
            try:
                removed = store.purge()
                if removed:
                    print(f'{utc()} purged {removed} raw records received while recording was off', flush=True)
            except sqlite3.Error as error:
                print(f'{utc()} purge failed: {error}', flush=True)
            time.sleep(600)
    def frames_forever():  # one still frame per minute while the video is live
        while True:
            time.sleep(60 - time.time() % 60)
            try:
                camera.save_frame(args.frames_dir)
            except OSError as error:
                print(f'{utc()} frame save failed: {error}', flush=True)
    for target in (local.serve_forever, camera.run, network.run, purge_forever) + ((frames_forever,) if args.frames_dir else ()):
        threading.Thread(target=target, daemon=True).start()
    print(f'Dashboard http://{args.bind}:{args.port} | local ingestion 127.0.0.1:{args.ingest_port}', flush=True)
    try:
        public.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        local.shutdown()
        public.server_close()
        local.server_close()


if __name__ == '__main__':
    main()
