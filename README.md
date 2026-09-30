# Shrimp Trail Hardware

Research-grade real-time aquaculture monitoring: lab-scale integration first, tank-scale deployment later.

面向南美白对虾养殖的科研级实时监测项目。正式目标缸名义容量 340 L、目标盐度 15–25 ppt；实际运行水量待确认。当前是实验室台架验证，不是已完成的长期部署。

## 当前进度 / Current status — 2026-09-27 晚（EDT）

**局域网实时链路已打通（Jetson 临时网关）**：Node 1、Node 2、泵 1（pump-node-1）→ 实验室 Wi-Fi → MQTT → Jetson SQLite → 网页；相机 → 有线 → RTSP → 同一网页。泵 1 已校准，可以在 Jetson 终端或登录后的控制页开关、调流速。
监控页（不需要登录，只读）：中文 `http://192.168.88.249:8080`，英文 `/en`。设备控制页（需要账号登录）：中文 `/control`，英文 `/control/en`。仅实验室局域网可访问，说明见 [jetson_web](lab_scale/jetson_web/README.md)。
在实验室外：先连学校 Cisco VPN，再用 SSH 端口转发访问，见 [远程访问说明](jetson_setting/REMOTE_ACCESS.md)。学校不允许在校园网运行第三方 VPN / 隧道，因此不使用 Tailscale 等。

| 分区 | 设备 | 局域网 IP | 已完成 | 尚未完成 |
|---|---|---|---|---|
| [lab_scale / Node-1](lab_scale/Node-1/README.md) | shrimp-node01；ESP32-S3 N16R8；DFRobot SEN0681 DO + SEN0709 ORP | 192.168.88.252 | MQTT 固件已烧录；数据实时进入 Jetson 数据库与网页；断线 25 s 补发无缺口；USB Type-C 电源适配器独立供电 | 校准/验证、UTC、断电持久缓存、长期稳定性 |
| [lab_scale / Node-2](lab_scale/Node-2/README.md) | shrimp-node02；ESP32-S3 N16R8；Atlas EZO-EC + EZO-pH、两块 ISCCB-2 | 192.168.88.251 | MQTT 固件已烧录；EC、pH 实时进入 Jetson；EC 掉线已重接；USB Type-C 电源适配器独立供电 | EC 读数 0（K=1 与 K10 不符）、校准、温度补偿、UTC |
| [lab_scale / pump-node-1](lab_scale/pump-node-1/README.md) | **泵 1**；shrimp-node04（总 Node 4）；单独 ESP32-S3；Atlas EZO-PMP 蠕动泵（UART） | 192.168.88.248 | 固件 0.2 已烧录；两种校准完成（`?CAL,3`），恒定流量上限 45.36 mL/min；终端 `pump_ctl.py` 与网页控制页可开关、调流速；每条操作记录操作人和泵回复（DECISION 048）；USB Type-C 电源适配器独立供电，不接 Jetson | 流量计（"运行中"只是控制器报告）、盐水软管兼容性、黑线 GND 与电机负极是否相通、长期运行；45 mL/min 低于 SPEC §29 构想值 |
| [lab_scale / pump-node-2](lab_scale/pump-node-2/README.md) | **泵 2**；shrimp-node05（总 Node 5）；单独 ESP32-S3；Atlas EZO-PMP（UART），与泵 1 同接线、同代码 | 192.168.88.247 | 2026-09-29 已烧录；两种校准完成（`?CAL,3`），恒定流量上限 49.63 mL/min，复核 9.85 mL；中英文监控页面板、控制页卡片（DECISION 049） | 流量计、盐水软管兼容性；用途暂定第二个旁路泵，SPEC 未改 |
| [lab_scale / Node-6](lab_scale/Node-6/README.md) | shrimp-node06；ESP32-S3；DFRobot SEN0710 浊度，RS485 Modbus | 192.168.88.246 | 2026-09-29 已烧录，实时进入网页，通信无错误（DECISION 050） | 读数停在 1000 NTU 满量程，待探头入水复查；盐水长期浸泡未确认；只报 NTU，不是 eTSS |
| [lab_scale / camera_node](lab_scale/camera_node/README.md) | Barlus 水下 IP 相机，标签 IPC5MPIR-PBX10 | 192.168.1.88（MAC 已核对） | ONVIF 取得视频地址；子码流 704×576 实时预览进入网页 | 录像策略、相机时钟（差约 6 个月）、改默认密码、淡水款不批准目标盐度长期部署 |
| [lab_scale / jetson_web](lab_scale/jetson_web/README.md) | Jetson Orin Nano，临时网关 | 有线 192.168.88.249（相机另需临时 192.168.1.200） | Mosquitto + 接收器 + SQLite + 中/英文监控页 + 登录控制页；落库后才 ACK | **开机自启**（2026-09-27 重启后约 4 小时无数据）、磁盘限额/备份、迁移到 Raspberry Pi |
| [tank_scale](tank_scale/README.md) | 未来实际部署 | 未分配 | 预留独立目录 | 正式部署设计与验收 |

Jetson 和各 ESP32 节点的 IP 已固定（路由器静态租约），完整列表见下方[设备 IP 一览](#设备-ip-一览2026-09-30-核对)；仍以 MAC 核对身份为准。
所有读数仍为 `UNVALIDATED`（未校准），采样 UTC 未同步，网页时间是 Jetson 接收时间。
节点断网缓冲只在 RAM：Node 1 约 80 s、Node 2 约 27 s、泵 1 约 2 分钟（估算），断电丢失；容量与限制条件见各固件 README。
Jetson 重启后服务不会自动启动，需要手动运行启动命令（见 jetson_web README）。
Jetson 是临时网关，正式架构仍按 SPEC 使用 Raspberry Pi。
2026-09-27 当天泵 1 从接线到网页控制的调试过程（现象 → 原因 → 处理）见 [pump-node-1 README](lab_scale/pump-node-1/README.md#调试过程2026-09-27摘要)，网关侧见 [jetson_web README](lab_scale/jetson_web/README.md#2026-09-27-晚泵-1-接入与设备控制页)。

## 设备 IP 一览（2026-09-30 核对）

实验室局域网 `192.168.88.0/24`，路由器 MikroTik hAP ax3。下表除相机和学校网外，都已在路由器上按 MAC 做了 DHCP 静态租约（用户 2026-09-30 设置），IP 与 MAC 的对应由 Jetson ARP 核对。

| 设备 | 节点名 | IP | MAC | 连接 / 端口 |
|---|---|---|---|---|
| 路由器 MikroTik hAP ax3 | — | 192.168.88.1 | — | 网关、DHCP；管理页 `http://192.168.88.1` |
| **Jetson（网关）** 有线 `enP8p1s0` | — | **192.168.88.249** | 4C:BB:47:62:1F:66 | MQTT `:1883`；监控页 `:8080`（`/`、`/en`）；控制页 `/control`、`/control/en`。所有节点固件都写死这个地址 |
| Node 1 · DO / ORP | shrimp-node01 | 192.168.88.252 | 44:B1:76:CE:D1:A8 | Wi-Fi 2.4 GHz |
| Node 2 · EC / pH | shrimp-node02 | 192.168.88.251 | 44:B1:76:CC:D4:84 | Wi-Fi 2.4 GHz |
| 泵 1 | shrimp-node04 | 192.168.88.248 | 7C:4F:AD:B5:33:38 | Wi-Fi 2.4 GHz |
| 泵 2 | shrimp-node05 | 192.168.88.247 | 7C:4F:AD:B5:1C:D4 | Wi-Fi 2.4 GHz |
| Node 6 · 浊度 | shrimp-node06 | 192.168.88.246 | 44:B1:76:CE:D8:6C | Wi-Fi 2.4 GHz |
| 水下相机 | ONVIF `NVT` | 192.168.1.88 | 00:12:34:C6:67:04 | 有线 PoE；相机内设固定地址，另一网段 |
| Jetson 相机网段临时地址 | — | 192.168.1.200/24 | 同 Jetson 有线 | 每次重启后 `sudo ip addr add 192.168.1.200/24 dev enP8p1s0` |
| Jetson 学校 Wi-Fi `wlP1p1s0`（eduroam） | — | 10.141.48.128/23 | — | 学校 DHCP，**会变**；只用于 VPN + SSH 远程访问 |

## 方法与原理（给参观者的整体介绍）

### 方法：数据是怎么从水里走到网页的

1. **传感器测量**。探头泡在水里，各自的信号板把测量结果变成数字信号：DO/ORP 探头输出 RS485 Modbus，Atlas EC/pH 探头经 EZO 电路和隔离载板输出 UART 文本。
2. **ESP32 采集**。每块 ESP32 每 4 秒轮询一次自己的两支探头，把每次读数连同原始字节、序号（`seq`）、开机标识（`boot_id`）和质量标记（`QC`）拼成一行 `key=value` 文本。读不到也记一行，标记通信错误，不写零。
3. **Wi-Fi + MQTT 上传**。节点连实验室 2.4 GHz Wi-Fi，把每行记录以 MQTT QoS 1 发到网关（当前 Jetson，正式为 Raspberry Pi）。每个节点有自己的 broker 账号，只能写自己的主题 `shrimp/lab/<节点>/records`。
4. **网关落库后确认**。接收器核对身份和序号后写入 SQLite；写入成功才回一条应用层 ACK。节点收到 ACK 才删除该记录，否则每 5 秒重发。网关中断 25 秒后能补发、无缺口（已实测）。
5. **网页展示**。浏览器从网关的只读 API 读最新值、QC 状态和历史曲线，同时显示相机预览（相机 → 有线 → RTSP → 网关解码为 JPEG → 网页），可导出 CSV。

### 原理：为什么这样设计

- **原始数据优先**。每条记录同时保留原始字节和解析值。以后校准或重新解析时，可以从原始数据重算，不会因为当时的解析错误丢掉证据。
- **失败不写零**。读不到、超时、配置不符时数值记为空并附 QC 标记（如 `COMMUNICATION_ERROR`、`CONFIGURATION_MISMATCH`）。零是一个合法的测量值，用零表示"没读到"会污染实验数据。
- **序号 + 开机标识**。`seq` 单调递增，网关据此发现丢失、重复和乱序；`boot_id` 每次开机变化，用来区分"序号回到 1 是因为重启"。这是 SPEC §21 的要求。
- **双时间戳**。设计上区分"采样时间"和"网关接收时间"，才能分清采样延迟和网络延迟（SPEC §20）。目前节点没有可信 UTC，所以采样时间记为空、标 `UNSYNCED`，只有接收时间；不会用开机时间冒充 UTC。
- **落库后再确认**。MQTT 自己的 PUBACK 只说明 broker 收到了消息，不代表已经写进数据库。本项目另加一层应用 ACK，保证"节点删掉记录"和"数据已在磁盘上"是同一件事。
- **节点互相独立**。每个 ESP32 只管自己的探头，掉一个不影响另一个；两支探头各走独立串口，一支超时不会卡住另一支（SPEC §39 非阻塞要求）。
- **网关可替换**。固件只依赖 MQTT 主题和 ACK 约定，不依赖 Jetson。把 broker、接收器和网页迁到 Raspberry Pi 时，固件架构不用改（SPEC §43）。
- **优先级**。按 SPEC §48：科学有效性 > 电气安全 > 数据完整性 > 可靠性 > 可维护性 > 模块化 > 可扩展性 > 成本。

各部分的具体方法与原理见 [lab_scale](lab_scale/README.md)、[Node-1](lab_scale/Node-1/README.md)、[Node-2](lab_scale/Node-2/README.md)、[camera_node](lab_scale/camera_node/README.md)、[jetson_web](lab_scale/jetson_web/README.md)。

## 目录与使用

```text
lab_scale/
  README.md                # 整体进度
  Node-1/                  # DO + ORP
    README.md              # 节点概况与 IP
    HARDWARE.md            # 传感器型号
    WIRING.md              # 接线
    COMMUNICATION.md       # 通信与脚本说明
    PROGRESS.md            # 调试进度
    script/DO_ORP_MQTT/    # 当前板上程序（MQTT）
    script/DO_ORP_WiFi/    # 旧版（仅 USB 串口），保留回退
    tests/
  Node-2/                  # 同样拆分文档
    script/Atlas_EC_pH_MQTT/   # 当前板上程序（MQTT）
    script/Atlas_EC_pH_UART/   # 旧版，保留回退
  pump-node-1/             # 泵 1：旁路蠕动泵（总 Node 4），同样拆分文档
    script/PMP_MQTT/       # 当前板上程序（MQTT 0.2，含操作命令）
  pump-node-2/             # 泵 2（总 Node 5），与泵 1 共用固件代码
  Node-6/                  # 浊度（DFRobot RS485），script/TURB_MQTT/
  camera_node/             # 相机文档；接入代码在 jetson_web
  jetson_web/              # Jetson 临时网关：MQTT broker、接收器、数据库、网页
  CHANGELOG.md             # 仓库整理记录
jetson_setting/            # Jetson 设置与交接说明
tank_scale/README.md        # 未来实际部署
```

每块 ESP32 独立上传自己的程序。MQTT 版本的本地配置用 `lab_scale/jetson_web/configure_node1.py --node 1|2|4|5|6` 生成
`arduino_secrets.h`（Wi-Fi 必须是 2.4 GHz；4 = pump-node-1，5 = pump-node-2，6 = 浊度），编译用 `build_node1.py --node 1|2|4|5|6`；真实密码文件禁止提交。
烧录前的板上 flash 备份在 `.codex-build/node*-backup/`（不入 Git），回退命令见各固件 README。

完整阶段记录见 [lab_scale README](lab_scale/README.md) 与各节点的 PROGRESS.md。
正式里程碑仍是 **传感器 → ESP32 → UTC → Wi-Fi/MQTT → Raspberry Pi → 数据库 → Dashboard**。
当前由 Jetson Orin 临时充当网关做实验室演示；它不替代规范中 Raspberry Pi 的基础网关要求。

## Documentation / 文档

- [Binding engineering specification / 约束性工程规范](SPEC.md)
- [Current project objective / 当前项目目标](GOAL.md)
- [实验室节点文档](lab_scale/README.md)
- [实际部署预留](tank_scale/README.md)

## 既有工程规划资料

- [决策记录](DECISIONS.md)
- [Phase 1 工程资料（English）](docs/phase1/README.md)
- [Phase 1 工程资料（中文）](docs/phase1/zh-CN/README.md)

这些文档保留早期选型、BOM、供电、接线、旁路和数据架构的规划进度，不代表所有候选硬件已购买或部署。当前台架实测状态以 lab_scale 为准，约束性设计以 SPEC 为准；历史内容如有差异，不静默当成最新实物状态。

`SPEC.md` and `GOAL.md` must be read before engineering, purchasing, wiring, firmware, software, Raspberry Pi, database, or Jetson work. Unverified hardware facts remain purchase gates; invalid or missing measurements are never converted to zero.

进行工程、采购、接线、固件、软件、树莓派、数据库或 Jetson 工作前，必须先完整阅读 `SPEC.md` 和 `GOAL.md`。未经验证的硬件事实仍是采购门槛；无效或缺失数据绝不写成零。
