#!/usr/bin/env python3
"""Prompt locally for Wi-Fi secrets; never prints passwords or flashes hardware."""
from getpass import getpass
import json
import argparse
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
TARGETS = {'1': ROOT.parent / 'Node-1/script/DO_ORP_MQTT/arduino_secrets.h',
           '2': ROOT.parent / 'Node-2/script/Atlas_EC_pH_MQTT/arduino_secrets.h',
           '4': ROOT.parent / 'pump-node-1/script/PMP_MQTT/arduino_secrets.h',
           '5': ROOT.parent / 'pump-node-2/script/PMP_MQTT/arduino_secrets.h',
           '6': ROOT.parent / 'Node-6/script/TURB_MQTT/arduino_secrets.h'}


def node1_wifi():
    """Reuse Node 1's verified lab Wi-Fi settings; values are never printed."""
    text = TARGETS['1'].read_text()
    ssid, password = (re.search(rf'{key} = (".*");', text) for key in ('WIFI_SSID', 'WIFI_PASSWORD'))
    if not ssid or not password:
        raise SystemExit('Node 1 本地配置中没有完整的 Wi-Fi 设置。')
    return json.loads(ssid.group(1)), json.loads(password.group(1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node', choices=TARGETS, default='1', help='Node number: 1, 2, or 4 = pump-node-1, 5 = pump-node-2, 6 = turbidity (default 1)')
    parser.add_argument('--wifi-from-node1', action='store_true', help='Copy the lab Wi-Fi SSID/password already verified on Node 1')
    args = parser.parse_args()
    node = f'shrimp-node0{args.node}'
    TARGET = TARGETS[args.node]
    os.umask(0o077)
    if TARGET.exists():
        answer = input('本地配置已存在。输入 UPDATE 才会替换，其他输入退出：').strip()
        if answer != 'UPDATE':
            return
    if args.wifi_from_node1:
        ssid, password = node1_wifi()
    else:
        ssid = input('实验室路由器 2.4 GHz Wi-Fi 名称（不是学校 Wi-Fi）：').strip()
        password = getpass('实验室 Wi-Fi 密码（输入不显示）：')
    if not ssid or not password:
        raise SystemExit('未填写完整，未保存。')
    credentials = json.loads((ROOT / 'data/mqtt/credentials.json').read_text())
    values = {'WIFI_SSID':ssid, 'WIFI_PASSWORD':password, 'MQTT_HOST':'192.168.88.249',
              'MQTT_USER':node, 'MQTT_PASSWORD':credentials[node]}
    text = '#pragma once\n// Private local configuration. Never commit.\n'
    text += ''.join(f'const char* {key} = {json.dumps(value,ensure_ascii=False)};\n' for key,value in values.items())
    text += 'const int MQTT_PORT = 1883;\n'
    TARGET.write_text(text)
    TARGET.chmod(0o600)
    print(f'{node} 本地配置已保存。未编译、未烧录；密码未输出。')


if __name__ == '__main__':
    main()
