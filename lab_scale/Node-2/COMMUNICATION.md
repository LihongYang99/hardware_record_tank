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
目前不支持把 Serial Monitor 输入直接转发为校准命令。

Wi-Fi 状态变化时及每 5 s 输出 `[WiFi] Connected | IP=... | node_id=shrimp-node02`；不发送测量到服务器。
USB Monitor 115200；UART 的 9600 与它不同。上传设置见 [总说明](../README.md)。
