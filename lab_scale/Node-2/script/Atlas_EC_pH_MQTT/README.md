# Node 2 MQTT 实验版本（2026-09-27 已烧录，局域网链路已实测）

原 `../Atlas_EC_pH_UART/` 保持不变，作为源代码回退版本。

## 保持不变的传感器行为

`AtlasChannel.h`、`AtlasParse.h` 与旧版**逐字节相同**：EC UART1 RX18/TX17，pH UART2 RX16/TX15，9600 8N1，4000 ms 共同调度。启动时仍写与旧版相同的输出设置（`C,0`、`*OK,1`、EC 的 `O,EC,1` `O,TDS,0` `O,S,1` `O,SG,0`），**不写 K、校准、温度补偿**，也不切换 UART/I2C。所有 TX/RX 原始行、QC、seq、cycle、uptime 照旧输出。

## 改动

- `BenchLog.h` 改成适配层：接口不变，但每行都进入 `Telemetry`（MQTT 队列 + 有限 USB 队列）。单行上限仍是 767 字符，超出计 `line_too_long`。
- `Telemetry.h` 复制自 Node 1 已实测版本，只把节点名和固件标记改成宏（`shrimp-node02`、`node02-mqtt-0.1`）。主题：`shrimp/lab/shrimp-node02/records|status|ack`，QoS 1，Jetson 落库后才回 ACK。
- 板身份检查：读 eFuse 出厂 MAC `44:B1:76:CC:D4:84`；不符时不启动传感器，USB 每 5 s 打印 `event=WRONG_BOARD`。
- HEALTH 行增加 `mqtt_lost usb_lost format_lost line_too_long queued`。
- 仍然 `UTC=UNSYNCED`，读数 `validation=UNVALIDATED`。

## 配置、编译、回退（仓库根目录）

```bash
python3 lab_scale/jetson_web/configure_node1.py --node 2 --wifi-from-node1   # 复用 Node 1 已验证的 2.4 GHz Wi-Fi，不显示密码
python3 lab_scale/jetson_web/build_node1.py --node 2                         # 只编译，不烧录
# 回退到烧录前的旧程序（Node 2 接 Jetson USB 时）：
.codex-build/arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool --chip esp32s3 --port /dev/ttyACM0 write-flash 0 .codex-build/node2-backup/node2-flash-before-mqtt-*.bin
```

烧录前的 16 MB flash 备份（含 sha256）在 `.codex-build/node2-backup/`，不入 Git。

## 容量与限制条件

大部分限制与 Node 1 相同（队列 64 条 × 约 1,168 B、MQTT 写缓冲 1,536 B 等），见 [Node 1 的说明](../../../Node-1/script/DO_ORP_MQTT/README.md#容量与限制条件)。Node 2 不同的数字：

| 项目 | 数值 |
|---|---|
| 程序大小 | 911,567 B / 1,310,720 B（69%） |
| 静态全局 RAM | 49,860 B / 327,680 B（15%）；去掉了旧版 32 × 768 B 的静态 USB 队列 |
| 单行上限 | 767 字符（`BenchLog`），超出计 `line_too_long` |
| 实测记录长度 | pH 结果约 425 B、TX 约 229 B、RX 约 247 B、HEALTH 约 289 B，平均约 250 B |
| 实测记录速率 | EC 正常时 **约 2.33 条/s**（EC 断线时约 1.74 条/s）；每个 TX/RX 都单独成行 |
| 64 条队列可覆盖的断网时间 | 约 **27 s**（估算） |
| 发送能力上限 | 一次一条、等 ACK：实测相邻记录间隔最短约 99 ms、中位数约 251 ms，约 **4–10 条/s**；积压补发只能用剩余余量 |

记录速率高是因为 Node 2 把每条命令和每段原始回复都作为独立行保存。这对追查问题有用，但断网缓冲时间只有 Node 1 的约三分之一，并且占用了较多的发送能力，这一点是否要调整留待顶层设计决定。
