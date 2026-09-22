# Node-1 — 硬件型号

| 通道 | 探头型号 | 转换器 | 当前固件通信 | 输出 |
|---|---|---|---|---|
| DO | DFRobot SEN0681，海水荧光溶解氧 | Waveshare TTL TO RS485 (B)，独立一块 | UART1；4800 / 8N1；Modbus RTU 地址 1 | DO mg/L、饱和度 %、温度 °C |
| ORP | DFRobot SEN0709 | Waveshare TTL TO RS485 (B)，独立一块 | UART2；4800 / 8N1；Modbus RTU 地址 1 | ORP mV、温度 °C |

两个地址 1 只允许在这里的独立总线上；不能直接并联成一条同地址总线。

本次 2026-09-22 核对 [DO 协议](https://wiki.dfrobot.com/sen0681/docs/21674) 和 [ORP 协议](https://wiki.dfrobot.com/sen0709/docs/23382)，支持上述地址、串口参数和解码。
[Waveshare 说明](https://www.waveshare.com/wiki/TTL_TO_RS485_%28B%29) 本次抓取被 403 阻止；型号和接线沿用已有记录，并非本次重新认证。
当前硬件为用户已拥有的台架设备，不标为长期部署 LOCKED。
