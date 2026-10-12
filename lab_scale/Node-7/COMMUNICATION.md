# Node-7 — 通信

| 文件 | 来源 |
|---|---|
| HEATER_MQTT.ino | 新写：MAC 检查、GPIO5 继电器、60 s 自动断开、状态与健康日志 |
| HeaterLogic.h | 新写：命令解析、超时判断（主机测试） |
| Telemetry.h / BenchLog.h | 与 pump-node-1 逐字节相同（带命令主题） |

## 命令（网关 → 节点）

主题 `shrimp/lab/shrimp-node07/cmd`，只有 broker 账号 `pump-operator` 能写。格式与泵相同：`id=<数字> operator=<名字> cmd=<命令>`。

| 命令 | 节点动作 |
|---|---|
| `HEAT,ON` | 继电器 CH1 通电，并记下时间；60 s 内没有新的 `HEAT,ON` 就自动断开（`reason=NO_ON_REFRESH`） |
| `HEAT,OFF` | 立即断开 |
| 其他任何内容 | 忽略，记 `event=COMMAND_REJECTED`，不改变继电器 |

节点离线时发的命令直接丢弃（clean session），不会在之后执行。

## 日志行

每 4 s：

```
node_id=shrimp-node07 boot_id=… sensor=HEATER_RELAY seq=… cycle=… request_uptime_ms=… UTC=UNSYNCED relay_on=1 gpio=1 on_command_age_s=12 COMM=OK QC=UNVALIDATED
```

继电器变化时：`event=RELAY_ON reason=COMMAND_ON` / `event=RELAY_OFF reason=COMMAND_OFF|NO_ON_REFRESH`。每 10 s 一行 `event=HEALTH`（命令数、拒绝数、队列丢失）。`relay_on` 是节点的控制状态，不是测得的加热功率。
