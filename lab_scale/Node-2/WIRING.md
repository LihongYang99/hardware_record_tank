# Node-2 — 接线与供电

每个探头接自己的 EZO 电路与 ISCCB-2，保留原同轴探头线。以下为当前脚本对应的接法；断电改线。

| ISCCB-2 主控侧 | EC 对应 ESP32 端 | pH 对应 ESP32 端 |
|---|---|---|
| VCC | 3.3 V | 3.3 V |
| GND | GND | GND |
| RX（UART 输入） | GPIO17（ESP TX） | GPIO15（ESP TX） |
| TX（UART 输出） | GPIO18（ESP RX） | GPIO16（ESP RX） |
| OFF | 不连接 | 不连接 |

ESP32 通过 USB 供电。此直接 GPIO 方案主控侧供电为 3.3 V；不要把载板改供 5 V 后仍直接接 ESP GPIO，不接 12 V。
两块载板不能共用同一 UART TX/RX 线；不能把探头同轴外壳/隔离侧地另接主控地以绕过隔离。
板载 3.3 V 总电流余量、第三方板稳压器型号 **NOT VERIFIED**；通信成功不等于通过供电验收。
参考 [ISCCB 手册](https://files.atlas-scientific.com/Isccb.pdf)（2026-09-22 可访问）；实物逐针连续性并未由本次远程操作验证。
