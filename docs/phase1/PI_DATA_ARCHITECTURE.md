# Raspberry Pi Real-Time and Data-Integrity Architecture

**Revision:** 2026-09-02  
**Role:** always-on Phase-1 gateway; Jetson-independent  
**Recommended resolution of OPEN-16:** Mosquitto + custom Python ingestion/QC + PostgreSQL + Grafana under Docker Compose, with chrony on the Pi host. This is **RECOMMENDED — REQUIRES PROMOTION**, not a silent decision-log change.

## 1. Stack decision

| Component | Selected role | Why |
|---|---|---|
| Raspberry Pi OS Lite 64-bit | Minimal host OS | Supported Pi base, low overhead; host owns clock, storage mount, firewall, and Docker. |
| chrony on host | UTC/NTP client and controlled LAN time server | Keeps container and gateway timestamps on one authoritative host clock; can serve ESP nodes on the sensor subnet. |
| Mosquitto 2.x | MQTT broker | Small, mature, persistent sessions, QoS 1, authentication/ACL, retained status/LWT. |
| Python ingestor/QC | Decode, validate, timestamp, deduplicate, transact, ACK, and flag | The domain logic is explicit/testable; no opaque low-code step in the required path. |
| PostgreSQL | Authoritative RAW/SYNCHRONIZED/DERIVED store | Exact payload bytes/JSONB, transactions, foreign keys, composite identity, calibration/events, robust duplicate/collision handling. |
| Grafana OSS | Dashboard and alert visualization | Built-in PostgreSQL data source; dashboards can be provisioned/versioned. |
| Docker Compose | Reproducible service lifecycle | Health checks, pinned images, volumes, restart policy, dependency readiness. |

### Alternatives not selected

- **InfluxDB:** good time-series query/retention tooling, but the project’s immutable raw payloads, relational calibration/events, transactional application ACK, and composite duplicate/collision audit are clearer in PostgreSQL. Running two authoritative databases would add failure modes.
- **Node-RED:** useful for prototyping, but not placed in the required ingestion/QC path. A versioned Python service gives deterministic tests, schema migrations, and transaction control.
- **Jetson Orin:** not needed for Phase 1. It may later read a documented Pi API/export; sensor firmware and core monitoring must work while Jetson is off.

Pin the current supported ARM64 image versions **and immutable digests** during deployment; record them in the release manifest. Do not write `latest` into the production Compose file. Apply version upgrades first to a copied dataset and pass the recovery suite.

Sources: [Mosquitto authentication/authorization](https://www.mosquitto.org/documentation/authentication-methods/), [Mosquitto configuration/persistence](https://www.mosquitto.org/man/mosquitto-conf-5.html), [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html), [PostgreSQL WAL/backup](https://www.postgresql.org/docs/current/continuous-archiving.html), [Grafana PostgreSQL data source](https://grafana.com/docs/grafana/latest/datasources/postgres/configure/), [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/), [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/).

## 2. Host and storage layout

The microSD contains the OS only. Mount a SMART-capable USB 3 SSD by filesystem UUID before Docker starts.

```text
/srv/shrimp/                       # SSD mount
├── postgres/                      # PostgreSQL data
├── mosquitto/data/                # broker persistence DB
├── mosquitto/log/
├── grafana/
├── ingest-quarantine/             # undecodable/collision export copies
├── exports/                       # controlled research exports
└── backups-staging/               # temporary local stage, not the only backup

/opt/shrimp/                       # version-controlled deployment/config
├── compose.yaml
├── .env.example                   # no real secrets
├── mosquitto/
├── ingestor/
├── migrations/
├── grafana/provisioning/
└── tests/
```

Requirements:

- Docker must not start the database if `/srv/shrimp` is absent; a missing SSD must fail closed instead of creating an empty database on microSD.
- `postgres`, `mosquitto`, `ingestor`, and `grafana` use `restart: unless-stopped` plus health checks.
- Ingestor waits for both broker and database health, but remains correct if Compose starts them in any order.
- Keep at least 30% SSD free; warn at 70%, critical at 85%, and stop nonessential derived jobs before raw ingestion is threatened.
- Nightly backups go to a physically separate device/NAS; the live SSD is not its own backup. Test a restore monthly.

## 3. MQTT namespace and policies

### Topics

```text
shrimp/v1/<tank_id>/<node_id>/measurement
shrimp/v1/<tank_id>/<node_id>/event
shrimp/v1/<tank_id>/<node_id>/health
shrimp/v1/<tank_id>/<node_id>/status
shrimp/v1/<tank_id>/<node_id>/ack
shrimp/v1/<tank_id>/<node_id>/command       # disabled except approved commissioning
```

### Delivery settings

| Topic | QoS | Retained | Owner/policy |
|---|---:|---|---|
| `measurement` | 1 | No | Node publishes; ingestor subscribes. Every durable sample has an identity. |
| `event` | 1 | No | Node/authorized ingestor; calibration/config/reboot/fault transitions. |
| `health` | 1 | No | Node publishes periodically; includes RSSI, uptime, buffer, errors, clock. |
| `status` | 1 | Yes | Node birth/LWT `online`/`offline`; not scientific measurement data. |
| `ack` | 1 | No | Ingestor publishes a positive or quarantined commit receipt only **after the exact raw bytes commit**; node subscribes only to its own ACK. |
| `command` | 1 | No | Disabled in normal ACL; temporary authorized use is audited. No chemical dosing. |

Use a stable MQTT client ID per node and ingestor, MQTT 5 clean start false, persistent session, keepalive, bounded reconnect backoff, and Last Will. Measurement payloads are never retained. Mosquitto persistence is enabled on the SSD. Per-client queue limits must exceed the tested gateway outage, and queue-overflow logs are alerts.

Authentication minimum: unique credential per node, password file/plugin, and ACL so a node can publish only its own measurement/event/health/status and subscribe only to its own ACK. The ingestor may subscribe to all node telemetry and publish ACKs. Grafana has no MQTT credential. TLS is required if the sensor LAN is not physically/administratively isolated; otherwise credentialed ACL is still mandatory. Secrets stay outside Git.

## 4. Measurement envelope

The wire payload is deterministic CBOR (`application/cbor`) to make the 8 MB ESP flash buffer practical. Its decoded logical representation is below. Every measurement still contains an ISO 8601 UTC field as required by `SPEC.md`; an unsynchronized sample contains the key with `null` and `CLOCK_UNSYNCED` rather than a fabricated time.

```json
{
  "schema_version": "1.0",
  "message_type": "measurement",
  "tank_id": "tank-100l-01",
  "experiment_id": "exp-2026-001",
  "node_id": "node-01",
  "boot_id": "4a6b5e3d-9fc5-4d37-97f2-88b8b8afca21",
  "boot_counter": 42,
  "sequence_number": 12345,
  "sensor_id": "sen0681-SERIAL",
  "sensor_model": "DFRobot SEN0681",
  "location": "mid-water-station-01",
  "timestamp_utc": "2026-09-03T01:23:45.382Z",
  "emitted_timestamp_utc": "2026-09-03T01:23:45.401Z",
  "monotonic_ms": 8344921,
  "clock": {
    "sync_status": "SYNCED",
    "last_ntp_sync_utc": "2026-09-03T01:20:00.000Z",
    "estimated_uncertainty_ms": 25
  },
  "values": [
    {"parameter": "dissolved_oxygen", "value": 6.42, "unit": "mg/L"},
    {"parameter": "temperature", "value": 28.13, "unit": "Cel"}
  ],
  "raw_value": {
    "encoding": "hex",
    "request": "010300020004...",
    "response": "010308..."
  },
  "sensor_status": "OK",
  "qc_flag": [],
  "firmware_version": "node-fw-gitsha",
  "driver_version": "sen0681-v1",
  "config_version": "cfg-sha256",
  "calibration_id": "cal-uuid",
  "temperature_compensation": {"value": 28.1, "unit": "Cel", "age_s": 1},
  "salinity_compensation": {"value": 20.0, "unit": "PSU", "age_s": 8},
  "rssi_dbm": -58,
  "uptime_ms": 8344921
}
```

CBOR uses a versioned integer-key dictionary and binary UUID/raw fields, but semantic names/types above are fixed. The encoder must be deterministic so a replay has byte-identical payload and SHA-256. The **exact MQTT payload bytes** are the primary raw record; decoded values never replace them.

Rules:

- One durable payload represents one sensor poll; multi-channel values from that same reply share a sequence number and become separate normalized reading rows with `item_index`.
- `value` is null on parse/sensor failure; it is never silently zero.
- Units and measurement basis are controlled metadata. For SEN0711 use `ammonia_n_reported_mg_l` until validated; do not label NH4 or TAN.
- A node may attach preliminary QC. The gateway adds its own QC records without mutating the raw payload.
- Firmware, configuration, and calibration identifiers are immutable references, not free-form descriptions.

## 5. UTC and clock behavior

### Pi

- chrony synchronizes from at least three appropriate upstream NTP sources when network access exists.
- The Pi serves NTP only to the sensor subnet using an explicit `allow <sensor-subnet>` rule and firewall rule for UDP 123.
- Do not configure a fake `local` reference as accurate UTC. During upstream loss, chrony holds over; clock health/offset/stratum are logged and displayed.
- Containers use the host UTC clock; database columns are `timestamptz`; dashboard display timezone may be local only at presentation time.

### ESP32

- Configure SNTP at boot and resynchronize periodically (initial target every 6 h; verify drift to finalize).
- Use the Pi’s fixed LAN address as primary NTP and a controlled fallback only if the network policy permits.
- Before first valid sync, continue sampling with `timestamp_utc: null`, monotonic time, and `CLOCK_UNSYNCED`.
- After a large initial correction, begin valid UTC timestamps; during normal operation prefer smooth adjustment. Record `CLOCK_STEP` whenever a step is unavoidable.
- Never rewrite a sample’s node timestamp after collection. The gateway adds its own receipt timestamp.
- Store `last_ntp_sync`, sync status, estimated uncertainty, uptime, and drift/offset diagnostics in health messages.

The gateway captures `gateway_received_timestamp_utc` immediately on MQTT callback, before decode/database work, plus a gateway monotonic counter. It also stores `database_committed_timestamp_utc`. Online chemistry may additionally store sample, analysis-complete, and result timestamps.

Sources: [ESP-IDF system time/SNTP](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/system/system_time.html), [chrony configuration](https://chrony-project.org/doc/4.7/chrony.conf.html).

## 6. Boot identity and sequence numbers

1. Each node has a stable `node_id` provisioned in configuration.
2. Increment a persistent NVS `boot_counter` once per boot, not once per measurement.
3. Generate a random UUID `boot_id` at boot and include the boot counter. Store that boot identity in RAM and the first durable boot event.
4. Start `sequence_number` at 0 for each boot and increment by one for every durable measurement payload.
5. The identity key is `(node_id, boot_id, sequence_number)`. It survives MQTT QoS duplicates and does not depend on the clock.
6. Use unsigned 64-bit counters. Never reset sequence within a boot, even after Wi-Fi/MQTT reconnection.

This avoids writing NVS on every sample. A reboot intentionally creates a new keyspace. A missing tail immediately before power loss is detected by the time/uptime/boot transition and expected-sampling monitor even though no later sequence exists in the old boot.

## 7. End-to-end commit and application ACK

MQTT QoS 1 `PUBACK` proves broker receipt, not PostgreSQL commit. The following application protocol closes that gap:

1. Node serializes the final deterministic payload and appends it to its durable ring buffer.
2. Node publishes the exact bytes at QoS 1.
3. Ingestor captures receipt time and inserts the raw delivery.
4. In one database transaction it classifies the identity/hash, inserts canonical/normalized rows if appropriate, adds gateway QC, and commits.
5. Only after commit, ingestor publishes an ACK/receipt containing `node_id`, `boot_id`, `sequence_number` when decodable, `payload_sha256`, `raw_delivery_id`, `disposition` (`ACCEPTED`, `DUPLICATE`, or `QUARANTINED`), and `database_committed_timestamp_utc`.
6. Node deletes/advances the ring only when the exact payload hash—and identity when available—matches a committed receipt. `QUARANTINED` advances the queue but latches a data-integrity fault/counter for operator review.

Lost ACKs cause safe duplicate replay. A duplicate with the same hash is audited and not normalized twice. The same key with a different hash is a `KEY_COLLISION`, is quarantined, and never overwrites the first canonical record. A collision receipt is sent only after the conflicting raw bytes and quarantine row commit, so the node can continue without discarding the evidence or wedging its entire queue.

During database failure the ingestor must stop acknowledging application messages and preferably disconnect its MQTT session after a bounded retry so the persistent broker queues QoS 1 deliveries. Nodes retain their own copies until application ACK, giving two independent recovery layers.

## 8. PostgreSQL storage model

### Core tables

| Table | Purpose / key |
|---|---|
| `raw_deliveries` | Append every broker delivery exactly as received: bigserial PK, receipt UTC/monotonic, topic/QoS/retain/DUP, payload `bytea`, SHA-256, decode status, optional identity, disposition. No update/delete during experiment. |
| `canonical_messages` | One accepted identity: PK `(node_id, boot_id, sequence_number)`, first raw-delivery FK, payload hash, node timestamp, gateway receipt/commit timestamps. |
| `readings` | One row per decoded `values[]` item: canonical FK + `item_index`, sensor/location/parameter, numeric/text value, unit, compensation and status references. |
| `reading_qc` | Many flags per reading/message with source (`node`, `gateway`, `manual`), rule/version, created UTC, detail JSONB. |
| `duplicate_audit` | Later raw delivery, canonical key, same hash, delivery time, MQTT DUP state. |
| `quarantine` | Parse/schema/identity/hash-collision reason and raw-delivery FK. Raw bytes remain in `raw_deliveries`. |
| `node_health` | RSSI, uptime, buffer records/bytes/oldest age, error counters, NTP state/offset, firmware/config. |
| `calibrations` | Sensor asset, method, standards/lots/expiry, pre/post results, coefficients, operator, UTC, document attachments/hashes. |
| `experiment_events` | Feeding, stocking, water exchange, cleaning, medication, sampling, maintenance, configuration deployment, power/network incident. |
| `derived_values` | Versioned calculation/model outputs with source reading IDs; never overwrites raw or synchronized values. |
| `clock_health` | Pi chrony samples and node-reported clock health. |

### Transaction classification

```text
append raw delivery
  ├── decode/schema fails → quarantine + QC; commit; QUARANTINED receipt by payload hash
  └── identity valid
      ├── key absent → insert canonical + readings + QC; commit; ACK
      ├── key present and SHA-256 identical → duplicate audit; commit; ACK
      └── key present and SHA-256 differs → KEY_COLLISION quarantine; commit; QUARANTINED receipt; no destructive overwrite; alert
```

Use foreign keys, check constraints for enum-like status, and database roles:

- `ingestor`: insert/call ingestion functions; no raw deletion;
- `grafana_reader`: read-only views only;
- `research_export`: controlled read/export;
- `migration_admin`: offline deployment only.

RAW is `raw_deliveries` plus source metadata. SYNCHRONIZED is the canonical/reading layer with node and gateway timestamps retained. DERIVED is separately versioned. These layers are never collapsed.

## 9. QC model

Minimum required flags plus gateway extensions:

| Flag | Trigger/action |
|---|---|
| `OK` | Represent as no adverse flags; do not combine literal `OK` with an error. |
| `WARMUP` | Manufacturer/commissioning stabilization interval active. |
| `OUT_OF_RANGE` | Outside documented measurement range; preserve raw/value. |
| `COMMUNICATION_ERROR` | Timeout, framing, CRC, NAK, I2C error; value null unless response is decodable. |
| `STALE` | Age exceeds versioned per-channel threshold. |
| `SENSOR_FAULT` | Device status bit/code or persistent self-test failure. |
| `CALIBRATION_REQUIRED` | Due date, failed check standard, drift, or sensor status. |
| `NETWORK_BUFFERED` | Gateway detects delayed/replayed sequence or node reports buffered delivery. |
| `COMPENSATION_MISSING` | Required temperature/salinity compensation absent. |
| `COMPENSATION_STALE` | Present but older than channel-specific limit. |
| `MANUAL_INVALID` | Authorized user marks unusable; original data remains. |
| `CLOCK_UNSYNCED` | Node UTC null/untrusted. |
| `CLOCK_STEP` | Discontinuous time correction. |
| `SEQUENCE_GAP` | Confirmed missing number after grace/replay window. |
| `DUPLICATE` | Same key and hash delivered again; audit only. |
| `KEY_COLLISION` | Same key, different payload hash; quarantine and alert. |
| `PARSE_ERROR` | Payload/schema/value cannot be decoded; raw bytes retained. |
| `RATE_OF_CHANGE` | Exceeds versioned scientific threshold; do not delete. |
| `STUCK` | Insufficient variation over versioned window, considering resolution. |
| `FLOW_LOW` / `FLOW_HIGH` | Bypass thresholds/persistence from design. |
| `MAINTENANCE` | Sensor/loop intentionally handled or cleaned. |

Range comes from manufacturer documentation. Rate-of-change and stuck thresholds require commissioning data and must carry a rule version; they are not invented as universal shrimp-health thresholds. Multiple flags may coexist.

## 10. ESP store-and-forward design

### Memory hierarchy

| Layer | Allocation | Purpose |
|---|---:|---|
| PSRAM working queue | 512 KiB | Encode/decode, batching, network retry, and replay window; volatile. |
| Flash durable ring | 2.25 MiB partition, target ≥2.0 MiB usable | Exact serialized MQTT payloads pending DB application ACK. |
| Pi/broker/DB | SSD-backed | Durable central storage and duplicate-safe replay. |

Proposed 8 MB flash partition budget, to be verified against the actual firmware image:

```text
nvs/otadata/phy + boot/partition overhead     about 0.125 MiB
ota_0 application slot                       2.500 MiB
ota_1 application slot                       2.500 MiB
spool wear-levelled ring                      2.250 MiB
remaining reserve/coredump                    about 0.625 MiB
```

Exact CSV offsets must be generated/alignment-checked by ESP-IDF and rejected if either signed application image approaches its slot limit. Use ESP-IDF wear levelling and a power-fail-safe filesystem/ring design; include record magic, schema, length, identity, payload length, exact payload, SHA-256 or compact integrity field, and CRC32. Two alternating ring headers prevent a torn header from destroying the queue.

Commit flash in bounded batches (target ≤5 s exposure) to reduce wear. An abrupt node power loss may lose the not-yet-committed tail, but it must never create a valid-looking corrupted record; the boot/time-gap monitor flags the outage. Batch/segment erase counts and bad-write/recovery counts are health metrics.

Sources: [ESP-IDF wear levelling](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/storage/wear-levelling.html), [ESP-IDF FAT filesystem](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/fatfs.html), [ESP-IDF NVS FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/storage/nvs.html).

### Capacity proof target

Use compact deterministic CBOR and require p95 stored record size ≤140 bytes in the commissioning capture.

| Node | Sampling assumption | Records/day | 4 h at 140 B |
|---|---|---:|---:|
| 1 | DO/5 s; pH/10 s; EC/10 s; PT-1000/10 s; turbidity/30 s; optional ammonia/60 s | 47,520 | 1.11 MB |
| 2 | RDO/5 s; ORP/5 s | 34,560 | 0.81 MB |
| 3 | H2S/10 s | 8,640 | 0.20 MB |
| 4 | flow/1 s; pump status/60 s | 87,840 | 2.05 MB |

A ≥2.0 MiB usable ring therefore gives approximately four hours on the worst-case Node 4 at the p95 limit. The acceptance test is empirical: disconnect Wi-Fi for four hours at full configured sample rates, then restore and require complete, ordered, duplicate-safe ingestion. If record size or usable capacity misses the target, increase flash/approved external endurance storage or revise the publish design under change control; do not silently lower scientific sampling.

Queue policy:

- persist before initial publish;
- replay oldest unacknowledged first, with a bounded rate so health/status remain visible;
- retain until exact key+hash application ACK;
- if full, raise/latch critical `BUFFER_FULL`, increment `data_loss_count`, and drop oldest only as the final documented policy—never silently;
- expose used bytes, record count, oldest age, write/erase errors, replay rate, and data-loss counter.

## 11. Expected data and SSD capacity

With all listed channels including conditional NH4, the nominal rate is about 178,560 sensor records/day. At an intentionally conservative average 350-byte MQTT payload equivalent:

- raw payload: ~62.5 MB/day;
- PostgreSQL raw + normalized rows + indexes at an initial 3× planning factor: ~188 MB/day;
- planning total: ~68.5 GB/year before logs/exports/backups.

A 500 GB SSD is adequate for initial Phase 1 with substantial headroom, but capacity is governed by measured row/index size, retention, and experiment duration. Measure `pg_total_relation_size` weekly for the first month and project exhaustion at the 70% warning threshold. Backups live elsewhere and are not counted as free live capacity.

## 12. Dashboard and alerts

Provision, version, and back up these Grafana views:

1. tank overview: last value, unit, sensor age, QC state, location;
2. synchronized trends: DO mid/bottom, pH, EC/salinity, temperature, turbidity, ORP/H2S, flow;
3. data integrity: sequence gaps, duplicates, collisions, null/parse/CRC counts, node-vs-gateway delay;
4. node health: online/LWT, RSSI, uptime/boot ID, firmware/config, buffer usage/oldest age, reset cause;
5. clock health: node sync status/age/uncertainty and Pi chrony offset/source;
6. bypass: 1 s flow with 1/5/15 min aggregates, pump command/status/reset, low/high events, maintenance age;
7. calibration/maintenance: due/overdue checks and recent events;
8. infrastructure: broker clients/queue, ingestion lag, DB health/connections, SSD free/SMART, Pi temperature/undervoltage.

Alerts are stateful and include persistence/hysteresis to avoid chatter. At minimum: node offline, channel stale, sequence gap, buffer >70%/>90%, any data loss, key collision, repeated communication errors, clock unsynced/stale, calibration overdue, flow low/high, disk >70%/>85%, database/broker unhealthy, Pi undervoltage/overtemperature.

No dashboard transformation changes authoritative values. Every derived curve names its algorithm/version and source records.

## 13. Recovery and acceptance matrix

| Test | Injection | Pass condition |
|---|---|---|
| Node reboot | Hard power Node 1 during sampling | New boot ID/counter, automatic reconnect, no malformed record, outage visible, buffered committed records replayed. |
| Four-hour Wi-Fi outage | Block node WLAN | Local queue stays within capacity; on restore all committed records arrive; duplicates dedupe; `NETWORK_BUFFERED` visible. |
| Broker restart | Restart/kill Mosquitto container | Nodes back off/reconnect; persistent state recovers; no canonical duplicate/loss beyond explicitly exposed uncommitted tail. |
| Ingestor restart | Kill during DB transaction and after commit-before-ACK | Transaction rollback or committed row is correct; replay becomes accepted or same-hash duplicate; never double reading. |
| PostgreSQL restart | Stop DB while broker/nodes run | No application ACK during outage; queues remain; complete recovery after health returns. |
| Pi hard power loss | Remove Pi power during sustained writes | Filesystems/DB recover without manual repair; nodes retain unacknowledged data; outage event visible. |
| Duplicate | Republish exact key/payload | Raw delivery appended, duplicate audited, canonical/readings unchanged, ACK returned. |
| Collision | Same key, one changed byte | Both raw deliveries preserved, second quarantined `KEY_COLLISION`, alarm; exact-hash quarantined receipt advances node queue only after raw commit; no canonical overwrite. |
| Sequence gap | Suppress one record then send later sequence | Gap becomes candidate, resolves if replay arrives, otherwise confirmed after grace with QC. |
| Bad CRC/schema | Corrupt sensor frame / CBOR | Raw stored, parse/communication QC, value null, other channels continue. |
| Clock unavailable | Block NTP at boot | Sampling continues with null UTC + monotonic and `CLOCK_UNSYNCED`; after sync, valid UTC resumes without rewriting old samples. |
| Clock correction | Force controlled offset in test environment | `CLOCK_STEP`/uncertainty recorded; sequence order remains authoritative. |
| Buffer full | Lab-only undersize/rate stress | Critical health before loss; `data_loss_count` nonzero if forced; no silent discard/corruption. |
| SSD absent | Reboot Pi without data SSD | Stack fails closed and alerts; no accidental empty DB on microSD. |
| Restore | Restore backup to clean test host | Counts/hashes/calibration/events/dashboards match the documented restore point. |

Phase 1 is not complete until a real sensor passes the entire path and the restart/failure matrix relevant to that slice. A green dashboard alone is not acceptance.

## 14. Implementation order

1. Inventory Pi model/RAM/power/SSD; update OS and record release.
2. Mount SSD by UUID; implement missing-mount fail-closed guard; check SMART and Pi undervoltage.
3. Configure chrony client/server and firewall; verify Pi and one ESP NTP behavior.
4. Deploy pinned Mosquitto/PostgreSQL/ingestor/Grafana Compose stack with secrets/ACL.
5. Apply schema migrations and seed controlled tank/node/sensor/config metadata.
6. Use a simulator to pass valid/invalid/duplicate/collision/out-of-order/clock cases.
7. Integrate SEN0681 → Node 1 and preserve exact frames.
8. Run the recovery matrix, restore test, and 72 h continuous soak.
9. Add one sensor/channel at a time only after its acceptance gate.
