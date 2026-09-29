# pump-node-2 MQTT 固件

与 [pump-node-1 固件](../../../pump-node-1/script/PMP_MQTT/README.md) 同一份代码：`PumpChannel.h`、`PumpParse.h`、`Telemetry.h`、`BenchLog.h` 逐字节相同，只有 `PMP_MQTT.ino` 的节点名 `shrimp-node05`、传感器编号 `PUMP2_ATLAS_PMP`、版本 `node05-pump-mqtt-0.2`、`NODE_MAC` 不同。行为、容量与限制见泵 1 的固件 README。

改共用头文件时两边一起改，然后核对（仓库根目录）：

```bash
for f in PumpChannel.h PumpParse.h Telemetry.h BenchLog.h; do cmp lab_scale/pump-node-{1,2}/script/PMP_MQTT/$f || echo "DIFFERENT: $f"; done
g++ -std=c++11 -Wall -Wextra -fsanitize=address,undefined -I lab_scale/pump-node-1/tests lab_scale/pump-node-1/tests/test.cpp -o /tmp/np && /tmp/np
```

| 版本 | 状态 |
|---|---|
| `node05-pump-mqtt-0.2` | 2026-09-29 填入 MAC 后真实编译：916,835 B（69%），静态 RAM 49,732 B；`PMP_MQTT.ino.bin` sha256 `7aceae6c4c68764cbbf889761166f29f9647808ba91c7ffb642e9cef27758f36`；2026-09-29 13:53 EDT 已烧录，运行正常 |

## 工作流程（Jetson 终端，仓库根目录）

每一步都不会自动进入下一步；第 6 步烧录前必须确认目标板。

```bash
ESPTOOL=.codex-build/arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool
FQBN='esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc'

# 1. 找串口：只插泵 2 这一块板子，以实际输出为准
ls -l /dev/serial/by-id/
PORT=/dev/ttyACM0

# 2. 读 MAC 和 flash（必须是 ESP32-S3、16 MB flash，MAC 不能是 7C:4F:AD:B5:33:38 = 泵 1）
$ESPTOOL --chip esp32s3 --port $PORT flash-id

# 3. 回读整片 16 MB flash 备份（约 8 分钟）
mkdir -p .codex-build/node5-backup && cd .codex-build/node5-backup
for i in $(seq 0 15); do ../arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool --chip esp32s3 --port $PORT --no-stub read-flash $((i*0x100000)) 0x100000 part$i.bin || break; done
ls part*.bin | wc -l      # 必须是 16，少于 16 说明中途失败，不要继续
STAMP=$(date -u +%Y%m%dT%H%M%SZ); cat $(for i in $(seq 0 15); do echo part$i.bin; done) > node5-flash-before-pump-$STAMP.bin
sha256sum node5-flash-before-pump-$STAMP.bin > node5-flash-before-pump-$STAMP.bin.sha256 && rm part*.bin; cd ../..

# 4. 把第 2 步的 MAC 填进 lab_scale/pump-node-2/script/PMP_MQTT/PMP_MQTT.ino 的 NODE_MAC，然后真实编译（只编译）
python3 lab_scale/jetson_web/build_node1.py --node 5

# 5. 重启网关两个服务，让 broker 读到 shrimp-node05 账号、接收器订阅 node05、网页出现泵 2。
#    必须在烧录之前：ACL 不允许订阅 cmd 时，节点会反复断开重连，一条数据都发不出去。
cd lab_scale/jetson_web
kill "$(cat data/mqtt.pid)" "$(cat data/server.pid)"
nohup python3 -u run_mqtt.py > data/mqtt.log 2>&1 & echo $! > data/mqtt.pid
set -a; . ./.env; set +a
nohup python3 -u server.py --bind 192.168.88.249 --interface enP8p1s0 --pump-control > data/server.log 2>&1 & echo $! > data/server.pid
cd ../..

# 6. 烧录（确认 $PORT 就是泵 2、MAC 与第 2 步一致之后）
.codex-build/tools/arduino-cli --config-file .codex-build/arduino-cli.yaml upload -p $PORT --fqbn "$FQBN" --input-dir .codex-build/node5-configured/output
```

板子插的是 ESP32-S3 原生 USB 口（设备名 `Espressif…`）。烧录后这个口会重新枚举，名字可能变成 `usb-Espressif_USB_JTAG_serial_debug_unit_<MAC>-if00`，再用时重新 `ls -l /dev/serial/by-id/`。原生口读 flash 若失败（NOT VERIFIED），改插板子的 COM/UART 口再试。

**回退**：`$ESPTOOL --chip esp32s3 --port $PORT write-flash 0 .codex-build/node5-backup/node5-flash-before-pump-*.bin`
