import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen
from http.server import ThreadingHTTPServer
from server import Store, Camera, Network, handler_for
from mqtt_receiver import Receiver, accept_record, mqtt, RUNTIME, TOPIC, topic
from prepare_mqtt import prepare


def packet(seq=1, age=0):
    return (f'node_id=shrimp-node01 boot_id=0123456789abcdef sensor=DO_SEN0681 seq={seq} '
            'request_uptime_ms=4000 rx_uptime_ms=4050 UTC=UNSYNCED raw=01030C '
            'DO_mg_L=7.575 saturation_pct=102.31 temperature_C=21.38 COMM=OK QC=UNVALIDATED '
            f'transport_boot_id=0123456789abcdef transport_seq={seq} transport_age_ms={age}').encode()


def node2_packet(seq=1):
    return (f'node_id=shrimp-node02 boot_id=fedcba9876543210 sensor=PH_ATLAS_EZO seq={seq} cycle=1 '
            'scheduled_uptime_ms=4000 request_uptime_ms=4000 rx_uptime_ms=4180 UTC=UNSYNCED pH=7.012 '
            'compensation_setting_C=25.00 calibration_reply=?CAL,0 COMM=OK QC=COMPENSATION_MISSING '
            f'validation=UNVALIDATED temp_source=NOT_VERIFIED transport_boot_id=fedcba9876543210 transport_seq={seq} '
            'firmware=node02-mqtt-0.1 transport_age_ms=3 network_buffered=0').encode()


class MQTTTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / 'measurements.sqlite3')

    def tearDown(self):
        self.temp.cleanup()

    def test_ack_only_after_commit_and_never_on_storage_failure(self):
        receiver = Receiver(self.store, '127.0.0.1', 1883, 'test')
        class Client:
            published = []
            def publish(inner, topic, payload, **kwargs):
                self.assertEqual(Store(self.store.path).latest()[1]['measurements'], 3)
                inner.published.append((topic, payload))
        client = Client()
        message = type('Message', (), {'topic': TOPIC+'records', 'payload': packet()})()
        receiver.on_message(client, None, message)
        self.assertEqual(client.published, [(TOPIC+'ack', '0123456789abcdef:1')])
        with patch.object(self.store, 'ingest', side_effect=sqlite3.OperationalError('disk full')):
            with self.assertRaises(sqlite3.OperationalError):
                receiver.on_message(client, None, message)
        self.assertEqual(len(client.published), 1)

    def test_corrupt_or_wrong_identity_cannot_become_measurement(self):
        for bad in [packet()+b' seq=99', packet().replace(b'node_id=shrimp-node01',b'node_id=shrimp-node02'), packet()+b'\n', packet().replace(b'transport_age_ms=0',b'transport_age_ms=NaN')]:
            with self.assertRaises(ValueError):
                accept_record(self.store, bad)
        self.assertEqual(self.store.latest()[1]['measurements'], 0)

    def test_node2_routed_by_topic_and_cannot_impersonate(self):
        receiver = Receiver(self.store, '127.0.0.1', 1883, 'test')
        class Client:
            published = []
            def publish(inner, topic_name, payload, **kwargs):
                inner.published.append((topic_name, payload))
        client = Client()
        message = type('Message', (), {'topic': topic('shrimp-node02')+'records', 'payload': node2_packet()})()
        receiver.on_message(client, None, message)
        self.assertEqual(client.published, [(topic('shrimp-node02')+'ack', 'fedcba9876543210:1')])
        self.assertEqual(self.store.latest()[1]['measurements'], 1)
        for payload, node in [(node2_packet(2), 'shrimp-node01'), (packet(), 'shrimp-node02'), (packet(), 'shrimp-node99')]:
            with self.assertRaises(ValueError):
                accept_record(self.store, payload, node)
        self.assertEqual(self.store.latest()[1]['measurements'], 1)

    def test_acl_isolates_each_node(self):
        credentials = prepare(Path(self.temp.name)/'mqtt', '127.0.0.2')
        self.assertIn('shrimp-node02', credentials)
        acl = (Path(self.temp.name)/'mqtt'/'acl').read_text().split('user ')
        node2 = next(block for block in acl if block.startswith('shrimp-node02'))
        self.assertIn('topic write shrimp/lab/shrimp-node02/records', node2)
        self.assertNotIn('shrimp-node01', node2)

    def test_retry_is_idempotent_and_buffered_data_is_stale_in_api(self):
        self.assertEqual(accept_record(self.store, packet(age=60000)), '0123456789abcdef:1')
        accept_record(self.store, packet(age=61000))
        self.assertEqual(self.store.latest()[1]['measurements'], 3)
        server = ThreadingHTTPServer(('127.0.0.1',0),handler_for(self.store,Camera(),Network('lo')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with urlopen(f'http://127.0.0.1:{server.server_port}/api/status') as response:
                rows=json.load(response)['latest']
            self.assertTrue(all(row['stale'] for row in rows))
        finally:
            server.shutdown(); server.server_close()

    def test_real_broker_database_ack_and_reconnect(self):
        broker = RUNTIME / 'usr/sbin/mosquitto'
        self.assertTrue(broker.exists(), 'Local broker runtime is required for this integration test')
        directory = Path(self.temp.name)/'mqtt'
        credentials = prepare(directory,'127.0.0.2')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0)); port=probe.getsockname()[1]
        config=directory/'mosquitto.conf'
        config.write_text(config.read_text().replace('listener 1883 127.0.0.1',f'listener {port} 127.0.0.1').replace('listener 1883 127.0.0.2\n',''))
        env=dict(os.environ, LD_LIBRARY_PATH=str(RUNTIME/'usr/lib/aarch64-linux-gnu'))
        with (directory/'test.log').open('w') as log:
            process=subprocess.Popen([str(broker),'-c',str(config)],env=env,stdout=log,stderr=log)
        receiver=Receiver(self.store,'127.0.0.1',port,credentials['jetson-receiver'])
        publisher=mqtt.Client('node01-integration-test')
        publisher.username_pw_set('shrimp-node01',credentials['shrimp-node01'])
        ack=threading.Event(); subscribed=threading.Event()
        publisher.on_connect=lambda c,u,f,rc:c.subscribe(TOPIC+'ack',1)
        publisher.on_subscribe=lambda *args:subscribed.set()
        publisher.on_message=lambda c,u,m:ack.set() if m.payload==b'0123456789abcdef:1' else None
        try:
            deadline=time.monotonic()+5
            while True:
                try:
                    receiver.client.connect('127.0.0.1',port);break
                except ConnectionRefusedError:
                    if time.monotonic()>deadline:raise
                    time.sleep(.05)
            receiver.client.loop_start()
            publisher.connect('127.0.0.1',port);publisher.loop_start()
            self.assertTrue(subscribed.wait(5))
            for _ in range(3):
                publisher.publish(TOPIC+'records',packet(),qos=1)
                if ack.wait(1):break
            self.assertTrue(ack.is_set(), 'No application ACK after storage')
            self.assertEqual(self.store.latest()[1]['measurements'],3)
            receiver.client.disconnect();receiver.client.loop_stop()
            ack.clear()
            publisher.publish(TOPIC+'records',packet(),qos=1)
            self.assertFalse(ack.wait(.2))
            receiver.client.reconnect();receiver.client.loop_start()
            for _ in range(3):
                publisher.publish(TOPIC+'records',packet(),qos=1)
                if ack.wait(1):break
            self.assertTrue(ack.is_set())
            self.assertEqual(self.store.latest()[1]['measurements'],3)
        finally:
            publisher.disconnect();publisher.loop_stop()
            receiver.client.disconnect();receiver.client.loop_stop()
            process.terminate();process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
