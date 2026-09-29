# Node-6 MQTT 固件（TURB_MQTT）

一路 DFRobot SEN0710 浊度（Modbus RTU）→ ESP32-S3 → 实验室 2.4 GHz Wi-Fi → MQTT → Jetson。行为（RAM 队列 64 条、落库 ACK、MAC 检查、`UTC=UNSYNCED`）与 Node-1 相同，见 [Node-1 固件 README](../../../Node-1/script/DO_ORP_MQTT/README.md)。

| 版本 | 状态 |
|---|---|
| `node06-mqtt-0.1` | 2026-09-29 填入 MAC 后真实编译：901,067 B（68%），静态 RAM 49,276 B；`TURB_MQTT.ino.bin` sha256 `33286567cae24a5d8a9f28827cd0e68c7f3b8399433edf370e78057f41df379b`；2026-09-29 19:36 EDT 已烧录，通信正常 |

## 工作流程（Jetson 终端，仓库根目录）

每一步都不会自动进入下一步。板子插的是原生 USB 口，出厂程序占着它：**读 MAC、备份、烧录之前都要先按 BOOT + RST 进下载模式，烧完单按一次 RST。**

```bash
ESPTOOL=.codex-build/arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool
PORT=/dev/ttyACM0

# 1. 读 MAC 和 flash（必须 ESP32-S3、16 MB；MAC 不能是其他节点的）
$ESPTOOL --chip esp32s3 --port $PORT flash-id

# 2. 回读整片 16 MB flash 备份（约 8 分钟；最后一行必须是 16）
mkdir -p .codex-build/node6-backup && cd .codex-build/node6-backup
for i in $(seq 0 15); do ../arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool --chip esp32s3 --port $PORT --no-stub read-flash $((i*0x100000)) 0x100000 part$i.bin || break; done
ls part*.bin | wc -l
STAMP=$(date -u +%Y%m%dT%H%M%SZ); cat $(for i in $(seq 0 15); do echo part$i.bin; done) > node6-flash-before-$STAMP.bin
sha256sum node6-flash-before-$STAMP.bin | tee node6-flash-before-$STAMP.bin.sha256 && rm part*.bin; cd ../..

# 3. 把 MAC 填进 lab_scale/Node-6/script/TURB_MQTT/TURB_MQTT.ino 的 NODE_MAC，然后编译（只编译）
python3 lab_scale/jetson_web/build_node1.py --node 6

# 4. 重启网关两个服务（broker 读新账号、接收器订阅 node06、网页出现面板），然后回到仓库根目录
cd lab_scale/jetson_web
kill "$(cat data/mqtt.pid)" "$(cat data/server.pid)"
nohup python3 -u run_mqtt.py > data/mqtt.log 2>&1 & echo $! > data/mqtt.pid
set -a; . ./.env; set +a
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 --pump-control > data/server.log 2>&1 & echo $! > data/server.pid
cd ../..

# 5. 烧录（先 BOOT + RST，确认 by-id 名字里的 MAC 与第 1 步一致），烧完单按 RST
.codex-build/tools/arduino-cli --config-file .codex-build/arduino-cli.yaml upload -p $PORT --fqbn 'esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc' --input-dir .codex-build/node6-configured/output
```

**回退**：`$ESPTOOL --chip esp32s3 --port $PORT write-flash 0 .codex-build/node6-backup/node6-flash-before-*.bin`

主机测试（仓库根目录）：

```bash
g++ -std=c++11 -Wall -Wextra -fsanitize=address,undefined -I lab_scale/Node-6/script/TURB_MQTT lab_scale/Node-6/tests/protocol_test.cpp -o /tmp/n6 && /tmp/n6
```
