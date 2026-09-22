# 归档记录 — 2026-09-22 目录归档

## 本次变更

用户指定仓库 `LihongYang99/hardware_record_tank`，要求区分 lab_scale、未来 tank_scale，以及 Node-1、Node-2、camera_node。
已在本地增加独立节点目录、原脚本副本、空密码模板、主机测试、节点 README 和分主题历史摘要。
根 README 更新当前进度与过期的 100 L 描述；SPEC/GOAL 及既有工程文件未在本次变更。
Node-2 IP 记录为用户本次确认的 192.168.88.251，不改固件 DHCP 行为。

## 本次验证

- Node-1 协议主机测试通过（退出码 0）。
- Node-2 严格解析、初始化、双路读取、单路超时及恢复、重启/身份检查、USB 队列模拟测试通过；启用 AddressSanitizer / UndefinedBehaviorSanitizer。
- `git diff --check` 通过。
- 两套程序的真实 `arduino_secrets.h` 路径均被 Git 忽略；新目录只提供空示例文件。
- `.ino` 和运行时头文件原样复制，未更改采集逻辑；Node-2 主机测试仅调整相对 include 路径。
- 本次未向 ESP32 上传、未修改传感器设置，也未重新进行实物采集或 Arduino 固件编译。之前编译和用户实测不冒充本次新硬件测试。

## GitHub 状态

早先 GitHub 接口返回 404，本机 Git 无可用 HTTPS 登录凭据，首次整理只保存在本地。
用户要求重试后，GitHub 连接已能读取该仓库并返回写入权限。远端已有单行 README 和空白 lab_scale/node-1 占位文件。
随后创建远程 tree 时仍返回 403，因此没有远程提交成功。
用户提供 GitHub Desktop 本地仓库路径后，改为整理到 Documents/GitHub/hardware_record_tank，供用户在 Desktop 查看、提交和推送。
整理范围包含 lab_scale、tank_scale、README、.gitignore、SPEC、GOAL、AGENTS、DECISIONS 以及 docs/phase1 既有规划资料；原样保留规划内容并在总 README 区分实测与规划。不复制 output 演示稿版本、真实密码或编译缓存。

## 目录修正

按用户澄清取消 sessions 目录，历史记录移入各节点 PROGRESS.md，硬件、接线、通信拆成独立文件；firmware 目录改为 script。保留代码及历史信息。
