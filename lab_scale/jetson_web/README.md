# Jetson 实验室三节点网页

本目录是临时集成，不替代 SPEC 中 Raspberry Pi 正式网关。使用系统 Python 3 标准库（HTTP + SQLite）；相机可选使用系统 Python GI/GStreamer。无需 npm、pip 或云端资源。

## 脚本导航：每个文件是干什么的

本目录的 Python 脚本主要在 **Jetson 的终端**运行，不是在 Arduino IDE 中运行。`static/` 中的 JavaScript 则由浏览器自动运行。网页本身使用 Python 标准库；MQTT 还需要 Paho 和 Mosquitto，相机预览需要 GI/GStreamer 及对应解码插件。不要把“网页无需 pip”理解成整套系统不需要依赖。

### 日常运行的脚本

| 文件 | 用途／输入与输出 | 如何使用及注意事项 |
| --- | --- | --- |
| [run_mqtt.py](run_mqtt.py) | 同时启动 Mosquitto broker 和 `mqtt_receiver.py`，让 ESP 的 MQTT 日志进入数据库。读取本地 `data/mqtt/mosquitto.conf`；默认数据库为 `data/measurements.sqlite3`。 | `python3 run_mqtt.py`。日常启动 MQTT 的入口；使用它时不要再重复启动接收器。Ctrl+C 或 SIGTERM 会停止它启动的两个子进程，不会停止单独运行的网页服务。 |
| [mqtt_receiver.py](mqtt_receiver.py) | 订阅两个节点的 `records`、`status` 主题，核对节点身份和传输字段，调用 `server.py` 中的 `Store` 保存原始日志与测量。数据库提交成功后才发应用层 ACK；拒收内容保存在 `mqtt_rejected`。 | 通常由 `run_mqtt.py` 启动。单独排查时可运行 `python3 mqtt_receiver.py`，前提是 broker 已运行且没有另一份接收器。它不负责网页和相机，也不直接读取 USB 串口。 |
| [server.py](server.py) | 提供网页、状态／历史 API、CSV 导出和 SQLite 存储逻辑；后台检查节点网络状态，并把相机 RTSP 解码为 JPEG 供网页查看。另有仅本机可访问的 `/ingest` 接口。 | `python3 server.py --bind 192.168.88.249 --interface enP8p1s0`。相机地址从环境变量 `CAMERA_RTSP_URI` 读取，**不会自动加载 `.env`**。网页服务与 MQTT 接收器必须指向同一个数据库。 |

### 配置与编译辅助脚本

这些脚本不是每天都要运行。它们会生成或更新本地文件，但不会自动烧录 ESP。

| 文件 | 用途／产生的文件 | 什么时候运行 |
| --- | --- | --- |
| [prepare_mqtt.py](prepare_mqtt.py) | 为两个节点和接收器生成 MQTT 账号、密码文件、ACL 和 broker 配置，存入私有的 `data/mqtt/`。已有账号密码会保留，只补缺失账号。 | 首次配置 broker，或核实需要重新生成配置时：`python3 prepare_mqtt.py --host 192.168.88.249`。需要 `mosquitto_passwd`；不会安装或启动 broker。更改地址前先确认 Jetson 实验室网卡地址。 |
| [configure_node1.py](configure_node1.py) | 交互读取实验室 Wi-Fi 配置和本地 MQTT 凭据，生成对应 ESP 程序目录内的 `arduino_secrets.h`。 | 名字虽然是 `node1`，但**支持两个节点**：`python3 configure_node1.py --node 1` 或 `--node 2`。Node 2 可加 `--wifi-from-node1` 复用本机已有 Node 1 Wi-Fi 配置。当前生成的 MQTT 主机地址固定为 `192.168.88.249`；不会修改 ESP 上已烧录的程序。 |
| [build_node1.py](build_node1.py) | 调用本地 Arduino CLI 编译对应 MQTT 固件；暂存源码和编译产物位于仓库根目录的 `.codex-build/`。 | 同样支持 `--node 1` 和 `--node 2`。例如 `python3 build_node1.py --node 2`。需要已配置的 Arduino CLI、ESP32 core 3.3.11 和相关库。`--check` 使用空凭据模板，只检查编译；该产物不能作为实际联网固件烧录。脚本没有上传功能。 |
| [camera_onvif.py](camera_onvif.py) | 向相机发送 ONVIF `GetStreamUri` 查询，取得 RTSP 地址并写入本地 `.env` 的 `CAMERA_RTSP_URI`。不修改相机设置。 | 相机网络可达后运行 `python3 camera_onvif.py`；默认 profile `001`，可用 `--profile` 指定。它只配置地址，不播放视频。`.env` 可能含账号密码，不得提交 GitHub；终端输出也应检查后再分享，目前脱敏没有覆盖 URI 中所有凭据格式。 |

ESP 实际源程序不在本目录：分别在 [Node 1 MQTT 固件](../Node-1/script/DO_ORP_MQTT/) 和 [Node 2 MQTT 固件](../Node-2/script/Atlas_EC_pH_MQTT/)。上述配置／编译脚本只是帮助准备这两个程序。

### 测试脚本

| 文件 | 检查什么 | 运行方式与边界 |
| --- | --- | --- |
| [test_server.py](test_server.py) | 原始记录保存、缺值／错误不变成零、测量去重、同启动周期乱序、节点身份、HTTP 接口和数据库持久化。 | `python3 -m unittest -v test_server`。使用临时数据库和本机临时端口，不向实际 ESP 或相机发送命令；不等于现场链路验收。 |
| [test_mqtt.py](test_mqtt.py) | ACK 在落库后发出、写盘失败不 ACK、重复／错误身份拒收、Node 2 路由、ACL 配置、积压读数过期，以及临时 broker 的收发和重连。 | `python3 -m unittest -v test_mqtt`。需要 Paho、密码工具及集成测试所指定的 `.codex-build/runtime/` broker。当前集成测试使用 Jetson Linux 运行环境，不能假定在未配置依赖的 Mac 上直接通过。 |

以上命令均在本目录运行。运行全部 Python 测试可用 `python3 -m unittest -v`。测试使用临时数据，不要为了测试把模拟记录发进正式数据库。

### 网页文件和私有配置

| 文件／目录 | 用途 |
| --- | --- |
| [static/index.html](static/index.html) / [static/en.html](static/en.html) | 中文／英文网页结构，分别由 `/` 和 `/en` 提供。 |
| [static/app.js](static/app.js) / [static/app_en.js](static/app_en.js) | 浏览器读取状态与历史 API、更新数值／QC／过期提示、绘制曲线、刷新相机图片；不直接连接 ESP 或 MQTT。 |
| [static/style.css](static/style.css) | 两种语言页面的布局、颜色和显示样式。 |
| [.env.example](.env.example) | 私有环境变量的填写模板；实际 `.env` 不提交。修改后需在启动 `server.py` 的终端加载环境，并重启该服务才生效。 |
| `data/` | 运行时数据库、日志、PID 和 MQTT 私有配置；由 `.gitignore` 排除，不是可随意删除的缓存。 |
| `../../.codex-build/` | 本地依赖、编译产物及设备备份等；不随 GitHub 同步，换电脑后需要另外准备。 |

### 最容易混淆的三件事

1. **看数据需要两个服务**：`run_mqtt.py` 负责 MQTT 入库，`server.py` 负责网页／相机；只开网页不会自动从 ESP 的 IP 抓取传感器读数。
2. **配置不等于部署**：`configure_node1.py` 只写配置，`build_node1.py` 只编译；都不会替你烧录 ESP。
3. **联网不等于数据有效**：相机 ping 通不等于视频成功；测量收到也不等于完成校准或 UTC 同步，仍需保留并查看 QC 与时钟状态。

## 当前状态（2026-09-27）

**Node 1、Node 2 和相机都已实时接入。** 中文页 `http://192.168.88.249:8080`，英文页 `http://192.168.88.249:8080/en`（仅实验室局域网）。

实验室外访问：学校 Cisco VPN + `ssh -L 8080:192.168.88.249:8080 lihongyang2026@10.141.48.128`，然后打开 `http://localhost:8080`。详见 [../../jetson_setting/REMOTE_ACCESS.md](../../jetson_setting/REMOTE_ACCESS.md)。

完整启动顺序（Jetson 终端，本目录）：

```bash
sudo ip addr add 192.168.1.200/24 dev enP8p1s0      # 相机网段，每次重启/重插网线后
nohup python3 -u run_mqtt.py > data/mqtt.log 2>&1 & echo $! > data/mqtt.pid
set -a; . ./.env; set +a
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 > data/server.log 2>&1 & echo $! > data/server.pid
# 停止：kill "$(cat data/mqtt.pid)" "$(cat data/server.pid)"
```

下方按日期保留历史记录；较早段落里“尚未接入”等描述已被后面的日期段落取代。

### 2026-09-23 初始状态（历史）

已完成页面、原始日志保存、测量解析、历史曲线、CSV 导出、序号异常记录和服务器端相机预览适配器。当时尚未接入真实数据。

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

## 2026-09-26：Node 1 MQTT 接入准备

新增 `Node-1/script/DO_ORP_MQTT/` 独立固件，原固件保留；板子尚未烧录。完整限制见该目录 README。UTC / 物理采集 / 断电缓存未宣称完成。

本地 `.codex-build/runtime/` 解包 Ubuntu Mosquitto 2.0.11、Paho 1.5.1 及依赖；未安装系统服务、未启用开机启动。`data/mqtt/` 保存未跟踪的密码、ACL、broker 配置。配置只监听 loopback 与核对后的实验室有线 IP，不监听学校网；端口 1883，使用独立随机凭据与每节点 topic ACL。本实验 LAN 的 MQTT TCP 未加 TLS，正式安全部署另行设计。

当前界面在 8081 使用调试数据库时，在 **Jetson 的另一个 VS Code 终端**运行：

```bash
cd ~/Documents/GitHub/hardware_record_tank/lab_scale/jetson_web
python3 run_mqtt.py --db data/debug/measurements.sqlite3
```

也可选择 VS Code「Terminal → Run Task → MQTT：接收至网页调试数据库」。Ctrl+C 停止 broker 和接收器。若运行网页使用默认真实数据库，则接收器也使用默认 `python3 run_mqtt.py`；两个服务必须指向同一个 SQLite 文件，不能一边指向 debug 一边指向真实库。调试库尚未写入模拟数据；自动测试始终使用临时目录。

接收器要求消息身份一致、无重复键、合法传输序号；不合格消息原文存 `mqtt_rejected` 且不发应用 ACK。合格消息在 `Store.ingest` 提交 SQLite 后发送应用 ACK。Paho 1.5.1 本身的 MQTT PUBACK 会早于 callback，所以不能把 MQTT PUBACK 当成落库确认；本项目明确使用第二层应用 ACK。记录重复时保留原日志，测量唯一键去重。

`mqtt_status` 保存 broker 的 online/offline 状态及接收时间，目前页面仍主要按实际记录过期时间判断数据状态。`transport_age_ms` 计入 STALE 判定，buffered 不是正常实时读数；它不包括 broker 内等待时间，离线 UTC 与严格端到端采样年龄验证尚待完成。

配置 Wi-Fi（只在本机终端输入密码，不写聊天）：

```bash
python3 configure_node1.py
```

自动测试：`python3 -m unittest discover -s lab_scale/jetson_web -v`（仓库根目录运行）。包含临时 broker、临时数据库、断开接收器后重连、ACK 必须在落库之后、写盘失败无 ACK、重复键/错节点拒绝、补发旧值 STALE 等。传感器解析使用既有 C++ 协议回归测试。

协议依据：[Arduino MQTT](https://github.com/256dpi/arduino-mqtt)、[Mosquitto 配置](https://mosquitto.org/man/mosquitto-conf-5.html)。

## 2026-09-26：Node 1 实时数据已接通

Node 1 已烧录 MQTT 固件，DO / 饱和度 / 温度 / ORP 实时写入 `data/measurements.sqlite3` 并显示在网页。后台运行方式（Jetson 终端，本目录）：

```bash
nohup python3 -u run_mqtt.py > data/mqtt.log 2>&1 & echo $! > data/mqtt.pid
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 > data/server.log 2>&1 & echo $! > data/server.pid
# 停止：
kill "$(cat data/mqtt.pid)" "$(cat data/server.pid)"
```

`run_mqtt.py` 收到 `kill`（SIGTERM）时会同时停止 broker 与接收器。两者都不会开机自启；Jetson 重启后需重新运行。Node 2 与相机尚未接入。

Node 1 已改由 USB 充电头供电，不再接 Jetson；Jetson USB 现接 Node 2（`/dev/ttyACM0`）。

### Jetson 端容量与限制（2026-09-26 实测/估算）

| 项目 | 数值 | 说明 |
|---|---|---|
| 单条上限 | 8,192 B | broker `message_size_limit` 与接收器上限一致，超出拒收 |
| Broker 离线排队 | `max_queued_messages 1000`，持久化每 10 s 写盘 | 仅对订阅会话有效；本项目接收器用 clean session，主要靠 ESP 端重发 |
| 数据库占用 | 603 条原始行 + 940 条测量 ≈ 1,187,840 B，约 2 KB/原始行（含测量行和索引） | 数据量还小，估算偏粗 |
| Node 1 数据量估算 | 0.80 条/s × 86,400 ≈ 69,000 条/天 ≈ **100–140 MB/天** | 估算，未长时间验证；加入 Node 2 会增加 |
| 磁盘 | 根分区可用约 77.8 GB / 124 GB | 按上面估算够用数月以上，但**没有自动清理、限额或备份** |
| STALE 判定 | 最后一条记录（加上传输延迟）超过 15 s | |
| 网页曲线 | 每个参数最近 300 个点 | CSV 导出全部 |
| 自启动 | 无 | Jetson 重启、断电后需手动运行上面两条命令 |

固件端的容量限制见 [../Node-1/script/DO_ORP_MQTT/README.md](../Node-1/script/DO_ORP_MQTT/README.md#容量与限制条件)。

## 2026-09-27：Node 2 接入

Node 2 已烧录 `Atlas_EC_pH_MQTT`，与 Node 1 共用同一个 broker、接收器和数据库。接收器按主题区分节点（`shrimp/lab/<node>/records`），记录中的 `node_id` 必须与主题一致，否则存入 `mqtt_rejected` 且不回 ACK。每个节点有独立 broker 账号，ACL 只允许它写自己的主题。

- `prepare_mqtt.py` 再次运行时保留已有密码，只补缺少的账号（已烧进节点的密码不能变）。
- `configure_node1.py` 与 `build_node1.py` 增加 `--node 2`；`--wifi-from-node1` 复用 Node 1 的 Wi-Fi 设置且不显示密码。
- 两个节点合计约 2.5 条/s，按前面的每行约 2 KB 估算，数据库约 **200–450 MB/天**（粗估，Node 2 EC 恢复后会更多）。
- 自动测试 14 项（新增 Node 2 按主题路由、冒充其他节点被拒、ACL 隔离）。

## 2026-09-27：相机视频接入

相机（`192.168.1.88`，有线接路由器）画面已显示在网页。

1. **网络（每次 Jetson 重启或重插网线后都要做，Jetson 终端）**：`sudo ip addr add 192.168.1.200/24 dev enP8p1s0`。撤销：`sudo ip addr del 192.168.1.200/24 dev enP8p1s0`。
2. **视频地址**：`python3 camera_onvif.py` 通过 ONVIF 向相机要子码流（profile `001`）地址，写入 `.env`（0600，Git 忽略，不打印）。`--profile 000` 为 1920×1080 主码流。
3. **启动网页时加载 `.env`**：

```bash
set -a; . ./.env; set +a
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 > data/server.log 2>&1 & echo $! > data/server.pid
```

相机管道改为明确的 H.264 链路：`uridecodebin` 在 Jetson 上会自动选硬件解码器，其 NVMM 输出接不上 `videoconvert`，导致一直无画面。

相机容量与限制：

| 项目 | 数值 / 说明 |
|---|---|
| 预览 | 子码流 704×576 H.264（相机上限 25 fps、1536 kbps），服务端转 5 帧/s JPEG（约 32 KB/帧），浏览器约每 2 s 取一帧 |
| 首帧时间 | 约 0.9 s |
| 录像 | **无**，不占磁盘 |
| 时间 | 相机时钟差约 6 个月，只用 Jetson 取帧时间 |
| 编码假设 | 只支持 H.264；相机改为 H.265 后需要改管道 |
| 安全 | 相机允许匿名 ONVIF 查询并返回带账号字段的 RTSP 地址；网页 API/日志不返回地址 |

## 2026-09-27：英文页面

`http://192.168.88.249:8080/en`：给外国访客看的全英文页面（`static/en.html` + `static/app_en.js`，共用 `style.css` 和同一套 API）。显示内容、QC 规则和“未校准 / UTC 未同步”提示与中文页一致，另加一段英文系统说明。两个页面右上角可以互相切换。接口新增语言无关的 `camera.code`（`LIVE` / `CONNECTING` / `RETRYING` / `NOT_CONFIGURED` / `NO_GSTREAMER`），英文页据此显示相机状态；传感器名称按 `sensor/parameter` 在前端翻译。
