# Phase-1 Compatibility Audit and Build Gates

**Revision:** 2026-09-02  
**Audit basis:** `SPEC.md`, `DECISIONS.md`, and the six companion engineering documents in this folder  
**Result:** the first SEN0681 integration path is design-ready. Several expansion channels remain correctly gated; none blocks the first path or Pi/data implementation.

## 1. Locked-decision compliance

| Locked requirement | Design evidence | Result |
|---|---|---|
| Sensor → converter → ESP32 → UTC → Wi-Fi → MQTT → Pi → DB → dashboard | First slice is SEN0681 → Waveshare TTL TO RS485 (B) → Node 1 → Mosquitto → Python → PostgreSQL → Grafana | **PASS, pending physical test** |
| Multiple independent ESP32-S3-DevKitC-1-N8R8 nodes | Four-node allocation and one spare in BOM; independent USB power | **PASS** |
| Pi always-on; Jetson not required | Pi hosts all Phase-1 services; Jetson absent from required path | **PASS** |
| MQTT | Versioned topics, QoS 1, LWT, ACL, persistence, application ACK | **PASS** |
| UTC ISO 8601 and dual timestamps | Node `timestamp_utc`; Pi receipt and commit UTC; unsynced null + QC | **PASS** |
| Sequence numbers | 64-bit sequence per boot; composite identity; gap logic | **PASS** |
| RAW/SYNCHRONIZED/DERIVED preservation | Separate raw deliveries, canonical/readings, derived tables | **PASS** |
| QC flags and missing/error visibility | Required flags retained and extended; invalid is null, never zero | **PASS** |
| Store-and-forward | Durable ESP ring + broker persistence + DB application ACK | **PASS by design; four-hour test required** |
| 12 V sensors separate from USB 5 V/3.3 V logic | Fused 12 V rail and galvanically isolated interfaces | **PASS** |
| Waveshare TTL TO RS485 (B) for RS485; one converter per compatible bus | Node 1 shared compatible 4800 8N1 bus; Node 2 incompatible settings split | **PASS** |
| H2S dedicated node and isolated RS232 if S1-1020 | Node 3/Waveshare matrix specified | **PASS, candidate still gated** |
| Bypass required | 80 mL/min recirculating design, measured <100 mL internal volume | **PASS by design; hardware gated** |
| Ca/Mg validation; NH4 is not TAN | No invented online Ca/Mg; external reference; strict ammonia naming | **PASS** |
| Electronics dry/permanent wiring | Dry NEMA enclosures, glands, ferrules, terminal labeling; no permanent Dupont | **PASS by design** |
| First integrate one verified sensor | Release A is SEN0681 only | **PASS** |
| No substantial Jetson ML | None included | **PASS** |

`DECISIONS.md` was not edited. Recommendations for open decisions remain explicitly unpromoted.

## 2. Cross-interface compatibility matrix

| Link | Voltage/domain | Protocol | Settings/address | Compatibility result |
|---|---|---|---|---|
| SEN0681 ↔ Waveshare TTL TO RS485 (B) | Sensor 12 V; isolated RS485 side | Modbus RTU | 4800 8N1, addr 1 | **VERIFIED by manufacturer pin functions; pending physical test** |
| Conditional SEN0710 ↔ Node 1 bus | 12 V; same RS485 domain | Modbus RTU | 4800 8N1, addr 2 after bench programming | Electrically/protocol compatible; **salinity HOLD** |
| Conditional SEN0711 ↔ Node 1 bus | 12 V; same RS485 domain | Modbus RTU | 4800 8N1, addr 3 | Electrically/protocol compatible; **scientific/salinity HOLD** |
| Waveshare TTL logic ↔ ESP | 3.3 V P3V3/LGND | UART | GPIO17 TX→RXD; TXD→GPIO18 RX | **VERIFIED by pin-function documentation** |
| EZO-pH/EC/RTD ↔ Node 1 | P3V3/LGND; pH/EC probe isolation in carriers | I2C | 100 kHz; 0x63/0x64/0x66 | Unique addresses; **pull-up measurement required** |
| RDO Blue ↔ Waveshare-A | 12 V; isolated RS485 | Modbus RTU | 19200 8E1, addr 1 | **VERIFIED**; controlled A/B swap fallback |
| SEN0709 ↔ Waveshare-B | 12 V; isolated RS485 | Modbus RTU | 4800 8N1, addr 1 | Separate UART prevents conflict; **salinity HOLD** |
| S1-1020 ↔ isolated RS232 | Sensor 12 V; isolated RS232 | ASCII RS232 | 38400 8N1, LF; `GETDATA ALL` | Protocol compatible; **sensor purchase HOLD** |
| DFR0565 ↔ ESP Node 4 | Controller 5 V/LGND | I2C isolation | GPIO8 SDA/GPIO9 SCL, 100 kHz | **VERIFIED** |
| DFR0565 output ↔ Pololu | isolated 5 V → 3.3 V | Power | 150 mA isolator capability; loads ~19 mA plus margin | **PASS**; measure 3.2–3.8 V at flow meter |
| SLF3S ↔ isolated I2C | 3.3 V/IGND4 | I2C + CRC | addr 0x08 | **PASS**; brackish calibration required |
| EZO-PMP logic ↔ same isolated bus | 3.3 V/IGND4; motor separately 12 V | I2C | addr 0x67; `DC,80,*` | Address/voltage compatible; reset recovery test required |
| ESP ↔ Pi | Independent power domains | Wi-Fi/MQTT | QoS 1, CBOR, per-node ACL | **PASS by design** |

No I2C or serial address collision remains in the defined configuration. Node 2’s two sensors must not be merged onto one UART even though both are RS485, because their default baud/parity differ. Node 4’s pump and flow sensor may share the isolated I2C bus because addresses and supply are compatible.

## 3. Scientific compatibility

| Claim | Permitted label/use | Prohibited shortcut |
|---|---|---|
| SEN0681 DO | `dissolved_oxygen_mg_l`, saturation, internal temperature; actual salinity compensation recorded | Leaving default 30 ‰ in a 15–25 ppt tank. |
| Atlas EC | Raw conductivity primary; salinity synchronized/derived with algorithm/version | Treating calculated salinity as an independent measured sensor. |
| SEN0710 | `turbidity_ntu` | Calling it eTSS before paired gravimetric site calibration. |
| SEN0711 | `ammonia_n_reported_mg_l` during validation | Calling it NH4+, NH3, or TAN without basis/interference validation. |
| RDO Blue | Bottom-risk DO with configured salinity | Assuming mid-water salinity is current when compensation input is stale. |
| ORP | Millivolts at the installed reference system | Converting ORP alone to H2S concentration. |
| S1-1020 | Dissolved H2S for exact ordered range after saline approval | Substituting headspace H2S gas sensing. |
| SLF3S | Relative/validated brackish flow after gravimetric correction | Claiming water-calibration accuracy directly in 15–25 ppt. |
| Mg/Ca/NO2/NO3/alkalinity/TAN | External, time-aligned validated reference results | Forcing an unvalidated continuous ISE/wet-chemistry channel into Phase 1. |

Hanna `HI97115C` was evaluated as an optional external screening instrument, not accepted as a primary reference: its Ca 200–600 ppm and Mg 1000–1800 ppm ranges do not span the full concentrations expected after diluting normal marine composition to 15–25 ppt, and its marine method matrix/manual revision must be validated. This closes the equipment-screening research without promoting an unsuitable Ca/Mg solution.

## 4. Environmental and mechanical audit

| Risk | Design control | Residual gate |
|---|---|---|
| Salt spray/condensation | Electronics and terminations in dry elevated enclosures; glands, drip loops, desiccant, strain relief | Physical enclosure fit and cable OD selection. |
| Biofouling | Inspection/cleaning events, optical-window checks, flow/filter trend, reference comparisons | Actual interval learned during soak; cannot exceed manufacturer life. |
| Bottom sediment | RDO/ORP/H2S heads held above sediment, not buried; spatial commissioning | Exact bracket height after tank survey. |
| Cable strain/shrimp contact | Anchored probes, guarded intake, fixed cable path | Tank-specific brackets. |
| Bypass leak/siphon | Peristaltic pump, return air gap, dry drip tray, clamps, low-flow shutdown | 24 h leak test and pump-on/off DO impact. |
| Wetted-metal toxicity/corrosion | PP/PVDF/HDPE/PEEK/316L only where documented; no copper/brass/plain steel | Exact fitting/elastomer SKU review. |
| Excess dead volume | ≤1.2 m tube, chamber ≤40 mL, measured total <100 mL | Final Ca/Mg geometry unknown; final chamber blocked. |
| Pump wear | Spare cassette, initial 30-day inspection, hard manufacturer-life limits | Empirical replacement interval. |

## 5. Power audit

- Known 12 V design allocation excluding H2S is 0.780 A.
- GST25A12-P1J supplies 2.08 A. To retain 40% headroom, H2S maximum/start allocation must be ≤0.706 A; for 25%, ≤0.884 A.
- EZO-PMP’s ~400 mA documentation is carried as a conservative 600 mA allocation until measured.
- Every 12 V load has a 1 A branch home run; a 2 A protected feed bounds total wiring current.
- ESP nodes use independent USB supplies; peripherals use local 3.3 V regulators. Node 4 isolation output is reduced from 5 V to 3.3 V before SLF3S.
- Sensor-side grounds and node USB grounds have no intentional conductive bond.

**Audit status:** PASS for Release A; GST remains PROVISIONAL for the full build until H2S maximum/start current and measured pump current close the calculation.

## 6. Data-integrity audit

| Failure | Detection | Preservation/recovery |
|---|---|---|
| Sensor timeout/CRC/NAK | Driver status and counters | Raw request/response/error, null value, QC; other tasks continue. |
| Wi-Fi loss | MQTT state, buffer growth, health age | Exact payload in flash ring; oldest-first replay. |
| Broker loss/restart | Connection/LWT/broker health | Node ring + persistent broker session; reconnect backoff. |
| DB/ingestor loss | No application ACK, service health | Node retains record; broker queues; transaction replay is idempotent. |
| ESP reset | New boot ID/counter/reset cause | Committed ring survives; clock and time gap visible. |
| Duplicate delivery | Same identity + same SHA-256 | Append raw delivery, audit duplicate, no second canonical reading. |
| Identity collision | Same identity + different SHA-256 | Preserve both, quarantine, alert, never overwrite. |
| Clock unavailable/step | Sync state/offset, dual timestamp, sequence | Null/untrusted node UTC + QC; monotonic/sequence order; no timestamp rewrite. |
| Buffer exhaustion | used %, oldest age, `data_loss_count` | Critical alert; explicit oldest-drop only as final policy, never silent. |
| SSD missing/full | mount guard, free-space/SMART alerts | Stack fails closed if missing; capacity thresholds protect raw ingestion. |

**Audit status:** design closes the failure modes. Physical/software acceptance tests remain mandatory before Phase-1 completion.

## 7. Firmware integration contract

All nodes use the same nonblocking modules:

```text
clock service
sensor driver state machines
sample scheduler
normalizer + node QC
deterministic CBOR serializer
durable ring
MQTT transport + application ACK handler
health/event reporter
watchdog and configuration manager
```

No sensor driver may block Wi-Fi, clock, buffer, or another sensor. Use deadline-driven states (`IDLE → REQUEST → WAIT → PARSE → PUBLISH/ERROR`) rather than long `delay()` calls. After a timeout, record the error, release the bus, and retry with bounded backoff; do not reboot the whole node for one sensor.

### Initial sampling schedule

| Node/channel | Raw interval | Notes |
|---|---:|---|
| N1 SEN0681 DO | 5 s | Sensor response may be much slower; raw still preserved. |
| N1 pH | 10 s | Temperature compensation must be fresh. |
| N1 EC/salinity | 10 s | Raw conductivity plus compensation. |
| N1 PT-1000 | 10 s | Schedule before pH/EC reads. |
| N1 turbidity conditional | 30 s | Optical fouling checks. |
| N1 ammonia conditional | 60 s | Validation only. |
| N2 RDO Blue | 5 s | Separate UART. |
| N2 ORP conditional | 5 s | Separate UART. |
| N3 H2S conditional | 10 s | Response <25 s means successive values may not be independent. |
| N4 flow | 1 s | Preserve every raw sample; dashboard aggregates. |
| N4 pump status | 60 s and every transition | Immediately after reset/fault as well. |
| all node health | 30 s | Buffer/clock/error/RSSI/uptime/reset state. |

Firmware configuration must reject duplicate I2C/Modbus addresses, unsupported baud/parity, sensor IDs missing from the asset table, and an H2S or pump enable flag without the corresponding purchase/commissioning approval. Every deployed config has a content hash/version and rollback copy.

## 8. Procurement release register

### Release now for first integration

- ESP32-S3-DevKitC-1-N8R8, Waveshare TTL TO RS485 (B) Part No. 23778, SEN0681.
- One node USB supply/cable, 12 V supply/distribution/protection, dry enclosure/wiring/labels.
- Pi SSD/network components after inventory, plus bench tools/reference salinity equipment.

### Technically recommended, formal promotion required

- OPEN-01: Atlas ENV-50-pH-NT + EZO-pH + ISCCB-2.
- OPEN-02: Atlas EC-KIT-10.
- Temperature dependency: Atlas KIT-306 configured PT-THRD.
- OPEN-09: EZO-PMP with Node 4 isolated I2C supervision.
- OPEN-10: EK-SLF3S-4000B with brackish gravimetric calibration.
- OPEN-11: short 5–6 mm-ID salt-compatible external tubing plus the pump’s 3 mm-ID head tube.
- OPEN-16: Mosquitto/Python/PostgreSQL/Grafana/Compose + host chrony.

### Verify before purchase

- OPEN-03/SEN0710: written continuous 15–25 ppt compatibility.
- OPEN-04/SEN0711: measurand basis, interference/salinity validity, external comparison.
- OPEN-05/SEN0709: written continuous 15–25 ppt compatibility.
- OPEN-06/S1-1020: exact low-range order code, continuous saline use, maximum/start current, cable and maintenance details.
- OPEN-12/final chamber: exact validated probe geometry and port requirements.
- Exact external tubing/fittings/glands/enclosure sizes: physical fit and wetted-material certificate.

### Deferred, not blockers

- OPEN-07/08 online Mg/Ca: periodic reference analysis; Node 4 reserved.
- OPEN-13/14/15 direct NO2/NO3/alkalinity: periodic validated external analysis.
- Jetson/ML.

## 9. Recommended change-control proposals

If the owner accepts them, promote each item separately in `DECISIONS.md` with evidence links and rollback criteria. Do not bundle unresolved holds into a locked decision.

| Proposal | Proposed decision | Evidence location |
|---|---|---|
| P-01 | Select Atlas ENV-50-pH-NT (SMA), EZO-pH, ISCCB-2 for OPEN-01 | `SENSOR_VERIFICATION.md` §2.2 |
| P-02 | Select Atlas EC-KIT-10 plus KIT-306/PT-THRD compensation for OPEN-02 | §2.3–2.4 |
| P-09 | Select EZO-PMP at 80 mL/min under Node 4 isolated supervision for OPEN-09 | `BYPASS_DESIGN.md` §2, §7 |
| P-10 | Select EK-SLF3S-4000B as calibrated flow-presence/relative monitor for OPEN-10 | `BYPASS_DESIGN.md` §3, §8 |
| P-11 | Select the two-diameter tubing architecture and measured <100 mL volume gate for OPEN-11 | `BYPASS_DESIGN.md` §5–6 |
| P-16 | Select Mosquitto/Python/PostgreSQL/Grafana/Compose/chrony for OPEN-16 | `PI_DATA_ARCHITECTURE.md` §1 |

## 10. Commissioning sequence

1. Freeze and photograph Release A parts; record asset/firmware/datasheet revisions.
2. Assemble/fuse dry power distribution and one Node 1 box; pass forbidden-continuity and loaded-voltage tests.
3. Configure SEN0681 alone at 4800 8N1/address 1; set/read back actual salinity; capture 100 valid frames.
4. Bring up Pi SSD/chrony/Mosquitto/PostgreSQL/ingestor/Grafana with simulator tests.
5. Send real SEN0681 data through the full path; confirm exact raw bytes, node/gateway UTC, sequence, QC, permanent DB, and dashboard.
6. Pass node/Wi-Fi/broker/ingestor/DB/Pi restart tests plus four-hour buffering and restore test.
7. Run 72 h continuous soak and close defects.
8. Promote and add pH, EC/PT-1000, then RDO one channel at a time.
9. Close written vendor gates before ORP/turbidity/H2S/NH4 purchase.
10. Bench/calibrate the bypass, prove measured volume/leak/fault behavior, then install.
11. Perform spatial commissioning and reference-analysis campaign before scientific reliance.

## 11. Phase-1 Definition-of-Done evidence packet

Phase 1 is complete only when the repository/experiment archive contains:

- released BOM and as-built wire schedule with photographs;
- asset serials, firmware/config hashes, calibration records, and manufacturer responses;
- real sensor raw frames and deterministic payload examples;
- Pi deployment manifest, schema migration, ACL, dashboard provisioning, backup/restore instructions;
- full-path proof from sensor to persistent database/dashboard;
- UTC/NTP and dual-timestamp evidence;
- sequence-gap, duplicate, collision, QC, and null-not-zero tests;
- four-hour offline buffer/replay report;
- restart/power-loss/recovery matrix results;
- 72 h soak report with data completeness/error/drift statistics;
- spatial commissioning and bypass representativeness results;
- remaining `VERIFY BEFORE PURCHASE` items clearly excluded from claims.

The engineering documentation is complete enough to execute Release A and to make the listed purchase decisions. Physical Phase-1 acceptance remains an experimental/build activity, not something documentation alone can declare complete.
