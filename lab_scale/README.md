# lab_scale — 实验室台架

整理日期：2026-09-22；**2026-09-27 更新**：两个节点改为 MQTT 固件，与相机一起接入 Jetson 临时网页（见 [jetson_web](jetson_web/README.md)）；新增泵 1（pump-node-1），已烧录、校准，可在终端或登录控制页（中文 `/control`、英文 `/control/en`）控制；当天的调试过程汇总见 [pump-node-1 README](pump-node-1/README.md#调试过程2026-09-27摘要)。

## 方法与原理（台架总览）

### 方法

台架由五块 ESP32-S3 节点（Node-1、Node-2、泵 1、泵 2、Node-6 浊度）、一台水下 IP 相机和一台临时网关（Jetson）组成，全部接在实验室的 MikroTik 路由器上，不依赖校园网或互联网。

- **Node-1** 接两支 RS485 Modbus 探头（DO、ORP），每支探头经一块独立的 TTL↔RS485 转换器接到 ESP32 的一个独立 UART。
- **Node-2** 接两支 Atlas 探头（EC、pH），每支探头经自己的 EZO 电路和 ISCCB-2 隔离载板接到 ESP32 的一个独立 UART。
- 两块节点的固件结构相同：传感器驱动（`Protocol.h` / `AtlasChannel.h`）只负责收发和解析，`Telemetry.h` 只负责排队和 MQTT 发送，两者不互相等待。每 4000 ms 一个调度轮次，依次请求两支探头、各自超时判断。
- 每次请求的结果写成一行文本（字段见下文第 4 节），先进 RAM 队列，再由独立任务经 MQTT 发到网关；网关落库后回 ACK 才出队。USB 串口同时输出同样的行，拔掉 USB 不影响上传。
- **泵 1（pump-node-1）、泵 2（pump-node-2）** 是执行器节点，两台共用同一份固件代码：ESP32 经 UART 控制 Atlas EZO-PMP 蠕动泵，每 4 s 上报运行状态；操作命令反方向经 MQTT 下发，只执行白名单命令，每条都记录操作人和泵的回复。
- 相机不经 ESP32，有线 PoE 接路由器，由网关直接取视频流。
- 固件在电脑上有主机测试（第 6 节），用模拟的串口数据验证解析和状态机，不需要接板子。

### 原理

- **独立串口而不是共用总线**：Node-1 两支探头出厂 Modbus 地址都是 1，并在同一条 RS485 上会互相冲突，固件也刻意不改探头地址；Node-2 的两块隔离载板不能共用 TX/RX。分开后一支探头超时或掉线也不影响另一支（SPEC §39"单个传感器故障不能冻结整个节点"）。
- **共同调度但不是同步采样**：两支探头在同一轮次里先后请求，时间差为毫秒级；两个节点之间也没有同步。日志里的 `cycle` 记录轮次，`request_uptime_ms` 记录实际发出时刻，方便以后分析。
- **RAM 队列有上限**：每节点 64 条，满了丢弃最新并计数 `mqtt_lost`，而不是让采集停下来。代价是断网只能缓冲约 80 s（Node-1）/ 27 s（Node-2），断电全丢。持久缓存（PSRAM / LittleFS / SD 卡）是下一阶段。
- **以 MAC 核对身份**：IP 由路由器 DHCP 分配，2026-09-30 起按 MAC 做了静态租约，但文档仍以 MAC 为准。固件启动时读 eFuse 出厂 MAC，不符就不启动传感器（`WRONG_BOARD`），防止把 Node-1 的程序烧进 Node-2。
- **COMM 与 QC 分开**：`COMM=OK` 只表示协议层（CRC、帧长、ASCII 格式）通过；`QC` 才表示读数是否可用。目前所有读数 `UNVALIDATED`，因为探头都还没校准。
- **UTC 未同步就如实标记**：局域网没有 NTP 源，节点只有开机后的毫秒计数，所以一律 `UTC=UNSYNCED`；网页显示的是网关接收时间。

## 1. 节点与网络

| 文件夹 | 固件 node_id / hostname | 设备 | IP（静态租约，2026-09-30 核对） | MAC |
|---|---|---|---|---|
| [Node-1](Node-1/README.md) | shrimp-node01 | SEN0681 DO、SEN0709 ORP | 192.168.88.252 | 44:B1:76:CE:D1:A8 |
| [Node-2](Node-2/README.md) | shrimp-node02 | Atlas EC K10、Industrial pH No Temp，分别经 EZO/ISCCB-2 | 192.168.88.251 | 44:B1:76:CC:D4:84 |
| [pump-node-1](pump-node-1/README.md) | shrimp-node04（总 Node 4） | Atlas EZO-PMP 旁路蠕动泵，UART 直连单独 ESP32 | 192.168.88.248 | 7C:4F:AD:B5:33:38 |
| [pump-node-2](pump-node-2/README.md) | shrimp-node05（总 Node 5，泵 2） | Atlas EZO-PMP 第二个旁路泵（暂定），与泵 1 同接线、同代码 | 192.168.88.247 | 7C:4F:AD:B5:1C:D4 |
| [Node-6](Node-6/README.md) | shrimp-node06 | DFRobot SEN0710 浊度，RS485 Modbus，单独 ESP32 | 192.168.88.246 | 44:B1:76:CE:D8:6C |
| [camera_node](camera_node/README.md) | ONVIF name `NVT` | 水下 IP 相机（有线接路由器） | 192.168.1.88 | 00:12:34:C6:67:04 |
| [jetson_web](jetson_web/README.md) | Jetson Orin Nano（临时网关） | MQTT broker、数据库、网页 | 有线 192.168.88.249 + 临时 192.168.1.200；学校 Wi-Fi 10.141.48.128（会变） | 4C:BB:47:62:1F:66 |

路由器截图：MikroTik hAP ax3，LAN 192.168.88.1/24。五个 ESP32 节点通过 Wi-Fi，相机通过有线 PoE 路径；用户已提供 TP-Link/Omada POE150S 注入器链接，实物版本待核对。Barlus 304 相机商品标明淡水用途，不批准目标盐度下长期部署；详见 camera_node/HARDWARE.md。没有上游互联网时局域网采集和网页仍可工作；但目前没有 UTC 来源。
2026-09-30 起 Jetson 和各 ESP32 的地址在路由器上按 MAC 做了静态租约（用户设置）；相机地址是相机内设的。仍以 MAC 核对身份，不要把摄像机 IP 猜成空闲地址。

## 2. 已完成与边界

- 两块板均由用户确认为 ESP32-S3 N16R8。不是对第三方板稳压器、额定负载的认证。
- Node-1：DO 和 ORP 都曾成功返回；ORP 曾超时，交换/重接转换器后用户报告恢复，根因未隔离。
- Node-2：两块 Atlas 模块身份查询及测量请求成功。当前 EC 查询 K=1，而探头为 K10；两模块回复 `?CAL,0`；温度补偿设定 25°C 不是实测温度。
- 节点读取周期都是 4000 ms。两路请求共用同一节点的调度轮次，但不是硬件同时触发；两个 ESP32 之间也尚未同步。
- 2026-09-27：两节点经 Wi-Fi → MQTT 实时发到 Jetson，落库后才确认（ACK）；相机视频经 RTSP 进入同一网页。中文页 `http://192.168.88.249:8080`，英文页 `/en`。
- 已实测：Jetson 接收端中断 25 s 后补发无缺口；节点换电源重启后自动恢复上传。
- 仍未完成：UTC 同步、断电持久缓存（RAM 队列 64 条：Node 1 约 80 s、Node 2 约 27 s）、路由器/Wi-Fi 断开测试、长时间运行、校准、Raspberry Pi 正式网关。
- Node 1、Node 2、泵 1、泵 2 的 ESP32 都经 USB Type-C 直接接电源适配器供电（用户 2026-09-27 确认；泵 1 于当晚 20:46 EDT 前从 Jetson USB 改接独立适配器，Jetson 上已无串口设备），不接 Jetson；适配器型号未记录；没有 UPS，断电时节点和 RAM 缓冲一起丢失。要烧录或看串口日志时再把对应板子插回 Jetson。
- 2026-09-27：Jetson 于 14:12 EDT 重启后 broker/接收器/网页没有自动启动；数据库最后一条 Node 1/2 记录为 16:42:38Z（12:42 EDT），到 20:39Z 仍无新数据，这段数据未被接收（超出节点 RAM 缓冲）。这是"无开机自启"缺口的实际后果。
- 2026-09-27：新增泵 1（pump-node-1，DECISION 048）。固件 0.2 已烧录（MAC 7C:4F:AD:B5:33:38，IP 192.168.88.248）；两种校准完成（10 mL 指令实测 8.3 mL，复核 9.7 mL），恒定流量上限 45.36 mL/min；操作经 MQTT `cmd` 主题下发，只有 `pump-operator` 账号能写。终端 `jetson_web/pump_ctl.py`，网页 `/control`（中文）、`/control/en`（英文，个人账号登录）。当天遇到的问题（演示灯、泵板没上电、80 mL/min 超上限、校准被拒、两种校准独立、设定流量卡片空、控制页三次改版）及处理见 [pump-node-1 README 调试过程](pump-node-1/README.md#调试过程2026-09-27摘要)。

台架节点分配与 SPEC 的正式 MID/BOTTOM 编号分开，N16R8 与首选 N8R8 的差异在此记录，不修改正式部署设计。
台架曾使用 12 V / 5 A 电源且用户暂未安装保险丝；这是未验收现状，不是安全批准。正式部署必须遵守 SPEC 保护要求。

## 3. 编译与烧录

当前板上程序是 MQTT 版本：Node-1 `Node-1/script/DO_ORP_MQTT/`，Node-2 `Node-2/script/Atlas_EC_pH_MQTT/`；泵 1 程序 `pump-node-1/script/PMP_MQTT/`（`--node 4`，0.2 已烧录）；泵 2 程序 `pump-node-2/script/PMP_MQTT/`（`--node 5`，与泵 1 共用头文件，待烧录）。旧版 `DO_ORP_WiFi/`、`Atlas_EC_pH_UART/`（仅 USB 串口）保留作回退。

1. 保留整个 sketch 文件夹，所有 `.h` 都参与同一次编译，不单独上传。
2. 本地配置（仓库根目录）：`python3 lab_scale/jetson_web/configure_node1.py --node 1`（或 `--node 2|4|5|6 --wifi-from-node1`）生成 `arduino_secrets.h`。Wi-Fi 必须是实验室路由器的 **2.4 GHz** 网络。真实密码文件禁止提交。
3. 编译：`python3 lab_scale/jetson_web/build_node1.py --node 1|2|4|5|6`（只编译不烧录）。板设置：ESP32S3 Dev Module；16 MB Flash；QIO；OPI PSRAM；Hardware CDC and JTAG；USB CDC On Boot Enabled；core 3.3.11；MQTT 库 2.5.2。
4. 烧录前核对 `/dev/serial/by-id/` 中的 MAC 与目标节点一致，并先回读 flash 备份（见各固件 README）。固件启动时也会检查出厂 MAC，不符就不运行传感器。
5. USB Serial 115200 仍输出同样的日志行；拔掉 USB 不影响 MQTT 发送，但板子需要其他 5 V 供电。

## 4. 日志字段

| 字段 | 含义 |
|---|---|
| node_id / sensor | 节点和传感器通道标识 |
| boot_id | 本次开机标识；重启后改变 |
| seq | 此传感器本次启动的实际测量请求计数；失败请求也计数 |
| cycle | 节点的 4 秒调度轮次；启动等待、忙碌或漏调度可导致与 seq 不同 |
| scheduled_uptime_ms | 计划发起时间，距启动毫秒数 |
| request_uptime_ms | 实际请求时间，不是传感器内部精确采样时刻 |
| rx_uptime_ms | 接收时间；无字节时 Node-1 为 NA |
| UTC=UNSYNCED | 没有可信 UTC，不允许用启动时间冒充 UTC |
| raw / raw_hex | 原始帧/ASCII 字节（十六进制） |
| COMM=OK | 协议层检查通过，不等于校准有效 |
| QC / validation | 质量状态；错误不能改成数值零 |
| compensation_setting_C | Atlas 保存的补偿设置，并非温度探头读数 |

MQTT 版本每行另加 `transport_boot_id`、`transport_seq`（传输序号，检测丢失）、`firmware`、`transport_age_ms`、`network_buffered`（超过 15 s 未发出为 1）。

`seq` 和 `cycle` 的偏差不是 UTC 导致。历史日志字段尚不完全统一、部分诊断没有全部标识；正式标准化消息仍待实现。

## 5. 分文件记录

每个节点分别维护 HARDWARE.md、WIRING.md、COMMUNICATION.md、PROGRESS.md，代码在 script/。
调试历史保留在各自 PROGRESS.md，不单独建立 sessions 目录。记录是聊天证据摘要，不伪造 UTC 或完整原始数据。仓库整理记录见 [CHANGELOG.md](CHANGELOG.md)。

## 6. 本地主机测试

从仓库根目录执行（需要 clang++，不连接或写入 ESP32）：

```sh
clang++ -std=c++11 -Wall -Wextra -I lab_scale/Node-1/script/DO_ORP_WiFi lab_scale/Node-1/tests/protocol_test.cpp -o /tmp/shrimp-node1-test
/tmp/shrimp-node1-test
clang++ -std=c++11 -Wall -Wextra -fsanitize=address,undefined -I lab_scale/Node-2/tests lab_scale/Node-2/tests/test.cpp -o /tmp/shrimp-node2-test
/tmp/shrimp-node2-test
clang++ -std=c++11 -Wall -Wextra -fsanitize=address,undefined -I lab_scale/pump-node-1/tests lab_scale/pump-node-1/tests/test.cpp -o /tmp/shrimp-pump-test
/tmp/shrimp-pump-test
```

Jetson 上没有 clang++ 时用 `g++` 代替，参数相同。Node-1、Node-2 的测试编译的是旧版 sketch 目录（传感器头文件与 MQTT 版逐字节相同；Node-2 的 `BenchLog.h` 例外）。

测试覆盖协议解析/模拟状态机，不代表物理供电、盐水兼容性、校准准确性或长期稳定性已通过。

## 7. 下一阶段

- Node 2：确认 EC 探头 K 值（K10）并校准 EC、pH，加入样品温度补偿。
- 离线局域网 UTC 来源（节点与相机都需要）。
- 断网缓冲：评估 PSRAM / LittleFS / SD 卡，以及发送能力（每节点约 4–10 条/s）。
- 相机录像策略、改相机默认密码。
- 把 broker、接收器和网页迁到 Raspberry Pi（SPEC 正式架构），加开机自启和磁盘管理。
- 泵 1：流量计（OPEN-10，接触流体需隔离）；确认 40–45 mL/min 是否满足以后的流通池（SPEC §29 构想 50–150）；盐水软管兼容性；万用表确认黑线 GND 与电机负极是否相通；长时间运行与 20 天自动复位恢复。
- 泵 2（暂定第二个旁路泵）：已烧录、已校准（上限 49.63 mL/min，复核 9.85 mL）；若长期保留要修订 SPEC（DECISION 049）。
- Node-6（浊度）：已接入；读数停在满量程，待探头入水复查；盐水长期浸泡待厂家确认（DECISION 050）。
- Jetson：开机自启（2026-09-27 重启后约 4 小时数据未接收）。

相机盐水部署限制见 camera_node/HARDWARE.md。正式部署资料保留在 [tank_scale](../tank_scale/README.md)。
