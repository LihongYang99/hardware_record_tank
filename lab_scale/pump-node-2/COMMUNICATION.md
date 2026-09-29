# pump-node-2 — 通信

UART 命令、日志字段、QC 含义、操作命令格式与泵 1 完全相同，见 [pump-node-1/COMMUNICATION.md](../pump-node-1/COMMUNICATION.md)。只有下面这些不同：

| 项目 | 泵 1 | 泵 2 |
|---|---|---|
| node_id / hostname / broker 账号 | `shrimp-node04` | `shrimp-node05` |
| 数据库传感器编号 | `PUMP_ATLAS_PMP` | `PUMP2_ATLAS_PMP` |
| 固件标识 | `node04-pump-mqtt-0.2` | `node05-pump-mqtt-0.2` |
| MQTT 主题 | `shrimp/lab/shrimp-node04/{records,status,ack,cmd}` | `shrimp/lab/shrimp-node05/{records,status,ack,cmd}` |
| 控制页设备 / 终端 | `pump1` / 默认 | `pump2` / `pump_ctl.py --device pump2` |

`cmd` 主题只有 broker 账号 `pump-operator` 能写（2026-09-29 已加入 ACL）；泵 2 只能读自己的 `cmd`，不能读写泵 1 的主题。
