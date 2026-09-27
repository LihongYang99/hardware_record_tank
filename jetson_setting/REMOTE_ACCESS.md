# 从实验室外访问 Jetson 网页（Cisco VPN + SSH 端口转发）

更新：2026-09-27。

## 为什么用这个方法

- **学校不允许在校园网上运行 VPN / 隧道服务**（用户确认）。所以不在 Jetson 上装 Tailscale、Cloudflare Tunnel、ZeroTier、反向 SSH 之类的东西，也不在路由器或校园网开端口。
- 学校提供 **Cisco VPN**，这是允许的。在校外连上 Cisco VPN，电脑就相当于进了校园网，再用标准 SSH 连到 Jetson。
- 网页本身**没有登录**，所以不改它的监听地址：它仍然只在实验室局域网 `192.168.88.249:8080` 上提供。外面的人必须先能 SSH 登录 Jetson，才能通过 SSH 转发看到网页。
- MQTT（1883）和相机（`192.168.1.88`）**不转发、不暴露**。

```text
你的电脑 ──Cisco VPN──▶ 校园网 ──SSH (22)──▶ Jetson 10.141.48.128 (eduroam)
                                                   │ 本机转发
                                                   ▼
                                    网页 192.168.88.249:8080（实验室局域网）
```

## Jetson 端现状（2026-09-27 只读检查）

| 项目 | 状态 |
|---|---|
| SSH 服务 | 已运行（`ssh` active），监听 `0.0.0.0:22`，所有网卡可连 |
| 学校网络 | Wi-Fi `wlP1p1s0` 连 **eduroam**，地址 `10.141.48.128/23`（DHCP，会变） |
| 实验室网络 | 有线 `enP8p1s0`，`192.168.88.249/24`（另有相机用的临时 `192.168.1.200/24`） |
| 用户名 | `lihongyang2026` |
| SSH 登录方式 | 密码（默认配置）；还没有配置密钥登录 |

Jetson 这边**不需要另外开 SSH**。

## 使用步骤（在你自己的电脑上）

1. 人在校外时，先连 Cisco VPN。在校内连 eduroam 时不用。
2. 测试能否登录（第一次会问是否信任，输入 `yes`，然后输入 Jetson 密码）：

   ```bash
   ssh lihongyang2026@10.141.48.128
   ```

3. 能登录后输入 `exit` 退出，改用带端口转发的命令，**保持窗口不关**：

   ```bash
   ssh -L 8080:192.168.88.249:8080 lihongyang2026@10.141.48.128
   ```

4. 浏览器打开：
   - 中文页：`http://localhost:8080`
   - 英文页：`http://localhost:8080/en`
   - CSV 导出：`http://localhost:8080/export.csv`

5. 看完关掉 SSH 窗口，转发随之断开。

如果你电脑的 8080 已被占用，把 `-L 8080:` 改成 `-L 18080:`，浏览器改开 `http://localhost:18080`。

Windows 10/11 自带 `ssh`（PowerShell 可以直接用）；macOS / Linux 在终端运行即可。

## 已验证 / 未验证

| 项目 | 状态 |
|---|---|
| Jetson SSH 服务运行、监听所有网卡 | 已验证（Jetson 本机检查） |
| 从用户电脑 SSH 登录 `10.141.48.128` | **用户报告成功**（2026-09-27）；当时是校内 eduroam 还是校外 Cisco VPN 未记录 |
| 通过 `ssh -L` 打开网页 | 待用户确认 |
| 校外经 Cisco VPN 访问 eduroam 上的设备 | **待验证**：学校 VPN 不一定能访问 eduroam 客户端，需要在校外实测一次 |

## 常见问题

| 现象 | 可能原因 / 处理 |
|---|---|
| `ssh` 卡住或超时 | eduroam 禁止设备之间互连，或学校 VPN 不能访问 eduroam 上的设备；问学校 IT |
| `Connection refused` | Jetson 的 SSH 没运行（Jetson 上 `systemctl status ssh` 查看） |
| 以前能连，现在连不上 | eduroam 地址变了。在 Jetson 上运行 `ip -br -4 addr show wlP1p1s0` 查新地址（需要有人在现场）；长期办法见下 |
| 登录成功但网页打不开 | Jetson 上的网页服务没运行（没有开机自启）；按 [jetson_web README](../lab_scale/jetson_web/README.md) 启动 |
| 网页有数据但相机黑屏 | Jetson 重启后相机网段临时地址丢了；在 Jetson 上重新运行 `sudo ip addr add 192.168.1.200/24 dev enP8p1s0` |
| `bind: Address already in use` | 你电脑的 8080 被占用，改用 18080 |

## 限制与待办

1. **地址会变**：eduroam 用动态地址，人在外面时无法得知新地址。长期办法：请学校 IT 给这台 Jetson 固定地址或校内主机名，或者提供有线校园网口。
2. **SSH 目前用密码登录**，而整个校园网都能连到 22 端口：必须用强密码。建议改成 SSH 密钥登录后再关闭密码登录（要 sudo；**关闭前必须先确认密钥登录成功**，否则会把自己锁在外面）。尚未实施。
3. **服务不会开机自启**：Jetson 重启或断电后，MQTT 接收、网页和相机网段都需要手动恢复，远程也就看不到数据。建议做 systemd 开机自启。尚未实施。
4. **外国访客**没有本校 VPN，这个方法对他们不适用。可以视频会议共享屏幕，或发导出的 CSV；要让他们自己打开网页，需另外征得学校 IT 同意。
5. 按 SPEC，正式网关是 Raspberry Pi。迁移后同样的“Cisco VPN + SSH 转发”方法仍然适用，只需把地址换成 Pi 的。
