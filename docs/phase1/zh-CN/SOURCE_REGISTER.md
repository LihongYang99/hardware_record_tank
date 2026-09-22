# Phase 1 技术资料来源登记表（中文读者版）

**英文完整登记表：** [Phase-1 Technical Source Register](../SOURCE_REGISTER.md)  
**研究截止：** 2026-09-02

产品电气参数、针脚、协议、材料和量程以厂家资料为首要证据；科学含义使用政府/标准资料；经销商页面只用于准确可购买的接头/普通物料，不能推翻厂家规格。

购买前要保存所引用 PDF 或网页导出，记录下载 UTC 和 SHA-256，并附到资产/采购记录。网页以后发生变化，不会自动改变已建系统。

## 1. 传感器与接口主要证据

| 物品 | 主要资料 | 本项目用来证明什么 | 结论 |
|---|---|---|---|
| DFRobot SEN0681 | [产品](https://wiki.dfrobot.com/sen0681)、[协议](https://wiki.dfrobot.com/sen0681/docs/21674) | 海水用途、供电、量程、线色、4800 8N1、寄存器、盐度/压力补偿 | 支持 Release A |
| Waveshare TTL TO RS485 (B)，Part No. 23778 | [厂家资料](https://www.waveshare.com/ttl-to-rs485-b.htm) | 3.3–5 V TTL供电、电气隔离、VCC/GND/TXD/RXD与SGND/A+/B-端口、120R开关 | 用户批准替代缺货DFR0845；不提供12 V传感器电源 |
| DFRobot SEN0707 | [厂家资料](https://wiki.dfrobot.com/sen0707/) | EC/盐度上限 | 支持对 15–25 ppt 用途的拒绝 |
| DFRobot SEN0709 | [产品](https://www.dfrobot.com/product-3102.html)、[协议](https://wiki.dfrobot.com/sen0709/docs/23382) | 供电、ORP 量程、RS485 | 电气/协议通过；盐水寿命缺证据 |
| DFRobot SEN0710 | [产品](https://www.dfrobot.com/product-3104.html)、[安装](https://wiki.dfrobot.com/sen0710/docs/23383)、[协议](https://wiki.dfrobot.com/sen0710/docs/23385) | 浊度、响应、供电、安装/清洁、RS485 | 电气/协议通过；盐水寿命缺证据 |
| DFRobot SEN0711 | [产品](https://wiki.dfrobot.com/sen0711/)、[协议](https://wiki.dfrobot.com/sen0711/docs/23361) | “氨氮”通道、pH/温度、供电、寄存器 | 基质/计量含义不足，HOLD |
| Atlas pH | [探头](https://files.atlas-scientific.com/IpH_probe.pdf)、[EZO-pH](https://atlas-scientific.com/embedded-solutions/ezo-ph-circuit/)、[ISCCB-2](https://files.atlas-scientific.com/electrically-isolated-ezo-carrier-board.pdf) | 盐水浸没、性能、地址/补偿、隔离载板 | 支持 pH 推荐 |
| Atlas K10 EC | [套件](https://atlas-scientific.com/kits/conductivity-k-10-kit/)、[探头](https://atlas-scientific.com/probes/conductivity-probe-k-10/)、[资料](https://files.atlas-scientific.com/l-EC_K_10_probe.pdf)、[EZO-EC](https://atlas-scientific.com/embedded-solutions/ezo-conductivity-circuit/) | 套件内容、盐水、量程、隔离、盐度/温补 | 支持 EC 推荐 |
| Atlas PT-1000 | [KIT-306](https://atlas-scientific.com/kits/sma-temperature-kit/?attribute_temperature-probe=Threaded+PT-1000)、[PT-THRD](https://files.atlas-scientific.com/PT-THRD-probe.pdf)、[EZO-RTD](https://files.atlas-scientific.com/EZO_RTD_Datasheet.pdf)、[SCCB](https://atlas-scientific.com/carrier-boards/ezo-carrier-board/) | 准确套件、盐水浸没、地址和载板 | 支持补偿温度推荐 |
| In-Situ RDO Blue | [产品](https://in-situ.com/us/rdo-blue/)、[手册](https://in-situ.com/pub/media/support/documents/RDO-Blue-Manual.pdf)、[接口](https://in-situ.com/pub/media/support/documents/rdoBlueInterfaceSpec-2020-08-10.pdf) | 长期淡/盐水、DO/温度、供电/电流、线色、19200 8E1、料号 | 支持推荐和 10 m P/N 0038620 修正 |
| SulfiLogger S1-1020 | [产品](https://sulfilogger.com/product/sulfilogger-1020/)、[安装](https://sulfilogger.com/wp-content/uploads/2024/02/C00620V02-SulfiLogger-sensor-Installation-manual_200.pdf)、[RS232](https://sulfilogger.com/wp-content/uploads/2023/06/SulfiLogger_RS232-protocol_104.pdf) | H2S 量程、性能、电压、线色、38400 8N1 命令 | 协议通过；盐水/最大电流/订货码缺证据 |
| Waveshare 隔离 RS232 | [厂家页](https://www.waveshare.com/product/ttl-to-rs232-b.htm) | 隔离 TTL/RS232 两侧和针脚 | 支持条件性 Node 3 |
| Sensirion SLF3S | [目录](https://sensirion.com/products/catalog/SLF3S-4000B)、[资料](https://sensirion.com/resource/datasheet/slf3s-4000b) | 量程、电压/电流、I2C/CRC、针脚、材料、体积、管径、标定液 | 支持校准后的相对/流量存在用途 |
| DFRobot DFR0565 | [厂家资料](https://wiki.dfrobot.com/dfr0565) | 5 V 输入、3.3 V I2C 高电平、隔离 5 V/150 mA 输出 | 支持隔离；后级必须降 3.3 V |
| Pololu D24V5F3 | [规格](https://www.pololu.com/product/2842/specs) | 3.3 V/500 mA、输入范围、保护限制 | 支持稳压设计 |
| Hanna HI97115C | [方法表](https://hannainst.com/marine-master-waterproof-wireless-multiparameter-photometer-HI97115.html)、[指南](https://www.documentation.hannainst.com/manuals/download/6977)、[校验套装](https://hannainst.com/CAL-Check-Standards-for-HI97105-Cuvette-Kit-HI97105-11.html) | 海水外部比色项目和量程 | 只作筛查；Ca/Mg 和方法版本有门槛 |

## 2. 供电、泵与水路证据

| 物品 | 资料 | 用途/结论 |
|---|---|---|
| Mean Well GST25A12-P1J | [厂家资料](https://www.meanwell.com/Upload/PDF/GST25A/GST25A-SPEC.PDF) | 12 V、2.08 A、25 W；完整配置仍等 H2S 电流。 |
| Atlas EZO-PMP | [厂家资料](https://files.atlas-scientific.com/EZO_PMP_Datasheet.pdf) | 流量、电机/控制电压、`DC`、`Dstart`、20 天复位和寿命；支持受监督 80 mL/min。 |
| Atlas PMP-PTK | [产品](https://atlas-scientific.com/peristaltic/premium-tubing-kit/)、[规格](https://files.atlas-scientific.com/premium_tubing_specs2.pdf) | 5 mm OD × 3 mm ID 和接头；只用于泵维修段。 |
| PharMed BPT | [厂家兼容表](https://www.biopharm.saint-gobain.com/sites/hps-mac3-lifesciences-bioprocess/files/chemical-compatibility-chart-bps_0.pdf) | 对 20% NaCl 兼容；准确公制 SKU/OD 仍需试配。 |
| Ark-Plas 过滤器候选 | [准确经销商物品](https://www.usplastic.com/catalog/item.aspx?itemid=163925) | 条件性服务过滤器；污染、死体积和转接仍需试验。 |

## 3. 计算、时间、存储和软件证据

| 主题 | 官方资料 | 用途 |
|---|---|---|
| ESP32-S3-DevKitC-1 | [Espressif 用户指南](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html) | N8R8、USB/UART/针脚和供电。 |
| ESP 时间 | [SNTP/系统时间](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/system/system_time.html) | 同步、平滑/跳变和 64 位时间。 |
| ESP Flash | [磨损均衡](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/storage/wear-levelling.html)、[FATFS](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/fatfs.html)、[NVS FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/storage/nvs.html) | 持久环和写磨损约束。 |
| chrony | [官方配置](https://chrony-project.org/doc/4.7/chrony.conf.html) | NTP 客户端/受控子网服务。 |
| Mosquitto | [认证](https://www.mosquitto.org/documentation/authentication-methods/)、[配置](https://www.mosquitto.org/man/mosquitto-conf-5.html) | 认证、ACL 和持久化。 |
| PostgreSQL | [约束](https://www.postgresql.org/docs/current/ddl-constraints.html)、[WAL/备份](https://www.postgresql.org/docs/current/continuous-archiving.html) | 身份约束、事务、持久性和恢复。 |
| Grafana | [PostgreSQL 数据源](https://grafana.com/docs/grafana/latest/datasources/postgres/configure/)、[配置化](https://grafana.com/docs/grafana/latest/administration/provisioning/) | 只读 PostgreSQL 和版本化仪表盘。 |
| Docker Compose | [启动/健康](https://docs.docker.com/compose/how-tos/startup-order/) | 按健康启动；正确性仍不依赖启动顺序。 |
| 氨/TAN 科学含义 | [US EPA 概述](https://www.epa.gov/caddis/ammonia)、[盐水标准文档](https://www.epa.gov/sites/default/files/2015-08/documents/ambient_water_quality_criteria_for_ammonia_saltwater_-_1989_0.pdf) | 区分 TAN、NH4/NH3，并说明有毒比例依赖 pH、温度和盐度/离子强度。 |

## 4. 已识别的资料冲突和修正

1. 项目旧文字把 In-Situ P/N 0038620 与 3 m 线缆关联；当前厂家资料显示为 **10 m**，BOM 已按 10 m 并明确修正。
2. `Dstart,*` 容易被误读为可保存任意恒流；厂家手册显示约 **105 mL/min**。80 mL/min 需 `DC,80,*` 和 Node 4 监督。
3. DFR0565 隔离侧输出 **5 V**，SLF3S 只允许 **3.2–3.8 V**；设计已加入后级 3.3 V 稳压和接入前实测。
4. SEN0707 量程无法有余量地达到项目 15–25 ppt，因此即使被称为工业 EC/盐度设备也被拒绝。
5. Hanna 当前资料对亚硝酸盐 ULR 上限有 200 ppb 与 800 ppb 差异；依赖扩大量程前要记录实物固件/手册/试剂并向 Hanna 澄清。

## 5. 资料归档清单

- [ ] 保存 PDF/网页导出、原 URL、下载 UTC、文件名、版本/日期和 SHA-256。
- [ ] 订单确认写清准确选件、线长、端接和附件。
- [ ] 厂家书面回复作为不可变附件，并从资产记录引用。
- [ ] 接线/固件所用资料版本写进配置元数据。
- [ ] 网页变化触发复核，不自动改变已装系统。
- [ ] 经销商替代品下单前重新对照厂家证据审计。
