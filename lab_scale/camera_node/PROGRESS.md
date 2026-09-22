# Camera — 调试进度

用户已进入 RouterOS WebFig → IP → DHCP Server；待查看 Leases。
之前 Quick Set 无线列表出现两个 ESP32，不代表有线相机一定应出现在该列表。
接 PoE 本身不能解释“找不到 IP”；静态地址、链路或供电都还没有排除。
先确认设备标签、PoE 路径和租约/MAC，再依据厂家资料确认视频接口；不猜默认密码或 RTSP 路径。
只做局域网测试，不需要端口转发或公开摄像机凭据。


## 历史调试记录

用户报告两块 ESP32 和 PoE 相机接同一个路由器，并拟在 Jetson Orin 临时测试可视化。
RouterOS 截图显示两个节点 hostname，随后用户进入 WebFig 的 IP / DHCP Server 页面。
尚未提供 Leases 结果、相机 IP 或厂家型号；不能判断相机链路是否已通。
没有已运行的网站、相机采集脚本或可验证视频流。下一步为识别相机，而不是宣称已完成三路可视化。
