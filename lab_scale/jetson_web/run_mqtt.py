#!/usr/bin/env python3
"""Run a foreground broker/receiver pair; Ctrl+C stops both. No auto-start changes."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT.parents[1] / '.codex-build/runtime'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=str(ROOT/'data/measurements.sqlite3'))
    args = parser.parse_args()
    config = ROOT/'data/mqtt/mosquitto.conf'
    if not config.exists():
        raise SystemExit('Run prepare_mqtt.py --host <verified lab Ethernet IP> first.')
    binary = shutil.which('mosquitto') or str(RUNTIME/'usr/sbin/mosquitto')
    env = dict(os.environ, LD_LIBRARY_PATH=str(RUNTIME/'usr/lib/aarch64-linux-gnu'))
    broker = subprocess.Popen([binary, '-c', str(config)], env=env)
    receiver = None
    try:
        time.sleep(.5)
        if broker.poll() is not None:
            raise SystemExit('Broker failed to start; check address/port/configuration.')
        receiver = subprocess.Popen([sys.executable, str(ROOT/'mqtt_receiver.py'), '--db', str(Path(args.db).resolve())])
        print('MQTT broker and receiver running. Ctrl+C stops both; no firmware was uploaded.', flush=True)
        while broker.poll() is None and receiver.poll() is None:
            time.sleep(.5)
        raise SystemExit('A MQTT process stopped. Inspect its terminal output before restarting.')
    except KeyboardInterrupt:
        pass
    finally:
        for process in (receiver, broker):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()


if __name__ == '__main__':
    main()
