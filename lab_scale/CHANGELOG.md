# 归档记录 — 2026-09-22 目录归档

## 本次变更

用户指定仓库 `LihongYang99/hardware_record_tank`，要求区分 lab_scale、未来 tank_scale，以及 Node-1、Node-2、camera_node。
已在本地增加独立节点目录、原脚本副本、空密码模板、主机测试、节点 README 和分主题历史摘要。
根 README 更新当前进度与过期的 100 L 描述；SPEC/GOAL 及既有工程文件未在本次变更。
Node-2 IP 记录为用户本次确认的 192.168.88.251，不改固件 DHCP 行为。

## 本次验证

- Node-1 协议主机测试通过（退出码 0）。
- Node-2 严格解析、初始化、双路读取、单路超时及恢复、重启/身份检查、USB 队列模拟测试通过；启用 AddressSanitizer / UndefinedBehaviorSanitizer。
- `git diff --check` 通过。
- 两套程序的真实 `arduino_secrets.h` 路径均被 Git 忽略；新目录只提供空示例文件。
- `.ino` 和运行时头文件原样复制，未更改采集逻辑；Node-2 主机测试仅调整相对 include 路径。
- 本次未向 ESP32 上传、未修改传感器设置，也未重新进行实物采集或 Arduino 固件编译。之前编译和用户实测不冒充本次新硬件测试。

## GitHub 状态

早先 GitHub 接口返回 404，本机 Git 无可用 HTTPS 登录凭据，首次整理只保存在本地。
用户要求重试后，GitHub 连接已能读取该仓库并返回写入权限。远端已有单行 README 和空白 lab_scale/node-1 占位文件。
随后创建远程 tree 时仍返回 403，因此没有远程提交成功。
用户提供 GitHub Desktop 本地仓库路径后，改为整理到 Documents/GitHub/hardware_record_tank，供用户在 Desktop 查看、提交和推送。
整理范围包含 lab_scale、tank_scale、README、.gitignore、SPEC、GOAL、AGENTS、DECISIONS 以及 docs/phase1 既有规划资料；原样保留规划内容并在总 README 区分实测与规划。不复制 output 演示稿版本、真实密码或编译缓存。

## 目录修正

按用户澄清取消 sessions 目录，历史记录移入各节点 PROGRESS.md，硬件、接线、通信拆成独立文件；firmware 目录改为 script。保留代码及历史信息。

# 2026-09-26 至 09-27 — 局域网实时链路（Jetson 临时网关）

## 变更

- Node-1 新增并烧录 `DO_ORP_MQTT`；Node-2 新增并烧录 `Atlas_EC_pH_MQTT`（传感器代码与旧版逐字节相同）。旧版程序保留；烧录前 16 MB flash 备份在 `.codex-build/node*-backup/`。
- 固件修正：MQTT 写缓冲 256 → 1536 B；板身份改读 eFuse MAC，身份不符时 USB 提示 `WRONG_BOARD`。
- Jetson：broker 每节点独立账号与 ACL；接收器支持两个节点并按主题校验身份；`run_mqtt.py` 响应 SIGTERM；`configure_node1.py` / `build_node1.py` 支持 `--node 2`。
- 相机：`camera_onvif.py` 通过 ONVIF 取 RTSP 地址存入私密 `.env`；网页相机管道改为明确的 H.264 链路（修复 Jetson 硬件解码器接不上导致无画面）。
- 网页新增英文页 `/en`；接口新增 `camera.code`。
- 根 README、lab_scale README、jetson_web README 与各节点/相机 PROGRESS 更新到当前状态，并记录容量与限制条件。

## 验证

- 网页/MQTT 自动测试 14 项通过（含 Node 2 路由、冒充拒收、ACL 隔离）。
- 实板：两个节点数据实时入库，无拒收、无序号缺口；Jetson 接收端中断 25 s 后补发无缺口；Node 1 换电源重启后自动恢复。
- 相机：IP↔MAC 核对；GStreamer 软/硬件解码均出画面；网页 API 与日志不含视频地址。
- 未验证：UTC、断电持久缓存、路由器/Wi-Fi 中断、长时间运行、校准。

# 2026-09-27 — 新增 pump-node-1（旁路蠕动泵，总 Node 4）

## 变更

- 用户已购买 Atlas EZO-PMP，决定单独一块 ESP32、UART 通信；记录为 DECISION 048（036 标为已取代，OPEN-09 暂定解决），SPEC 升为 0.3（§5 NODE 04、§31）。Phase-1 的 WIRING/BYPASS 文档（中英文）加注指向 048。
- 新目录 `lab_scale/pump-node-1/`：README（含方法与原理）、HARDWARE、WIRING、COMMUNICATION、PROGRESS、固件 `script/PMP_MQTT/`、主机测试 `tests/`。`Telemetry.h`、`BenchLog.h` 从 Node-2 逐字节复制。
- Jetson：node04 加入 `prepare_mqtt.py`、`mqtt_receiver.py`、`server.py`、`configure_node1.py`、`build_node1.py`；中英文网页新增"04 / 旁路泵"面板（运行中/已停止、电机电压、累计体积，只读）。

## 验证

- 泵主机测试通过（g++，ASan/UBSan，无警告）；Python 测试 16 项通过。
- ESP32 编译：`--check` 通过；填入虚拟 MAC 的完整编译 912,103 B（69%）。未烧录，未接实物。

# 2026-09-27 傍晚 — pump-node-1 烧录与操作控制

- 泵节点 ESP32（MAC 7C:4F:AD:B5:33:38）备份并烧录 0.1；修正控制板电源接线后通信成功；真实日志存 `pump-node-1/SAMPLE_LOG.md`。泵报告未校准时恒定流量上限 54.66 mL/min，原定 80 mL/min 不可行。
- 用户决定自己控制开关和流速：固件 0.2 加 MQTT 操作命令（白名单、去重、NVS 保存设定、默认不转）；Jetson 新增 `pump_ctl.py` 与 `pump-operator` 账号；网页加"设定流量"。DECISION 048 第 4 条同步修改。
- Jetson 14:12 EDT 重启后服务未自启，12:42–16:42 EDT 无数据，已记入 lab_scale README。
- 用户要求网页控制泵：最终方案为单独的登录控制页 `/control`（个人账号、会话 cookie、锁定、只允许启动/停止），监控页保持只读无需登录。`pump_ctl.py` 新增 `web-user` 账号管理与共用的 `execute()`。
- 控制页改为多设备"设备控制台"（设备登记在 `pump_ctl.DEVICES`，接口 `/api/control`），泵命名为泵 1 / Pump 1；中文 `/control`，英文 `/control/en`（共用 `control.js`）。各 README 按 2026-09-27 晚实际状态更新：泵 1 已烧录校准、Node 1/2 经 Type-C 接电源适配器、Jetson 重启后无自启导致约 4 小时数据缺口、相机恢复 LIVE。
- 调试过程入档：pump-node-1 README 新增"调试过程"表（15 项：演示灯、`--check` 体积假象、泵板没上电、欠压拒绝、80 mL/min 超上限、校准被拒、两种校准独立、shell 尖括号、停泵方式、固件复查、设定流量卡片空、控制页三版、中英文、Jetson 无自启）；jetson_web README 新增"泵 1 接入与设备控制页"段（账号/ACL、命令通道、三版控制页、接收器需随参数表重启、测试迭代、服务重启时间）；CLAUDE.md 加"改参数表后两个服务都要重启"。用户 20:21 / 20:28 EDT 重启两服务后设定流量入库、英文控制页生效。
