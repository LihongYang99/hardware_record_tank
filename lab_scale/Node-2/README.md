# Node-2 — Atlas EC / salinity + pH

## 身份与 IP

- 固件标识：`shrimp-node02`；同款 ESP32-S3 N16R8。
- 局域网 IP：**192.168.88.251**，用户于 2026-09-22 确认。DHCP 地址，未在代码中固定。
- 两条独立 TTL UART，不是 RS485，也不需要 Modbus 地址。

## 当前状态（2026-09-27）

- 板上程序：[script/Atlas_EC_pH_MQTT/](script/Atlas_EC_pH_MQTT/)（`firmware=node02-mqtt-0.1`），经实验室 2.4 GHz Wi-Fi → MQTT 发到 Jetson；IP 192.168.88.251（实测），MAC `44:B1:76:CC:D4:84`。
- 当前通过 USB 接在 Jetson 上（供电 + 串口）。
- pH：正常读取并进入 Jetson 数据库和网页，QC=`COMPENSATION_MISSING`，未校准。
- EC：掉线已重新接好，通信恢复；但读数仍为 0.000，QC=`CONFIGURATION_MISMATCH`（K=1.000 与 K10 探头不符），K/校准待用户确认，见 [PROGRESS.md](PROGRESS.md)。
- 容量与限制条件见 [script/Atlas_EC_pH_MQTT/README.md](script/Atlas_EC_pH_MQTT/README.md#容量与限制条件)。

## 文件导航

- [HARDWARE.md](HARDWARE.md)：传感器型号与硬件。
- [WIRING.md](WIRING.md)：接线与供电边界。
- [COMMUNICATION.md](COMMUNICATION.md)：通信参数与脚本行为。
- [PROGRESS.md](PROGRESS.md)：调试进度、原始日志片段与待办。
- [script/](script/)：Arduino 程序；保留同名 sketch 子目录及全部头文件。
- [tests/](tests/)：主机测试。
