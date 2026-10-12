# Node-7 — 硬件

| 部件 | 型号 | 状态 |
|---|---|---|
| 继电器 | Two-Channel Control IoT AC Power Relay Module（用户提供的名称） | 品牌、具体型号、额定值未记录（NOT VERIFIED） |
| 加热器 | 未记录 | 功率、电压、自带温控范围、最低水位：未记录 |
| 控制器 | ESP32-S3 开发板；esptool 2026-10-12：ESP32-S3 (QFN56) rev v0.2，内置 PSRAM 8 MB，flash 16 MB（68/4018，quad，3.3 V），MAC `44:1B:F6:FE:73:48` | 与项目 N16R8 编译配置一致 |

同名产品资料（[vxb.com 产品页](https://vxb.com/products/two-channel-iot-relay-outlet-module-for-smart-home)，2026-10-12 读取，**不确定是同一款**）：光耦隔离控制输入，DC 3–120 V / AC 8–150 V；每路 10 A 继电器，120 V 输出；两个 NEMA 5-15R 插座；15 A 可复位过载保护。资料没有写控制输入电流和每个插座的常开 / 常断标识。

待核对（接加热器前）：
- 模块控制输入的电压范围和电流（决定 GPIO 能否直接驱动）。
- 加热器功率不超过继电器单路额定电流（120 V 下 10 A ≈ 1200 W，以实物额定为准）。
- 墙插是否有漏电保护（GFCI）。
