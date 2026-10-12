# Node-7 — 调试进度

## 2026-10-12：建立节点，固件与网关控温已准备，尚未烧录

- 用户：新 ESP32 接双路 IoT 交流继电器控制水温，作为 Node 7；水温取 DO 探头与浊度探头温度的平均值；控制页可调设定温度（例 15 °C，低于就启动）；要有一个人为开关，打开时才自动调节。加热器已接 CH1 的 normally OFF 插座。记录为 DECISION 052（这是第一个由水质数据驱动的闭环控制，SPEC §0.2 原写"不是闭环控制"）。
- 继电器型号未记录；查到的同名产品为光耦隔离输入、DC 3–120 V（不确定是同一款，NOT VERIFIED）。
- 固件 `script/HEATER_MQTT/`：`Telemetry.h`、`BenchLog.h` 与 pump-node-1 逐字节相同；新写 `HeaterLogic.h`（主机测试通过：只认 `HEAT,ON`/`HEAT,OFF` 与严格格式、60 s 超时含 millis 回绕）与 `HEATER_MQTT.ino`（GPIO5，开机先断开，`NODE_MAC` 全零 = 不动作）。编译检查 883,663 B（67%）。
- 网关：`heater_ctl.py`（平均水温、回差 0.5 °C、两探头相差 > 3 °C / 过期 / 不合理 / 无数据都断电、开启时每 20 s 重发、每次通断记入 `operator_event`）；`server.py` 新增 `/api/heater`（登录、设定 5–32 °C、没设温度不能开自动）和状态接口的 `heater`；控制页加热器卡片；监控页"07 / HEATER"面板。网关测试 28 项通过。
- `prepare_mqtt.py` 已运行：新增 `shrimp-node07`（可读自己的 `cmd`），`pump-operator` 可写 node07 `cmd`；原有账号密码不变。`configure_node1.py --node 7 --wifi-from-node1` 已生成本地配置。
- Jetson 上的串口：`usb-Espressif_Systems_Espressif_Device_123456-if00`（出厂程序，读 MAC 前要按 BOOT + RST）。

## 待记录

- 继电器与加热器型号、额定值；控制输入电压范围。
- MAC、IP。
- 台灯测试结果（自动开关、断联 60 s 自动断电）。
