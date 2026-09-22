# Phase 1 兼容性审计与开工门槛（中文读者版）

**英文工程基准：** [Phase-1 Compatibility Audit and Build Gates](../COMPATIBILITY_AUDIT.md)  
**结论：** 第一条 `SEN0681` 链路在设计上已可执行；若干扩展通道仍被正确 HOLD，但都不阻止第一条链路和 Pi 数据系统。

## 1. 对锁定要求的符合性

| 锁定要求 | 设计证据 | 结果 |
|---|---|---|
| Sensor → converter → ESP32 → UTC → Wi-Fi → MQTT → Pi → DB → dashboard | SEN0681 → Waveshare TTL TO RS485 (B) → Node 1 → Mosquitto → Python → PostgreSQL → Grafana | `PASS`，待实物测试 |
| 多个独立 ESP32-S3-DevKitC-1-N8R8 节点 | 四节点 + 一备件，各自 USB 电源 | `PASS` |
| Pi 常开，Jetson 非必需 | 所有 Phase 1 服务在 Pi；关键链路无 Jetson | `PASS` |
| MQTT | 版本化主题、QoS 1、LWT、ACL、持久化、应用 ACK | `PASS` |
| UTC ISO 8601 和双时间戳 | 节点时间、Pi 接收/提交时间；未同步时 null + QC | `PASS` |
| 序号 | 每次启动 64 位序号、组合身份、缺口逻辑 | `PASS` |
| RAW/SYNCHRONIZED/DERIVED | raw、canonical/readings、derived 分表 | `PASS` |
| QC 和错误可见 | 无效为 null，不变成 0 | `PASS` |
| 断网转存 | ESP 持久环 + broker 持久会话 + DB 应用 ACK | 设计 `PASS`，须 4 h 测试 |
| 12 V 与 USB 5 V/3.3 V 分开 | 12 V 分支保险和隔离接口 | `PASS` |
| RS485 用 Waveshare TTL TO RS485 (B) | Node 1 共用兼容 4800 8N1；Node 2 不兼容设置分开 | `PASS` |
| H2S 独立节点和隔离 RS232 | Node 3/Waveshare 逐线表 | 架构 `PASS`，候选仍 HOLD |
| 必须有旁路 | 80 mL/min、实测内部体积 <100 mL | 设计 `PASS`，硬件仍有门槛 |
| Ca/Mg 验证，NH4 不等于 TAN | 不猜在线 Ca/Mg；外部参考；严格命名 | `PASS` |
| 电子件干燥和永久接线 | 干燥 NEMA 箱、格兰、冷压端头、标签，无永久杜邦线 | 设计 `PASS` |
| 先接一只已验证传感器 | Release A 只有 SEN0681 | `PASS` |
| Phase 1 不做大规模 Jetson ML | 未包含 | `PASS` |

`DECISIONS.md` 没有被修改，开放项推荐仍未正式提升。

## 2. 接口兼容性

| 链路 | 电压/协议 | 设置 | 审计结果 |
|---|---|---|---|
| SEN0681 ↔ Waveshare TTL TO RS485 (B) | 传感器 12 V；隔离 RS485/Modbus | 4800 8N1，地址 1 | 针脚功能已核对，待实物测试 |
| 条件性 SEN0710 ↔ Node 1 | 同一 12 V/RS485 域 | 先单独改地址 2，4800 8N1 | 电气/协议兼容；盐水 `HOLD` |
| 条件性 SEN0711 ↔ Node 1 | 同上 | 地址 3 | 电气/协议兼容；科学/盐水 `HOLD` |
| Waveshare TTL逻辑 ↔ ESP | 3.3 V UART | GPIO17 TX→RXD；TXD→GPIO18 RX | 针脚功能 `VERIFIED` |
| EZO-pH/EC/RTD ↔ Node 1 | 3.3 V I2C；pH/EC 探头由载板隔离 | 100 kHz，`0x63/0x64/0x66` | 地址唯一；须测总上拉 |
| RDO Blue ↔ Waveshare-A | 12 V，隔离 RS485 Modbus | 19200 8E1，地址 1 | `VERIFIED`；受控 A/B 后备程序 |
| SEN0709 ↔ Waveshare-B | 12 V，隔离 RS485 | 4800 8N1，地址 1 | 分开 UART 无冲突；盐水 `HOLD` |
| S1-1020 ↔ 隔离 RS232 | 传感器 12 V，ASCII RS232 | 38400 8N1，LF，`GETDATA ALL` | 协议兼容；采购 `HOLD` |
| DFR0565 ↔ Node 4 | 控制侧 5 V I2C | GPIO8/9，100 kHz | `VERIFIED` |
| DFR0565 → Pololu | 隔离 5 V → 3.3 V | 能力 150 mA，已知负载约 19 mA | `PASS`；流量计处实测 3.2–3.8 V |
| SLF3S ↔ 隔离 I2C | 3.3 V/IGND4 | `0x08` + CRC | `PASS`；需盐水重量法校准 |
| EZO-PMP ↔ 同一隔离 I2C | 逻辑 3.3 V；电机独立 12 V | `0x67`，`DC,80,*` | 地址/电压兼容；须复位恢复测试 |
| ESP ↔ Pi | 电源域独立 | Wi-Fi/MQTT QoS 1、CBOR、逐节点 ACL | 设计 `PASS` |

Node 2 两只 RS485 设备不能因为“都是 RS485”就并到同一 UART，它们的 baud/parity 不同。Node 4 泵和流量计可以共用隔离 I2C，因为地址和电源兼容。

## 3. 科学含义兼容性

| 设备/量 | 可以怎样称呼 | 禁止的捷径 |
|---|---|---|
| SEN0681 | `dissolved_oxygen_mg_l`、饱和度、内部温度 | 在 15–25 ppt 缸中保留默认 30 ‰ 补偿。 |
| Atlas EC | 原始电导率为主，盐度为带算法版本的同步/派生值 | 把计算盐度当独立传感器。 |
| SEN0710 | `turbidity_ntu` | 配对重量法标定前叫 eTSS。 |
| SEN0711 | 验证期叫 `ammonia_n_reported_mg_l` | 未验证就叫 NH4+、NH3 或 TAN。 |
| RDO Blue | 使用已配置盐度的底层 DO | 补偿值过旧仍假设中层盐度最新。 |
| ORP | 当前参比系统下的 mV | 只凭 ORP 换算 H2S 浓度。 |
| S1-1020 | 盐水批准且准确量程后的溶解 H2S | 用顶空气体 H2S 传感器替代。 |
| SLF3S | 重量法校正后的相对/盐水流量 | 直接宣称厂家水标精度适用于 15–25 ppt。 |
| Mg/Ca/NO2/NO3/碱度/TAN | 时间对齐的外部验证结果 | 强行加入未验证在线 ISE/湿化学通道。 |

Hanna `HI97115C` 只作可选外部筛查仪器，不是主要参考。其 Ca 200–600 ppm、Mg 1000–1800 ppm 量程无法覆盖按正常海水组成稀释至 15–25 ppt 后的全部预期浓度；其海水方法基质和手册版本也要验证。

## 4. 环境和机械风险

| 风险 | 设计控制 | 剩余门槛 |
|---|---|---|
| 盐雾/冷凝 | 干燥高位盒、格兰、滴水弯、干燥剂、应力释放 | 实体盒尺寸与线径。 |
| 生物污染 | 清洁事件、光窗检查、流量/过滤趋势、参考比对 | 连续测试确定实际周期，不能超过厂家寿命。 |
| 底泥 | RDO/ORP/H2S 头高于沉积物，做空间调试 | 缸体调查后定支架高度。 |
| 线缆受力/虾接触 | 探头固定、进水护罩、固定线路 | 缸体专用支架。 |
| 旁路漏水/虹吸 | 蠕动泵、回水气隙、干式接液盘、夹具、低流停泵 | 24 h 检漏及泵开/关 DO 影响。 |
| 接液腐蚀/毒性 | 只用有证据的 PP/PVDF/HDPE/PEEK/316L；禁铜/黄铜/普通钢 | 准确接头/弹性体 SKU。 |
| 死体积 | 管长 ≤1.2 m、池 ≤40 mL、总量实测 <100 mL | Mg/Ca 几何未知，最终池 HOLD。 |
| 泵磨损 | 备用泵盒、30 天初检、厂家寿命硬门槛 | 用实测确定更短周期。 |

## 5. 供电和数据审计结论

12 V 已知设计分配不含 H2S 为 0.780 A。GST25A12-P1J 是 2.08 A；保留 40% 余量时 H2S 最大/启动分配需 ≤0.706 A，25% 时 ≤0.884 A。泵的约 400 mA 暂按 600 mA 设计，等实测。

Release A 供电审计通过；完整配置的电源仍为 `PROVISIONAL`。各 12 V 负载独立 1 A 分支，2 A 主保护限制总路；节点各自 USB，Node 4 的 5 V 隔离输出在到达 SLF3S 前降为 3.3 V。

数据方面，传感器超时、断 Wi-Fi、broker/DB 故障、ESP 复位、重复、身份冲突、时钟问题、缓存满和 SSD 缺失都已有检测和保留路径。设计审计通过，但物理和软件故障注入测试仍是 Phase 1 完成条件。

## 6. 固件合同与初始采样

所有节点使用相同非阻塞模块：时钟、传感器状态机、调度、规范化/QC、确定性 CBOR、持久环、MQTT/应用 ACK、健康事件、看门狗和配置管理。单个传感器超时只记录错误并有限退避，不能重启整个节点。

| 通道 | 原始间隔 |
|---|---:|
| N1 SEN0681 DO | 5 s |
| N1 pH / EC / PT-1000 | 各 10 s；温度排在 pH/EC 前 |
| N1 条件性浊度 | 30 s |
| N1 条件性氨氮 | 60 s，只用于验证 |
| N2 RDO / 条件性 ORP | 各 5 s，分开 UART |
| N3 条件性 H2S | 10 s；响应 <25 s，连续值未必独立 |
| N4 流量 | 1 s，每个 raw 保存 |
| N4 泵状态 | 60 s 及每次状态变化 |
| 所有节点健康 | 30 s |

配置必须拒绝重复 I2C/Modbus 地址、不支持的串口格式、资产表中没有的 sensor ID，以及未经审批就启用 H2S/泵。每个部署配置都有内容哈希、版本和回滚副本。

## 7. 采购放行总览

现在第一批可买：ESP32-S3-DevKitC-1-N8R8、Waveshare TTL TO RS485 (B) Part No. 23778、SEN0681；一个节点的 USB 电源/线；12 V 配电保护；干燥盒/线材/标签；盘点后的 Pi SSD/网络；台架工具和参考盐度设备。

推荐但需正式提升：pH 链、EC-KIT-10、KIT-306/PT-THRD、EZO-PMP、EK-SLF3S-4000B、双管径旁路、Pi 软件栈。

购买前核实：SEN0710 长期盐水；SEN0711 计量基础/干扰/盐水/外比；SEN0709 长期盐水；S1-1020 订货码/盐水/最大电流/线缆/维护；最终流通池探头几何；准确软管/接头/格兰/盒尺寸。

延后且不阻塞：在线 Mg/Ca、在线 NO2/NO3/碱度、Jetson/ML。

## 8. 调试顺序

1. 冻结并拍摄 Release A 实物，记录资产、固件和资料版本。
2. 搭建干燥配电和一只 Node 1 箱，做禁接连续性和带载电压测试。
3. SEN0681 单独设 4800 8N1/地址 1，写入并读回实际盐度，保存 100 个正确帧。
4. 用模拟器启动 Pi SSD/chrony/Mosquitto/PostgreSQL/ingestor/Grafana。
5. 让真实 SEN0681 走完全链路，核对 raw、双 UTC、序号、QC、永久数据库和图表。
6. 通过节点/Wi-Fi/broker/ingestor/DB/Pi 重启、4 h 缓存和备份恢复。
7. 连续运行 72 h 并关闭缺陷。
8. 再逐个提升并加入 pH、EC/PT-1000、RDO。
9. ORP/浊度/H2S/NH4 必须先关闭厂家书面门槛。
10. 旁路先台架校准和检漏，再安装。
11. 科学使用前做空间代表性和外部参考分析。

## 9. Phase 1 完成证据

需要有：放行 BOM、实装线表和照片；资产/固件/配置哈希；校准和厂家回复；真实传感器 raw；Pi 部署/schema/ACL/仪表盘/恢复说明；端到端证据；UTC/双时间戳；缺号/重复/冲突/QC/null-not-zero 测试；4 h 缓存报告；重启/断电矩阵；72 h 连续报告；空间和旁路代表性结果；仍未核实项明确排除。

文档可以让 Release A 开始执行，但不能只凭文档宣称 Phase 1 已经实物验收完成。
