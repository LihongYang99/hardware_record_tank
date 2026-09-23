# Camera — 硬件

更新：2026-09-22。以下区分商品标称、厂家同系列资料与现场证据。新增用户标签照片型号为 **IPC5MPIR-PBX10**，默认 IP 为 `192.168.1.88`；不是厂商全部规格验收，也不能自动等同以下商品 SKU。网络调试结果见 [JETSON_NETWORK_DEBUG.md](JETSON_NETWORK_DEBUG.md)。

## 相机：Barlus（用户提供的商品链接）

| 参数 | 记录及证据状态 |
|---|---|
| 商品 / ASIN | Barlus 水下 PoE IP 相机；B07G857V5G [S1] |
| 商品型号 | IPC5MPIP68IR42POE-B；用户实物标签为 IPC5MPIR-PBX10；两个型号对应关系及序列号 **NOT VERIFIED** |
| 图像 | 标称 5 MP、2592 × 1944、20 fps；实际视频流未验证 |
| 镜头 | 标称 3.6 mm；水平视角描述 85°，商品信息另一处写 80°，存在冲突 |
| 对焦 | 页面写“Focus 2Meter”；不能据此认定最小对焦距离，近距离成像 **NOT VERIFIED** |
| 机身 / 防护 | 标称 304 不锈钢、IP68；不是本项目浸泡验收结果 |
| 深度 / 压力 | 页面标称水深 <15 m、最大 150 kPa；未实测，不据此推定盐水耐久性 |
| 线长 | 商品标称 32 ft（约 9.75 m）；厂家同系列默认 10 m，不当作本机精确测量 |
| 网络 | 有线以太网，无 Wi-Fi；标称 RTSP、ONVIF、DHCP、NTP |
| 供电 | 商品标称 DC 12 V 或 PoE 48–54 V；具体版本的标准兼容性、功耗和电源标签待核实 |
| 低照度 | 标称红外照明；波长、对虾行为影响均 **NOT VERIFIED** |

来源：[Amazon 商品页 S1](https://www.amazon.com/dp/B07G857V5G?th=1)。页面信息有冲突，不能将标称参数当作本机实测或安全批准。

### 淡水限制与正式部署冲突

商品说明明确限制淡水、不可用于盐水；页面另一个材料字段却写 seawater grade，不能用该字段覆盖明确的用途限制。[S1]
[Barlus 厂家同系列页面 S2](https://barluscam.com/products/hd-5-megapixel-304-stainless-steel-ip68-waterproof) 也明确说明 304 版本用于淡水、不适合海水。

SPEC 的正式目标为 **15–25 ppt**。因此当前证据**不能批准这款相机用于目标盐度的长期浸泡**；IP68 不代表耐盐腐蚀。该用途状态为 **VERIFY BEFORE PURCHASE / DEPLOYMENT**，不是 LOCKED；已购设备也需在部署前获得厂家针对盐度、时长及准确型号的书面确认或提出替代方案。此处仅记录冲突，不更换设备、不修改 SPEC。

厂家 S2 页面型号有 IPC5MPIR-BX10 / IPC5MPIR-PBX10 两种写法，与 Amazon 型号不同，准确对应关系 **NOT VERIFIED**；其正文还有 4 MP 与表格 5 MP 的冲突。因此 S2 仅用于同系列交叉核对，不能直接移植全部规格。

## PoE 注入器：TP-Link / Omada

用户链接：[Amazon B001PS9E5I](https://www.amazon.com/dp/B001PS9E5I)。当前商品名称为 Omada POE150S；[厂家 S3](https://www.omadanetworks.com/us/business-networking/omada-accessory-poe-adapter/poe150s/) 同时注明 POE150S (TL-POE150S)。本机硬件版本、适配器铭牌仍 **NOT VERIFIED**。

| 参数 | 厂家公开规格 [S3] |
|---|---|
| 类型 | IEEE 802.3af PoE 注入器，自动检测受电设备，不是普通无协商被动注入器 |
| 功率 | 最大 15.4 W；不等于相机实际功耗或线缆末端保证可用功率 |
| 网口 | 2 × 10/100/1000 Mbps RJ45 |
| 电源输入 | 本次所查官方页面列 48 V DC；本机须按实际版本与原配适配器标签确认 |
| 传输距离 | 标称最长 100 m，受线缆及安装条件约束 |
| 工作环境 | 0–40°C；相对湿度 10–90%，无凝露 |

注入器与电源留在干燥区域；不能沿用相机 IP68 等级。尚未完成整套 PoE 配对、启动和持续录像负载验证。
