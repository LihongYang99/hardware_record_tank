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


## 2026-09-27 MQTT 固件烧录与 Jetson 接入

- 经用户确认，先以 ROM 模式分 1 MB 块回读 16 MB flash 备份到 `.codex-build/node2-backup/`（含 sha256，镜像中有 `shrimp-node02` 字符串），再烧录 `Atlas_EC_pH_MQTT`，写入校验通过。
- Wi-Fi 复用 Node 1 已验证的 2.4 GHz 设置，约数秒连上，IP 192.168.88.251。Jetson broker 新增独立账号 `shrimp-node02` 与只允许本节点主题的 ACL；Node 1 密码未变，Node 1 数据未中断。
- 实测：148 条记录全部入库，transport_seq 1–148 连续，无拒收；网页 API 显示 Node 2 pH 实时值。
- pH：约 3.44（QC=`COMPENSATION_MISSING`，`?CAL,0` 未校准，`?T,25.00` 不是实测水温）。这是未校准的原始读数，**不能据此判断水样 pH**；探头当时浸在什么液体中未记录。
- **EC 无回复**：启动时 `C,0`、`*OK,1` 之后收不到任何字节，`REPLY_TIMEOUT`，每约 20 s 重试一次，`EC_ready=0`。pH 同一时间正常。传感器代码与旧版逐字节相同，引脚与波特率相同。烧录前这一次 EC 是否正常没有记录，所以还不能确定是硬件问题还是与新固件有关。
- EC 待查（先不改接线/K/校准）：EZO-EC 板 LED 颜色与状态、ISCCB-2 的 3.3 V/GND、RX18/TX17 两根线是否松动；必要时临时刷回备份，用旧程序对比 EC 是否有回复。
- 记录速率约 1.74 条/s（每个 TX/RX 单独成行），64 条 RAM 队列约只够 37 s 断网，见 sketch README 的容量表。

### 2026-09-27 EC 恢复通信

- 用户检查后确认 **EC 掉了一根线**，重新接好。无需重启或重新烧录：固件每约 20 s 重试初始化，00:29:10Z 起收到 EC 回复。前面的 `REPLY_TIMEOUT` 由断线引起，与新固件无关。
- 初始化回复与历史一致：`?I,EC,2.17`、`?K,1.00`、`?T,25.00`、`?CAL,0`。之后 EC 每 4 s 读数，无通信错误，无拒收。
- **EC 读数仍是 `EC_uS_cm=0.000 salinity_PSU=0.000`，QC=`CONFIGURATION_MISMATCH`（K=1.000，与买的 K10 探头不符）**，和 2026-09 之前的历史现象相同。这是模块实际回复的 0（原始回复原样保存），不是软件把错误值填成 0。原因可能是 K 设置不对、探头没有浸入液体或探头问题，**尚未确定**；K 与校准需要用户确认后才改，本次未改。
- pH 约 3.28–3.44，仍未校准、未做温度补偿，不代表水样 pH。

### 实测发送能力（重要的容量限制）

- EC 恢复后 Node 2 实测 **2.33 条/s**，64 条 RAM 队列约只够 **27 s** 断网（之前 EC 无回复时估的是 37 s）。
- 发送是“一次一条，等 Jetson 落库 ACK 再发下一条”。实测相邻两条记录的到达间隔最短约 99 ms，中位数约 251 ms（Node 1 最短约 107 ms）。所以每个节点**最多大约每秒 4–10 条**；Node 2 平时已经用掉不少，初始化时的一连串 TX/RX 会让 `transport_age_ms` 暂时升到约 4.7 s。断网后积压的记录只能用剩下的余量慢慢补发。
- 往返延迟较长的原因**未验证**，可能是 ESP32 Wi-Fi 默认省电模式（modem sleep）。可选的改进（未实施，留给顶层设计决定）：关闭 Wi-Fi 省电（`WiFi.setSleep(false)`，节点用 USB 供电，多耗一点电影响不大）、一次发送多条后批量 ACK、减少 TX/RX 单独成行的数量。

## 2026-09-27 晚：供电方式

- 用户确认 Node 2 经 USB Type-C 直接接电源适配器供电，已不接 Jetson USB（当晚 Jetson 上只有泵 1 的串口设备）。数据经 Wi-Fi 正常上传，网关核对 IP/MAC 一致。适配器型号未记录。

## 2026-10-06 至 10-12：pH 停止回复，用户报告已恢复

- 2026-10-06 21:16:06Z 之后 pH 不再回复：每次初始化 `*OK,1` 都 `REPLY_TIMEOUT`，节点 `pH_ready=0`，每约 20 s 重试；同一块板上的 EC 一直正常。现象与 2026-09-27 EC 掉线相同（当时是掉了一根线）。到网关停机前（2026-10-11 11:10Z）仍未恢复。
- 2026-10-12 用户报告 Node 2 已恢复，具体处理未说明。网关服务当时未运行，**尚未从数据核对**；启动服务后看 pH 是否有新的 `COMM=OK` 读数。
- 2026-10-12 核对：服务 17:24 EDT 重启后 pH 恢复正常读数（到 18:09 EDT 共 675 条非通信错误记录，最新 3.651，`COMPENSATION_MISSING`，仍未校准）。恢复已由数据确认。

## 2026-10-13：校准命令通道（DECISION 053），代码完成，尚未烧录

- 用户要校准 EC 和 pH，选择"加进网页 / 终端，烧录一次"；校准液尚未购买。
- 固件 `node02-mqtt-0.2`（见 [COMMUNICATION.md](COMMUNICATION.md#操作员校准命令atlas_ec_ph_mqtt-02decision-053)），网关 `ezo_cal.py` 与控制页卡片；步骤见 [CALIBRATION.md](CALIBRATION.md)。
- 验证：主机测试通过（白名单与格式、K,10 后重新读取状态、EC 干/低/高三步、pH 中点与 `Slope,?`、`*ER` 只结束该命令、去重、忙、EZO 复位取消、操作超时；无命令时启动流程仍不写 K/校准）；编译 914,183 B（69%），静态 RAM 50,220 B；回退版 `Atlas_EC_pH_UART` 也编译通过；网关测试 31 项通过；真实 broker 端到端：工具生成的 10 条命令只送到 node02 主题，均被固件解析器接受，其他节点账号发不进去。
- 待做：用户部署（prepare_mqtt、重启服务、备份、烧录，见 CALIBRATION.md 第 1 节）；买到校准液后先做 EC 的 `K,10`（解决 `CONFIGURATION_MISMATCH`），再做两路校准并记录验收读数。
