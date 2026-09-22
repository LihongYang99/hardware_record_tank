# Node-2 — Atlas EC / salinity + pH

## 身份与 IP

- 固件标识：`shrimp-node02`；同款 ESP32-S3 N16R8。
- 局域网 IP：**192.168.88.251**，用户于 2026-09-22 确认。DHCP 地址，未在代码中固定。
- 两条独立 TTL UART，不是 RS485，也不需要 Modbus 地址。

## 文件导航

- [HARDWARE.md](HARDWARE.md)：传感器型号与硬件。
- [WIRING.md](WIRING.md)：接线与供电边界。
- [COMMUNICATION.md](COMMUNICATION.md)：通信参数与脚本行为。
- [PROGRESS.md](PROGRESS.md)：调试进度、原始日志片段与待办。
- [script/](script/)：Arduino 程序；保留同名 sketch 子目录及全部头文件。
- [tests/](tests/)：主机测试。
