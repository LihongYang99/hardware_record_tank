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

    def test_turbidity_is_stored_and_errors_are_not_zero(self):
        base = 'node_id=shrimp-node06 boot_id=t sensor=TURB_SEN0710 cycle=1 request_uptime_ms=4000 UTC=UNSYNCED '
        self.assertEqual(self.store.ingest('shrimp-node06', base + 'seq=1 raw=0103040D2E00DBD8CD turbidity_NTU=337.4 temperature_C=21.9 COMM=OK QC=UNVALIDATED'), 2)
        self.assertEqual({r['parameter']: r['value'] for r in self.store.latest()[0]}, {'turbidity_NTU': 337.4, 'temperature_C': 21.9})
        self.store.ingest('shrimp-node06', base + 'seq=2 raw= COMM=ERROR QC=COMMUNICATION_ERROR reason=TIMEOUT')
        self.assertTrue(all(r['value'] is None and r['qc_flag'] == 'COMMUNICATION_ERROR' for r in self.store.latest()[0]))
        with self.assertRaises(ValueError):
            self.store.ingest('shrimp-node01', base + 'seq=3 turbidity_NTU=1.0 COMM=OK QC=UNVALIDATED')

    def test_pump_state_is_stored_and_errors_are_not_zero(self):
        base = 'node_id=shrimp-node04 boot_id=p sensor=PUMP_ATLAS_PMP cycle=1 request_uptime_ms=4000 UTC=UNSYNCED '
        self.assertEqual(self.store.ingest('shrimp-node04', base + 'seq=1 pump_on=1 int_pin=1 motor_V=12.10 total_volume_mL=5.25 '
                                           'target_mL_min=80.00 raw_D=?D,*,1 raw_PV=?PV,12.10 raw_TV=?TV,5.25 COMM=OK QC=UNVALIDATED'), 4)
        values = {r['parameter']: r['value'] for r in self.store.latest()[0]}
        self.assertEqual(values, {'pump_on': 1.0, 'target_mL_min': 80.0, 'motor_V': 12.1, 'total_volume_mL': 5.25})
        self.assertEqual(json.loads(self.store.latest()[0][0]['metadata'])['raw_D'], '?D,*,1')
        self.store.ingest('shrimp-node04', base + 'seq=2 command=D,? reply=NONE COMM=ERROR QC=COMMUNICATION_ERROR reason=REPLY_TIMEOUT')
        self.assertTrue(all(r['value'] is None and r['qc_flag'] == 'COMMUNICATION_ERROR' for r in self.store.latest()[0]))
        with self.assertRaises(ValueError):
            self.store.ingest('shrimp-node01', base + 'seq=3 pump_on=1 COMM=OK QC=UNVALIDATED')
        with self.assertRaises(ValueError):  # pump 2 cannot write pump 1's sensor
            self.store.ingest('shrimp-node05', base.replace('shrimp-node04', 'shrimp-node05') + 'seq=3 pump_on=1 COMM=OK QC=UNVALIDATED')
        pump2 = 'node_id=shrimp-node05 boot_id=q sensor=PUMP2_ATLAS_PMP cycle=1 UTC=UNSYNCED seq=1 pump_on=0 motor_V=0.00 COMM=OK QC=UNVALIDATED'
        self.assertEqual(self.store.ingest('shrimp-node05', pump2), 4)  # absent parameters are stored as NULL rows, never 0

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


    def test_control_page_requires_login_and_monitoring_stays_public(self):
        import pump_ctl

        def call(root, path, body=None, cookie=None, kind='application/json'):
            headers = {'Content-Type': kind} if body is not None else {}
            if cookie:
                headers['Cookie'] = f'pump_session={cookie}'
            request = Request(root + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
            try:
                with urlopen(request) as response:
                    return response.status, json.load(response), response.headers.get('Set-Cookie')
            except HTTPError as error:
                return error.code, json.load(error), error.headers.get('Set-Cookie')

        def serve(pump):
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(self.store, Camera(), Network('lo'), pump=pump))
            threading.Thread(target=server.serve_forever, daemon=True).start()
            return server, f'http://127.0.0.1:{server.server_port}'

        server, root = serve(None)
        try:
            self.assertEqual(call(root, '/api/session')[1]['reason'], 'NOT_ENABLED')
            self.assertEqual(call(root, '/api/login', {'username': 'li', 'password': 'x'})[0], 403)
            self.assertEqual(call(root, '/api/control', {'device': 'pump1', 'action': 'stop'})[0], 403)
            with urlopen(root + '/control') as response:
                self.assertIn('操作员登录', response.read().decode())
            with urlopen(root + '/control/en') as response:
                self.assertIn('OPERATOR LOGIN', response.read().decode())
            self.assertEqual(call(root, '/api/status')[0], 200)
        finally:
            server.shutdown(); server.server_close()

        users = Path(self.temp.name) / 'users.json'
        control = pump_ctl.WebControl(self.store.path, None, users)
        sent = []
        control.run = lambda device, command, name: sent.append((device, command, name)) or {'result': 'OK', 'reply': 'NONE', 'target_mL_min': '50.00'}
        server, root = serve(control)
        try:
            self.assertEqual(call(root, '/api/session')[1]['reason'], 'NO_USERS')
            self.assertEqual(call(root, '/api/login', {'username': 'li', 'password': 'correct horse'})[0], 403)
            for name, password in [('li hy', 'correct horse'), ('li', 'short'), ('x' * 21, 'correct horse')]:
                with self.assertRaises(ValueError):
                    pump_ctl.add_user(users, name, password)
            pump_ctl.add_user(users, 'li', 'correct horse')
            self.assertEqual(oct(users.stat().st_mode & 0o777), '0o600')
            self.assertNotIn('correct horse', users.read_text())
            self.assertEqual(call(root, '/api/control', {'device': 'pump1', 'action': 'stop'})[0], 401)
            self.assertEqual(call(root, '/api/control/events')[0], 401)
            self.assertEqual(call(root, '/api/login', {'username': 'li', 'password': 'wrong password'})[0], 401)
            self.assertEqual(call(root, '/api/login', {'username': 'nobody', 'password': 'correct horse'})[0], 401)
            status, data, cookie = call(root, '/api/login', {'username': 'li', 'password': 'correct horse'})
            self.assertEqual((status, data['user']), (200, 'li'))
            self.assertIn('HttpOnly', cookie)
            self.assertIn('SameSite=Strict', cookie)
            token = cookie.split(';')[0].split('=', 1)[1]
            session = call(root, '/api/session', cookie=token)[1]
            self.assertEqual(session['user'], 'li')
            self.assertEqual([(d['id'], d['name'], d['kind']) for d in session['devices']], [('pump1', '泵 1', 'pump'), ('pump2', '泵 2', 'pump')])
            self.assertEqual(call(root, '/api/control', {'device': 'pump1', 'action': 'start', 'rate': 50}, token, 'text/plain')[0], 415)
            for body in ({'device': 'pump1', 'action': 'start', 'rate': 500}, {'device': 'pump1', 'action': 'start', 'rate': 'nan'},
                         {'device': 'pump1', 'action': 'dispense'}, {'device': 'pump1', 'action': 'start'},
                         {'device': 'pump9', 'action': 'stop'}, {'action': 'stop'}, {'device': ['pump1'], 'action': 'stop'}):
                self.assertEqual(call(root, '/api/control', body, token)[0], 400, body)
            self.assertEqual(call(root, '/api/control', {'device': 'pump1', 'action': 'start', 'rate': 50}, token)[1]['result'], 'OK')
            self.assertEqual(call(root, '/api/control', {'device': 'pump1', 'action': 'stop'}, token)[1]['command'], 'X')
            self.assertEqual(call(root, '/api/control', {'device': 'pump2', 'action': 'stop'}, token)[1]['command'], 'X')
            self.assertEqual(sent, [('pump1', 'DC,50.00,*', 'li'), ('pump1', 'X', 'li'), ('pump2', 'X', 'li')])
            self.assertEqual(call(root, '/api/control/events', cookie=token)[0], 200)
            self.assertEqual(call(root, '/api/control', {'device': 'pump1', 'action': 'stop'}, 'forged-token')[0], 401)
            self.assertIn('Max-Age=0', call(root, '/api/logout', {}, token)[2])
            self.assertEqual(call(root, '/api/control', {'device': 'pump1', 'action': 'stop'}, token)[0], 401)
            # Removing an account ends its live session at the next request.
            token = call(root, '/api/login', {'username': 'li', 'password': 'correct horse'})[2].split(';')[0].split('=', 1)[1]
            pump_ctl.add_user(users, 'other', 'another pass')
            remaining = pump_ctl.load_users(users); remaining.pop('li'); pump_ctl.save_users(users, remaining)
            self.assertIsNone(call(root, '/api/session', cookie=token)[1]['user'])
            # Five wrong passwords lock the account name even for the right password.
            pump_ctl.add_user(users, 'li', 'correct horse')
            for _ in range(5):
                self.assertEqual(call(root, '/api/login', {'username': 'li', 'password': 'wrong password'})[0], 401)
            self.assertEqual(call(root, '/api/login', {'username': 'li', 'password': 'correct horse'})[0], 429)
            self.assertEqual(len(sent), 3)
        finally:
            server.shutdown(); server.server_close()

if __name__ == '__main__':
    unittest.main()
