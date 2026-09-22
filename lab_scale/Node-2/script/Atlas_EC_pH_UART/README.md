# Atlas_EC_pH_UART sketch

完整接线、供电限制、通信与进度见 [Node-2 README](../../README.md)。
保留此文件夹中的 .ino 与所有 .h；将空白 arduino_secrets.example.h 复制为 arduino_secrets.h 并在本地填入 Wi-Fi 信息。
真实密码不提交；初始化会写输出设置，但不写 K、温度或校准。当前只有 USB 日志，尚无 MQTT / UTC 同步。
