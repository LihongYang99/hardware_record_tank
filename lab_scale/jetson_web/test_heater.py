import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from pathlib import Path
import tempfile
import time
import unittest
from server import Camera, Network, Store, handler_for
import pump_ctl
import heater_ctl
from heater_ctl import decide, water_temperature


def row(sensor, value, age=0.0, qc='UNVALIDATED', now=1000.0, transport='0'):
    return {'sensor_id': sensor, 'parameter': 'temperature_C', 'value': value, 'qc_flag': qc,
            'received_epoch': now - age, 'metadata': json.dumps({'transport_age_ms': transport})}


class HeaterTests(unittest.TestCase):
    def test_water_temperature_is_the_mean_of_two_fresh_valid_probes(self):
        ok = [row('DO_SEN0681', 14.0), row('TURB_SEN0710', 15.0)]
        self.assertEqual(water_temperature(ok, 1000.0)[:2], (14.5, 'OK'))
        cases = {'NO_DATA:TURB_SEN0710': [row('DO_SEN0681', 14.0)],
                 'NO_DATA:DO_SEN0681': [row('DO_SEN0681', None, qc='COMMUNICATION_ERROR'), row('TURB_SEN0710', 15.0)],
                 'STALE:DO_SEN0681': [row('DO_SEN0681', 14.0, age=31), row('TURB_SEN0710', 15.0)],
                 'STALE:TURB_SEN0710': [row('DO_SEN0681', 14.0), row('TURB_SEN0710', 15.0, transport='40000')],
                 'IMPLAUSIBLE:TURB_SEN0710': [row('DO_SEN0681', 14.0), row('TURB_SEN0710', 45.0)],
                 'SOURCES_DISAGREE': [row('DO_SEN0681', 14.0), row('TURB_SEN0710', 17.5)]}
        for reason, rows in cases.items():
            self.assertEqual(water_temperature(rows, 1000.0)[:2], (None, reason))

    def test_decide_heats_only_below_setpoint_with_hysteresis_and_fails_off(self):
        self.assertEqual(decide(True, 15.0, 14.9, False), (True, 'BELOW_SETPOINT'))
        self.assertEqual(decide(True, 15.0, 15.2, True), (True, 'HOLD'))
        self.assertEqual(decide(True, 15.0, 15.2, False), (False, 'HOLD'))
        self.assertEqual(decide(True, 15.0, 15.5, True), (False, 'AT_SETPOINT'))
        self.assertEqual(decide(False, 15.0, 10.0, True), (False, 'DISABLED'))
        self.assertEqual(decide(True, None, 10.0, True), (False, 'NO_SETPOINT'))
        self.assertEqual(decide(True, 15.0, None, True, 'STALE:DO_SEN0681'), (False, 'STALE:DO_SEN0681'))

    def test_thermostat_publishes_repeats_on_and_logs_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            store, sent = Store(Path(temp) / 'db.sqlite3'), []
            def temps(do, turb, seq):
                for node, sensor, value in (('shrimp-node01', 'DO_SEN0681', f'DO_mg_L=8 saturation_pct=90 temperature_C={do}'),
                                            ('shrimp-node06', 'TURB_SEN0710', f'turbidity_NTU=3 temperature_C={turb}')):
                    store.ingest(node, f'node_id={node} boot_id=b sensor={sensor} seq={seq} {value} COMM=OK QC=UNVALIDATED transport_age_ms=0')
            thermostat = heater_ctl.Thermostat(store, None, lambda conn, payload, topic: sent.append((topic, payload.split(' cmd=')[1])))
            temps(14.0, 14.4, 1)
            now = time.time()
            thermostat.step(now)
            self.assertEqual(sent[-1], (heater_ctl.TOPIC, 'HEAT,OFF'))  # not enabled yet
            store.put_setting('heater:setpoint', 15.0, 'shrimp-node07', 'web-li', 'HEATER_SETPOINT,15.0')
            store.put_setting('heater:enabled', 1, 'shrimp-node07', 'web-li', 'HEATER_AUTO_ON')
            thermostat.step(now + 1)
            self.assertEqual(sent[-1][1], 'HEAT,ON')
            self.assertEqual(thermostat.snapshot()['temperature_C'], 14.2)
            count = len(sent)
            thermostat.step(now + 5)
            self.assertEqual(len(sent), count)              # no repeat before REFRESH_S
            thermostat.step(now + 1 + heater_ctl.REFRESH_S)
            self.assertEqual(sent[-1][1], 'HEAT,ON')        # dead-man refresh
            temps(15.6, 15.6, 2)
            thermostat.step(time.time())
            self.assertEqual((sent[-1][1], thermostat.snapshot()['reason']), ('HEAT,OFF', 'AT_SETPOINT'))
            import sqlite3
            with sqlite3.connect(store.path) as db:
                self.assertEqual([c for (c,) in db.execute("SELECT command FROM operator_event WHERE operator='thermostat' ORDER BY id")],
                                 ['HEAT,OFF', 'HEAT,ON', 'HEAT,OFF'])
            def broken(*a):
                raise ConnectionError('down')
            thermostat.publish = broken
            store.put_setting('heater:enabled', 0, 'shrimp-node07', 'web-li', 'HEATER_AUTO_OFF')
            thermostat.step(time.time() + 100)
            self.assertEqual(thermostat.snapshot()['error'], 'BROKER_UNAVAILABLE')

    def test_heater_api_requires_login_validates_and_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp) / 'db.sqlite3')
            users = Path(temp) / 'users.json'
            pump_ctl.add_user(users, 'li', 'correct horse')
            heater = heater_ctl.Thermostat(store, None, lambda *a: None)
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(store, Camera(), Network('lo'),
                                         pump=pump_ctl.WebControl(store.path, None, users), heater=heater))
            threading.Thread(target=server.serve_forever, daemon=True).start()
            root = f'http://127.0.0.1:{server.server_port}'
            def call(path, body, cookie=None):
                headers = {'Content-Type': 'application/json'} | ({'Cookie': f'pump_session={cookie}'} if cookie else {})
                try:
                    with urlopen(Request(root + path, json.dumps(body).encode(), headers)) as r:
                        return r.status, json.load(r), r.headers.get('Set-Cookie')
                except HTTPError as e:
                    return e.code, json.load(e), None
            try:
                self.assertEqual(call('/api/heater', {'setpoint': 15})[0], 401)
                token = call('/api/login', {'username': 'li', 'password': 'correct horse'})[2].split(';')[0].split('=', 1)[1]
                for body in ({}, {'setpoint': 40}, {'setpoint': 'x'}, {'setpoint': True}, {'setpoint': float('nan')}, {'enabled': 'yes'},
                             {'enabled': True}):  # last one: no setpoint stored yet
                    self.assertEqual(call('/api/heater', body, token)[0], 400, body)
                self.assertEqual(call('/api/heater', {'setpoint': 15.04, 'enabled': True}, token)[0], 200)
                self.assertEqual(store.settings()['heater:setpoint'], 15.0)
                self.assertEqual(store.settings()['heater:enabled'], 1)
                self.assertTrue(heater.wake.is_set())
                import sqlite3
                with sqlite3.connect(store.path) as db:
                    self.assertEqual(db.execute("SELECT operator, command FROM operator_event ORDER BY id").fetchall(),
                                     [('web-li', 'HEATER_SETPOINT,15.0'), ('web-li', 'HEATER_AUTO_ON')])
            finally:
                server.shutdown(); server.server_close()


if __name__ == '__main__':
    unittest.main()
