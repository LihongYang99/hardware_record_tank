# lab_scale — 实验室台架

整理日期：2026-09-22。依据：用户提供的实物描述、串口日志、路由器截图，以及现有 `output/bench` 程序；不是本次重新测量结果。

## 1. 节点与网络

| 文件夹 | 固件 node_id / hostname | 设备 | IP 记录 |
|---|---|---|---|
| [Node-1](Node-1/README.md) | shrimp-node01 | SEN0681 DO、SEN0709 ORP | 192.168.88.252；历史还出现 .254，需复核 |
| [Node-2](Node-2/README.md) | shrimp-node02 | Atlas EC K10、Industrial pH No Temp，分别经 EZO/ISCCB-2 | 192.168.88.251；用户本次确认 |
| [camera_node](camera_node/README.md) | NOT VERIFIED；目录名不是设备 hostname | 水下 PoE 相机 | NOT VERIFIED |

路由器截图：MikroTik hAP ax3，LAN 192.168.88.1/24。两节点通过 Wi-Fi，相机通过有线 PoE 路径（具体注入器/交换机型号未确认）。没有上游互联网时仍可进行局域网通信，但当前固件没有 UTC 来源或测量网络接口。
未配置固定地址；不要仅凭旧 IP 判断设备身份，也不要把摄像机 IP 猜成空闲地址。

## 2. 已完成与边界

- 两块板均由用户确认为 ESP32-S3 N16R8。不是对第三方板稳压器、额定负载的认证。
- Node-1：DO 和 ORP 都曾成功返回；ORP 曾超时，交换/重接转换器后用户报告恢复，根因未隔离。
- Node-2：两块 Atlas 模块身份查询及测量请求成功。当前 EC 查询 K=1，而探头为 K10；两模块回复 `?CAL,0`；温度补偿设定 25°C 不是实测温度。
- 节点读取周期都是 4000 ms。两路请求共用同一节点的调度轮次，但不是硬件同时触发；两个 ESP32 之间也尚未同步。
- Wi-Fi 已连接；网络传输测量值、MQTT、UTC、数据库、网页仪表盘、视频流接入均尚未完成。
- USB 仅输出，不自动保存磁盘文件。Node-2 有有限 RAM 日志队列，溢出会计数丢失；断电丢失 RAM。Node-1 串口输出仍可能阻塞。

台架节点分配与 SPEC 的正式 MID/BOTTOM 编号分开，N16R8 与首选 N8R8 的差异在此记录，不修改正式部署设计。
台架曾使用 12 V / 5 A 电源且用户暂未安装保险丝；这是未验收现状，不是安全批准。正式部署必须遵守 SPEC 保护要求。

## 3. Arduino IDE 使用

1. Node-1 打开 `Node-1/script/DO_ORP_WiFi/DO_ORP_WiFi.ino`；Node-2 打开 `Node-2/script/Atlas_EC_pH_UART/Atlas_EC_pH_UART.ino`。
2. 保留各自整个 sketch 文件夹，所有 `.h` 都参与同一次编译，不单独上传。
3. 将同目录 `arduino_secrets.example.h` 复制为 `arduino_secrets.h` 并本地填写。示例文件没有真实 SSID/密码。
4. 沿用先前测试设置：ESP32S3 Dev Module；16 MB Flash；QIO；OPI PSRAM；Hardware CDC and JTAG；USB CDC On Boot Enabled。原测试 core 为 3.3.11。
5. 选择实际连接的板子和端口上传；Mac `/dev/cu.usbmodem...` 会变化，不写死。Serial Monitor 为 115200。
6. 上传后板子可独立运行，但仍需供电；当前若拔掉电脑，不能因此期待在网页看到数据。

没有新增网络、校准或远程控制功能；这里整理的是已存在的程序。板上实际二进制与本次整理快照是否完全相同，没有做回读比对。

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

先解决 EC K10 配置、校准、样品温度补偿和接线可靠性；然后实现离线局域网 UTC 来源、MQTT、Raspberry Pi 原始记录与仪表盘、掉线恢复。
相机独立确认型号/IP/视频协议。正式部署资料保留在 [tank_scale](../tank_scale/README.md)。
