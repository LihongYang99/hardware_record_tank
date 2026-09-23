# Jetson 设置与工作交接

此目录保存 Jetson Orin 的设置与交接说明。当前任务是在 Jetson 上临时集成 lab_scale 两个 ESP32 节点和相机的网页，不改变正式 Raspberry Pi 网关架构。

## 给 Jetson 上 Codex 的入口

先完整阅读仓库根目录的 `AGENTS.md`、`SPEC.md`、`GOAL.md`，再阅读 [JETSON_HANDOVER.md](JETSON_HANDOVER.md)。

当前网络：有线接实验室局域网，Wi-Fi 接学校网络。请先只读检查真实网卡、地址、路由、软件与固件，不直接套用历史 IP 或无线接口名称。

交接说明包含节点信息、MQTT 缺口、相机已验证与待验证状态、网页需求、执行顺序、安全边界和验收要求。不保存任何密码。

详细的历史相机命令解释见 [Jetson 相机网络调试记录](../lab_scale/camera_node/JETSON_NETWORK_DEBUG.md)。

说明原位于 `lab_scale/JETSON_HANDOVER.md`，现统一移动至本目录。
