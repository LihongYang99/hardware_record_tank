# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Binding rules (from AGENTS.md — read it)

- Before **any** engineering decision (hardware, wiring, sensor config, firmware, software, Pi/database/Jetson, purchasing) read `SPEC.md` (binding spec) and `GOAL.md` (current objective) in full. If either is missing or conflicts with the request, stop and report; do not invent requirements.
- Do not silently change a sensor model, supply voltage, interface, pin/wiring, or safety boundary. Flag conflicts with SPEC and propose a revision instead.
- Never invent voltages, wire colors, pinouts, baud rates, Modbus registers, model numbers, ratings, fittings or prices. Unverified external facts are marked `NOT VERIFIED`. Hardware status labels: LOCKED / RECOMMENDED / OPTIONAL / VERIFY BEFORE PURCHASE / QUOTE REQUIRED / REJECTED (never LOCKED if unresolved).
- Data integrity: preserve raw lines, timestamps, sequence numbers and QC state. Invalid/missing readings are stored as NULL with a QC flag, **never zero**, and never carry over the previous value. Never label a timestamp UTC/SYNCED unless a trusted UTC source actually exists (none exists yet: `UTC=UNSYNCED`, `sample_timestamp_utc` is NULL).
- Priority order: scientific validity > electrical safety > data integrity > reliability > maintainability > modularity > expandability > cost.
- Formal milestone: Sensor → ESP32 → UTC → Wi-Fi → MQTT → **Raspberry Pi** → DB → dashboard. The Jetson in `lab_scale/jetson_web` is a *temporary* lab gateway; do not let Jetson/ML work displace the Pi architecture.
- Never flash an ESP32 without explicit user confirmation of the target board (MAC via `/dev/serial/by-id/`) and a flash read-back backup. `build_node1.py` deliberately has no upload option.

Documentation is mostly Chinese (with `docs/phase1/` in English + `zh-CN/`). `SPEC.md`/`GOAL.md`/`DECISIONS.md` hold the formal design; `lab_scale/` records actual bench state. When they differ, don't treat historical planning docs as current hardware state.

## Repository layout (big picture)

- `SPEC.md`, `GOAL.md`, `DECISIONS.md`, `docs/phase1/` — formal design, decision log, BOM/power/wiring/bypass planning.
- `lab_scale/` — bench prototype. Each node dir (`Node-1`, `Node-2`, `camera_node`) keeps `README/HARDWARE/WIRING/COMMUNICATION/PROGRESS.md` + `script/` (Arduino sketches) + `tests/`. Debug history goes in each node's `PROGRESS.md` (no sessions dir); repo reorganizations go in `lab_scale/CHANGELOG.md`.
- `lab_scale/jetson_web/` — gateway: Mosquitto broker, MQTT receiver, SQLite, bilingual dashboard, camera preview.
- `jetson_setting/` — Jetson handover and remote access (school Cisco VPN + SSH port-forward; third-party tunnels like Tailscale are not allowed on campus).
- `tank_scale/` — placeholder for future real deployment.
- `.codex-build/` (git-ignored) — arduino-cli, ESP32 core 3.3.11, unpacked Mosquitto 2.0.11 / Paho 1.5.1 runtime, build outputs, and pre-flash backups `node*-backup/`.

## Data path and architecture

**Firmware** (ESP32-S3 N16R8, Arduino). Current on-board sketches: `Node-1/script/DO_ORP_MQTT` (DFRobot SEN0681 DO + SEN0709 ORP, Modbus RTU over UART, 4800 8N1) and `Node-2/script/Atlas_EC_pH_MQTT` (Atlas EZO-EC + EZO-pH over UART). `DO_ORP_WiFi` / `Atlas_EC_pH_UART` are the older USB-serial-only versions kept for rollback. All `.h` files in a sketch folder compile together.
- Sensor headers (`Protocol.h`, `BenchChannel.h`, `AtlasChannel.h`, `AtlasParse.h`) are byte-identical between old and MQTT sketches; keep it that way unless intentionally changing acquisition. `Telemetry.h` is the MQTT-only addition.
- Each node emits one `key=value` text line per event (fields documented in `lab_scale/README.md` §4: `node_id`, `sensor`, `boot_id`, `seq`, `cycle`, uptimes, `raw`, `COMM`, `QC`, …) plus transport fields `transport_boot_id` (16 hex), `transport_seq`, `transport_age_ms`, `network_buffered`.
- `Telemetry.h`: a FreeRTOS worker owns the MQTT client; bounded RAM queue of 64 records (lost on power-off; overflow counted as `mqtt_lost`). It publishes to `shrimp/lab/<node>/records` and keeps the head record until an **application ACK** `<transport_boot_id>:<transport_seq>` arrives on `shrimp/lab/<node>/ack` (retry every 5 s). MQTT PUBACK is *not* treated as delivery confirmation. LWT/status on `shrimp/lab/<node>/status`.
- Firmware checks the eFuse factory MAC and refuses to poll sensors on the wrong board (`event=WRONG_BOARD`).
- Credentials live in git-ignored `arduino_secrets.h` (template: `arduino_secrets.example.h`). Wi-Fi must be the lab router's 2.4 GHz SSID.

**Gateway** (`lab_scale/jetson_web`, system Python 3 standard library only; Paho and Mosquitto come from `.codex-build/runtime` if not installed system-wide; no pip/npm).
- `prepare_mqtt.py --host <lab IP>` writes `data/mqtt/` (credentials.json, hashed passwords, per-node ACL, mosquitto.conf). Re-running keeps existing passwords, because they are already flashed into nodes.
- `run_mqtt.py` supervises broker + `mqtt_receiver.py` together (SIGTERM/Ctrl+C stops both).
- `mqtt_receiver.py`: node identity comes from the topic (enforced by broker ACL). `accept_record` validates framing, duplicate keys, transport identity and node/boot consistency. Rejects are stored verbatim in `mqtt_rejected` with no ACK. Accepted records go through `Store.ingest`, and the ACK is published only after the SQLite commit.
- `server.py`: `Store` owns the schema (`raw_log`, `measurement` with UNIQUE(node, sensor, boot, seq, parameter), `issue` for sequence gaps/duplicates/out-of-order). It uses WAL mode. `NODES`/`SENSORS` dicts define allowed node↔sensor mappings and parameters/units. It serves a read-only HTTP UI/API (default :8080; Chinese `static/index.html`+`app.js`, English `/en` → `en.html`+`app_en.js`, shared API) plus a loopback-only `POST /ingest` port (:8766). It also runs a `Camera` GStreamer RTSP→JPEG preview thread (explicit H.264 pipeline; `uridecodebin` breaks on Jetson NVMM) and a `Network` interface monitor.
- STALE = no report within 15 s (including `transport_age_ms`). Error QC clears the current value instead of keeping the last good value.
- `.env` (from `.env.example`, git-ignored): `TANK_ID`, `EXPERIMENT_ID`, `SENSOR_LOCATION`, `CAMERA_RTSP_URI`. Leave the IDs empty rather than invent them. `camera_onvif.py` fills the RTSP URI via ONVIF, and the API never returns it.
- Adding a node or sensor means updating `NODES`/`SENSORS` in `server.py`, `MQTT_NODES` in `mqtt_receiver.py`, `NODES` in `prepare_mqtt.py`, the `SKETCHES` map in `build_node1.py`/`configure_node1.py`, and both frontends' labels.

## Code style: keep it concise, reach it by iterating

- Aim for the smallest code that fully does the job. No speculative abstractions, unused options, dead code, or duplicated logic. Match the existing terse style (standard library only, short functions).
- Work in a loop: write a minimal version → run the relevant tests (and a compile check for firmware) → simplify → rerun. Repeat until nothing more can be removed without losing behavior. Report what was tried and the final test output.
- Conciseness never overrides the binding rules. Keep QC flags, raw-line preservation, identity/sequence checks, ACK-after-commit, bounds checks and error handling even if they add lines. Don't drop a safety check to make code shorter.
- Firmware sensor headers shared with the rollback sketches stay byte-identical. Simplify `Telemetry.h`/`.ino` or gateway code instead, and only with passing host tests plus `build_node1.py --check`.

## Commands

Run all commands from the repo root unless noted.

```bash
# Gateway tests (14 tests; use temp DBs, never touch data/). One includes a real-broker test needing .codex-build/runtime.
python3 -m unittest discover -s lab_scale/jetson_web -v
# Single test (tests import siblings, so cd into the dir)
cd lab_scale/jetson_web && python3 -m unittest -v test_mqtt.MQTTTests.test_acl_isolates_each_node

# Firmware host tests (no ESP32 needed; README uses clang++, g++ also works).
# Note: these compile against the OLD sketch dirs. Sensor headers are identical, but Node-2 BenchLog.h differs in the MQTT sketch.
clang++ -std=c++11 -Wall -Wextra -I lab_scale/Node-1/script/DO_ORP_WiFi lab_scale/Node-1/tests/protocol_test.cpp -o /tmp/n1 && /tmp/n1
clang++ -std=c++11 -Wall -Wextra -fsanitize=address,undefined -I lab_scale/Node-2/tests lab_scale/Node-2/tests/test.cpp -o /tmp/n2 && /tmp/n2

# Firmware config + compile only (never uploads)
python3 lab_scale/jetson_web/configure_node1.py --node 1        # or: --node 2 --wifi-from-node1 (prompts for Wi-Fi; writes arduino_secrets.h)
python3 lab_scale/jetson_web/build_node1.py --node 1|2          # --check = template creds, output must NOT be flashed
```

Running the gateway on the Jetson (in `lab_scale/jetson_web`, no autostart):

```bash
sudo ip addr add 192.168.1.200/24 dev enP8p1s0   # camera subnet; redo after reboot/replug
nohup python3 -u run_mqtt.py > data/mqtt.log 2>&1 & echo $! > data/mqtt.pid
set -a; . ./.env; set +a
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 > data/server.log 2>&1 & echo $! > data/server.pid
kill "$(cat data/mqtt.pid)" "$(cat data/server.pid)"   # stop (verify PIDs first)
```

The debug setup is separate from production. The VS Code launch config "Jetson 网页：本机调试" serves :8081 / ingest :8767 against `data/debug/measurements.sqlite3`, and the task "MQTT：接收至网页调试数据库" runs `run_mqtt.py --db data/debug/...`. Broker/receiver and server must point at the **same** SQLite file. Never feed test or replay data into the live `data/measurements.sqlite3`. Back up the whole `data/` dir (including WAL) only while services are stopped.

## Known state / gaps (as of 2026-09-27)

All readings are `UNVALIDATED` (uncalibrated) and UTC is unsynced (dashboard time = Jetson receive time). Node-2 EC reads 0 because the module is configured K=1 but the probe is K10. There is no persistent buffering on nodes, no autostart, and no disk quota or backup on the gateway. IPs are DHCP, so verify device identity by MAC. The camera (freshwater model) is not approved for saline deployment.
