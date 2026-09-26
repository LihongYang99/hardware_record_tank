import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from server import Store, Camera, Network, handler_for


def record(seq=1, boot='boot-a', values='DO_mg_L=8.2 saturation_pct=92 temperature_C=24 COMM=OK QC=UNVALIDATED'):
    return f'node_id=shrimp-node01 boot_id={boot} sensor=DO_SEN0681 seq={seq} request_uptime_ms=4000 rx_uptime_ms=4120 cycle=1 UTC=UNSYNCED raw=01030C {values}'


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / 'test.sqlite3')

    def tearDown(self):
        self.temp.cleanup()

    def test_unsynced_raw_and_metadata_preserved(self):
        self.assertEqual(self.store.ingest('shrimp-node01', record()), 3)
        rows, stats = self.store.latest()
        self.assertEqual(stats['raw_records'], 1)
        self.assertTrue(all(r['sample_timestamp_utc'] is None for r in rows))
        self.assertTrue(all(r['clock_sync_status'] == 'UNSYNCED' for r in rows))
        self.assertEqual(json.loads(rows[0]['metadata'])['raw'], '01030C')

    def test_errors_never_become_zero_or_keep_previous_value(self):
        self.store.ingest('shrimp-node01', record())
        self.store.ingest('shrimp-node01', record(2, values='COMM=ERROR QC=COMMUNICATION_ERROR reason=TIMEOUT'))
        rows, _ = self.store.latest()
        self.assertTrue(all(r['value'] is None for r in rows))
        self.assertTrue(all(r['qc_flag'] == 'COMMUNICATION_ERROR' for r in rows))

    def test_duplicates_gaps_reboots_and_delayed_records(self):
        for line in [record(1), record(1), record(3), record(2)]:
            self.store.ingest('shrimp-node01', line)
        rows, stats = self.store.latest()
        self.assertEqual(stats['raw_records'], 4)
        self.assertEqual(stats['measurements'], 9)
        self.assertEqual(stats['issues'], 3)
        self.assertTrue(all(r['sequence_number'] == 3 for r in rows))
        self.store.ingest('shrimp-node01', record(1, 'boot-b'))
        self.assertTrue(all(r['boot_id'] == 'boot-b' for r in self.store.latest()[0]))

    def test_nonfinite_and_missing_values(self):
        self.store.ingest('shrimp-node01', record(values='DO_mg_L=nan saturation_pct=inf COMM=OK QC=UNVALIDATED'))
        rows, _ = self.store.latest()
        self.assertTrue(all(r['value'] is None for r in rows))
        self.assertTrue(all(r['qc_flag'] != 'UNVALIDATED' for r in rows))

    def test_node2_zero_retains_configuration_warning_and_rx(self):
        self.store.ingest('shrimp-node02', 'node_id=shrimp-node02 boot_id=b sensor=EC_ATLAS_EZO seq=1 event=RX raw_hex=302C300D')
        self.store.ingest('shrimp-node02', 'node_id=shrimp-node02 boot_id=b sensor=EC_ATLAS_EZO seq=1 EC_uS_cm=0 salinity_PSU=0 K=1.000 calibration_reply=?CAL,0 compensation_setting_C=25 UTC=UNSYNCED COMM=OK QC=CONFIGURATION_MISMATCH')
        rows, stats = self.store.latest()
        self.assertEqual(stats['raw_records'], 2)
        self.assertTrue(all(r['value'] == 0 and r['qc_flag'] == 'CONFIGURATION_MISMATCH' for r in rows))
        self.assertEqual(json.loads(rows[0]['metadata'])['calibration_reply'], '?CAL,0')

    def test_identity_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.ingest('shrimp-node02', record())
        self.assertEqual(self.store.latest()[1]['raw_records'], 0)

    def test_local_ingestion_roundtrip_and_persistence(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.store, Camera(), Network('lo'), True))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            payload = json.dumps({'node_id': 'shrimp-node01', 'line': record()}).encode()
            with urlopen(Request(f'http://127.0.0.1:{server.server_port}/ingest', data=payload,
                                 headers={'Content-Type': 'application/json'})) as response:
                self.assertEqual(json.load(response)['stored_measurements'], 3)
            reopened = Store(self.store.path)
            self.assertEqual(reopened.latest()[1]['measurements'], 3)
        finally:
            server.shutdown()
            server.server_close()

    def test_public_api_is_read_only_and_empty_state_is_honest(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.store, Camera(), Network('lo')))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        root = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(root + '/api/status') as response:
                data = json.load(response)
            self.assertEqual(data['latest'], [])
            self.assertFalse(data['camera']['live'])
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(root + '/ingest', data=b'{}'))
            self.assertEqual(error.exception.code, 405)
            with self.assertRaises(HTTPError) as error:
                urlopen(root + '/camera.jpg')
            self.assertEqual(error.exception.code, 503)
            with urlopen(root + '/export.csv') as response:
                self.assertIn('sample_timestamp_utc', response.read().decode())
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()
