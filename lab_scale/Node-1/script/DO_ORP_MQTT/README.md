# Node 1 MQTT 实验版本（未烧录验收）

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

本次准备验证结果（2026-09-26）：ESP32 core 3.3.11 + MQTT 2.5.2 按上述 N16R8/CDC 配置编译通过，程序 901875 bytes（68%）、静态全局 RAM 49660 bytes（15%）。该结果来自空凭据模板检查，**不是可烧录配置**；RAM 数字不包含运行时创建的队列与任务。既有 C++ 传感器协议回归通过；网页/MQTT 的 12 项测试通过。未进行实板 MQTT 验收。
