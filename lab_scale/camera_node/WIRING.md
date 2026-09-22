# Camera — 接线

用户报告通过 PoE 接入同一 MikroTik 路由器局域网；2026-09-22 提供 TP-Link/Omada POE150S 商品链接。实物版本及路由器端口编号尚未确认。

预期连接路径（不是已完成的逐线验收）：

```text
MikroTik LAN → 注入器 LAN / DATA IN
原配电源     → 注入器电源输入
注入器 PoE / POWER+DATA OUT → 相机以太网线
```

端口名称须核对实物；注入器供电规格见 [HARDWARE.md](HARDWARE.md)。不要将相机 DC 12 V 输入与注入器电源输入混为一谈，也不需要给 ESP32 接 PoE 输出。
注入器、电源和未经确认防水的接头保持干燥。当前 304 相机的盐水适用性未获批准。
这是以太网相机节点，不挂在 ESP32 的 GPIO 上，也不使用 Node-1/Node-2 的 UART。
本目录名称不是相机 hostname。
