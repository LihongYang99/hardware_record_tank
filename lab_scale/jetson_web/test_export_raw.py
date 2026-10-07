import csv
from pathlib import Path
import tempfile
import unittest
import time
from server import Camera, Store
import export_raw


class ExportRawTests(unittest.TestCase):
    def test_lines_go_verbatim_to_node_sensor_day_folders(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            store = Store(temp / 'db.sqlite3')
            orp = 'node_id=shrimp-node01 boot_id=b sensor=ORP_SEN0709 seq=1 ORP_mV=-5 temperature_C=23 COMM=OK QC=UNVALIDATED'
            store.ingest('shrimp-node01', orp)
            store.ingest('shrimp-node02', 'sensor=PH_ATLAS_EZO event=POLL_SKIPPED_NOT_READY cycle=1')
            store.ingest('shrimp-node06', 'node_id=shrimp-node06 boot_id=b event=HEALTH uptime_ms=1')
            written = export_raw.export(temp / 'db.sqlite3', temp / 'out')
            self.assertEqual({p.parent.relative_to(temp / 'out').as_posix() for p in written},
                             {'Node-1-ORP-DO/ORP_SEN0709', 'Node-2-pH-Conductivity/PH_ATLAS_EZO', 'Node-6-Turbidity/node_log'})
            self.assertTrue((temp / 'out/Pump-2/PUMP2_ATLAS_PMP').is_dir())  # tree exists before data does
            rows = list(csv.reader(open(next(p for p in written if 'ORP' in p.parts[-2]), encoding='utf-8')))
            self.assertEqual(rows[1][3], orp)  # verbatim, no spreadsheet escaping
            self.assertEqual(list((temp / 'out').rglob('*.tmp')), [])

    def test_camera_frame_saved_only_when_fresh(self):
        with tempfile.TemporaryDirectory() as temp:
            camera = Camera()
            self.assertIsNone(camera.save_frame(temp))  # no video yet
            camera.frame, camera.last_frame = b'\xff\xd8jpeg', 1790000000.0  # 2026-09-21T13:33:20Z, stale
            self.assertIsNone(camera.save_frame(temp))
            camera.last_frame = time.time()
            path = camera.save_frame(temp)
            self.assertEqual(path.read_bytes(), b'\xff\xd8jpeg')
            self.assertRegex(path.relative_to(temp).as_posix(), r'^\d{4}-\d\d-\d\d/\d{6}Z\.jpg$')
            self.assertEqual([p.name for p in Path(temp).rglob('*.tmp')], [])


if __name__ == '__main__':
    unittest.main()
