# Node-1 — 调试进度

用户曾收到 DO 约 6.55 mg/L、22.85°C，ORP 309–310 mV、22.6°C；这些是未验证台架示例，不是校准结果。
后续 ORP 超时，在对调/重接转换器后用户报告两个都恢复；不能确定转换器损坏或唯一根因。
未完成长时稳定性、标准液核查、补偿及正式部署验收。


## 历史调试记录

证据：用户串口片段与恢复报告；确切实验 UTC 未提供。

1. DO 单路接通，随后加入 Wi-Fi，再加入独立 ORP 转换器，共同 4 s 调度。
2. 用户贴出 DO 与 ORP 成功帧；同 cycle 的实际请求时间相同或接近，不代表探头内部同时采样。
3. 后续 ORP 出现 `raw= COMM=ERROR QC=COMMUNICATION_ERROR reason=TIMEOUT`，DO 仍正常。
4. 用户确认 12 V，移除保护帽仍超时；按交换/重接转换器的排查后报告“两个都好了”。根因未隔离，不断言是帽子或校准问题。

以下是聊天原始成功记录节选（不是持续运行数据文件）：

```text
node_id=shrimp-node01 boot_id=ee512acae3de7398 sensor=ORP_SEN0709 seq=6 request_uptime_ms=64079 rx_uptime_ms=64121 cycle=16 scheduled_uptime_ms=64079 report_uptime_ms=64151 UTC=UNSYNCED raw=010304013600E29B88 ORP_mV=310 temperature_C=22.6 COMM=OK QC=UNVALIDATED
node_id=shrimp-node01 boot_id=ee512acae3de7398 sensor=DO_SEN0681 seq=6 request_uptime_ms=64079 rx_uptime_ms=64138 cycle=16 scheduled_uptime_ms=64079 report_uptime_ms=64168 UTC=UNSYNCED raw=01030C3F689B0640D1A59D41B6CA025DD2 DO_mg_L=6.551 saturation_pct=90.86 temperature_C=22.85 COMM=OK QC=UNVALIDATED
```

首次行的 node_id 开头在聊天拷贝时缺少两个字符，此处按同一批完整后续行恢复；其余字段照录。不把后续恢复事件与这个旧 boot_id 合并成一次连续实验。
最新给出的 DHCP 地址为 192.168.88.252，未配置固定租约的证据。

## 2026-09-26 Jetson USB 核对与 MQTT 准备

- 本机识别 `/dev/ttyACM0`，USB by-id 包含 `44:B1:76:CE:D1:A8`，与 Node 1 对应。用户添加 dialout 权限并重启后，被动读取串口成功。
- 本次串口完整末轮：DO 7.575 mg/L、饱和度 102.31%、DO 温度 21.38°C；ORP 282 mV、ORP 温度 23.2°C。均仍为 UNVALIDATED、UTC UNSYNCED。开头出现拼接日志及 MISSED_POLL_CYCLES，不能把该片段作为完整测量。
- 新增独立 DO_ORP_MQTT 版本，原读取参数/协议保留；USB 整行缓冲、网络独立任务、有限 RAM 队列、应用落库 ACK、重试及溢出计数。
- 模板凭据编译通过（ESP32 core 3.3.11 / MQTT 2.5.2）。12 项网页/MQTT 测试和 C++ 协议回归通过，测试使用临时 broker/数据库。
- Jetson 临时 broker/接收器已在本次会话前台启动，绑定 127.0.0.1 与 192.168.88.249:1883；重启后须按运行说明重新启动。配置和密码未入 Git。
- 等待用户在 Jetson 本地填写实验室 Wi-Fi 配置。尚未编译真实凭据、回读备份或烧录，新代码不代表三节点已接通。Node 2 与相机未修改。

## 2026-09-26 晚：Node 1 MQTT 固件烧录与 Jetson 端到端验证

- 烧录前经用户确认，用 esptool 5.3.1 回读板上 16 MB flash 作为旧程序备份（`.codex-build/node1-backup/`，含 sha256，不入 Git）。stub 模式在 0x6A000 处稳定中断，改用 `--no-stub` 每 1 MB 分块读取后拼接成功。
- 修正两处会导致链路失败的固件问题：MQTT 写缓冲 256 B 小于单条记录（约 400–1280 B），改为 1536 B；板身份检查改读 eFuse 出厂 MAC（`WiFi.macAddress()` 在网卡就绪前为空，导致静默退出），身份不符时 USB 每 5 s 打印 `WRONG_BOARD`。
- 本地配置 SSID 与旧固件不同导致 Wi-Fi 连不上；旧固件中 SSID 为 2.4 GHz 网络、密码相同，改回后连接成功（192.168.88.252）。
- 实测：DO、饱和度、温度、ORP 经 MQTT 写入 Jetson SQLite 并在 8080 网页 API 可见；无拒收、无序号缺口。broker/接收器停 25 s 后恢复，14 条缓冲记录补发（`network_buffered=1`），transport_seq 1–81 连续。
- 仍未完成：UTC 同步（仍 UNSYNCED）、ESP 断电缓存（RAM 队列 64 条，断电丢失）、路由器/Wi-Fi 断开测试、长时间运行、跨电脑访问验证、探头校准验证（读数 UNVALIDATED）。
- 同晚换电源测试：Node 1 从 Jetson USB 拔下改接 USB 充电头。重启后新 `boot_id=488a1b43c9de3427`，约 18 s 恢复上传，至 2026-09-27T00:03Z 已收到 122 条，无拒收、无序号问题；`usb_lost` 持续增加（无主机读 USB，属预期）。重启前未发出的 RAM 记录数量不可知。
- 此后 Jetson 的 USB 口改接 Node 2（`/dev/ttyACM0`，MAC `44:B1:76:CC:D4:84`）。Node 1 需要重新烧录时再接回。
- 容量（字节）、速率、缓冲时长和可能影响顶层设计的限制条件，统一记录在 [script/DO_ORP_MQTT/README.md](script/DO_ORP_MQTT/README.md#容量与限制条件)。要点：RAM 队列 64 条（约 74.8 KB）≈ 80 s 断网缓冲，断电丢失；单条记录实测最大 427 B；程序占 app 分区 68%。
