# Node-1 — 通信与脚本说明

入口：[DO_ORP_WiFi.ino](script/DO_ORP_WiFi/DO_ORP_WiFi.ino)。
`BenchChannel.h` 保存通道状态；`Protocol.h` 处理 CRC、帧格式和大端数值；`arduino_secrets.example.h` 是空密码模板。
上传与 Arduino 设置见 [lab_scale README](../README.md)。

每 4000 ms 按共同轮次先后请求 DO、ORP，分别接收并超时判断；不是硬件同步采样。
只发功能码 03：DO 从 0 读 6 个寄存器，ORP 从 0 读 2 个；无校准、地址或补偿写入。
DO 为大端浮点（饱和度比值乘 100），ORP 为有符号 16 位 mV，温度有符号数除 10。
每笔保留 raw、seq、boot_id、请求/接收 uptime、QC；读不到不输出伪零。Wi-Fi 状态约每 5 s 输出。
仅 USB 日志，无 MQTT/NTP/持久缓存；`UTC=UNSYNCED`、`QC=UNVALIDATED` 是真实未完成状态。
