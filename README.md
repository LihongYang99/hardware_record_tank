# Shrimp Trail Hardware

Research-grade real-time aquaculture monitoring: lab-scale integration first, tank-scale deployment later.

面向南美白对虾养殖的科研级实时监测项目。正式目标缸名义容量 340 L、目标盐度 15–25 ppt；实际运行水量待确认。当前是实验室台架验证，不是已完成的长期部署。

## 当前进度 / Current status — 2026-09-27

**局域网实时链路已打通（Jetson 临时网关）**：Node 1、Node 2 → 实验室 Wi-Fi → MQTT → Jetson SQLite → 网页；相机 → 有线 → RTSP → 同一网页。
网页：中文 `http://192.168.88.249:8080`，英文 `http://192.168.88.249:8080/en`（仅实验室局域网可访问）。说明见 [jetson_web](lab_scale/jetson_web/README.md)。
在实验室外：先连学校 Cisco VPN，再用 SSH 端口转发访问，见 [远程访问说明](jetson_setting/REMOTE_ACCESS.md)。学校不允许在校园网运行第三方 VPN / 隧道，因此不使用 Tailscale 等。

| 分区 | 设备 | 局域网 IP（实测） | 已完成 | 尚未完成 |
|---|---|---|---|---|
| [lab_scale / Node-1](lab_scale/Node-1/README.md) | shrimp-node01；ESP32-S3 N16R8；DFRobot SEN0681 DO + SEN0709 ORP | 192.168.88.252 | MQTT 固件已烧录；数据实时进入 Jetson 数据库与网页；断线 25 s 补发无缺口；USB 充电头独立供电 | 校准/验证、UTC、断电持久缓存、长期稳定性 |
| [lab_scale / Node-2](lab_scale/Node-2/README.md) | shrimp-node02；ESP32-S3 N16R8；Atlas EZO-EC + EZO-pH、两块 ISCCB-2 | 192.168.88.251 | MQTT 固件已烧录；EC、pH 实时进入 Jetson；EC 掉线已重接 | EC 读数 0（K=1 与 K10 不符）、校准、温度补偿、UTC |
| [lab_scale / camera_node](lab_scale/camera_node/README.md) | Barlus 水下 IP 相机，标签 IPC5MPIR-PBX10 | 192.168.1.88（MAC 已核对） | ONVIF 取得视频地址；子码流 704×576 实时预览进入网页 | 录像策略、相机时钟（差约 6 个月）、改默认密码、淡水款不批准目标盐度长期部署 |
| [lab_scale / jetson_web](lab_scale/jetson_web/README.md) | Jetson Orin Nano，临时网关 | 有线 192.168.88.249（相机另需临时 192.168.1.200） | Mosquitto + 接收器 + SQLite + 中/英文网页；落库后才 ACK | 开机自启、磁盘限额/备份、迁移到 Raspberry Pi |
| [tank_scale](tank_scale/README.md) | 未来实际部署 | 未分配 | 预留独立目录 | 正式部署设计与验收 |

IP 来自 DHCP，重启后可能变化，以 MAC 核对身份为准。
所有读数仍为 `UNVALIDATED`（未校准），采样 UTC 未同步，网页时间是 Jetson 接收时间。
节点断网缓冲只在 RAM：Node 1 约 80 s、Node 2 约 27 s，断电丢失；容量与限制条件见各固件 README。
Jetson 是临时网关，正式架构仍按 SPEC 使用 Raspberry Pi。

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
  camera_node/             # 相机文档；接入代码在 jetson_web
  jetson_web/              # Jetson 临时网关：MQTT broker、接收器、数据库、网页
  CHANGELOG.md             # 仓库整理记录
jetson_setting/            # Jetson 设置与交接说明
tank_scale/README.md        # 未来实际部署
```

每块 ESP32 独立上传自己的程序。MQTT 版本的本地配置用 `lab_scale/jetson_web/configure_node1.py --node 1|2` 生成
`arduino_secrets.h`（Wi-Fi 必须是 2.4 GHz），编译用 `build_node1.py --node 1|2`；真实密码文件禁止提交。
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
