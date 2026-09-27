# Node-2 — 原始输出样例（sample log）

以下是 **真实记录**，原样摘自 Jetson 数据库 `raw_log` 表（2026-09-27，固件 `node02-mqtt-0.1`，boot `cdcfd61afb3d26be`）。没有改写或补造。所有读数都**未校准**：EC 显示 0 是因为 K=1.000 与 K10 探头不符（QC=`CONFIGURATION_MISMATCH`），pH 没有温度补偿。这里只用来说明格式。

- **USB 串口（115200）看到的行**：和下面一样，但末尾**没有** `transport_age_ms` 和 `network_buffered`（发 MQTT 时才加）。
- **Jetson 接收时间**单独存在数据库 `received_utc` 列（下面每行前面的注释）。

## 稳定运行时的一轮（4 秒）

```text
# 00:40:00.226Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO event=TX command=R uptime_ms=1028067 seq=162 transport_boot_id=cdcfd61afb3d26be transport_seq=2175 firmware=node02-mqtt-0.1 transport_age_ms=3 network_buffered=0
# 00:40:00.356Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=PH_ATLAS_EZO event=TX command=R uptime_ms=1028067 seq=256 transport_boot_id=cdcfd61afb3d26be transport_seq=2176 firmware=node02-mqtt-0.1 transport_age_ms=68 network_buffered=0
# 00:40:00.669Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO rx_uptime_ms=1028513 seq=162 event=RX raw_hex=302E30302C302E30300D transport_boot_id=cdcfd61afb3d26be transport_seq=2177 firmware=node02-mqtt-0.1 transport_age_ms=1 network_buffered=0
# 00:40:00.813Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO rx_uptime_ms=1028518 seq=162 event=RX raw_hex=2A4F4B0D transport_boot_id=cdcfd61afb3d26be transport_seq=2178 firmware=node02-mqtt-0.1 transport_age_ms=98 network_buffered=0
# 00:40:01.070Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO seq=162 cycle=257 scheduled_uptime_ms=1028067 request_uptime_ms=1028067 rx_uptime_ms=1028513 UTC=UNSYNCED EC_uS_cm=0.000 salinity_PSU=0.000 K=1.000 compensation_setting_C=25.00 calibration_reply=?CAL,0 COMM=OK QC=CONFIGURATION_MISMATCH validation=UNVALIDATED temp_source=NOT_VERIFIED transport_boot_id=cdcfd61afb3d26be transport_seq=2179 firmware=node02-mqtt-0.1 transport_age_ms=353 network_buffered=0
# 00:40:01.380Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=PH_ATLAS_EZO rx_uptime_ms=1028695 seq=256 event=RX raw_hex=332E3435380D transport_boot_id=cdcfd61afb3d26be transport_seq=2180 firmware=node02-mqtt-0.1 transport_age_ms=421 network_buffered=0
# 00:40:01.565Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=PH_ATLAS_EZO rx_uptime_ms=1028699 seq=256 event=RX raw_hex=2A4F4B0D transport_boot_id=cdcfd61afb3d26be transport_seq=2181 firmware=node02-mqtt-0.1 transport_age_ms=671 network_buffered=0
# 00:40:01.817Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=PH_ATLAS_EZO seq=256 cycle=257 scheduled_uptime_ms=1028067 request_uptime_ms=1028067 rx_uptime_ms=1028695 UTC=UNSYNCED pH=3.458 compensation_setting_C=25.00 calibration_reply=?CAL,0 COMM=OK QC=COMPENSATION_MISSING validation=UNVALIDATED temp_source=NOT_VERIFIED transport_boot_id=cdcfd61afb3d26be transport_seq=2182 firmware=node02-mqtt-0.1 transport_age_ms=914 network_buffered=0
# 00:40:02.155Z
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be event=HEALTH uptime_ms=1030000 EC_ready=1 pH_ready=1 UTC=UNSYNCED mqtt_lost=0 usb_lost=2114 format_lost=0 line_too_long=0 queued=0 transport_boot_id=cdcfd61afb3d26be transport_seq=2183 firmware=node02-mqtt-0.1 transport_age_ms=2 network_buffered=0
# 00:40:03.967Z
[WiFi] Connected | IP=192.168.88.251 | node_id=shrimp-node02 transport_boot_id=cdcfd61afb3d26be transport_seq=2184 firmware=node02-mqtt-0.1 transport_age_ms=2 network_buffered=0
```

每个传感器一轮 4 行：**TX**（发命令 `R`）→ **RX**（数值回复）→ **RX**（`*OK` 确认）→ **结果行**。加上 Wi-Fi 和 HEALTH，平均约 2.3 行/秒，比 Node 1 多很多。

`usb_lost=2114`：当时没有人读 USB 串口，USB 队列满了被丢弃的行数。**不影响** MQTT 发送（`mqtt_lost=0`）。

## 五种行

| 行 | 什么时候出现 | 用途 |
|---|---|---|
| `event=TX command=…` | 每次向 EZO 模块发命令 | 记录发了什么（读数用 `R`，初始化时有查询和输出设置） |
| `event=RX raw_hex=…` | 每收到一段回复 | 模块原始回复的 ASCII 字节（十六进制），原样保存 |
| 结果行（含 `EC_uS_cm` 或 `pH`） | 每 4 s 每个传感器一行 | 解码后的值 + 设置信息 + QC |
| `event=HEALTH` | 每 10 s | 模块是否就绪、各种丢失计数、发送队列长度 |
| `[WiFi] …` | 每 5 s | 网络状态 |

另外还有 `event=BOOT`（开机）、`event=READY`（模块初始化完成）、`event=REPLY_TIMEOUT`（没回复）、`event=POLL_SKIPPED_NOT_READY`（模块未就绪，本轮跳过）。

## raw_hex 怎么读

EZO 模块回的是 ASCII 文本，以回车 `0D` 结尾：

| raw_hex | 文字 | 含义 |
|---|---|---|
| `302E30302C302E30300D` | `0.00,0.00` | EC 回复：EC=0.00 µS/cm，盐度=0.00 PSU（按 `O,EC,1`、`O,S,1` 设置的输出顺序） |
| `332E3435380D` | `3.458` | pH 回复 |
| `2A4F4B0D` | `*OK` | 命令已执行 |
| `3F492C45432C322E31370D` | `?I,EC,2.17` | 设备信息：EC 模块，固件 2.17 |
| `3F4B2C312E30300D` | `?K,1.00` | 探头常数 K=1.00（**与 K10 探头不符**） |
| `3F542C32352E30300D` | `?T,25.00` | 温度补偿设定 25 °C（设定值，不是实测水温） |
| `3F43414C2C300D` | `?CAL,0` | 没有校准记录 |

## 结果行的字段（以 EC 为例）

| 字段 | 本例 | 含义 |
|---|---|---|
| `seq` / `cycle` | 162 / 257 | 该传感器第几次读取 / 第几个 4 s 调度轮（EC 中途掉线过，所以两者相差大） |
| `request_uptime_ms` / `rx_uptime_ms` | 1028067 / 1028513 | 发 `R` 和收到回复的开机毫秒数（EZO 读数约需 450–630 ms） |
| `UTC` | UNSYNCED | 没有可信 UTC |
| `EC_uS_cm` / `salinity_PSU` | 0.000 / 0.000 | 模块真实回复的值，不是软件填 0 |
| `K` | 1.000 | 模块里存的探头常数 |
| `compensation_setting_C` | 25.00 | 模块里存的温度补偿设定 |
| `calibration_reply` | ?CAL,0 | 校准状态 |
| `QC` | CONFIGURATION_MISMATCH | K 与探头不符，网页不把这个值画成正常曲线 |
| `validation` / `temp_source` | UNVALIDATED / NOT_VERIFIED | 未验证；温度来源未验证 |
| `transport_*` / `firmware` / `network_buffered` | | 同 Node 1，见 [Node-1 样例](../Node-1/SAMPLE_LOG.md) 的“字段含义” |

## EC 模块初始化的样子

EC 掉线重新接好后（00:29），固件自动重试初始化。节选（去掉了中间穿插的 pH 行）：

```text
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO uptime_ms=378015 event=STOP_CONTINUOUS_C0 seq=0 cycle=0 transport_boot_id=cdcfd61afb3d26be transport_seq=660 firmware=node02-mqtt-0.1 transport_age_ms=73 network_buffered=0
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO event=TX command=i uptime_ms=380838 seq=0 transport_boot_id=cdcfd61afb3d26be transport_seq=672 firmware=node02-mqtt-0.1 transport_age_ms=1506 network_buffered=0
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO rx_uptime_ms=380853 seq=0 event=RX raw_hex=3F492C45432C322E31370D transport_boot_id=cdcfd61afb3d26be transport_seq=673 firmware=node02-mqtt-0.1 transport_age_ms=1743 network_buffered=0
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO event=TX command=K,? uptime_ms=381057 seq=0 transport_boot_id=cdcfd61afb3d26be transport_seq=675 firmware=node02-mqtt-0.1 transport_age_ms=2036 network_buffered=0
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO rx_uptime_ms=381071 seq=0 event=RX raw_hex=3F4B2C312E30300D transport_boot_id=cdcfd61afb3d26be transport_seq=676 firmware=node02-mqtt-0.1 transport_age_ms=2268 network_buffered=0
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO event=TX command=O,EC,1 uptime_ms=381714 seq=0 transport_boot_id=cdcfd61afb3d26be transport_seq=684 firmware=node02-mqtt-0.1 transport_age_ms=3639 network_buffered=0
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO event=TX command=O,S,1 uptime_ms=382141 seq=0 transport_boot_id=cdcfd61afb3d26be transport_seq=689 firmware=node02-mqtt-0.1 transport_age_ms=4449 network_buffered=0
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO uptime_ms=382566 event=READY seq=0 cycle=0 transport_boot_id=cdcfd61afb3d26be transport_seq=693 firmware=node02-mqtt-0.1 transport_age_ms=5024 network_buffered=0
```

顺序：停止连续输出（`C,0`）→ 查设备信息（`i`）→ 查 K（`K,?`）→ 查温度补偿（`T,?`）→ 查校准（`Cal,?`）→ 写输出设置（`O,EC,1`、`O,TDS,0`、`O,S,1`、`O,SG,0`）→ `READY`。只写输出设置，不写 K、校准或温度。初始化时一连串行会让 `transport_age_ms` 暂时升到约 5 s（发送能力限制，见 [固件 README](script/Atlas_EC_pH_MQTT/README.md#容量与限制条件)）。

## 模块没回复的样子（EC 掉线时）

```text
node_id=shrimp-node02 boot_id=cdcfd61afb3d26be sensor=EC_ATLAS_EZO uptime_ms=5815 event=REPLY_TIMEOUT seq=0 cycle=0 transport_boot_id=cdcfd61afb3d26be transport_seq=25 firmware=node02-mqtt-0.1 transport_age_ms=2263 network_buffered=0
sensor=EC_ATLAS_EZO event=POLL_SKIPPED_NOT_READY cycle=94 transport_boot_id=cdcfd61afb3d26be transport_seq=654 firmware=node02-mqtt-0.1 transport_age_ms=2 network_buffered=0
```

这时不产生 EC 数值行，网页 EC 显示过期，不会显示 0。

注意：同一时段（00:29，重新接线期间）pH 读数曾出现 0.309、1.044，之后回到约 3.4。这些是接线扰动期间的原始值，已原样保存，不能当作水样 pH。
