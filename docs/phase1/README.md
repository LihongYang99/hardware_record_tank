# Phase-1 Engineering Design Package

**Languages / 语言：** English engineering baseline (this page) · [中文导读与文档索引](zh-CN/README.md) · [硬件小白入门指南](zh-CN/BEGINNER_GUIDE.md)

The Chinese companion pages explain the same design in beginner-friendly language. Exact model numbers, voltages, pin names, wire IDs, protocol settings, and English status tokens remain unchanged. If a translation ever appears inconsistent, stop and use `SPEC.md`, `DECISIONS.md`, and the English engineering page as the controlling text until the inconsistency is reviewed.

**Revision:** 2026-09-02  
**Scope:** 100 L *Litopenaeus vannamei* tank, 15–25 ppt, continuous Phase-1 monitoring  
**Authority:** [SPEC.md](../../SPEC.md) and [DECISIONS.md](../../DECISIONS.md) remain binding; [GOAL.md](../../GOAL.md) defines the objective and [AGENTS.md](../../AGENTS.md) defines repository working rules. This package does not silently promote or replace a `LOCKED` decision.

## Status vocabulary

- **VERIFIED** — current manufacturer documentation supports the stated electrical/interface/range claim.
- **RECOMMENDED — REQUIRES PROMOTION** — engineering selection for an open decision; it is not `LOCKED` until copied into `DECISIONS.md` under change control.
- **VERIFY BEFORE PURCHASE** — a critical fact is absent or ambiguous; the purchase or permanent connection is blocked, but other design work continues.
- **REJECTED FOR THIS DUTY** — documented limitation makes the item unsuitable for the stated Phase-1 duty.
- **DEFERRED** — scientifically desirable, but no defensible continuous Phase-1 implementation is ready.

## Deliverables

1. [Sensor verification and selection](SENSOR_VERIFICATION.md) — manufacturer-backed ranges, interfaces, protocols, saline-use evidence, rejected candidates, and unresolved gates.
2. [Complete Phase-1 BOM](BOM.md) — quantities, exact models/part numbers where defensible, purchase gates, consumables, spares, and owned equipment.
3. [Wire-by-wire matrix and GPIO map](WIRING_AND_GPIO.md) — every designed conductor, bus setting, address, shield rule, and reserved GPIO.
4. [Power architecture](POWER_ARCHITECTURE.md) — domain boundaries, load calculation, fusing, grounding/isolation, and power-up checks.
5. [100 L bypass design](BYPASS_DESIGN.md) — pump comparison, nominal flow, plumbing order, residence-volume budget, maintenance, and final chamber gate.
6. [Raspberry Pi and data-integrity architecture](PI_DATA_ARCHITECTURE.md) — MQTT, database, schema, UTC, sequence/idempotency, QC, buffering, recovery, dashboards, and acceptance tests.
7. [Final compatibility audit](COMPATIBILITY_AUDIT.md) — cross-domain audit, unresolved procurement gates, and commissioning sequence.
8. [Source register](SOURCE_REGISTER.md) — primary manufacturer/official references, the claims each supports, and archival rules.

## Recommended open-decision disposition

These are recommendations only; `DECISIONS.md` has not been edited.

| Open item | Engineering disposition | Current status |
|---|---|---|
| OPEN-01 pH | Atlas Scientific ENV-50-pH-NT (SMA) + EZO-pH + ISCCB-2 | RECOMMENDED — REQUIRES PROMOTION |
| OPEN-02 EC/salinity | Atlas Scientific EC-KIT-10 plus independent PT-1000 compensation | RECOMMENDED — REQUIRES PROMOTION |
| OPEN-03 turbidity/eTSS | DFRobot SEN0710; turbidity is not eTSS until site calibration | VERIFY BEFORE PURCHASE: no explicit 15–25 ppt long-duration statement |
| OPEN-04 NH4 | Do not buy SEN0711 yet; validate against TAN reference methods in actual brackish matrix | VERIFY BEFORE PURCHASE |
| OPEN-05 bottom ORP | DFRobot SEN0709 | VERIFY BEFORE PURCHASE: written saline-immersion confirmation required |
| OPEN-06 H2S | SulfiLogger S1-1020 low range + isolated RS232 | VERIFY BEFORE PURCHASE: written saline compatibility and maximum current required |
| OPEN-07 and OPEN-08 Mg/Ca | Leave Node 4 ports reserved; use periodic laboratory reference analysis; HI97115C only as validated screening | DEFERRED; HI97115C Ca/Mg ranges do not cover the full brackish expectation |
| OPEN-09 bypass pump | Atlas Scientific EZO-PMP at 80 mL/min under Node 4 isolated I2C supervision | RECOMMENDED — REQUIRES PROMOTION; 20-day reset/startup endurance test required |
| OPEN-10 flow meter | Sensirion EK-SLF3S-4000B during commissioning | RECOMMENDED — REQUIRES PROMOTION; gravimetric saltwater calibration required |
| OPEN-11 tubing | 5 mm OD × 3 mm ID pump-head tube plus short 5–6 mm ID external salt-compatible tubing; keep total wet volume bounded | RECOMMENDED — REQUIRES PROMOTION |
| OPEN-12 flow cell | Do not order a final multi-probe chamber before Ca/Mg probe geometry is known | VERIFY BEFORE PURCHASE |
| OPEN-13, OPEN-14, and OPEN-15 NO2/NO3/alkalinity | Periodic external reference methods; optionally validate HI97115C screening | DEFERRED from direct online sensing |
| OPEN-16 Pi stack | Mosquitto + Python ingestor/QC + PostgreSQL + Grafana under Docker Compose; chrony on host | RECOMMENDED — REQUIRES PROMOTION |

## First build slice

The lowest-risk first integration remains the `LOCKED` Phase-1 path:

`SEN0681 → Waveshare TTL TO RS485 (B) → ESP32-S3 Node 1 → Wi-Fi → MQTT → Raspberry Pi → PostgreSQL → Grafana`

This slice is electrically specified and uses a manufacturer-published RS485 protocol. Configure the SEN0681 salinity compensation to the independently measured tank salinity (15–25 ppt); its seawater default of 30 ‰ must not be accepted silently.

## What is intentionally not claimed

- This package is an engineering design and procurement gate, not a claim that Phase 1 has been physically commissioned.
- A candidate is not called `LOCKED` merely because its protocol is known.
- Turbidity is not converted to eTSS without tank-specific paired gravimetric samples.
- An ammonia-nitrogen sensor output is not relabeled `NH4+` or `TAN` without a validated matrix method.
- No exact Mg/Ca online sensor or final flow-cell port geometry is invented.
- No substantial Jetson/ML work is included.
