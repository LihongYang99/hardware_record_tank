# Exact Wiring Matrix and ESP32 GPIO Allocation

**Revision:** 2026-09-05
**Controller:** ESP32-S3-DevKitC-1-N8R8, one independent USB 5 V supply per node  
**Conventions:** `P5V` = node USB-derived 5 V; `LGND` = ESP/logic ground; `P3V3` = Pololu-regulated peripheral 3.3 V; `SGND12` = isolated sensor-side 12 V return; `IGND4` = Node 4 isolated I2C ground.

## 1. Non-negotiable electrical boundaries

1. Never connect 12 V, RS232, or RS485 A/B directly to an ESP32 pin.
2. Never connect `LGND` to `SGND12`, the RS485-side `SGND` of the Waveshare TTL TO RS485 (B), the RS232-side SGND, or Node 4 `IGND4`.
3. The Waveshare TTL TO RS485 (B) does not supply 12 V sensor power. Sensors receive 12 V from the fused main sensor rail.
4. Node 4’s DFR0565 isolated side produces 5 V. The SLF3S-4000B maximum supply is 3.8 V, so its VDD must come from the downstream Pololu 3.3 V regulator.
5. The EZO-PMP’s motor rail is 12 V, while its data/control VCC is 3.3 V on the isolated Node 4 bus. These are different pins and must be labeled before insertion.
6. No shield is connected at both ends. RDO Blue’s silver drain/shield goes to one verified dry chassis/functional-earth point only, never to an ESP pin or sensor return. If no legitimate earth/chassis point exists in the all-plastic, Class-II installation, insulate it and record it as floating rather than inventing a bond.

Before applying power, perform continuity tests for all forbidden pairs above. Required result is open circuit except where a manufacturer device internally references two pins; any such result must be documented before installation.

## 2. GPIO policy

| GPIO | Policy | Reason/use |
|---:|---|---|
| 0, 3, 45, 46 | Do not use for sensors | ESP32-S3 strapping/startup risk. |
| 19, 20 | Reserve | Native USB D−/D+ on DevKitC-1. |
| 43, 44 | Reserve | UART0 programming/diagnostic console. |
| 48 | Reserve | Board-dependent RGB/status LED use; avoid a revision-specific dependency. |
| 8 | I2C SDA where assigned | Node 1 local chemistry bus; Node 4 isolated bypass bus. |
| 9 | I2C SCL where assigned | Node 1 local chemistry bus; Node 4 isolated bypass bus. |
| 17 | UART1 TX where assigned | Nodes 1 and 3; reserved service UART on Node 4. |
| 18 | UART1 RX where assigned | Nodes 1 and 3; reserved service UART on Node 4. |
| 15 | UART2 TX | Node 2 ORP link. |
| 16 | UART2 RX | Node 2 ORP link. |

ESP32-S3 routes UART signals through its GPIO matrix, so these are firmware assignments, not claims that each pin has only one hardware function. The reserved pins protect USB, programming, and boot behavior. Source: [ESP32-S3-DevKitC-1 guide](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html).

## 3. Common node power wiring

Apply this matrix to Nodes 1–3. Node 4 does **not** use N-P02–N-P07; its DFR0565 and downstream regulator are wired only by §7 so the pump/flow bus remains isolated.

| Wire ID | From | To | Gauge/color | Check |
|---|---|---|---|---|
| N-P01 | Listed 5 V USB adapter | ESP32 DevKit USB connector | supplied USB cable | 4.75–5.25 V at board under Wi-Fi load; no brownout log. |
| N-P02 | DevKit pin marked `5V`/`VBUS` on the received board | Pololu D24V5F3 `VIN` | 24 AWG red | Confirm pin marking against received board guide; never use `3V3` as input. |
| N-P03 | DevKit `GND` | Pololu `GND` | 24 AWG black | Same `LGND`. |
| N-P04 | Pololu `VOUT` | Peripheral `VCC` distribution terminal | 24 AWG orange | 3.30 V ± regulator tolerance before peripherals. |
| N-P05 | Pololu `GND` | Peripheral `GND` distribution terminal | 24 AWG black | Same `LGND`; no connection to sensor side. |
| N-P06 | ESP GPIO signal | Interface module logic signal | 24 AWG assigned | 0–3.3 V only. |
| N-P07 | ESP `LGND` | Interface module logic GND | 24 AWG black | Required for TTL/I2C reference on non-isolated side. |

Do not power Node 1 peripheral circuits from the DevKit’s onboard 3.3 V regulator. The external Pololu rail carries the Atlas carriers and Waveshare converter logic load; measure peak current and keep it below the 400 mA design load for the nominal 500 mA board.

## 4. Node 1 — mid-water

### 4.1 Logical allocation

| Bus | ESP pins | Devices | Settings/address |
|---|---|---|---|
| UART1 → Waveshare TTL TO RS485 (B) | TX GPIO17, RX GPIO18 | SEN0681; conditional SEN0710; conditional SEN0711 | Modbus RTU 4800, 8N1; addresses 1, 2, 3 respectively. |
| I2C | SDA GPIO8, SCL GPIO9 | EZO-pH, EZO-EC, EZO-RTD | 100 kHz initial; `0x63`, `0x64`, `0x66`. |

### 4.2 UART/RS485 converter

Waveshare labels describe the converter’s direction: its TTL `TXD` output drives ESP RX; its TTL `RXD` input is driven by ESP TX. The approved exact product is Waveshare TTL TO RS485 (B), Part No. 23778.

| Wire ID | From | To | Domain/color | State |
|---|---|---|---|---|
| N1-R01 | P3V3 | Waveshare TTL `VCC` | logic/orange | 3.3 V. |
| N1-R02 | LGND | Waveshare TTL `GND` | logic/black | Logic only. |
| N1-R03 | ESP GPIO17 UART1 TX | Waveshare TTL `RXD` | logic/white | ESP→converter. |
| N1-R04 | Waveshare TTL `TXD` | ESP GPIO18 UART1 RX | logic/green | Converter→ESP. |
| N1-R05 | Waveshare RS485 `A+` | yellow RS485 distribution | isolated/yellow | To each approved DFR sensor yellow A. |
| N1-R06 | Waveshare RS485 `B-` | blue RS485 distribution | isolated/blue | To each approved DFR sensor blue B. |
| N1-R07 | Waveshare RS485 `SGND` | SGND12 distribution | isolated/black | Common-mode reference on sensor side. |
| N1-R08 | Waveshare `120R` switch | OFF for initial point-to-point bench wiring | — | Enable only if the converter is at a physical bus end and termination is required. |

### 4.3 RS485 sensor cables

| Wire ID | Sensor conductor | Destination | Fuse/setting | Status |
|---|---|---|---|---|
| N1-D01 | SEN0681 brown | fused `+12V_DO1` | 1 A branch | Installed. |
| N1-D02 | SEN0681 black | SGND12 | — | Installed. |
| N1-D03 | SEN0681 yellow | RS485 A | address 1 | Installed. |
| N1-D04 | SEN0681 blue | RS485 B | 4800 8N1 | Installed. |
| N1-T01 | SEN0710 brown | fused `+12V_MID_AUX` | 1 A branch | Conditional. |
| N1-T02 | SEN0710 black | SGND12 | — | Conditional. |
| N1-T03 | SEN0710 yellow | RS485 A | address 2 | Conditional; program alone before bus connection. |
| N1-T04 | SEN0710 blue | RS485 B | 4800 8N1 | Conditional. |
| N1-A01 | SEN0711 brown | fused `+12V_MID_AUX` | 1 A branch | Reserved only; do not install before validation. |
| N1-A02 | SEN0711 black | SGND12 | — | Reserved only. |
| N1-A03 | SEN0711 yellow | RS485 A | address 3 | Reserved; program alone. |
| N1-A04 | SEN0711 blue | RS485 B | 4800 8N1 | Reserved. |

The first build has only SEN0681, making this a point-to-point link. Additional fixed 5 m sensor leads create a panel-centered multidrop topology rather than an ideal daisy chain. Add one device at a time and perform a 24 h CRC/timeout test. If errors exceed the acceptance limit, do not add arbitrary termination; use an isolated RS485 hub or a separately approved converter/UART plan.

### 4.4 Atlas I2C chain

All controller-side grounds below are `LGND`. The pH and EC probe grounds remain isolated internally by their carriers.

| Wire ID | From | To | Note |
|---|---|---|---|
| N1-I01 | ESP GPIO8 | I2C SDA trunk | 100 kHz initially. |
| N1-I02 | ESP GPIO9 | I2C SCL trunk | Keep local dry wiring <20 cm. |
| N1-I03 | P3V3 | ISCCB-2 pH carrier `VCC` | Manufacturer allows 3.3–5 V. |
| N1-I04 | LGND | pH carrier `GND` | Controller side only. |
| N1-I05 | I2C SDA | pH carrier `TX/SDA` | EZO-pH `0x63`. |
| N1-I06 | I2C SCL | pH carrier `RX/SCL` | Do not reverse labels. |
| N1-I07 | pH carrier `OFF` | NC, individually insulated | Manufacturer default is enabled with OFF open; do not ground. |
| N1-I08 | ENV-50-pH-NT SMA | pH carrier SMA | Hand-tighten; connector remains dry. |
| N1-I09 | P3V3 | EC-KIT-10 isolated carrier `VCC` | EZO-EC `0x64`. |
| N1-I10 | LGND | EC carrier `GND` | Controller side only. |
| N1-I11 | I2C SDA | EC carrier `TX/SDA` | — |
| N1-I12 | I2C SCL | EC carrier `RX/SCL` | — |
| N1-I13 | EC carrier `OFF` | NC, individually insulated | Default enabled; do not ground. |
| N1-I14 | K10 probe connector | EC carrier probe connector | Match the kit’s exact connector; keep dry. |
| N1-I15 | P3V3 | EZO-RTD/SCCB `VCC` | Non-isolated carrier. |
| N1-I16 | LGND | EZO-RTD/SCCB `GND` | — |
| N1-I17 | I2C SDA | EZO-RTD/SCCB `TX/SDA` | Address `0x66`. |
| N1-I18 | I2C SCL | EZO-RTD/SCCB `RX/SCL` | — |
| N1-I19 | PT-THRD SMA | SCCB carrier SMA | Keep connector dry. |

Power off and measure total pull-up resistance from SDA and SCL to P3V3 before connection. Multiple Atlas carriers may each include pullups. Target a bus pull-up that meets I2C rise time without excessive sink current; remove/disable redundant pullups only by documented board provision, never by an improvised trace cut.

Before the shared bus is assembled, configure and identify each EZO circuit individually in accordance with its manufacturer procedure, switch it to I2C mode, verify the expected address, and enable protocol lock only after recovery has been demonstrated. A device that still boots in UART mode is not connected to the shared SDA/SCL trunk.

## 5. Node 2 — bottom-risk

RDO Blue and ORP use two separate UART/Waveshare TTL TO RS485 (B) links because their serial formats differ and their failure domains are intentionally separate.

### 5.1 RDO Blue link — UART1

| Wire ID | From | To | Setting/note |
|---|---|---|---|
| N2-D01 | P3V3 | Waveshare-A TTL `VCC` | 3.3 V. |
| N2-D02 | LGND | Waveshare-A TTL `GND` | — |
| N2-D03 | ESP GPIO17 UART1 TX | Waveshare-A TTL `RXD` | 19200, 8E1. |
| N2-D04 | Waveshare-A TTL `TXD` | ESP GPIO18 UART1 RX | — |
| N2-D05 | Waveshare-A RS485 `A+` | RDO Blue **blue**, RS485 positive | See controlled A/B fallback below. |
| N2-D06 | Waveshare-A RS485 `B-` | RDO Blue **green**, RS485 negative | — |
| N2-D07 | Waveshare-A RS485 `SGND` | SGND12 | Isolated-side reference. |
| N2-D08 | RDO Blue red | fused `+12V_RDO` | 1 A dedicated branch. |
| N2-D09 | RDO Blue black | SGND12 | Power return. |
| N2-D10 | RDO Blue silver shield | verified chassis/functional-earth bar in dry panel, or insulated NC if none exists | One end only; never SGND12 or LGND. Record the chosen state. |
| N2-D11 | Waveshare-A `120R` switch | OFF initially | Enable only after bus-end and termination verification. |

Controlled A/B fallback: if power, device address, 19200 8E1, request bytes, and CRC implementation are verified but no CRC-valid response is received, power both devices off, swap **only** N2-D05/N2-D06, and repeat. Record the final polarity; do not hot-swap.

### 5.2 Conditional SEN0709 ORP link — UART2

| Wire ID | From | To | Setting/note |
|---|---|---|---|
| N2-O01 | P3V3 | Waveshare-B TTL `VCC` | Conditional after saline approval. |
| N2-O02 | LGND | Waveshare-B TTL `GND` | — |
| N2-O03 | ESP GPIO15 UART2 TX | Waveshare-B TTL `RXD` | 4800, 8N1. |
| N2-O04 | Waveshare-B TTL `TXD` | ESP GPIO16 UART2 RX | — |
| N2-O05 | Waveshare-B RS485 `A+` | SEN0709 yellow | Address 1. |
| N2-O06 | Waveshare-B RS485 `B-` | SEN0709 blue | — |
| N2-O07 | Waveshare-B RS485 `SGND` | SGND12 | — |
| N2-O08 | SEN0709 brown | fused `+12V_ORP` | 1 A dedicated branch. |
| N2-O09 | SEN0709 black | SGND12 | — |
| N2-O10 | Waveshare-B `120R` switch | OFF initially | Enable only after bus-end and termination verification. |

## 6. Node 3 — dedicated dissolved H2S

This matrix is conditional on the exact S1-1020 purchase release.

### 6.1 Logic and isolated RS232 data

| Wire ID | From | To | Note |
|---|---|---|---|
| N3-S01 | P3V3 | Waveshare TTL `VCC` | 3.3 V. |
| N3-S02 | LGND | Waveshare TTL `GND` | Logic side only. |
| N3-S03 | ESP GPIO17 UART1 TX | Waveshare TTL `RXD` | Sensor protocol 38400, 8N1, no flow. |
| N3-S04 | Waveshare TTL `TXD` | ESP GPIO18 UART1 RX | — |
| N3-S05 | Waveshare RS232 `TXD` | S1-1020 RS232 cable **brown sensor RXD** | Converter sends to sensor. |
| N3-S06 | S1-1020 RS232 cable **blue sensor TXD** | Waveshare RS232 `RXD` | Sensor sends to converter. |
| N3-S07 | S1-1020 RS232 cable **black GND** | Waveshare RS232 `SGND` | Do not connect to LGND. |

### 6.2 Sensor power

| Wire ID | From | To | Note |
|---|---|---|---|
| N3-P01 | fused `+12V_H2S` | S1-1020 **power cable brown** | Power cable must carry a permanent `POWER` tag. |
| N3-P02 | SGND12 | S1-1020 **power cable blue** | Do not confuse with blue TXD on the separate RS232 cable. |

No additional jumper is installed between the power cable’s blue return and the RS232 cable’s black signal ground; use the manufacturer-provided interface as shipped. Verify with the manufacturer whether they are internally common and document the measured behavior. The 4–20 mA output is capped and insulated in Phase 1 unless a separately isolated receiver is approved.

## 7. Node 4 — bypass pump and flow

### 7.1 Controller side of I2C isolation

| Wire ID | From | To | Note |
|---|---|---|---|
| N4-C01 | DevKit `5V`/`VBUS` | DFR0565 **Controller** `+` | DFR0565 requires 5.0 ±0.15 V. Verify under load. |
| N4-C02 | LGND | DFR0565 Controller `-` | Controller side only. |
| N4-C03 | ESP GPIO9 I2C SCL | DFR0565 Controller `C` | 100 kHz initial. |
| N4-C04 | ESP GPIO8 I2C SDA | DFR0565 Controller `D` | — |

### 7.2 Isolated 3.3 V bus generation

| Wire ID | From | To | Note |
|---|---|---|---|
| N4-I01 | DFR0565 **Module** `+` isolated 5 V output | Pololu D24V5F3 `VIN` | Never connect directly to flow-sensor VDD. |
| N4-I02 | DFR0565 Module `-` | Pololu `GND` | Defines IGND4. |
| N4-I03 | Pololu `VOUT` | isolated 3.3 V terminal | Measure 3.30 V before device insertion. |
| N4-I04 | Pololu `GND` | IGND4 terminal | Common only on isolated side. |
| N4-I05 | DFR0565 Module `C` | isolated SCL terminal | To both pump and flow meter. |
| N4-I06 | DFR0565 Module `D` | isolated SDA terminal | To both pump and flow meter. |

### 7.3 Sensirion evaluation-kit pigtail

Wire by the numbered PicoBlade/pigtail pin, not by an unverified color.

| Wire ID | SLF3S-4000B pin | Destination | Note |
|---|---|---|---|
| N4-F01 | 1 `IRQ` | NC, insulated | Not required. |
| N4-F02 | 2 `SDA` | isolated SDA | I2C address `0x08`; validate word CRC. |
| N4-F03 | 3 `VDD` | isolated 3.3 V | Allowed range 3.2–3.8 V. |
| N4-F04 | 4 `GND` | IGND4 | — |
| N4-F05 | 5 `SCL` | isolated SCL | — |
| N4-F06 | 6 `NC` | NC, insulated | — |

### 7.4 EZO-PMP

The pump’s motor input and five-wire data/control cable are separate.

| Wire ID | From | To | Note |
|---|---|---|---|
| N4-P01 | fused `+12V_BYPASS` | EZO-PMP keyed motor `+` | 1 A branch. Verify keyed connector polarity before insertion. |
| N4-P02 | SGND12 | EZO-PMP keyed motor `-` | Sensor-side domain. |
| N4-P03 | isolated 3.3 V | EZO-DC **red `VCC`** | Pump logic accepts 3.3–5.5 V. |
| N4-P04 | IGND4 | EZO-DC **black `GND`** | Internal pump construction may reference motor domain; DFR0565 maintains isolation from ESP. |
| N4-P05 | isolated SCL | EZO-DC **white `RX/SCL`** | Pump set to I2C, address `0x67`. |
| N4-P06 | isolated SDA | EZO-DC **green `TX/SDA`** | — |
| N4-P07 | EZO-DC **blue `INT`** | NC, insulated | DFR0565 isolates only SDA/SCL; infer run state from command/status/flow. |

Node 4 startup sequence:

1. initialize isolated I2C at 100 kHz and verify flow sensor `0x08` plus pump `0x67` separately;
2. read pump identity/status and the stored calibration state;
3. read zero/baseline flow with pump stopped;
4. send `DC,80,*` only after flow-path valves/caps are in the run position;
5. require measured flow to enter 60–100 mL/min within 30 s;
6. if low flow persists, stop pump, raise `FLOW_LOW`, and require inspection—do not repeatedly run a blocked pump;
7. after any pump reset/status discontinuity, reissue `DC,80,*`. The documented 20-day continuous-mode reset is an expected event and must be tested.

`Dstart,*` may be configured only as a tested fail-safe; it starts at approximately 105 mL/min, not the 80 mL/min setpoint. Node 4 must correct it promptly and the high-flow limit remains 120 mL/min.

GPIO17/18 remain reserved for a future isolated service UART. Mg/Ca interfaces and addresses are unassigned; no wires are installed until exact models are validated.

## 8. 12 V distribution matrix

| Branch | Positive path | Return path | Nominal installed load | Fuse |
|---|---|---|---|---|
| `DO1` | PSU + → main protection → branch fuse → SEN0681 brown | SEN0681 black → SGND12 → PSU − | 0.2 W ≈17 mA at 12 V | 1 A |
| `RDO` | branch fuse → RDO red | RDO black → SGND12 | ≤50 mA | 1 A |
| `ORP` | branch fuse → conditional SEN0709 brown | SEN0709 black → SGND12 | 0.4 W ≈33 mA | 1 A |
| `H2S` | branch fuse → power-cable brown | power-cable blue → SGND12 | unknown | 1 A provisional; manufacturer max-current gate |
| `BYPASS` | branch fuse → EZO-PMP motor + | motor − → SGND12 | ~400 mA at 12 V | 1 A |
| `MID_AUX` | branch fuse → conditional SEN0710/SEN0711 brown | black returns → SGND12 | 0.2 W + 0.3 W ≈42 mA | 1 A |

The common sensor return is a deliberate 12 V distribution net. It does not authorize tying that net to any ESP/USB ground.

## 9. Commissioning order and electrical sign-off

1. With all loads removed, verify PSU barrel polarity, 12 V, each fuse path, and no continuity to any node `LGND`.
2. Power each USB node alone; verify P5V, P3V3, boot, native USB/console, and Wi-Fi current stability.
3. Add one interface module at a time. Recheck that its isolation-side ground is open to LGND before sensor attachment.
4. Configure RS485 addresses with exactly one sensor connected.
5. Connect SEN0681 first and capture 100 CRC-valid frames.
6. Add Node 1 I2C devices one at a time; scan only expected addresses and measure rise time/pull-up resistance.
7. Commission RDO, H2S, and Node 4 only after their purchase gates.
8. Torque/secure terminals, tug-test ferrules, install strain relief and drip loops, then photograph both ends of every labeled conductor.

Sign-off record must contain `wire_id`, from/to terminal photographs, continuity result, insulation/isolation result, unloaded/loaded voltage, current, technician, UTC, drawing revision, and deviations.
