# Node-2 — 调试进度

- 已完成两路通信；`EC_ready=1 pH_ready=1`；`COMM=OK`。
- EC 模块实际输出 `0.00,0.00`。这是收到的值，不是软件将错误填零；零值原因尚未确定，浸没状态等需核实。
- 查询 `?K,1.00`，与 K10 探头不匹配：`QC=CONFIGURATION_MISMATCH`。**尚未更改 K**。
- 两模块回复 `?CAL,0`：尚无本次可用校准记录，不能当校准完毕。
- `?T,25.00` 是保存的补偿设定，未验证为样品温度；pH 标 `QC=COMPENSATION_MISSING`。
- pH 5.189 → 5.326 → 5.428 → 5.512 的变化仅是调试输出，不能据此判定水质酸碱情况。
- 所有值 `validation=UNVALIDATED`，UTC 未同步。K、校准和实际温度补偿须另行确认并记录，不在本次整理中自动修改。

此前程序因只接受小写身份/校准前缀，误拒真实大写 `?I` / `?CAL`，现有代码已兼容，模拟测试覆盖；不是“未校准导致串口不通”。


## 历史调试记录

证据：用户串口片段；确切实验 UTC 未提供。

初始化误报 `WRONG_OR_MISSING_EZO_ID`、`BAD_CAL_REPLY`：程序早期前缀大小写处理与 EZO 2.17 实际回复不一致。现有快照接受 `?I` / `?i`、`?CAL` / `?Cal`，保留 EC/pH 型号检查。

实测原始十六进制及解码：

| raw_hex | ASCII 含义 |
|---|---|
| 3F492C45432C322E31370D | ?I,EC,2.17 + CR |
| 3F492C70482C322E31370D | ?I,pH,2.17 + CR |
| 3F4B2C312E30300D | ?K,1.00 + CR |
| 3F542C32352E30300D | ?T,25.00 + CR |
| 3F43414C2C300D | ?CAL,0 + CR |
| 2A4F4B0D | *OK + CR |

后续真实读取片段：

```text
node_id=shrimp-node02 boot_id=b1d653f3374e3af5 sensor=EC_ATLAS_EZO rx_uptime_ms=136514 seq=33 event=RX raw_hex=302E30302C302E30300D
node_id=shrimp-node02 boot_id=b1d653f3374e3af5 sensor=EC_ATLAS_EZO seq=33 cycle=34 scheduled_uptime_ms=136069 request_uptime_ms=136069 rx_uptime_ms=136514 UTC=UNSYNCED EC_uS_cm=0.000 salinity_PSU=0.000 K=1.000 compensation_setting_C=25.00 calibration_reply=?CAL,0 COMM=OK QC=CONFIGURATION_MISMATCH validation=UNVALIDATED temp_source=NOT_VERIFIED
node_id=shrimp-node02 boot_id=b1d653f3374e3af5 sensor=PH_ATLAS_EZO rx_uptime_ms=136695 seq=33 event=RX raw_hex=352E3332360D
node_id=shrimp-node02 boot_id=b1d653f3374e3af5 sensor=PH_ATLAS_EZO seq=33 cycle=34 scheduled_uptime_ms=136069 request_uptime_ms=136069 rx_uptime_ms=136695 UTC=UNSYNCED pH=5.326 compensation_setting_C=25.00 calibration_reply=?CAL,0 COMM=OK QC=COMPENSATION_MISSING validation=UNVALIDATED temp_source=NOT_VERIFIED
```

通信恢复不等于准确度通过。EC K=1 与 K10 不匹配、未校准、无实测温度补偿均未解决。
2026-09-22 用户确认 Node-2 IP 为 192.168.88.251；不把该日期或 IP 反填进旧测量日志。
