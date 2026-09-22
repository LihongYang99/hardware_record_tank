# Phase-1 Bill of Materials

**Revision:** 2026-09-05
**Basis:** four ESP32 nodes, one 100 L tank, 15–25 ppt, one Raspberry Pi gateway  
**Procurement rule:** only rows marked **RELEASE** may be ordered without additional technical evidence. **HOLD** rows have a stated gate. Prices are intentionally omitted because they are time- and region-dependent.

Quantities marked `+1 spare` are reliability stock, not installed load. Vendor substitutions must preserve every voltage, isolation, wetted-material, interface, connector, environmental, and dimensional requirement and must be recorded before purchase.

## 1. Release groups

- **Release A — first integration:** one SEN0681, one ESP32 node, one Waveshare TTL TO RS485 (B), independent 5 V USB power, 12 V distribution, Pi data stack, and bench wiring/test equipment.
- **Release B — verified expansion:** pH/EC/PT-1000 chain and RDO Blue after the first path passes its acceptance test.
- **Release C — conditional:** turbidity, ORP, H2S, NH4, pump, flow meter, and final chamber only after their row-specific gates.

Do not place a single combined order that bypasses these release gates.

## 2. Core compute and communications

| ID | Qty | Manufacturer / exact item | Installed at | Status | Notes / gate |
|---|---:|---|---|---|---|
| C-01 | 4 + 1 spare | Espressif ESP32-S3-DevKitC-1-N8R8 | Nodes 1–4 | **RELEASE** | N8R8 = 8 MB flash + 8 MB PSRAM; confirm exact module marking at receipt. |
| C-02 | 3 + 1 spare | Waveshare TTL TO RS485 (B), Part No. 23778, rail-mount galvanically isolated converter | Node 1 ×1; Node 2 ×2 | **LOCKED — user-approved DFR0845 replacement** | TTL power 3.3–5 V; use 3.3 V. Screw terminals: VCC/GND/TXD/RXD and SGND/A+/B-. It does not supply 12 V sensor power. |
| C-03 | 1 + 1 spare | Waveshare Industrial Isolated TTL to RS232 (B) | Node 3 | **HOLD with H2S** | Buy only if S1-1020 is selected; 3.3 V TTL side. |
| C-04 | 1 + 1 spare | DFRobot DFR0565 Gravity I2C Digital Signal Isolator | Node 4 | **HOLD with flow meter** | Controller input 5 V; isolated output 5 V/150 mA; I2C high level 3.3 V. |
| C-05 | 4 + 1 spare | Pololu D24V5F3, item 2842, 3.3 V/500 mA step-down regulator | Nodes 1–3 peripheral rails; Node 4 isolated side | **RELEASE** | Keeps peripheral load off the DevKit regulator; Node 4 converts DFR0565’s isolated 5 V to SLF3S/pump-safe 3.3 V. No reverse-voltage protection; add keyed wiring. |
| C-06 | 2 + 1 spare | Short PH2.0-4P Gravity cables for DFR0565 only | Node 4 dry box | **HOLD with flow meter** | The Waveshare RS485 converters use screw terminals and do not need Gravity cables. Map DFR0565 cable continuity before use. |
| C-07 | 4 | Listed 5 V USB supply, ≥1 A continuous, one per node | Nodes 1–4 | **RELEASE** | Independent supplies; use the DevKit’s USB input. Record exact approved SKU before order. No shared sensor-rail buck. |
| C-08 | 4 + 1 spare | Data/power USB cable matching the received DevKitC-1 connector | Nodes | **RELEASE after connector check** | Current DevKit revisions must be physically checked; do not assume Micro-USB vs USB-C from a reseller photo. |

Manufacturer sources: [ESP32-S3-DevKitC-1 guide](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html), [Waveshare TTL TO RS485 (B)](https://www.waveshare.com/ttl-to-rs485-b.htm), [DFR0565](https://wiki.dfrobot.com/dfr0565), [Waveshare isolated RS232](https://www.waveshare.com/product/ttl-to-rs232-b.htm), [Pololu 2842](https://www.pololu.com/product/2842/specs).

## 3. Sensors and analytical channels

| ID | Qty | Manufacturer / exact item | Node | Status | Purchase gate / included interface |
|---|---:|---|---|---|---|
| S-01 | 1 | DFRobot SEN0681 seawater optical dissolved oxygen sensor | 1 | **RELEASE A** | First integration sensor; RS485, 5 m cable. |
| S-02 | 1 | Atlas Scientific Industrial pH Probe Gen 3, `ENV-50-pH-NT`, **SMA** termination | 1 | **RELEASE B / requires decision promotion** | Purchase order must say no-temperature version and SMA. |
| S-03 | 1 | Atlas Scientific EZO-pH circuit | 1 | **RELEASE B / requires decision promotion** | Default I2C `0x63`. |
| S-04 | 1 | Atlas Scientific electrically isolated EZO carrier, `ISCCB-2` | 1 | **RELEASE B / requires decision promotion** | Do not join isolated/non-isolated grounds. |
| S-05 | 1 | Atlas Scientific Conductivity K 10 Kit, `EC-KIT-10` | 1 | **RELEASE B / requires decision promotion** | Confirm kit contents include K10 probe, EZO-EC, isolated carrier, 12,880 and 150,000 µS/cm standards at order date. Default I2C `0x64`. |
| S-06 | 1 | Atlas Scientific SMA PT-1000 Temperature Kit `KIT-306`, configured with **Threaded PT-1000** | 1 | **RELEASE B / requires decision promotion** | Current kit includes PT-THRD, EZO-RTD, and non-isolated `SCCB`; default I2C `0x66`. Verify selected probe on order confirmation. |
| S-07 | 1 | DFRobot SEN0710 turbidity sensor | 1 | **HOLD — VERIFY BEFORE PURCHASE** | Written months-long 15–25 ppt confirmation required; change Modbus address to 2 before bus connection. |
| S-08 | 0 initially | DFRobot SEN0711 ammonia-nitrogen sensor | 1 | **HOLD — VERIFY BEFORE PURCHASE** | Saline matrix/selectivity/TAN meaning and external comparison required; reserve address 3. |
| S-09 | 1 | In-Situ RDO Blue, **10 m stripped/tinned cable, P/N 0038620** | 2 | **RELEASE B** | 8–36 V, RS485; this corrects the earlier 3 m description associated with the part number. |
| S-10 | 1 | DFRobot SEN0709 ORP sensor | 2 | **HOLD — VERIFY BEFORE PURCHASE** | Written long-term 15–25 ppt compatibility required. |
| S-11 | 1 | SulfiLogger S1-1020, exact low-range 0–0.5 mg/L order code | 3 | **HOLD — VERIFY BEFORE PURCHASE** | Exact range/order code, saline life, max/start current, cable, maintenance kit, RS232 behavior all required in writing. |
| S-12 | 1 | Sensirion `EK-SLF3S-4000B` evaluation kit | 4 | **HOLD — requires pump/flow decision promotion** | Includes clamp and pigtail needed for integration; saltwater gravimetric calibration required. |
| S-13 | 0 | Online Mg sensor | 4 | **DEFERRED** | No approved model. |
| S-14 | 0 | Online Ca sensor | 4 | **DEFERRED** | No approved model. |
| S-15 | 0 | Online NO2/NO3/alkalinity analyzer | External | **DEFERRED** | Use periodic validated external measurements; do not force a direct sensor. |
| S-16 | 1 optional | Hanna Instruments `HI97115C` Marine Master kit | External grab samples | **HOLD — SCREENING ONLY** | Validate each method at 15/20/25 ppt against laboratory results. Ca/Mg ranges do not cover the full expected brackish concentrations; ammonia basis and nitrite manual revision require confirmation. |

## 4. Calibration, maintenance, and reference-analysis supplies

| ID | Initial qty | Item/specification | Status | Notes |
|---|---:|---|---|---|
| K-01 | 1 box each | Atlas pH 4.00, 7.00, 10.00 single-use calibration pouches | **RELEASE B** | Record lot and expiry; never return used solution to stock. |
| K-02 | 1 each | Conductivity standards 12,880 and 150,000 µS/cm | **RELEASE B** | Included in EC-KIT-10 if current kit contents match; add one independent check standard near operating EC. |
| K-03 | 1 | RDO Blue calibration/maintenance accessories required by current manual | **RELEASE B after manual/SKU check** | Confirm cap lifetime and whether a spare sensing cap should be stocked. |
| K-04 | 1 | Optical-grade lint-free swabs/wipes and manufacturer-approved cleaning supplies | **RELEASE** | Keep separate by sensor; no abrasive cleaning. |
| K-05 | 1 | Certified thermometer/reference temperature logger, uncertainty ≤0.1 °C | **RELEASE or inventory** | For PT-1000 and internal-temperature comparisons. |
| K-06 | 1 | Independent salinity/conductivity reference meter covering at least 0–50 ppt | **RELEASE or inventory** | Used to set DO salinity compensation and verify EC. Record calibration. |
| K-07 | service | Accredited saline-water laboratory analysis for TAN, NO2-N, NO3-N, Ca, Mg; alkalinity by validated method | **RELEASE as service** | Minimum low/mid/high validation campaign, duplicates and matrix spikes where applicable. |
| K-08 | 1 set | Gravimetric flow calibration: balance ≥2 kg with ≤0.1 g readability, collection vessel, timer, temperature/density record | **RELEASE or inventory** | Ten-minute collections at 60/80/100 mL/min. |
| K-09 | as required | Turbidity standards covering tank range | **HOLD with SEN0710** | Use manufacturer-approved standards and shelf life. |
| K-10 | as required | SulfiLogger membrane/cleaning/calibration kit | **HOLD exact SKU** | Obtain exact interval and included parts from manufacturer. |
| K-11 | 1 lot | Reagent-grade anhydrous sodium sulfite, DI water, labeled calibration vessel, and chemical-waste container | **RELEASE A** | Prepare SEN0681 5% zero-oxygen solution exactly per manufacturer instructions; use PPE/SDS and never return it to the tank. Dispose through the approved chemical-waste route. |
| K-12 | 1 | SEN0681 replacement phosphor film/cap, exact current service SKU | **HOLD exact SKU before one-year service** | Manufacturer recommends annual replacement; obtain procedure/SKU from DFRobot. |
| K-13 | 1 optional | Hanna `HI97105-11` CAL Check set plus exact current HI97115 reagents, cuvettes, syringes/pipettes, DI water, and reagent-waste container | **HOLD with S-16** | Log method/firmware/manual/reagent lot/expiry and never return test waste to tank. |

## 5. 12 V sensor power and protection

| ID | Qty | Item/specification | Status | Notes |
|---|---:|---|---|---|
| P-01 | 1 | Mean Well `GST25A12-P1J`, 12 V, 2.08 A, 25 W | **PROVISIONAL / RELEASE A only after connector check** | Capacity passes known-load calculation; H2S maximum current remains unknown. P1J barrel dimensions must match adapter. |
| P-02 | 1 + 1 spare | 5.5 × 2.1 mm female barrel-to-screw-terminal adapter, rated ≥3 A/24 V | **RELEASE after P1J fit check** | Verify center-positive polarity and actual dimensions with meter/calipers. |
| P-03 | 1 | Six-circuit 32 VDC branch fuse block with negative bus, e.g. Blue Sea Systems 5025 | **RELEASE** | Install in dry enclosure; labels `DO1`, `MID_AUX`, `RDO`, `ORP`, `H2S`, `BYPASS`. Separate bottom fuses prevent an ORP fault from removing RDO. |
| P-04 | 10 + spares | ATC/ATO blade fuses: 1 A branch; 2 A main if a separate main holder is used | **RELEASE** | Final H2S branch fuse reviewed after maximum current is received. Never fit above wire/device rating. |
| P-05 | 1 optional | In-line main fuse holder rated ≥32 V/5 A | **RELEASE if P-03 lacks protected feed** | Place immediately after barrel adapter. |
| P-06 | 10 | WAGO 221-413 (3-conductor) lever connectors | **RELEASE** | Red +12 V distribution and black sensor-return distribution kept physically separate. |
| P-07 | 6 | WAGO 221-415 (5-conductor) lever connectors | **RELEASE** | Use only in dry enclosure; one electrical net per connector. |
| P-08 | 1 lot | 22 AWG stranded copper, red/black, 300 V or better | **RELEASE** | Sensor-power branches. Derate/size up if run length creates >3% drop. |
| P-09 | 1 set | Ferrules for 22–24 AWG plus ratcheting ferrule crimper | **RELEASE or inventory** | No solder-tinned stranded wire under screw clamps. |
| P-10 | 1 | Lockable dry polycarbonate/NEMA 4X power-distribution enclosure, sized after physical layout | **RELEASE after layout** | Electronics remain dry; strain relief and drip loops mandatory. |
| P-11 | as required | UL/IEC listed cable glands sized to each actual cable OD, plus blanking plugs | **RELEASE after cable measurement** | SKU is dimension-dependent; record gland range and cable OD. |
| P-12 | 1 | Code-compliant GFCI/RCD-protected receptacle or listed portable protection for the complete installation | **RELEASE or facility inventory** | Water-adjacent AC protection; installation by a qualified person where required. |

Manufacturer source: [Mean Well GST25A datasheet](https://www.meanwell.com/Upload/PDF/GST25A/GST25A-SPEC.PDF).

## 6. Node enclosures and permanent signal wiring

| ID | Qty | Item/specification | Status | Notes |
|---|---:|---|---|---|
| W-01 | 4 | Dry polycarbonate/NEMA 4X node enclosure with clear or opaque lid, DIN plate/standoffs | **RELEASE after physical fit** | Size from a full-scale paper layout; no submerged electronics. |
| W-02 | 4 | Removable pluggable terminal blocks, 3.5/5.08 mm pitch, rated ≥2 A/30 V | **RELEASE** | Label by conductor function and node. |
| W-03 | 1 roll | 24 AWG stranded twisted pair, yellow/blue, shielded where sensor cable does not supply a pair | **RELEASE** | RS485 A/B; shield terminated at one dry-panel chassis point only when used. |
| W-04 | 1 roll | 24 AWG stranded, multiple colors | **RELEASE** | TTL/I2C inside dry boxes; keep <20 cm where possible. |
| W-05 | 1 kit | Adhesive-lined heat-shrink, wire markers, self-laminating cable labels | **RELEASE** | Both SulfiLogger brown/blue cables must be labeled `POWER` vs `RS232`. |
| W-06 | as required | Cable glands sized to actual USB, sensor, and power cable ODs | **RELEASE after measurement** | USB cable may require split gland or panel bulkhead. |
| W-07 | 4 | DIN rail/standoff mounting hardware, noncorroding | **RELEASE** | No loose boards. Maintain access to ESP USB and BOOT/RESET. |
| W-08 | 1 kit | 120 Ω, 1%, 0.25 W termination resistors | **RELEASE** | Fit only at physical ends of a long RS485 bus after waveform/error testing; do not blindly terminate every short point-to-point link. |
| W-09 | 1 kit | 10 kΩ resistors and small terminal breakout/prototyping PCB | **RELEASE** | I2C pullups only if verified absent/insufficient; do not parallel unknown pullups blindly. |
| W-10 | 1 | Chassis/PE bonding bar for cable shields, if shielded cables are installed | **RELEASE after enclosure plan** | Must not bridge isolated sensor return to ESP USB ground. |

## 7. Bypass pump and plumbing

| ID | Qty | Item/specification | Status | Notes / gate |
|---|---:|---|---|---|---|
| B-01 | 1 | Atlas Scientific `EZO-PMP` embedded dosing pump | **HOLD — RECOMMENDED, requires promotion** | 0.5–105 mL/min. Node 4 commands `DC,80,*` over the DFR0565-isolated I2C bus; 20-day reset/restart behavior must pass. `Dstart,*` is only a ~105 mL/min fail-safe, not a saved 80 mL/min mode. |
| B-02 | 1 | Atlas `EZO-DC` data cable | **HOLD with pump** | Permanent pigtail: red/black/white/green connect isolated 3.3 V/GND/SCL/SDA; blue interrupt is insulated unused. Also permits isolated bench service. |
| B-03 | 1 installed + 1 spare | Atlas `PMP-RC` replacement cassette | **HOLD with pump** | Cassette life stated 1,500 h; stock a spare before 24/7 service. |
| B-04 | 1 | Atlas `PMP-PTK` premium tubing kit | **HOLD with pump** | Tygon A-60-F, 5 mm OD × 3 mm ID, 2 m plus two HDPE inline connectors; use for pump/cassette service, not as the 5–6 mm-ID flow-meter run. |
| B-05 | 1.2 m maximum installed + spare | PharMed BPT or equivalently documented salt-compatible tubing, **5–6 mm ID**, OD compatible with selected barbs/clamps | **HOLD exact supplier SKU/OD** | Sensirion requires 5–6 mm ID; 6 mm is preferred if the clamp/barbs pass. Saint-Gobain rates PharMed BPT excellent for 20% NaCl. Keep installed wet length within the volume budget. |
| B-06 | 4 + spares | Nonmetallic straight barb/transition fittings: 4.8–5 mm OD pump connector to selected 5–6 mm-ID tube | **HOLD dimensional fit test** | Atlas-supplied HDPE connector nipple is approximately 4.8 mm OD with 2.8 mm bore. No brass/copper wetted parts. |
| B-07 | 4 + spares | 316L or polymer clamps sized to final tubing OD | **HOLD dimension** | Use Sensirion clamp for sensor; clamp every pressurized barb. |
| B-08 | 1 | Accessible coarse intake guard/strainer, PP/PVDF/316L, ≥1 mm openings, low dead volume | **HOLD exact tank geometry** | Avoid fine 100-mesh filter as the baseline; fouling would bias low flow. |
| B-09 | 1 | Conditional Ark-Plas `FCX14-PP0`, U.S. Plastic item 96391, 1/4 × 1/4 in PP inline filter, 316 SS 100 mesh | **HOLD fouling/dimensional test** | Optional downstream service filter. Confirm wetted certificate/dead volume and 5–6 mm tube transitions; omit if it loads too rapidly. |
| B-10 | 1 | Manual sample tee and normally capped valve, PP/PVDF, 5–6 mm flow bore | **HOLD exact fittings** | Sample to waste; disinfect cap; position after flow chamber, before return. |
| B-11 | 1 | Clear low-dead-volume bubble/pulse inspection section, ≤10 mL, vertically mounted | **HOLD exact geometry** | Used only if pump pulsation/bubbles impair flow signal; does not expose DO/pH channels. |
| B-12 | 1 | Provisional removable blank chamber/manifold, ≤40 mL, capped ports | **HOLD — DO NOT BUY FINAL CHAMBER** | Port/thread/immersion depth wait for validated Ca/Mg models. |
| B-13 | 1 | Return bracket with visible air-gap/anti-siphon outlet | **RELEASE after tank fit** | Secure above normal water level; prevent hose escape and splashing into electronics. |
| B-14 | 1 | Dry drip tray/leak sensor under pump/chamber | **RECOMMENDED** | Leak alarm may be local until a safely isolated input is designed. |
| B-15 | 1 | Atlas-approved silicone lubricating grease (manufacturer cites Super Lube), exact food-contact/service SKU | **HOLD with pump service kit** | Required when rebuilding the cassette tube; archive SDS and apply only at the documented cassette points. |

Sources: [EZO-PMP datasheet](https://files.atlas-scientific.com/EZO_PMP_Datasheet.pdf), [premium tubing specifications](https://files.atlas-scientific.com/premium_tubing_specs2.pdf), [Saint-Gobain chemical compatibility](https://www.biopharm.saint-gobain.com/sites/hps-mac3-lifesciences-bioprocess/files/chemical-compatibility-chart-bps_0.pdf), [Sensirion flow-meter datasheet](https://sensirion.com/resource/datasheet/slf3s-4000b), [Ark-Plas filter candidate](https://www.usplastic.com/catalog/item.aspx?itemid=163925).

## 8. Raspberry Pi, network, and storage

| ID | Qty | Item/specification | Status | Notes |
|---|---:|---|---|---|
| R-01 | 1 | Existing Raspberry Pi, 64-bit OS capable, wired Ethernet preferred | **INVENTORY / RELEASE** | Record model, RAM, serial, OS, PSU, and thermal state. Pi is the always-on Phase-1 gateway. |
| R-02 | 1 | Official/approved Pi power supply sized for the owned model | **INVENTORY / RELEASE** | Check undervoltage history under SSD load. |
| R-03 | 1 | USB 3 SSD, ≥500 GB, SMART/health reporting supported | **RELEASE after Pi compatibility check** | PostgreSQL, Mosquitto persistence, exports, and logs live here; not on microSD. Record exact SKU/serial. |
| R-04 | 1 | Short USB 3 data cable/enclosure matching the SSD | **RELEASE** | Disable USB autosuspend for the device only if testing proves necessary. |
| R-05 | 1 | High-endurance microSD, ≥32 GB, for OS only, plus imaged spare | **RELEASE** | Database excluded. Keep a tested restore image. |
| R-06 | 1 | Managed or dedicated Wi-Fi access point/router with Ethernet to Pi | **RELEASE or inventory** | Stable 2.4 GHz SSID for ESP32; reserve DHCP leases; isolate from guest network. |
| R-07 | 1 | Cat6 patch cable | **RELEASE** | Pi-to-router wired path. |
| R-08 | 1 optional | UPS sized for Pi + router graceful shutdown | **RECOMMENDED after runtime test** | Not required to prove restart recovery, but reduces corruption/outage risk. Choose exact model only after measured watts. |
| R-09 | 1 | Separate backup destination, removable SSD or authenticated NAS | **RELEASE / inventory** | Nightly encrypted backup; never treat the live SSD as its own backup. |

## 9. Bench and commissioning equipment

| ID | Qty | Item/specification | Status | Purpose |
|---|---:|---|---|---|
| T-01 | 1 | True-RMS digital multimeter, CAT-rated for the environment | **RELEASE or inventory** | Polarity, voltage, continuity, current, isolation-boundary checks. |
| T-02 | 1 | USB-isolated RS485 adapter with selectable 3.3/5 V logic or native isolated USB-RS485 | **RELEASE** | Configure addresses one sensor at a time; not permanently installed. |
| T-03 | 1 | USB-isolated RS232 adapter | **HOLD with H2S** | Bench protocol verification. |
| T-04 | 1 | Logic analyzer/oscilloscope with differential/isolated measurement practice | **RECOMMENDED or inventory** | UART/I2C timing and RS485 waveform diagnosis; never clip grounded scope across an isolation boundary. |
| T-05 | 1 | Adjustable current-limited bench supply, 0–30 V | **RELEASE or inventory** | One-device bring-up before main rail. |
| T-06 | 1 | Label printer | **RELEASE or inventory** | Every node, conductor, fuse, sensor, and cable-end ID. |
| T-07 | 1 lot | Desiccant/humidity cards | **RELEASE** | Dry enclosures; inspect/replace on schedule. |

## 10. Explicit exclusions

- No Jetson purchase or ML accelerator work is included.
- No SEN0707 EC sensor: documented range is inadequate.
- No generic non-isolated MAX3232 or bare RS485 transceiver is allowed in permanent wet-sensor links.
- No final Mg/Ca chamber or probe adapter is purchased before exact probe geometry and saline validity are known.
- No copper, brass, plain steel, or unverified elastomer is allowed in the wetted bypass.
- No database is hosted on the Pi microSD.
- No loose Dupont jumpers remain in permanent installation.

## 11. Receiving inspection

For every serialized/active item, record manufacturer, full SKU, hardware revision, serial number, firmware, supplier, purchase date, datasheet revision/hash, included cable length/termination, measured idle/active current, and acceptance result. Quarantine any item whose marking or documentation differs from the released BOM.
