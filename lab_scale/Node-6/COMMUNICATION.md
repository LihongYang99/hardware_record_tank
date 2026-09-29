# Node-6 — 通信与脚本说明

入口：[TURB_MQTT.ino](script/TURB_MQTT/TURB_MQTT.ino)。

| 文件 | 来源 |
|---|---|
| TURB_MQTT.ino | 新写：节点名、MAC 检查、一路浊度通道、4 s 调度、Wi-Fi、健康日志 |
| Protocol.h / BenchChannel.h | 与 Node-1 逐字节相同（Modbus CRC、帧检查、通道状态） |
| Telemetry.h | 与 Node-2 逐字节相同（RAM 队列、MQTT、落库 ACK） |
| arduino_secrets.example.h | 空模板；真实文件由 `configure_node1.py --node 6` 生成 |

## Modbus

UART1，RX GPIO18 / TX GPIO17，4800 8N1，地址 1。每 4 s 发 `01 03 00 00 00 02 C4 0B`（只读 2 个寄存器）；等回复最多 1 s，收到字节后 30 ms 无新字节即认为一帧结束。

## 日志行（每 4 s 一行）

```
node_id=shrimp-node06 boot_id=… sensor=TURB_SEN0710 seq=… request_uptime_ms=… rx_uptime_ms=… cycle=… scheduled_uptime_ms=… report_uptime_ms=… UTC=UNSYNCED raw=0103040D2E00DBD8CD turbidity_NTU=337.4 temperature_C=21.9 COMM=OK QC=UNVALIDATED
```

| QC | 含义 |
|---|---|
| `UNVALIDATED` | 通信正常、在 0–1000 NTU 内，但探头未校准 |
| `OUT_OF_RANGE` | 浊度 > 1000 NTU（超出资料量程）；数值照记 |
| `COMMUNICATION_ERROR` | `TIMEOUT` / `CRC_ERROR` / `SHORT_FRAME` / `WRONG_ADDRESS` / `MODBUS_EXCEPTION` / `UNEXPECTED_FRAME` / `RX_OVERFLOW`，不输出数值，网关存空值（不是 0） |

MQTT 主题 `shrimp/lab/shrimp-node06/{records,status,ack}`，账号 `shrimp-node06` 只能写自己的主题；此节点没有命令主题。
