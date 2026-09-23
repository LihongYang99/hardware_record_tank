# camera_node — 水下 PoE IP 相机

已记录 Barlus 相机和 TP-Link/Omada POE150S 注入器商品参数。2026-09-22 实物标签显示相机型号 IPC5MPIR-PBX10、默认 IP 192.168.1.88；用户修正 Jetson 临时地址后报告 ping 已有回应。最终 MAC 对照和视频流仍待验证；商品型号对应关系见 HARDWARE.md。

**重要：当前 304 相机标明淡水用途；不能批准用于项目 15–25 ppt 的长期盐水浸泡。** 规格来源、冲突和验证边界见 HARDWARE.md。

- [HARDWARE.md](HARDWARE.md)：设备描述与待确认型号。
- [WIRING.md](WIRING.md)：PoE 接线记录。
- [COMMUNICATION.md](COMMUNICATION.md)：IP、网络及协议状态。
- [PROGRESS.md](PROGRESS.md)：调试进度。
- [JETSON_NETWORK_DEBUG.md](JETSON_NETWORK_DEBUG.md)：Jetson 局域网调试命令、逐项解释、地址拼写排错和撤销方法。
- [script/](script/)：预留相机采集脚本，当前未实现。
