# pump-node-1 — 硬件型号

| 部件 | 型号 | 状态 |
|---|---|---|
| 泵 | Atlas Scientific **EZO-PMP** 嵌入式蠕动计量泵（[产品页](https://atlas-scientific.com/peristaltic/ezo-pmp/)） | 用户已购买（2026-09-27）；DECISION 048 PROVISIONAL，台架验收未完成 |
| 控制器 | ESP32-S3 开发板；esptool 读取：ESP32-S3 (QFN56) rev v0.2，Wi-Fi + BLE，内置 PSRAM 8 MB (AP_3v3)，flash 16 MB（厂商 c8 / 器件 4018，eFuse 设为 quad），MAC `7C:4F:AD:B5:33:38` | 与项目 N16R8 编译配置（16 MB、QIO、OPI PSRAM）一致；板子品牌/型号未记录 |
| 电机电源 | 12 V 直流适配器（建议单独一个，见 [WIRING.md](WIRING.md)） | 型号未记录 |

## EZO-PMP 数据手册要点

来源：[EZO-PMP datasheet](https://files.atlas-scientific.com/EZO_PMP_Datasheet.pdf)，2026-09-27 下载并提取原文核对。

| 项目 | 手册内容 |
|---|---|
| 类型 | 蠕动泵：液体只接触软管，不接触泵体金属或电路 |
| 流量 | 0.5–105 mL/min；`D,*` 连续约 105 mL/min（配套软管）；`DC,<mL/min>,*` 恒定流量 |
| 精度 | 未校准 ±5%，校准后 ±1%（单点校准） |
| 控制电源 | VCC 3.3–5.5 V；3.3 V 时约 12.5 mA |
| 电机电源 | 12–24 V；12 V 约 400 mA，24 V 约 200 mA；最低 10.8 V；手册称转速不随电压变化 |
| 最大进/出口压力 | 80 kPa |
| 协议 | UART（出厂默认，9600 8N1，ASCII，`<cr>` 结尾）或 I2C（地址 0x67） |
| 数据线 | 红 VCC、黑 GND、白 RX/SCL、绿 TX/SDA、蓝 INT |
| INT | 泵输送时为高 |
| 其他能力 | 可自吸、可空转 |
| 寿命（手册标称） | 软管 >1,000 h，泵头 1,500 h，电机 5,000 h；24/7 运行约 42 / 63 / 208 天 |
| 已知限制 | **连续模式运行 20 天后泵会自行复位**，固件必须检测并重新下发流量设定 |
| 本机实测（2026-09-27） | 泵固件 1.06；校准前恒定流量上限 54.66 mL/min；10 mL 指令实测 8.3 mL（体积、按时间各一次）；校准后 `?CAL,3`、上限 **45.36 mL/min** |
| 软管 | 配套 Saint-Gobain PharMed BPT；15–25 ppt 盐水长期兼容性：**NOT VERIFIED** |

手册没有说明控制板 GND 与电机 − 是否相通，也没有给出 12 V 输入的物理形式和极性标注：**NOT VERIFIED**，以实物为准。

## 为什么这个节点不做电气隔离

Phase-1 设计把泵和流量计放在同一条隔离 I2C 总线上，主要是因为流量计的电气参考可能接触流体。蠕动泵里液体只接触软管，泵本身不和水形成电气通路，所以泵单独接 ESP32 的 UART 可以直连。**以后如果在这个节点加流量计或 Mg/Ca 等接触流体的传感器，那一路必须重新做隔离**（见 DECISION 048）。
