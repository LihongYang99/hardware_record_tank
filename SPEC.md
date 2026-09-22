# Aquaculture Real-Time Monitoring Platform
## Engineering Specification

Version: 0.2
Status: Engineering Specification — tank description updated 2026-09-14

---

# 1. Project Purpose

Build a modular, research-grade, real-time water-quality monitoring platform for a round polyethylene Litopenaeus vannamei aquaculture tank with a nominal capacity of 340 L (90 US gallons). Actual operating water volume is to be confirmed.

The primary objective is reliable continuous sensing and timestamped data acquisition.

The initial system must support:

Sensor
→ ESP32
→ timestamp
→ Wi-Fi
→ MQTT
→ Raspberry Pi
→ database
→ real-time dashboard

Future expansion:

Raspberry Pi / database
→ NVIDIA Jetson Orin
→ edge AI / ML / anomaly detection

Machine learning is NOT part of the minimum viable monitoring platform.

---

# 2. Experimental System

Tank description (user-provided; revision authorized 2026-09-14):

- Shape and material: round polyethylene tank.
- Nominal capacity: 340 L (90 US gallons; rounded nominal capacities).
- Internal diameter: 39 in (99.06 cm).
- Tank depth: 20 in (50.8 cm). This is tank depth, not operating water depth.
- Actual operating water depth and volume: NOT VERIFIED; confirm before using them in installation geometry or water-volume-dependent calculations.

This description supersedes the previous 100 L tank assumption. It is based on
the tank description supplied by the user; the exact manufacturer/model and
manufacturer documentation are NOT VERIFIED. Do not assume a flat bottom or
calculate operating water volume from an ideal cylinder without verification.

Species:

Litopenaeus vannamei

Water:

Brackish / saline

Target salinity:

15–25 ppt

Experiment duration:

weeks to months

Operating requirement:

continuous 24/7 monitoring

Environment:

high humidity
salt aerosol
possible splashing
long-term sensor immersion

All electronics must remain outside the water unless explicitly designed for submersion.

---

# 3. Primary System Requirements

The system SHALL:

1. continuously acquire water-quality measurements;
2. timestamp every measurement;
3. use UTC internally;
4. preserve raw sensor data;
5. detect missing data;
6. identify sensor communication errors;
7. recover automatically from Wi-Fi interruption;
8. recover automatically from MQTT interruption;
9. recover after ESP32 reboot;
10. support multiple independent ESP32 sensor nodes;
11. transmit data to Raspberry Pi;
12. store measurements locally on Raspberry Pi;
13. provide real-time visualization;
14. remain functional without Jetson Orin;
15. support future Jetson Orin edge computation without changing the sensor firmware architecture.

---

# 4. Computing Hardware

## 4.1 ESP32

Preferred controller:

Espressif ESP32-S3-DevKitC-1-N8R8

Preferred use:

sensor acquisition nodes

Important electrical constraints:

Board input:
5 V via USB preferred

GPIO logic:
3.3 V

NEVER apply:

5 V directly to GPIO
12 V directly to GPIO
RS232 directly to GPIO
RS485 A/B directly to GPIO

Signal conversion must be used where required.

---

## 4.2 Raspberry Pi

Already owned.

Primary role:

- MQTT broker
- central data ingestion
- database
- dashboard
- experiment metadata
- system health monitoring
- data export
- local backup
- time infrastructure

The Raspberry Pi should be the always-on gateway.

---

## 4.3 NVIDIA Jetson Orin

Already owned.

Jetson is NOT required for basic monitoring.

Future role:

- anomaly detection
- sensor fusion
- water-quality prediction
- shrimp stress prediction
- computer vision
- edge inference
- predictive control

The monitoring system must continue operating normally if Jetson is offline.

---

# 5. Node Architecture

Preferred initial architecture:

## NODE 01 — MID

Potential sensors:

- DO-mid
- pH
- EC
- salinity
- temperature
- turbidity / eTSS
- NH4+ if technically valid

---

## NODE 02 — BOTTOM

Sensors:

- DO-bottom
- ORP-bottom

---

## NODE 03 — H2S

Dedicated ESP32.

Sensor:

- dissolved H2S

Reason for dedicated node:

- specialized interface
- easier calibration
- easier maintenance
- easier troubleshooting
- isolation from DO/ORP node

---

## NODE 04 — BYPASS

Sensors:

- Mg2+
- Ca2+
- flow

Possible functions:

- bypass pump status
- bypass flow monitoring
- additional flow-cell sensors

Node allocation may be modified only when a clear engineering advantage exists.

Any modification must be documented.

---

# 6. Current Sensor Candidates

These are current candidates, not automatically approved.

Each must be independently verified.

## Mid DO

Candidate:

DFRobot SEN0681
Seawater Optical Dissolved Oxygen Sensor

Expected interface:

RS485 / Modbus RTU

Expected power:

approximately 10–30 VDC

System target:

12 VDC

Status:

VERIFY against current manufacturer documentation.

---

## Bottom DO

Candidate:

In-Situ RDO Blue

Preferred version:

stripped-and-tinned cable

Previously identified candidate:

3 m
P/N 0038620

Expected interface:

RS485 / Modbus RTU

Expected supply:

8–36 VDC

System target:

12 V

Status:

VERIFY.

---

## Bottom ORP

Candidate:

DFRobot SEN0709

Expected interface:

RS485 / Modbus RTU

Expected supply:

10–30 VDC

System target:

12 V

Status:

VERIFY SALINITY COMPATIBILITY.

---

## H2S

Candidate:

SulfiLogger S1-1020 Low Range

Desired range:

approximately 0–0.5 mg/L dissolved H2S

Expected interface:

RS232
and
4–20 mA

Expected supply:

12–28 VDC

System target:

12 V

Important unresolved requirement:

continuous long-term immersion in 15–25 ppt brackish/saline water must be verified.

Status:

VERIFY BEFORE PURCHASE.

---

# 7. Sensor Scientific Requirements

Every sensor selected must be evaluated for:

- measurement principle
- target analyte
- measurement range
- accuracy
- resolution
- response time
- drift
- temperature effects
- salinity effects
- ionic interference
- biofouling
- maintenance
- calibration
- continuous-duty operation

A sensor must not be selected only because it produces an electronic signal.

It must be scientifically appropriate for the water chemistry.

---

# 8. Salinity Requirement

The tank operates at:

15–25 ppt.

For every submerged probe, documentation must establish one of:

PASS:
explicitly compatible with this salinity range

VERIFY:
manufacturer confirmation required

FAIL:
not appropriate for long-term deployment

IP68 alone does NOT satisfy this requirement.

---

# 9. Power Architecture

Preferred main sensor supply:

Mean Well GST25A12-P1J

Output:

12 VDC
2.08 A
approximately 25 W

Primary use:

industrial sensors

The complete design must calculate total current consumption before approval.

Minimum desired power reserve:

25–40%.

---

# 10. Electrical Power Domains

The design must distinguish:

## 12 V

industrial sensor supply

## 5 V

ESP32 development-board input where appropriate

## 3.3 V

ESP32 GPIO logic

Supply voltage and signal voltage must never be confused.

---

# 11. Power Distribution

Expected concept:

AC mains
→ Mean Well 12 V PSU
→ DC barrel adapter
→ fuse
→ distribution terminal
→ sensors

Preferred connector:

5.5 × 2.1 mm female barrel
→ screw terminal

Preferred distribution:

WAGO 221 series

Separate nodes shall exist for:

+12 V
GND

Never combine unrelated signals in the same terminal.

---

# 12. Permanent Wiring

Preferred:

22–24 AWG stranded copper hookup wire

Suggested color convention:

Red:
+12 V

Black:
GND

Yellow:
RS485 A

Blue:
RS485 B

Ferrules are preferred for stranded wire entering screw terminals.

Loose Dupont wiring should only be used for prototyping.

---

# 13. RS485 Requirements

RS485 A/B are communication lines.

They do NOT normally provide sensor power.

Typical industrial RS485 probe therefore requires:

V+
GND
A
B

Approved RS485 converter:

Waveshare TTL TO RS485 (B), Part No. 23778

Reason for revision:

DFRobot DFR0845 is unavailable. The user approved the Waveshare replacement on
2026-09-05. The replacement provides galvanic isolation, accepts 3.3–5 V TTL
logic power, and exposes screw terminals labeled VCC, GND, TXD, RXD, SGND, A+,
and B-. Industrial sensors still receive 12 V from their own fused branches;
the converter does not supply sensor power.

Superseded converter:

DFRobot DFR0845 — REJECTED FOR PROCUREMENT because it is unavailable.

Isolation is preferred because sensors operate in conductive saline water.

---

# 14. Shared RS485 Bus

Multiple sensors may share one RS485 bus ONLY when:

- baud rate is compatible
- data bits are compatible
- parity is compatible
- stop bits are compatible
- device addresses are unique

Every device must have a documented Modbus address.

Duplicate addresses are prohibited.

Codex must explicitly identify which devices:

CAN SHARE BUS

CAN SHARE AFTER RECONFIGURATION

CANNOT SHARE BUS

---

# 15. RS232 Requirements

RS232 is NOT ESP32 TTL UART.

Any RS232 sensor requires:

RS232
→ RS232-to-TTL converter
→ ESP32 UART

Direct connection of RS232 to ESP32 GPIO is prohibited.

For the H2S node, an isolated converter is preferred.

Current candidate:

Waveshare TTL TO RS232 (B)

Must be verified before purchase.

---

# 16. Analog Sensors

If analog sensors are selected:

ESP32 built-in ADC should not automatically be assumed to be sufficient for scientific measurements.

External precision ADC should be evaluated.

Potential candidate:

ADS1115

Input voltage must always remain within ADC limits.

---

# 17. 4–20 mA Sensors

If 4–20 mA is used:

the design must include an appropriate input stage.

Required checks:

- current loop topology
- burden resistor
- ADC range
- isolation
- sensor power
- ground configuration

Do not connect a 4–20 mA loop directly to an ESP32 ADC.

---

# 18. Timestamp Specification

Timestamping is a CRITICAL system requirement.

Every measurement must contain:

timestamp_utc

Format:

ISO 8601

Preferred example:

2026-09-03T01:23:45.382Z

Millisecond resolution is preferred when useful.

---

# 19. Timestamp Sources

ESP32 nodes shall synchronize using NTP.

NTP synchronization should occur:

- during boot
- periodically during operation

Loss of NTP connectivity must NOT stop sensor acquisition.

Each node should maintain:

last_ntp_sync
uptime
clock_sync_status

---

# 20. Dual Timestamping

Where possible store:

sample_timestamp_utc

and:

gateway_received_timestamp_utc

This allows later discrimination between:

sampling delay
network delay
processing delay

For online chemistry instruments also allow:

sample_time
analysis_complete_time
result_time

---

# 21. Sequence Numbers

Every node must include a monotonically increasing:

sequence_number

Example:

1001
1002
1003
1005

The gateway must detect that:

1004

was missing.

This is required for scientific data-integrity analysis.

---

# 22. Measurement Schema

Every measurement should follow a common logical structure.

Required fields:

timestamp_utc
gateway_received_timestamp_utc
tank_id
experiment_id
node_id
sensor_id
sensor_model
location
parameter
value
unit
qc_flag
sequence_number

Recommended additional fields:

raw_value
sensor_status
RSSI
uptime_ms
firmware_version
calibration_id
temperature_compensation
salinity_compensation

---

# 23. QC Flags

Minimum QC states:

OK

WARMUP

OUT_OF_RANGE

COMMUNICATION_ERROR

STALE

SENSOR_FAULT

CALIBRATION_REQUIRED

NETWORK_BUFFERED

COMPENSATION_MISSING

MANUAL_INVALID

Invalid measurements must NOT silently become zero.

---

# 24. Local Buffering

Temporary network failure is expected.

The system shall support:

store-and-forward

Original measurement timestamps must be preserved.

Determine appropriate use of:

RAM
LittleFS
external storage

Avoid excessive flash wear.

---

# 25. MQTT

Preferred transport:

MQTT

Preferred broker location:

Raspberry Pi

Required design elements:

- topic convention
- QoS
- reconnect
- Last Will and Testament
- health messages
- node heartbeat
- sensor measurement messages

---

# 26. Raspberry Pi Data Stack

Evaluate a maintainable stack using components such as:

Mosquitto

InfluxDB

Grafana

Node-RED

Python

Docker Compose

The exact stack must be justified.

Minimum capabilities:

- MQTT broker
- ingestion
- raw database storage
- dashboard
- CSV export
- automatic restart
- health monitoring

---

# 27. Data Storage Layers

The database must preserve:

## RAW

original data at original acquisition frequency

## SYNCHRONIZED

common time grids such as:

1 min
5 min

## DERIVED

Examples:

DO_mid_minus_DO_bottom

DO_5min_mean

DO_5min_min

dDO_dt

dORP_dt

Mg_Ca_ratio

NH3_N

Raw data must never be destroyed by aggregation.

---

# 28. Approximate Sampling Targets

Initial targets:

DO:
1–5 s

temperature:
5–10 s

pH:
5–10 s

EC:
~10 s

ORP:
10–30 s

turbidity:
10–30 s

H2S:
30–60 s

NH4:
30–120 s

Mg/Ca:
1–5 min

flow:
1–10 s

These values are starting points only.

Final polling frequency must respect sensor response time and manufacturer guidance.

---

# 29. Bypass Requirement

A physical bypass loop must be built for selected sensors.

Tank nominal capacity:

340 L (90 US gallons); actual operating water volume is NOT VERIFIED.
Use the tank geometry and verification limits in Section 2.

Preferred conceptual flow:

50–150 mL/min

This value must be validated.

Preferred total bypass internal volume:

less than approximately 50–100 mL

when technically possible.

---

# 30. Bypass Architecture

Desired conceptual path:

Tank
→ intake strainer
→ tubing
→ pump
→ flow control
→ flow meter
→ compact sensor chamber / flow cell
→ Mg sensor
→ Ca sensor
→ return tubing
→ tank

Every physical transition must be specified.

---

# 31. Bypass Pump

The selected pump must be evaluated for:

- continuous duty
- appropriate low flow
- 15–25 ppt compatibility
- tubing compatibility
- pressure
- pulsation
- controllability
- reliability
- heat generation

Avoid grossly oversized pumps.

Compare:

peristaltic
diaphragm
centrifugal

before selection.

---

# 32. Bypass Plumbing BOM

The finished BOM must include:

pump
tubing
tube ID
tube OD
intake strainer
flow-control valve
flow meter
flow cell
check valve if needed
T/Y fittings
reducers
hose barbs
compression fittings
O-rings
clamps
bulkhead fittings if required
return fitting
bubble trap if required

All dimensions must match.

---

# 33. Mg/Ca Scientific Constraint

Do NOT assume Ca and Mg ISE measurements are automatically accurate in 15–25 ppt saline water.

Evaluate:

Na interference
K interference
Ca/Mg cross-sensitivity
ionic strength
temperature
reference electrode
matrix matching
drift

Any real-time Ca/Mg system must include a validation strategy against a laboratory method such as:

IC
or
ICP-OES

if scientifically appropriate.

---

# 34. NH4 / TAN Scientific Constraint

NH4+ is not the same measurement as TAN.

TAN:

NH3-N + NH4+-N

If an NH4 ISE is used in saline water, treat it initially as:

high-frequency proxy

unless properly validated.

NH3 calculations must incorporate:

pH
temperature
salinity

---

# 35. Physical Placement

MID station should represent bulk water.

Initial target:

approximately 0.5–0.7 tank radius

and

approximately 0.4–0.6 water depth

Final placement should be verified experimentally.

Avoid:

wall
air diffuser
large bubbles
feed entry
water inlet
return jet

---

# 36. Bottom Station

DO-bottom
ORP
H2S

should characterize approximately the same near-bottom environment.

Initial mounting range:

approximately 3–10 cm above bottom

depending on probe geometry.

Do not bury standard probes in sludge.

---

# 37. Spatial Commissioning

Before final installation perform spatial mapping.

Suggested:

3 radial positions
×
3 depths
=
9 sampling locations

Evaluate:

DO
temperature
pH
EC
ORP
turbidity

under:

baseline
before feeding
after feeding
low-DO period
changed aeration

Use results to choose permanent positions.

---

# 38. Environmental Protection

All dry-side electronics require protection against:

splashes
salt aerosol
humidity
condensation

Preferred:

IP65/IP67 ABS enclosure

Include:

cable glands
strain relief
fuses
organized terminal blocks

Do not place exposed breadboards beside the tank during long-term operation.

---

# 39. Firmware Design Requirements

Firmware must be modular.

Sensor drivers must be separated from:

Wi-Fi
MQTT
timestamping
buffering
QC

A failed sensor should not freeze an entire node.

Use:

timeouts
retries
watchdog
non-blocking scheduling

Avoid long delay() usage.

---

# 40. Configuration

Configuration must include:

tank_id
experiment_id
node_id
sensor_id
sampling interval
Modbus address
serial settings
MQTT host

Credentials must not be committed to a public repository.

Use a secrets template.

---

# 41. Calibration Metadata

Calibration records must contain:

sensor_id
timestamp
standard
calibration type
operator
pre-calibration response
post-calibration response
notes

Calibration events must be linkable to later measurements.

---

# 42. Experiment Events

The system should support timestamped experiment events including:

feeding
carbon addition
water exchange
chemical dosing
aeration changes
sensor cleaning
sensor calibration
maintenance

This information will later support time-series and ML interpretation.

---

# 43. Jetson Integration Constraint

ESP32 firmware must NOT depend on Jetson.

Preferred:

ESP32
→ MQTT
→ Pi

Jetson later subscribes to MQTT or retrieves data through a defined service.

Removing the Jetson must not stop monitoring.

---

# 44. Purchase Decision Status

Every hardware item must receive one of:

LOCKED

RECOMMENDED

OPTIONAL

VERIFY BEFORE PURCHASE

QUOTE REQUIRED

REJECTED

Items with unresolved critical compatibility issues cannot be classified as LOCKED.

---

# 45. Evidence Requirement

Important specifications must be supported by current manufacturer documentation.

Never invent:

- wiring
- colors
- communication parameters
- Modbus registers
- voltage
- current
- salinity rating
- immersion rating
- prices
- SKU
- fittings

Unknown information must be marked:

NOT VERIFIED.

---

# 46. Final Hardware Documentation Requirement

For every sensor produce:

1. exact product
2. exact cable
3. exact power source
4. exact converter
5. exact pinout
6. exact ESP32 pin
7. communication settings
8. mounting location
9. calibration method
10. purchase information

The documentation must be sufficient to physically assemble the system without guessing.

---

# 47. Phase 1 Definition of Done

Phase 1 is COMPLETE when a real sensor measurement successfully travels through:

Sensor
→ ESP32
→ accurate timestamp
→ Wi-Fi
→ MQTT
→ Raspberry Pi
→ database
→ real-time dashboard

and successfully survives:

ESP32 reboot
Wi-Fi interruption
MQTT reconnect
temporary network loss

while preserving:

timestamps
sequence numbers
QC status
raw data.

---

# 48. Main Engineering Principle

Priorities, in order:

1. Scientific validity
2. Electrical safety
3. Data integrity
4. Reliability
5. Maintainability
6. Modularity
7. Expandability
8. Cost

Cost reduction must never override the first four priorities.
