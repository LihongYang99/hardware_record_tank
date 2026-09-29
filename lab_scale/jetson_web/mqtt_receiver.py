"""Receive Node 1/Node 2/pump-node-1 (Node 4) records; application acknowledgement follows SQLite commit."""
import argparse
import importlib.util
import json
import logging
from pathlib import Path
import re
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT.parents[1] / '.codex-build' / 'runtime'
if importlib.util.find_spec('paho') is None:
    sys.path.insert(0, str(RUNTIME / 'usr/lib/python3/dist-packages'))
import paho.mqtt.client as mqtt
from server import Store, fields, utc

MQTT_NODES = ('shrimp-node01', 'shrimp-node02', 'shrimp-node04', 'shrimp-node05', 'shrimp-node06')
NODE = 'shrimp-node01'
TOPIC = f'shrimp/lab/{NODE}/'  # Node 1 prefix, kept for existing callers


def topic(node):
    return f'shrimp/lab/{node}/'


def accept_record(store, payload, node=NODE):
    """Reject ambiguous identity; retain malformed payload in a separate quarantine."""
    line = payload.decode('utf-8', errors='strict')
    if len(payload) > 8192 or '\n' in line or '\r' in line:
        raise ValueError('Invalid record size or framing')
    pairs = re.findall(r'(\w+)=([^\s]*)', line)
    f = fields(line)
    if len(pairs) != len(f):
        raise ValueError('Duplicate keys')
    boot = f.get('transport_boot_id', '')
    seq = f.get('transport_seq', '')
    if not re.fullmatch(r'[0-9a-f]{16}', boot) or not seq.isdigit() or not 0 < int(seq) <= 4294967295:
        raise ValueError('Invalid delivery identity')
    if node not in MQTT_NODES:
        raise ValueError('Unknown node')
    if f.get('boot_id', boot) != boot or f.get('node_id', node) != node:
        raise ValueError('Conflicting source identity')
    if not f.get('transport_age_ms', '').isdigit() or int(f['transport_age_ms']) > 2**63-1:
        raise ValueError('Invalid transport age')
    store.ingest(node, line, transport='mqtt')
    return f'{boot}:{int(seq)}'


class Receiver:
    def __init__(self, store, host, port, password):
        self.store, self.host, self.port = store, host, port
        # Clean session is safe: ESP retains its head record until our application ACK.
        self.client = mqtt.Client(client_id='jetson-lab-receiver', clean_session=True)
        self.client.username_pw_set('jetson-receiver', password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS mqtt_rejected(id INTEGER PRIMARY KEY, received_utc TEXT NOT NULL, topic TEXT NOT NULL, payload BLOB NOT NULL, reason TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS mqtt_status(node_id TEXT PRIMARY KEY, received_utc TEXT NOT NULL, status TEXT NOT NULL)')

    def on_connect(self, client, _userdata, _flags, rc):
        if rc == 0:
            client.subscribe([(topic(n) + suffix, 1) for n in MQTT_NODES for suffix in ('records', 'status')])
            logging.info('MQTT connected; subscribed to %s', ', '.join(MQTT_NODES))
        else:
            logging.error('MQTT connection refused (code %s)', rc)

    def on_message(self, client, _userdata, message):
        # Identity comes from the topic, which the broker ACL restricts to that node's account.
        parts = message.topic.split('/')
        if len(parts) != 4 or parts[:2] != ['shrimp', 'lab'] or parts[2] not in MQTT_NODES:
            return
        node, kind = parts[2], parts[3]
        if kind == 'status':
            status = message.payload.decode('utf-8', errors='replace')
            if status in ('online', 'offline'):
                with self.store.connect() as db:
                    db.execute('INSERT OR REPLACE INTO mqtt_status VALUES(?,?,?)', (node, utc(), status))
            return
        if kind != 'records':
            return
        try:
            ack = accept_record(self.store, message.payload, node)
        except (ValueError, UnicodeError) as error:
            with self.store.connect() as db:
                db.execute('INSERT INTO mqtt_rejected(received_utc,topic,payload,reason) VALUES(?,?,?,?)',
                           (utc(), message.topic, message.payload, str(error)))
            logging.error('Rejected %s record; preserved in mqtt_rejected, no application ACK', node)
            return
        # Store.ingest has committed and closed its SQLite transaction before this call.
        client.publish(topic(node) + 'ack', ack, qos=1, retain=False)

    def run(self):
        while True:
            try:
                self.client.connect(self.host, self.port, keepalive=20)
                self.client.loop_forever(retry_first_connection=True)
            except (OSError, sqlite3.Error):
                logging.error('MQTT/storage unavailable; no application ACK; reconnecting')
            finally:
                self.client.disconnect()
            time.sleep(3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=1883)
    parser.add_argument('--db', default=str(ROOT / 'data/measurements.sqlite3'))
    parser.add_argument('--credentials', default=str(ROOT / 'data/mqtt/credentials.json'))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    credentials = json.loads(Path(args.credentials).read_text())
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    Receiver(Store(args.db), args.host, args.port, credentials['jetson-receiver']).run()


if __name__ == '__main__':
    main()
