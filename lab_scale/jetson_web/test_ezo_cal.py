import itertools
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ezo_cal
from server import OPERATOR_EVENT_DDL, Store, fields, utc

NODE = 'shrimp-node02'
SEQ = itertools.count(1)


class EzoCalibrationTests(unittest.TestCase):
    """ezo_cal against a fake Node 2 that answers like the firmware (OPERATOR_DONE, READY, then a new reading)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / 'db.sqlite3')
        self.db = sqlite3.connect(self.store.path, timeout=15)
        self.k, self.cal, self.sent, self.refuse = '1.000', {'EC': '?CAL,0', 'PH': '?CAL,0'}, [], set()
        self.reading('EC', '0.000')
        self.reading('PH', '7.212')
        self.real_execute, ezo_cal.execute = ezo_cal.execute, self.execute

    def tearDown(self):
        ezo_cal.execute = self.real_execute
        self.db.close()
        self.temp.cleanup()

    def reading(self, prefix, value):
        if prefix == 'EC':
            line = (f'node_id={NODE} boot_id=b sensor=EC_ATLAS_EZO seq={next(SEQ)} cycle=1 UTC=UNSYNCED EC_uS_cm={value} salinity_PSU=0.000 '
                    f'K={self.k} compensation_setting_C=25.00 calibration_reply={self.cal["EC"]} COMM=OK QC=COMPENSATION_MISSING validation=UNVALIDATED')
        else:
            line = (f'node_id={NODE} boot_id=b sensor=PH_ATLAS_EZO seq={next(SEQ)} cycle=1 UTC=UNSYNCED pH={value} compensation_setting_C=25.00 '
                    f'calibration_reply={self.cal["PH"]} COMM=OK QC=COMPENSATION_MISSING validation=UNVALIDATED')
        self.store.ingest(NODE, line)

    def execute(self, db, conn, command, operator, note, timeout, node, topic):
        """Like pump_ctl.execute + the node: operator_event row, OPERATOR_DONE, and after a change READY + a reading."""
        prefix, cmd = command.split(':', 1)
        sensor = {'EC': 'EC_ATLAS_EZO', 'PH': 'PH_ATLAS_EZO'}[prefix]
        self.sent.append(command)
        cmd_id = str(time.time_ns())
        with db:
            db.execute(OPERATOR_EVENT_DDL)
            db.execute('INSERT INTO operator_event(sent_utc,node_id,cmd_id,operator,command,note) VALUES(?,?,?,?,?,?)', (utc(), node, cmd_id, operator, command, note))
        ok = cmd not in self.refuse
        if ok and cmd == 'K,10':
            self.k = '10.000'
        elif ok and cmd.startswith('Cal,') and '?' not in cmd:
            self.cal[prefix] = '?CAL,0' if cmd in ('Cal,clear', 'Cal,dry') or cmd.startswith('Cal,low,') and prefix == 'EC' else '?CAL,2' if prefix == 'EC' else '?CAL,1'
        reply = {'Cal,?': self.cal[prefix], 'K,?': f'?K,{self.k}', 'Slope,?': '?Slope,99.7,100.3,-0.89'}.get(cmd, 'NONE')
        line = f'node_id={NODE} boot_id=b sensor={sensor} uptime_ms=1 event=OPERATOR_DONE cmd_id={cmd_id} operator={operator} command={cmd} result={"OK" if ok else "ER"} reply={reply}'
        self.store.ingest(NODE, line)
        done_id = db.execute('SELECT MAX(id) FROM raw_log').fetchone()[0]
        if ok and '?' not in cmd:
            self.store.ingest(NODE, f'node_id={NODE} boot_id=b sensor={sensor} uptime_ms=2 event=READY seq=1 cycle=1')
            self.reading(prefix, '12880.000' if prefix == 'EC' else '7.000')
        with db:
            db.execute('UPDATE operator_event SET result_line=? WHERE cmd_id=?', (line, cmd_id))
        return cmd_id, done_id, fields(line)

    def test_commands_match_the_firmware_whitelist(self):
        self.assertEqual(ezo_cal.command('ec', 'low', '12880'), 'Cal,low,12880')
        self.assertEqual(ezo_cal.command('ec', 'high', 150000), 'Cal,high,150000')
        self.assertEqual(ezo_cal.command('ec', 'single', '12880.5'), 'Cal,12880.5')
        self.assertEqual(ezo_cal.command('ph', 'mid', '7'), 'Cal,mid,7.00')
        self.assertEqual(ezo_cal.command('ph', 'low', 4.01), 'Cal,low,4.01')
        self.assertEqual(ezo_cal.command('ec', 'k10'), 'K,10')
        for device, action, value in [('ec', 'low', '5'), ('ec', 'mid', '7'), ('ph', 'mid', '8'), ('ph', 'low', '6.5'), ('ph', 'high', 'inf'),
                                      ('ph', 'high', True), ('ec', 'k10', '1'), ('ph', 'k10', None), ('ec', 'Factory', None), ('ec', 'low', None)]:
            with self.assertRaises((ValueError, TypeError)):
                ezo_cal.command(device, action, value)

    def test_order_is_enforced_before_anything_is_sent(self):
        conn = None
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'dry', 'Cal,dry', 'li', 'air')['result'], 'K_NOT_10')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ph', 'low', 'Cal,low,4.00', 'li', 'pH 4')['result'], 'MID_FIRST')
        self.assertEqual(self.sent, [])
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'k10', 'K,10', 'li', 'K10 probe')['result'], 'OK')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'high', 'Cal,high,150000', 'li', 'x')['result'], 'LOW_FIRST')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'low', 'Cal,low,12880', 'li', 'x')['result'], 'DRY_FIRST')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'dry', 'Cal,dry', 'li', 'air')['result'], 'OK')
        # A refused step does not count as done.
        self.refuse.add('Cal,low,12880')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'low', 'Cal,low,12880', 'li', 'x')['result'], 'ER')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'high', 'Cal,high,150000', 'li', 'x')['result'], 'LOW_FIRST')
        self.refuse.clear()
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'low', 'Cal,low,12880', 'li', 'x')['result'], 'OK')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ec', 'high', 'Cal,high,150000', 'li', 'x')['result'], 'OK')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ph', 'mid', 'Cal,mid,7.00', 'li', 'pH 7')['result'], 'OK')
        self.assertEqual(ezo_cal.run(self.db, conn, 'ph', 'low', 'Cal,low,4.00', 'li', 'pH 4')['result'], 'OK')

    def test_calibration_record_has_standard_pre_and_post_response(self):
        out = ezo_cal.run(self.db, None, 'ph', 'mid', 'Cal,mid,7.00', 'li', 'pH 7.00 buffer lot 42, 22.4 C')
        self.assertEqual(out['result'], 'OK')
        self.assertEqual(out['pre'], '7.212')
        self.assertEqual(out['post'], {'Cal,?': '?CAL,1', 'Slope,?': '?Slope,99.7,100.3,-0.89', 'reading': '7.000'})
        self.assertEqual(self.sent, ['PH:Cal,mid,7.00', 'PH:Cal,?', 'PH:Slope,?'])
        note = self.db.execute("SELECT note FROM operator_event WHERE command='PH:Cal,mid,7.00'").fetchone()[0]
        self.assertEqual(note, 'pH 7.00 buffer lot 42, 22.4 C | pre: pH=7.212 cal=?CAL,0 | post: Cal,?=?CAL,1 Slope,?=?Slope,99.7,100.3,-0.89 reading=7.000')
        # Queries are sent as-is and change nothing.
        self.assertEqual(ezo_cal.run(self.db, None, 'ec', 'query:k', 'K,?', 'li', '')['reply'], '?K,1.000')


if __name__ == '__main__':
    unittest.main()
