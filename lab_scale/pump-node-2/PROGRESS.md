# pump-node-2 — 调试进度

## 2026-09-29：建立节点，固件与网关已准备，尚未烧录

- 用户：Node 5 与 Node 4 一样是泵，单独一块 ESP32，同样接线（GPIO17 → 白、GPIO18 → 绿），要求照 Node 4 的流程建文件夹、烧录、同步到中英文监控页并可控制。记录为 DECISION 049；泵 2 的用途未定义，SPEC 未改。
- Jetson 上的串口：`/dev/serial/by-id/usb-Espressif_Systems_Espressif_Device_123456-if00 → /dev/ttyACM0`（ESP32-S3 原生 USB 口，出厂程序的序列号 123456）。MAC 待读取。
- 固件：泵 1 的 `PumpChannel.h`、`PMP_MQTT.ino` 中写死的 `shrimp-node04` / `PUMP_ATLAS_PMP` 改为宏 `TELEMETRY_NODE` / `PUMP_SENSOR`，四个头文件复制到本目录，逐字节相同；本目录 `.ino` 只改节点名、传感器编号、版本号，`NODE_MAC` 暂为全零（全零时永远不启动泵）。
- 泵 1 不需要重烧：改宏前后用 `build_node1.py --node 4` 各编一次，改前正好是板上的 `db70a2df…`；改后与之相比只有 `0xb0–0xcf`（ESP-IDF 应用描述里的 ELF 哈希）和镜像末尾校验和不同，其余字节全部相同。同一源码连编两次结果完全一致，所以这个比较有效。
- 编译检查 `build_node1.py --node 5 --check` 通过（486,216 B；全零 MAC 使大部分代码被优化掉，属预期，真实编译约 917 KB）。主机测试（pump-node-1/tests）通过。
- 网关：`server.py`（NODES、SENSORS 增加 `PUMP2_ATLAS_PMP`）、`mqtt_receiver.py`、`prepare_mqtt.py`（COMMAND_NODES 加 node05）、`configure_node1.py`/`build_node1.py`（`--node 5`）、中英文监控页"05 / PUMP 2"面板、`pump_ctl.py`（设备 `pump2`，终端 `--device`）。测试 18 项通过（新增：泵 2 不能写泵 1 的传感器、泵 2 ACL、控制页两台设备、泵 2 命令路由）。
- `prepare_mqtt.py --host 192.168.88.249` 已运行：新增 `shrimp-node05` 账号，原有账号密码不变（核对泵 1 已烧录的密码一致）；`pump-operator` 可写两台泵的 `cmd`。运行中的 broker 需要重启 `run_mqtt.py` 才读取。
- `configure_node1.py --node 5 --wifi-from-node1` 已生成 `arduino_secrets.h`（0600，Git 忽略）。
- **下一步（用户在 Jetson 终端执行）**：读 MAC → 回读 flash 备份 → 填 MAC 编译 → 重启网关服务 → 烧录。

## 2026-09-29 12:49 EDT：读到 MAC，真实编译通过

- 第一次 `flash-id` 失败（`No serial data received`）：板子运行出厂演示程序，原生 USB 口被它占成普通 USB 设备（`303a:4001`，名字 `Espressif_Device_123456`），esptool 无法自动让它进下载模式。用户手动按 BOOT + RST 进入下载模式后，设备变为 `usb-Espressif_USB_JTAG_serial_debug_unit_7C:4F:AD:B5:1C:D4-if00 → /dev/ttyACM0`。
- `esptool flash-id`：ESP32-S3 (QFN56) rev v0.2，内置 PSRAM 8 MB (AP_3v3)，40 MHz 晶振，flash 16 MB（c8/4018，quad，3.3 V），**MAC 7c:4f:ad:b5:1c:d4**，与泵 1（7C:4F:AD:B5:33:38）、Node 1/2 都不同。
- 用户把泵 2 用途暂定为**第二个旁路泵**（DECISION 049 更新，SPEC 未改）；校准稍后做。
- MAC 写入 `NODE_MAC`；`build_node1.py --node 5` 真实编译通过：916,835 B（69%），静态 RAM 49,732 B；sha256 `7aceae6c…758f36`。
- flash-id 结束时 esptool 已硬复位，板子回到出厂程序；备份和烧录前要再按一次 BOOT + RST。

## 2026-09-29 13:53 EDT：备份、烧录完成，通信成功

- 备份：`.codex-build/node5-backup/node5-flash-before-pump-20260929T172303Z.bin`，16,777,216 B，`sha256sum -c` 通过，文件头 `E9`。sha256 `d73b6dd5…6fb15` 与泵 1 烧录前的备份完全相同：两块板出厂装的是同一个演示程序，flash 里没有每块板自己的数据。第二遍在仓库根目录误跑的拼接命令留下一个 0 字节 `.sha256`，已删除。
- 13:26:55 EDT 用户重启 `run_mqtt.py` 和 `server.py`；接收器订阅 shrimp-node05。
- 烧录后没有任何数据，USB 日志也没有输出：手动 BOOT + RST 进的下载模式，烧录后的自动复位没让芯片退出下载模式。用户单独按 RST 后程序启动。
- 17:53:57Z 首条记录：`event=BOOT`（MAC 检查通过），`target_mL_min=0.00 target_source=DEFAULT`；Wi-Fi `IP=192.168.88.247`（Jetson ARP 显示同一 MAC）；MQTT online；无 `mqtt_rejected`。
- 泵初始化（原始回复见 raw_log）：C,0 之前收到出厂连续输出 `0.00`（每秒一次）→ `C,0` → `*OK`；`i` → `?I,PMP,1.06`；`Status` → `?STATUS,P,3.33`（上次重启 = 上电，VCC 3.33 V）；`Cal,?` → `?CAL,0`；`Dstart,?` → `?DSTART,0.00`；`DC,?` → **`?MAXRATE,54.66`**（与泵 1 未校准时相同）；`event=READY`。
- 每 4 s 结果：`pump_on=0 int_pin=0 motor_V=0.00 total_volume_mL=0.00 COMM=OK QC=UNVALIDATED`：停止，12 V 未接。
- `server.py` 的 node05 写入 IP 与 MAC（网页"MAC 已核对"需重启 `server.py` 生效）。

## 2026-09-29 14:15 EDT：接 12 V，体积校准完成（?CAL,1）

操作序列（operator_event / raw_log）：

- 17:51:41Z 网页控制页 `DC,40.00,*` → `NO_REPLY`：当时板子还停在下载模式，程序没运行，命令丢弃（节点离线时不补执行，符合设计）。
- 17:57:39Z 终端 `start 40` → `*UV,PUMPPWR,0.05` + `*ER`（12 V 未接）。设定 40 已存 NVS，固件每约 60 s 重发一次（`control_commands` 递增到 10），均被欠压拒绝，符合设计。
- 18:09:04Z 网页 `X` → `*DONE,30.66`：说明这期间 12 V 已接上，泵已按 40 mL/min 运转过（泵按未校准系数计 30.66 mL）。
- 18:09:14Z `start 40` → OK；18:10:43Z `stop` → `*DONE,59.21`（约 89 s 排气泡）。
- 18:11:15Z `dispense 10` → OK；节点计时 5.86 s 后 `DISPENSE_DONE`（泵 1 校准前为 5.99 s）。
- 用户报告实测 **9.19 mL**（−8.1%，超出手册未校准 ±5%；泵 1 同条件为 8.3 mL）。量具与用水未单独说明，备注写"按泵 1 做法（10 mL 量筒、淡水），待确认"。
- 18:15Z `Cal,9.19` → OK；重新初始化读到 `?CAL,1`，`?MAXRATE,54.66` 不变（体积校准不改恒定流量上限，与泵 1 相同）。
- 当前：停止，电机 11.97 V，`TV` 归零。

下一步：按时间校准（`dispense 10 --minutes 1` → 量 → `calibrate`），期望 `?CAL,3` 并得到校准后的恒定流量上限；再复核一次。

## 2026-09-29 14:30 EDT：两种校准完成（?CAL,3），恒定流量上限 49.63 mL/min

- 18:27:41Z `dispense 10 --minutes 1`（`D,10.00,1.00`）→ OK；节点计时 60.2 s 后 `DISPENSE_DONE`。用户报告实测 **9.08 mL**（−9.2%）。
- 18:3xZ `Cal,9.08` → OK；重新初始化：`?CAL,3`（体积 + 按时间），**`?MAXRATE,49.63`**（校准前 54.66；49.63/54.66 = 0.908，与实测比例一致）。
- 对比泵 1：两种校准实测 8.3 / 8.3 mL，校准后上限 45.36 mL/min。两台同型号泵的出厂误差不同（−17% 与 −8~9%），所以每台必须单独校准。
- 泵 2 的上限 49.63 mL/min 仍略低于 SPEC §29 构想的 50–150 mL/min（与泵 1 同样记入 DECISION 049 风险项）。
- 当前：停止，电机 11.96 V。

## 2026-09-29 14:50 EDT：校准复核 9.85 mL

- 18:48:47Z 复核 `D,10.00,1.00` → OK，节点计时 60.3 s 完成。用户报告实测 **9.85 mL**：偏差 −1.5%，在手册未校准 ±5% 内，略超校准后 ±1%。10 mL 量筒读数本身约 ±0.1–0.2 mL（1–2%），单次测量不能区分泵与读数。泵 1 复核为 9.7 mL（−3%）。
- 该读数只记在本文件，数据库 `operator_event` 中该行备注为空。
- 当前：停止，设定 0，电机 11.95 V，`?CAL,3`，`?MAXRATE,49.63`。泵 2 台架调试完成；未完成项见 README。

## 待记录

- 黑线 GND 与电机 − 是否导通（万用表）。
