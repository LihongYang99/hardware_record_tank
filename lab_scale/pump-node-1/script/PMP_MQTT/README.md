# pump-node-1 MQTT 固件

Atlas EZO-PMP 蠕动泵 → UART → ESP32-S3 → 实验室 2.4 GHz Wi-Fi → MQTT → Jetson 数据库 → 网页；操作命令反方向经 MQTT `cmd` 主题下发。`node_id=shrimp-node04`。

| 版本 | 状态 |
|---|---|
| `node04-pump-mqtt-0.1` | 2026-09-27 已烧录，通信成功；固定 80 mL/min 设定（超过泵上限 54.66，被拒） |
| `node04-pump-mqtt-0.2` | 增加操作命令、NVS 保存设定、默认不转；已编译（916,835 B，69%），待烧录 |

## 行为

- **控制**：流量设定由操作人用 [pump_ctl.py](../../../jetson_web/pump_ctl.py) 下发，存进 ESP32 NVS，开机恢复；从未设定过时为 `PUMP_DEFAULT_ML_MIN = 0`（不转）。设定 > 0 时：启动后第一轮发 `DC,<设定>,*`；泵复位（`*RS` / `*RE`，含手册所说 20 天自动复位）后重新初始化并再发一次；泵报告停止时最多每 60 s 重发一次。命令格式与白名单见 [COMMUNICATION.md](../../COMMUNICATION.md#操作命令固件-02)。
- **监测**：每 4 s 查 `D,?`（运行位）、读 INT 引脚、查 `PV,?`（电机电压）、`TV,?`（本次上电累计体积），合成一行结果，原始回复原样保留。
- **身份**：启动时读 eFuse 出厂 MAC，与 `NODE_MAC` 不符（或 `NODE_MAC` 仍是全零）就不启动泵，USB 每 5 s 打印 `event=WRONG_BOARD board_mac=…`。
- **传输**：`Telemetry.h`、`BenchLog.h` 与 Node-2 逐字节相同：RAM 队列 64 条、QoS 1、落库 ACK 后出队、无 ACK 每 5 s 重发。
- 仍然 `UTC=UNSYNCED`；泵未校准，`validation=UNVALIDATED`。

## 工作流程（Jetson 终端，仓库根目录）

每一步都不会自动进入下一步；第 7 步烧录前必须由用户确认目标板。

```bash
ESPTOOL=.codex-build/arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool
FQBN='esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc'

# 1. 插上泵节点 ESP32，找到它的串口（以实际输出为准，不要沿用 Node 2 的 /dev/ttyACM0）
ls -l /dev/serial/by-id/
PORT=/dev/ttyACM0

# 2. 读出厂 MAC、芯片与 flash 信息（确认是 ESP32-S3、16 MB flash）
$ESPTOOL --chip esp32s3 --port $PORT read-mac
$ESPTOOL --chip esp32s3 --port $PORT flash-id

# 3. 回读整片 16 MB flash 备份（stub 模式在 0x6A000 会中断，所以用 --no-stub 按 1 MB 分块，约 8 分钟）
mkdir -p .codex-build/node4-backup && cd .codex-build/node4-backup
for i in $(seq 0 15); do ../arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool --chip esp32s3 --port $PORT --no-stub read-flash $((i*0x100000)) 0x100000 part$i.bin || break; done
STAMP=$(date -u +%Y%m%dT%H%M%SZ); cat $(for i in $(seq 0 15); do echo part$i.bin; done) > node4-flash-before-pump-$STAMP.bin
sha256sum node4-flash-before-pump-$STAMP.bin > node4-flash-before-pump-$STAMP.bin.sha256 && rm part*.bin; cd ../..

# 4. 把第 2 步读到的 MAC 填进 PMP_MQTT.ino 的 NODE_MAC（并记到 ../../PROGRESS.md）

# 5. 给 broker 补 shrimp-node04 账号（已有节点的密码保持不变）
python3 lab_scale/jetson_web/prepare_mqtt.py --host 192.168.88.249

# 6. 生成本地配置（复用 Node 1 已验证的 2.4 GHz Wi-Fi，不显示密码），然后编译（只编译不烧录）
python3 lab_scale/jetson_web/configure_node1.py --node 4 --wifi-from-node1
python3 lab_scale/jetson_web/build_node1.py --node 4

# 7. 烧录（确认 $PORT 就是泵节点、MAC 与第 2 步一致之后）
.codex-build/tools/arduino-cli --config-file .codex-build/arduino-cli.yaml upload -p $PORT --fqbn "$FQBN" --input-dir .codex-build/node4-configured/output

# 8. 让 broker 读取新账号/ACL（不断开现有连接），并重启网页服务（新面板/字段）。
#    固件 0.2 起必须在第 7 步烧录之前做：ACL 不允许订阅 cmd 时，节点会反复断开重连，一条数据都发不出去。
cd lab_scale/jetson_web
kill -HUP "$(pgrep -f 'mosquitto -c')"
kill "$(cat data/server.pid)"
set -a; . ./.env; set +a
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 --pump-control > data/server.log 2>&1 & echo $! > data/server.pid
# （首次部署、接收器代码改动时才需要整体重启 run_mqtt.py：）
cd lab_scale/jetson_web
kill "$(cat data/mqtt.pid)" "$(cat data/server.pid)"    # 先确认 PID 属于这两个服务
nohup python3 -u run_mqtt.py > data/mqtt.log 2>&1 & echo $! > data/mqtt.pid
set -a; . ./.env; set +a
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 --pump-control > data/server.log 2>&1 & echo $! > data/server.pid
```

重启服务期间 Node 1/Node 2 的记录留在各自 RAM 队列里（约 80 s / 27 s），服务恢复后补发。

**回退**（泵节点接 Jetson USB 时，仓库根目录）：

```bash
$ESPTOOL --chip esp32s3 --port $PORT write-flash 0 .codex-build/node4-backup/node4-flash-before-pump-*.bin
```

主机测试（仓库根目录，不需要接板子）：

```bash
g++ -std=c++11 -Wall -Wextra -fsanitize=address,undefined -I lab_scale/pump-node-1/tests lab_scale/pump-node-1/tests/test.cpp -o /tmp/pump-node-test && /tmp/pump-node-test
```

## 容量与限制条件

数字来自源码常量、2026-09-27 编译输出和估算；"估算"项未经实板验证。

| 项目 | 数值 | 说明 |
|---|---|---|
| 程序大小 | 0.2：916,835 B / 1,310,720 B（69%）；0.1：912,183 B | 全零 MAC 的 `--check` 编译只有约 48 万字节（代码被优化掉），不代表实际 |
| 静态全局 RAM | 0.2：49,732 B / 327,680 B（15%） | 不含运行时队列和任务 |
| 命令队列 | 4 条 × 128 B；满或超长计 `command_lost` | 一次只执行一条 |
| 发送队列 | 64 条 × 约 1,168 B，断电即丢 | 与 Node-1/2 相同 |
| 单行长度（估算） | 结果行约 520 B（含传输字段）；BenchLog 上限 767 字符 | |
| 记录速率（估算） | 约 0.55 条/s（结果 0.25 + Wi-Fi 状态 0.2 + HEALTH 0.1） | 每轮只 1 行结果，比 Node-2 的约 2.3 条/s 少 |
| 64 条队列可覆盖的断网（估算） | 约 **2 分钟** | 超出后丢最新记录并计 `mqtt_lost` |
| 单条命令超时 | 1.8 s；每轮 3–4 条命令 | 超时即 `COMMUNICATION_ERROR`，15 s 后重新初始化 |
| 设定重发 | 复位后立即；报告停止时 ≥60 s 一次 | |

### 可能影响顶层设计的限制（待决定）

1. **"运行中"只是控制器自己的报告**：软管脱落、堵塞、没吸到水时它照样报运行。要证明旁路真的有水流，需要流量计（OPEN-10）。
2. **网页只读**：启停和调流速用 Jetson 终端的 `pump_ctl.py`（需要登录 Jetson）。网页控制涉及局域网无登录的安全问题，另行决定。
3. **未校准时**流量误差 ±5%，恒定流量上限 54.66 mL/min；`TV` 累计体积断电清零。校准由操作人用 `pump_ctl.py calibrate` 完成，必须写 `--note`，记录在 `operator_event`。
4. **断网缓冲只在 RAM**，同 Node-1/2。
