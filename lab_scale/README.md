# lab_scale — 实验室台架

整理日期：2026-09-22；**2026-09-27 更新**：两个节点改为 MQTT 固件，与相机一起接入 Jetson 临时网页（见 [jetson_web](jetson_web/README.md)）。

## 1. 节点与网络

| 文件夹 | 固件 node_id / hostname | 设备 | IP（2026-09-27 实测） | MAC |
|---|---|---|---|---|
| [Node-1](Node-1/README.md) | shrimp-node01 | SEN0681 DO、SEN0709 ORP | 192.168.88.252 | 44:B1:76:CE:D1:A8 |
| [Node-2](Node-2/README.md) | shrimp-node02 | Atlas EC K10、Industrial pH No Temp，分别经 EZO/ISCCB-2 | 192.168.88.251 | 44:B1:76:CC:D4:84 |
| [camera_node](camera_node/README.md) | ONVIF name `NVT` | 水下 IP 相机（有线接路由器） | 192.168.1.88 | 00:12:34:C6:67:04 |
| [jetson_web](jetson_web/README.md) | Jetson Orin Nano（临时网关） | MQTT broker、数据库、网页 | 有线 192.168.88.249 + 临时 192.168.1.200 | — |

路由器截图：MikroTik hAP ax3，LAN 192.168.88.1/24。两节点通过 Wi-Fi，相机通过有线 PoE 路径；用户已提供 TP-Link/Omada POE150S 注入器链接，实物版本待核对。Barlus 304 相机商品标明淡水用途，不批准目标盐度下长期部署；详见 camera_node/HARDWARE.md。没有上游互联网时局域网采集和网页仍可工作；但目前没有 UTC 来源。
未配置固定地址；不要仅凭旧 IP 判断设备身份，也不要把摄像机 IP 猜成空闲地址。

## 2. 已完成与边界

- 两块板均由用户确认为 ESP32-S3 N16R8。不是对第三方板稳压器、额定负载的认证。
- Node-1：DO 和 ORP 都曾成功返回；ORP 曾超时，交换/重接转换器后用户报告恢复，根因未隔离。
- Node-2：两块 Atlas 模块身份查询及测量请求成功。当前 EC 查询 K=1，而探头为 K10；两模块回复 `?CAL,0`；温度补偿设定 25°C 不是实测温度。
- 节点读取周期都是 4000 ms。两路请求共用同一节点的调度轮次，但不是硬件同时触发；两个 ESP32 之间也尚未同步。
- 2026-09-27：两节点经 Wi-Fi → MQTT 实时发到 Jetson，落库后才确认（ACK）；相机视频经 RTSP 进入同一网页。中文页 `http://192.168.88.249:8080`，英文页 `/en`。
- 已实测：Jetson 接收端中断 25 s 后补发无缺口；节点换电源重启后自动恢复上传。
- 仍未完成：UTC 同步、断电持久缓存（RAM 队列 64 条：Node 1 约 80 s、Node 2 约 27 s）、路由器/Wi-Fi 断开测试、长时间运行、校准、Raspberry Pi 正式网关。
- Node 1 由 USB 充电头供电；Node 2 目前经 USB 接在 Jetson 上。

台架节点分配与 SPEC 的正式 MID/BOTTOM 编号分开，N16R8 与首选 N8R8 的差异在此记录，不修改正式部署设计。
台架曾使用 12 V / 5 A 电源且用户暂未安装保险丝；这是未验收现状，不是安全批准。正式部署必须遵守 SPEC 保护要求。

## 3. 编译与烧录

当前板上程序是 MQTT 版本：Node-1 `Node-1/script/DO_ORP_MQTT/`，Node-2 `Node-2/script/Atlas_EC_pH_MQTT/`。旧版 `DO_ORP_WiFi/`、`Atlas_EC_pH_UART/`（仅 USB 串口）保留作回退。

1. 保留整个 sketch 文件夹，所有 `.h` 都参与同一次编译，不单独上传。
2. 本地配置（仓库根目录）：`python3 lab_scale/jetson_web/configure_node1.py --node 1`（或 `--node 2 --wifi-from-node1`）生成 `arduino_secrets.h`。Wi-Fi 必须是实验室路由器的 **2.4 GHz** 网络。真实密码文件禁止提交。
3. 编译：`python3 lab_scale/jetson_web/build_node1.py --node 1|2`（只编译不烧录）。板设置：ESP32S3 Dev Module；16 MB Flash；QIO；OPI PSRAM；Hardware CDC and JTAG；USB CDC On Boot Enabled；core 3.3.11；MQTT 库 2.5.2。
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
```

测试覆盖协议解析/模拟状态机，不代表物理供电、盐水兼容性、校准准确性或长期稳定性已通过。

## 7. 下一阶段

- Node 2：确认 EC 探头 K 值（K10）并校准 EC、pH，加入样品温度补偿。
- 离线局域网 UTC 来源（节点与相机都需要）。
- 断网缓冲：评估 PSRAM / LittleFS / SD 卡，以及发送能力（每节点约 4–10 条/s）。
- 相机录像策略、改相机默认密码。
- 把 broker、接收器和网页迁到 Raspberry Pi（SPEC 正式架构），加开机自启和磁盘管理。

相机盐水部署限制见 camera_node/HARDWARE.md。正式部署资料保留在 [tank_scale](../tank_scale/README.md)。
