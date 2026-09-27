# Node-1 — 原始输出样例（sample log）

以下是 **真实记录**，原样摘自 Jetson 数据库 `raw_log` 表（2026-09-27，固件 `node01-mqtt-0.1`，boot `488a1b43c9de3427`，即换到 USB 充电头供电后的那次开机）。没有改写或补造。读数都是 `UNVALIDATED`（未校准），只用来说明格式。

- **USB 串口（115200）看到的行**：和下面一样，但末尾**没有** `transport_age_ms` 和 `network_buffered`，这两个字段是在发出 MQTT 时才加上的。
- **Jetson 接收时间**不在行内，单独存在数据库的 `received_utc` 列（下面每行前面的注释就是这个时间）。

## 开机后的前 12 行

```text
# 00:00:39.085Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 event=BOOT UTC=UNSYNCED transport=MQTT mqtt_lost=0 transport_boot_id=488a1b43c9de3427 transport_seq=1 firmware=node01-mqtt-0.1 transport_age_ms=3597 network_buffered=0
# 00:00:39.427Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 sensor=ORP_SEN0709 seq=1 request_uptime_ms=4073 rx_uptime_ms=4116 cycle=1 scheduled_uptime_ms=4073 report_uptime_ms=4146 UTC=UNSYNCED raw=010304011B00EA0A47 ORP_mV=283 temperature_C=23.4 COMM=OK QC=UNVALIDATED transport_boot_id=488a1b43c9de3427 transport_seq=2 firmware=node01-mqtt-0.1 transport_age_ms=10 network_buffered=0
# 00:00:39.649Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 sensor=DO_SEN0681 seq=1 request_uptime_ms=4073 rx_uptime_ms=4133 cycle=1 scheduled_uptime_ms=4073 report_uptime_ms=4163 UTC=UNSYNCED raw=01030C3F81F39F40EF2F7441AD8A683C19 DO_mg_L=7.475 saturation_pct=101.52 temperature_C=21.69 COMM=OK QC=UNVALIDATED transport_boot_id=488a1b43c9de3427 transport_seq=3 firmware=node01-mqtt-0.1 transport_age_ms=168 network_buffered=0
# 00:00:40.285Z
[WiFi] Connected | IP=192.168.88.252 transport_boot_id=488a1b43c9de3427 transport_seq=4 firmware=node01-mqtt-0.1 transport_age_ms=3 network_buffered=0
# 00:00:43.423Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 sensor=ORP_SEN0709 seq=2 request_uptime_ms=8073 rx_uptime_ms=8116 cycle=2 scheduled_uptime_ms=8073 report_uptime_ms=8146 UTC=UNSYNCED raw=010304011B00EA0A47 ORP_mV=283 temperature_C=23.4 COMM=OK QC=UNVALIDATED transport_boot_id=488a1b43c9de3427 transport_seq=5 firmware=node01-mqtt-0.1 transport_age_ms=3 network_buffered=0
# 00:00:43.656Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 sensor=DO_SEN0681 seq=2 request_uptime_ms=8073 rx_uptime_ms=8133 cycle=2 scheduled_uptime_ms=8073 report_uptime_ms=8163 UTC=UNSYNCED raw=01030C3F81C67340EEC55E41ADB4117E7C DO_mg_L=7.462 saturation_pct=101.39 temperature_C=21.71 COMM=OK QC=UNVALIDATED transport_boot_id=488a1b43c9de3427 transport_seq=6 firmware=node01-mqtt-0.1 transport_age_ms=171 network_buffered=0
# 00:00:45.277Z
[WiFi] Connected | IP=192.168.88.252 transport_boot_id=488a1b43c9de3427 transport_seq=7 firmware=node01-mqtt-0.1 transport_age_ms=7 network_buffered=0
# 00:00:45.394Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 event=HEALTH uptime_ms=10000 UTC=UNSYNCED mqtt_lost=0 usb_lost=0 format_lost=0 queued=1 transport_boot_id=488a1b43c9de3427 transport_seq=8 firmware=node01-mqtt-0.1 transport_age_ms=75 network_buffered=0
# 00:00:47.424Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 sensor=ORP_SEN0709 seq=3 request_uptime_ms=12073 rx_uptime_ms=12115 cycle=3 scheduled_uptime_ms=12073 report_uptime_ms=12145 UTC=UNSYNCED raw=010304011B00EA0A47 ORP_mV=283 temperature_C=23.4 COMM=OK QC=UNVALIDATED transport_boot_id=488a1b43c9de3427 transport_seq=9 firmware=node01-mqtt-0.1 transport_age_ms=9 network_buffered=0
# 00:00:47.632Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 sensor=DO_SEN0681 seq=3 request_uptime_ms=12073 rx_uptime_ms=12133 cycle=3 scheduled_uptime_ms=12073 report_uptime_ms=12163 UTC=UNSYNCED raw=01030C3F81BAF440EEE12D41AD59F7346B DO_mg_L=7.465 saturation_pct=101.35 temperature_C=21.67 COMM=OK QC=UNVALIDATED transport_boot_id=488a1b43c9de3427 transport_seq=10 firmware=node01-mqtt-0.1 transport_age_ms=161 network_buffered=0
# 00:00:50.312Z
[WiFi] Connected | IP=192.168.88.252 transport_boot_id=488a1b43c9de3427 transport_seq=11 firmware=node01-mqtt-0.1 transport_age_ms=1 network_buffered=0
# 00:00:51.423Z
node_id=shrimp-node01 boot_id=488a1b43c9de3427 sensor=ORP_SEN0709 seq=4 request_uptime_ms=16073 rx_uptime_ms=16116 cycle=4 scheduled_uptime_ms=16073 report_uptime_ms=16146 UTC=UNSYNCED raw=010304011B00EA0A47 ORP_mV=283 temperature_C=23.4 COMM=OK QC=UNVALIDATED transport_boot_id=488a1b43c9de3427 transport_seq=12 firmware=node01-mqtt-0.1 transport_age_ms=4 network_buffered=0
```

节奏：每 4 秒一轮，先 ORP 后 DO；每 5 秒一行 Wi-Fi 状态；每 10 秒一行 HEALTH。平均约 0.8 行/秒。

## 五种行

| 行 | 什么时候出现 | 用途 |
|---|---|---|
| `event=BOOT` | 每次开机一次 | 新的 `boot_id` 从这里开始；`seq` 等计数全部归零 |
| `sensor=ORP_SEN0709 ...` | 每 4 s | ORP 一次读取，含原始帧和解码值 |
| `sensor=DO_SEN0681 ...` | 每 4 s | DO 一次读取 |
| `[WiFi] Connected / Not connected` | 每 5 s | 网络状态 |
| `event=HEALTH` | 每 10 s | 丢失计数与发送队列长度 |

## 字段含义（以第 3 行 DO 为例）

| 字段 | 本例 | 含义 |
|---|---|---|
| `node_id` | shrimp-node01 | 节点 |
| `boot_id` | 488a1b43c9de3427 | 本次开机的随机 ID，重启就变 |
| `sensor` | DO_SEN0681 | 传感器通道 |
| `seq` | 1 | 该传感器本次开机的第几次请求（失败也计数） |
| `request_uptime_ms` | 4073 | 发出 Modbus 请求时的开机毫秒数 |
| `rx_uptime_ms` | 4133 | 收到最后一个字节的时间；没收到为 `NA` |
| `cycle` / `scheduled_uptime_ms` | 1 / 4073 | 第几个 4 s 调度轮、计划时间 |
| `report_uptime_ms` | 4163 | 生成这一行的时间 |
| `UTC` | UNSYNCED | 节点没有可信 UTC，**不代表采样时间已知** |
| `raw` | 01030C3F81F3…3C19 | 传感器原始 Modbus 回复（十六进制），原样保存 |
| `DO_mg_L` / `saturation_pct` / `temperature_C` | 7.475 / 101.52 / 21.69 | 由 `raw` 解码的值 |
| `COMM` | OK | 帧长度、CRC 等协议检查通过；**不等于准确** |
| `QC` | UNVALIDATED | 质量状态：未校准验证 |
| `transport_boot_id` / `transport_seq` | … / 3 | 传输序号，每一行 +1；Jetson 用它发现丢行 |
| `firmware` | node01-mqtt-0.1 | 固件版本 |
| `transport_age_ms` | 168 | 这一行生成后多久才发出（节点单调时钟） |
| `network_buffered` | 0 | `transport_age_ms` 超过 15 s 时为 1，表示这是断网后补发的旧记录 |

## 原始帧怎么解码

**DO**：`01 03 0C | 3F81F39F | 40EF2F74 | 41AD8A68 | 3C19`

- `01` 地址，`03` 功能码（读寄存器），`0C` = 12 字节数据
- `3F81F39F` → 浮点 1.01525 → ×100 = **饱和度 101.52 %**
- `40EF2F74` → **DO 7.475 mg/L**
- `41AD8A68` → **温度 21.69 °C**
- `3C19` CRC 校验

**ORP**：`01 03 04 | 011B | 00EA | 0A47`

- `011B` = 283 → **ORP 283 mV**（有符号 16 位）
- `00EA` = 234 → ÷10 = **温度 23.4 °C**
- `0A47` CRC

## 断网补发的样子

Jetson 接收端停了 25 s 期间生成的行，恢复后补发时 `network_buffered=1`（2026-09-26，boot `debb82e368bfb8b3`）：

```text
node_id=shrimp-node01 boot_id=debb82e368bfb8b3 sensor=DO_SEN0681 seq=13 request_uptime_ms=52108 rx_uptime_ms=52168 cycle=13 scheduled_uptime_ms=52108 report_uptime_ms=52198 UTC=UNSYNCED raw=01030C3F81EE2640EF568E41AD30431323 DO_mg_L=7.479 saturation_pct=101.51 temperature_C=21.65 COMM=OK QC=UNVALIDATED transport_boot_id=debb82e368bfb8b3 transport_seq=42 firmware=node01-mqtt-0.1 transport_age_ms=27314 network_buffered=1
```

`transport_age_ms=27314`：这一行在节点上等了约 27 s 才送达。网页会把它标成 STALE，不当作实时值。

## 通信失败的样子

MQTT 版本运行期间数据库里还没有出现过通信错误。按固件代码，传感器没回复时这一行会是这样（`raw=` 为空，没有数值字段，数值**不会**写成 0）：

```text
node_id=shrimp-node01 boot_id=… sensor=ORP_SEN0709 seq=… request_uptime_ms=… rx_uptime_ms=NA cycle=… scheduled_uptime_ms=… report_uptime_ms=… UTC=UNSYNCED raw= COMM=ERROR QC=COMMUNICATION_ERROR reason=TIMEOUT
```

历史上真实出现过的片段见 [PROGRESS.md](PROGRESS.md)（ORP `reason=TIMEOUT`）。
