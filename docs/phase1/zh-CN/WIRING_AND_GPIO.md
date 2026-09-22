# 逐线接线与 ESP32 GPIO 说明（中文读者版）

**英文逐线工程基准：** [Exact Wiring Matrix and ESP32 GPIO Allocation](../WIRING_AND_GPIO.md)  
**控制器：** `ESP32-S3-DevKitC-1-N8R8`；每个节点使用独立 USB 5 V 电源

本页帮助理解和复核。实际端接时必须逐个 wire ID 对照英文表，不能把中文概述当作替代接线图。

## 1. 先记住五个电气简称

| 名称 | 含义 |
|---|---|
| `P5V` | 节点从 USB 得到的 5 V |
| `LGND` | 该 ESP32 节点的逻辑地 |
| `P3V3` | Pololu 稳压后的外设 3.3 V |
| `SGND12` | 与 ESP 隔离的 12 V 传感器回路 |
| `IGND4` | Node 4 隔离 I2C 一侧的地 |

## 2. 六条不可违反的边界

1. 12 V、真正的 RS232、电气上的 RS485 A/B 都不能直接接 ESP32 GPIO。
2. `LGND` 不能接 `SGND12`、Waveshare TTL TO RS485 (B) 的 RS485 侧 `SGND`、RS232 侧 SGND 或 `IGND4`。
3. Waveshare TTL TO RS485 (B) 不提供 12 V 传感器电源；传感器从带保险丝的 12 V 主路供电。
4. DFR0565 隔离侧输出是 5 V；SLF3S 最大允许 3.8 V，必须经过 Pololu 降为 3.3 V。
5. EZO-PMP 的电机电源是 12 V，数据/控制 VCC 是隔离侧 3.3 V；这是两组不同引脚。
6. 屏蔽层不得两端都接。RDO 银色屏蔽线只能单端接合法干燥机壳/功能地；若不存在合法点，则绝缘悬空并记录。

上电前对所有禁接组合做断电连续性检查。除非厂家设备内部明确连接并已经记录，否则结果应为开路。

## 3. GPIO 分配

| GPIO | 用法 | 原因 |
|---:|---|---|
| 0、3、45、46 | 不接传感器 | 启动绑带脚风险。 |
| 19、20 | 保留 | DevKitC-1 原生 USB D−/D+。 |
| 43、44 | 保留 | UART0 编程/诊断。 |
| 48 | 保留 | 可能连板载 RGB/状态 LED。 |
| 8 | I2C SDA | Node 1 化学总线、Node 4 隔离旁路总线。 |
| 9 | I2C SCL | 同上。 |
| 17 | UART1 TX | Nodes 1、3；Node 4 未来维修串口预留。 |
| 18 | UART1 RX | 同上。 |
| 15 | UART2 TX | Node 2 ORP。 |
| 16 | UART2 RX | Node 2 ORP。 |

ESP32-S3 可以通过 GPIO matrix 路由串口，这些是本项目固件分配，不是说芯片只有这些脚能做串口。

## 4. Nodes 1–3 公共电源线

Node 4 不使用本节 N-P02 至 N-P07；它按第 8 节独立接隔离 I2C。

| 线号 | 从 | 到 | 检查 |
|---|---|---|---|
| N-P01 | 合规 5 V USB 适配器 | ESP32 DevKit USB | Wi-Fi 负载下板端 4.75–5.25 V，无 brownout。 |
| N-P02 | 到货板上明确标记 `5V`/`VBUS` 的脚 | Pololu `VIN` | 红色 24 AWG；不可把 `3V3` 当输入。 |
| N-P03 | DevKit `GND` | Pololu `GND` | 同一 `LGND`。 |
| N-P04 | Pololu `VOUT` | 外设 `VCC` 分配端 | 上设备前实测 3.3 V。 |
| N-P05 | Pololu `GND` | 外设 `GND` 分配端 | 仍属 `LGND`，不接传感器侧。 |
| N-P06 | ESP GPIO | 接口模块逻辑信号 | 只能 0–3.3 V。 |
| N-P07 | ESP `LGND` | 接口模块逻辑 GND | TTL/I2C 参考地。 |

Node 1 的 Atlas 载板和 Waveshare 转换器逻辑侧由外置 Pololu 3.3 V 供电，不压在 DevKit 板载 3.3 V 稳压器上。外设实测峰值必须低于 400 mA 设计上限。

## 5. Node 1：第一条链路

### 5.1 总线分配

| 总线 | ESP 引脚 | 设备 | 设置 |
|---|---|---|---|
| UART1 → Waveshare TTL TO RS485 (B) | TX GPIO17、RX GPIO18 | SEN0681；条件性 SEN0710/SEN0711 | 4800、8N1；地址 1/2/3。 |
| I2C | SDA GPIO8、SCL GPIO9 | EZO-pH、EZO-EC、EZO-RTD | 初始 100 kHz；`0x63/0x64/0x66`。 |

### 5.2 Waveshare TTL TO RS485 (B) 逻辑侧和 RS485 侧

Waveshare 的 TTL `RXD` 是转换器输入，接 ESP TX；TTL `TXD` 是转换器输出，接 ESP RX。批准型号为 Part No. 23778。

| 线号 | 从 | 到 | 状态 |
|---|---|---|---|
| N1-R01 | `P3V3` | Waveshare TTL `VCC` | 3.3 V |
| N1-R02 | `LGND` | Waveshare TTL `GND` | 只在逻辑侧 |
| N1-R03 | ESP GPIO17 TX | Waveshare TTL `RXD` | ESP → 转换器 |
| N1-R04 | Waveshare TTL `TXD` | ESP GPIO18 RX | 转换器 → ESP |
| N1-R05 | Waveshare RS485 `A+` | 黄色 RS485 A 分配 | 隔离侧 |
| N1-R06 | Waveshare RS485 `B-` | 蓝色 RS485 B 分配 | 隔离侧 |
| N1-R07 | Waveshare RS485 `SGND` | `SGND12` | 传感器侧共模参考 |
| N1-R08 | Waveshare `120R` 开关 | 初始保持 OFF | 只有确认转换器位于总线物理末端且需要终端电阻时才打开 |

### 5.3 SEN0681 接线

| 线号 | 传感器线 | 目的地 | 设置 |
|---|---|---|---|
| N1-D01 | 棕 | 带 1 A 保险的 `+12V_DO1` | 电源正 |
| N1-D02 | 黑 | `SGND12` | 12 V 回路 |
| N1-D03 | 黄 | RS485 A | 地址 1 |
| N1-D04 | 蓝 | RS485 B | 4800 8N1 |

首次搭建只接 SEN0681。若以后 SEN0710 获批，棕/黑/黄/蓝分别接 `MID_AUX`、`SGND12`、A、B，并在单独连接时改为地址 2。SEN0711 获批前只预留地址 3，不安装。

### 5.4 Atlas I2C 链

| 设备 | 电源/地 | SDA/SCL | 地址与探头 |
|---|---|---|---|
| pH ISCCB-2 | `P3V3/LGND` 仅控制侧 | GPIO8 → `TX/SDA`；GPIO9 → `RX/SCL` | `0x63`；`ENV-50-pH-NT` SMA 手紧，接头保持干燥；`OFF` 绝缘悬空。 |
| EC 隔离载板 | `P3V3/LGND` 仅控制侧 | 同一 SDA/SCL | `0x64`；K10 使用套件准确连接器；`OFF` 绝缘悬空。 |
| EZO-RTD/SCCB | `P3V3/LGND` | 同一 SDA/SCL | `0x66`；PT-THRD SMA 保持干燥。 |

共享前，每块 EZO 单独设置为 I2C 模式并确认地址。断电测 SDA/SCL 到 P3V3 的总上拉电阻；不能因为看见多块板就盲目并联额外上拉，也不能随意割板上走线。

## 6. Node 2：底层风险

RDO Blue 和 ORP 用两套 Waveshare TTL TO RS485 (B)/UART，因为串口设置不同，且故障需要隔离。

### 6.1 RDO Blue（UART1）

| 线号 | 连接 | 说明 |
|---|---|---|
| N2-D01/D02 | `P3V3/LGND` → Waveshare-A TTL `VCC/GND` | 只在逻辑侧。 |
| N2-D03 | GPIO17 TX → Waveshare-A TTL `RXD` | 19200、8E1。 |
| N2-D04 | Waveshare-A TTL `TXD` → GPIO18 RX | — |
| N2-D05 | Waveshare-A `A+` → RDO **蓝色** RS485 正 | 按受控 A/B 后备程序处理。 |
| N2-D06 | Waveshare-A `B-` → RDO **绿色** RS485 负 | — |
| N2-D07 | Waveshare-A `SGND` → `SGND12` | 隔离侧参考。 |
| N2-D08/D09 | RDO 红 → `+12V_RDO`；黑 → `SGND12` | 独立 1 A 分支。 |
| N2-D10 | RDO 银屏蔽 | 单端合法机壳/功能地，或绝缘 NC | 绝不接 `SGND12/LGND`。 |
| N2-D11 | Waveshare-A `120R` 开关 | 初始 OFF | 只在确认总线末端且需要终端电阻时打开。 |

### 6.2 条件性 SEN0709 ORP（UART2）

| 线号 | 连接 | 设置 |
|---|---|---|
| N2-O01/O02 | `P3V3/LGND` → Waveshare-B TTL `VCC/GND` | 盐水批准后才装。 |
| N2-O03/O04 | GPIO15 TX → `RXD`；`TXD` → GPIO16 RX | 4800、8N1。 |
| N2-O05/O06/O07 | `A+` → SEN0709 黄；`B-` → 蓝；`SGND` → `SGND12` | 地址 1。 |
| N2-O08/O09 | SEN0709 棕 → `+12V_ORP`；黑 → `SGND12` | 独立 1 A。 |
| N2-O10 | Waveshare-B `120R` 开关 | 初始 OFF；按总线末端测试决定。 |

## 7. Node 3：专用溶解 H2S

本节只有 S1-1020 完成采购门槛后才实施。

| 线号 | 连接 | 说明 |
|---|---|---|
| N3-S01/S02 | `P3V3/LGND` → Waveshare TTL `VCC/GND` | 逻辑侧 3.3 V。 |
| N3-S03 | GPIO17 TX → Waveshare TTL `RXD` | 38400、8N1、无流控。 |
| N3-S04 | Waveshare TTL `TXD` → GPIO18 RX | — |
| N3-S05 | Waveshare RS232 `TXD` → S1 RS232 **棕色 RXD** | 转换器发给传感器。 |
| N3-S06 | S1 RS232 **蓝色 TXD** → Waveshare RS232 `RXD` | 传感器发给转换器。 |
| N3-S07 | S1 RS232 **黑色 GND** → Waveshare RS232 `SGND` | 不接 `LGND`。 |
| N3-P01 | `+12V_H2S` → S1 **电源线棕色** | 永久标 `POWER`。 |
| N3-P02 | `SGND12` → S1 **电源线蓝色** | 不要与 RS232 蓝色 TXD 混淆。 |

不要额外跳线连接电源蓝色回路和 RS232 黑色信号地；实测内部关系并记录。Phase 1 的 4–20 mA 线端盖住并绝缘，除非另行批准隔离接收器。

## 8. Node 4：旁路泵和流量

### 8.1 DFR0565 控制侧

| 线号 | 从 | 到 |
|---|---|---|
| N4-C01 | DevKit `5V/VBUS` | DFR0565 Controller `+`；负载下 4.85–5.15 V |
| N4-C02 | `LGND` | Controller `-` |
| N4-C03 | GPIO9 SCL | Controller `C` |
| N4-C04 | GPIO8 SDA | Controller `D` |

### 8.2 隔离侧 3.3 V

| 线号 | 从 | 到/检查 |
|---|---|---|
| N4-I01 | DFR0565 Module `+` 隔离 5 V | Pololu `VIN`；不能直接给流量计 |
| N4-I02 | Module `-` | Pololu `GND`，定义 `IGND4` |
| N4-I03/I04 | Pololu `VOUT/GND` | 隔离 3.3 V / `IGND4`；插设备前测量 |
| N4-I05/I06 | Module `C/D` | 隔离 SCL/SDA，泵和流量计共用 |

### 8.3 SLF3S 尾线必须按针脚号

| 针脚 | 去向 |
|---:|---|
| 1 `IRQ` | NC、绝缘 |
| 2 `SDA` | 隔离 SDA；地址 `0x08`，校验 CRC |
| 3 `VDD` | 隔离 3.3 V；实测 3.2–3.8 V |
| 4 `GND` | `IGND4` |
| 5 `SCL` | 隔离 SCL |
| 6 `NC` | NC、绝缘 |

### 8.4 EZO-PMP

| 线号 | 连接 | 说明 |
|---|---|---|
| N4-P01/P02 | `+12V_BYPASS/SGND12` → 泵电机 `+/-` | 独立 1 A；核实防呆插头极性。 |
| N4-P03 | 隔离 3.3 V → EZO-DC 红 `VCC` | 控制电源。 |
| N4-P04 | `IGND4` → EZO-DC 黑 `GND` | 与 ESP 仍隔离。 |
| N4-P05 | 隔离 SCL → EZO-DC 白 `RX/SCL` | I2C 地址 `0x67`。 |
| N4-P06 | 隔离 SDA → EZO-DC 绿 `TX/SDA` | — |
| N4-P07 | 蓝 `INT` | NC、绝缘 |

启动时先识别 `0x08` 和 `0x67`，泵停时读零流量，再在管路处于运行位置后发送 `DC,80,*`。30 s 内未进入 60–100 mL/min，停止并报 `FLOW_LOW`，不能反复顶着堵塞运行。泵复位或状态中断后重新发送 `DC,80,*`。

`Dstart,*` 只会以约 105 mL/min 启动，不是保存 80 mL/min 的命令。

## 9. 12 V 分支

| 分支 | 设备 | 设计负载 | 保险丝 |
|---|---|---:|---:|
| `DO1` | SEN0681 | 约 17 mA | 1 A |
| `RDO` | RDO Blue | ≤50 mA | 1 A |
| `ORP` | 条件性 SEN0709 | 约 33 mA | 1 A |
| `H2S` | 条件性 S1-1020 | 未知 | 暂定 1 A，等最大电流 |
| `BYPASS` | EZO-PMP 电机 | 约 400 mA | 1 A |
| `MID_AUX` | 条件性 SEN0710/SEN0711 | 合计约 42 mA | 1 A |

`SGND12` 是有意设置的 12 V 公共回路，但这不授权它与任一 ESP/USB `LGND` 相连。

## 10. 通电与签字顺序

1. 全部负载移除，核实桶形插头极性、12 V、每个保险分支，以及对所有 `LGND` 无导通。
2. 每个 USB 节点单独上电，检查 P5V、P3V3、启动、USB 控制台和 Wi-Fi 稳定。
3. 每次只增加一个接口模块；接传感器前再次检查隔离侧地对 LGND 开路。
4. 一次只接一只 RS485 传感器配置地址。
5. 先接 SEN0681，保存 100 个 CRC 正确帧。
6. Node 1 I2C 设备逐个加入，只看到预期地址，并检查上拉和上升时间。
7. RDO、H2S 和 Node 4 只有各自采购门槛关闭后才调试。
8. 固定端子、拉力检查冷压端头、安装应力释放和滴水弯，拍摄每根标记线两端。

签字记录至少包含：`wire_id`、两端照片、连续性、隔离结果、空载/负载电压、电流、操作人、UTC、图纸版本和偏差。
