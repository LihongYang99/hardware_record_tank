# Node-6 — 调试进度

## 2026-09-29：建立节点，固件与网关已准备，尚未烧录

- 用户：部署 Node 6，DFRobot 浊度传感器（和 Node-1 一样是 DFRobot），本节点只有这一个传感器；接线完成，GPIO17 → 转换器 RXD、GPIO18 → 转换器 TXD；ESP32 已接 Jetson。要求像其他节点一样实时监测并接入网页。记录为 DECISION 050。
- 型号：用户未说明，按 Phase-1 预选的 SEN0710 编写；**待用户核对实物标签**。重新读取官方 Modbus 协议页（2026-09-29）：地址 1、4800 8N1、功能码 03、寄存器 0 浊度 uint16 ÷10、寄存器 1 温度 int16 ÷10；示例 `01 03 00 00 00 02 C4 0B` → `01 03 04 0D 2E 00 DB D8 CD` = 337.4 NTU / 21.9 °C。
- 固件 `script/TURB_MQTT/`：`Protocol.h`、`BenchChannel.h` 与 Node-1 逐字节相同，`Telemetry.h` 与 Node-2 逐字节相同；新写 `TURB_MQTT.ino`（一路通道，只读，`NODE_MAC` 暂为全零 = 不轮询）。
- 主机测试（tests/protocol_test.cpp，ASan/UBSan）通过：请求 CRC、官方示例帧解码、CRC 错误、超时。
- 编译检查 `build_node1.py --node 6 --check` 通过：883,139 B（67%），静态 RAM 49,220 B。
- 网关：`server.py`（NODES、传感器 `TURB_SEN0710`）、`mqtt_receiver.py`、`prepare_mqtt.py`、`configure_node1.py` / `build_node1.py`（`--node 6`）、中英文监控页"06 / TURBIDITY"面板。网关测试 19 项通过（新增浊度入库、错误不写零、防冒充）。
- `prepare_mqtt.py` 已运行：新增 `shrimp-node06`，原有账号密码不变（核对 Node 1、泵 1、泵 2 已烧录的密码一致）。`configure_node1.py --node 6 --wifi-from-node1` 已生成 `arduino_secrets.h`（0600，Git 忽略）。
- Jetson 上的串口：`usb-Espressif_Systems_Espressif_Device_123456-if00 → /dev/ttyACM0`（原生 USB 口，出厂演示程序；要按 BOOT + RST 才能读）。

- 用户确认实物型号为 **SEN0710**，与固件按的协议一致。

## 2026-09-29 19:14 EDT：读到 MAC，真实编译通过

- 用户按 BOOT + RST 后 `esptool flash-id`：设备 `usb-Espressif_USB_JTAG_serial_debug_unit_44:B1:76:CE:D8:6C-if00 → /dev/ttyACM0`；ESP32-S3 (QFN56) rev v0.2，内置 PSRAM 8 MB，flash 16 MB（厂商 68 / 器件 4018，quad，3.3 V），**MAC 44:b1:76:ce:d8:6c**。与 Node 1（…CE:D1:A8）、Node 2、泵 1、泵 2 都不同。
- MAC 写入 `NODE_MAC`；`build_node1.py --node 6` 真实编译：901,067 B（68%），sha256 `33286567…df379b`。
- esptool 结束时已硬复位，备份和烧录前要再按 BOOT + RST。

## 2026-09-29 19:36 EDT：备份、烧录完成，通信正常，读数停在量程上限

- 备份：`.codex-build/node6-backup/node6-flash-before-20260929T233346Z.bin`，16,777,216 B，`sha256sum -c` 通过；sha256 `d73b6dd5…`，与泵 1、泵 2 的出厂镜像相同。
- 19:33:57 EDT 用户重启 `run_mqtt.py` 和 `server.py`；接收器订阅 shrimp-node06；中英文监控页出现"06 / TURBIDITY"面板。
- 23:36:01Z 首条记录：MQTT online，Wi-Fi `IP=192.168.88.246`（Jetson ARP 同一 MAC），无 `mqtt_rejected`、无序号问题、无通信错误。
- 读数：前 17 次全部 `raw=010304271000FBB0C1` → **`turbidity_NTU=1000.0`**（0x2710，正好是资料量程上限），`temperature_C` 25.1–25.2。固件按规则标 `QC=UNVALIDATED`（≤1000 视为在量程内）。
- 判断：浊度固定在满量程，说明读数饱和，**不代表真实水体浊度**。最可能是探头在空气中或窗口被遮挡（光学探头离开水面常见满量程；NOT VERIFIED，待用户告知探头位置）。待用户把探头完全浸入清水后复查。
- `server.py` 的 node06 写入 IP 与 MAC（网页"MAC 已核对"需重启 `server.py` 生效）。

## 待记录

- 探头浸入清水后的读数。
- 首批真实读数与探头当时所处液体。
- 12 V 是否与其他探头共用适配器。
