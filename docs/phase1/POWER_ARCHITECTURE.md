# Phase-1 Power Architecture

**Revision:** 2026-09-02  
**Locked architecture preserved:** 12 V industrial-sensor rail; independent USB 5 V per ESP32 node; 3.3 V logic; Raspberry Pi separately powered.

## 1. One-line architecture

```text
GFCI/RCD-protected AC receptacle
├── listed Mean Well GST25A12-P1J (Class-II plug-in supply)
│   └── center-positive barrel → 2 A main protection → fused 12 V distribution
│       ├── 1 A DO1 → SEN0681
│       ├── 1 A MID_AUX → conditional SEN0710/SEN0711
│       ├── 1 A RDO → RDO Blue
│       ├── 1 A ORP → conditional SEN0709
│       ├── 1 A H2S → conditional S1-1020
│       └── 1 A BYPASS → EZO-PMP motor
├── listed USB 5 V supply → Node 1 ESP32 → local 3.3 V peripheral regulator
├── listed USB 5 V supply → Node 2 ESP32 → local 3.3 V peripheral regulator
├── listed USB 5 V supply → Node 3 ESP32 → local 3.3 V peripheral regulator
├── listed USB 5 V supply → Node 4 ESP32 → DFR0565 isolation → isolated 3.3 V pump/flow bus
└── approved Raspberry Pi PSU → Pi; database SSD powered per Pi/SSD limits
```

No AC mains conductor is cut or landed in a project-built box. Use listed plug-in supplies and a protected receptacle. All low-voltage distribution and electronics stay above splash level in dry enclosures with drip loops.

## 2. Domain table

| Domain | Nominal voltage | Source | Loads | Reference | Permitted crossings |
|---|---:|---|---|---|---|
| `S12` | 12 VDC | GST25A12-P1J | Industrial probes, EZO-PMP motor | `SGND12` | Isolated RS485/RS232/I2C only. |
| `N1-L`…`N4-L` | 5 V USB | One listed supply per ESP node | DevKit and local logic | Node-specific `LGND` | Wi-Fi; isolated converter logic side. Node grounds are not wired together. |
| `N1-P3`…`N3-P3` | 3.3 V | Pololu D24V5F3 from local USB 5 V | Waveshare RS485/RS232 logic; Atlas carriers on Node 1 | Same node `LGND` | 3.3 V GPIO only. |
| `N4-I3` | isolated 3.3 V | DFR0565 isolated 5 V → Pololu D24V5F3 | SLF3S and EZO-PMP control logic | `IGND4` | SDA/SCL only through DFR0565. |
| `PI` | Pi-specific | approved Pi PSU | Pi and permitted USB load | Pi ground | Ethernet/Wi-Fi; no hard-wired sensor signals. |

The 12 V negative is a shared sensor return, not protective earth and not ESP logic ground. Galvanic isolation prevents ground loops and keeps electrode/flow-path currents out of USB ground.

## 3. 12 V load calculation

Manufacturer nominal/max values available today are converted conservatively. “Design allocation” is the value used for supply and fuse review; it is not a claim about measured current.

| 12 V load | Documentation | Calculated current | Design allocation |
|---|---|---:|---:|
| SEN0681 | 0.2 W | 16.7 mA | 20 mA |
| SEN0710 conditional | 0.2 W | 16.7 mA | 20 mA |
| SEN0711 conditional | 0.3 W | 25.0 mA | 30 mA |
| RDO Blue | maximum 50 mA at 12 V | 50 mA | 50 mA |
| SEN0709 conditional | 0.4 W | 33.3 mA | 40 mA |
| EZO-PMP motor | approximately 400 mA at 12 V | ~400 mA | **600 mA** pending inrush measurement |
| S1-1020 conditional | maximum/start current absent | unknown | **unknown; purchase gate** |
| Wiring/auxiliary allowance | engineering allowance | — | 20 mA |
| **Known design subtotal, excluding H2S** | — | — | **780 mA** |

GST25A12-P1J rating is 12 V, 2.08 A, 25 W. Applying reserve to the entire working load:

- 40% headroom criterion: permitted continuous design load = `2.08 A / 1.40 = 1.486 A`.
- 25% headroom criterion: permitted continuous design load = `2.08 A / 1.25 = 1.664 A`.
- With the 0.780 A subtotal, the S1-1020 maximum/start allocation must be **≤0.706 A** to retain 40% headroom, or **≤0.884 A** to retain 25% headroom.

This is likely generous for an instrument but is not assumed. The GST25A remains **PROVISIONAL** until SulfiLogger supplies maximum/start current and the EZO-PMP startup current is measured. If either limit fails, propose a larger listed 12 V supply under change control; do not silently replace Decision 016.

At commissioning, log branch current at idle, sensor read, pump start, normal 80 mL/min flow, and fault/blockage. Recalculate headroom from measured worst-case values plus manufacturer maxima, not averages.

Source: [Mean Well GST25A specification](https://www.meanwell.com/Upload/PDF/GST25A/GST25A-SPEC.PDF).

## 4. Five-volt and 3.3-volt budgets

Each ESP32 node gets its own listed USB 5 V adapter rated at least 1 A continuous. Use 2 A or 3 A only if it is a reputable regulated supply; the larger rating does not force extra current into the board.

### Node 1

The current ISCCB-2 documentation lists about 35 mA at 3.3 V with EZO-pH and 43 mA with EZO-EC; the non-isolated EZO-RTD/SCCB and Waveshare TTL TO RS485 (B) add load. Use one 500 mA Pololu D24V5F3 and require:

- measured peripheral peak ≤400 mA (20% local reserve);
- P3V3 ≥3.20 V during simultaneous I2C/RS485 activity;
- no ESP brownout during Wi-Fi transmit;
- enclosure temperature below every module’s limit.

If the measured peripheral peak exceeds 400 mA, select a documented higher-current 3.3 V regulator from the same 5 V node domain under BOM change control. Do not parallel regulators.

### Nodes 2 and 3

One D24V5F3 supplies the converter logic. Require ≤400 mA measured peak. The sensor side remains powered from 12 V.

### Node 4

DFR0565 controller input is 5.0 ±0.15 V and draws about 15 mA unloaded. Its isolated output can supply 5 V at up to 150 mA. The downstream 3.3 V loads are approximately 6 mA maximum for the flow sensor plus about 13 mA for EZO-PMP logic, leaving ample converter/regulator margin. Confirm:

- DFR0565 input stays 4.85–5.15 V;
- isolated 3.3 V stays within the SLF3S 3.2–3.8 V limit;
- no continuity from `IGND4` to `LGND` with power removed;
- I2C high level is near 3.3 V, never 5 V.

Sources: [DFR0565](https://wiki.dfrobot.com/dfr0565), [SLF3S-4000B datasheet](https://sensirion.com/resource/datasheet/slf3s-4000b), [EZO-PMP datasheet](https://files.atlas-scientific.com/EZO_PMP_Datasheet.pdf), [ISCCB-2 datasheet](https://files.atlas-scientific.com/Isccb.pdf).

## 5. Protection and distribution

### 5.1 Main path

1. Verify the P1J barrel dimension and center-positive polarity before connecting the female screw adapter.
2. Place a 2 A fuse immediately after the adapter if the chosen branch block does not protect its feed.
3. Land positive and return on separate, covered distribution hardware. Label both ends of every branch.
4. Branch fuses are initially 1 A. This protects the 22 AWG distribution conductors and isolates faults; it is not a substitute for device protection.
5. Do not increase a fuse because it opens. Diagnose measured current, shorts, pump blockage, cable damage, and inrush first.

The sum of branch fuse ratings may exceed the supply rating; diversity is not used to size the PSU. The supply’s current limit and main fuse bound total current, while branch fuses isolate individual cable faults.

### 5.2 Voltage-drop criterion

For every installed branch, measure voltage at the device during its worst operating state. Target no more than 3% drop from the distribution output:

`Vdrop_target ≤ 0.36 V on the 12 V rail`.

If exceeded, shorten the run, increase conductor area, repair terminals, or split the distribution. Do not raise PSU voltage beyond its specification to compensate for poor wiring.

### 5.3 Motor-noise control

- Give the EZO-PMP its own fused home-run pair, physically separated from RS485 and electrode cables.
- Twist pump positive/return and keep the loop area small.
- Route signal and motor cables separately; cross at 90° where unavoidable.
- Do not add an external capacitor, TVS, or flyback part across an unknown internal controller without Atlas approval. First use the pump’s documented input and observe the rail with suitable isolated measurement technique.
- If conducted noise is demonstrated, select a manufacturer-approved filter and record before/after evidence.

## 6. Grounding, shielding, and isolation

### Required connections

- Waveshare TTL `GND` → node `LGND`.
- Waveshare isolated RS485 `SGND` → `SGND12` next to the sensor’s return.
- Waveshare TTL `GND` → Node 3 `LGND`; Waveshare RS232 `SGND` → S1-1020 RS232 signal ground.
- DFR0565 Controller `-` → Node 4 `LGND`; Module `-` → `IGND4`.

### Forbidden connections

- `SGND12 ↔ any LGND` external jumper.
- `IGND4 ↔ Node 4 LGND` external jumper.
- RDO shield ↔ `SGND12` or `LGND`.
- USB cable shield/ground used as a sensor return.
- Oscilloscope protective-earth clip placed across an isolation barrier.

RDO Blue’s shield is bonded at one end only to a legitimate chassis/functional-earth point. In a plastic, Class-II system with no such point, insulate it and document it as floating. Never fabricate a “ground” by connecting it to water, neutral, or sensor negative.

The Waveshare TTL TO RS485 (B), Waveshare RS232 converter, and DFR0565 provide interface isolation, but this design does not authorize field hipot testing across assembled electronics. Verify open circuit with a DMM and use manufacturer certificates for high-voltage isolation ratings.

## 7. Environmental and AC safety

- Use a GFCI/RCD-protected outlet and comply with local electrical rules for water-adjacent equipment.
- Place plug connections and power strips above the highest credible water line, outside splash/condensation zones.
- Form a drip loop below every enclosure entry.
- Use only gland sizes matched to measured cable OD; unused holes receive rated blanking plugs.
- Use a dry enclosure with strain relief, desiccant/humidity indication, and enough spacing for inspection.
- Do not put the GST supply, mains connections, WAGO blocks, ESP board, carrier boards, or cable splices over an open tank.
- Do not rely on an enclosure’s IP rating while its lid is open or a cable is unterminated.

## 8. Start, stop, and recovery behavior

| Event | Required behavior |
|---|---|
| 12 V sensor rail starts before ESP | Sensors may boot; no data link may back-power the ESP through isolated interfaces. |
| ESP starts before 12 V sensors | Driver reports `SENSOR_TIMEOUT`; other tasks/Wi-Fi continue. |
| Pi/router unavailable | ESP continues sampling and buffers locally; no power cycling loop. |
| Node 4 boots | It validates I2C devices/path state, then sends `DC,80,*`; it does not start blindly before the loop is ready. |
| EZO-PMP 20-day reset | `Dstart,*`, if enabled and tested, restarts near 105 mL/min; Node 4 detects status/flow transition and restores 80 mL/min. |
| Low flow/blockage | Stop pump after the configured persistence interval; latch alarm and require inspection. |
| Mains returns | Pi, broker, DB, nodes, and pump recover without manual data repair; startup events and clock state are recorded. |

An optional UPS may keep Pi/router alive, but Phase-1 acceptance still includes uncontrolled power-loss/restart testing so correctness does not depend on the UPS.

## 9. Power acceptance checklist

- [ ] Exact supply/adapter polarity and connector dimensions verified.
- [ ] Every fuse and branch label matches the wiring matrix.
- [ ] All loads disconnected: correct 12 V/5 V/3.3 V measured; no forbidden ground continuity.
- [ ] Loads added one by one with idle/active/start currents recorded.
- [ ] Worst-case 12 V subtotal plus H2S retains at least 25%, target 40%, PSU headroom.
- [ ] Each 12 V device sees ≤3% branch drop at worst case.
- [ ] Node 1 peripheral 3.3 V peak ≤400 mA and no Wi-Fi brownout.
- [ ] Node 4 isolated bus never exceeds 3.8 V at the SLF3S.
- [ ] Pump start produces no persistent sensor CRC/UART/I2C errors.
- [ ] Pi reports no undervoltage and SSD remains stable during sustained database writes.
- [ ] A complete power-cycle sequence passes without corrupt records or manual database repair.
