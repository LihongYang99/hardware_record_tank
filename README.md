# Shrimp Trail Hardware

Research-grade real-time aquaculture monitoring: lab-scale integration first, tank-scale deployment later.

面向南美白对虾养殖的科研级实时监测项目。正式目标缸名义容量 340 L、目标盐度 15–25 ppt；实际运行水量待确认。当前是实验室台架验证，不是已完成的长期部署。

## 当前进度 / Current status — 2026-09-22

| 分区 | 设备 | 最近记录的局域网 IP | 已完成 | 尚未完成 |
|---|---|---|---|---|
| [lab_scale / Node-1](lab_scale/Node-1/README.md) | shrimp-node01；ESP32-S3 N16R8；DFRobot SEN0681 DO + SEN0709 ORP | 192.168.88.252（此前日志，待现场复核） | 两路独立 RS485 读取成功；Wi-Fi 已连接；4 s 请求周期 | 校准/验证、UTC、MQTT、长期稳定性 |
| [lab_scale / Node-2](lab_scale/Node-2/README.md) | shrimp-node02；ESP32-S3 N16R8；Atlas EZO-EC + EZO-pH、两块 ISCCB-2 | 192.168.88.251（用户 2026-09-22 确认） | 两路 UART 回复、读取成功；Wi-Fi 已连接；4 s 请求周期 | K10 配置不匹配、校准、温度补偿、UTC、MQTT |
| [lab_scale / camera_node](lab_scale/camera_node/README.md) | 用户提供的水下 PoE IP 相机 | NOT VERIFIED | 已接 PoE 网络（用户报告） | 精确型号、IP、视频流、录像验证 |
| [tank_scale](tank_scale/README.md) | 未来实际部署 | 未分配 | 预留独立目录 | 正式部署设计与验收 |

这些 IP 是记录值，不是固件固定 IP；DHCP 重启后可能变化。Wi-Fi 已连接不等于数据已经通过网络发送。
目前两块 ESP32 的数据出口仍是 USB 串口；尚无 MQTT、UTC 同步、数据库或实时网页端到端验证。
`COMM=OK` 只代表通信检查通过，所有测量仍为 `UNVALIDATED`。

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
    script/DO_ORP_WiFi/     # .ino 与配套 .h
    tests/
  Node-2/                  # 同样拆分文档
    script/Atlas_EC_pH_UART/
  camera_node/             # 同样拆分文档，script/ 暂为空实现
  CHANGELOG.md             # 仓库整理记录
tank_scale/README.md        # 未来实际部署
```

每块 ESP32 独立上传自己的程序。先将对应程序目录中的 `arduino_secrets.example.h`
复制为同目录 `arduino_secrets.h`，只在本地填写 Wi-Fi 信息；真实密码文件禁止提交。
脚本来自现有台架工作副本，本次仅整理目录、补充记录，不变更采集行为、不上传硬件。
历史 `output/bench` 保留不动；整理后的入口是 `lab_scale`，不要混用不同副本修改。

完整阶段记录见 [lab_scale README](lab_scale/README.md) 与各节点的 PROGRESS.md。
正式里程碑仍是 **传感器 → ESP32 → UTC → Wi-Fi/MQTT → Raspberry Pi → 数据库 → Dashboard**。
Jetson Orin 只作为用户拟用的临时测试电脑/后续计算平台，不替代规范中的基础网关要求。

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
