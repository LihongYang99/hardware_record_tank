# Engineering instructions for Codex

`SPEC.md` is the binding engineering specification for Shrimp Trail. It defines
the approved architecture, safety rules, data-integrity requirements, and the
evidence standard for this project.

Before making **any engineering decision**—including research conclusions,
hardware selection, electrical wiring, sensor configuration, firmware design,
software architecture, implementation, testing, or procurement—every Codex
agent must read, in full:

1. `SPEC.md`
2. `GOAL.md`

If either file is missing, unreadable, or conflicts with a requested action,
stop before making that engineering decision and report the condition. Do not
invent the missing requirements or silently choose an alternative.

Treat these rules as mandatory:

- Do not begin implementation unless `GOAL.md` explicitly authorizes it.
- Do not silently change a sensor model, supply-voltage assumption, communication
  interface, pin/wiring logic, or safety boundary.
- Flag electrical, scientific, or protocol inconsistencies before proposing a
  change.
- Verify externally sourced electrical specifications, pinouts, serial settings,
  Modbus registers, cable colors, environmental ratings, and SKUs against current
  manufacturer documentation. Mark anything not proven as `NOT VERIFIED`.
- Preserve raw measurements, timestamps, sequence numbers, and QC state. Never
  turn invalid or missing readings into zero.
- Prefer the project priorities listed in `SPEC.md`; cost never overrides
  scientific validity, electrical safety, data integrity, or reliability.

If a direct user instruction conflicts with `SPEC.md` or `GOAL.md`, identify the
conflict explicitly and request resolution before changing the binding design.


# Project Instructions

This repository contains a research-grade real-time aquaculture monitoring platform.

Before performing ANY engineering, purchasing, wiring, plumbing, firmware, Raspberry Pi, database, or Jetson-related work:

1. Read `SPEC.md`.
2. Read `GOAL.md`.
3. Treat `SPEC.md` as the binding engineering specification.
4. Treat `GOAL.md` as the current project objective.
5. Do not silently override decisions or constraints in `SPEC.md`.

If research conflicts with `SPEC.md`:

- do not guess,
- do not silently modify the architecture,
- document the conflict,
- cite the evidence,
- propose a revision.

For hardware specifications, prioritize:

1. manufacturer documentation,
2. manufacturer manuals/datasheets,
3. authorized distributors.

Never invent:

- voltages,
- wire colors,
- pinouts,
- baud rates,
- Modbus registers,
- salinity compatibility,
- immersion ratings,
- model numbers,
- fittings,
- prices.

Use these statuses for hardware decisions:

- LOCKED
- RECOMMENDED
- OPTIONAL
- VERIFY BEFORE PURCHASE
- QUOTE REQUIRED
- REJECTED

Do not classify an unresolved component as LOCKED.

## Primary project priority

The first engineering milestone is:

Sensor
→ ESP32
→ UTC timestamp
→ Wi-Fi
→ MQTT
→ Raspberry Pi
→ database
→ real-time dashboard

Jetson Orin / ML is a later phase.

Do not allow Jetson work to delay or complicate the basic real-time monitoring platform.

## Data integrity

Every measurement must eventually contain:

- UTC sample timestamp
- gateway received timestamp where practical
- tank ID
- node ID
- sensor ID
- parameter
- value
- unit
- QC flag
- sequence number

Raw data must be preserved.

## Engineering principle

Optimize in this order:

1. scientific validity
2. electrical safety
3. data integrity
4. reliability
5. maintainability
6. modularity
7. expandability
8. cost
