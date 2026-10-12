# Raw_data — 各传感器原始数据

从 Jetson 网关数据库（`lab_scale/jetson_web/data/measurements.sqlite3`）按"节点 / 传感器 / 日期"导出的**原始日志行**。CSV 文件很大，不进 Git（见 `.gitignore`），只有文件夹结构和本说明进 Git。

## 文件夹

| 节点文件夹 | 传感器子文件夹 | 内容 |
|---|---|---|
| `Node-1-ORP-DO/` | `DO_SEN0681/`、`ORP_SEN0709/` | DFRobot 溶解氧、氧化还原电位 |
| `Node-2-pH-Conductivity/` | `EC_ATLAS_EZO/`、`PH_ATLAS_EZO/` | Atlas 电导率（盐度）、pH；含每条 TX/RX 原始收发行 |
| `Pump-1/` | `PUMP_ATLAS_PMP/` | 泵 1 的状态、操作命令和泵的回复 |
| `Pump-2/` | `PUMP2_ATLAS_PMP/` | 泵 2 同上 |
| `Node-6-Turbidity/` | `TURB_SEN0710/` | DFRobot 浊度 |
| `Node-7-Heater/` | `HEATER_RELAY/` | 加热器继电器状态与开关事件 |
| `Node-3-Camera/` | `YYYY-MM-DD/` | 水下相机，每分钟一张 JPEG（见下） |
| 每个节点下的 `node_log/` | — | 不属于某个传感器的节点日志：开机、健康、Wi-Fi |

每个传感器文件夹里一天一个文件：`YYYY-MM-DD.csv`，日期按 **UTC**（美东时间晚 8 点后的数据算到第二天）。

## 列

| 列 | 含义 |
|---|---|
| `raw_id` | 数据库 `raw_log` 的行号，可回查 |
| `received_utc_gateway` | Jetson 收到这一行的时间。**不是采样时间**：节点没有可信时钟（`UTC=UNSYNCED`） |
| `keep` | 1 = 收到时该节点在"长期记录"；0 = 当时没开，数据库里这行会在 12 小时后删除，但已导出的文件不会被删 |
| `line` | 节点发来的原文，一字不改：`raw=` 原始字节、`seq`、`boot_id`、读数、`COMM`、`QC` 都在里面 |

读数的含义和 QC 见 [lab_scale/README.md](../lab_scale/README.md) 第 4 节和各节点的 COMMUNICATION.md。原文不做 Excel 转义；用 Excel 打开时不要让它"自动转换"。整理好的数值表（每分钟一条、带单位）用监控页各传感器的"CSV"按钮导出。

## 相机（Node-3-Camera）

- 网页服务 `server.py` 运行时，每到整分钟把相机当前画面存一张：`Node-3-Camera/<UTC 日期>/<时分秒>Z.jpg`，例如 `2026-10-06/213400Z.jpg`。文件名是 Jetson 解码出这一帧的时间（相机自己的时钟差约 6 个月，不用）。
- 只在视频正常时存（画面 10 秒内更新过）；断线、未配置相机时这一分钟跳过，不存旧画面。
- 子码流 704×576，每张约 36 KB，每天约 51 MB（1,440 张）。
- "Node 3"是台架上对相机的叫法；SPEC 里的 NODE 03 规划给 H₂S 传感器，两者不是一回事。
- 不受控制页"数据记录"开关影响，也不会自动删除。不想存时，启动 `server.py` 加 `--frames-dir ''`。

## 更新

在 Jetson 上（仓库根目录）：

```bash
python3 lab_scale/jetson_web/export_raw.py          # 补上新的日期；今天（UTC）的文件每次都会重写
python3 lab_scale/jetson_web/export_raw.py --all    # 全部重新导出
```

只读数据库，可以在服务运行时执行。已经导完的日期记在 `exported_days.txt`，不再重复写。

2026-10-06 第一次导出：2026-09-26 到 2026-10-06，55 个文件、700,695 行、231 MB，与数据库逐行核对无遗漏、无重复。2026-09-30 14:49 到 2026-10-06 17:15（美东）网关未运行，那段没有数据。
