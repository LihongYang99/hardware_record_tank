#!/usr/bin/env python3
"""Ask the camera itself (ONVIF GetStreamUri) for its RTSP URI and store it in the private .env.

The URI can embed camera credentials, so it is never printed; only its structure is shown.
No camera settings are changed: only ONVIF read requests are sent.
"""
import argparse
import html
import os
from pathlib import Path
import re
import shlex
import urllib.request

ROOT = Path(__file__).resolve().parent
SOAP = ('<?xml version="1.0" encoding="UTF-8"?><s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:trt="http://www.onvif.org/ver10/media/wsdl" xmlns:tt="http://www.onvif.org/ver10/schema">'
        '<s:Body>{}</s:Body></s:Envelope>')


def call(url, body):
    request = urllib.request.Request(url, SOAP.format(body).encode(), {'Content-Type': 'application/soap+xml; charset=utf-8'})
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.read().decode('utf-8', errors='replace')


def stream_uri(media_url, profile):
    reply = call(media_url, '<trt:GetStreamUri><trt:StreamSetup><tt:Stream>RTP-Unicast</tt:Stream><tt:Transport>'
                            f'<tt:Protocol>RTSP</tt:Protocol></tt:Transport></trt:StreamSetup><trt:ProfileToken>{profile}'
                            '</trt:ProfileToken></trt:GetStreamUri>')
    match = re.search(r'<tt:Uri>([^<]+)<', reply)
    if not match:
        raise SystemExit('Camera did not return a stream URI (login may be required).')
    return html.unescape(match.group(1))


def update_env(path, key, value):
    lines = path.read_text().splitlines() if path.exists() else []
    lines = [line for line in lines if not line.startswith(key + '=')] + [f'{key}={shlex.quote(value)}']
    path.write_text('\n'.join(lines) + '\n')
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--media', default='http://192.168.1.88:8899/onvif/media_service',
                        help='ONVIF media service address reported by the camera (GetCapabilities)')
    parser.add_argument('--profile', default='001', help='ONVIF profile token; 001 = subStream00 704x576 H264')
    parser.add_argument('--env', default=str(ROOT / '.env'))
    args = parser.parse_args()
    os.umask(0o077)
    uri = stream_uri(args.media, args.profile)
    if not uri.startswith('rtsp://'):
        raise SystemExit('Unexpected URI scheme; nothing saved.')
    update_env(Path(args.env), 'CAMERA_RTSP_URI', uri)
    shape = re.sub(r'=([^&?]*)', lambda m: '=<empty>' if not m.group(1) else '=<set>', uri)
    print(f'Saved camera-reported URI for profile {args.profile} to {args.env} (0600): {shape}')


if __name__ == '__main__':
    main()
