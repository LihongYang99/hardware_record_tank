# lab_scale — 实验室台架

整理日期：2026-09-22；**2026-10-12 更新**：五块 ESP32 节点（含泵 2、Node-6 浊度）接入；控制页按节点的数据记录开关、按传感器导出、`Raw_data/` 原始数据文件夹、相机每分钟存图；当前状态与待处理问题见[根目录 README](../README.md#当前进度--current-status--2026-10-12edt)。**2026-09-27**：两个节点改为 MQTT 固件，与相机一起接入 Jetson 临时网页（见 [jetson_web](jetson_web/README.md)）；新增泵 1（pump-node-1），已烧录、校准，可在终端或登录控制页（中文 `/control`、英文 `/control/en`）控制；当天的调试过程汇总见 [pump-node-1 README](pump-node-1/README.md#调试过程2026-09-27摘要)。

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
| [Node-7](Node-7/README.md) | shrimp-node07 | 双路 IoT 交流继电器 CH1 控制加热器（网关自动控温，DECISION 052） | 192.168.88.245 | 44:1B:F6:FE:73:48 |
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
- 2026-10-12：服务 10:50 EDT 启动后，Jetson 10:51 正常关机重启（不是死机或断电），broker/接收器/网页没有自动启动，8080 和 1883 无程序监听，相机临时地址 192.168.1.200 也丢失；最后一条数据 10:51:31，之后约 6.5 小时未保存。重启步骤见 [jetson_web README](jetson_web/README.md#2026-10-12jetson-重启后网页打不开)。
- 2026-09-27：新增泵 1（pump-node-1，DECISION 048）。固件 0.2 已烧录（MAC 7C:4F:AD:B5:33:38，IP 192.168.88.248）；两种校准完成（10 mL 指令实测 8.3 mL，复核 9.7 mL），恒定流量上限 45.36 mL/min；操作经 MQTT `cmd` 主题下发，只有 `pump-operator` 账号能写。终端 `jetson_web/pump_ctl.py`，网页 `/control`（中文）、`/control/en`（英文，个人账号登录）。当天遇到的问题（演示灯、泵板没上电、80 mL/min 超上限、校准被拒、两种校准独立、设定流量卡片空、控制页三次改版）及处理见 [pump-node-1 README 调试过程](pump-node-1/README.md#调试过程2026-09-27摘要)。

台架节点分配与 SPEC 的正式 MID/BOTTOM 编号分开，N16R8 与首选 N8R8 的差异在此记录，不修改正式部署设计。
台架曾使用 12 V / 5 A 电源且用户暂未安装保险丝；这是未验收现状，不是安全批准。正式部署必须遵守 SPEC 保护要求。

## 3. 编译与烧录

### 板上程序

| 节点 | `--node` | sketch | 板上版本 |
|---|---|---|---|
| Node-1 | 1 | `Node-1/script/DO_ORP_MQTT/` | node01-mqtt-0.1 |
| Node-2 | 2 | `Node-2/script/Atlas_EC_pH_MQTT/` | node02-mqtt-0.1（仓库里是 0.2 = 校准命令，待烧录，见 [CALIBRATION.md](Node-2/CALIBRATION.md)） |
| 泵 1 | 4 | `pump-node-1/script/PMP_MQTT/` | node04-pump-mqtt-0.2 |
| 泵 2 | 5 | `pump-node-2/script/PMP_MQTT/` | node05-pump-mqtt-0.2 |
| Node-6 | 6 | `Node-6/script/TURB_MQTT/` | node06-mqtt-0.1 |
| Node-7 | 7 | `Node-7/script/HEATER_MQTT/` | node07-heater-mqtt-0.1 |

旧版 `DO_ORP_WiFi/`、`Atlas_EC_pH_UART/`（仅 USB 串口）保留作回退。保留整个 sketch 文件夹，所有 `.h` 一起编译。板设置：ESP32S3 Dev Module；16 MB Flash；QIO；OPI PSRAM；Hardware CDC and JTAG；USB CDC On Boot Enabled；core 3.3.11；MQTT 库 2.5.2。

### 烧录一块新板子的完整流程

这是 2026-09-26 至 10-12 实际烧录 6 块板子（Node 1、2、泵 1、泵 2、Node 6、Node 7）总结出来的顺序。所有命令在 Jetson 终端、仓库根目录运行。**Claude 不直接操作硬件**：读 MAC、备份、烧录都由用户执行，Claude 核对输出后再给下一步。

**准备（Claude 做，不需要板子）**

1. 建节点文件夹：README / HARDWARE / WIRING / COMMUNICATION / PROGRESS、`script/<SKETCH>/`、`tests/`，固件里 `NODE_MAC` 先写全零（全零时固件什么都不做）。
2. 网关加节点：`server.py` 的 `NODES`/`SENSORS`、`mqtt_receiver.py`、`prepare_mqtt.py`（需要命令的节点加进 `COMMAND_NODES`）、`configure_node1.py`/`build_node1.py`、`export_raw.py`、两个监控页面板。跑测试。
3. `python3 lab_scale/jetson_web/build_node1.py --node N --check`（空凭据编译检查，**这个产物不能烧录**）。
4. `python3 lab_scale/jetson_web/prepare_mqtt.py --host 192.168.88.249`：补新节点的 broker 账号和 ACL，已有账号密码不变（它们已经烧在各节点里）。
5. `python3 lab_scale/jetson_web/configure_node1.py --node N --wifi-from-node1`：生成本地 `arduino_secrets.h`（Git 忽略，密码不显示）。

**第 1 步：读 MAC（用户）**

```bash
ls -l /dev/serial/by-id/
.codex-build/arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool --chip esp32s3 --port /dev/ttyACM0 flash-id
```

- 新板子跑的是出厂演示程序，设备名是 `Espressif_Device_123456`（USB ID `303a:4001`），esptool 会报 `No serial data received`。**先手动进下载模式：按住 BOOT，按一下 RST，松开 RST，再松开 BOOT**；成功后设备名变成 `…USB_JTAG_serial_debug_unit_<MAC>`。
- 核对：ESP32-S3、16 MB flash、MAC 与已有节点都不同（Node 1 `44:B1:76:CE:D1:A8` 与 Node 6 `44:B1:76:CE:D8:6C` 只差后两段，要逐位看）。
- esptool 结束时会让板子复位回出厂程序，**下一步之前要再按一次 BOOT + RST**。
- 泵 1 那块板子当时插的是板上的 COM/UART 口（CH343 芯片），esptool 能自动进下载模式，不用按键。

**第 2 步：回读整片 flash 备份（用户，约 8 分钟）**

```bash
PORT=/dev/ttyACM0
mkdir -p .codex-build/nodeN-backup && cd .codex-build/nodeN-backup
for i in $(seq 0 15); do ../arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool --chip esp32s3 --port $PORT --no-stub read-flash $((i*0x100000)) 0x100000 part$i.bin || break; done
ls part*.bin | wc -l                 # 必须是 16，少了说明中途失败，不要继续
```

```bash
# 只运行一次，而且终端必须还在 nodeN-backup 目录里
STAMP=$(date -u +%Y%m%dT%H%M%SZ); cat $(for i in $(seq 0 15); do echo part$i.bin; done) > nodeN-flash-before-$STAMP.bin
sha256sum nodeN-flash-before-$STAMP.bin | tee nodeN-flash-before-$STAMP.bin.sha256 && rm part*.bin; cd ~/Documents/GitHub/hardware_record_tank
```

- 用 `--no-stub` 按 1 MB 分块读：stub 模式在 0x6A000 处会稳定中断（Node 1 时发现）。
- 泵 2 时这段被运行了两次，第二次在仓库根目录报 `No such file`，其实第一次已经成功；Claude 用 `sha256sum -c` 核对了备份，并删掉了误生成的空 `.sha256`。
- 泵 1、泵 2、Node 6 的出厂镜像 sha256 都是 `d73b6dd5…`：同一批出厂演示程序，flash 里没有每块板自己的数据。

**第 3 步：填 MAC，真实编译（Claude）**

把 MAC 写进 `.ino` 的 `NODE_MAC`，运行 `python3 lab_scale/jetson_web/build_node1.py --node N`，记录大小和 `.bin` 的 sha256。

**第 4 步：重启网关两个服务（用户，必须在烧录之前）**

```bash
cd ~/Documents/GitHub/hardware_record_tank/lab_scale/jetson_web
kill "$(cat data/mqtt.pid)" "$(cat data/server.pid)"
nohup python3 -u run_mqtt.py > data/mqtt.log 2>&1 & echo $! > data/mqtt.pid
set -a; . ./.env; set +a
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 --pump-control > data/server.log 2>&1 & echo $! > data/server.pid
cd ~/Documents/GitHub/hardware_record_tank
```

broker 只在启动时读账号：不重启，新节点连上 Wi-Fi 也连不上 MQTT，一条数据都进不来（Node 7 烧完后就是这样）。接收器也要重启才订阅新节点、认识新参数。

**第 5 步：烧录（用户）**

先按 BOOT + RST，`ls -l /dev/serial/by-id/` 确认设备名里的 MAC 就是第 1 步那块，然后：

```bash
.codex-build/tools/arduino-cli --config-file .codex-build/arduino-cli.yaml upload -p /dev/ttyACM0 --fqbn 'esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc' --input-dir .codex-build/nodeN-configured/output
```

**烧完单按一次 RST（不按 BOOT）**。手动进的下载模式，烧录后的自动复位不一定能退出，程序不会运行，USB 上也没有任何输出（泵 2 时遇到，按 RST 后立即启动）。

**第 6 步：核对（Claude）**

- 数据库里出现 `event=BOOT`（MAC 检查通过）、Wi-Fi IP、MQTT online，无 `mqtt_rejected`，传感器 / 执行器有正常回复。
- Jetson ARP 里 IP 对应的 MAC 与板子一致；把 IP 和 MAC 写进 `server.py` 的 `NODES` 和各 README。
- 在路由器上给这个 MAC 做静态租约（WebFig：IP → DHCP Server → Leases → Make Static）。
- 换成独立 USB 电源适配器后再核对一次重新上线（程序和配置都在板子里，不需要 Jetson）。

**回退**：`esptool --chip esp32s3 --port $PORT write-flash 0 .codex-build/nodeN-backup/nodeN-flash-before-*.bin`。

USB Serial 115200 也输出同样的日志行；拔掉 USB 不影响 MQTT 发送，但板子需要其他 5 V 供电。

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
