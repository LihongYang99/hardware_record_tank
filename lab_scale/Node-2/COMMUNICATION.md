# Node-2 — 通信与脚本说明

入口：[Atlas_EC_pH_UART.ino](script/Atlas_EC_pH_UART/Atlas_EC_pH_UART.ino)。

| 文件 | 用途 |
|---|---|
| Atlas_EC_pH_UART.ino | node02、GPIO、Wi-Fi、4000 ms 调度、健康日志 |
| AtlasChannel.h | 两路独立初始化、请求/回复与超时状态机 |
| AtlasParse.h | ASCII 数值与模块身份解析 |
| BenchLog.h | 有限 RAM USB 日志队列；丢失计数 |
| arduino_secrets.example.h | 空 Wi-Fi 模板；本地复制为 arduino_secrets.h |

启动停止连续输出 `C,0`，启用确认 `*OK,1`，查询 `i`、`T,?`、`Cal,?`，EC 另查 `K,?`。
EC 输出设置为 `O,EC,1`、`O,TDS,0`、`O,S,1`、`O,SG,0`，随后每 4 s 发送 `R`。
**程序会写输出/响应配置，不是完全只读**；不会写校准、K、温度补偿或切换 UART/I2C。
这些是现有代码行为；协议参考 [EZO-EC 手册](https://files.atlas-scientific.com/EC_EZO_Datasheet.pdf)、[EZO-pH 手册](https://files.atlas-scientific.com/pH_EZO_Datasheet.pdf)。
Serial Monitor 的输入不会转发给 EZO。

## 操作员校准命令（`Atlas_EC_pH_MQTT` 0.2，DECISION 053）

- 主题 `shrimp/lab/shrimp-node02/cmd`，只有 broker 账号 `pump-operator` 能写；节点用 clean session，离线期间发的命令直接丢弃，不会补执行。
- 格式：`id=<数字> operator=<名字> cmd=EC:<命令>` 或 `cmd=PH:<命令>`（`ezo_cal.py` / 控制页生成）。
- 白名单（`AtlasParse.h` `atlasOperatorCommand`）：EC `K,10`、`Cal,dry`、`Cal,low,<µS/cm>`、`Cal,high,<µS/cm>`、`Cal,<µS/cm>`（10–500000）；pH `Cal,mid,<6.5–7.5>`、`Cal,low,<1–6>`、`Cal,high,<8–13>`；两路都可 `Cal,clear`、`Cal,?`、`T,?`；EC `K,?`；pH `Slope,?`。其他一律拒绝（`NOT_ALLOWED`）。
- 每路一次一条，在两次读数之间发送；回复 `*OK` / `*ER` 结束这条命令，超时 3 s。K 或校准改动成功后，这一路重新执行启动查询（`i`、`K,?`、`T,?`、`Cal,?`），之后的读数行带新的 `K`、`calibration_reply`。
- 日志行：`event=OPERATOR_ACCEPTED|OPERATOR_COMMAND|OPERATOR_DONE|OPERATOR_REJECTED cmd_id=… operator=… command=… result=… reply=…`；格式不对的整条消息记 `event=OPERATOR_REJECTED_INVALID raw_hex=…`。HEALTH 行新增 `operator_commands`、`command_lost`。
- `result`：`OK`、`ER`（EZO 拒绝）、`OK_WITHOUT_DATA`、`DUPLICATE_ID`、`NOT_ALLOWED`、`SENSOR_NOT_READY`、`ANOTHER_COMMAND_PENDING`，或取消原因（`*RS`、`REPLY_TIMEOUT` 等）。

Wi-Fi 状态变化时及每 5 s 输出 `[WiFi] Connected | IP=... | node_id=shrimp-node02`。旧版 `Atlas_EC_pH_UART` 不发送测量到服务器；2026-09-27 起板上是 [Atlas_EC_pH_MQTT](script/Atlas_EC_pH_MQTT/README.md)，每一行日志都经 MQTT 发到 Jetson。
USB Monitor 115200；UART 的 9600 与它不同。上传设置见 [总说明](../README.md)。
