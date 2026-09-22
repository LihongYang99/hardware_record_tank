# Phase-1 Technical Source Register

**Research cut-off:** 2026-09-02  
**Evidence policy:** manufacturer documentation is primary for product facts. Government/standards sources support scientific meaning. Distributor pages are used only for an exact purchasable fitting/commodity and never override a manufacturer specification.

Before purchase, download the cited PDF/web export, record retrieval UTC and SHA-256, and attach it to the asset/procurement record. Web pages evolve; a later page does not silently change the as-built design.

## Sensors and interfaces

| Item | Primary source | Claims used | Evidence outcome |
|---|---|---|---|
| DFRobot SEN0681 | [product wiki](https://wiki.dfrobot.com/sen0681), [protocol](https://wiki.dfrobot.com/sen0681/docs/21674) | Seawater duty, 10–30 V/0.2 W, range/accuracy/response, wire colors, 4800 8N1, registers, salinity/pressure compensation | Supports Release A. |
| Waveshare TTL TO RS485 (B), Part No. 23778 | [manufacturer page](https://www.waveshare.com/ttl-to-rs485-b.htm) | 3.3–5 V TTL power, galvanic isolation, VCC/GND/TXD/RXD and SGND/A+/B- pinout, switchable 120R | LOCKED user-approved replacement for unavailable DFR0845; converter does not supply sensor 12 V. |
| DFRobot SEN0707 | [manufacturer wiki](https://wiki.dfrobot.com/sen0707/) | EC/salinity upper range | Supports rejection for 15–25 ppt duty. |
| DFRobot SEN0709 | [product](https://www.dfrobot.com/product-3102.html), [protocol](https://wiki.dfrobot.com/sen0709/docs/23382) | 10–30 V/0.4 W, ORP range/accuracy, RS485 settings/registers | Electrical/protocol pass; saline-life evidence absent. |
| DFRobot SEN0710 | [product](https://www.dfrobot.com/product-3104.html), [setup](https://wiki.dfrobot.com/sen0710/docs/23383), [protocol](https://wiki.dfrobot.com/sen0710/docs/23385) | Turbidity range, response, power, placement/cleaning, RS485 settings | Electrical/protocol pass; saline-life evidence absent. |
| DFRobot SEN0711 | [product/wiki](https://wiki.dfrobot.com/sen0711/), [protocol](https://wiki.dfrobot.com/sen0711/docs/23361) | “Ammonia nitrogen” range, pH/temp channels, power, RS485 registers/calibration | Insufficient matrix/measurand evidence; hold. |
| Atlas industrial pH | [probe datasheet](https://files.atlas-scientific.com/IpH_probe.pdf), [EZO-pH](https://atlas-scientific.com/embedded-solutions/ezo-ph-circuit/), [ISCCB-2](https://files.atlas-scientific.com/electrically-isolated-ezo-carrier-board.pdf) | Saltwater immersion, probe performance, circuit address/compensation, isolated carrier voltage/current/pins | Supports pH recommendation. |
| Atlas K10 EC | [EC-KIT-10](https://atlas-scientific.com/kits/conductivity-k-10-kit/), [probe](https://atlas-scientific.com/probes/conductivity-probe-k-10/), [probe datasheet](https://files.atlas-scientific.com/l-EC_K_10_probe.pdf), [EZO-EC](https://atlas-scientific.com/embedded-solutions/ezo-conductivity-circuit/) | Kit contents, saltwater use, 10 µS/cm–1 S/cm probe, isolation, salinity and temperature compensation | Supports EC recommendation. |
| Atlas PT-1000 | [KIT-306](https://atlas-scientific.com/kits/sma-temperature-kit/?attribute_temperature-probe=Threaded+PT-1000), [PT-THRD](https://files.atlas-scientific.com/PT-THRD-probe.pdf), [EZO-RTD](https://files.atlas-scientific.com/EZO_RTD_Datasheet.pdf), [SCCB](https://atlas-scientific.com/carrier-boards/ezo-carrier-board/) | Exact kit contents, saline immersion, RTD circuit/address, non-isolated carrier | Supports compensation-temperature recommendation. |
| In-Situ RDO Blue | [product](https://in-situ.com/us/rdo-blue/), [manual](https://in-situ.com/pub/media/support/documents/RDO-Blue-Manual.pdf), [interface specification](https://in-situ.com/pub/media/support/documents/rdoBlueInterfaceSpec-2020-08-10.pdf) | Fresh/salt long-term use, DO/temp performance, 8–36 V/current, wire colors, 19200 8E1 Modbus, cable P/N | Supports RDO recommendation and 10 m P/N 0038620 correction. |
| SulfiLogger S1-1020 | [product](https://sulfilogger.com/product/sulfilogger-1020/), [installation manual](https://sulfilogger.com/wp-content/uploads/2024/02/C00620V02-SulfiLogger-sensor-Installation-manual_200.pdf), [RS232 protocol](https://sulfilogger.com/wp-content/uploads/2023/06/SulfiLogger_RS232-protocol_104.pdf) | Dissolved H2S range options, performance, power range, RS232 wires/38400 8N1 ASCII commands | Protocol supported; saline life/max current/order-code evidence absent. |
| Waveshare isolated RS232 | [manufacturer product page](https://www.waveshare.com/product/ttl-to-rs232-b.htm) | Isolated TTL and RS232 sides, 3.3–5 V TTL pinout | Supports conditional Node 3 converter. |
| Sensirion SLF3S-4000B | [catalog](https://sensirion.com/products/catalog/SLF3S-4000B), [datasheet](https://sensirion.com/resource/datasheet/slf3s-4000b) | Range/accuracy, 3.2–3.8 V/current, I2C/address/CRC, pinout, wetted materials, volume, tubing, water/IPA calibration | Supports calibrated relative/flow-presence recommendation. |
| DFRobot DFR0565 | [manufacturer wiki](https://wiki.dfrobot.com/dfr0565) | 5 V controller input, 3.3 V I2C high, isolated 5 V/150 mA output, pinout | Supports Node 4 isolation; requires downstream 3.3 V regulator. |
| Pololu D24V5F3 | [manufacturer specification](https://www.pololu.com/product/2842/specs) | 3.3 V/500 mA, 3.4–36 V input, protection/limitations | Supports peripheral and isolated-side regulation. |
| Hanna HI97115C Marine Master | [manufacturer product/method table](https://hannainst.com/marine-master-waterproof-wireless-multiparameter-photometer-HI97115.html), [current guide](https://www.documentation.hannainst.com/manuals/download/6977), [CAL Check set](https://hannainst.com/CAL-Check-Standards-for-HI97105-Cuvette-Kit-HI97105-11.html) | External marine pH/alkalinity/ammonia/Ca/Mg/nitrate/nitrite/phosphate methods and ranges | Screening candidate only; Ca/Mg range and 15–25 ppt matrix do not support primary-reference status. Nitrite revision conflict must be resolved per instrument. |

## Power, pump, and plumbing

| Item | Primary source | Claims used | Evidence outcome |
|---|---|---|---|
| Mean Well GST25A12-P1J | [manufacturer datasheet](https://www.meanwell.com/Upload/PDF/GST25A/GST25A-SPEC.PDF) | 12 V, 2.08 A, 25 W, AC range and connector family | Provisional full-build supply; H2S current gate remains. |
| Atlas EZO-PMP | [manufacturer datasheet](https://files.atlas-scientific.com/EZO_PMP_Datasheet.pdf) | 0.5–105 mL/min, 12/24 V motor, 3.3–5.5 V control, current, pin colors, I2C/UART, `DC`, `Dstart`, 20-day reset, tubing/cassette/motor life | Supports supervised 80 mL/min recommendation. |
| Atlas PMP-PTK | [manufacturer product](https://atlas-scientific.com/peristaltic/premium-tubing-kit/), [specification](https://files.atlas-scientific.com/premium_tubing_specs2.pdf) | Tygon A-60-F 5 mm OD ×3 mm ID, connector dimensions/material | Supports pump-service tubing, not large-bore flow run. |
| Saint-Gobain PharMed BPT | [manufacturer chemical-compatibility guide](https://www.biopharm.saint-gobain.com/sites/hps-mac3-lifesciences-bioprocess/files/chemical-compatibility-chart-bps_0.pdf) | Compatibility with 20% NaCl | Supports salt-compatible tubing material; exact metric SKU/OD remains a fit gate. |
| Ark-Plas service filter candidate | [distributor exact item](https://www.usplastic.com/catalog/item.aspx?itemid=163925) | FCX14-PP0, 1/4 ×1/4 in, PP/316 SS, 100 mesh | Conditional fitting only; fouling, dead volume, and transitions must pass. |

## Compute, time, storage, and software

| Item | Official source | Claims used |
|---|---|---|
| ESP32-S3-DevKitC-1 | [Espressif user guide](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html) | N8R8 memory, USB/UART/pin exposure, board power. |
| ESP-IDF time | [Espressif system time/SNTP](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/system/system_time.html) | SNTP configuration, smooth/step behavior, 64-bit time. |
| ESP flash | [wear levelling](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/storage/wear-levelling.html), [FATFS](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/fatfs.html), [NVS FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/storage/nvs.html) | Durable ring implementation constraints and write-wear controls. |
| chrony | [official chrony.conf documentation](https://chrony-project.org/doc/4.7/chrony.conf.html) | Controlled client/server configuration and subnet `allow`. |
| Mosquitto | [authentication](https://www.mosquitto.org/documentation/authentication-methods/), [configuration](https://www.mosquitto.org/man/mosquitto-conf-5.html) | Explicit auth/ACL and broker persistence. |
| PostgreSQL | [constraints](https://www.postgresql.org/docs/current/ddl-constraints.html), [WAL/backup](https://www.postgresql.org/docs/current/continuous-archiving.html) | Identity constraints, transactions, durability, backup/restore. |
| Grafana | [PostgreSQL data source](https://grafana.com/docs/grafana/latest/datasources/postgres/configure/), [provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/) | Direct read-only PostgreSQL integration and versioned dashboards. |
| Docker Compose | [startup order/health](https://docs.docker.com/compose/how-tos/startup-order/) | Health-conditioned startup; correctness still independent of order. |

## Scientific interpretation

| Topic | Authoritative source | Use |
|---|---|---|
| Ammonia/TAN and saltwater | [US EPA ammonia overview](https://www.epa.gov/caddis/ammonia), [EPA saltwater criteria document](https://www.epa.gov/sites/default/files/2015-08/documents/ambient_water_quality_criteria_for_ammonia_saltwater_-_1989_0.pdf) | Supports distinction among TAN, NH4/NH3, and the dependence of toxic fraction on pH, temperature, and ionic strength/salinity. |

## Source conflicts and corrections

1. Project text previously associated In-Situ P/N 0038620 with a 3 m stripped/tinned cable. Current manufacturer material identifies it as **10 m**; the BOM uses 10 m and flags the correction.
2. EZO-PMP `Dstart,*` is sometimes easy to interpret as a saved arbitrary constant-flow setting. The manufacturer manual shows it starts near **105 mL/min**; an 80 mL/min indefinite setpoint requires `DC,80,*` and Node 4 supervision.
3. DFR0565 provides an isolated **5 V** output while the SLF3S accepts only **3.2–3.8 V**. The design includes a downstream 3.3 V regulator and a preconnection voltage test.
4. DFRobot SEN0707 salinity/EC range does not reach the project’s 15–25 ppt band with margin; it is rejected even though it is marketed as an industrial EC/salinity device.
5. Current Hanna HI97115 materials list different nitrite ULR upper limits (200 ppb on the product method table and 800 ppb in a newer quick reference). Record the exact instrument firmware/manual/reagent method and obtain Hanna clarification before relying on the extended range.

## Archival checklist

- [ ] PDF/web export stored with retrieval UTC, original URL, filename, revision/date, and SHA-256.
- [ ] Order confirmation shows exact option, cable length, termination, and accessories.
- [ ] Written vendor answers stored as immutable attachments and referenced from the asset record.
- [ ] Datasheet revision used for wiring/firmware is recorded in configuration metadata.
- [ ] A changed online page triggers review; it does not automatically change an installed system.
- [ ] Distributor substitutions are re-audited against manufacturer evidence before purchase.
