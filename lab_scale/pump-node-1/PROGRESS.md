# pump-node-1 — 调试进度

## 2026-09-27：建立节点，固件与网页已准备，尚未烧录

- 用户已购买 Atlas EZO-PMP，决定：命名 pump-node-1（总 Node 4）、单独一块 ESP32、UART 通信、网页显示泵是否在工作。记录为 DECISION 048，SPEC §5/§31 同步更新。
- 已核对数据手册（2026-09-27 下载）：UART 出厂默认 9600 8N1；五根线色；`D,?` 运行位；INT 输送时为高；可空转；连续模式 20 天自动复位。
- 新固件 `script/PMP_MQTT/`：`Telemetry.h`、`BenchLog.h` 从 Node-2 逐字节复制；`PumpChannel.h`、`PumpParse.h` 新写。
- 主机测试 `tests/test.cpp` 通过（g++，AddressSanitizer + UBSan，无编译警告）：解析、QC、身份、复位后重发设定、`*TOOFAST` 被拒、超时不写零、仅监测模式、命令白名单。
- 编译检查（ESP32 core 3.3.11，N16R8 配置）：
  - `build_node1.py --node 4 --check`（空凭据、全零 MAC）通过，但只有 482,632 B：全零 MAC 让编译器判定"永远不会运行"，把 Wi-Fi/MQTT/泵代码优化掉了，不代表完整程序。
  - 草稿副本填入虚拟 MAC 后完整编译：**912,103 B / 1,310,720 B（69%）**，静态 RAM 49,476 B（15%），与 Node-2 相当。该产物不烧录。
- Jetson 端：`prepare_mqtt.py`、`mqtt_receiver.py`、`server.py`、`configure_node1.py`、`build_node1.py` 增加 node04；中英文网页新增"04 / 旁路泵"面板；Python 测试 16 项全部通过（新增泵入库、泵主题路由/防冒充、ACL 隔离）。
- **尚未完成**：实物接线核对、读取 ESP32 MAC、flash 回读备份、生成 broker 账号、烧录、重启 Jetson 服务、接 12 V 实测。

## 2026-09-27 傍晚：配置完成，等待读取 MAC

- 用户确认 80 mL/min 足够。
- 用户报告"灯红绿蓝交替闪烁"。数据手册的泵灯定义：UART 模式绿 = 待机、青 = 正在读数、紫 = 改波特率、红 = 命令不识别、白闪 = Find；I2C 模式待机为蓝。"红绿蓝交替"不是手册里的单一状态，尚未确认看到的是泵控制板的灯还是 ESP32 板载 RGB 灯。
- Jetson 上只有一个串口设备：`/dev/serial/by-id/usb-1a86_USB_Single_Serial_5C93111989-if00 → /dev/ttyACM0`（CH343 USB 转串口，即开发板的 COM/UART 口，不是 ESP32-S3 原生 USB 口）。是哪块板子要靠 MAC 确认。
- `prepare_mqtt.py --host 192.168.88.249` 已运行：新增 `shrimp-node04` 账号和 ACL（6 行），已有三个账号的密码哈希前后一致。
- `configure_node1.py --node 4 --wifi-from-node1` 已生成 `arduino_secrets.h`（0600，Git 忽略）。
- 本次会话中 Claude 运行 esptool 读板子被权限系统拒绝，读 MAC、备份、烧录需用户在 Jetson 终端执行或授权。

## 2026-09-27 16:44 EDT：确认板子身份，真实配置编译通过

- 用户在 Jetson 终端运行 `esptool --chip esp32s3 --port /dev/ttyACM0 flash-id`：ESP32-S3 (QFN56) rev v0.2，内置 PSRAM 8 MB (AP_3v3)，40 MHz 晶振，flash 16 MB（c8/4018，quad），**MAC 7c:4f:ad:b5:33:38**。与 Node 1（44:B1:76:CE:D1:A8）、Node 2（44:B1:76:CC:D4:84）都不同，确认是泵节点板。
- 用户在 16:42 EDT 重新启动了 Jetson 服务，Node 1/2 数据恢复。服务在新增 node04 账号之后启动，已能接收泵节点。
- MAC 写入 `NODE_MAC`；`server.py` 的 node04 MAC 同步（IP 仍待记录）。
- `build_node1.py --node 4` 真实配置编译通过：912,183 B（69%），静态 RAM 49,476 B（15%）。`PMP_MQTT.ino.bin` sha256 `e8e4c94bc7099ad5a176568b3f3b317bf9a53163f68655477adbb51865a0d907`。
- 下一步：用户备份 flash、烧录。

## 2026-09-27 16:54 EDT：已烧录，联网正常，泵 UART 无回应

- 用户回读备份：`.codex-build/node4-backup/node4-flash-before-pump-20260927T204921Z.bin`，16,777,216 B，sha256 `d73b6dd5a15e469a30629798664fb6e9e5c0ee30ef2679d75858d97a72b6fb15`。
- 用户经 `/dev/ttyACM0`（COM 口）烧录 `node04-pump-mqtt-0.1`。首条记录 20:54:24Z：`event=BOOT`（MAC 检查通过），Wi-Fi `IP=192.168.88.248`，MQTT `online`，无 `mqtt_rejected`。
- **泵无应答**：`*OK,1` → `REPLY_TIMEOUT`，每约 19 s 重试同样超时。开机 72 ms 收到一个 `raw_hex=00` 的残缺字节，此后 C,0 静默期间也没有任何 RX；出厂连续输出（每秒一次）也未出现。说明 GPIO18 没有收到泵的 TX。
- 待查：白/绿（RX/TX）是否接反、红线是否在 3V3、黑线是否共地、泵灯颜色（蓝 = I2C 模式，灭 = 没电）。
- `usb_lost` 持续增加：板子插在 COM 口，原生 USB 口无主机读取，属预期。
- 20:57Z 用户检查接线后重新插 USB（boot `726b4dfb09318437`）：症状不变，仍然只有开机时一个 `00` 字节，此后无任何 RX。泵灯颜色和接线检查结果尚未告知。
- 用户报告：泵的灯不亮。与"UART 完全无输入"一致，最可能是泵控制板没有 VCC（泵端插头未插紧、红线不在 3V3、黑线未共地）。烧录前看到的"红绿蓝交替闪烁"很可能是新 ESP32 出厂演示程序的板载 RGB 灯，烧录后该灯停止。待用万用表确认泵端 3.3 V。
- 数据手册"Manual switching to UART"（p.76）：断电 → 拆下 TX、RX → TX 接 INT → 确认 RX 悬空 → 上电 → 等灯由蓝变绿 → 断电 → 恢复所有接线。

## 2026-09-27 17:00 EDT：电源接对后通信成功

- 用户发现泵控制板电源接错（具体接法未记录；当时泵灯不亮，说明控制板未上电），改正后插回。
- boot `62f68654e8e0a6f6`：收到 `*RS`、`*RE` → 固件重新初始化 → 全部查询通过，`event=READY`。原文见 [SAMPLE_LOG.md](SAMPLE_LOG.md)。
- 泵信息：`?I,PMP,1.06`；`?STATUS,B,3.28`（上次重启 = 欠压，VCC 3.28 V）；`?CAL,0`；`?DSTART,0.00`；**`?MAXRATE,54.66`**。
- `DC,80.00,*` → `*UV,PUMPPWR,0.00` + `*ER`（12 V 未接，泵拒绝启动），固件记 `CONTROL_REJECTED`，结果行 `pump_on=0 int_pin=0 motor_V=0.00 QC=NOT_RUNNING_AS_COMMANDED`，INT 与控制器一致。
- **发现：DC 模式最大 54.66 mL/min，低于设定的 80 mL/min。** 接 12 V 后 `DC,80` 预计会被 `*TOOFAST` 拒绝，泵不会转。需要用户决定流量（见下）。

## 2026-09-27 17:30 EDT：用户决定自己控制开关和流速，先校准

- 用户选择：自己控制泵的开关和流速，先做校准（替代"固定流量"方案）。
- 固件 0.2（`node04-pump-mqtt-0.2`）：MQTT `cmd` 主题的操作命令（白名单、编号去重、一次一条、复位时取消）；设定存 NVS，默认 0 = 不转；READY 行增加 `max_rate_reply`。主机测试通过（ASan/UBSan，无警告）。编译 916,835 B（69%），`PMP_MQTT.ino.bin` sha256 `db70a2df736379d9745702adb8b4f4bf10d39a1073bec68e6a7bb5eb98e20346`。待烧录。
- Jetson：`pump_ctl.py` 操作工具；`prepare_mqtt.py` 新增 `pump-operator` 账号（只能写 `shrimp/lab/shrimp-node04/cmd`），node04 可读 `cmd`；已在运行中的 `data/mqtt/` 生成（已有 5 个账号中原 4 个密码哈希不变，ACL 多 3 行），运行中的 broker 需 `kill -HUP` 才读取。网页新增"设定流量"卡片（需重启 server.py）。Python 测试 17 项通过（新增真实 broker 测试：只有 pump-operator 能下发命令）。

## 2026-09-27 19:27 EDT：固件 0.2 已烧录；第一次校准被泵拒绝

- 固件 0.2 于 21:18:57Z 开机：`event=BOOT target_mL_min=0.00 target_source=DEFAULT`，初始化通过，`READY` 行带 `max_rate_reply=?MAXRATE,54.66`。操作命令通道工作正常（`OPERATOR_ACCEPTED` → `COMMAND` → `DONE`）。
- 23:27:30Z 用户直接运行 `calibrate 9.8`：本次上电后没有任何 `dispense`（`TV` 0.00 mL），12 V 未接（电机 0.11 V）。泵 16 ms 内回 `*ER`，校准未写入（仍 `?CAL,0`）。`operator_event` 如实记录 result=ER；该行备注"气泡已排"与记录不符（本次上电泵未运转过）。
- 推断：`Cal,<mL>` 需要先完成一次输送（数据手册写"按实际输送体积校准"，未明说无输送时拒绝）。
- `pump_ctl.py calibrate` 增加检查：上一条操作必须是结果 OK 的 `dispense`，之后收到 `DISPENSE_DONE`，且中间没有节点/泵重启，否则不发送。校准备注自动附上 `dispensed=<命令>`。测试 17 项通过。
- 开机时第一条 RX 是 `*ER`（2028 ms，发生在启动静默期，是对开机 `C,0` 前残缺字节的回应），随后正式初始化的 `C,0` 得到 `*OK`，无影响。

## 2026-09-27 19:37 EDT：第一次体积校准完成（?CAL,1）

操作序列（raw_log / operator_event，操作人 lihongyang2026）：

- 23:29:34Z `DC,50.00,*` → `*UV,PUMPPWR,0.00` + `*ER`（12 V 未接，拒绝）。
- 23:30:37Z `DC,50.00,*` → `*OK`（12 V 已接），运行约 4 min 52 s 排气泡。
- 23:35:29Z `X` → `*DONE,242.81`（泵按未校准的系数计算的体积，约等于 50 mL/min × 4.87 min）。
- 23:35:56Z `D,10.00` → `*OK`；23:36:02Z `*DONE,10.00`（约 6 s，即接近全速）。
- 23:37:27Z `Cal,8.30` → `*OK`；重新初始化读到 `?CAL,1`（体积校准），`?MAXRATE,54.66` 未变。备注：`10mL量筒 淡水 气泡已排 | dispensed=D,10.00 pre=?CAL,0 post=?CAL,1 max_rate=?MAXRATE,54.66`（备注文字沿用示例，量具与用水待用户确认）。
- 校准后状态：停止，电机 11.97 V。

判断：实测 8.3 mL / 指令 10 mL = 0.83，偏差 17%，远大于手册标称的未校准 ±5%。可能原因：量筒读数（弯月面、管内残留液滴）、软管或进水条件与出厂假设不同。单次测量，**NOT VERIFIED**，需要校准后再输送 10 mL 复核。若系数属实，校准前 `DC,50` 实际约 41.5 mL/min。

待做：复核 `dispense 10`（期望 9.9–10.1 mL）；按时间校准（`dispense 10 --minutes 1` → `calibrate`，期望 `?CAL,3`）并复查 MAXRATE。

## 2026-09-27 19:43 EDT：体积校准生效的时长证据；按时间输送 10 mL 实测 8.3 mL

- 校准后 23:39–23:40Z 连续 4 次 `D,10.00`，23:41:10Z 一次 `D,10.00,1.00`（节点 uptime 计时 60.67 s）。
- 输送时长（节点 uptime，`OPERATOR_DONE` → `*DONE`）：校准前 `D,10` 5.99 s；校准后 6.84 / 7.52 / 6.71 / 7.04 s，平均 7.03 s，为校准前的 1.17 倍，与 10/8.3 = 1.20 接近 → 体积校准已生效（间接证据；4 次的实测体积尚未由用户报告）。
- 用户报告按时间输送实测 8.3 mL（量具：10 mL 量筒，淡水）。按时间校准与体积校准相互独立，尚未做过，所以与校准前的系数一致。用户第一次输入 `calibrate <8.3>`，尖括号被 shell 当成重定向，命令未执行。
- 当前：停止，电机 11.95 V，`TV` 51.45 mL，`?CAL,1`，`?MAXRATE,54.66`。

## 2026-09-27 19:43 EDT：两种校准完成（?CAL,3），恒定流量上限 45.36 mL/min

- 23:43:36Z `Cal,8.30`（对应 `D,10.00,1.00`，备注"10mL量筒 淡水"）→ `*OK`；重新初始化：`?CAL,3`（体积 + 按时间），**`?MAXRATE,45.36`**（校准前 54.66；45.36/54.66 = 0.83，与两次实测比例一致）。
- 23:45:24Z 复核 `D,10.00,1.00`，节点计时 60.8 s 完成；用户报告实测 **9.7 mL**（10 mL 量筒，淡水）：偏差 −3%，在手册未校准 ±5% 内，超出校准后 ±1%。10 mL 量筒读数本身约有 ±0.1–0.2 mL（1–2%）的不确定度，单次测量不能区分是泵还是读数。该读数只记在本文件，数据库 `operator_event` 中该行备注为空。校准后 4 次 `D,10` 的实测体积也待报告。
- 当前：停止，电机 11.97 V，`TV` 10.00 mL（校准后泵的累计体积重新计数）。
- **与 SPEC §29 的关系**：恒定流量上限 45.36 mL/min 低于 SPEC §29 的构想范围 50–150 mL/min（SPEC 注明"需验证"）。未修改 SPEC；已记入 DECISION 048 风险项，待确定流通池和传感器流量需求时再决定（接受约 40–45 mL/min、改用更粗的软管，或不做闭环的全速模式）。

## 2026-09-27 20:00 EDT：网页开关

- 用户要求在网页上控制泵的开关和流速。实现：`server.py --pump-control` 时泵面板显示操作人/流速/密码和"启动 / 改流速""停止"；`POST /api/pump` 只接受 JSON 的 start/stop，密码为 `pump_ctl.py set-web-password` 设置的加盐 PBKDF2 哈希，连续 5 次错误锁 60 s，一次只执行一条，结果为泵的真实回复。校准仍只在终端。无需重新烧录。
- `pump_ctl.py` 重构：终端与网页共用 `execute()`；新增 `WebControl`、`set-web-password`。测试 18 项通过（新增：未开启 403、非 JSON 415、越界/未知动作 400、错密码 401、锁定 429、正确命令只发 `DC,50.00,*` / `X`）。临时网页截图确认表单显示、未设密码时按钮灰掉。
- 23:52Z 用户用终端 `start 40` 开泵（运行中，电机 12.37 V）；随后询问如何停泵。

## 2026-09-27 20:15 EDT：控制改为单独的登录页面

- 用户提出：单独做一个需要账号密码的控制页，监控数据不需要登录。上一版（监控页上的密码开关）尚未启用（用户未设密码、网页未带 `--pump-control`），直接替换。
- 监控页 `/`、`/en` 恢复只读，泵面板只留"泵控制（需要登录）"链接。新控制页 `/control`：个人账号登录（`pump_ctl.py web-user add|remove|list`，加盐 PBKDF2，`data/pump_web_users.json` 0600）；内存会话，HttpOnly + SameSite=Strict cookie，30 分钟无操作过期，删除账号立即失效；同一账号 5 次错误锁 60 s；只允许启动/改流速、停止；显示最近 15 条操作；操作人记为 `web-<账号>`。
- 测试 18 项通过（新测试覆盖：未开启 403、无账号 403、未登录 401、错误密码/不存在账号 401、cookie 属性、JSON/范围/动作校验、登出、删除账号会话失效、锁定 429、伪造 cookie 401）。临时服务截图确认登录前、登录后两种页面。

## 2026-09-27 20:25 EDT：控制页改为多设备"设备控制台"，泵命名为泵 1

- 用户已建控制页账号，并在 20:10 EDT 以 `--pump-control` 重启网页服务；网关核对：泵节点在线、MAC 一致，停止，电机 11.96 V，`TV` 67.97 mL；相机 `LIVE`；Node 1/2 数据实时。
- 发现：`run_mqtt.py`（接收器）自 16:42 EDT 运行，早于 `server.py` 的 SENSORS 加入 `target_mL_min`，所以设定流量没有单独存成测量行（原始行中仍有）。控制页改为从状态行的原始字段读取设定；监控页的"设定流量"卡片需要重启 `run_mqtt.py` 后才有值。
- 用户要求：控制页以后会有多台设备，这台泵叫泵 1；控制页全部中文。实现：`pump_ctl.DEVICES` 设备登记（`pump1` = 泵 1），`POST /api/control {device, action, rate}`，`/api/control/events` 带设备列；控制页按设备生成卡片，操作记录把命令翻译成中文（如"启动 40 mL/min""校准（实测 8.3 mL）"）。监控页面板改为"04 / PUMP 1 · 泵 1"。数据库传感器编号保持 `PUMP_ATLAS_PMP`。
- 测试 18 项通过；临时服务截图确认新控制页（数据为模拟，仅看排版）。需要重启 `server.py` 生效。

- 20:24 EDT：用户问"怎么还是中文"，上一条"控制页改成中文"可能本意是英文。新增英文控制页 `/control/en`（与 `/control` 共用 `control.js`，按页面语言选文字，右上角互相切换；设备登记增加 `name_en` / `description_en`，泵 1 英文为 Pump 1）。英文监控页的链接指向英文控制页。测试 18 项通过，截图确认英文页。

## 2026-09-27 20:30 EDT：两个服务已重启，中英文控制页上线；当天调试过程汇总

- 用户重启了两个服务（`ps` 核对启动时间）：`run_mqtt.py` 20:21:46 EDT，`server.py … --pump-control` 20:27:59 EDT。接收器重启后 `target_mL_min` 从 00:21:49Z 起单独入库（到 00:32Z 已 161 行），监控页"设定流量"卡片有值；英文控制页 `/control/en` 生效。网页重启后内存会话清空，需要重新登录。
- 当前（00:32Z，`pump_ctl.py show`）：停止，设定 0，电机 11.95 V，本次上电累计 73.06 mL，`?CAL,3`，`?MAXRATE,45.36`。
- 20:46 EDT 前：用户把泵 1 的 ESP32 从 Jetson USB 改接独立 USB Type-C 电源适配器（5 V），Jetson 上 `/dev/serial/by-id/` 已无任何串口设备。适配器型号未记录。板子重新上电后设定仍为 0（NVS），不会自己转。当晚计划关闭 Jetson，之后节点数据不接收；烧录或看串口日志时再插回 Jetson。
- 当天从建节点到控制页的全部调试过程按"现象 → 原因 → 处理"汇总在 [README.md](README.md#调试过程2026-09-27摘要)；本文件保留逐条原始记录。网关侧过程见 [jetson_web README](../jetson_web/README.md#2026-09-27-晚泵-1-接入与设备控制页)。

## 待记录（烧录时补）

- 泵上电灯色（绿 = UART）。
- 黑线 GND 与电机 − 是否导通（万用表）。
- 第一批真实日志（届时新建 SAMPLE_LOG.md，原样摘录，不改写）。
