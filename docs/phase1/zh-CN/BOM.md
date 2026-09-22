# Phase 1 物料清单与采购说明（中文读者版）

**英文逐项基准：** [Phase-1 Bill of Materials](../BOM.md)  
**基础：** 4 个 ESP32 节点、1 个 100 L 缸、15–25 ppt、1 台 Raspberry Pi

> 采购规则：只有英文 BOM 中标为 `RELEASE` 的行，才可以在不补充技术证据的情况下下单。`HOLD` 行必须先关闭该行门槛。价格随时间和地区变化，本设计故意不写价格。

下单时必须同时打开英文 BOM 按 ID 对照。本中文页解释采购意图；英文页保留完整数量、规格和门槛。

## 1. 分批采购

| 批次 | 内容 | 为什么这样分 |
|---|---|---|
| Release A | SEN0681、一个 ESP32 节点、Waveshare TTL TO RS485 (B)、独立 USB 5 V、12 V 配电、Pi 数据栈和台架工具 | 先证明最小端到端链路。 |
| Release B | pH/EC/PT-1000 和 RDO Blue | 第一条链路通过验收后逐个加入。 |
| Release C | 浊度、ORP、H2S、氨氮、泵、流量计和最终流通池 | 只有各自厂家证据/决策门槛关闭后才买。 |

不要把三批合成一张订单来绕过门槛。`+1 spare` 是备件库存，不是同时工作的负载。

## 2. 核心计算与通信（C 系列）

| ID | 数量 | 准确物品 | 状态 | 中文说明 |
|---|---:|---|---|---|
| C-01 | 4 + 1 备 | Espressif `ESP32-S3-DevKitC-1-N8R8` | `RELEASE` | N8R8 = 8 MB Flash + 8 MB PSRAM；收货核对模块丝印。 |
| C-02 | 3 + 1 备 | Waveshare `TTL TO RS485 (B)`，Part No. 23778，导轨式电气隔离转换器 | `LOCKED — 用户批准替换DFR0845` | Node 1 一块、Node 2 两块；TTL侧用3.3 V。端口为VCC/GND/TXD/RXD与SGND/A+/B-；不提供12 V传感器电源。 |
| C-03 | 1 + 1 备 | Waveshare Industrial Isolated TTL to RS232 (B) | `HOLD with H2S` | 只有选定 S1-1020 才买，TTL 侧 3.3 V。 |
| C-04 | 1 + 1 备 | DFRobot `DFR0565` I2C 隔离器 | `HOLD with flow meter` | 控制侧 5 V，隔离侧输出 5 V/150 mA；后面仍要降到 3.3 V。 |
| C-05 | 4 + 1 备 | Pololu `D24V5F3`，item 2842，3.3 V/500 mA | `RELEASE` | Nodes 1–3 给外设供电；Node 4 把隔离 5 V 降为 3.3 V。没有反接保护，接插件必须防呆。 |
| C-06 | 2 + 1 备 | 仅供 DFR0565 使用的短 PH2.0-4P Gravity 线 | `HOLD with flow meter` | Waveshare RS485板使用螺丝端子，不需要Gravity线；DFR0565线仍须先做连续性映射。 |
| C-07 | 4 | 合规 5 V USB 电源，每只持续 ≥1 A | `RELEASE` | 每节点独立一只，从 DevKit USB 口供电。订购前记录确切获批 SKU。 |
| C-08 | 4 + 1 备 | 与到货 DevKitC-1 插座相配的数据/供电 USB 线 | `RELEASE after connector check` | 不根据商家照片猜 Micro-USB 或 USB-C。 |

## 3. 传感器与分析通道（S 系列）

| ID | 数量 | 物品 | 状态 | 下单前要点 |
|---|---:|---|---|---|
| S-01 | 1 | DFRobot `SEN0681` 海水光学溶氧 | `RELEASE A` | 第一条链路，RS485，5 m 电缆。 |
| S-02 | 1 | Atlas `ENV-50-pH-NT`，必须 **SMA** 端接 | `RELEASE B / requires promotion` | 订单写明无温度版本和 SMA。 |
| S-03 | 1 | Atlas EZO-pH | 同上 | 默认 I2C `0x63`。 |
| S-04 | 1 | Atlas `ISCCB-2` 隔离 EZO 载板 | 同上 | 不可连接隔离/非隔离地。 |
| S-05 | 1 | Atlas `EC-KIT-10` K10 电导套件 | `RELEASE B / requires promotion` | 核对 K10、EZO-EC、隔离载板、12,880/150,000 µS/cm 标准液；地址 `0x64`。 |
| S-06 | 1 | Atlas `KIT-306`，选择 **Threaded PT-1000** | `RELEASE B / requires promotion` | 核对 PT-THRD、EZO-RTD、非隔离 SCCB；地址 `0x66`。 |
| S-07 | 1 | DFRobot `SEN0710` 浊度 | `HOLD — VERIFY BEFORE PURCHASE` | 需长期 15–25 ppt 书面确认；上总线前单独改地址 2。 |
| S-08 | 初始 0 | DFRobot `SEN0711` 氨氮 | `HOLD — VERIFY BEFORE PURCHASE` | 需盐水基质、选择性、计量含义和外部比对；预留地址 3。 |
| S-09 | 1 | In-Situ RDO Blue，**10 m 裸线镀锡，P/N 0038620** | `RELEASE B` | 不要误买成 3 m。 |
| S-10 | 1 | DFRobot `SEN0709` ORP | `HOLD — VERIFY BEFORE PURCHASE` | 需长期 15–25 ppt 书面确认。 |
| S-11 | 1 | SulfiLogger `S1-1020`，0–0.5 mg/L 低量程准确订货码 | `HOLD — VERIFY BEFORE PURCHASE` | 核实盐水寿命、最大/启动电流、电缆、维护套件和 RS232。 |
| S-12 | 1 | Sensirion `EK-SLF3S-4000B` | `HOLD — requires promotion` | 套件含夹具和尾线；必须做盐水重量法标定。 |
| S-13/S-14 | 0 | 在线 Mg/Ca 传感器 | `DEFERRED` | 无获批型号，不买。 |
| S-15 | 0 | 在线 NO2/NO3/碱度分析仪 | `DEFERRED` | 使用定期外部验证测量。 |
| S-16 | 可选 1 | Hanna `HI97115C` | `HOLD — SCREENING ONLY` | 只作筛查；每种方法在 15/20/25 ppt 与实验室结果比对。 |

## 4. 校准、维护和参考分析（K 系列）

| ID | 主要物品 | 状态 | 解释 |
|---|---|---|---|
| K-01 | pH 4.00/7.00/10.00 单次校准液 | `RELEASE B` | 记录批号/有效期，用过不倒回原包装。 |
| K-02 | 12,880 和 150,000 µS/cm 电导标准液 | `RELEASE B` | EC 套件内容要复核；另加接近运行电导的独立检查标准。 |
| K-03 | RDO Blue 当前手册要求的校准/维护附件 | `RELEASE B after check` | 核实感应帽寿命和备件。 |
| K-04 | 光学级无绒拭子和厂家允许的清洁用品 | `RELEASE` | 每只传感器分开，不能磨擦清洗。 |
| K-05 | 不确定度 ≤0.1 °C 的认证温度计/记录器 | `RELEASE or inventory` | 检查 PT-1000 和传感器内部温度。 |
| K-06 | 覆盖至少 0–50 ppt 的独立盐度/电导参考仪 | `RELEASE or inventory` | 设置 DO 盐度补偿并复核 EC。 |
| K-07 | TAN、NO2-N、NO3-N、Ca、Mg 的合格盐水实验室服务及验证碱度法 | `RELEASE as service` | 至少低/中/高验证，适用时做重复和基质加标。 |
| K-08 | ≥2 kg、分辨率 ≤0.1 g 的秤、收集容器、计时、温度/密度记录 | `RELEASE or inventory` | 流量 60/80/100 mL/min，每点收集 10 min。 |
| K-09 | 浊度标准 | `HOLD with SEN0710` | 只能用厂家允许并在有效期内的标准。 |
| K-10 | SulfiLogger 膜/清洗/校准套件 | `HOLD exact SKU` | 从厂家拿准确周期和内容。 |
| K-11 | 无水亚硫酸钠、DI 水、标记容器和废液容器 | `RELEASE A` | 按厂家做 SEN0681 5% 无氧液；PPE/SDS；绝不回缸。 |
| K-12 | SEN0681 磷光膜/帽当前维护 SKU | `HOLD exact SKU` | 一年维护前确认程序和料号。 |
| K-13 | Hanna 校验套装/试剂/比色皿/移液工具/废液容器 | `HOLD with S-16` | 记录方法、固件、手册、批号和有效期。 |

## 5. 12 V 电源和保护（P 系列）

| ID | 物品 | 状态 | 解释 |
|---|---|---|---|
| P-01 | Mean Well `GST25A12-P1J`，12 V、2.08 A、25 W | `PROVISIONAL`；Release A 前查插头 | 已知负载通过，但 H2S 最大电流未知。 |
| P-02 | 5.5 × 2.1 mm 母头转螺丝端子，≥3 A/24 V | 检查 P1J 后 `RELEASE` | 用万用表/卡尺核实中心正极和尺寸。 |
| P-03 | 六路 32 VDC 保险丝盒带负极母排，如 Blue Sea 5025 | `RELEASE` | 六路标记 `DO1/MID_AUX/RDO/ORP/H2S/BYPASS`。 |
| P-04 | ATC/ATO：分支 1 A；需要独立主座时主保险 2 A | `RELEASE` | 不能超过线材/设备额定值。 |
| P-05 | ≥32 V/5 A 在线主保险座，可选 | 视 P-03 `RELEASE` | 紧靠桶形插头适配器后安装。 |
| P-06/P-07 | WAGO 221-413 与 221-415 | `RELEASE` | 只在干燥盒内；一只连接器只能属于一个电气网络。 |
| P-08 | 22 AWG 多股铜线，红/黑，≥300 V | `RELEASE` | 12 V 分支；最坏工况压降 >3% 时加粗或缩短。 |
| P-09 | 22–24 AWG 冷压端头和棘轮压线钳 | `RELEASE or inventory` | 螺丝端子下不用焊锡镀硬的多股线。 |
| P-10/P-11 | 干燥 NEMA 4X 配电箱、按实测线径选的合规格兰头/堵头 | 尺寸核对后 `RELEASE` | 必须应力释放和滴水弯。 |
| P-12 | 合规 GFCI/RCD 保护插座或便携保护 | `RELEASE or facility inventory` | 靠水市电保护由合格人员完成。 |

## 6. 节点盒和信号接线（W 系列）

| ID | 内容 | 关键点 |
|---|---|---|
| W-01/W-02 | 4 个干燥 NEMA 4X 节点盒、可插拔端子 | 用 1:1 纸样确认尺寸；电子件不下水。 |
| W-03 | 24 AWG 黄/蓝双绞线，必要时屏蔽 | RS485 A/B；屏蔽只在一个合法干燥点处理。 |
| W-04 | 24 AWG 多色线 | 盒内 TTL/I2C，尽量 <20 cm。 |
| W-05 | 带胶热缩、线号、覆膜标签 | SulfiLogger 两组棕/蓝线必须区分 `POWER`/`RS232`。 |
| W-06/W-07 | 按实际外径选格兰头；DIN/支架 | 板卡固定，USB 和 BOOT/RESET 可接近。 |
| W-08 | 120 Ω、1%、0.25 W 电阻 | 只在长 RS485 总线物理末端且经测试需要时使用。 |
| W-09 | 10 kΩ 电阻和小端子板 | 只有证明 I2C 上拉缺失/不足才加。 |
| W-10 | 机壳/PE 屏蔽汇流排 | 不能跨接隔离传感器回路和 USB 地。 |

## 7. 旁路（B 系列）

| ID | 物品 | 状态/要点 |
|---|---|---|
| B-01 | Atlas `EZO-PMP` | `HOLD`；推荐但需决策提升。Node 4 用 `DC,80,*`；必须测试 20 天复位。 |
| B-02/B-03 | `EZO-DC` 线、安装 1 + 备用 1 个 `PMP-RC` 泵盒 | 与泵一起 HOLD；蓝色中断线绝缘不用。 |
| B-04 | `PMP-PTK`，5 mm OD × 3 mm ID | 只用于泵头/维修，不是 5–6 mm ID 主流量管。 |
| B-05 | 安装最长 1.2 m + 备件，PharMed BPT 或等效 5–6 mm ID 盐水兼容管 | `HOLD exact SKU/OD`；控制湿体积。 |
| B-06/B-07 | 非金属转换接头与合适夹具 | 实体配合后放行；接液处禁用黄铜/铜。 |
| B-08/B-09 | ≥1 mm 粗进水防护；可选 100 目服务过滤器 | 细滤网可能堵塞并造成假低流量，先做污染试验。 |
| B-10/B-11 | 带帽取样三通；≤10 mL 透明检查段 | 只在准确几何确认后买。 |
| B-12 | ≤40 mL 可拆空白腔/歧管 | `DO NOT BUY FINAL CHAMBER`；等 Mg/Ca 准确探头几何。 |
| B-13/B-14/B-15 | 防虹吸回水架、干式接液盘/漏水报警、厂家允许润滑脂 | 分别按缸体、隔离输入和维修 SKU 核实。 |

## 8. 树莓派、网络和存储（R 系列）

- R-01/R-02：盘点现有 Pi 和适配电源；记录型号、RAM、序列号、OS、电源与温度状态。
- R-03：≥500 GB、支持健康监测的 USB 3 SSD；数据库、MQTT 持久化、日志和导出都在 SSD，不在 microSD。
- R-05：≥32 GB 高耐久 microSD 只放系统，并保留测试过的镜像备件。
- R-06/R-07：稳定 2.4 GHz AP/路由器和 Pi 有线 Cat6；固定 DHCP 租约，隔离访客网络。
- R-08：UPS 可选，先量实际功率再选型。
- R-09：单独备份目的地；实时 SSD 不能充当自己的备份。

## 9. 台架与调试工具（T 系列）

至少需要：CAT 等级合适的真有效值万用表、隔离 USB-RS485 适配器、可限流 0–30 V 台式电源、标签机和干燥剂/湿度卡。H2S 才需要隔离 USB-RS232。示波器/逻辑分析仪可选，但不能把接地示波器夹子跨接隔离边界。

## 10. 明确排除

- 不采购 Jetson 或 ML 加速器用于 Phase 1。
- 不采用量程不足的 `SEN0707`。
- 永久湿传感器链路不用通用非隔离 MAX3232 或裸 RS485 板。
- 未确定 Mg/Ca 探头前不买最终流通池或钻孔适配器。
- 接液旁路不用铜、黄铜、普通钢或未验证弹性体。
- 数据库不放 Pi microSD。
- 永久安装不留松散杜邦线。

## 11. 收货检验

每个带序列号或有源设备都记录：厂家、完整 SKU、硬件版、序列号、固件、供应商、购买日期、资料版本/哈希、线长和端接、空闲/工作电流、验收结论。标记或资料与放行 BOM 不同的物品先隔离，不得直接替换。
