# Node 1 MQTT 实验版本（2026-09-26 已烧录，局域网链路已实测）

2026-09-26：准备 ESP32 → 实验室 Wi-Fi → Jetson MQTT → SQLite → 网页链路。原 `../DO_ORP_WiFi/` 保持不变，作为源代码回退版本。当前板上仍是旧程序；源码备份不是板上二进制回读备份。

## 保持的传感器行为

DO UART1 RX18/TX17，ORP UART2 RX16/TX15；4800 / 8N1；4000 ms 共同调度；仅 Modbus 功能码 03 读取。Protocol.h、BenchChannel.h 与旧版逐字相同。解析、范围检查及 raw、QC、seq、cycle、request/rx uptime 都保留。不写校准、补偿、地址或探头设置。

## 新增行为

- 整行日志入队，USB 有限队列（8 条），不等待未打开/拥塞的 USB 终端。
- 网络独立 FreeRTOS 任务；Arduino MQTT 2.5.2，MQTT QoS 1，20 秒 keepalive；LWT/上线状态主题 `shrimp/lab/shrimp-node01/status`。
- 记录主题 `shrimp/lab/shrimp-node01/records`，ACK 主题 `shrimp/lab/shrimp-node01/ack`。
- 每条日志带独立 `transport_boot_id` + `transport_seq`，不替代各传感器 seq。Jetson 完成数据库事务后才发 `boot:transport_seq` ACK。发送端没收到应用 ACK 就保留队首，每 5 秒重试，故即使 broker 的 MQTT PUBACK 先到，也不会提前删除记录。
- RAM 队列 64 条，满后丢弃新日志并累计 `mqtt_lost`。每 10 秒 health 报告队列和 mqtt/USB/格式丢失计数。整个队列断电丢失，不宣称持久可靠缓存；恢复后 health 才可能报告溢出。
- `transport_age_ms` 是日志完成至尝试发送的单调时钟间隔，超过 15 秒标记 buffered；不能作为准确 UTC。broker 内等待时间不包含在该 age，需在正式验收中进一步限制，不能把网络到达时间当采样时间。
- 始终保留 `UTC=UNSYNCED`，本阶段尚未实现离线局域网 NTP。原始读数 `UNVALIDATED` 不变。
- 固件只允许 Node 1 MAC `44:B1:76:CE:D1:A8` 启用传感器轮询，错误板不会启动轮询。这不替代烧录前核对目标。

## 工具和配置

板配置沿用项目记录：ESP32S3 Dev Module，16 MB Flash，QIO，OPI PSRAM，Hardware CDC and JTAG，USB CDC On Boot Enabled。Arduino ESP32 core 固定 3.3.11，MQTT library 固定 2.5.2。工具暂存仓库忽略目录 `.codex-build/`。

在 Jetson 的 VS Code 终端，从仓库根目录运行：

```bash
python3 lab_scale/jetson_web/configure_node1.py
```

按提示在终端输入实验室 Wi-Fi SSID 和密码；密码不显示，不发到聊天。该脚本读取本地已生成的 MQTT 密码，写入此目录下的 `arduino_secrets.h`（Git 忽略，0600 权限）。Jetson 当前实验室 IP 为 192.168.88.249，变化后需重新核对并更新 broker 与固件配置。

先编译检查，再由用户明确确认目标板、影响和回退方式后烧录。不得自动上传 Node 2。尚未进行实板断网恢复、USB 关闭不阻塞、缓冲溢出、重启、实际 MQTT 数据验收；测试通过不代表完成这些验收。

## 来源

- MQTT 库 API / QoS / callback：https://github.com/256dpi/arduino-mqtt
- Arduino CLI：https://docs.arduino.cc/arduino-cli/
- 本项目既有传感器读取与硬件约束：Node-1/COMMUNICATION.md、WIRING.md、SPEC.md。

编译命令（仓库根目录）：

```bash
# 仅检查源码，使用空凭据模板；此产物禁止烧录。
python3 lab_scale/jetson_web/build_node1.py --check
# 本地配置完成后编译真实配置；仍然不会烧录。
python3 lab_scale/jetson_web/build_node1.py
```

编译产物分别放 `.codex-build/node1-check/` 和 `.codex-build/node1-configured/`，均不入 Git。烧录前还需对连接的 Node 1 做身份复核，准备板上固件回读备份并取得用户确认；本脚本没有上传命令。

烧录前准备时的验证结果（2026-09-26，已被下方实板结果取代）：ESP32 core 3.3.11 + MQTT 2.5.2 按上述 N16R8/CDC 配置编译通过，程序 901875 bytes（68%）、静态全局 RAM 49660 bytes（15%）。该结果来自空凭据模板检查，**不是可烧录配置**；RAM 数字不包含运行时创建的队列与任务。既有 C++ 传感器协议回归通过；网页/MQTT 的 12 项测试通过。未进行实板 MQTT 验收。

## 2026-09-26 烧录与实板结果

已烧录到 Node 1（MAC `44:B1:76:CE:D1:A8`），经 MQTT 实测送达 Jetson 数据库与网页。烧录前把板上 16 MB flash 整体回读备份到 `.codex-build/node1-backup/`（含 sha256，不入 Git）。

烧录后修正的两个问题（都会让链路失败）：

1. **MQTT 写缓冲太小**：原 `MQTTClient mqtt{256,256}`，但一条传感器记录实测 381–427 B，库会返回 `LWMQTT_BUFFER_TOO_SHORT`，结果是“连上 MQTT 却一条数据都发不出”。改为 `{256,1536}`。
2. **板身份检查读到空值**：`WiFi.macAddress()` 在网卡就绪前为空，导致 `setup()` 静默退出（无串口、不上网）。改为读 eFuse 出厂 MAC；身份不符时 USB 每 5 s 打印 `event=WRONG_BOARD`。

另外本地配置曾填错 SSID（非 2.4 GHz 网络），改为实验室 2.4 GHz SSID 后连接成功。

回退到烧录前的旧程序（仓库根目录，Node 1 接 Jetson USB 时）：

```bash
.codex-build/arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool --chip esp32s3 --port /dev/ttyACM0 write-flash 0 .codex-build/node1-backup/node1-flash-before-mqtt-*.bin
```

回读备份注意：esptool 默认 stub 模式在地址 0x6A000 处稳定中断；需用 `--no-stub` 并按 1 MB 分块读取（约 28 s/MB）。

## 容量与限制条件

以下数字来自源码常量、编译输出（ESP32 core 3.3.11，MQTT 2.5.2）及 2026-09-26 实测；“估算”项未经长时间验证。

### 程序与内存

| 项目 | 数值 | 说明 |
|---|---|---|
| 程序大小 | 901,747 B / 1,310,720 B（68%） | 编译输出的 app 分区上限；板子 flash 共 16 MB，其余未用于程序 |
| 静态全局 RAM | 49,660 B / 327,680 B（15%） | 不含运行时创建的队列和任务 |
| 发送队列 `pending` | 64 条 × 约 1,168 B ≈ 74.8 KB | 内部 RAM（FreeRTOS 队列），**断电/重启即丢失** |
| USB 队列 | 8 条 × 约 1,168 B ≈ 9.3 KB | 满了就丢弃并计 `usb_lost`，不影响 MQTT |
| MQTT 发送任务栈 | 8,192 B | 含 1,280 B 发送缓冲 |
| MQTT 缓冲 | 读 256 B / 写 1,536 B | ACK 很短；写缓冲须容纳 topic + 头 + 整条记录 |
| PSRAM 8 MB | 未使用 | 缓冲可扩展的方向之一 |

### 单条记录长度

| 限制 | 数值 | 超出时 |
|---|---|---|
| 固件拼行缓冲 `assembling` | 959 字符 | 整行丢弃，计 `format_lost` |
| 记录 `Record.text`（含传输后缀） | 1,152 B | `snprintf` 截断 |
| 发送文本 `outgoing`（再加 age 字段） | 1,280 B | 本次不发送，5 s 后重试 |
| Broker `message_size_limit` / Jetson 接收上限 | 8,192 B | 拒收 |
| 实测长度 | DO 约 427 B、ORP 约 386 B、HEALTH 约 255 B、Wi-Fi 状态约 155 B | 平均约 321 B |

### 速率与缓冲时长

| 项目 | 数值 |
|---|---|
| 传感器轮询 | 每 4,000 ms 一轮（DO + ORP 各 1 次） |
| 实测记录速率 | 465 条 / 579 s ≈ **0.80 条/s**（传感器行 + Wi-Fi 状态 + HEALTH） |
| 64 条队列可覆盖的断网时间 | 约 **80 s**（估算）；更长的中断会丢弃**最新**记录并累计 `mqtt_lost` |
| 发送方式 | 一次只发一条，收到 Jetson 落库 ACK 才发下一条；无 ACK 每 5 s 重发 |
| 发送能力上限 | 实测相邻记录到达间隔最短约 107 ms，约 **4–10 条/s**（原因可能是 Wi-Fi 省电模式，未验证）；Node 1 平时 0.8 条/s，余量充足 |
| MQTT keepalive / 连接超时 / 重连间隔 | 20 s / 2 s / 5 s |
| Wi-Fi 重连 | 每 30 s 调用一次 `WiFi.reconnect()`，另开启自动重连 |
| `network_buffered=1` 判定 | 记录生成到尝试发送超过 15 s |

### 已实测的恢复行为

- Jetson broker/接收器停 25 s：14 条记录补发并标 `network_buffered=1`，transport_seq 1–81 连续，无拒收。
- 换电源（USB 从 Jetson 改到充电头）：重启，新 `boot_id`，约 18 s 恢复上传。重启时队列里未发出的记录丢失，数量不可知（正常时 `queued` 通常为 1）。
- 无主机读取 USB 时 `usb_lost` 持续增加，属预期。

### 可能影响顶层设计的限制（待决定）

1. **断网缓冲只有约 80 s，且只在 RAM**：不满足 SPEC §24 store-and-forward，也不满足 §47“临时断网后保留数据”的验收。可选方向：PSRAM 队列（容量大但仍断电丢失）、LittleFS（持久但要控制 flash 磨损）、SD 卡。
2. **没有 UTC 采样时间**：全部 `UTC=UNSYNCED`，网页时间是 Jetson 接收时间。需要在局域网内提供 NTP（Jetson/Pi 或路由器），SPEC §19。
3. **逐条确认的发送方式**：简单可靠，但积压后补发速度受往返时延限制；长时间积压的清空速度未测。
4. **传输格式是整行文本（key=value）**：保留了原始日志，但每条约 321 B，比结构化消息大，Jetson 端要重新解析。
5. **broker 在 Jetson，不在 Raspberry Pi**：这是临时演示，与 SPEC §4.2、§43 的正式架构不同；迁到 Pi 需要改 `MQTT_HOST` 并重新烧录。
6. **Node 1 供电只有 USB 充电头，没有 UPS**：一断电，节点和 RAM 缓冲一起丢失。
