# pump-node-1 — 通信与脚本说明

入口：[PMP_MQTT.ino](script/PMP_MQTT/PMP_MQTT.ino)。

| 文件 | 用途 |
|---|---|
| PMP_MQTT.ino | node04、引脚、目标流量、板身份（MAC）检查、Wi-Fi、4000 ms 调度、健康日志 |
| PumpChannel.h | 泵的初始化、每轮查询、流量设定下发、复位检测、超时状态机 |
| PumpParse.h | 严格解析 `?D` / `?PV` / `?TV` / 身份回复，以及 QC 判定 |
| Telemetry.h / BenchLog.h | BenchLog.h 与 Node-2 逐字节相同；Telemetry.h 是 Node-2 那份加上可选的命令主题（`TELEMETRY_COMMAND_TOPIC`，不定义时行为与 Node-2 相同） |
| arduino_secrets.example.h | 空 Wi-Fi/MQTT 模板；真实文件由 `configure_node1.py --node 4` 生成 |

## UART 与命令

UART1，GPIO18 RX / GPIO17 TX，9600 / 8N1（手册出厂默认）。命令 ASCII、`<cr>` 结尾；每条命令等到 `*OK` 才算完成，超时 1.8 s。

启动（以及泵复位、超时之后）依次发送，**全部是查询或输出设置**：

| 命令 | 作用 | 期望回复 |
|---|---|---|
| `C,0`（先发，再静默 2 s） | 关掉出厂默认的每秒连续输出 | `*OK` |
| `*OK,1` | 打开应答码 | `*OK` |
| `i` | 确认是泵而不是其他 EZO 电路 | `?i,PMP,<版本>` |
| `Status` | 上次重启原因（P 掉电 / S 软复位 / B 欠压 / W 看门狗）与 VCC | `?Status,P,3.30` |
| `Cal,?` | 是否校准过 | `?Cal,0`（未校准）… |
| `Dstart,?` | 是否设了上电自动输送（只查不改） | `?Dstart,0` |
| `DC,?` | 当前允许的最大流量 | `?MAXRATE,…` |

每 4 s 一轮：

| 命令 | 作用 |
|---|---|
| `DC,<设定>,*` | **仅当设定 > 0 且需要时**：启动后第一轮、泵复位后、或泵报告停止且距上次下发 ≥60 s。设定来自操作命令（存 NVS），默认 0 |
| `D,?` | 运行状态：`?D,<上次体积或 *>,<1 运行/0 停止>`；同时读 INT 引脚 |
| `PV,?` | 电机电源电压 |
| `TV,?` | 本次上电累计体积（手册：断电不保留） |

## 操作命令（固件 0.2）

主题 `shrimp/lab/shrimp-node04/cmd`，QoS 1，只有 broker 账号 `pump-operator` 能写（`pump_ctl.py` 使用）。载荷：

```text
id=<1–20 位数字> operator=<字母数字 _ . -，≤24> cmd=<命令>
```

| 允许的命令 | 作用 | 对设定的影响 |
|---|---|---|
| `DC,<0.5–105>,*` | 恒定流量启动 | 设定 = 该流量（存 NVS） |
| `X` | 停止（回复 `*DONE,<体积>`） | 设定 = 0 |
| `D,<0.5–1000>` / `D,<mL>,<0.01–1440 分钟>` | 定量 / 按时间输送（校准用） | 设定 = 0 |
| `Cal,<mL>` / `Cal,clear` | 写入 / 清除校准；成功后固件重新初始化，读新的校准状态和最大流量 | 不变 |
| `D,?` `DC,?` `Cal,?` `TV,?` `ATV,?` `PV,?` `Status` `i` | 只读查询 | 不变 |

其他命令一律拒绝（`OPERATOR_REJECTED_INVALID`，原文以十六进制记录），包括 `Factory`、`D,*`、反转、`Dstart`、`Baud`、`I2C`、`Plock`、`Name`、`Sleep`。同一编号只执行一次（`DUPLICATE_ID`）；一次只处理一条（`ANOTHER_COMMAND_PENDING`）；泵没初始化好时拒绝（`PUMP_NOT_READY`）；排队中遇到泵复位则取消（`CANCELLED_PUMP_RESET`），不会稍后补执行。

日志事件：`OPERATOR_ACCEPTED` → `OPERATOR_COMMAND` → `TX` / `RX` → `OPERATOR_DONE result=OK|ER|<超时原因> reply=<泵的回复或拒绝原因>`；设定变化后 `TARGET_SAVED nvs=OK`。定量输送完成时泵主动发 `*DONE,<体积>`，记为 `DISPENSE_DONE`。

除操作命令外，固件自己从不发送写校准、恢复出厂、改上电行为、改波特率/协议等命令。命令白名单由主机测试检查。

## 日志行

每轮一行结果，原始回复原样放在同一行（`raw_D` / `raw_PV` / `raw_TV`），不像 Node-2 那样每条 TX/RX 单独成行，所以记录数少、RAM 缓冲能撑更久：

```text
node_id=shrimp-node04 boot_id=… sensor=PUMP_ATLAS_PMP seq=12 cycle=12 scheduled_uptime_ms=… request_uptime_ms=… rx_uptime_ms=… UTC=UNSYNCED pump_on=1 int_pin=1 motor_V=12.10 total_volume_mL=5.25 target_mL_min=80.00 raw_D=?D,*,1 raw_PV=?PV,12.10 raw_TV=?TV,5.25 calibration_reply=?Cal,0 COMM=OK QC=UNVALIDATED validation=UNVALIDATED
```

（上面是主机测试里模拟泵的输出格式，不是实测数据。）启动命令、`DC` 下发、以及所有非 `*OK` 的应答码和意外行都单独记 `event=TX` / `event=RX raw_hex=…`。

| QC | 含义 |
|---|---|
| `UNVALIDATED` | 通信正常、状态一致；泵未校准，流量未验证 |
| `STATE_MISMATCH` | INT 引脚与 `D,?` 的运行位不一致（蓝线没接、接错或泵异常） |
| `MOTOR_VOLTAGE_LOW` | 控制器报告运行，但电机电压 < 10.8 V（12 V 没接或掉电） |
| `NOT_RUNNING_AS_COMMANDED` | 设定了流量但泵报告停止（例如 `*TOOFAST` 被拒） |
| `COMMUNICATION_ERROR` | 超时、格式不对、身份不对；这一行不带任何数值，不会写成 0 |

事件：`PUMP_RESET`（收到 `*RS`，计入 `pump_resets`）、`PUMP_BOOT_READY`（`*RE`）、`CONTROL_REJECTED`（`DC` 被 `*ER` 拒绝）、`ASYNC_CODE`（`*TOOFAST` `*UV` `*OV` `*DONE` 等）、`READY`、`WRONG_OR_MISSING_PMP_ID`。

## MQTT

与 Node-1/Node-2 相同：主题 `shrimp/lab/shrimp-node04/records|status|ack`，QoS 1，独立 broker 账号 `shrimp-node04`（ACL 只能写自己的主题、读自己的 `ack` 和 `cmd`），Jetson 落库后才回 ACK。USB 串口 115200 同时输出同样的行。
