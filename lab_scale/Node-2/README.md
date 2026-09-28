# Node-2 — Atlas EC / salinity + pH

## 身份与 IP

- 固件标识：`shrimp-node02`；同款 ESP32-S3 N16R8。
- 局域网 IP：**192.168.88.251**，用户于 2026-09-22 确认。DHCP 地址，未在代码中固定。
- 两条独立 TTL UART，不是 RS485，也不需要 Modbus 地址。

## 当前状态（2026-09-27 晚）

- 板上程序：[script/Atlas_EC_pH_MQTT/](script/Atlas_EC_pH_MQTT/)（`firmware=node02-mqtt-0.1`），经实验室 2.4 GHz Wi-Fi → MQTT 发到 Jetson；IP 192.168.88.251（实测），MAC `44:B1:76:CC:D4:84`。
- 供电：ESP32 经 USB Type-C 直接接电源适配器（用户 2026-09-27 确认），已不接 Jetson USB；经 Wi-Fi 正常上传、网关核对 MAC 一致。ISCCB-2 载板仍由 ESP32 的 3.3 V 供电。适配器型号、额定输出未记录。
- pH：正常读取并进入 Jetson 数据库和网页，QC=`COMPENSATION_MISSING`，未校准。
- EC：掉线已重新接好，通信恢复；但读数仍为 0.000，QC=`CONFIGURATION_MISMATCH`（K=1.000 与 K10 探头不符），K/校准待用户确认，见 [PROGRESS.md](PROGRESS.md)。
- 容量与限制条件见 [script/Atlas_EC_pH_MQTT/README.md](script/Atlas_EC_pH_MQTT/README.md#容量与限制条件)。

## 方法与原理

### 方法：怎么读数

1. **硬件链路**。EC 探头（Atlas K10）接 EZO-EC 电路，pH 探头（Atlas Industrial Gen3, No Temp）接 EZO-pH 电路；每块 EZO 各装在一块 ISCCB-2 隔离载板上，载板以 3.3 V 供电，UART 直接接 ESP32：EC 用 UART1（RX GPIO18 / TX GPIO17），pH 用 UART2（RX GPIO16 / TX GPIO15）。详见 [WIRING.md](WIRING.md)。
2. **协议**。EZO 模块用 9600 bps / 8N1 的 ASCII 文本命令。启动时固件关闭连续输出（`C,0`）、打开应答确认（`*OK,1`），查询身份 `i`、温度补偿 `T,?`、校准状态 `Cal,?`，EC 另查电极常数 `K,?`；并把 EC 的输出设为只输出电导率和盐度（`O,EC,1` `O,TDS,0` `O,S,1` `O,SG,0`）。之后每 4 s 发一次 `R` 读数。
3. **解析**。回复是 ASCII 数字（EC 为 `电导率,盐度`，pH 为一个数），固件严格解析，格式不对就标通信错误。每一条发出的命令（TX）和每一段原始回复（RX）都单独记一行日志，最后再记一行解析结果。
4. **调度与上传**。与 Node-1 相同：4000 ms 一轮、两路独立超时、RAM 队列、MQTT 主题 `shrimp/lab/shrimp-node02/records`、落库 ACK 后出队。

### 原理：为什么测这两个量、为什么这样接

- **电导率（EC）与盐度**。水中离子越多导电越强，EC 就是水的导电能力（µS/cm）。对虾养殖用的 15–25 ppt 盐水电导率很高，所以选 K10 探头：K 是电极常数，由两电极的面积和间距决定，模块用"测得的电导 × K"得到电导率。K 值大的探头适合高电导率水。**目前模块设定 K=1 而探头是 K10，标度不符，读数为 0，固件标 `CONFIGURATION_MISMATCH`**，需要人工设定 K 并校准。盐度（PSU）不是另一支探头，是 EZO-EC 根据电导率和温度补偿设定算出来的。
- **pH**。pH 玻璃电极在膜两侧产生随氢离子浓度变化的电位，模块把这个毫伏级电压换算成 pH（Nernst 关系，通用原理）。这个换算随温度变化，所以需要温度补偿；本探头是 No Temp 型，没有内置温度传感器，模块里的 25 °C 只是一个设定值，不是实测水温，因此固件标 `COMPENSATION_MISSING`。
- **为什么要隔离载板（ISCCB-2）**。EC 测量要往水里注入交流信号，pH 测量的是极微弱的电压；两支探头同在一缸水里、又共用一个主控地，就会形成回路互相干扰。ISCCB-2 把探头侧和 ESP32 侧电气隔离，两路各自独立。因此不能把探头同轴外壳或隔离侧地另接主控地来"省事"，那会绕过隔离。
- **为什么两条独立 UART**。两块载板不能共用同一对 TX/RX 线；分开后也符合"一支探头故障不影响另一支"的要求。
- **为什么每条 TX/RX 都记录**。Atlas 模块的回复是文本，有 `*OK`、`*ER`、`?K,1.00` 这类状态行，全部保留才能事后追查"为什么 EC 是 0"这类问题（这次正是从 `?K,1.00` 的原始回复发现 K 值不符）。代价是记录条数多（约 2.3 条/s），RAM 队列只能缓冲约 27 s 断网，是否精简留待顶层设计决定。
- **为什么固件会写输出设置但不写校准/K**。输出设置只影响回复格式，不影响测量本身，每次启动重写可以保证解析一致；而校准、K、温度补偿会改变测量结果，必须由人工完成并记录（SPEC §41）。

## 文件导航

- [HARDWARE.md](HARDWARE.md)：传感器型号与硬件。
- [WIRING.md](WIRING.md)：接线与供电边界。
- [COMMUNICATION.md](COMMUNICATION.md)：通信参数与脚本行为。
- [PROGRESS.md](PROGRESS.md)：调试进度、原始日志片段与待办。
- [SAMPLE_LOG.md](SAMPLE_LOG.md)：真实原始输出样例与逐字段解释。
- [script/](script/)：Arduino 程序；保留同名 sketch 子目录及全部头文件。
- [tests/](tests/)：主机测试。
