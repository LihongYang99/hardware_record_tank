# Phase-1 Sensor Verification and Selection

**Revision:** 2026-09-02  
**Operating matrix:** 100 L *L. vannamei*, 15–25 ppt, nominal 0–40 °C, continuous weeks to months  
**Rule:** manufacturer documentation is the primary source. Missing saline-life, material, current, protocol, or measurement-meaning evidence is a purchase gate rather than an inferred pass.

## 1. Selection summary

| Duty | Candidate | Electrical/interface evidence | 15–25 ppt evidence | Decision |
|---|---|---|---|---|
| Mid-water DO | DFRobot SEN0681 seawater version | 10–30 VDC, 0.2 W, RS485/Modbus | Product is explicitly the seawater version and has salinity compensation | **VERIFIED / recommended first integration** |
| Mid pH | Atlas ENV-50-pH-NT, SMA + EZO-pH + ISCCB-2 | 3.3–5 V circuit, I2C/UART, isolated carrier | Probe datasheet explicitly permits indefinite fresh/saltwater submersion to the connector | **RECOMMENDED — REQUIRES PROMOTION** |
| Mid EC/salinity | Atlas EC-KIT-10 + independent PT-1000 | K10, 10 µS/cm–1 S/cm probe; EZO-EC I2C/UART | Kit/product targets saltwater; probe permits indefinite saltwater submersion | **RECOMMENDED — REQUIRES PROMOTION** |
| Temperature compensation | Atlas PT-THRD + EZO-RTD | PT-1000, EZO-RTD I2C/UART | Probe permits indefinite saltwater submersion to SMA | **RECOMMENDED — REQUIRES PROMOTION** |
| Turbidity | DFRobot SEN0710 | 10–30 VDC, 0.2 W, RS485/Modbus | No explicit long-duration 15–25 ppt statement found | **VERIFY BEFORE PURCHASE** |
| Ammonia-N candidate | DFRobot SEN0711 | 10–30 VDC, 0.3 W, RS485/Modbus | No brackish matrix/interference validation found | **VERIFY BEFORE PURCHASE; do not label NH4/TAN** |
| Bottom DO | In-Situ RDO Blue, 10 m stripped/tinned cable P/N 0038620 | 8–36 VDC, ≤50 mA at 12 V, RS485/Modbus | Manufacturer states long-term fresh or saltwater use | **VERIFIED / recommended** |
| Bottom ORP | DFRobot SEN0709 | 10–30 VDC, 0.4 W, RS485/Modbus | No explicit long-duration saline statement found | **VERIFY BEFORE PURCHASE** |
| Dissolved H2S | SulfiLogger S1-1020 low range | 12–28 VDC, RS232 and 4–20 mA | Aquaculture use is stated, but 15–25 ppt immersion and maximum current are not | **VERIFY BEFORE PURCHASE** |
| Bypass flow | Sensirion SLF3S-4000B / evaluation kit | 3.2–3.8 V, ≤6 mA, I2C | Wetted materials documented; calibration fluids are water/IPA, not brackish water | **RECOMMENDED as flow-presence/relative meter; calibrate** |
| Mg/Ca | No approved online model | — | High ionic strength and cross-ion selectivity remain unresolved | **DEFERRED; external reference analysis** |
| NO2-N/NO3-N/alkalinity | No approved continuous model | — | Direct continuous validity not established | **DEFERRED to external reference methods** |

## 2. Mid-water sensors

### 2.1 Dissolved oxygen — DFRobot SEN0681

**Disposition:** VERIFIED for the first integration slice.

Manufacturer-published facts:

- Seawater optical DO probe, 10–30 VDC, 0.2 W.
- RS485, Modbus RTU; default address 1 and 4800 baud, 8 data bits, no parity, 1 stop bit.
- DO 0–20 mg/L and saturation 0–200%; ±3% full scale; 0.01 mg/L resolution.
- Temperature 0–40 °C; response no more than 60 s; IP68; 0.6 MPa; 5 m cable.
- Brown = supply positive, black = supply return, yellow = RS485 A, blue = RS485 B.
- Floating-point measurement registers use two consecutive 16-bit registers. Saturation starts at `0x0000`, DO at `0x0002`, and temperature at `0x0004`.
- Seawater salinity compensation is at `0x1020`; the documented default is 30 ‰. Pressure compensation is at `0x1022`.

Engineering controls:

1. Write a measured salinity value during commissioning and verify it by readback. Never silently use the 30 ‰ default for a 15–25 ppt experiment.
2. Poll at 5 s, enforce at least the manufacturer’s 200 ms command interval, and do not interpret 5 s polling as 5 s sensor response.
3. Store raw Modbus request/response bytes, decoded values, compensation setting, serial number, firmware, and calibration event.
4. Flag readings outside 0–20 mg/L or 0–200% and impossible/stuck/rate-of-change behavior; preserve the raw response.
5. Follow the documented two-point sequence: 100% oxygen environment then oxygen-free 5% sodium-sulfite solution, using register `0x1010` commands and recording raw echoes. For long-term use, begin with the manufacturer’s three-month calibration and 30-day cleaning intervals, shorten them if check standards/drift/fouling require it, and plan annual phosphor-film replacement.

Sources: [SEN0681 product wiki](https://wiki.dfrobot.com/sen0681), [SEN0681 Modbus protocol](https://wiki.dfrobot.com/sen0681/docs/21674).

### 2.2 pH — Atlas Industrial pH Gen 3

**Recommended chain:** `ENV-50-pH-NT (SMA termination) → EZO-pH → ISCCB-2 → Node 1 I2C`.

Why this chain is recommended:

- Probe: pH 0–14, ±0.002 stated accuracy, 95% response in 1 s, -5–99 °C, 100 psi, 3 m cable, and manufacturer-stated indefinite fresh/saltwater submersion up to the connector/tinned-lead boundary.
- `ENV-50-pH-NT` has no embedded temperature element, avoiding an undocumented mixed interface. Temperature compensation is supplied explicitly by the PT-1000 channel.
- EZO-pH: 3.3–5 V logic, UART/I2C, default I2C address `0x63`, one reading per second, external temperature compensation commands.
- ISCCB-2 provides the required probe/circuit galvanic isolation. The manufacturer warns not to join isolated and non-isolated grounds.

Controls and gates:

- Select the **SMA** termination to match ISCCB-2; verify termination on the purchase order.
- Bench-calibrate with fresh pH 4/7/10 solutions at experiment temperature; record solution lot/expiry and slope.
- Push the latest valid PT-1000 temperature before each pH read. If temperature is stale or missing, retain the reading with `COMPENSATION_STALE` or `COMPENSATION_MISSING`.
- This recommendation resolves OPEN-01 technically but requires formal promotion in `DECISIONS.md`.

Sources: [industrial pH probe datasheet](https://files.atlas-scientific.com/IpH_probe.pdf), [EZO-pH product documentation](https://atlas-scientific.com/embedded-solutions/ezo-ph-circuit/), [ISCCB-2 datasheet](https://files.atlas-scientific.com/Isccb.pdf).

### 2.3 EC and salinity — Atlas EC-KIT-10

**Disposition:** RECOMMENDED — REQUIRES PROMOTION. Procure the current `KIT-306` SMA PT-1000 Temperature Kit with the **Threaded PT-1000** option; it packages PT-THRD, EZO-RTD, and the non-isolated `SCCB` carrier.

The kit combines a K10 conductivity probe, EZO-EC circuit, electrically isolated carrier, and appropriate high-conductivity calibration standards. The K10 probe range (10 µS/cm to 1 S/cm) covers brackish/saline aquaculture. The EZO-EC circuit reports conductivity, salinity, TDS, and specific gravity, supports external temperature compensation, and has default I2C address `0x64`.

Use the independent PT-1000 temperature as the sole compensation source. Store raw conductivity as the primary measurement; salinity is a synchronized/derived output with its algorithm/firmware version recorded. Do not treat salinity as a second independent sensor.

Calibration:

- Use 12,880 µS/cm and 150,000 µS/cm standards supplied with the kit or their documented replacements.
- Calibrate at the experiment temperature and verify with an independent certified standard near the tank’s expected conductivity.
- Record cell constant, standards, lot/expiry, temperature, operator, timestamps, and before/after values.

**Rejected alternative:** DFRobot SEN0707 is documented for only 10–20,000 µS/cm and salinity 0–11,476 ppm. That does not cover the 15–25 ppt operating range with defensible margin, so it is rejected for this duty.

Sources: [Atlas K10 kit](https://atlas-scientific.com/kits/conductivity-k-10-kit/), [K10 probe](https://atlas-scientific.com/probes/conductivity-probe-k-10/), [K10 probe datasheet](https://files.atlas-scientific.com/l-EC_K_10_probe.pdf), [EZO-EC circuit](https://atlas-scientific.com/embedded-solutions/ezo-conductivity-circuit/), [DFRobot SEN0707](https://wiki.dfrobot.com/sen0707/).

### 2.4 Temperature — Atlas PT-THRD and EZO-RTD

**Disposition:** RECOMMENDED — REQUIRES PROMOTION.

- Threaded PT-1000 with SMA connector; manufacturer permits indefinite fresh/saltwater immersion up to the connector.
- EZO-RTD supports PT-100/PT-1000, one reading per second, UART/I2C, default I2C address `0x66`.
- The manufacturer indicates probe isolation is normally unnecessary for RTD; use the non-isolated carrier and keep the SMA/connector dry.

Use this channel to compensate pH and EC. The DO probes retain their own documented temperature/compensation paths. Cross-compare all available temperatures daily; do not automatically substitute one channel for another without recording the substitution.

Sources: [KIT-306 SMA PT-1000 Temperature Kit](https://atlas-scientific.com/kits/sma-temperature-kit/?attribute_temperature-probe=Threaded+PT-1000), [PT-THRD datasheet](https://files.atlas-scientific.com/PT-THRD-probe.pdf), [EZO-RTD circuit](https://atlas-scientific.com/embedded-solutions/ezo-rtd-temperature-circuit/), [non-isolated SCCB carrier](https://atlas-scientific.com/carrier-boards/ezo-carrier-board/).

### 2.5 Turbidity — DFRobot SEN0710

**Disposition:** VERIFY BEFORE PURCHASE.

Verified electrical/protocol facts: 10–30 VDC, 0.2 W, RS485/Modbus RTU, 0–1000 NTU, ±5% full scale, 0.1 NTU resolution, response ≤30 s, temperature channel, default address 1 at 4800 8N1, and the same brown/black/yellow/blue power/A/B colors as other DFRobot industrial probes.

Unresolved gate: the manufacturer pages reviewed do not explicitly warrant long-term 15–25 ppt immersion. Obtain written confirmation for wetted materials, seals, cable transition, cleaning chemistry, and expected maintenance life in brackish shrimp water.

If approved:

- change its Modbus address to 2 before it joins the Node 1 bus;
- mount with at least the documented clearances and keep the upper cable transition as directed by the setup guide;
- clean the optical window on a condition-based schedule beginning at 30 days and verify/calibrate at least every three months;
- publish `turbidity_ntu`; do **not** publish eTSS until paired gravimetric TSS samples establish a tank-specific, versioned model with uncertainty.

Sources: [SEN0710 product page](https://www.dfrobot.com/product-3104.html), [setup guide](https://wiki.dfrobot.com/sen0710/docs/23383), [Modbus protocol](https://wiki.dfrobot.com/sen0710/docs/23385).

### 2.6 Ammonia candidate — DFRobot SEN0711

**Disposition:** VERIFY BEFORE PURCHASE; excluded from the initial purchase release.

The manufacturer documents 10–30 VDC, 0.3 W, RS485/Modbus, a reported “ammonia nitrogen” channel 0–100 mg/L, integrated pH and temperature, and default 4800 8N1 operation. It does not provide sufficient evidence for selectivity, ionic-strength correction, chloride interference, long-term 15–25 ppt performance, or equivalence to TAN/NH4 in this matrix.

Scientific naming rule:

- Preserve the reported quantity initially as `ammonia_n_reported_mg_l` with the manufacturer’s exact basis in metadata.
- Never rename it `nh4_mg_l`, `tan_mg_l`, or toxic un-ionized `nh3_mg_l` without a validated conversion and external reference comparison.
- TAN is the combined ammonia pool; the un-ionized toxic fraction depends on pH, temperature, and salinity/ionic strength. A second pH/temperature channel inside an ISE assembly does not by itself establish TAN accuracy.

Release gate: written saline-matrix evidence plus a validation plan using at least low/mid/high tank-matrix spikes and independent laboratory TAN measurements. Until it passes, reserve Modbus address 3 but do not add it to the operational bus.

Sources: [SEN0711 wiki](https://wiki.dfrobot.com/sen0711/), [SEN0711 protocol](https://wiki.dfrobot.com/sen0711/docs/23361), [US EPA ammonia overview](https://www.epa.gov/caddis/ammonia), [EPA saltwater ammonia criteria document](https://www.epa.gov/sites/default/files/2015-08/documents/ambient_water_quality_criteria_for_ammonia_saltwater_-_1989_0.pdf).

## 3. Bottom-risk sensors

### 3.1 Dissolved oxygen — In-Situ RDO Blue

**Disposition:** VERIFIED and recommended for Node 2.

Corrected purchase configuration: **10 m stripped-and-tinned cable, P/N 0038620**. The prior project text associating P/N 0038620 with 3 m is not supported by the current manufacturer documentation.

Manufacturer-published facts:

- Designed for long-term fresh- or saltwater monitoring.
- DO 0–60 mg/L and 0–600%; ±0.1 mg/L over 0–20 mg/L and ±2% of reading over 20–60 mg/L; 0.01 mg/L resolution.
- Temperature -5–50 °C, ±0.1 °C; salinity compensation can be fixed or updated in real time.
- 8–36 VDC; ≤50 mA at 12 V during reading and approximately 2 mA idle; one reading per second.
- RS485 Modbus RTU; default 19200 baud, 8 data bits, even parity, one stop bit.
- Red = external power, black = return, blue = RS485 positive, green = RS485 negative, silver = cable shield/chassis only.

Controls:

- Blue (+) is wired to Waveshare `A+` and green (-) to `B-`. Because vendors use inconsistent A/B labels, the commissioning fallback is strictly controlled: after verifying power, address, 19200 8E1, and CRC logic, power down and swap only A/B if no valid response is obtained.
- Bond the silver shield at one dry-panel chassis/PE point only. Do not bond it to the isolated RS485 return at both ends.
- Update the configured salinity from the validated mid-water EC/salinity value when fresh; otherwise retain the last known value and set a compensation-stale flag.

Sources: [RDO Blue product page](https://in-situ.com/us/rdo-blue/), [RDO Blue manual](https://in-situ.com/pub/media/support/documents/RDO-Blue-Manual.pdf), [RDO Blue interface specification](https://in-situ.com/pub/media/support/documents/rdoBlueInterfaceSpec-2020-08-10.pdf).

### 3.2 ORP — DFRobot SEN0709

**Disposition:** VERIFY BEFORE PURCHASE.

Verified: 10–30 VDC, 0.4 W, RS485/Modbus, -1999 to 1999 mV, ±5 mV, 1 mV resolution, response <1 s, integrated temperature, default 4800 8N1/address 1, IP68 and 0.6 MPa claims.

Unverified: the current manufacturer material does not explicitly establish weeks-to-months continuous use in 15–25 ppt with the expected biofouling/ sulfide environment. Obtain written material/seal/reference-junction compatibility and maintenance guidance. If accepted, place it on its own Waveshare TTL TO RS485 (B)/UART because its 4800 8N1 settings differ from the RDO Blue 19200 8E1 channel and because bottom-risk channels should fail independently.

Sources: [SEN0709 product page](https://www.dfrobot.com/product-3102.html), [SEN0709 protocol](https://wiki.dfrobot.com/sen0709/docs/23382).

## 4. Dissolved H2S — SulfiLogger S1-1020

**Disposition:** VERIFY BEFORE PURCHASE and retain the dedicated Node 3 architecture.

Verified facts:

- Direct dissolved H2S measurement; low-range option around 0–0.5 mg/L is offered.
- 12–28 VDC/4–20 mA loop and RS232 interface; ±5% accuracy, 1% full-scale detection limit, response <25 s, 0–40 °C, 10 m depth; 316L body.
- Firmware 2.7+ RS232 protocol: 38400 baud, 8N1, no flow control, ASCII, case-sensitive, LF terminator; sensor acts as slave. `GETDATA ALL` returns the data set; `#`, `!`, and `^` are ACK, NAK, and abort control characters.
- RS232 data cable: brown sensor RXD, blue sensor TXD, black signal ground. The separate power cable also uses brown/blue, for positive/negative power, so both cables must be permanently tagged before termination.

Open purchase gates:

1. written confirmation of continuous 15–25 ppt compatibility, including membrane/body/seal/cable materials and cleaning constraints;
2. maximum and startup current at 12 V (missing from reviewed documents), needed to close the PSU calculation;
3. exact order code for the 0–0.5 mg/L range, cable lengths, connector/termination option, included maintenance kit, and replacement interval;
4. verification that the desired RS232 output and 4–20 mA power/interface configuration can be used simultaneously as ordered.

The baseline data path uses the RS232 output through a Waveshare Industrial Isolated TTL-to-RS232 (B). Do not use a non-isolated MAX3232 board in the wet-sensor system.

Sources: [SulfiLogger S1-1020](https://sulfilogger.com/product/sulfilogger-1020/), [installation manual](https://sulfilogger.com/wp-content/uploads/2024/02/C00620V02-SulfiLogger-sensor-Installation-manual_200.pdf), [RS232 protocol v1.04](https://sulfilogger.com/wp-content/uploads/2023/06/SulfiLogger_RS232-protocol_104.pdf), [Waveshare isolated converter](https://www.waveshare.com/product/ttl-to-rs232-b.htm).

## 5. Bypass flow sensing

### Sensirion SLF3S-4000B

**Recommended procurement:** one `EK-SLF3S-4000B` evaluation kit for commissioning; it includes the sensor, clamp, USB cable, 15 cm adapter cable, and 30 cm pigtail. The bare standard sensor does not include the necessary cable/clamp.

Verified facts: ±600 mL/min bidirectional water range; stated accuracy is the greater of ±5% of measured value or ±0.5 mL/min up to 300 mL/min; 3.2–3.8 V, ≤6 mA; I2C address `0x08`; per-word CRC; approximately 58 µL internal volume; PPS/316L/epoxy wetted materials; 5–6 mm tubing ID recommended.

Limits and controls:

- Calibration is documented for water/isopropanol, not 15–25 ppt saline water. At 60, 80, and 100 mL/min, compare 10-minute collected mass (density-corrected) to the sensor and store a calibration factor/version.
- Use it for flow-present, trend, and alarm service. Do not claim the manufacturer’s water accuracy in brackish water before that test.
- Its electrical reference can contact the fluid path; isolate the Node 4 I2C bus with DFR0565. DFR0565 isolated output is 5 V, so a Pololu D24V5F3 regulator must reduce the isolated bus supply to 3.3 V. The same isolated 3.3 V bus supplies the low-voltage EZO-PMP control circuit. Never connect 5 V directly to the flow sensor.
- Use the evaluation-kit pigtail by **connector pin number**, not assumed wire color: pin 1 IRQ (unused), 2 SDA, 3 VDD, 4 GND, 5 SCL, 6 NC.

Sources: [SLF3S-4000B catalog](https://sensirion.com/products/catalog/SLF3S-4000B), [SLF3S-4000B datasheet](https://sensirion.com/resource/datasheet/slf3s-4000b), [DFR0565 isolation module](https://wiki.dfrobot.com/dfr0565), [Pololu D24V5F3](https://www.pololu.com/product/2842/specs).

## 6. Mg, Ca, NO2-N, NO3-N, alkalinity, and TAN reference strategy

No continuous model is approved for these channels. This is a deliberate scientific constraint, not an omitted design task.

### Mg and Ca

The tank matrix has high ionic strength and a large background of competing ions. No reviewed manufacturer package simultaneously establishes selective Mg/Ca measurement, 15–25 ppt validation, long-duration wet operation, an open digital interface, and suitable flow-cell geometry. Node 4 therefore reserves electrical and plumbing capacity but does not invent probe models or ports.

Phase-1 reference plan:

- take time-aligned grab samples from the bypass sample port;
- use an accredited laboratory method such as ICP-OES/ICP-MS or a validated ion-chromatography/titration method appropriate to saline water;
- store sample ID, collection UTC, preservation, method, dilution, detection limits, uncertainty, and laboratory result in the calibration/reference table;
- evaluate an online candidate only by paired samples across the actual 15–25 ppt, temperature, pH, and concentration range.

### NO2-N, NO3-N, alkalinity, and TAN

Use external colorimetric/titrimetric or accredited laboratory reference methods until a method is shown to control chloride/salinity interference and sample/reagent waste for a 100 L system. Continuous automated wet-chemistry analyzers can consume sample and reagents, create waste, and introduce maintenance burdens that must be explicitly quantified before being connected.

**Evaluated external screening candidate:** Hanna Instruments `HI97115C` Marine Master. The current manufacturer package is a stand-alone/Bluetooth marine photometer with methods for alkalinity, ammonia, calcium, magnesium, nitrate low/high range, nitrite ultra-low range, pH, and phosphate. It is useful for rapid time-aligned screening, but it is **not approved as the primary reference** for this project:

- its calcium range is 200–600 ppm and magnesium range is 1000–1800 ppm; proportional dilution of normal seawater to 15–25 ppt can place Ca and especially Mg below these ranges;
- its methods are described for reef/marine aquarium water, not explicitly the complete 15–25 ppt brackish interval;
- current manufacturer pages/manual revisions conflict on the nitrite ULR upper limit (200 versus 800 ppb), so the exact instrument firmware, manual, method, reagent lot, and basis must travel with every result;
- the ammonia page labels the range “as NH3” while describing reaction with ammonia and ammonium; it must not be used as TAN evidence without a method-basis confirmation and paired laboratory comparison.

If acquired, use `HI97115C` for screening/trend checks only, validate each method at 15, 20, and 25 ppt against the contracted laboratory, run the `HI97105-11` CAL Check set, keep blanks/duplicates/spikes, and export results with sample UTC and method/reagent metadata. Do not return tested sample or reagents to the tank.

Sources: [HI97115 manufacturer product page and method ranges](https://hannainst.com/marine-master-waterproof-wireless-multiparameter-photometer-HI97115.html), [current quick-reference/manual download](https://www.documentation.hannainst.com/manuals/download/6977), [HI97105-11 CAL Check set](https://hannainst.com/CAL-Check-Standards-for-HI97105-Cuvette-Kit-HI97105-11.html).

Minimum comparison requirements for any future analyzer:

1. manufacturer method explicitly covers the sample salinity or documents dilution/interference correction;
2. result basis is explicit (`as N`, `as NO2−`, `as NO3−`, `as NH3-N`, `as CaCO3`, etc.);
3. blank, standard, duplicate, matrix spike, detection/quantitation limits, and uncertainty are recorded;
4. sample removal and reagent waste are not returned to the tank;
5. the device provides a documented interface and raw result/status codes.

## 7. Manufacturer questions that block purchases

Send and archive written responses using the exact wording below.

### DFRobot SEN0709 and SEN0710

“Please confirm whether this exact SKU is approved for uninterrupted immersion for months in aerated aquaculture water at 15–25 ppt salinity and 24–32 °C. Please identify all wetted materials, seal/cable limits, allowed cleaning chemicals, calibration interval, and any chloride/sulfide or biofouling limitations.”

### DFRobot SEN0711

“Please provide the measurand definition and reference method for the ‘ammonia nitrogen’ output; selectivity/interference data for Na+, K+, Ca2+, Mg2+, chloride and pH; and accuracy/maintenance data in 15–25 ppt shrimp aquaculture water. Is the value TAN as N, NH4-N, or another basis?”

### SulfiLogger S1-1020

“For the exact 0–0.5 mg/L S1-1020 order code, confirm continuous months-long 15–25 ppt immersion, all wetted materials, cleaning/calibration/membrane interval, 12 V maximum/start current, included cable/termination, and simultaneous RS232 plus powered-loop behavior.”

## 8. Sensor acceptance tests

No recommended sensor becomes operational solely from a successful serial reply.

1. Photograph SKU, serial, firmware, cable tags, and wetted assembly; record them in the asset register.
2. Inspect seals/connectors; keep all electronics, cable splices, SMA/BNC connectors, and converters dry.
3. Confirm supply polarity and voltage with the sensor disconnected, then connected.
4. Capture 100 valid raw messages at the exact protocol settings; require zero unexplained CRC/framing errors.
5. Perform zero/standard/air-saturation or manufacturer-required calibration and an independent check standard where applicable.
6. Run a 72 h tank-matrix soak with reference comparisons and inspect drift/fouling.
7. Exercise power loss, unplugged sensor, shorted/swapped data pair, stale compensation, implausible value, and recovery cases.
8. Promote the component only after purchase gates and acceptance evidence are recorded under change control.
