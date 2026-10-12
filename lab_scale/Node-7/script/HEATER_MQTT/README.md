# Node-7 固件（HEATER_MQTT）

| 版本 | 状态 |
|---|---|
| `node07-heater-mqtt-0.1` | 2026-10-12 编译检查通过；`NODE_MAC` 待填，未烧录 |

流程与 Node-6、泵 2 相同（板子插原生 USB 口时，读 MAC、备份、烧录前都先按 BOOT + RST，烧完单按 RST）。仓库根目录：

```bash
ESPTOOL=.codex-build/arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool
PORT=/dev/ttyACM0
$ESPTOOL --chip esp32s3 --port $PORT flash-id                     # 1. 读 MAC
mkdir -p .codex-build/node7-backup && cd .codex-build/node7-backup  # 2. 备份 16 MB（结束时 ls part*.bin | wc -l 必须是 16）
for i in $(seq 0 15); do ../arduino-data/packages/esp32/tools/esptool_py/5.3.1/esptool --chip esp32s3 --port $PORT --no-stub read-flash $((i*0x100000)) 0x100000 part$i.bin || break; done
ls part*.bin | wc -l
STAMP=$(date -u +%Y%m%dT%H%M%SZ); cat $(for i in $(seq 0 15); do echo part$i.bin; done) > node7-flash-before-$STAMP.bin
sha256sum node7-flash-before-$STAMP.bin | tee node7-flash-before-$STAMP.bin.sha256 && rm part*.bin; cd ~/Documents/GitHub/hardware_record_tank
# 3. MAC 填进 HEATER_MQTT.ino 的 NODE_MAC 后编译
python3 lab_scale/jetson_web/build_node1.py --node 7
# 4. 重启 run_mqtt.py 与 server.py（新账号、新节点、控温线程），见 jetson_web README
# 5. 烧录（先 BOOT + RST，确认 by-id 里的 MAC）
.codex-build/tools/arduino-cli --config-file .codex-build/arduino-cli.yaml upload -p $PORT --fqbn 'esp32:esp32:esp32s3:FlashSize=16M,FlashMode=qio,PSRAM=opi,USBMode=hwcdc,CDCOnBoot=cdc' --input-dir .codex-build/node7-configured/output
```

主机测试：`g++ -std=c++11 -Wall -Wextra -fsanitize=address,undefined lab_scale/Node-7/tests/test.cpp -o /tmp/n7 && /tmp/n7`
