# Jetson 实验室三节点网页

本目录是临时集成，不替代 SPEC 中 Raspberry Pi 正式网关。使用系统 Python 3 标准库（HTTP + SQLite）；相机可选使用系统 Python GI/GStreamer。无需 npm、pip 或云端资源。

## 当前状态（2026-09-23）

已完成页面、原始日志保存、测量解析、历史曲线、CSV 导出、序号异常记录和服务器端相机预览适配器。**尚未完成三个节点的真实数据端到端接入。**

本机实测：Jetson Orin Nano，Ubuntu 22.04.5 / aarch64。有线 `enP8p1s0` 为 `192.168.88.249/24`，学校 Wi-Fi `wlP1p1s0` 提供优先默认路由。两个节点 `192.168.88.252` / `.251` ping 有回应，MAC 分别匹配交接中的 `44:b1:76:ce:d1:a8` / `44:b1:76:cc:d4:84`。这些地址须在网络变化后重新核对。

仓库固件尚无 MQTT，当前没有 USB 串口设备。因此真实数据库起始为空。未安装或配置 MQTT broker，未改写或烧录 ESP32。相机 `192.168.1.88` 目前路由走学校 Wi-Fi，需先修复有线临时相机网段，再从设备/厂家证据取得真实 URI；不能猜测 RTSP 路径。GStreamer rtspsrc、jpegenc 和 Python GI 已检测到；尚未通过实际视频验收。

## 启动与停止（在 Jetson 终端运行）

```bash
cd ~/Documents/GitHub/hardware_record_tank/lab_scale/jetson_web
python3 server.py --bind 192.168.88.249 --interface enP8p1s0
```

浏览器访问 `http://192.168.88.249:8080`。同实验室 LAN 的电脑可以使用此地址；远端访问仍需从另一台电脑实际验证。只绑定实验室地址，不绑定学校 Wi-Fi，也未开放公网端口。页面是实验室 LAN 只读服务，无用户登录；请勿直接暴露到公网。

终端按 Ctrl+C 停止。默认仅在启动命令持续运行时服务，不自动开机启动。若用 nohup 启动，运行日志放 `data/server.log`，PID 放 `data/server.pid`，停止使用 `kill "$(cat data/server.pid)"`，先核对该 PID 确为本服务。

默认数据文件 `data/measurements.sqlite3`，SQLite WAL 开启。重启保留历史。停服务后备份整个 `data/` 目录，切勿只复制正在写入的主数据库而遗漏 WAL。数据/日志已被本目录 `.gitignore` 忽略。停止服务即可撤销本次运行；本次未修改网络、系统服务或设备。

## 测量接入接口

浏览器端口只读；另一个仅监听 `127.0.0.1:8766` 的本机端口提供 `POST /ingest`。JSON 格式：

```json
{"node_id":"shrimp-node01","line":"<一整行真实的现有固件串口输出>"}
```

接收器是后续 USB/MQTT 桥接的入口，不会主动从 ESP IP 抓取读数。桥接必须发送所有日志行，包括 Node 2 的独立 RX 原始回复行，不能只发最终数值行。桥接须在 HTTP 成功后才确认消费，并明确实现缓冲、重试和溢出记录；本次尚未实现桥接，不能宣称断网缓冲已验收。请勿把测试/回放数据送进运行中的真实数据库，测试使用临时数据库。

每行保存在 `raw_log`，成功和失败测量报告拆成 `measurement`，序号缺口/重复/乱序保存在 `issue`。序号以 node + sensor + boot 分组，重复测量不重复计数，但原始行仍保存。当前同 boot 乱序旧值不覆盖最新卡片；网络积压与跨 boot 迟到记录仍需在接入桥接时进一步验证。缺口事件是接收时观察值，迟到补齐不会抹去原始事件。

现有固件无可信 sample UTC，所以 `sample_timestamp_utc` 为 NULL，`clock_sync_status=UNSYNCED`；`received_utc` 是 Jetson 系统时钟，不是采样时间，也不是已验证的准确 UTC。保留原日志中的 cycle、请求/接收 uptime、raw、K、补偿和校准信息。未来固件同步后须升级解析并验证，不能只把 UTC 标签改成 SYNCED。

15 秒无新报告显示 STALE。通信错误清空当前值而不沿用上次正常值。配置异常的零值原样保存并带 QC；异常 QC 不绘制为正常曲线。UNVALIDATED 曲线用黄色展示。历史横轴明确使用网关接收 UTC。曲线最多显示最近 300 条；CSV 导出全体测量及对应报告原文，额外 RX/健康日志保存在 SQLite。CSV 的潜在公式字段加前导单引号，数据库原文不变。

## 实验标识与相机配置

启动前在本机未跟踪的 `.env` 中按 `.env.example` 填写；不要将密码写入聊天或 Git。若使用 shell 加载，文件内容需采用合法 shell 引号：

```bash
set -a
. ./.env
set +a
python3 server.py --bind 192.168.88.249 --interface enP8p1s0
```

`TANK_ID` 和 `EXPERIMENT_ID` 尚未确定时保持空，网页会提示，不虚构实验标识。`SENSOR_LOCATION` 是此临时台架的可选公共位置描述；不同探头位置须在后续正式配置中逐传感器设置。

`CAMERA_RTSP_URI` 只填写已通过设备 ONVIF 或厂家资料验证的 URI。凭据只留在本机私有环境，网页 API 不返回 URI。后端可解码为 JPEG，浏览器每约 2 秒取一帧，属于低帧率预览；不提供音频，不录制视频。超过 10 秒无帧不显示旧画面，失败自动重试。实际编码兼容性、恢复和长期资源占用尚待真实相机测试。

数据暂不自动删除；保留时长和磁盘预算待用户确定，尚无磁盘限额和自动备份，不应宣称已完成无人值守长期部署。数据库写入失败返回 503，发送方必须重试。

## 验证

```bash
python3 -m unittest -v
```

测试使用临时 SQLite，不向真实数据库注入模拟测量。覆盖 UTC 不伪造、原文保留、错误/缺失值、Node 2 配置异常零值、序号缺口/重复/乱序/重启、节点身份校验、公共 API 只读和未接入视频状态。

待完成验收：确认实际烧录版本与接入方式；一条真实传感器链路后扩展第二节点；相机网络与真实视频；ESP 重启及 Wi-Fi/MQTT 中断恢复；跨电脑访问；学校网断开时本地运行；时钟可信度与缓冲/磁盘策略。

## VS Code 调试（在 Jetson 上）

用 VS Code 打开仓库根目录 `~/Documents/GitHub/hardware_record_tank`，不要只打开某个 Python 文件。根目录 `.vscode/` 已配置 Microsoft Python / Python Debugger，使用系统 `/usr/bin/python3`，可访问系统安装的 GI/GStreamer。

1. 打开 `lab_scale/jetson_web/server.py`，点击行号左侧设置断点。
2. 在「运行和调试」中选择 **Jetson 网页：本机调试**，按 F5。
3. 打开 `http://127.0.0.1:8081` 查看调试页面。调试接收端口是 `127.0.0.1:8767`。
4. Shift+F5 停止调试。F10 单步，F11 进入函数，F5 继续。
5. 选择 **Jetson 网页：调试单元测试** 可在解析/存储逻辑中设置断点，通过临时测试数据触发；测试不写真实数据库。

调试使用 `data/debug/measurements.sqlite3`，独立于 8080 的运行数据库。默认相机 URI 和实验标识清空，避免无意连接相机或写入真实实验。当前测试页面只在 Jetson 本机可见；若需另一台实验室电脑调试，将 launch.json 中 bind 改为现场核对后的实验室有线地址，并保持 8081/8767 独立端口。ESP32 固件的编译/烧录环境尚未配置，以上配置针对网页后端。

调试配置参考：https://code.visualstudio.com/docs/python/debugging
