#!/usr/bin/env python3
"""Compile only. There is deliberately no upload option."""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SKETCHES = {'1': ROOT / 'lab_scale/Node-1/script/DO_ORP_MQTT',
            '2': ROOT / 'lab_scale/Node-2/script/Atlas_EC_pH_MQTT'}
BUILD = ROOT / '.codex-build'
FQBN = 'esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node', choices=SKETCHES, default='1', help='Node number (default 1)')
    parser.add_argument('--check', action='store_true', help='Use empty template credentials; output must never be flashed')
    args = parser.parse_args()
    if not (BUILD / 'arduino-data/packages/esp32/hardware/esp32/3.3.11').exists():
        raise SystemExit('ESP32 core 3.3.11 is not installed in .codex-build yet.')
    sketch = SKETCHES[args.node]
    tag = f'node{args.node}-check' if args.check else f'node{args.node}-configured'
    stage = BUILD / tag / sketch.name
    stage.mkdir(parents=True, exist_ok=True)
    for path in sketch.iterdir():
        if path.suffix in ('.ino','.h') and path.name != 'arduino_secrets.h':
            shutil.copy2(path,stage/path.name)
    credentials = sketch / ('arduino_secrets.example.h' if args.check else 'arduino_secrets.h')
    if not credentials.exists():
        raise SystemExit(f'Run configure_node1.py --node {args.node} in your terminal first; no credentials were found.')
    shutil.copy2(credentials,stage/'arduino_secrets.h')
    (stage/'arduino_secrets.h').chmod(0o600)
    result = subprocess.run([str(BUILD/'tools/arduino-cli'),'--config-file',str(BUILD/'arduino-cli.yaml'),
                            'compile','--fqbn',FQBN,'--jobs','2','--build-path',str(BUILD/tag/'output'),str(stage)],cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)
    print('Compile passed. NO upload was performed. ' + ('Template credentials: DO NOT FLASH this build.' if args.check else 'Target confirmation and firmware backup are required before upload.'))


if __name__ == '__main__':
    main()
