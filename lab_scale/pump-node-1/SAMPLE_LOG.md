# pump-node-1 — 原始输出样例（sample log）

以下是 **真实记录**，由脚本从 Jetson 数据库 `raw_log` 表原样摘出（2026-09-27，固件 `node04-pump-mqtt-0.1`，boot `62f68654e8e0a6f6`），未改写。当时 12 V 电机电源**尚未连接**，所以泵拒绝启动，这是预期结果。泵未校准。

- `# ` 开头的注释是 Jetson 接收时间（`received_utc`），不是采样时间。
- USB 串口看到的行末尾没有 `transport_age_ms` / `network_buffered`（发 MQTT 时才加）。

## raw_hex 解码

| raw_hex | ASCII | 含义（数据手册） |
|---|---|---|
| 2A52530D | `*RS` | 泵复位（这次是控制板电源刚接对） |
| 2A52450D | `*RE` | 泵启动完成 |
| 302E30300D | `0.00` | 出厂默认的每秒连续输出，随后被 `C,0` 关掉 |
| 3F492C504D502C312E30360D | `?I,PMP,1.06` | 设备是 PMP，固件 1.06 |
| 3F5354415455532C422C332E32380D | `?STATUS,B,3.28` | 上次重启原因 B = 欠压；VCC 3.28 V |
| 3F43414C2C300D | `?CAL,0` | 未校准 |
| 3F4453544152542C302E30300D | `?DSTART,0.00` | 未设置上电自动输送 |
| 3F4D4158524154452C35342E36360D | `?MAXRATE,54.66` | 恒定流量（DC）模式最大 54.66 mL/min |
| 2A55562C50554D505057522C302E30300D | `*UV,PUMPPWR,0.00` | 电机电源欠压：0.00 V（12 V 未接） |
| 2A45520D | `*ER` | 命令被拒绝 |

注意：这台泵的回复前缀是大写（`?I`、`?STATUS`、`?CAL`），与数据手册示例的小写不同；固件按不区分大小写解析。

## 记录原文

```text
# 2026-09-27T21:00:06.103Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=28658 seq=0 event=RX raw_hex=2A52530D transport_boot_id=62f68654e8e0a6f6 transport_seq=27 firmware=node04-pump-mqtt-0.1 transport_age_ms=58 network_buffered=0
# 2026-09-27T21:00:06.565Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=28662 seq=0 event=RX raw_hex=2A52450D transport_boot_id=62f68654e8e0a6f6 transport_seq=29 firmware=node04-pump-mqtt-0.1 transport_age_ms=514 network_buffered=0
# 2026-09-27T21:00:07.071Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=29637 seq=0 event=RX raw_hex=302E30300D transport_boot_id=62f68654e8e0a6f6 transport_seq=31 firmware=node04-pump-mqtt-0.1 transport_age_ms=41 network_buffered=0
# 2026-09-27T21:00:11.317Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=33298 seq=0 event=RX raw_hex=3F492C504D502C312E30360D transport_boot_id=62f68654e8e0a6f6 transport_seq=42 firmware=node04-pump-mqtt-0.1 transport_age_ms=625 network_buffered=0
# 2026-09-27T21:00:12.065Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=33427 seq=0 event=RX raw_hex=3F5354415455532C422C332E32380D transport_boot_id=62f68654e8e0a6f6 transport_seq=45 firmware=node04-pump-mqtt-0.1 transport_age_ms=1245 network_buffered=0
# 2026-09-27T21:00:12.816Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=33549 seq=0 event=RX raw_hex=3F43414C2C300D transport_boot_id=62f68654e8e0a6f6 transport_seq=48 firmware=node04-pump-mqtt-0.1 transport_age_ms=1877 network_buffered=0
# 2026-09-27T21:00:13.813Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=33678 seq=0 event=RX raw_hex=3F4453544152542C302E30300D transport_boot_id=62f68654e8e0a6f6 transport_seq=52 firmware=node04-pump-mqtt-0.1 transport_age_ms=2748 network_buffered=0
# 2026-09-27T21:00:14.571Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=33805 seq=0 event=RX raw_hex=3F4D4158524154452C35342E36360D transport_boot_id=62f68654e8e0a6f6 transport_seq=55 firmware=node04-pump-mqtt-0.1 transport_age_ms=3379 network_buffered=0
# 2026-09-27T21:00:15.217Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP uptime_ms=33909 event=READY target_mL_min=80.00 calibration_reply=?CAL,0 transport_boot_id=62f68654e8e0a6f6 transport_seq=57 firmware=node04-pump-mqtt-0.1 transport_age_ms=3784 network_buffered=0
# 2026-09-27T21:00:15.345Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP event=TX command=DC,80.00,* uptime_ms=36075 seq=1 transport_boot_id=62f68654e8e0a6f6 transport_seq=58 firmware=node04-pump-mqtt-0.1 transport_age_ms=1855 network_buffered=0
# 2026-09-27T21:00:15.568Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=36106 seq=1 event=RX raw_hex=2A55562C50554D505057522C302E30300D transport_boot_id=62f68654e8e0a6f6 transport_seq=59 firmware=node04-pump-mqtt-0.1 transport_age_ms=2072 network_buffered=0
# 2026-09-27T21:00:16.191Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP rx_uptime_ms=36110 seq=1 event=RX raw_hex=2A45520D transport_boot_id=62f68654e8e0a6f6 transport_seq=61 firmware=node04-pump-mqtt-0.1 transport_age_ms=2692 network_buffered=0
# 2026-09-27T21:00:16.434Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP uptime_ms=36110 event=CONTROL_REJECTED seq=1 cycle=9 transport_boot_id=62f68654e8e0a6f6 transport_seq=62 firmware=node04-pump-mqtt-0.1 transport_age_ms=2816 network_buffered=0
# 2026-09-27T21:00:16.563Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 sensor=PUMP_ATLAS_PMP seq=1 cycle=9 scheduled_uptime_ms=36074 request_uptime_ms=36074 rx_uptime_ms=36230 UTC=UNSYNCED pump_on=0 int_pin=0 motor_V=0.00 total_volume_mL=0.00 target_mL_min=80.00 raw_D=?D,0.00,0 raw_PV=?PV,0.00 raw_TV=?TV,0.00 calibration_reply=?CAL,0 COMM=OK QC=NOT_RUNNING_AS_COMMANDED validation=UNVALIDATED transport_boot_id=62f68654e8e0a6f6 transport_seq=63 firmware=node04-pump-mqtt-0.1 transport_age_ms=2606 network_buffered=0
# 2026-09-27T21:00:17.351Z
node_id=shrimp-node04 boot_id=62f68654e8e0a6f6 event=HEALTH uptime_ms=40000 pump_ready=1 pump_resets=1 control_commands=1 UTC=UNSYNCED mqtt_lost=0 usb_lost=56 format_lost=0 line_too_long=0 queued=0 transport_boot_id=62f68654e8e0a6f6 transport_seq=65 firmware=node04-pump-mqtt-0.1 transport_age_ms=1 network_buffered=0
```
