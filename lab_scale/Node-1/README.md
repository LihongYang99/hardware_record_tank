# Node-1 — DO + ORP

## 身份与 IP

- 固件标识：`shrimp-node01`；ESP32-S3 N16R8（用户确认的第三方开发板）。
- IP：`192.168.88.254` 
- 台架用途：把两条独立 RS485 测量链路接到同一 ESP32；不是正式部署中的空间位置编号。

## 文件导航

- [HARDWARE.md](HARDWARE.md)：传感器型号与硬件。
- [WIRING.md](WIRING.md)：接线与供电边界。
- [COMMUNICATION.md](COMMUNICATION.md)：通信参数与脚本行为。
- [PROGRESS.md](PROGRESS.md)：调试进度、原始日志片段与待办。
- [script/](script/)：Arduino 程序；保留同名 sketch 子目录及全部头文件。
- [tests/](tests/)：主机测试。
