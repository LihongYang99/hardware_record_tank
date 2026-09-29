#!/usr/bin/env python3
"""Generate local broker credentials/config. Does not install, launch, or flash."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
NODES = ('shrimp-node01', 'shrimp-node02', 'shrimp-node04', 'shrimp-node05')
# Only these nodes accept operator commands, and only the pump-operator account may send them.
COMMAND_NODES = ('shrimp-node04', 'shrimp-node05')


def prepare(directory, host):
    ipaddress.IPv4Address(host)
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    credentials_file = directory / 'credentials.json'
    credentials = json.loads(credentials_file.read_text()) if credentials_file.exists() else {}
    # Keep existing passwords (already flashed into nodes); only add missing accounts.
    for name in (*NODES, 'jetson-receiver', 'pump-operator'):
        credentials.setdefault(name, secrets.token_hex(24))
    credentials_file.write_text(json.dumps(credentials))
    passwd = shutil.which('mosquitto_passwd') or str(ROOT.parents[1] / '.codex-build/runtime/usr/bin/mosquitto_passwd')
    password_file = directory / 'passwords'
    password_file.write_text(''.join(f'{name}:{password}\n' for name, password in credentials.items()))
    password_file.chmod(0o600)
    # Official utility hashes the private file in place; passwords never enter process arguments.
    subprocess.run([passwd, '-U', str(password_file)], check=True, capture_output=True)
    acl = ''.join(f'user {n}\ntopic write shrimp/lab/{n}/records\ntopic write shrimp/lab/{n}/status\ntopic read shrimp/lab/{n}/ack\n'
                  + (f'topic read shrimp/lab/{n}/cmd\n' if n in COMMAND_NODES else '') for n in NODES)
    acl += 'user jetson-receiver\n' + ''.join(f'topic read shrimp/lab/{n}/records\ntopic read shrimp/lab/{n}/status\ntopic write shrimp/lab/{n}/ack\n' for n in NODES)
    acl += 'user pump-operator\n' + ''.join(f'topic write shrimp/lab/{n}/cmd\n' for n in COMMAND_NODES)
    (directory / 'acl').write_text(acl)
    (directory / 'mosquitto.conf').write_text(f'''listener 1883 127.0.0.1
listener 1883 {host}
allow_anonymous false
password_file {directory / 'passwords'}
acl_file {directory / 'acl'}
persistence true
persistence_location {directory}/
autosave_interval 10
max_queued_messages 1000
message_size_limit 8192
log_dest stdout
log_type error
log_type warning
connection_messages true
''')
    for path in directory.iterdir():
        if path.is_file():
            path.chmod(0o600)
    return credentials


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True, help='Verified laboratory Ethernet IPv4 address')
    args = parser.parse_args()
    os.umask(0o077)
    prepare(ROOT / 'data/mqtt', args.host)
    print('Private broker configuration ready under data/mqtt; passwords were not printed.')
