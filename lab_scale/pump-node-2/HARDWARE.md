# pump-node-2 — 硬件

| 部件 | 型号 | 状态 |
|---|---|---|
| 泵 | Atlas Scientific EZO-PMP | 用户报告与泵 1 同型号；泵固件版本待初始化时读取（`i`） |
| 控制器 | ESP32-S3 开发板；esptool 2026-09-29：ESP32-S3 (QFN56) rev v0.2，内置 PSRAM 8 MB (AP_3v3)，40 MHz 晶振，flash 16 MB（c8/4018，quad，3.3 V），MAC `7C:4F:AD:B5:1C:D4` | 与项目 N16R8 编译配置一致；板子品牌/型号未记录 |
| 电机电源 | 12 V 直流适配器 | 型号未记录 |

数据手册要点、盐水软管兼容性、控制板 GND 与电机 − 是否相通等未验证项，与泵 1 相同，见 [pump-node-1/HARDWARE.md](../pump-node-1/HARDWARE.md)。本机实测（2026-09-29）：泵固件 1.06；校准前恒定流量上限 54.66 mL/min；10 mL 指令实测 9.19 mL（体积）/ 9.08 mL（按时间）；校准后 `?CAL,3`、上限 **49.63 mL/min**。
