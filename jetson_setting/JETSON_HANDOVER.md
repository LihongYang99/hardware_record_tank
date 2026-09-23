# Handover：Jetson Orin 上的三节点局域网监控网页

交接日期：2026-09-23。写给运行在 Jetson 上的 Codex。

## 用户的需求与授权范围

我要在现有 Jetson 上做一个 **lab_scale 临时集成网页**，同时查看 Node 1、Node 2 的水质读数和一台水下相机的画面，并保存传感器历史数据。希望其他同局域网电脑也能通过浏览器访问。

用户口语中称设备为“Jetson Nano / Orin”，已确认指同一台设备；准确 SKU、内存、JetPack 和可用资源请在本机检查，不能仅根据称呼假设。此前系统截图是 Ubuntu jammy/ARM64，仍以当前本机信息为准。

当前连接由用户描述为：**Jetson 有线连接实验室局域网，Wi-Fi 连接学校网络以使用互联网/GPT**。实验室路由器承载两个 ESP 和相机；不是要求给三个节点接学校网。

这次先做 Jetson 实验演示，不把正式架构悄悄改成依赖 Jetson。仓库 SPEC 的正式主链路仍是 Sensor → ESP32 → UTC → Wi-Fi/MQTT → Raspberry Pi → database → dashboard。设计应便于之后迁移到 Raspberry Pi。

## 先读项目，再行动

仓库：https://github.com/LihongYang99/hardware_record_tank

1. 定位 Jetson 本地 checkout；没有则取得仓库。不要把 Mac 上的绝对路径当成 Jetson 路径。
2. 完整阅读本仓库 `AGENTS.md`、`SPEC.md`、`GOAL.md`，并检查下级目录指令。缺失或要求冲突时停止并说明。
3. 检查 git 状态，保留已有改动，不覆盖固件、秘密文件或用户工作。
4. 阅读 `lab_scale/Node-1/`、`lab_scale/Node-2/`、`lab_scale/camera_node/`，特别是固件源码、COMMUNICATION.md 和相机 JETSON_NETWORK_DEBUG.md。

用户此前已要求编写三节点网页；本说明是继续此任务的交接，不授权校准探头、改接线、重置相机/路由器、开放公网端口或自动烧录设备。

## 三个节点：已知状态

| 节点 | 标识与硬件 | 采集与传输现状 |
|---|---|---|
| Node 1 | `shrimp-node01`，ESP32-S3；DFRobot DO SEN0681、ORP SEN0709 | 独立 RS485/Modbus 链路；约每 4 s 同轮轮询；成功读过 DO、饱和度、温度、ORP。仓库程序只有 USB 串口输出和 Wi-Fi 连接，没有 MQTT/HTTP 测量接口 |
| Node 2 | `shrimp-node02`，同款 ESP32-S3；Atlas EZO EC + pH，各通过 ISCCB-2，TTL UART | 约每 4 s 读取；仓库启动日志明确 `transport=USB_ONLY mqtt=NOT_IMPLEMENTED`；Wi-Fi 在线不等于已发送读数 |
| Camera | Barlus，实物标签 `IPC5MPIR-PBX10`，有线 IP 相机 | 标签目标 IP `192.168.1.88`；已见 ping 成功和 HTTP Web Viewer；视频尚未验证 |

### IP 与身份：历史信息，不要硬编码成当前事实

- 路由器：`192.168.88.1/24`，MikroTik hAP ax3。
- Node 1：历史日志 `192.168.88.252`，MAC `44:B1:76:CE:D1:A8`。
- Node 2：用户曾确认 `192.168.88.251`，MAC `44:B1:76:CC:D4:84`。
- 用户表示已做 DHCP 静态租约；仍需核对当前租约/MAC 或当前串口日志，不只靠 IP 判断节点身份。
- Jetson 以前通过实验室 Wi-Fi 获取 `192.168.88.254`；**现在改成有线接实验室，地址和网卡名称必须重新检查**。
- 相机 ether5 动态学习 MAC 为 `00:12:34:C6:67:04`；还需在 Jetson 用邻居表核对 IP/MAC。

### 数据质量不能“美化”

- 两份仓库固件均未实现 UTC 同步，日志 `UTC=UNSYNCED`；不是精准同步完成。
- Node 2 曾出现 EC=0、K=1.000、`?CAL,0`、`CONFIGURATION_MISMATCH`；用户购买的链接是 K=10 套件，但实际探头常数与配置需要核对，不能擅自写 K 或把 0 当作有效盐度。
- pH 曾显示 `COMPENSATION_MISSING`、25°C 补偿设置和未校准状态；设置温度不等于实测水温。
- Node 1 `QC=UNVALIDATED` 不等于测量已做科学验证。
- 保留 raw、QC、node/sensor ID、boot_id、seq、cycle、请求/接收 uptime、单位和时钟状态。缺失/错误值不能填成零。

## 网络：先核对双网卡，不要照抄旧配置

先运行只读诊断：

```bash
uname -m
cat /etc/os-release
ip -br -4 addr
ip -4 route
ip route get 192.168.88.1
ip route get 192.168.1.88
command -v gst-launch-1.0 gst-inspect-1.0 ffprobe ffmpeg vlc
```

目标：实验室设备流量走有线；公网流量走学校 Wi-Fi。不要删除默认路由、清空地址、改学校网络或导致 Codex 断联。任何修正先说明具体接口、影响与撤销方法。

相机仍可能在 `192.168.1.0/24`，实验室 LAN 是 `192.168.88.0/24`。此前成功办法是在实验室连接接口上添加一个不冲突的临时地址 `192.168.1.200/24`。当时接口是 `wlP1p1s0`（P 大写），**现在不可把这个旧无线接口作为实验室接口使用**。

确认真实有线接口及地址占用后，可按已验证的思路进行临时配置。以下 `<LAB_ETHERNET_INTERFACE>` 是占位符，必须替换，不能原样执行：

```text
sudo ip addr add 192.168.1.200/24 dev <LAB_ETHERNET_INTERFACE>
ping -c 4 192.168.1.88
ip neigh show 192.168.1.88
```

仅未配置时添加；避免旧接口仍带同网段地址导致路由歧义。撤销对应的临时地址用 `ip addr del`，不使用 `flush`。永久网络配置不是本次默认授权。

## 相机：已经做了什么，下一步做什么

1. 2026-09-22 截图已显示 `ping -c 4 192.168.1.88`：4 发、4 收、0% 丢包（仅该次短测试）。此前文档仅写“用户报告成功”，这份交接补充后续截图证据。
2. Chromium 已能打开 `http://192.168.1.88`，标题 Web Viewer。
3. 页面要求 VideoPlayTool，系统提示没有应用处理 `videoplaytool://`；这是播放器集成问题，不是 HTTP 不通。
4. 不按相机页面指示关闭浏览器安全保护；不依赖旧专有插件，不猜 RTSP 路径。
5. Jetson 已找到 `/usr/bin/gst-launch-1.0`，当时未在 PATH 找到 ffprobe/ffmpeg/vlc。`gst-inspect-1.0 rtspsrc` 与 `gst-inspect-1.0 playbin` 尚未收到结果，优先检查。
6. 从准确型号厂家文档或设备 ONVIF 返回获取真实视频 URI，并记录证据；ONVIF/RTSP 在这台设备上的可用性、端口、编码和账号登录尚未验证。
7. 相机凭据由用户私下输入，不写入 Git、示例 URL、日志或浏览器前端；不要让用户在对话公开密码。
8. 获取可解码的实际画面后，再选择适合浏览器的服务端转换方案。网页能打开、端口开放、ping 有回复都不能算视频验收。

相机目前直接接 router ether5，并由用户报告单独供电；不要称原 PoE 注入器链路已验收。304 相机的长期盐水兼容性存在已记录限制；网络成功不批准 15–25 ppt 长期浸泡。参阅 HARDWARE.md。

## ESP 固件：需要补的不是“存储”，而是网络发送

当前程序入口：

- `lab_scale/Node-1/script/DO_ORP_WiFi/DO_ORP_WiFi.ino`
- `lab_scale/Node-2/script/Atlas_EC_pH_UART/Atlas_EC_pH_UART.ino`

最近检查源码确认只有串口测量日志；不是只有缺网页。先确认实际烧录版本是否与仓库一致，再以保留现有成功版本的方式增加 MQTT 发送。

- 保留传感器引脚、串口参数、解析逻辑、轮询与原始日志；不能为网页随意改传感器配置。
- Node 2 初始化已有输出配置写入；不能把整个驱动描述成完全只读，也不要增加校准/K/补偿写入。
- 网络失败不能阻塞传感器采集；重连、序号、重启身份、掉线/缓冲及溢出策略须明确。
- Jetson 临时作为 MQTT broker/接收端。具体库与服务先检查现有环境再选，不假设已安装。
- 每条测量保存 node_id、sensor_id、parameter、value、unit、QC、seq、boot_id、uptime、raw、时钟状态和网关接收 UTC；按项目规范加入 tank/experiment 标识。
- 未同步的 sample UTC 留空并标明 UNSYNCED，不能用接收时间冒充采样时间。双节点同为 4 s 不代表硬件同步或同一采样瞬间。
- 凭据使用未跟踪的配置/环境文件和空模板。烧录前告诉用户明确目标板与影响，由用户确认；禁止两个板写错程序。

## 网页需求

先做一个可在 Jetson 及实验室其他电脑浏览器访问的页面：

1. 总览：三个节点连接状态、最后数据时间、过期/断线提醒、时间同步状态。
2. Node 1：DO mg/L、饱和度 %、ORP mV、各自温度；明确传感器来源。
3. Node 2：EC µS/cm、盐度 PSU、pH；显示校准/配置/温度补偿 QC，不把无效值显示为正常绿色卡片。
4. 传感器实时更新与历史曲线；保留原始记录，提供数据导出。
5. Camera：实际视频、离线/连接失败状态；未接通显示“视频待验证”，禁止用模拟画面冒充实拍。
6. Jetson 后端集中接收、存储、提供数据接口；浏览器不直接持有相机凭据。

前端可以先用明确标为 DEMO 的测试数据开发，但不能混入真实数据库或宣布三节点已接通。历史数据量、录像是否需要、保留时长和磁盘预算需与用户确认；不要默认持续录像占满磁盘。

## 建议执行顺序和验收

1. 读规范/代码，报告当前硬件、双网卡、路由和软件现状；不要先大规模安装或升级。
2. 验证 Node IP/MAC 和相机连接，确认真实视频协议/URI。
3. 先完成一个真实传感器 → MQTT → Jetson 存储 → 网页的垂直链路，再扩展到第二节点。
4. 集成实际视频，保留独立错误状态；相机失败不影响传感器页面。
5. 验证 ESP 重启、Wi-Fi/MQTT 中断恢复、旧值标记、时钟不同步；不得静默丢失/伪造数据。
6. 测试学校 Wi-Fi/外网不可用时本地网页与采集的行为，明确 UTC 来源及其限制。
7. 提供真实访问地址、启动/停止方法、依赖/版本、配置模板、日志位置、回滚方法和未完成清单。

为 Jetson 临时演示单独使用 `lab_scale/jetson_web/` 保存实现和运行说明（若已有相关目录先核对，避免重复）；修改已有固件时保持每节点 script 结构。不要新建 sessions 目录来堆记录，用户偏好按主题分别记录。

## 之前的软件安装问题

此前 apt 出现 NOSPLIT、证书不受信任及下载包大小异常，导致 arping 未安装。根因未最终确认，不能据此认为 Jetson 没网卡。当前学校 Wi-Fi 上网是否真正可用仍应检查；必要时核对系统时钟/网络认证/代理。不要关闭 TLS 或 APT 签名验证，也不要为了此次测试自动做 JetPack/系统大升级。

## 沟通方式

用户需要中文、分步骤指导。命令旁解释“在哪台机器运行、做什么、是否修改设置、成功看什么”。先给有证据的结论，区分历史值、推测、用户反馈和本机实测；不要把“联网”写成“数据已经发送”，也不要把“ping 通”写成“视频已经成功”。
