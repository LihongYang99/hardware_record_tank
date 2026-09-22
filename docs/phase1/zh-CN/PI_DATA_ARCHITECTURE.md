# Raspberry Pi 实时与数据完整性架构（中文读者版）

**英文工程基准：** [Raspberry Pi Real-Time and Data-Integrity Architecture](../PI_DATA_ARCHITECTURE.md)  
**角色：** Phase 1 常开网关；不依赖 Jetson

推荐 OPEN-16 使用 Mosquitto + Python 入库/QC + PostgreSQL + Grafana + Docker Compose，Pi 主机运行 chrony。状态仍是 `RECOMMENDED — REQUIRES PROMOTION`，不是已经静默修改了决策日志。

## 1. 软件各做什么

| 组件 | 任务 | 小白解释 |
|---|---|---|
| Raspberry Pi OS Lite 64-bit | 最小主机系统 | 管时钟、SSD 挂载、防火墙和容器。 |
| chrony | UTC/NTP 同步，并可服务传感器局域网 | 让 Pi 和 ESP32 对“现在几点”尽量一致。 |
| Mosquitto 2.x | MQTT 消息中转 | 像带身份和队列的邮局。 |
| Python ingestor/QC | 解码、检查、去重、事务入库、回执、QC | 决定消息是否完整并写入数据库。 |
| PostgreSQL | 权威原始/同步/派生数据存储 | 保存原始字节、关系和审计轨迹。 |
| Grafana OSS | 图表和报警显示 | 只读数据库，不改权威数值。 |
| Docker Compose | 固定服务组合和启动方式 | 让部署、健康检查和恢复可重复。 |

不选两套权威数据库；Node-RED 可做原型但不放在关键入库路径；Jetson 以后可读 Pi API/导出，但关闭 Jetson 时基本监测必须照常工作。

生产镜像固定版本和不可变 digest，不使用 `latest`。升级先在复制数据集上通过恢复测试。

## 2. SSD 与目录

microSD 只放操作系统。PostgreSQL、MQTT 持久化、Grafana、日志和导出全部放支持健康监测的 USB 3 SSD。

```text
/srv/shrimp/              # SSD
├── postgres/
├── mosquitto/data/
├── mosquitto/log/
├── grafana/
├── ingest-quarantine/
├── exports/
└── backups-staging/

/opt/shrimp/              # 版本控制的部署配置
├── compose.yaml
├── .env.example          # 不放真实密钥
├── mosquitto/
├── ingestor/
├── migrations/
├── grafana/provisioning/
└── tests/
```

SSD 没有按 UUID 挂载时，数据库必须“失败关闭”，不能偷偷在 microSD 新建空数据库。SSD 至少保留 30% 空间：70% 使用量警告、85% 严重。夜间备份写到另一台实体设备/NAS；每月实际恢复一次。

## 3. MQTT 主题和策略

```text
shrimp/v1/<tank_id>/<node_id>/measurement
shrimp/v1/<tank_id>/<node_id>/event
shrimp/v1/<tank_id>/<node_id>/health
shrimp/v1/<tank_id>/<node_id>/status
shrimp/v1/<tank_id>/<node_id>/ack
shrimp/v1/<tank_id>/<node_id>/command
```

测量、事件、健康和 ACK 用 QoS 1。测量不 retained；status retained 用来显示 online/offline。command 正常 ACL 下禁用，只在获批调试时临时开放并审计；不允许化学投药。

每个节点用独立凭证和 ACL：只能发布自己的遥测、订阅自己的 ACK。ingestor 可订阅所有节点并发 ACK；Grafana 不需要 MQTT 凭证。传感器 LAN 不是物理/管理隔离时必须 TLS，即使隔离也必须认证和 ACL。密钥不进 Git。

> 小白解释：MQTT QoS 1 的 PUBACK 只说明“邮局收到了包裹”，并不证明 PostgreSQL 已经把它永久写好。因此项目还需要数据库提交后的应用层 ACK。

## 4. 每条测量必须带什么

逻辑字段包括：

- `tank_id`、`experiment_id`、`node_id`；
- `boot_id`、`boot_counter`、`sequence_number`；
- `sensor_id`、`sensor_model`、位置；
- 采样 UTC、发出 UTC、单调时钟、时钟同步状态；
- 参数、数值、单位；
- 原始请求/响应字节；
- 传感器状态、QC、固件/驱动/配置/校准版本；
- 温度/盐度补偿值及其年龄；
- RSSI 和运行时间。

线上使用确定性 CBOR 以节省 ESP flash。解码后的 JSON 语义固定。确切 MQTT payload 字节才是首要原始记录；解码值不能替换它。

一轮传感器回复中的多个通道共享一个 sequence number，再按 `item_index` 分成多行。解析或传感器失败时 `value = null`，不可写 0。SEN0711 在验证前只能用 `ammonia_n_reported_mg_l`。

## 5. UTC 和顺序

### Pi

- chrony 从至少三个合适上游 NTP 源同步；
- 只对传感器子网显式开放 UDP 123；
- 不把假 `local` 时钟冒充准确 UTC；
- 容器使用主机 UTC，数据库用 `timestamptz`；本地时区只在显示时转换。

### ESP32

- 启动时 SNTP，同步目标初始每 6 h，最终按漂移验证；
- 未首次同步也继续采样：`timestamp_utc: null`、保留单调时间、加 `CLOCK_UNSYNCED`；
- 时钟跳变记录 `CLOCK_STEP`；旧数据的节点时间永远不重写；
- Pi 收消息时立即加 `gateway_received_timestamp_utc`，数据库提交再加 `database_committed_timestamp_utc`。

每次启动增加持久 `boot_counter`，生成新 UUID `boot_id`，本次启动从 sequence 0 递增。唯一身份是 `(node_id, boot_id, sequence_number)`，不依赖时钟，也能抵抗 MQTT 重复发送。

## 6. 从 ESP 到数据库提交的完整回执

```text
ESP 生成确定性 payload
  → 先写入本地持久环形缓存
  → MQTT QoS 1 发布原始字节
  → ingestor 立即记录网关接收时间
  → 在一个数据库事务中：保存 raw、判定身份/哈希、解码、QC
  → PostgreSQL 成功 COMMIT
  → ingestor 才发布应用 ACK
  → ESP 核对身份 + payload SHA-256 后才从缓存移除
```

ACK 丢失会导致安全重发。同一身份且哈希相同：记录 duplicate 审计，不重复生成科学读数；同一身份但哈希不同：`KEY_COLLISION`，两份原始数据都保存，第二份隔离并报警，绝不覆盖第一份。

数据库故障时不得发应用 ACK。ingestor 可在有限重试后断开，让 broker 持久队列和 ESP 本地缓存形成两层恢复。

## 7. 数据库分层

| 表/层 | 内容 |
|---|---|
| `raw_deliveries` | 每次 broker 投递的准确 bytes、主题、QoS、时间、SHA-256、解码/处置；实验期间不更新/删除。 |
| `canonical_messages` | 每个合法唯一身份的一条权威消息。 |
| `readings` | `values[]` 中每个参数的规范化行。 |
| `reading_qc` | 每条数据可以有多个 node/gateway/manual QC。 |
| `duplicate_audit` | 同 key 同 hash 的再次投递。 |
| `quarantine` | 解析、schema、身份或哈希冲突；原始 bytes 仍在 raw。 |
| `node_health` | RSSI、运行时间、缓存、错误和 NTP。 |
| `calibrations` | 标准液、批号、前后值、系数、人员、UTC 和附件哈希。 |
| `experiment_events` | 投喂、放苗、换水、清洗、用药、取样、维护、配置、停电/断网。 |
| `derived_values` | 带算法版本和来源读数 ID 的派生值，不覆盖原始值。 |

RAW、SYNCHRONIZED、DERIVED 永远分层，不压成一张“最终数据表”。Grafana 账号只读视图；ingestor 没有删除 raw 的权限。

## 8. QC 标志怎么理解

| 标志 | 含义 |
|---|---|
| `WARMUP` | 传感器或调试稳定期。 |
| `OUT_OF_RANGE` | 超出厂家量程；值和 raw 仍保留。 |
| `COMMUNICATION_ERROR` | 超时、帧、CRC、NAK 或 I2C 错误；不能解码时值为 null。 |
| `STALE` | 数据年龄超过该通道带版本门槛。 |
| `SENSOR_FAULT` | 设备状态或自检故障。 |
| `CALIBRATION_REQUIRED` | 到期、标准检查失败或漂移。 |
| `NETWORK_BUFFERED` | 数据因网络延迟后回放。 |
| `COMPENSATION_MISSING/STALE` | 温度/盐度补偿缺失或太旧。 |
| `MANUAL_INVALID` | 授权人员判无效，但原数据保留。 |
| `CLOCK_UNSYNCED/CLOCK_STEP` | 时钟未同步或发生跳变。 |
| `SEQUENCE_GAP` | 宽限/回放后仍确认缺号。 |
| `DUPLICATE` | 同身份同哈希的重复投递。 |
| `KEY_COLLISION` | 同身份不同哈希，隔离并报警。 |
| `PARSE_ERROR` | payload/schema/值无法解析，raw 保留。 |
| `RATE_OF_CHANGE/STUCK` | 变化过快或长期不动；阈值要用调试数据并带版本。 |
| `FLOW_LOW/FLOW_HIGH` | 旁路流量门槛触发。 |
| `MAINTENANCE` | 正在清洗或维护。 |

没有不良标志可视为 OK；不要同时写字面 `OK` 和错误标志。QC 不是删除按钮，可以并存。

## 9. ESP 断网缓存

| 层 | 分配 | 用途 |
|---|---:|---|
| PSRAM 工作队列 | 512 KiB | 编解码、批处理、网络重试；断电丢失。 |
| Flash 持久环 | 2.25 MiB 分区，目标可用 ≥2.0 MiB | 未获得数据库应用 ACK 的准确 payload。 |
| Pi/broker/DB | SSD | 中央持久化和安全去重回放。 |

8 MB flash 初始预算：两个 OTA 应用槽各 2.5 MiB，持久环 2.25 MiB，其余给 NVS/启动/预留。最终偏移由 ESP-IDF 生成并对齐核查；镜像接近槽上限就拒绝，不挤压缓存。

缓存记录含魔数、schema、长度、身份、准确 payload、哈希/完整性字段和 CRC32；双交替头部防止断电撕裂破坏整个队列。Flash 批量提交的未落盘暴露目标 ≤5 s；突然断电可能丢掉这段尾部，但不能生成“看似正常”的损坏记录。

验收要求 p95 单条存储记录 ≤140 bytes。Node 4 以流量 1 Hz + 泵状态 60 s 计算，4 h 约 2.05 MB，是最坏节点。真实验收必须断 Wi-Fi 4 h，再恢复并证明完整、有序、去重入库。若容量不够，应改存储/设计，不能静默降低科学采样率。

缓存满前发严重报警；只有最终明确策略才可丢最老记录，并增加 `data_loss_count`，绝不静默丢弃。

## 10. SSD 容量规划

全部通道含条件性 NH4 时约 178,560 条/天。按每条等效 350 bytes 以及 PostgreSQL 原始+规范行+索引 3 倍规划：约 188 MB/天，约 68.5 GB/年，未含日志/导出/备份。

500 GB SSD 对初期 Phase 1 有较大余量，但真实容量由实测行/索引大小、保留期和实验时长决定。首月每周测 `pg_total_relation_size` 并按 70% 警戒线预测耗尽日期。

## 11. Grafana 应看到什么

1. 缸体概览：最后值、单位、数据年龄、QC、位置；
2. 同步趋势：中/底层 DO、pH、EC/盐度、温度、浊度、ORP/H2S、流量；
3. 数据完整性：缺号、重复、冲突、null、解析/CRC、节点到网关延迟；
4. 节点健康：online/LWT、RSSI、uptime/boot ID、固件/配置、缓存和复位原因；
5. 时钟：节点同步状态/年龄/不确定度和 Pi chrony；
6. 旁路：1 s 原始流量及 1/5/15 min 聚合、泵命令/复位、报警和维护；
7. 校准/维护到期；
8. 基础设施：broker、入库延迟、DB、SSD/SMART、Pi 温度/欠压。

图表转换不能改变权威值；每条派生曲线标明算法版本和来源记录。

## 12. 必须注入的故障测试

- Node 采样时硬重启：新 boot ID，自动重连，旧缓存回放，无畸形记录。
- Wi-Fi 断 4 h：容量足够，恢复后完整有序、重复可去重。
- Mosquitto、ingestor、PostgreSQL 分别重启：无错误 ACK，无双重科学读数。
- Pi 写入时断电：文件系统/DB 自动恢复，节点保留未 ACK 数据。
- 重发完全相同 payload：raw 多一条审计，canonical/readings 不变。
- 同 key 改一个字节：两份 raw 保留，第二份 `KEY_COLLISION` 隔离，无覆盖。
- 故意漏一号：宽限期内可由回放修复，之后才确认 `SEQUENCE_GAP`。
- 坏 CRC/schema：raw 保存、值 null、QC 正确、其他通道继续。
- 启动时禁 NTP：继续采样，UTC null + 单调时间；同步后不重写旧时间。
- 缓存压力到满：丢失前严重报警，任何丢弃都有计数。
- 拔掉 SSD 重启 Pi：服务失败关闭，不能在 microSD 起空库。
- 在干净测试主机恢复备份：数量、哈希、校准、事件和仪表盘匹配恢复点。

一个绿色仪表盘不等于验收完成；真实 SEN0681 必须通过完整链路和相关故障矩阵。

## 13. 实施顺序

1. 盘点 Pi/RAM/电源/SSD，记录 OS 版本。
2. SSD 按 UUID 挂载，做缺盘失败关闭，检查 SMART 和 Pi 欠压。
3. 配置 chrony 和防火墙，验证一只 ESP 的 NTP。
4. 部署固定版本/digest 的 Mosquitto/PostgreSQL/ingestor/Grafana Compose 栈和 ACL/密钥。
5. 执行 schema migration，录入受控的缸/节点/传感器/配置元数据。
6. 用模拟器通过正常、坏数据、重复、冲突、乱序和时钟测试。
7. 接入 SEN0681 → Node 1，保存准确原始帧。
8. 做恢复矩阵、备份恢复和 72 h 连续测试。
9. 只有各通道验收门槛关闭后，才每次增加一个传感器。
