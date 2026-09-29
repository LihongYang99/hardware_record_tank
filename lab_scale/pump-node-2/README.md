# pump-node-2 — 泵 2：第二个旁路泵节点（总 Node 5）

## 身份与 IP

- 固件标识：`shrimp-node05`；台架名称 pump-node-2；网页和控制页叫 **泵 2 / Pump 2**（设备编号 `pump2`）；数据库传感器编号 `PUMP2_ATLAS_PMP`（DECISION 049）。
- 控制器：单独一块 ESP32-S3（esptool 2026-09-29：QFN56 rev v0.2，内置 8 MB PSRAM，16 MB flash），与项目 N16R8 编译配置一致。
- MAC：`7C:4F:AD:B5:1C:D4`（已写入固件 `NODE_MAC`）。IP：`192.168.88.247`（2026-09-29 固件日志与 Jetson ARP 一致，DHCP，未固定）。
- 泵：Atlas Scientific EZO-PMP（用户报告与泵 1 同型号），UART 直连，单独 12 V 电机电源。
- **用途：第二个旁路泵**（用户 2026-09-29 暂定）。SPEC 只规定了一个旁路泵（NODE 04），尚未修改；见 DECISION 049。

## 当前状态（2026-09-29）

- 接线：用户完成，与泵 1 相同（GPIO17 → 白、GPIO18 → 绿），见 [WIRING.md](WIRING.md)。板子插在 Jetson USB 上（`/dev/serial/by-id/usb-Espressif_Systems_Espressif_Device_123456-if00`，ESP32-S3 原生 USB 口）。
- 已完成：固件（与泵 1 共用代码）、编译检查、broker 账号 `shrimp-node05` 与 ACL、本地 Wi-Fi/MQTT 配置、网关和两个监控页的"05 / PUMP 2"面板、控制页的泵 2 卡片。自动测试 18 项通过。
- 2026-09-29 已烧录 `node05-pump-mqtt-0.2`：联网、MQTT 在线、泵初始化通过（泵固件 `?I,PMP,1.06`，`?CAL,0` 未校准，未校准恒定流量上限 `?MAXRATE,54.66`）。当前停止、设定 0；12 V 未接（电机 0.00 V）。
- 2026-09-29 已接 12 V（电机约 12 V）；两种校准完成（`?CAL,3`）：10 mL 指令实测 9.19 mL（体积）、9.08 mL（按时间）。**校准后恒定流量上限 49.63 mL/min**（泵 1 为 45.36）。
- 校准后复核：1 分钟输送 10 mL，实测 9.85 mL（−1.5%）。
- 未完成：流量计、盐水软管兼容性、黑线 GND 与电机负极是否相通。步骤见 [script/PMP_MQTT/README.md](script/PMP_MQTT/README.md)。

## 控制

与泵 1 完全相同，只是终端命令要加 `--device pump2`（不加就是泵 1）：

```bash
cd ~/Documents/GitHub/hardware_record_tank/lab_scale/jetson_web
python3 pump_ctl.py --device pump2 show
python3 pump_ctl.py --device pump2 start 30
python3 pump_ctl.py --device pump2 stop
python3 pump_ctl.py --device pump2 dispense 10
python3 pump_ctl.py --device pump2 --note "10mL量筒 淡水" calibrate 9.6
```

网页：控制页 `http://192.168.88.249:8080/control`（英文 `/control/en`）登录后，泵 1、泵 2 各一张卡片。校准步骤与注意事项见 [pump-node-1 README](../pump-node-1/README.md#控制与校准jetson-终端)。泵 2 的流量上限要在它自己校准后读 `query maxrate`，不能沿用泵 1 的 45.36 mL/min。

## 方法与原理

方法和原理与泵 1 相同（UART 查询/控制、每 4 s 监测、命令白名单、NVS 设定、复位后重发、"运行中"只是控制器报告），见 [pump-node-1 README 方法与原理](../pump-node-1/README.md#方法与原理)。这里只说明两台泵为什么这样分：

- **两块 ESP32、两个节点编号**。一台泵出故障、复位或调试时不影响另一台，也不影响传感器节点（SPEC §39）。
- **代码共用，不复制两份**。四个头文件在两个文件夹里逐字节相同，只有 `PMP_MQTT.ino` 里的节点名、传感器编号、版本号和 MAC 不同。改一处 bug 就复制到另一处并用 `cmp` 核对，不会出现两台泵行为悄悄不一致。
- **传感器编号不同**。网关规定每个传感器编号只属于一个节点，这样泵 2 不能冒充泵 1 写数据（有自动测试）。

## 文件导航

- [HARDWARE.md](HARDWARE.md)：硬件与待读取的板子信息。
- [WIRING.md](WIRING.md)：接线（与泵 1 相同）。
- [COMMUNICATION.md](COMMUNICATION.md)：与泵 1 的差异（节点名、主题、传感器编号）。
- [PROGRESS.md](PROGRESS.md)：调试进度。
- [script/PMP_MQTT/](script/PMP_MQTT/)：Arduino 程序与烧录流程。
- 主机测试：共用 [pump-node-1/tests](../pump-node-1/tests/)（头文件相同）。
