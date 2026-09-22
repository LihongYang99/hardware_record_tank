# DECISIONS.md
# Aquaculture Real-Time Monitoring Platform
## Engineering Decision Log

Version: 0.1  
Project: 100 L Litopenaeus vannamei Real-Time Monitoring Platform

---

# Decision Status Definitions

Use the following status definitions throughout this project.

## LOCKED

The decision has been intentionally made and should NOT be changed without an explicit engineering reason.

Codex must not silently replace or redesign a LOCKED decision.

---

## PROVISIONAL

The current design direction is preferred, but it may be changed if research identifies a clearly superior technical solution.

Any change must be documented.

---

## VERIFY BEFORE PURCHASE

The component or design is promising, but at least one important technical requirement still requires verification.

It must NOT be placed in the final BUY NOW list until verification is complete.

---

## REJECTED

The option has been considered and should not be used unless new evidence materially changes the decision.

---

# DECISION 001 — Primary Project Objective

Status:

LOCKED

Decision:

The first objective is to build a reliable real-time water-quality monitoring platform.

The required Phase-1 data path is:

Sensor  
→ signal interface / converter  
→ ESP32  
→ UTC timestamp  
→ Wi-Fi  
→ MQTT  
→ Raspberry Pi  
→ database  
→ real-time dashboard

Reason:

Reliable timestamped sensing is required before machine learning or edge computing has scientific value.

Jetson Orin / ML work must not delay the monitoring platform.

---

# DECISION 002 — Tank and Experimental Context

Status:

LOCKED

System:

- approximately 100 L tank
- Litopenaeus vannamei
- brackish / saline water
- approximately 15–25 ppt salinity
- experiments may operate continuously for weeks to months

Engineering consequence:

All sensor, material, plumbing, power, and enclosure decisions must consider long-term saline-water operation.

---

# DECISION 003 — Modular Multi-Node Architecture

Status:

LOCKED

Decision:

Do NOT attempt to connect the entire monitoring system to one ESP32.

Use multiple independent ESP32 nodes.

Reason:

- easier troubleshooting
- reduced failure propagation
- easier sensor maintenance
- easier calibration
- simpler UART management
- improved modularity
- easier future expansion

The goal is reliability, not minimum ESP32 count.

---

# DECISION 004 — Preferred ESP32 Platform

Status:

LOCKED

Preferred board:

Espressif ESP32-S3-DevKitC-1-N8R8

Use official Espressif hardware where practical.

Reason:

- sufficient GPIO
- multiple UART interfaces
- I2C / SPI / ADC availability
- 8 MB Flash
- 8 MB PSRAM
- Wi-Fi
- strong manufacturer support
- standardized hardware across nodes

ESP32 GPIO logic:

3.3 V

Board power:

USB 5 V preferred.

Never apply 5 V or 12 V directly to ESP32 GPIO.

---

# DECISION 005 — Initial ESP32 Node Layout

Status:

PROVISIONAL

Preferred architecture:

## NODE 01 — MID WATER

Potential sensors:

- DO-mid
- pH
- EC / salinity
- temperature
- turbidity / eTSS
- NH4+ if scientifically appropriate

## NODE 02 — BOTTOM RISK

- DO-bottom
- ORP-bottom

## NODE 03 — H2S

Dedicated ESP32 node.

- dissolved H2S

## NODE 04 — BYPASS

- Mg
- Ca
- flow
- bypass pump status / control if useful

This architecture may be modified only if there is a clear technical benefit.

Do not consolidate nodes merely to reduce hardware count.

---

# DECISION 006 — Raspberry Pi Role

Status:

LOCKED

Decision:

The Raspberry Pi will be the primary always-on gateway and monitoring computer.

Primary roles:

- MQTT broker
- central sensor-data ingestion
- database
- dashboard
- experiment metadata
- node-health monitoring
- data export
- local backup
- system-service management

The Raspberry Pi should remain sufficient for the complete Phase-1 monitoring platform.

---

# DECISION 007 — Jetson Orin Role

Status:

LOCKED

Decision:

Jetson Orin is NOT required for basic real-time monitoring.

Future role:

- edge ML
- anomaly detection
- sensor fusion
- prediction
- computer vision
- intelligent control

Preferred future relationship:

ESP32
→ MQTT
→ Raspberry Pi
→ Jetson Orin subscriber / data consumer

The platform must continue working normally when Jetson Orin is powered off.

---

# DECISION 008 — Network Transport

Status:

LOCKED

Preferred protocol:

MQTT

Preferred broker location:

Raspberry Pi

Reason:

MQTT provides a modular publish/subscribe architecture suitable for multiple sensor nodes and future Jetson integration.

MQTT design must support:

- reconnect
- node heartbeat
- Last Will and Testament
- QC information
- sequence numbers
- future multiple tanks

---

# DECISION 009 — Timestamp Standard

Status:

LOCKED

Every measurement must have a timestamp.

Internal standard:

UTC

Preferred format:

ISO 8601

Example:

2026-09-03T01:23:45.382Z

Each ESP32 should synchronize time using NTP.

NTP synchronization should occur:

- at startup
- periodically during operation

Loss of NTP must not stop sensor acquisition.

---

# DECISION 010 — Dual Timestamp Strategy

Status:

LOCKED

Where practical, preserve both:

sample_timestamp_utc

and:

gateway_received_timestamp_utc

Purpose:

Distinguish:

- actual measurement time
- network delay
- gateway delay
- buffered transmission

For delayed chemistry measurements, support:

sample_time
analysis_complete_time
result_time

Do not replace sample time with arrival time.

---

# DECISION 011 — Sequence Numbers

Status:

LOCKED

Every ESP32 measurement stream must include a monotonically increasing:

sequence_number

Example:

10431
10432
10434

The Raspberry Pi must be able to detect that:

10433

was missing.

Reason:

Required for scientific data-integrity checking.

---

# DECISION 012 — Raw Data Preservation

Status:

LOCKED

Raw measurements must always be preserved.

Data architecture:

## RAW

Original sensor values at original acquisition frequency.

## SYNCHRONIZED

Common time grid such as:

1 minute
5 minutes

## DERIVED

Examples:

- DO_mid_minus_DO_bottom
- rolling DO minimum
- rolling DO mean
- dDO/dt
- dORP/dt
- Mg/Ca
- calculated NH3-N

Aggregated data must never overwrite raw data.

---

# DECISION 013 — QC Flags

Status:

LOCKED

Invalid values must never silently become zero.

Use QC/status fields.

Initial QC vocabulary:

- OK
- WARMUP
- OUT_OF_RANGE
- COMMUNICATION_ERROR
- STALE
- SENSOR_FAULT
- CALIBRATION_REQUIRED
- NETWORK_BUFFERED
- COMPENSATION_MISSING
- MANUAL_INVALID

---

# DECISION 014 — Network Failure Handling

Status:

LOCKED

Temporary Wi-Fi or MQTT interruption must not immediately destroy measurements.

The platform must implement a store-and-forward strategy.

Buffered measurements must preserve:

- original timestamp
- sequence number
- QC state

Avoid excessive ESP32 flash wear.

Exact buffering implementation remains to be designed.

---

# DECISION 015 — Main Sensor Power Voltage

Status:

LOCKED

Preferred industrial sensor power rail:

12 VDC

Reason:

Many selected industrial water-quality probes support 12 V operation.

A common 12 V rail simplifies power distribution.

This does NOT mean all electronics use 12 V.

The system must always distinguish:

12 V sensor power

5 V development-board power

3.3 V ESP32 GPIO logic

---

# DECISION 016 — Main 12 V Power Supply

Status:

PROVISIONAL

Current preferred model:

Mean Well GST25A12-P1J

Nominal output:

12 VDC

2.08 A

approximately 25 W

Use:

industrial sensor power

Before final purchase/design approval, calculate total maximum current for all connected devices.

Desired reserve:

approximately 25–40% unused capacity.

If the full system exceeds an appropriate power margin, select a larger Mean Well supply rather than operating near the PSU limit.

---

# DECISION 017 — ESP32 Power

Status:

LOCKED

Preferred ESP32 power method:

USB 5 V

Do not power industrial sensors from ESP32 GPIO or 3.3 V pins.

Do not connect 12 V to the ESP32 5 V pin.

---

# DECISION 018 — Power Distribution

Status:

LOCKED

Use dedicated power distribution rather than forcing multiple sensors to draw power through communication converters.

Preferred topology:

12 V PSU
→ fuse
→ distribution connector
→ individual sensor power branches

Preferred distribution hardware:

WAGO 221 series or equivalent high-quality terminal connectors.

Separate electrical nodes must be maintained for:

+12 V
GND
RS485 A
RS485 B

---

# DECISION 019 — Permanent Wiring

Status:

LOCKED

Preferred permanent wiring:

22–24 AWG stranded copper hookup wire

Preferred color convention:

Red:
+12 V

Black:
GND

Yellow:
RS485 A

Blue:
RS485 B

Ferrules should be used where appropriate for stranded wire entering screw terminals.

Dupont wires may be used for short prototype logic connections but are not preferred for permanent sensor-power wiring.

---

# DECISION 020 — RS485 Conversion

Status:

LOCKED

RS485 A/B must NOT connect directly to ESP32 GPIO.

Preferred converter:

DFRobot DFR0845
Gravity Active Isolated RS485 to UART Signal Adapter

Use:

RS485 / Modbus RTU
→ DFR0845
→ UART
→ ESP32

Isolation is preferred because the sensors operate in conductive saline water and ground-loop / noise problems are possible.

---

# DECISION 021 — One Converter Does Not Equal One Sensor

Status:

LOCKED

One RS485-to-UART converter corresponds to one RS485 BUS.

Multiple compatible sensors may share the same converter/bus when:

- baud rate matches
- data bits match
- parity matches
- stop bits match
- every Modbus device has a unique address

Do not assign duplicate Modbus addresses.

Do not force incompatible default serial settings onto one bus.

---

# DECISION 022 — RS485 Distribution

Status:

LOCKED

When multiple sensors share one bus:

all A conductors share the A bus.

all B conductors share the B bus.

Example:

DFR0845 A
→ distribution connector
├─ Sensor 1 A
├─ Sensor 2 A
└─ Sensor 3 A

DFR0845 B
→ distribution connector
├─ Sensor 1 B
├─ Sensor 2 B
└─ Sensor 3 B

Do not create electrical connection between A and B.

Proper RS485 topology, termination and cable layout must still be evaluated.

---

# DECISION 023 — Mid-Water DO Candidate

Status:

RECOMMENDED / VERIFY CURRENT SPECIFICATIONS

Current preferred sensor:

DFRobot SEN0681
Seawater Optical Dissolved Oxygen Sensor

Intended role:

DO-mid

Expected characteristics already identified:

- optical DO
- seawater-oriented
- RS485 / Modbus RTU
- 12 V system integration possible

Before purchase, Codex must verify current:

- voltage
- exact wiring
- Modbus settings
- salinity compensation
- availability
- cable
- immersion specification

Do not replace it without documenting why.

---

# DECISION 024 — Bottom DO Candidate

Status:

RECOMMENDED / VERIFY CURRENT SPECIFICATIONS

Current preferred sensor:

In-Situ RDO Blue

Preferred configuration:

stripped-and-tinned cable version

Previously identified candidate:

3 m cable
P/N 0038620

Intended role:

DO-bottom

Reason:

Research-grade optical DO sensor suitable for long-term deployment.

Installation intent:

approximately 5–10 cm above tank bottom.

Do not bury the sensing surface in sludge.

Codex must verify current product documentation before final purchase.

---

# DECISION 025 — Bottom ORP Candidate

Status:

VERIFY BEFORE PURCHASE

Current candidate:

DFRobot SEN0709

Intended role:

ORP-bottom

Expected interface:

RS485 / Modbus RTU

Expected system power:

12 V

Critical unresolved requirement:

confirm suitability for continuous long-term use in approximately 15–25 ppt saline/brackish water.

Do NOT mark LOCKED until this is verified.

---

# DECISION 026 — H2S Must Measure Dissolved H2S

Status:

LOCKED

The H2S sensor must measure dissolved H2S in the water.

Do NOT use an atmospheric H2S gas sensor as a substitute.

The sensor must be suitable for near-bottom monitoring.

Preferred mounting:

near-bottom water layer

not buried in sludge.

---

# DECISION 027 — H2S Dedicated ESP32

Status:

LOCKED

H2S will use its own dedicated ESP32 node unless a compelling technical reason emerges.

Reason:

- specialized sensor interface
- easier troubleshooting
- easier calibration
- easier removal/maintenance
- avoids communication conflicts with bottom DO/ORP

---

# DECISION 028 — H2S Sensor Candidate

Status:

VERIFY BEFORE PURCHASE

Current candidate:

SulfiLogger S1-1020 Low Range

Desired range:

approximately 0–0.5 mg/L dissolved H2S

Expected interface:

RS232
and
4–20 mA

Expected power:

12–28 VDC

System target:

12 V

Critical unresolved item:

manufacturer documentation or written confirmation must establish suitability for long-term continuous immersion in approximately 15–25 ppt brackish/saline water.

Until then:

DO NOT classify as LOCKED.

---

# DECISION 029 — H2S RS232 Interface

Status:

LOCKED IF S1-1020 IS SELECTED

RS232 must NOT connect directly to ESP32 UART pins.

Required architecture:

SulfiLogger
→ RS232
→ isolated RS232-to-TTL converter
→ ESP32 UART

Current preferred converter candidate:

Waveshare TTL TO RS232 (B)

Verify exact logic voltage and pin assignments before purchase/wiring.

---

# DECISION 030 — H2S Sensor Power

Status:

LOCKED IF S1-1020 IS SELECTED

The H2S sensor receives power from the 12 V sensor power system.

It is NOT powered from ESP32.

ESP32 remains USB / 5 V powered.

---

# DECISION 031 — Mid-Water Placement

Status:

PROVISIONAL

Initial target position:

radial location:
approximately 0.5–0.7 tank radius

vertical position:
approximately 0.4–0.6 water depth

Avoid:

- walls
- diffuser bubbles
- feeder
- water inlet
- strong return jet

Final position should be confirmed with spatial commissioning.

---

# DECISION 032 — Bottom-Risk Placement

Status:

PROVISIONAL

Bottom-risk sensors:

- DO-bottom
- ORP
- H2S

should characterize approximately the same near-bottom water environment.

Initial mounting target:

approximately 3–10 cm above tank bottom

Exact height depends on sensor dimensions and sensing-face geometry.

Do not bury standard water probes in sediment/sludge.

---

# DECISION 033 — Spatial Commissioning

Status:

LOCKED

Before permanent sensor placement, conduct a spatial characterization test.

Initial design:

3 radial positions
×
3 depths
=
9 locations

Potential parameters:

- DO
- temperature
- pH
- EC
- ORP
- turbidity

Evaluate under:

- baseline
- before feeding
- after feeding
- low-DO period
- modified aeration

Purpose:

select a representative MID location and a meaningful BOTTOM-risk location.

---

# DECISION 034 — Bypass Required

Status:

LOCKED

A small independent bypass loop will be built.

Initial intended use:

- Mg
- Ca
- flow
- potentially other flow-through sensors

The bypass is part of the monitoring platform and must receive a full engineering design and BOM.

---

# DECISION 035 — Bypass Scale

Status:

PROVISIONAL

Tank volume:

100 L

Initial conceptual flow:

approximately 50–150 mL/min

Preferred internal bypass volume:

approximately less than 50–100 mL where practical.

These numbers are NOT final until actual sensor and flow-cell requirements are verified.

Do not oversize the bypass.

---

# DECISION 036 — Bypass Pump Selection

Status:

OPEN / RESEARCH REQUIRED

Pump type has NOT yet been locked.

Codex must compare:

- peristaltic
- diaphragm
- miniature centrifugal

Selection criteria:

- continuous duty
- appropriate low-flow range
- 15–25 ppt compatibility
- flow stability
- tubing compatibility
- maintenance
- pressure
- pulsation
- ESP32 controllability

Do not purchase a pump until the bypass flow-cell and sensor requirements are known.

---

# DECISION 037 — Ca/Mg Measurements Require Validation

Status:

LOCKED

Do not treat real-time Ca/Mg ISE readings as unquestioned ground truth in 15–25 ppt water.

Potential interference includes:

- Na
- K
- Ca/Mg cross-response
- ionic strength
- temperature

Any real-time Ca/Mg sensing system must include an appropriate validation strategy.

Potential reference methods:

- IC
- ICP-OES

Exact sensor technology remains to be researched.

---

# DECISION 038 — NH4 Is Not TAN

Status:

LOCKED

NH4+ measurement must not automatically be labeled TAN.

TAN:

NH3-N + NH4+-N

If an NH4 ISE is used in saline water, it should initially be treated as:

high-frequency proxy / signal

unless validated.

Calculated NH3 must account for:

- pH
- temperature
- salinity

---

# DECISION 039 — Direct Purchase Preference

Status:

LOCKED

Prefer commercially available products that can be purchased directly online.

However:

scientific validity and reliability take priority over purchasing convenience.

Hardware classification must clearly distinguish:

DIRECT PURCHASE

QUOTE REQUIRED

VERIFY BEFORE PURCHASE

Do not select an inappropriate sensor solely because it is available on Amazon.

---

# DECISION 040 — Manufacturer Documentation Priority

Status:

LOCKED

Technical evidence priority:

1. manufacturer product page
2. manufacturer datasheet
3. manufacturer manual
4. manufacturer protocol documentation
5. authorized distributor
6. reputable supplier
7. generic marketplace only for non-critical accessories

Do not use marketplace descriptions as the primary source for electrical specifications.

---

# DECISION 041 — No Hallucinated Specifications

Status:

LOCKED

Never invent:

- voltage
- current
- wire color
- pin assignment
- baud rate
- Modbus register
- salinity rating
- immersion rating
- model number
- SKU
- thread size
- fitting dimension
- price

If evidence is unavailable, use:

NOT VERIFIED

or:

VERIFY BEFORE PURCHASE

Do not guess.

---

# DECISION 042 — Electronics Must Remain Dry

Status:

LOCKED

ESP32 boards, converters, WAGO connectors, terminal blocks and exposed electrical connections must remain outside the water.

Preferred enclosure:

IP65 / IP67 ABS enclosure.

Include:

- cable glands
- strain relief
- organized terminals
- appropriate fusing

Only components explicitly designed for immersion may enter the tank.

---

# DECISION 043 — Firmware Architecture

Status:

LOCKED

Sensor drivers must be independent from:

- Wi-Fi
- MQTT
- NTP
- buffering
- QC
- data transport

A failed sensor must not freeze an entire node.

Use:

- timeouts
- retries
- watchdog
- non-blocking operation

Avoid long blocking delay() calls in production firmware.

---

# DECISION 044 — Phase-1 First Integration Test

Status:

LOCKED

Do not initially attempt to bring every sensor online simultaneously.

Select one well-verified sensor and establish the complete path first:

Real sensor
→ ESP32-S3
→ parsed reading
→ UTC timestamp
→ sequence number
→ QC flag
→ Wi-Fi
→ MQTT
→ Raspberry Pi
→ database
→ dashboard

This becomes the reference implementation for all remaining nodes.

---

# DECISION 045 — Phase-1 Definition of Done

Status:

LOCKED

Phase 1 is complete only when the platform demonstrates:

- real sensor data
- ESP32 acquisition
- accurate UTC timestamps
- sequence numbers
- QC flags
- Wi-Fi communication
- MQTT
- Raspberry Pi ingestion
- permanent raw-data storage
- real-time dashboard

and survives:

- ESP32 reboot
- Wi-Fi interruption
- MQTT reconnect
- Raspberry Pi service restart

without silently corrupting measurements.

---

# DECISION 046 — Jetson Work Starts Later

Status:

LOCKED

Do not begin significant Jetson ML development until Phase 1 monitoring is operational.

Future ML-ready architecture should be prepared now, but ML implementation is later.

---

# DECISION 047 — Engineering Optimization Priority

Status:

LOCKED

Optimize in this order:

1. scientific validity
2. electrical safety
3. data integrity
4. reliability
5. maintainability
6. modularity
7. traceability
8. future expansion
9. cost

Do not sacrifice reliability to save:

- one converter
- one ESP32
- one power module
- a small amount of money

---

# Current Critical Open Decisions

The following items are NOT yet locked and require research.

## OPEN-01

Final pH sensor model.

## OPEN-02

Final EC / salinity sensor model.

## OPEN-03

Final turbidity / eTSS sensor model.

## OPEN-04

Final NH4 sensing strategy.

## OPEN-05

SEN0709 long-term 15–25 ppt compatibility.

## OPEN-06

SulfiLogger S1-1020 long-term 15–25 ppt compatibility.

## OPEN-07

Final Mg sensor technology/model.

## OPEN-08

Final Ca sensor technology/model.

## OPEN-09

Final bypass pump.

## OPEN-10

Final bypass flow meter.

## OPEN-11

Final bypass tubing size.

## OPEN-12

Final compact flow cell / sensor chamber.

## OPEN-13

NO2 real-time measurement strategy.

## OPEN-14

NO3 real-time measurement strategy.

## OPEN-15

Alkalinity online measurement strategy.

## OPEN-16

Final Raspberry Pi software stack.

Candidate stack:

- Mosquitto
- InfluxDB
- Grafana
- Python
- Docker Compose

Must be evaluated before locking.

---

# Change-Control Rule

Codex may discover evidence that suggests one of these decisions should change.

If so:

DO NOT silently modify this file.

Instead create a proposed change containing:

1. Decision ID
2. Existing decision
3. Proposed decision
4. Technical reason
5. Evidence / manufacturer source
6. Effect on other parts of the system
7. Required BOM changes
8. Required wiring changes
9. Risk of changing
10. Recommendation

Only after the decision is intentionally accepted should the status or content in DECISIONS.md be updated.

---

# Final Rule

When `SPEC.md`, `GOAL.md`, research findings, and `DECISIONS.md` conflict:

1. Do not guess.
2. Preserve safety.
3. Preserve scientific validity.
4. Identify the conflict.
5. Document it.
6. Propose a resolution.

Do not silently redesign the system.