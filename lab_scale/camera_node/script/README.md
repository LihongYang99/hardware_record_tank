# 相机脚本

相机接入代码放在 Jetson 网页目录，不在这里：

- [../../jetson_web/camera_onvif.py](../../jetson_web/camera_onvif.py)：通过 ONVIF `GetStreamUri` 向相机要 RTSP 地址并写入私密 `.env`（只发 ONVIF 读取请求，不改相机设置，不打印地址）。
- [../../jetson_web/server.py](../../jetson_web/server.py) 的 `Camera`：GStreamer `rtspsrc`(TCP) → H.264 → 解码（优先 Jetson 硬件 `nvv4l2decoder`，否则 `avdec_h264`）→ 5 帧/s JPEG → 网页。

不要手写或猜测 RTSP 路径；相机更换设置后重新运行 `camera_onvif.py`。
