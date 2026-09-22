# Phase 1 工程设计包（中文导读）

**版本：** 2026-09-03  
**英文工程基准：** [Phase-1 Engineering Design Package](../README.md)  
**项目范围：** 100 L 南美白对虾（*Litopenaeus vannamei*）养殖缸，盐度 15–25 ppt，连续实时监测

> 小白解释：这一整套系统的任务，是把水里的真实读数安全、完整地送进数据库和实时仪表盘。它首先是“科研数据采集系统”，不是自动加药或自动控制系统。

## 1. 双语文档怎么使用

英文文件保留为精确工程基准；中文文件负责翻译、解释和操作提示。型号、料号、电压、引脚、线号、寄存器、串口参数和英文状态词不翻写成另一套名称。

如果中英文出现矛盾：

1. 立即停止接线、采购或通电；
2. 以仓库根目录的 `SPEC.md`、`DECISIONS.md` 和英文工程页为控制文本；
3. 记录差异并复核，不能凭感觉选一个版本。

## 2. 中文文档索引

| 中文读者版 | 英文工程版 | 适合解决的问题 |
|---|---|---|
| [硬件小白入门指南](BEGINNER_GUIDE.md) | — | 完全不懂电压、接口、隔离和万用表时先读这里。 |
| [传感器核实与选择](SENSOR_VERIFICATION.md) | [Sensor verification](../SENSOR_VERIFICATION.md) | 哪些传感器可以买，哪些必须等厂家回复，为什么。 |
| [物料清单与采购说明](BOM.md) | [BOM](../BOM.md) | 买什么、买几个、哪些现在不能买。 |
| [逐线接线与 GPIO 说明](WIRING_AND_GPIO.md) | [Wiring and GPIO](../WIRING_AND_GPIO.md) | 每根线去哪里，哪些地线绝对不能相连。 |
| [供电架构](POWER_ARCHITECTURE.md) | [Power architecture](../POWER_ARCHITECTURE.md) | 12 V、5 V、3.3 V 如何分开，保险丝和安全检查。 |
| [旁路、泵与流量设计](BYPASS_DESIGN.md) | [Bypass design](../BYPASS_DESIGN.md) | 小流量取样回路怎么装，为什么设为 80 mL/min。 |
| [树莓派与数据完整性](PI_DATA_ARCHITECTURE.md) | [Pi/data architecture](../PI_DATA_ARCHITECTURE.md) | 数据如何从 ESP32 进入数据库，断网时为什么不会变成 0。 |
| [最终兼容性审计](COMPATIBILITY_AUDIT.md) | [Compatibility audit](../COMPATIBILITY_AUDIT.md) | 开工前检查是否还有冲突或缺证据。 |
| [资料来源登记表](SOURCE_REGISTER.md) | [Source register](../SOURCE_REGISTER.md) | 每个关键参数来自哪份厂家资料。 |

## 3. 状态词：看到它就知道能不能买

英文状态词是受控字段，中文只解释含义。

| 英文状态 | 中文含义 | 你应该怎么做 |
|---|---|---|
| `LOCKED` | 已正式锁定 | 严格照做，不能自行换型号或改参数。 |
| `VERIFIED` | 已由当前厂家资料核实 | 该项事实有证据，但仍要按验收步骤检查实物。 |
| `RECOMMENDED — REQUIRES PROMOTION` | 工程上推荐，但尚未正式锁定 | 可以评审，正式采购前需写入 `DECISIONS.md`。 |
| `RELEASE A` | 第一批可放行 | 用于最小可行链路，仍须完成到货和上电检查。 |
| `RELEASE B` | 后续批次可放行 | 通常等第一链路通过后再加入。 |
| `VERIFY BEFORE PURCHASE` | 购买前必须核实 | 暂停下单；缺少关键厂家证据。 |
| `HOLD` | 暂停 | 不买、不装、不接电，直到列出的门槛关闭。 |
| `DEFERRED` | 延后 | Phase 1 暂不做，不代表永远不做。 |
| `REJECTED` | 本用途不采用 | 已知限制不满足本项目，不能因为便宜而替换回来。 |
| `NOT VERIFIED` | 未核实 | 不能把猜测当规格。 |

> 小白解释：`VERIFIED` 不等于“买来随便接就能用”；它只表示文档事实已被核实。真正安装仍要做极性、电压、线序、绝缘和通信测试。

## 4. 整个系统的一句话路线

```text
水中传感器
  → 隔离接口板
  → ESP32 采集节点
  → Wi-Fi / MQTT
  → Raspberry Pi
  → PostgreSQL 数据库
  → Grafana 实时仪表盘
```

第一条必须优先跑通的链路是：

```text
SEN0681 海水溶氧传感器
  → Waveshare TTL TO RS485 (B) 隔离转换器
  → ESP32-S3 Node 1
  → Wi-Fi / MQTT
  → Raspberry Pi / PostgreSQL / Grafana
```

> 小白解释：先让“一只已经核实的传感器”从头到尾稳定工作，比一次接上十只传感器更容易发现问题。后面每增加一个设备，都能知道新故障是谁带来的。

## 5. 四个节点分别做什么

| 节点 | 主要任务 | 当前边界 |
|---|---|---|
| Node 1 | 中层水：溶氧、pH、电导率/盐度、温度；浊度和氨氮为条件项 | 先只接 SEN0681。 |
| Node 2 | 底层风险：RDO Blue 溶氧；ORP 为条件项 | 两个串口分开，避免不同串口参数和故障互相影响。 |
| Node 3 | 溶解 H2S | 只有 S1-1020 的盐水兼容性、最大电流、准确订货码等确认后才采购。 |
| Node 4 | 旁路泵和流量计 | 只控制取样循环；不做自动加药。Mg/Ca 接口预留但不猜型号。 |

## 6. 三个最重要的电压世界

| 电压域 | 用在哪里 | 绝对不要做什么 |
|---|---|---|
| 12 V `S12` | 工业探头和 EZO-PMP 电机 | 不可直接接 ESP32 引脚；`SGND12` 不可随意接 `LGND`。 |
| USB 5 V | 每个 ESP32 节点各一只合规 USB 电源 | 不要把各节点地线因为“都是黑线”就接在一起。 |
| 3.3 V | ESP32 逻辑和接口板逻辑侧 | 不要给 SLF3S 流量计 5 V；其允许范围是 3.2–3.8 V。 |

“隔离”可以想象成两座小岛之间用翻译员讲话：数据可以过去，但两边的地线不直接用铜线连起来。这样能减少水中电极、长线和 USB 电源之间的地环路。

## 7. 第一阶段明确不做的事

- 不让 Jetson/机器学习拖慢最基本的数据链路。
- 不做自动投药或自动水质控制。
- 不把错误、无效或缺失读数写成 0。
- 不把浊度直接叫作 eTSS，除非做过本缸配对标定。
- 不把厂家所称“ammonia nitrogen”擅自改名为 `NH4+`、TAN 或 `NH3`。
- 不为 Mg/Ca 猜传感器型号或先钻流通池孔。
- 不在永久接线中使用松散杜邦线、未隔离 MAX3232 或裸 RS485 板。

## 8. 建议阅读顺序

1. 先读 [硬件小白入门指南](BEGINNER_GUIDE.md)，只理解概念，不通电。
2. 读 [物料清单](BOM.md)，区分 `RELEASE`、`HOLD` 和 `DEFERRED`。
3. 读 [供电架构](POWER_ARCHITECTURE.md)，画出 12 V、5 V、3.3 V 和各地线。
4. 只针对 Release A 阅读 [Node 1 接线](WIRING_AND_GPIO.md#5-node-1第一条链路)。
5. 先在桌面上完成 SEN0681 单传感器测试，再进入树莓派数据链路。
6. 第一条链路通过 72 h 连续测试后，按兼容性审计顺序逐个扩展。

## 9. 当前推荐，但尚未自动变成锁定决定

| 开放项 | 推荐方向 | 当前状态 |
|---|---|---|
| pH | Atlas `ENV-50-pH-NT`（SMA）+ EZO-pH + ISCCB-2 | `RECOMMENDED — REQUIRES PROMOTION` |
| EC/盐度 | Atlas `EC-KIT-10` + 独立 PT-1000 温度补偿 | `RECOMMENDED — REQUIRES PROMOTION` |
| 旁路泵 | Atlas `EZO-PMP`，Node 4 发送 `DC,80,*` | `RECOMMENDED — REQUIRES PROMOTION` |
| 流量计 | Sensirion `EK-SLF3S-4000B`，用盐水做重量法标定 | `RECOMMENDED — REQUIRES PROMOTION` |
| 树莓派软件 | Mosquitto + Python + PostgreSQL + Grafana + Docker Compose；主机 chrony | `RECOMMENDED — REQUIRES PROMOTION` |

这些推荐没有修改 `DECISIONS.md`。正式锁定前仍需按变更控制逐项批准。

## 10. 动手前的总停机线

出现以下任一情况就先停：

- 不知道一根线的两端确切名称；
- 只凭线色判断功能，没有对照厂家针脚和连续性；
- 万用表显示 12 V 传感器地与 ESP32 `LGND` 意外导通；
- SLF3S 的电源不是实测 3.2–3.8 V；
- 电源极性、插头尺寸或保险丝额定值还没核实；
- 接线盒可能被水溅、冷凝或拉扯；
- `HOLD`/`VERIFY BEFORE PURCHASE` 项还没有书面证据；
- 想用一个“差不多”的替代品，但型号、接口或电压不同。

任何市电插座、GFCI/RCD 或设施布线问题都交给合格电工处理。项目盒内只做已设计的低压直流分配，不自行剪接市电线。
