# Node-1 — 通信与脚本说明

入口：[DO_ORP_WiFi.ino](script/DO_ORP_WiFi/DO_ORP_WiFi.ino)。
`BenchChannel.h` 保存通道状态；`Protocol.h` 处理 CRC、帧格式和大端数值；`arduino_secrets.example.h` 是空密码模板。
上传与 Arduino 设置见 [lab_scale README](../README.md)。

每 4000 ms 按共同轮次先后请求 DO、ORP，分别接收并超时判断；不是硬件同步采样。
只发功能码 03：DO 从 0 读 6 个寄存器，ORP 从 0 读 2 个；无校准、地址或补偿写入。
DO 为大端浮点（饱和度比值乘 100），ORP 为有符号 16 位 mV，温度有符号数除 10。
每笔保留 raw、seq、boot_id、请求/接收 uptime、QC；读不到不输出伪零。Wi-Fi 状态约每 5 s 输出。
仅 USB 日志，无 MQTT/NTP/持久缓存；`UTC=UNSYNCED`、`QC=UNVALIDATED` 是真实未完成状态。

## 2026-09-26 MQTT 版本准备（尚未烧录）

新增独立入口 `script/DO_ORP_MQTT/DO_ORP_MQTT.ino`；原 USB 程序保留。读取指令与传感器参数不变，增加非阻塞日志队列、独立 MQTT 工作任务、应用层落库 ACK 和显式溢出计数。离线 UTC 尚未实现，继续标记 UNSYNCED。实际运行状态仍以板上程序为准，不能把新源码视为已完成 Wi-Fi 数据验收。详细队列、topic 和回退约束见新目录 README。
