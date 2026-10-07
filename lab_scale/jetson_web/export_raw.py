#!/usr/bin/env python3
"""Copy raw node lines from the gateway database into Raw_data/<node folder>/<sensor>/<UTC date>.csv.

Read-only on the database. Lines are written verbatim (no parsing, no Excel escaping) with the gateway receive
time; lines without a known sensor (health, Wi-Fi, boot) go to <node folder>/node_log/. A finished UTC day is
written once and listed in Raw_data/exported_days.txt; today's (incomplete) day is rewritten on every run.
"""
import argparse
import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from server import NODES, SENSORS, fields

ROOT = Path(__file__).resolve().parent
FOLDERS = {'shrimp-node01': 'Node-1-ORP-DO', 'shrimp-node02': 'Node-2-pH-Conductivity', 'shrimp-node04': 'Pump-1',
           'shrimp-node05': 'Pump-2', 'shrimp-node06': 'Node-6-Turbidity'}
assert set(FOLDERS) == set(NODES), 'every node needs a Raw_data folder'


def export(db_path, out, everything=False):
    out = Path(out)
    for sensor, (node, _, _) in SENSORS.items():  # the folder tree exists even before a sensor has data
        (out / FOLDERS[node] / sensor).mkdir(parents=True, exist_ok=True)
    for node in NODES:
        (out / FOLDERS[node] / 'node_log').mkdir(parents=True, exist_ok=True)
    manifest = out / 'exported_days.txt'
    done = set() if everything or not manifest.exists() else set(manifest.read_text().split())
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    files, written = {}, {}
    db = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    try:
        for raw_id, received, node, keep, line in db.execute('SELECT id, received_utc, node_id, keep, line FROM raw_log ORDER BY id'):
            day = received[:10]
            if day in done or node not in FOLDERS:
                continue
            sensor = fields(line).get('sensor')
            path = out / FOLDERS[node] / (sensor if SENSORS.get(sensor, ('',))[0] == node else 'node_log') / f'{day}.csv'
            if path not in files:
                handle = open(path.with_suffix('.csv.tmp'), 'w', newline='', encoding='utf-8')
                files[path] = (handle, csv.writer(handle))
                files[path][1].writerow(['raw_id', 'received_utc_gateway', 'keep', 'line'])
                written[path] = 0
            files[path][1].writerow([raw_id, received, keep, line])
            written[path] += 1
    finally:
        db.close()
        for path, (handle, _) in files.items():
            handle.close()
            os.replace(path.with_suffix('.csv.tmp'), path)  # a reader never sees a half-written file
    days = {p.stem for p in written}
    manifest.write_text(''.join(f'{d}\n' for d in sorted(done | {d for d in days if d < today})))
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=str(ROOT / 'data' / 'measurements.sqlite3'))
    parser.add_argument('--out', default=str(ROOT.parents[1] / 'Raw_data'))
    parser.add_argument('--all', action='store_true', help='rewrite every day, including ones already exported')
    args = parser.parse_args()
    written = export(args.db, args.out, args.all)
    print(f'{len(written)} files, {sum(written.values())} lines written under {args.out}')


if __name__ == '__main__':
    main()
