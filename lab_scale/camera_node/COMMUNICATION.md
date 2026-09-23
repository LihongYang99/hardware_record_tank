# Camera — 网络与通信

- 相机目标 IP：`192.168.1.88`（实物标签）；2026-09-22 用户报告修正 Jetson 附加地址后 ping 有回应，成功原始输出尚未归档。
- 候选相机 MAC：`00:12:34:C6:67:04`（RouterOS ether5 动态学习，用户确认直连相机）；最终 IP→MAC 对照待验证。相机登录、准确 RTSP URL：**NOT VERIFIED**；凭据不入库。
- [商品页](https://www.amazon.com/dp/B07G857V5G?th=1) 标称支持 RTSP、ONVIF、DHCP、NTP；本机是否启用及互通性 **NOT VERIFIED**。这不是 Wi-Fi 相机。
- 没有 DHCP 租约不等于没有 IP。本次使用标签地址调试；Jetson 临时附加 `192.168.1.200/24`，保留原 LAN 地址。命令及撤销见 [JETSON_NETWORK_DEBUG.md](JETSON_NETWORK_DEBUG.md)。下一步保存邻居表输出核对 MAC，不由 PoE 注入器型号推算相机 IP。
- 标称 NTP 支持不等于 UTC 已同步；离线局域网仍需可信的本地时间源。编码格式、实际帧率、视频时间戳及掉线恢复待验证。
- 当前采集脚本：**尚未建立**；没有已验证的画面、录像或网页嵌入。
- 用户拟用 Jetson Orin 进行临时测试，不改变正式基础平台不依赖 Jetson 的要求。
