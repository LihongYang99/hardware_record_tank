# Camera — 网络与通信

- 相机 IP：**NOT VERIFIED**；没有查到可确认的地址。
- MAC、登录账号、准确 RTSP URL：**NOT VERIFIED**；不猜默认账号或流地址。
- [商品页](https://www.amazon.com/dp/B07G857V5G?th=1) 标称支持 RTSP、ONVIF、DHCP、NTP；本机是否启用及互通性 **NOT VERIFIED**。这不是 Wi-Fi 相机。
- 下一步按实物 MAC 核对 RouterOS DHCP Leases；没有租约不等于没有 IP，仍需核对厂家静态地址/发现方式。PoE 注入器型号不能用于推算相机 IP。
- 标称 NTP 支持不等于 UTC 已同步；离线局域网仍需可信的本地时间源。编码格式、实际帧率、视频时间戳及掉线恢复待验证。
- 当前采集脚本：**尚未建立**；没有已验证的画面、录像或网页嵌入。
- 用户拟用 Jetson Orin 进行临时测试，不改变正式基础平台不依赖 Jetson 的要求。
