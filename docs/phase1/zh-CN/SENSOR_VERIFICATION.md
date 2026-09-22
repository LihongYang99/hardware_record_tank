# Phase 1 传感器核实与选择（中文读者版）

**英文工程基准：** [Phase-1 Sensor Verification and Selection](../SENSOR_VERIFICATION.md)  
**工作环境：** 100 L 南美白对虾缸，15–25 ppt，名义 0–40 °C，连续运行数周至数月

本页解释为什么某些传感器可以进入项目、某些仍要等待。精确参数和证据链接以英文工程页及厂家资料为准。

## 1. 选择总表

| 测量任务 | 候选设备 | 已知接口/供电 | 对 15–25 ppt 的证据 | 结论 |
|---|---|---|---|---|
| 中层溶氧 | DFRobot `SEN0681` 海水版 | 10–30 VDC、0.2 W、RS485/Modbus | 明确为海水版，支持盐度补偿 | `VERIFIED`；第一条链路 |
| 中层 pH | Atlas `ENV-50-pH-NT`（SMA）+ EZO-pH + `ISCCB-2` | 3.3–5 V、I2C/UART、隔离载板 | 探头资料允许淡/盐水长期浸没至连接器边界 | `RECOMMENDED — REQUIRES PROMOTION` |
| EC/盐度 | Atlas `EC-KIT-10` + 独立 PT-1000 | K10；EZO-EC I2C/UART | 面向盐水，探头资料支持长期盐水浸没 | `RECOMMENDED — REQUIRES PROMOTION` |
| 补偿温度 | Atlas `PT-THRD` + EZO-RTD | PT-1000、I2C/UART | 探头可浸没至 SMA 边界 | `RECOMMENDED — REQUIRES PROMOTION` |
| 浊度 | DFRobot `SEN0710` | 10–30 VDC、0.2 W、RS485/Modbus | 未找到明确的长期 15–25 ppt 承诺 | `VERIFY BEFORE PURCHASE` |
| 氨氮候选 | DFRobot `SEN0711` | 10–30 VDC、0.3 W、RS485/Modbus | 未找到充分的半咸水基质/干扰验证 | `VERIFY BEFORE PURCHASE`；不可直接称 NH4/TAN |
| 底层溶氧 | In-Situ RDO Blue，10 m 裸线镀锡，P/N `0038620` | 8–36 VDC、12 V 时 ≤50 mA、RS485/Modbus | 厂家明确淡水或盐水长期使用 | `VERIFIED`；推荐 |
| 底层 ORP | DFRobot `SEN0709` | 10–30 VDC、0.4 W、RS485/Modbus | 缺长期盐水证明 | `VERIFY BEFORE PURCHASE` |
| 溶解 H2S | SulfiLogger `S1-1020` 低量程 | 12–28 VDC、RS232、4–20 mA | 有水产用途，但缺 15–25 ppt 长期浸没和最大电流 | `VERIFY BEFORE PURCHASE` |
| 旁路流量 | Sensirion `SLF3S-4000B` 评估套件 | 3.2–3.8 V、≤6 mA、I2C | 接液材料已列出，但原厂用水/IPA 标定 | 作为流量存在/相对监测推荐；必须盐水标定 |
| Mg/Ca | 无获批在线型号 | — | 选择性和高离子强度问题未解决 | `DEFERRED`；外部参考检测 |
| NO2-N/NO3-N/碱度 | 无获批连续型号 | — | 连续测量有效性未证明 | `DEFERRED`；外部参考方法 |

> 小白解释：“能通信”只说明 ESP32 可能读得到数字，不代表这个数字在半咸水里有科学意义。盐度干扰、长期浸泡、污染和校准同样重要。

## 2. SEN0681：为什么先从它开始

已核实参数：海水光学溶氧，10–30 VDC、0.2 W；RS485 Modbus RTU；默认地址 1、4800 baud、8N1；DO 0–20 mg/L，饱和度 0–200%；温度 0–40 °C；5 m 线缆。

线色必须保持：

| 线色 | 功能 |
|---|---|
| 棕 | 电源正 |
| 黑 | 电源回路 |
| 黄 | RS485 A |
| 蓝 | RS485 B |

重要寄存器：饱和度从 `0x0000` 开始，DO 从 `0x0002` 开始，温度从 `0x0004` 开始；盐度补偿位于 `0x1020`，压力补偿位于 `0x1022`。

厂家默认盐度补偿为 30 ‰，本项目水体是 15–25 ppt。调试时必须用独立盐度测量值写入并读回验证，不能保留默认值。

采样控制：每 5 s 轮询，命令之间至少 200 ms；保存请求/响应原始字节、解码值、补偿值、序列号、固件和校准事件。超范围、卡死或变化不合理时加 QC 标志，但保留原始响应。

校准按厂家两点法：100% 氧环境，再用 5% 亚硫酸钠无氧溶液。校准液不可回到养殖缸，必须按 SDS/PPE 和化学废液规则处理。

来源：[产品资料](https://wiki.dfrobot.com/sen0681)、[Modbus 协议](https://wiki.dfrobot.com/sen0681/docs/21674)。

## 3. pH：探头、读取电路和隔离板缺一不可

推荐链路：

```text
ENV-50-pH-NT（SMA）→ EZO-pH → ISCCB-2 → Node 1 I2C
```

- `ENV-50-pH-NT` 是无内置温度元件版本，避免混入未说明的复合接口。
- EZO-pH 默认 I2C 地址 `0x63`，支持外部温度补偿。
- ISCCB-2 提供电气隔离；隔离侧和非隔离侧地线不能外接在一起。
- 每次 pH 读取前推送最新有效 PT-1000 温度；温度过旧或缺失仍保留 pH 读数，但加 `COMPENSATION_STALE` 或 `COMPENSATION_MISSING`。
- 使用新鲜 pH 4/7/10 校准液，记录批号、有效期、温度和斜率。

> 小白解释：pH 会随温度影响电极响应。温度补偿不是“美化数据”，而是把测量放到可解释的条件下。

来源：[pH 探头资料](https://files.atlas-scientific.com/IpH_probe.pdf)、[EZO-pH](https://atlas-scientific.com/embedded-solutions/ezo-ph-circuit/)、[ISCCB-2](https://files.atlas-scientific.com/Isccb.pdf)。

## 4. EC/盐度和 PT-1000

推荐 `EC-KIT-10`；K10 探头范围 10 µS/cm–1 S/cm，适合本项目半咸水。EZO-EC 默认地址 `0x64`，可输出电导率、盐度、TDS 和比重。温度使用独立 `KIT-306` 中的 `PT-THRD + EZO-RTD + SCCB`，EZO-RTD 默认地址 `0x66`。

数据规则：原始电导率是主要测量；盐度是同步/派生输出，需要记录算法或固件版本，不能把它当成第二只独立传感器。

校准使用 12,880 和 150,000 µS/cm 标准液，并用接近缸体实际电导的独立认证标准复核。记录电极常数、批号、有效期、温度、人员、UTC 和校准前后值。

`SEN0707` 被本用途拒绝：资料上限只有 20,000 µS/cm、盐度 11,476 ppm，无法有余量地覆盖 15–25 ppt。

来源：[EC-KIT-10](https://atlas-scientific.com/kits/conductivity-k-10-kit/)、[K10 资料](https://files.atlas-scientific.com/l-EC_K_10_probe.pdf)、[EZO-EC](https://atlas-scientific.com/embedded-solutions/ezo-conductivity-circuit/)、[KIT-306](https://atlas-scientific.com/kits/sma-temperature-kit/?attribute_temperature-probe=Threaded+PT-1000)。

## 5. 浊度和氨氮为什么暂缓

### SEN0710 浊度

电气和协议已知：10–30 VDC、0.2 W、RS485/Modbus、0–1000 NTU、默认地址 1、4800 8N1。但厂家资料未明确长期 15–25 ppt 使用。采购前要厂家书面确认接液材料、密封、电缆过渡、清洗方法和预期寿命。

获批后单独改为地址 2，再加入 Node 1 总线。只能发布 `turbidity_ntu`；没有本缸配对重量法 TSS 样本和带版本模型时，不可发布 eTSS。

### SEN0711 氨氮候选

资料称“ammonia nitrogen”0–100 mg/L，并带 pH/温度，但不足以证明半咸水选择性、氯离子干扰、离子强度校正或等同于 TAN/NH4。

初始字段只能叫 `ammonia_n_reported_mg_l`。TAN、NH4+ 和有毒非离子 NH3 不是同一概念；NH3 比例又依赖 pH、温度和盐度。必须用实际水样的低/中/高加标和独立实验室 TAN 结果验证后再决定。

## 6. 底层溶氧和 ORP

### RDO Blue

正确采购配置是 **10 m 裸线镀锡电缆，P/N `0038620`**。已核实长期淡/盐水监测，8–36 VDC，12 V 读数时 ≤50 mA，RS485 Modbus 默认 19200、8E1。

| 线色 | 功能 |
|---|---|
| 红 | 电源正 |
| 黑 | 电源回路 |
| 蓝 | RS485 正，设计接 Waveshare `A+` |
| 绿 | RS485 负，设计接 Waveshare `B-` |
| 银 | 屏蔽/排流线，只能单端接合法干燥机壳/功能地；无合法点则绝缘悬空并记录 |

### SEN0709 ORP

已知 10–30 VDC、0.4 W、RS485/Modbus、-1999 至 1999 mV、默认 4800 8N1。长期半咸水材料和维护证据不足，因此采购前核实。若获批，独占 Node 2 第二路 Waveshare TTL TO RS485 (B)/UART，不与 19200 8E1 的 RDO 共用串口。

## 7. S1-1020 溶解 H2S

已知：12–28 VDC、RS232 与 4–20 mA、低量程约 0–0.5 mg/L；固件 2.7+ 的 RS232 为 38400、8N1、ASCII、LF 结束、传感器作从机。

购买前必须拿到：

1. 15–25 ppt 连续浸没的书面确认；
2. 12 V 最大/启动电流；
3. 0–0.5 mg/L 的准确订货码、线长、端接和维护套件；
4. RS232 与 4–20 mA 配置能否按目标订单同时使用。

电源线和 RS232 线都包含棕/蓝色，必须永久标记 `POWER` 和 `RS232`。通信使用 Waveshare Industrial Isolated TTL to RS232 (B)，不使用非隔离 MAX3232。

## 8. 旁路流量计

首台建议买 `EK-SLF3S-4000B` 评估套件，因为包含夹具和尾线。参数：±600 mL/min、3.2–3.8 V、≤6 mA、I2C 地址 `0x08`、每字 CRC、内部体积约 58 µL、建议 5–6 mm 内径管。

厂家用水/异丙醇标定，不是 15–25 ppt 盐水。因此要在 60、80、100 mL/min 三点各收集 10 分钟液体，按温度和密度换算真实体积，保存校正版本。未完成前只能用于流量存在、趋势和报警。

Node 4 必须经过 DFR0565 隔离；DFR0565 隔离侧先输出 5 V，再由 Pololu D24V5F3 降到 3.3 V。严禁把 5 V 直接送进流量计。

## 9. Mg、Ca、氮盐和碱度的策略

没有获批的连续在线型号，是有意的科学边界，不是文档漏写。

- Mg/Ca：用旁路取样口做时间对齐的抓样，送有资质实验室采用适合盐水的 ICP-OES/ICP-MS、离子色谱或滴定等验证方法。
- NO2-N、NO3-N、碱度、TAN：先使用经验证的外部比色/滴定或实验室方法。
- 保存样品 ID、采样 UTC、保存条件、方法、稀释、检出限、不确定度和结果。
- Hanna `HI97115C` 只作为待验证的筛查工具；Ca/Mg 量程覆盖不了全部预期半咸水浓度，氨的计量基础和亚硝酸盐手册差异也需确认。

## 10. 到货时必须记录

厂家、完整 SKU、硬件版本、序列号、固件、供应商、购买日期、资料版本/哈希、附带线缆长度/端接、实测空闲/工作电流和验收结果。标签或资料与已放行 BOM 不一致的物品要隔离，不要“先试试看”。
