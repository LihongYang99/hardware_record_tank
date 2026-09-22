# Node-2 — 硬件型号

| 通道 | 探头 | 测量电路 | 隔离载板 | 固件接口 |
|---|---|---|---|---|
| EC / salinity | Atlas Conductivity K 10 kit 中的 K10 探头 | EZO-EC | ISCCB-2 | UART1，9600 / 8N1 |
| pH | Atlas Industrial Gen3 pH Probe — No Temp；用户链接选择 3 m SMA | EZO-pH | ISCCB-2 | UART2，9600 / 8N1 |

两块 EZO 实测回复固件版本 2.17；这不是 ESP32 固件版本。
盐度是 EZO-EC 输出，不是另一支独立盐度探头。pH 探头为 No Temp，不能把温度补偿设置当温度测量。
产品入口：[K10 kit](https://atlas-scientific.com/kits/conductivity-k-10-kit/)、[pH probe](https://atlas-scientific.com/probes/industrial-gen3-ph-probe-nt/)。准确实物序列号未记录。
