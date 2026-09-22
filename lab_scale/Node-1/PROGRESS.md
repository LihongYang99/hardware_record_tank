# Node-1 — 调试进度

用户曾收到 DO 约 6.55 mg/L、22.85°C，ORP 309–310 mV、22.6°C；这些是未验证台架示例，不是校准结果。
后续 ORP 超时，在对调/重接转换器后用户报告两个都恢复；不能确定转换器损坏或唯一根因。
未完成长时稳定性、标准液核查、补偿及正式部署验收。


## 历史调试记录

证据：用户串口片段与恢复报告；确切实验 UTC 未提供。

1. DO 单路接通，随后加入 Wi-Fi，再加入独立 ORP 转换器，共同 4 s 调度。
2. 用户贴出 DO 与 ORP 成功帧；同 cycle 的实际请求时间相同或接近，不代表探头内部同时采样。
3. 后续 ORP 出现 `raw= COMM=ERROR QC=COMMUNICATION_ERROR reason=TIMEOUT`，DO 仍正常。
4. 用户确认 12 V，移除保护帽仍超时；按交换/重接转换器的排查后报告“两个都好了”。根因未隔离，不断言是帽子或校准问题。

以下是聊天原始成功记录节选（不是持续运行数据文件）：

```text
node_id=shrimp-node01 boot_id=ee512acae3de7398 sensor=ORP_SEN0709 seq=6 request_uptime_ms=64079 rx_uptime_ms=64121 cycle=16 scheduled_uptime_ms=64079 report_uptime_ms=64151 UTC=UNSYNCED raw=010304013600E29B88 ORP_mV=310 temperature_C=22.6 COMM=OK QC=UNVALIDATED
node_id=shrimp-node01 boot_id=ee512acae3de7398 sensor=DO_SEN0681 seq=6 request_uptime_ms=64079 rx_uptime_ms=64138 cycle=16 scheduled_uptime_ms=64079 report_uptime_ms=64168 UTC=UNSYNCED raw=01030C3F689B0640D1A59D41B6CA025DD2 DO_mg_L=6.551 saturation_pct=90.86 temperature_C=22.85 COMM=OK QC=UNVALIDATED
```

首次行的 node_id 开头在聊天拷贝时缺少两个字符，此处按同一批完整后续行恢复；其余字段照录。不把后续恢复事件与这个旧 boot_id 合并成一次连续实验。
最新给出的 DHCP 地址为 192.168.88.252，未配置固定租约的证据。
