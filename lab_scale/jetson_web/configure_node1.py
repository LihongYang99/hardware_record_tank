#!/usr/bin/env python3
"""Prompt locally for Wi-Fi secrets; never prints passwords or flashes hardware."""
from getpass import getpass
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT.parent / 'Node-1/script/DO_ORP_MQTT/arduino_secrets.h'


def main():
    os.umask(0o077)
    if TARGET.exists():
        answer = input('本地配置已存在。输入 UPDATE 才会替换，其他输入退出：').strip()
        if answer != 'UPDATE':
            return
    ssid = input('实验室路由器 Wi-Fi 名称（不是学校 Wi-Fi）：').strip()
    password = getpass('实验室 Wi-Fi 密码（输入不显示）：')
    if not ssid or not password:
        raise SystemExit('未填写完整，未保存。')
    credentials = json.loads((ROOT / 'data/mqtt/credentials.json').read_text())
    values = {'WIFI_SSID':ssid, 'WIFI_PASSWORD':password, 'MQTT_HOST':'192.168.88.249',
              'MQTT_USER':'shrimp-node01', 'MQTT_PASSWORD':credentials['shrimp-node01']}
    text = '#pragma once\n// Private local configuration. Never commit.\n'
    text += ''.join(f'const char* {key} = {json.dumps(value,ensure_ascii=False)};\n' for key,value in values.items())
    text += 'const int MQTT_PORT = 1883;\n'
    TARGET.write_text(text)
    TARGET.chmod(0o600)
    print('Node 1 本地配置已保存。未编译、未烧录；密码未输出。')


if __name__ == '__main__':
    main()
