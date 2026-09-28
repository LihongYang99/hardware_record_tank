# Jetson 设置与工作交接

此目录保存 Jetson Orin 的设置与交接说明。当前任务是在 Jetson 上临时集成 lab_scale 两个 ESP32 节点和相机的网页，不改变正式 Raspberry Pi 网关架构。

## 给 Jetson 上 Codex 的入口

先完整阅读仓库根目录的 `AGENTS.md`、`SPEC.md`、`GOAL.md`，再阅读 [JETSON_HANDOVER.md](JETSON_HANDOVER.md)。

当前网络：有线接实验室局域网，Wi-Fi 接学校网络。请先只读检查真实网卡、地址、路由、软件与固件，不直接套用历史 IP 或无线接口名称。

交接说明包含节点信息、MQTT 缺口、相机已验证与待验证状态、网页需求、执行顺序、安全边界和验收要求。不保存任何密码。

从实验室外访问网页（学校 Cisco VPN + SSH 端口转发，不用第三方隧道）见 [REMOTE_ACCESS.md](REMOTE_ACCESS.md)。转发后监控页是 `http://localhost:8080`，设备控制页是 `http://localhost:8080/control`（需要账号）。

**注意：Jetson 重启后 broker、接收器和网页都不会自动启动**，相机网段的临时地址也会消失。2026-09-27 重启后约 4 小时没有接收数据。重启后按 [jetson_web README](../lab_scale/jetson_web/README.md) 的"完整启动顺序"重新启动。

## 方法与原理

### 方法：Jetson 在系统里的位置

Jetson Orin Nano 有两个网络接口：有线接实验室路由器（`192.168.88.249`，节点和网页都在这个网段），Wi-Fi 接学校网络（用于远程 SSH 进来）。它目前同时承担三件事：MQTT broker、接收器 + SQLite、网页与相机解码，全部在 `lab_scale/jetson_web` 目录里，没有安装成系统服务，重启后要手动启动。

在实验室外看网页的路径是：电脑连学校 Cisco VPN → SSH 到 Jetson 的校园网地址并做端口转发（`ssh -L 8080:192.168.88.249:8080 …`）→ 浏览器打开 `http://localhost:8080`。网页本身始终只绑定实验室有线地址。

### 原理

- **为什么是"临时"网关**。SPEC 要求基础监测不依赖 Jetson（§43），Jetson 的正式角色是后期的边缘计算/机器学习（§4.3）。现在用它只是因为手头有、性能够；broker、接收器和网页最终要迁到 Raspberry Pi，迁移时固件不用改。
- **为什么不用 Tailscale 之类的隧道**。学校不允许在校园网运行第三方 VPN/隧道，所以只用学校自己的 Cisco VPN 加 SSH 端口转发；两者都是加密的，网页端口本身不对校园网或公网开放。
- **为什么网页只绑定实验室地址**。网页无登录、只读，绑定学校 Wi-Fi 地址等于向整个校园网公开传感器数据和相机画面。只绑实验室有线地址，外部访问必须先经过 SSH 认证。
- **为什么要先只读检查网络再操作**。Jetson 的接口名（`enP8p1s0`）、IP 都可能随重启、换网线变化；相机网段的临时地址也会失效。按旧记录直接操作会把命令发错设备，所以交接说明要求先查再动。

详细的历史相机命令解释见 [Jetson 相机网络调试记录](../lab_scale/camera_node/JETSON_NETWORK_DEBUG.md)。

说明原位于 `lab_scale/JETSON_HANDOVER.md`，现统一移动至本目录。
