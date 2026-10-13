# Node-2 — EC 和 pH 校准步骤

2026-10-13 起，固件 `node02-mqtt-0.2` 可以接收校准命令。校准有两种做法，用的是同一套代码、同一张命令白名单：一是在控制页 `/control` 上用 "EC / 盐度" 和 "pH" 两张卡片，二是在 Jetson 终端运行 `lab_scale/jetson_web/ezo_cal.py`。每一步都会自动记进 `operator_event`，内容包括操作人、UTC 时间、命令（即校准类型和数值）、你填写的标准液说明，以及校准前后的读数和 EZO 状态（SPEC §41）。

> **必须先烧录 0.2 固件**，否则节点收不到命令，网页上会显示"节点没有回复"。烧录步骤见下面第 1 节。

## 0. 需要准备的东西

| 用途 | 东西 | 说明 |
|---|---|---|
| EC（K10 探头） | 12,880 µS/cm 和 150,000 µS/cm 校准液 | Atlas "Conductivity Calibration K 10 Set"。如果当初买的是 Atlas K 10 kit，盒子里本来就有这两瓶，先找找 |
| pH | pH 7.00、4.00、10.00 缓冲液 | 瓶身上要有温度对照表 |
| 冲洗 | 蒸馏水或去离子水、洗瓶 | 每换一种液体之前都要冲洗 |
| 其他 | 干净小杯（每种液体一个）、无绒纸、温度计 | 温度也可以读 DO 探头的数值 |

注意事项：

- 校准液倒进小杯里用，**用过的不要倒回瓶里**。
- pH 探头的玻璃泡**不能擦**，只能用纸轻轻吸干。探头也不能长时间放在空气里干着。

## 1. 第一次使用：部署新固件和网关（只做一次）

所有命令都在 Jetson 终端、仓库根目录下运行。硬件操作都由你来做：Claude 不会直接烧录，只负责核对你贴回来的输出。

1. **拿到新代码**。这次的改动在 GitHub 的 `node2-ezo-calibration` 分支（合并后就在 `main`）：
   ```bash
   git fetch origin && git checkout node2-ezo-calibration && git pull
   ```
2. **给 broker 加权限**。下面这条命令让 Node 2 能订阅自己的命令主题，并让 `pump-operator` 账号可以给它发命令。已有账号的密码不会变。
   ```bash
   python3 lab_scale/jetson_web/prepare_mqtt.py --host 192.168.88.249
   ```
3. **重启两个网关服务**。broker 只在启动时读取权限，所以一定要重启。命令见 [lab_scale/README.md 第 4 步](../README.md#烧录一块新板子的完整流程)。
4. **真实编译**：
   ```bash
   python3 lab_scale/jetson_web/build_node1.py --node 2
   ```
   本地已经有 `arduino_secrets.h` 就不用重新配置；没有的话先运行 `configure_node1.py --node 2 --wifi-from-node1`。
5. **备份并烧录**。把 Node 2 的 USB 从电源适配器换插到 Jetson 上，然后按 [lab_scale/README.md 第 1、2、5 步](../README.md#烧录一块新板子的完整流程)操作：
   - 先读 MAC，必须是 `44:B1:76:CC:D4:84`；
   - 回读 16 MB 备份，存到 `.codex-build/node2-backup/`；
   - 烧录 `.codex-build/node2-configured/output`；
   - 烧完单独按一次 RST。
6. **核对**。在监控页或数据库里确认以下几点，再把 USB 插回电源适配器：
   - 出现 `event=BOOT` 和 `firmware=node02-mqtt-0.2`；
   - HEALTH 行里有 `operator_commands=0 command_lost=0`；
   - EC 和 pH 都有读数。

回退方法：用第 5 步的备份执行 `esptool … write-flash 0 …`。旧网关和旧固件之间不会互相影响，只是没有校准功能。

## 2. 每次校准都要遵守的规则

1. **一次只校准一支探头**。控制页同一时间只执行一条命令，两张卡片会轮流处理。
2. **每一点都要等读数稳定**。卡片中间的"最近约 1 分钟波动"就是用来判断这个的：
   - EC：Atlas 的标准是 ±3 % 以内（100 µS/cm 以上时）。
   - pH：参考值是 1 分钟内变化 ≤ 0.02。这是经验值，不是厂家要求。
3. **温度**。固件里的温度补偿保持 Atlas 出厂的 25 °C，不会去改。
   - 先测校准液的温度。
   - 校准数值填**瓶身温度表上对应这个温度的值**；液温正好 25 °C 时就填瓶上的标称值。Atlas 的 EZO-EC 手册是这样要求的；pH 缓冲液同理。
   - 把实测温度写进备注。
4. **每一步都要写备注**。内容是：标准液名称、批号、液温，例如 `Atlas 12,880 µS/cm, lot 1234, 22.4 °C`。不写备注，网页和终端都不会发送命令。
5. 每一步发出后**大约需要 15 秒**：节点会重新读取 K 和校准状态，网关再追加查询一次。结果会显示校准前的读数和校准后的状态。

## 3. EC（K10 探头）

顺序：**K=10 → 干校准 → 低点 12,880 → 高点 150,000**。网关会检查顺序，顺序不对的命令不会发出。

| 步骤 | 探头放在哪里 | 网页按钮 | 终端命令 |
|---|---|---|---|
| 1 | 不限 | 1 · 设 K=10 | `python3 lab_scale/jetson_web/ezo_cal.py ec k10 --note "K10 probe"` |
| 2 | **擦干，放在空气里**，读数稳定（应接近 0） | 2 · 干校准 | `… ec dry --note "dry, in air"` |
| 3 | 12,880 µS/cm 校准液里，轻轻晃动赶掉气泡，等 1–2 分钟 | 3 · 低点（填当前液温下的数值） | `… ec low 12880 --note "Atlas 12,880, lot …, 22.4 °C"` |
| 4 | 先冲洗吸干，再放进 150,000 µS/cm 校准液，等稳定 | 4 · 高点 | `… ec high 150000 --note "Atlas 150,000, lot …, 22.4 °C"` |

- 第 1 步只需要做一次。设好以后监控页上的 QC 会从 `CONFIGURATION_MISMATCH` 变成 `COMPENSATION_MISSING`。改 K 之后到校准完成之前，读数显示 0 或者不准是正常的。
- 第 3 步之后读数**不会变**，要做完第 4 步才生效。完成后校准状态显示 `?CAL,2`（Atlas 把干校准也算一点：`?CAL,1` = 干 + 1 种液，`?CAL,2` = 干 + 低 + 高）。
- **验收**：把探头冲洗后放回 12,880 液里，读数应该接近瓶上的值。这个读数会作为验收记录，最好也写进备注或实验记录。
- 盐度（PSU）是 EZO 根据电导率算出来的，用的是 25 °C 的设定值。只要还没有接入实测水温（也就是 QC 仍是 `COMPENSATION_MISSING`），盐度就会带有温度误差。

## 4. pH（Industrial Gen3，无温度探头）

顺序：**中点 7.00 → 低点 4.00 → 高点 10.00**。中点必须第一个做，并且做中点会**清除**之前的所有校准点。

| 步骤 | 缓冲液 | 网页按钮 | 终端命令 |
|---|---|---|---|
| 1 | pH 7.00 | 1 · 中点 | `python3 lab_scale/jetson_web/ezo_cal.py ph mid 7.00 --note "pH 7.00, lot …, 22.4 °C"` |
| 2 | pH 4.00 | 2 · 低点 | `… ph low 4.00 --note "…"` |
| 3 | pH 10.00 | 3 · 高点 | `… ph high 10.00 --note "…"` |

- 每换一种缓冲液都要先冲洗、吸干。
- 做完后点"查询 Slope,?"（终端是 `… ph query slope`），返回 `?Slope,酸侧%,碱侧%,零点mV`。Atlas 的 EZO-pH 手册说：新探头的斜率应该**大于 95 %**，零点在 **−5 到 +5 mV** 之间；零点超过 10 mV 时性能会明显下降。斜率偏低说明需要清洗或更换探头。
- **盐水提醒**：pH 4/7/10 是低离子强度的 NBS 缓冲液，放进 20–25 ppt 海水后，读数相对海水 pH 标度可能有系统偏差（量级 NOT VERIFIED）。用于论文的 pH 数据需要另外和参考方法对照。

## 5. 其他操作

- **只看状态**：`ezo_cal.py ec show`。会显示最新读数、校准状态、K，以及最近 15 个读数的波动。
- **持续看读数**：`ezo_cal.py ph watch`，每 4 秒刷新一次，按 Ctrl+C 退出。
- **查询**：`ezo_cal.py ec query cal|k|t`、`ezo_cal.py ph query cal|slope|t`。
- **清除校准**：网页上点红色的"清除校准"，或运行 `ezo_cal.py ph clear --note "原因"`。清除后要从头重新校准。
- **单点 EC 校准**（备用，只能在终端做）：`ezo_cal.py ec single 12880 --note …`，前提是已经做过干校准。
- 所有操作记录都在控制页底部的"最近操作"里，备注列就是校准前后的数据。

## 6. 网页或终端返回的结果

| 结果 | 意思 | 怎么办 |
|---|---|---|
| `OK` | EZO 接受了 | 看校准后状态 |
| `ER` | EZO 拒绝了（`*ER`） | 检查数值和顺序；探头和通道都还正常 |
| `K_NOT_10` / `DRY_FIRST` / `LOW_FIRST` / `MID_FIRST` | 顺序不对，**命令没有发出** | 按提示先做前面的步骤 |
| `NO_REPLY` | 20 秒内节点没有回复 | Node 2 是否在线？是否已经烧录 0.2？先用 `show` 确认，不要连续重发 |
| `SENSOR_NOT_READY` | 这一路还在初始化 | 等几秒再试 |
| `ANOTHER_COMMAND_PENDING` | 上一条命令还没完成 | 等它完成 |
| `*RS` / `REPLY_TIMEOUT` 等 | EZO 重启或通信超时，命令已取消 | 等读数恢复以后，重做这一步 |

## 7. 多久校准一次

Atlas 的手册没有规定校准周期，SPEC 也没有。下面是经验建议，不是厂家要求：

- pH 每 2–4 周做一次；
- EC 每月做一次；
- 读数可疑、清洗或更换探头、改了线缆长度之后都要重做。

每次都按上面的顺序完整做一遍。

## 来源

- Atlas EZO-EC 手册（v54）：K 命令、`Cal,dry` → `Cal,low` → `Cal,high` 的顺序、不在 25 °C 附近时按瓶身温度表取值、K 10 探头的量程 10 µS – 1 S。https://cdn.sparkfun.com/assets/d/9/1/8/6/EC_EZO_Datasheet_v54.pdf
- Atlas EZO-pH 手册：中点必须第一个并且会清除其他点、`Slope,?` 的含义和新探头的判断标准。https://cdn.robotshop.com/media/A/Atl/RB-Atl-266/pdf/atlas_scientific_ezo_complete_ph_datasheet.pdf
- Atlas K 10 kit 的内容（12,880 和 150,000 µS 两瓶校准液）：https://atlas-scientific.com/kits/conductivity-k-10-kit/
