# Node-1 — DO + ORP

## 身份与 IP

- 固件标识：`shrimp-node01`；ESP32-S3 N16R8（用户确认的第三方开发板）。
- IP：`192.168.88.252`（2026-09-26 串口日志与 Jetson 实测；MAC `44:B1:76:CE:D1:A8`）。旧文档写的 `.254` 是 Jetson 以前的 Wi-Fi 地址，已更正。
- 台架用途：把两条独立 RS485 测量链路接到同一 ESP32；不是正式部署中的空间位置编号。

## 当前状态（2026-09-26）

- 板上程序：[script/DO_ORP_MQTT/](script/DO_ORP_MQTT/)（`firmware=node01-mqtt-0.1`），通过实验室 2.4 GHz Wi-Fi → MQTT 把整行日志发到 Jetson（192.168.88.249:1883），Jetson 落库后再回 ACK。
- 供电：ESP32 由 USB 充电头 5 V 供电（已离开 Jetson USB）；探头仍由独立 12 V 适配器供电。
- 已实测：数据进入 Jetson SQLite 与网页；Jetson 接收端中断 25 s 后补发、无缺口；换电源重启后约 18 s 自动恢复上传。
- 容量与限制条件见 [script/DO_ORP_MQTT/README.md](script/DO_ORP_MQTT/README.md#容量与限制条件)。
- 未完成：UTC 同步、断电持久缓存、路由器/Wi-Fi 中断测试、长时间运行、探头校准验证。

## 文件导航

- [HARDWARE.md](HARDWARE.md)：传感器型号与硬件。
- [WIRING.md](WIRING.md)：接线与供电边界。
- [COMMUNICATION.md](COMMUNICATION.md)：通信参数与脚本行为。
- [PROGRESS.md](PROGRESS.md)：调试进度、原始日志片段与待办。
- [script/](script/)：Arduino 程序；保留同名 sketch 子目录及全部头文件。
- [tests/](tests/)：主机测试。
