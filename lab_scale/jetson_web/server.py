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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
NODES = {
    'shrimp-node01': {'name': 'Node 1 · DO / ORP', 'ip': '192.168.88.252', 'mac': '44:b1:76:ce:d1:a8'},
    'shrimp-node02': {'name': 'Node 2 · EC / pH', 'ip': '192.168.88.251', 'mac': '44:b1:76:cc:d4:84'},
}
SENSORS = {
    'DO_SEN0681': ('shrimp-node01', 'DFRobot SEN0681', [('DO_mg_L', 'DO', 'mg/L'), ('saturation_pct', '饱和度', '%'), ('temperature_C', 'DO 温度', '°C')]),
    'ORP_SEN0709': ('shrimp-node01', 'DFRobot SEN0709', [('ORP_mV', 'ORP', 'mV'), ('temperature_C', 'ORP 温度', '°C')]),
    'EC_ATLAS_EZO': ('shrimp-node02', 'Atlas EZO-EC', [('EC_uS_cm', 'EC', 'µS/cm'), ('salinity_PSU', '盐度', 'PSU')]),
    'PH_ATLAS_EZO': ('shrimp-node02', 'Atlas EZO-pH', [('pH', 'pH', 'pH')]),
}


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def fields(line):
    return dict(re.findall(r'(\w+)=([^\s]*)', line))


class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
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
            ''')

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
            raw_id = db.execute('INSERT INTO raw_log(received_utc,received_epoch,node_id,transport,line) VALUES(?,?,?,?,?)',
                                (stamp, now, node, transport, line)).lastrowid
            # Health, RX and TX lines remain raw records; only completed measurement reports are parsed.
            if sensor not in SENSORS or 'QC' not in f or 'COMM' not in f:
                return 0
            if not f.get('boot_id') or not f.get('seq', '').isdigit():
                db.execute('INSERT INTO issue(received_utc,node_id,sensor_id,kind,details) VALUES(?,?,?,?,?)',
                           (stamp, node, sensor, 'UNPARSED_MEASUREMENT', str(raw_id)))
                return 0
            seq = int(f['seq'])
            if seq > 4294967295:
                raise ValueError('Sequence out of range')
            previous = db.execute('SELECT MAX(sequence_number) AS seq FROM measurement WHERE node_id=? AND sensor_id=? AND boot_id=?',
                                  (node, sensor, f['boot_id'])).fetchone()['seq']
            if previous is not None and seq > previous + 1:
                db.execute('INSERT INTO issue(received_utc,node_id,sensor_id,kind,details) VALUES(?,?,?,?,?)',
                           (stamp, node, sensor, 'SEQUENCE_GAP', json.dumps({'after': previous, 'before': seq})))
            elif previous is not None and seq <= previous:
                db.execute('INSERT INTO issue(received_utc,node_id,sensor_id,kind,details) VALUES(?,?,?,?,?)',
                           (stamp, node, sensor, 'DUPLICATE_OR_OUT_OF_ORDER', json.dumps({'previous': previous, 'received': seq})))
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
            rows = db.execute('''SELECT * FROM measurement WHERE id IN
                (SELECT MAX(id) FROM measurement WHERE json_extract(metadata, '$.delivery_order') != 'OUT_OF_ORDER' GROUP BY sensor_id,parameter)''').fetchall()
            latest = [dict(row) for row in rows]
            stats = dict(db.execute('SELECT COUNT(*) AS measurements, MAX(received_utc) AS last_received_utc FROM measurement').fetchone())
            stats['raw_records'] = db.execute('SELECT COUNT(*) FROM raw_log').fetchone()[0]
            stats['issues'] = db.execute('SELECT COUNT(*) FROM issue').fetchone()[0]
        return latest, stats

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


def handler_for(store, camera, network, ingest_only=False):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def send(self, content, kind='application/json; charset=utf-8', status=200):
            if not isinstance(content, bytes):
                content = json.dumps(content, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
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
                                      'series': [{'sensor': sensor, 'parameter': p, 'label': label, 'unit': unit, 'node': data[0]}
                                                 for sensor, data in SENSORS.items() for p, label, unit in data[2]]})
                if parsed.path == '/api/history':
                    return self.send(store.history(query.get('sensor', [''])[0], query.get('parameter', [''])[0]))
                if parsed.path == '/camera.jpg':
                    with camera.lock:
                        frame = camera.frame if time.time() - camera.last_frame < 10 else None
                    if frame:
                        return self.send(frame, 'image/jpeg')
                    return self.send({'error': 'Video unavailable'}, status=503)
                if parsed.path == '/export.csv':
                    # A transaction provides a consistent export while acquisition continues.
                    # Spool rows to disk to avoid loading the full history in RAM.
                    import tempfile
                    with tempfile.TemporaryFile(mode='w+', encoding='utf-8', newline='') as output:
                        with store.connect() as db:
                            cursor = db.execute('SELECT m.*, r.line AS raw_line FROM measurement m JOIN raw_log r ON r.id=m.raw_id ORDER BY m.id')
                            writer = csv.writer(output)
                            writer.writerow([column[0] for column in cursor.description])
                            for row in cursor:
                                writer.writerow(["'" + x if isinstance(x, str) and x.startswith(('=', '+', '-', '@')) else x for x in row])
                        output.seek(0)
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/csv; charset=utf-8')
                        self.send_header('Content-Disposition', 'attachment; filename="measurements.csv"')
                        self.end_headers()
                        while chunk := output.read(65536):
                            self.wfile.write(chunk.encode())
                    return
                if parsed.path == '/api/issues':
                    with store.connect() as db:
                        return self.send([dict(row) for row in db.execute('SELECT * FROM issue ORDER BY id DESC LIMIT 100')])
                files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css'),
                         '/en': ('en.html', 'text/html; charset=utf-8'), '/app_en.js': ('app_en.js', 'text/javascript')}
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
    args = parser.parse_args()
    os.umask(0o077)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    store, camera, network = Store(args.db), Camera(), Network(args.interface)
    public = ThreadingHTTPServer((args.bind, args.port), handler_for(store, camera, network))
    local = ThreadingHTTPServer(('127.0.0.1', args.ingest_port), handler_for(store, camera, network, True))
    (Path(args.db).parent / 'server.pid').write_text(str(os.getpid()) + '\n')
    for target in (local.serve_forever, camera.run, network.run):
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
