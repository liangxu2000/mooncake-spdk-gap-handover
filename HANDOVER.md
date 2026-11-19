# 交接文件（单向：开发指挥 Agent → 测试执行 Agent）

- 仓库：`https://github.com/liangxu2000/mooncake-spdk-gap-handover`（public，匿名 HTTPS 可拉取）
- 首次接入：`git clone https://github.com/liangxu2000/mooncake-spdk-gap-handover.git`
- 之后每轮：`cd mooncake-spdk-gap-handover && git pull`
- 权限：**只 pull，不要 push**；本仓不接收反向提交
- 回执：按下方《回执格式》在会话里输出，由用户转交
- 最后更新：2026-11-19
- 当前任务：**GAP-05（工具补齐与可行性验证，只读 + 仅写 `~/gap`，可立即执行）**；GAP-06（首轮实测）待 GAP-05 回执 + 用户对高风险操作的逐项确认

> **编号变更（2026-11-19，用户定名）**：序列名由用户定为 `GAP-xx`（本项目自有，不沿用同事的 Round 编号）。
> 原 `R7-01` / `R7-02` 已更名为 `GAP-01` / `GAP-02`。若你正在执行旧任务号 `R7-02`，继续执行完即可，回执按 `GAP-02` 登记。

## 协作约定

1. **方向单向**：本文件只由开发指挥 Agent 更新并 push；测试执行 Agent 只 pull。
2. **任务编号**：`GAP-01`、`GAP-02`…（本项目自有序列）；状态：`待执行` / `执行中` / `待回执` / `已关闭`。
3. **事实与推测必须分开**：所有陈述按 `[事实]` / `[推算]` / `[未获取]` 三类标注（沿用你 11-19 交接文档的写法）。
   - `[事实]`：直接读到或实测，附来源（`文件:行号` / 命令 / 原始输出）。
   - `[推算]`：由事实四则运算得到，写出式子，可复算。
   - `[未获取]`：没查到或没权限，写明原因与已尝试的路径。
   - **禁止用默认值、经验值或猜测填充**。查不到比编造有价值；查不到就标 `[未获取]`。
4. **资料最小化**：回执只给结论、`文件:行号`、`≤20 行`原始输出片段；不贴整文件、大段日志或源码。
5. **回执格式**（每个任务固定五段）：

   ```
   一句话结论
   1. 结论（按问项逐条编号回答）
   2. 证据（file:line / 命令 / ≤20 行原始片段）
   3. 未做 / 未获取（原因）
   4. 风险与偏差
   5. 产物（路径清单；本次无产物则写"无"）
   ```

6. **安全红线（所有任务默认生效）**：

   > **共用机约束（2026-11-19 用户重申，最高优先级）：node2 / node4 为公用机，当前非独占。**
   > - 禁止停止、挂起、renice、信号干扰任何非本方进程；禁止触碰他人启动的 master / client / target / 压测进程。
   > - 禁止重启 master / target 或任何共享服务；禁止走 target takeover / restore；禁止装卸共享驱动。
   > - **只有用户在当轮对话中明确宣布"独占"（如"佛挡杀佛"）时**，才允许对确认占用资源的他人进程按 PID 处理（先 TERM，10 s 后 KILL；仍禁止 pkill/killall）。
   > - 任务书里若与本条冲突，以用户当轮明确口径为准；没有明确宣布，一律按共用机处理。

   - 默认只读；不启停进程、不碰盘/vfio、不改文件、不重启、不装卸驱动。
   - 需要写临时探针脚本时沿用 base64 方式写到 `/tmp`，用后立即删除。
   - 禁止 pkill/killall；不动非本方进程（含"看起来空转"的进程）。
   - 不 reboot；不 rmmod 底层驱动。
   - 所有远程命令非交互（`sudo -n`），不等待输入。
7. **长任务**：预计超过 30 min 的任务，每 ~15 min 输出一行进度（阶段 / 已完成问项 / 阻塞）。
8. **不猜原则**：任务书中凡要求取证的点，一律以实测或源码为准；无法取得的，按 `[未获取]` 记录并说明，不要下结论。
9. **长命令状态汇报**：编译、压测、长脚本执行期间，按 §7 定期报进度，不要长时间无输出。

## 端口规范（2026-11-19 用户定，所有任务生效）

**不能照搬同事的端口。我们启动的 Mooncake 组件端口一律以 6 结尾；SPDK nvmf target 用 4457。**

| 组件 | 端口 | 说明 |
| --- | --- | --- |
| SPDK nvmf target listener（trsvcid） | **4457** | 固定。旧 4421 / 4420 停用；若已有旧 listener，先 `nvmf_subsystem_remove_listener` |
| Mooncake master RPC | **50056** | 必须显式传（默认 50051） |
| Mooncake master HTTP metadata | **8086** | 必须显式传（默认 8080） |
| Mooncake master metrics | **9006** | 必须显式传（默认 9003） |
| Mooncake client 侧 RPC | **50156** | 必须显式传（具体开关在任务预检里核实） |

- **本轮机器（2026-11-19 用户定）：node1 / node3**。角色（连接文档声明，GAP-04 核实）：**node1 = initiator / client（有 GPU）**，**node3 = target / master（无 GPU）**；两台不同物理机，数据跨机。**必须保持 initiator ≠ target**（组长第 1 条要求）。
- **独占与高风险授权（2026-11-19 用户宣布）**：node1/node3 现为本方独占；**GAP-05 §0 的两个遗留进程停止、GAP-06 的 vfio 接管/还原与本方 target/master 启停，均已获用户当轮整体授权**。仍禁止：pkill/killall、reboot、rmmod udma、动他人进程；异常即停并回报；**授权范围之外的新类型高风险动作**仍需先问。
- **启动前必须做端口占用检查**；任一端口被他人占用 → 停手回报，不得抢占、不得改回同事的端口。
- 已核实的源码事实（供预检对照）：
  - master 三个端口都有显式 flag：`--rpc_port` / `--http_metadata_server_port` / `--metrics_port`（`mooncake-store/src/master.cpp:134/410/547`）。
  - SPDK `target_nvme_takeover.sh:96` 把 `LISTEN_PORT` 写死为 4420 → **用脚本副本改 4457**，不改原脚本，记录原/新脚本 md5。
  - TE RPC 端口范围 `MC_MIN_RPC_PORT / MC_MAX_RPC_PORT` 经 `mooncake-transfer-engine/src/config.cpp:842` 的 `ValidatePortRange` 校验，**排除 32768–60999（临时端口段）**；50156 落在该段内 → 若客户端走这两个 env，50156 会被拒绝并回落到 15000–17000。50156 到底由哪个开关控制，必须在预检里核实；若无法设置，回执提出替代（如 15556 / 16556，同样以 6 结尾），由用户定。

## 工作目录铁规（2026-11-19 用户定，node1/node3 生效）

- 在 node1 与 node3 上各自创建 **`~/gap`**（用户指定 `~/gap`）作为唯一工作目录；用户已授权创建。
- **所有写入只允许发生在 `~/gap` 内**：脚本、日志、结果、V3 文件、临时文件。`/tmp` 仅限一次性探针且用完即删，长期产物一律放 `~/gap`。
- **`~/gap` 之外一律只读**：可以只读查看或执行已有的二进制、库、脚本与系统路径；**严禁修改、删除、移动、创建任何 gap 外的文件或目录**。
- 回执/台账里的产物路径写 `~/gap/...` 形式，不写绝对 home 路径。

## 背景与总目标（供理解任务用，回执不必复述）

项目总目标：**消除 Mooncake 与裸 SPDK 在 8 MiB 读上的 ~200 µs 时延差距**。这是同事交接的原始问题，
也是最终交付物——不是写分析报告，而是把差距消掉。参照值以用户指定的 Round5 诊断文件为准（见任务 G1）。

你的 11-19 交接文档（Round6 事实清单）是当前基线；Round6 已量出差距，并拿到部分 target 侧分段账本与客户端 RPC RTT
（数字以你的文档 §4 为准，本仓不重复）。

我们的路径：**先定位、后消除**。第一步是在同一 target 配置、同一测量窗口、同一套打点下，对 Mooncake 与裸 SPDK
的 seq / rand 各臂同时取 target 侧分段与客户端侧分段，把 ~200 µs 差距定位到具体层、具体段；定位清楚后再选优化项。

`GAP-01` 是只读前置任务：把设计首轮实测（`GAP-06`）所需的开关、风险、口径查清楚。**该任务不跑任何压测。**

## 任务历史

| 编号 | 日期 | 内容 | 状态 | 回执摘要 |
| --- | --- | --- | --- | --- |
| GAP-01（原 R7-01） | 2026-11-19 | 只读情报：首轮实测设计前置（打点开关 / target 重新拉起的数据安全 / 客户端阶段通道 / 对照口径 / worker 旋钮 / 同事 Round5 诊断文件 / 源码版本与二进制归属） | 已关闭 | 同一 `nvmf_tgt`（md5 `95ce0bfd…`）；两路 target 参数 4 处不同（`-s`/taskset/`-L`/`-I`）；master 心跳实际关闭（3600s×999999），500k keys 元数据仍在（4.19 TB，精确 500000×8 MiB）；同事 Round6 无 prefill；客户端仅阈值采样/≤8192 行 CSV；裸 SPDK=`urma_perf -T1 -b1`、rand 覆盖全 namespace；H 节未答（并入 GAP-02） |
| GAP-02（原 R7-02） | 2026-11-19 | 只读：补 H 节（源码/二进制归属 + 未提交文件 diff）+ 打点能力核对 + 实测参数匹配事实 | 已关闭 | 三套打点在三个二进制均可用（V3 env 串在，魔数不显）；两节点 `nvmf_tgt` 非同一文件（被测 target 在 node4）；`-L`/`-I` 实际相同，实质差异只剩 `-s` 与 taskset；源码树 7 处未提交改动（node2 多 `urma.c` +44 行）；Mooncake 客户端运行期 liburma 为第三条路径（md5 `87d4fb60…`）；ns 容量 84.5 TB = Mooncake 工作集的 15.4 倍；V3 源码在 HEAD（宏拼接，回执"源码已不在磁盘"的判断需更正） |
| GAP-03 | 2026-11-19 | 只读条件审计：把同事全部实验逐臂提取「客户端/target/master 节点、数据路径是否跨节点、参数与库」，标出同节点/条件不可比的数字 | 已关闭 | 归档结果中**没有** initiator=target 同节点的 8 MiB gap 对比（R5/R6/R11 均 node2→node4，R11 有 includes_same_host=False）；r7bi 系列 target 在 node2 且无测量输出，不可用；`0.4667 ms vs 259.92 µs` 因 strip 256 vs 128 + taskset/-s 不同**不可比**；R6 rand 655.6 vs 327.2 因随机范围 15.4× **不可比**；R6 seq 466.6 vs 245.7 仅差 taskset/-s；可用基线=Round6 框架内 Mooncake 各臂与 R6 SPDK 各臂自身 |
| GAP-04 | 2026-11-19 | 新环境接入与只读侦察：node1/node3 连接与角色、硬件/盘/URMA、代码与二进制（含 V3 打点）、端口占用、工作集与容量 | 已关闭 | 两台可登录、不同物理机；文档角色 node1=initiator/client、node3=target/master；node3 的 `nvmf_tgt` 带完整 V3（md5 `e7440ae0…`），**node1 的 `urma_perf` 与我方 Mooncake 客户端均不带 V3**；盘各 11×7.68 TB；4457 空闲；node3 的 50056/8086/9006/50156 被**本方 23 h 遗留进程**占用；工作集=0；node3 大页 9.06 GB（iobuf 需 ~8.06 GB，余量小）；两台 liburma `5c021f7f…`（≠ node2/4） |
| GAP-05 | 2026-11-19 | 工具补齐与可行性验证（只读 + 仅写 `~/gap`）：e3bd 栈盘点、跨机复制并 `--help` 验证 urma_perf / Mooncake client、确认 50156 开关、大页核算 | 待执行 | — |
| GAP-06 | 2026-11-19 | 首轮实测（待 GAP-05 回执 + 高风险操作逐项确认）：按端口规范起本方 target/master + prefill；同参数 6 臂 × 60 s，客户端 V3 逐请求账本 + target 聚合 dump，输出各段分解 + 条件台账 | 待执行 | — |

---

# GAP-01（已关闭 · 2026-11-19）· 只读情报收集：首轮实测设计前置

> 回执已收（见任务历史摘要）。H 节未答，并入 GAP-02。

> **性质：纯只读**。不改任何文件、不启停任何进程、不碰盘/vfio、不重启。不需要独占窗口。
> 若某个问项必须写操作才能取证：跳过，在回执里记 `[未获取] 需要写操作`。
> 机器：node2、node4（即你 11-19 交接文档中的两台）。
> Round6 中你已经读全的配置与结果不必重读；本任务只查下方问项。

> **开发侧已从公开源码核实（SPDK `e12b7cb21` / Mooncake `706551a8`），下列问项只需核对本机部署与源码一致，不必重新探索：**
> - target 聚合分段：`SPDK_URMA_TARGET_DUMP_SEC=<秒>`（transport 创建时读取，周期 dump；`target_nvme_takeover.sh -s <秒>` 即此开关），代码常开，无需特殊编译。
> - per-IO 跨端账本（GAP-06 可用）：initiator 设 `SPDK_URMA_STAGE_TRACE_US=<µs>` 后每个请求才带 `trace_seq`；两侧设 `SPDK_URMA_STAGE_{READER,TARGET}_SINK=buffer` + `_PATH`（文件，O_EXCL）+ `_CAPACITY`（记录数，192 B/条）后，进程退出时落二进制文件（头/尾魔数 `URMA3B01` / `URMA3END`，side=1 initiator / 2 target）。
> - `SPDK_URMA_TRACE=1` 只控制 LEGACY 模式下的 per-IO CSV tx/rx trace；LEGACY 模式下 initiator 对超阈值请求打印 `URMA_SLOW_IO ...` 行（含 target 各阶段 tick）。
> - `MC_WORKERS_PER_CTX` 默认 2（transfer-engine env）。
> - master NoF 心跳默认：间隔 10 s、单次探测超时 1000 ms、连续失败阈值 3（≈30 s 卸载）；`--nof_heartbeat_interval_sec / --nof_heartbeat_probe_timeout_ms / --nof_heartbeat_failures_threshold` 为 master 启动参数。
>
> **但机器上有两个未提交修改文件（`urma_perf.c`、`trace_defs.h`），且两仓远端分支已前进（SPDK 尖端 `e90642ea3`、Mooncake 尖端 `af253a2`）——所以"机器实际运行的代码"仍需 H 节核对。**

## A. target 侧阶段计时

- **A1** Round6 中 Mooncake 测试与裸 SPDK 测试各自启动的 target：分别使用哪个 `nvmf_tgt` 二进制（路径 + md5）？是否同一个文件？给出启动脚本的 `文件:行号`。
- **A2** 核对：本机 `nvmf_tgt` 二进制是否包含上述聚合打点与 stage buffer 代码（用 `strings` 找 `URMA3B01`、`SPDK_URMA_STAGE_TARGET_SINK`、`SPDK_URMA_TARGET_DUMP_SEC` 即可）；Round6 `seq_diag` 的启动命令里实际带了哪些开关（脚本/日志原文 ≤10 行）。
- **A3** 核对：本机版本与公开 `e12b7cb21` 的打点差异（若 H2 的 diff 涉及打点代码，指出文件:行号）；`seq_diag` 那次的 target 日志是否就是聚合 dump。
- **A4** 若 A1 结论是两套测试用的不是同一个二进制：逐项列出两边 target 启动参数差异（strip、`-C` / `-U`、reactor/核、iobuf、队列深度、listener 等），并给出各自来源 `文件:行号`。

## B. 本方测试 target 重新拉起时的数据安全（只取证；**本任务不启动、不重启、不 takeover**）

> **先澄清对象**：本节说的 target 指 **Round6 中你按 `target_nvme_takeover.sh` 拉起的那个 SPDK NVMe-oF target（node4）**，
> 属于本方测试链路，不是任何同事的服务；按你 11-19 文档 §1.2，它目前处于停止状态（无 `nvmf_tgt`、端口未监听、vfio 无设备）。
> 本节全部是只读问题，只回答"**将来若在用户明确授权的窗口内重新拉起它**，数据会怎样"。
> **不要启动、不要重启、不要 takeover/restore、不要碰 shared master**；任何启停都必须由用户在当轮明确授权。

- **B1** Mooncake master 对 NoF 段的心跳/卸载逻辑：心跳间隔与超时次数（即多少秒会 unmount）、unmount 后已注册 key 的状态（失效/保留），给 `文件:行号`。
- **B2** target takeover / restore 脚本各做了什么：RAID0 成员盘与顺序在哪写死、strip 多少、是否对盘上数据做过校验或写操作（`文件:行号`）。
- **B3** 当前 500,000 keys 的工作集是否可判定仍存在：给出只读查询命令与输出（master 的 key 数 / 内存分配比例 / NoF 段状态，任一可得即可）；若无法判定，说明缺什么。
- **B4** 若将来需要重启 master（同样只在用户授权的窗口内）：key 是否全部丢失？给源码或历史实测依据，不执行。若丢失，给出 Round6 实测的 prefill 写入量与耗时（从 driver.log 取，标明出处行）。

## C. 客户端阶段账本

- **C1** 核对：本机 `urma_perf` / Mooncake 客户端链接的 SPDK 库中是否存在 `SPDK_URMA_STAGE_READER_SINK` / `SPDK_URMA_STAGE_TRACE_US` 及 `URMA3B01` 字样（`strings` + `文件:行号`）。注意：这是 **URMA 传输层**的阶段（submit/send/completion + 对端 target 阶段），不是 Mooncake 的 NoFRead/Query/Wait 层。
- **C2** Mooncake 客户端层（Query / NoFRead / Submit / Wait）的现成计时通道：`spdiag` 之外还有哪些（env/日志/编译开关），各自覆盖哪些阶段、开销如何；给 `文件:行号`。
- **C3** `spdiag` 的 SHM 由谁创建、谁附加：为什么 master 先启动、SHM 后创建时表为空（`文件:行号`）；是否存在不重启 master 的热附加通道。
- **C4** 除 `.ylt.log` 的 `rtt_us=`（已知）外，还有哪些现成客户端通道能给出每请求阶段耗时（env / 日志 / trace 点），各自开销如何。

## D. 裸 SPDK 对照口径

- **D1** Round6 裸 SPDK 8 MiB 测试的完整信息：initiator 程序名、完整命令行（≤15 行原文）、QD/线程数、随机 LBA 范围、每 rep 时长、rep 次数；给 `文件:行号`。
- **D2** 该 initiator 与 Mooncake 客户端对 8 MiB 请求的拆分（child 数 / child 大小 / 并发方式）是否一致？不一致给证据。

## E. nof_workers

- **E1** `nof_workers=4` 的来源：env / 配置文件 / 默认值 / 命令行？给 `文件:行号`。
- **E2** 调到 8 / 16 需要改什么、是否必须重启 client 或 master、是否会触发 key 失效或需要重做 prefill。

## F. 快项

- **F1** 完整读取 `equal_key_audit.json`，把 rand 与 seq_b 两个臂的跳跃分桶补全（只给表，不贴文件）。
- **F2** node2 / node4 当前相关进程与监听端口快照（只读，一行一项；含进程属主、启动时长、启动命令/工作目录，并标注是否属于 Round6 本方测试链路；依据不足标 `[未获取]`，不要猜）。
- **F3** 同事 Round6 每个 Mooncake arm 的总耗时（driver.log 的 rc 与总时长），用于估算实测窗口。

## G. 用户指定的本地诊断文件（只读）

- **G1** 读取本地 `5.round5_diagnosis\RESULTS_20261118.md`（即你 11-19 文档 §10 本地路径清单里 `5.round5_diagnosis` 目录下的该文件）。用户点名要求以它为参照。回执给出：
  - 文件章节结构（标题列表）；
  - Mooncake `0.4667 ms` 与 SPDK `259.92 µs`（≈200 µs gap）这两个数字在该文件中的出处（`行号`）；
  - 该文件已经给出的**根因判断 / 结论 / 待办**逐条摘录（每条 ≤2 行，注明行号）；
  - 该文件里已列出但尚未解决或未验证的点（逐条）。
  - 不要贴整份文件；总摘录 ≤40 行。
- **G2** 该文件与你 11-19 文档（Round6 事实清单）的**冲突点**：若两处数字或结论不一致，逐项列出（各自给行号）。

## H. 源码版本与二进制归属核对（只读）

> 你提供的两仓信息已由开发侧核实为 public；以下逐条核对"机器上的代码/二进制"与"公开 commit"是否一致。**只读 git 命令，不 fetch、不 pull、不 checkout、不改文件。**

- **H1** node2 / node4 上 SPDK 源码树位置；每棵树的 `git rev-parse HEAD`、`git status --porcelain`、`git remote -v`、`git branch --show-current`（或 `git describe --all`）。确认是否与你提供的 `e12b7cb21` / `urma_enable_v2` 一致，两节点是否同一棵树。
- **H2** 两个未提交修改文件的差异：`examples/nvme/urma_perf/urma_perf.c`、`include/spdk_internal/trace_defs.h` 的 `git diff --stat` + 完整 diff（≤200 行；超长给 hunk 标题 + 关键 hunk）+ 两文件的 `md5sum`。
- **H3** 二进制归属：`nvmf_tgt` 与 `urma_perf` 的可执行文件路径 + `md5sum` + `ls -l` 时间；用构建目录里的 .o/ninja 时间或 `strings` 特征，判断它们是否由 H1 这棵树 + H2 的修改编出（不需要重编）。
- **H4** Mooncake 源码树（node2 的 `mooncake-930`）：`git rev-parse HEAD`、`git status --porcelain`、`git remote -v`；确认是否 `706551a8` / `nof-gdr-supercache-snapshot-930`，是否也有未提交修改（若有，同 H2 给 diff）。
- **H5** 部署文档一致性：`docs/yin/mooncake_nof_deployment.md` 记录的是旧配对（`urma_modified_v6` + `nof-urma-v2`），与当前分支不一致；只需列出该文档中**仍在使用、但可能与当前代码不符**的启动参数或 env（≤10 条，给文档行号），不要贴全文。

## 约束

- **共用机、非独占**：不触碰任何非本方进程；不重启 master / target；不走 takeover / restore；不装卸驱动（详见《协作约定》§6 最高优先级红线）。
- 纯只读：不启动/停止任何进程，不 mount/unmount，不碰 vfio 与盘，不修改任何文件（`/tmp` 探针脚本用完即删）。
- 不运行任何压测、不重新 prefill。
- 非交互执行（`sudo -n`）。
- 回执按《协作约定》§5 五段格式；逐条编号回答 A1–H5，**不要下结论性判断，只给事实与依据**。

## 回执必答的一句话（放在回执第一行）

GAP-06 能否在 ①不重做 prefill ②两套测试同 target 二进制同参数 ③两端都开阶段计时 这三个前提下开跑；不能的部分，缺什么。

---

# GAP-02（已关闭 · 2026-11-19）· 只读：补 H 节 + 首轮实测前置核对

> 回执已收。**一处更正**：回执判断"V3 源码已不在磁盘上"不成立——`SPDK_URMA_STAGE_READER_SINK`
> 在源码里是宏拼接（`URMA_STAGE_ENV "SINK"`，见 `include/spdk_internal/urma_stage_buffer.h:38` 与 `:108`），
> 所以源码 grep 全名必然为 0；该头文件在本机 HEAD（`e12b7cb21`）中且未被修改。GAP-06 §0.2 会做一次只读确认。

> **纯只读**：不启动/停止任何进程、不碰盘/vfio、不跑压测、不修改文件（`/tmp` 探针脚本用完即删）。
> 你 GAP-01 的回执 A–G 已收到；本任务补齐未答的 H 节，并加 I/J 两节，为首轮实测 GAP-06（需用户独占窗口）定参数与账本方案。
> 目的只有三个：①确认机器代码/二进制与公开 commit 的差异；②确认三套打点在三个被测二进制里各自是否可用；③拿到参数匹配所需的事实。
> 机器：node2、node4（共用机、非独占，红线同《协作约定》§6）。

## H. 源码版本与二进制归属（若 GAP-01 已做过，直接复用结果）

- **H1** node2 / node4 上 SPDK 源码树位置；每棵树的 `git rev-parse HEAD`、`git status --porcelain`、`git remote -v`、`git branch --show-current`（或 `git describe --all`）。确认是否为 `e12b7cb21` / `urma_enable_v2`，两节点是否同一棵树。
- **H2** 两个未提交修改文件：`examples/nvme/urma_perf/urma_perf.c`、`include/spdk_internal/trace_defs.h` 的 `git diff --stat` + 完整 diff（≤200 行；超长给 hunk 标题 + 关键 hunk）+ 两文件 `md5sum`。
- **H3** 二进制归属：`nvmf_tgt`、`urma_perf` 的路径 + `md5sum` + `ls -l` 时间；用构建目录 .o/ninja 时间或 strings 特征判断它们是否由 H1 这棵树 + H2 的修改编出（不重编）。
- **H4** Mooncake 源码树（node2 的 `mooncake-930`）：`git rev-parse HEAD`、`git status --porcelain`、`git remote -v`；是否也有未提交修改（若有，同 H2 给 diff）。
- **H5** 部署文档一致性：`docs/yin/mooncake_nof_deployment.md` 记录的是旧配对（`urma_modified_v6` + `nof-urma-v2`）；只列出该文档中**仍在使用、但可能与当前代码不符**的启动参数或 env（≤10 条，给文档行号），不贴全文。

## I. 打点能力核对（决定 GAP-06 用哪套客户端账本）

- **I1** `nvmf_tgt` 二进制 strings 检查：`URMA3B01`、`SPDK_URMA_STAGE_TARGET_SINK`、`SPDK_URMA_TARGET_DUMP_SEC` 是否出现（各给 是/否 + 1 行样例）。
- **I2** `urma_perf` 二进制 strings 检查：`URMA3B01`、`SPDK_URMA_STAGE_READER_SINK`、`SPDK_URMA_STAGE_TRACE_US`。
- **I3** Mooncake 客户端实际链接的 SPDK：`ldd` 解析出的库路径 + md5；对这些库做与 I2 相同的 strings 检查。若客户端是多进程（client/master），指明哪一个进程负责 NoF 读写。
- **I4** 汇总一张表：三套通道（target 聚合 dump / LEGACY `URMA_SLOW_IO` 慢 IO / stage buffer V3）在 **nvmf_tgt、urma_perf、Mooncake 客户端** 三处各自可用与否。只给事实，不给建议。

## J. 实测参数匹配所需事实（只读）

- **J1** Mooncake target 启动的实际 `-I` 值：从 `start_mooncake.py` 的 `select_nvme_devices` 逻辑推导（给公式与变量来源），或从 Round6 target 启动日志/命令行快照里找实际值；给 `文件:行号`。
- **J2** 两条 `-L` 库目录（Mooncake 侧 `/home/tong/umdk_gpu_isolated/lib`、裸 SPDK 侧 `/home/yin/gdr/UMDK_netlab/lib`）的文件清单：`liburma*.so*`、`liburma_common*` 的 `ls -l` + `md5sum`；判断是否同一构建。
- **J3** bare SPDK 侧 `run_exp.sh` 是否支持/方便加 taskset（给位置与用法）；Mooncake 侧 `taskset -c 2-7` 与 `-m 0xfc` 的对应关系（`文件:行号`）。
- **J4** namespace 容量（bytes）：从 target 启动日志、RPC 输出或盘容量任一处给出，用于换算 `urma_perf` rand 的实际 LBA 范围。
- **J5** 最近一次 Mooncake target 的完整启动命令行原文（≤6 行）与拉起时间，确认 `-s 10`、`-I`、`-L`、taskset 的实际组合。

## 约束

- 共用机、非独占：不触碰任何非本方进程；不重启 master/target；不走 takeover/restore；不装卸驱动（《协作约定》§6）。
- 纯只读；非交互 `sudo -n`；不跑压测、不 prefill。
- 回执按《协作约定》§5 五段格式；逐条编号回答 H1–J5，只给事实与依据。

## 回执必答的一句话（放在回执第一行）

三套打点在三个被测二进制里各自是否可用；`-L` 两条库是否同一构建；Mooncake target 的 `-I` 实际值是多少。

---

# GAP-03（已关闭 · 2026-11-19）· 只读条件审计：同事全部实验的节点/参数/条件台账

> 回执已收（见任务历史摘要）。关键：归档中无同节点 gap 对比；历史参照数字对均存在条件差异，不能直接当"同参数 gap"。

> **纯只读**：不启动/停止进程、不碰盘/vfio、不跑压测、不改文件（`/tmp` 探针脚本用完即删）。
> 背景：组长提出三条硬要求——①同事有些测试做错了（存在"在同一个节点上做"的情况），要查出来并避免；②SPDK 与 Mooncake 的对比必须同场景、同参数，否则"gap"不成立；③每次测试的参数与条件必须记录清楚，才能判断是否符合要求。
> 本任务把同事的资料逐实验、逐臂提取成一张"条件台账"，并标出**不能用于 gap 对比**的数字。**只给事实与出处，不下结论。**

## 1. 逐臂台账（每个实验/每条结果一行）

对你能访问到的每一份同事结果（含本地 `5.round5_diagnosis`、机器上 `/home/yin/round6_results/` 与 `/home/yin/round6_seq_avg_rand_p99/`，以及其它同事资料目录），逐臂提取：

| 字段 | 说明 |
| --- | --- |
| 来源 | `文件:行号`（结果/脚本/日志） |
| 实验/臂 | 名称 |
| initiator 节点 | 实际执行读请求的节点（依据：脚本 SSH 行 / driver.log / 命令行） |
| target 节点 | 被读的 `nvmf_tgt` 所在节点（依据：listener IP / takeover 日志） |
| master 节点 | 元数据服务所在节点 |
| 数据是否跨节点 | 是 / 否 / 无法判定（同节点或 127.0.0.1 / 本机 IP 一律标"否"） |
| 关键参数 | strip、`-C/-I/-O/-m/-L`(md5)、taskset、worker/队列、`-s`、传输方式 |
| 负载参数 | I/O 大小、seq/rand、种子、随机范围、QD、时长、warmup、measure mode |
| 结论可用性 | 可用于 gap 对比 / 不可用（原因） / 仅单机参考 |

## 2. 重点核查（组长第 1 条）

- **2.1** 是否存在 initiator 与 target 在**同一物理节点**的实验（数据走本机/回环，不是跨机网络）？逐条列出并给证据。
- **2.2** 是否存在文档写"跨节点"、但日志/参数显示实际同节点的实验？
- **2.3** `--client-node / --target-node / --master-node` 这些参数在各脚本里是否真的被使用（不是摆设）？给 `文件:行号` 与对应的 SSH/执行行。
- **2.4** 单盘 vfio / 本地画像类实验（如 Round6 E 节）若为单机设计，单独归类为"单机参考"，不要与跨机 gap 混用。

## 3. 条件可比性核查（组长第 2、3 条）

- **3.1** 列出同事材料里**所有被用来做 SPDK vs Mooncake 对比的数字对**，逐对标注两边的 strip、I/O 大小、QD/并发、随机范围、target 参数、节点角色。任一项不同 → 标"条件不可比"。
- **3.2** 特别核对：`0.4667 ms`（Mooncake）与 `259.92 µs`（SPDK）这一对，以及 Round6 的 466.6 vs 245.7、655.6 vs 327.2，各自的条件是否一致（strip、节点、随机范围、target 参数）。
- **3.3** 给一张"**可用数字 / 不可用数字**"清单：可作为 gap 证据的数字与出处；不能用的数字与原因。
- **3.4** 同事各实验用的端口：master RPC / HTTP metadata / metrics、target listener、客户端 RPC 各是多少（`文件:行号`）；是否存在端口冲突、复用别人端口、或改了端口未 remove 旧 listener 的情况。
- **3.5** 历史 prefill 事实：同事材料里是否有 prefill 的记录（写入量、耗时）；若有给出处，没有则标 `[未获取]`。用于估算 GAP-06 §1b 的时间。

## 4. 交付

- 台账表（每臂一行，≤40 行；字段多可用分号分隔）。
- 2.x / 3.x 的逐条回答与证据（`文件:行号`，每条 ≤20 行摘录）。
- 一张"需要重测 / 重新建立基线"的清单。

## 约束

- 只读；共用机非独占；不碰任何进程/服务（《协作约定》§6）。
- 不跑压测、不启停、不 takeover、不 prefill。
- 回执按 §5 五段格式；先给台账，再给证据；**不要下结论性判断**。

## 回执必答的一句话（第一行）

是否存在同节点（数据不跨机）的测试；哪些用于 gap 对比的数字对条件不可比；哪些数字可以继续用作基线。

---

# GAP-04（已关闭 · 2026-11-19）· 新环境接入与只读侦察：node1 / node3

> 回执已收（见任务历史摘要）。四个硬缺口：①node1 无我方 Mooncake 客户端；②node1 的 `urma_perf` 无 V3/慢 IO；③node3 的 4 个端口被本方 23 h 遗留进程占用；④node3 大页余量仅 ~1 GB。另：工作集为 0，需 prefill。

> **只读侦察 + 唯一写动作：在两台各创建 `~/gap`**。除此之外不启停进程、不碰盘/vfio、不跑压测、不改任何文件；gap 外只读（见《工作目录铁规》）。

## 0. 建立工作目录（唯一授权的写动作）

- 在 node1 / node3 各执行 `mkdir -p ~/gap`；记录绝对路径、属主、权限。
- 可写性验证：在 `~/gap` 内 `touch` 一个探针文件再删除。
- 之后所有探针/记录/产物一律写 `~/gap`；gap 外只读。
> 背景：用户决定把实测换到 **node1 / node3**（2026-11-19）。这两台是旧项目环境，代码/二进制/盘可能与 node2/node4 不同，必须先核实再定 GAP-06 的配置。
> **用户已授权你读取其指定的本地连接文档（"get whatever you need"）**：桌面 `mooncake主仓\nds\测试相关资料\node1&3测试\连接node1和node3.md`。
> **回执脱敏**：不抄送账号、密码、密钥、完整 IP；节点一律用 node1 / node3 代称。文档里若有口令，只写"文档含口令，已使用、未外传"。

## 1. 连接与角色

- **1.1** 读上述连接文档，回执给出（脱敏）：连接方式（SSH/跳板/密钥）、文档声明的两台角色（谁是 initiator/master、谁是 target）、与本轮相关的约束（端口、GPU、大页、禁动作）。
- **1.2** 非交互验证两台可登录（`ssh -o BatchMode=yes` 一条只读命令）与 `sudo -n` 可用性；给成功/失败与报错原文（≤5 行）。
- **1.3** 证明两台是不同物理机（主机名 / machine-id 不同）；列出跨机链路使用的 URMA 设备名（两台各自），为"数据跨节点"做准备。

## 2. 硬件与约束盘点（只读）

- **2.1** CPU 核数、NUMA、内存、大页；GPU（如有）与驱动状态。
- **2.2** NVMe 盘：数量、型号、容量、BDF；系统盘是哪块；当前 vfio 占用状态；**能否凑出 11 盘 RAID0**（若盘数不足，给实际可用盘数与总容量）。
- **2.3** URMA：设备名、内核模块、`/dev/uburma/*`；node1↔node3 是否为同一网络/设备。
- **2.4** 当前进程与端口快照（属主 / 启动时长 / 端口），标出哪些是他人进程。

## 3. 代码与二进制盘点（只读）

- **3.1** SPDK 源码树位置、HEAD、分支或游离头、`git status --porcelain`、remote；与 `e12b7cb21` / `urma_enable_v2` 是否一致；`include/spdk_internal/urma_stage_buffer.h` 是否存在。
- **3.2** `nvmf_tgt`、`urma_perf` 路径 + md5 + mtime；`strings` 检查 `SPDK_URMA_STAGE_READER_SINK` / `SPDK_URMA_STAGE_TARGET_SINK` / `URMA_SLOW_IO` / `URMA3B01` 是否在。
- **3.3** Mooncake 源码树位置、HEAD、分支、`git status`；运行期 `ldd` 解析到的 liburma / liburma_common 路径 + md5。
- **3.4** 与 node2/node4 的差异清单（事实层）：版本、二进制 md5、URMA 库 md5、盘配置。**若 node1/node3 的二进制不含 V3 打点，必须明确写出来**——这决定 GAP-06 是否还按原账本方案。

## 4. 端口与数据（只读）

- **4.1** 按《端口规范》检查 4457 / 50056 / 8086 / 9006 / 50156 在 node1、node3 上是否被占用（属主为准）。
- **4.2** 是否存在可用的 500k × 8MiB 工作集（给事实即可）；盘可用容量能否装下 3.81 TiB。
- **4.3** 两台机器上现有的 master / target / client 进程（属主），以及 4457 是否有旧 listener。

## 5. 报告

- 一张结论表：能否在 node1/node3 上按原方案跑（跨机、盘数、V3 打点、端口）；缺什么。
- "需要改的参数"清单（只列事实与影响，不给方案）：盘数、strip、URMA 设备名、二进制/库版本等。
- 不贴 IP/账号/口令；不贴整文件。

## 回执必答（第一行）

两台是否可登录且为不同物理机；文档声明的角色分派；V3 打点与 `nvmf_tgt`/`urma_perf` 是否可用；盘数与端口能否支撑原方案、缺什么。

---

# GAP-05（待执行 · 2026-11-19）· 工具补齐与可行性验证（只读 + 仅写 `~/gap`）

> **约束**：gap 外只读；所有复制/解包/试运行都在 `~/gap`；**除 §0 用户已授权的两个遗留进程外，不启停任何服务**；不连 target、不跑流量、不 takeover。允许 `--help` / `-h` / `ldd` / `strings` 级验证。

## 0. 释放 node3 端口（用户已授权 · 2026-11-19）

- 目标进程：**PID 1184018**（master，cwd `~/nds/e3bd/mooncake_master_runtime`）与 **PID 1243055**（client，cwd `~/nds/e3bd/mooncake_client_runtime`）。
- 停前核对三重证据：cmdline、cwd、监听端口 —— 确认仍是本方遗留进程，且工作集为 0。
- 按 PID：`kill -TERM` → 等 10 s → 仍在则 `kill -KILL`；**禁 pkill/killall**。**不动 2879174（他人 client）**。
- 验证 50056 / 8086 / 9006 / 50156 全部释放；给 `ps`/`ss` 前后对比（≤10 行）。
- 若 PID 不存在或核对不符 → 停手回报，不扩大范围。
> 背景：GAP-04 发现两个硬缺口——①node1 没有我方 Mooncake 客户端；②node1 没有带 V3/慢 IO 的 initiator（`urma_perf`）。本任务用"复制可用二进制进 `~/gap` 再试运行"的方式补齐/验证，**不重编、不改代码**。
> 回执不要贴二进制/源码；只给路径、md5、`--help` 关键行（≤10 行）。

## 1. e3bd 栈盘点（node3，只读）

- **1.1** `~/nds/e3bd/` 目录树（≤2 层）：Mooncake build、runtime、脚本、Python venv、bench 工具。
- **1.2** 我方 Mooncake 构建：`mooncake_master` / `mooncake_client` / 其它工具 的路径、md5、mtime、`--help` 是否可用；版本/commit 依据（`strings` / find_version）。
- **1.3** 是否存在能做「8 MiB GET、50 万 key、seq/rand、4 worker」的现成工具（如 nof_worker_pool_bench / stress_cluster_bench / benchmark 脚本）；逐个给 `--help` 关键参数（≤10 行）。
- **1.4** `mooncake_client --help`：确认 `--port` 能否设 50156；TE RPC 端口是否另有开关。
- **1.5** `ldd`：e3bd 的 client/master 解析到的 liburma 路径与 md5。
- **1.6** `strings` 检查 e3bd 的 `mooncake_client` 是否含 `SPDK_URMA_STAGE_READER_SINK` / `SPDK_URMA_STAGE_TRACE_US`（决定 Mooncake 臂有没有客户端账本）。

## 2. 跨机二进制可用性（只写 `~/gap`）

- **2.1** 候选 `urma_perf` 两个：node2 的（md5 `c39b3489…`，Round6 实际 initiator 用的）与 node4 的（`c84ec7e3…`）。先对两者做 `strings` 检查（`SPDK_URMA_STAGE_READER_SINK` / `SPDK_URMA_STAGE_TRACE_US` / `URMA_SLOW_IO`），优先复制**带 V3 且与 Round6 initiator 同源**的那个到 node1 的 `~/gap/bin/`；记录 md5 / `ldd` / `--help`（确认 `--range-bytes` 与 `URMA_PERF_ADDR_MODE`）。
- **2.2** 把 node3 的 e3bd Mooncake build（client/master 及依赖）复制到 node1 的 `~/gap/mooncake/`；记录 `ldd` 与 `--help`。体积过大或依赖缺失时，只复制最小集合并说明缺什么。
- **2.3** 判断：node1 上能否直接运行这两样（`--help` 成功即可执行；不启动服务、不连网）。
- **2.4** 记录复制方式与文件清单（含 md5）；二进制本身不外传。

## 3. 资源可行性（只读）

- **3.1** node3 大页：总量/空闲；按 target iobuf `-I 8192,8192,1024,8388608` 计算需要量；给"够/不够"与缺口。
- **3.2** 若不够：列出可选做法（减少 large 池 / 增加大页 / 换 iobuf），只列事实与影响，不给方案。
- **3.3** node1 跑 Mooncake 客户端所需大页是否够。

## 4. 交付

- 一张表：缺口 → 现状 → 可用替代 → 仍需用户决策的点。
- 明确回答：GAP-06 能否开跑；缺哪几件。

## 回执必答（第一行）

node1 上是否已具备可运行的 Mooncake 客户端与带 V3 的 `urma_perf`（`--help` 级）；50156 的实际开关；node3 大页是否够 iobuf；node3 四个端口是否已释放。

---

# GAP-06（待执行 · 2026-11-19，待 GAP-05 回执后定稿）· 首轮实测：同参数 target 下 Mooncake vs 裸 SPDK 的 8 MiB 读双层账本

> **硬门：只有用户在本轮对话中明确宣布"独占"（例如"现在可以独占/佛挡杀佛"）才允许执行 §1 及之后的所有步骤。若未明确宣布：只做 §0 只读预检，然后停手回报；不得启动 target、不得停任何进程。**
> 目标：把 ~200 µs（同口径 222 µs）差距定位到具体层/段。**本轮不改代码、不重编、不优化。**
> 预计占机 60–90 min（含我方 master 启动与 prefill）。机器：**node1 = initiator/client，node3 = target/master（已确认）**；两台不同物理机，数据跨机。**高风险操作已获用户 2026-11-19 整体授权**（停资源占用者、vfio 接管/还原、启停本方 target/master）；必须按 PID、禁 pkill/killall、不 reboot、不 rmmod udma、不动他人进程；异常即停并回报。
> **定稿前置（GAP-05 回执）：①node1 上可用的 Mooncake 客户端与带 V3 的 urma_perf；②50156 的实际开关；③node3 大页是否够 iobuf；④node3 的端口处置方案（用户确认）。**
> **GAP-03 审计结论（2026-11-19）**：历史 `0.4667 ms vs 259.92 µs` 因 strip 256/128 与 taskset/-s 不同，**不构成同参数对照**；R6 rand `655.6 vs 327.2` 因随机范围 15.4× **不可比**；R6 seq `466.6 vs 245.7` 仅差 taskset/-s。**本轮必须由我方在同一窗口重测两侧基线**；历史数字只作漂移参考（R6 MC seq_a vs seq_b 的 p99 漂移 0.0073 ms 可作噪声标尺）。

## 0. 预检（只读；未授权时到此为止）

- **0.0 条件台账（每臂一行，贯穿全程）**：动手前先建台账文件（`conditions.csv` + `meta.md`），逐臂记录：
  节点角色与 IP（initiator / target / master）、**数据是否跨节点**；盘列表与顺序、BDF、strip；target 参数（`-m/-C/-I/-O/-L` 路径+md5、taskset、`-s`、transport、listener）；客户端 env（workers、chunk bytes、qpairs、liburma 路径+md5、打点 env）；负载参数（I/O 大小、seq/rand、seed、随机范围/`--range-bytes`、QD/批次、时长、warmup、measure mode）；跑前/跑中他人负载采样；起止时间与命令原文。
  **回执必须附台账；缺台账的臂，其数字不进 gap 结论。**
- **0.0b 匹配矩阵**：列一张表 `参数 | Mooncake 臂 | urma_perf 臂 | 是否一致 | 处理`，覆盖：节点角色、盘/顺序、strip、iobuf、max_io_size、C、mask、taskset、`-s`、transport、I/O 大小、QD、随机范围、warmup、时长。不一致的必须标 `有意变量` 或 `无法匹配（原因）`；**未在矩阵中列出的差异，不得用于结论**。
- **0.1 独占判定**（按 §独占判定规范）：node1/node3 可疑进程 10 s `/proc` 差值与绑核空闲率；他人负载 >1% 单核则停手回报（除非用户当轮明确要求带载跑）。记录 load、`mpstat`。
- **0.2 V3 源码核对（纠正 GAP-02 H3 的推断）**：
  - `git -C <spdk树> ls-tree HEAD include/spdk_internal/urma_stage_buffer.h` → 记录是否存在与 blob hash；
  - `grep -n "URMA_STAGE_ENV" <spdk树>/include/spdk_internal/urma_stage_buffer.h` → 证明确为宏拼接（`URMA_STAGE_ENV "SINK"`），所以源码 grep 全名为 0 属正常；
  - `git -C <spdk树> status --porcelain include/spdk_internal/urma_stage_buffer.h` → 应为空（未修改）。
- **0.3 发起 NoF 读的进程**：确认 `benchmark.py` 运行时真正发起 NoF 读的是哪个进程（python 基准进程 vs `mooncake_client` 服务），给依据（`/proc/<pid>/environ` 里的 SPDK env、线程名、fd、日志）。V3 env 只加在该进程上——V3 文件用 O_EXCL 打开，同一路径被两个进程打开会 abort。
- **0.4 内存**：node1/node3 `free -g`；V3 每条记录 192 B，按 12,000,000 条预分配 ≈ 2.3 GB/进程。
- **0.5 `--range-bytes` 语义**：给出 urma_perf `--range-bytes` 的 usage 与代码位置（`文件:行号`），确认它如何把随机范围限制到指定字节数。
- **0.6 快照**：现有 target/master/client 进程与端口；master metrics 的 NoF 段与已分配字节（复核 500k keys）。
- **0.7 确认 target 当前确实停止**（旧 listener 未监听、vfio 无设备）。
- **0.8 端口预检**：
  - 按《端口规范》核实五个端口的实际开关（master 三个 flag 已知；client 50156 的开关必须核实，含 `MC_MIN_RPC_PORT/MC_MAX_RPC_PORT` 的临时端口段限制）；
  - 占用检查：`ss -ltnp | grep -E ':(4457|50056|8086|9006|50156)\b'`；被他人占用 → 停手回报；
  - 解释器脚本副本：确认 `target_nvme_takeover.sh:96` 的 `LISTEN_PORT=4420`，准备副本改为 4457。
- **0.9 我方 master 与 keys 影响（必读）**：
  - 旧 master（Round6 那个）保持不动；本轮按端口规范起**我方新 master**（50056/8086/9006）。新 master 没有旧元数据，**500k keys 需要本轮重新 prefill**；除非预检发现旧 master 启用了 snapshot/restore（检查命令行与 snapshot 目录）——若有，先回报再定。
  - **prefill 会覆盖盘上旧数据**：旧 master 的 keys 在本轮之后将不可用。用户 2026-11-19 已明确接受该副作用；进入 §1b 前在回执里写明即可。
  - 若 prefill 预计耗时超过 30 min 或失败 → 停手回报。

## 1. 启动 target（仅在授权后；参数与 Mooncake 侧完全一致；listener=4457）

- 复制 `target_nvme_takeover.sh` 到 `~/gap/<本轮目录>/`（gap 外只读复制，不改编），**只把副本里的 `LISTEN_PORT` 改为 4457**；记录原/新脚本 md5 与 1 行 diff。
- 用副本启动，参数与 Mooncake 侧一致：
  外层 `taskset -c 2-7`；`-R 256 -m 0xfc -C 64 -O 8388608 -I 8192,8192,1024,8388608 -N udmac1d1e2 -L /home/tong/umdk_gpu_isolated/lib -p urma -s 10 -y`
  盘序与 Round6 相同（11 块数据盘，按脚本现算的字典序）。
- 若 target 上已有旧 listener（4420/4421）→ 先 `nvmf_subsystem_remove_listener` 再加 4457；记录命令原文。
- 记录：完整命令行原文、PID、启动时间、listener、`nvmf_tgt` md5、`/tmp/nvmf_tgt.log` 路径。
- 验收：**4457** 监听；`/tmp/nvmf_tgt.log` 出现 URMA target timing 头部。
- **不动旧 master。**

## 1b. 启动我方 master（新端口）+ prefill

- 在 node1 起我方 master：`--rpc_port=50056 --http_metadata_server_port=8086 --metrics_port=9006`（其余参数照 GAP-04 侦察到的本机 master 启动方式逐项记录原文；**不动任何既有进程**）。
- 客户端 / NoF 注册指向 `50056`；NoF 注册端口 `4457`。
- **prefill：500k keys × 8 MiB = 3.81 TiB**，用 Round6 驱动的首次写入路径（`--reuse-keys` 关、`--keep-keys` 开；具体参数照 Round6 脚本）。记录写入量、耗时、失败数。
- 验收：master key 数 = 500000；NoF 段挂载；`master_nof_allocated_bytes` = 4,194,304,000,000（允许等价误差）。失败或预计超过 30 min → 停手回报。
- 之后各 Mooncake 臂用 `--reuse-keys` 复用本轮 keys。

## 2. 测量臂（每臂 60 s；顺序如下）

客户端公共 env（只加在 §0.3 确认的进程上；路径每臂唯一且事先不存在）：
```
SPDK_URMA_STAGE_TRACE_US=1
SPDK_URMA_STAGE_READER_SINK=buffer
SPDK_URMA_STAGE_READER_PATH=<每臂唯一路径>
SPDK_URMA_STAGE_READER_CAPACITY=12000000
MC_NOF_PORT=4457
（客户端 RPC 50156 按 §0.8 核实出的开关显式设置；若不可设 → 停手回报）
```
target 侧：`-s 10`（聚合 dump 进 `/tmp/nvmf_tgt.log`）。

| 臂 | 配置 |
| --- | --- |
| G3-1 | Mooncake seq，4 workers（沿用 Round6 驱动，指向我方 master:50056，`--reuse-keys --no-start-env`，时长 60 s） |
| G3-2 | Mooncake rand，4 workers（同上） |
| G3-3 | Mooncake seq，1 worker（`--nof-workers 1`） |
| G3-4 | Mooncake rand，1 worker |
| G3-5 | urma_perf seq：与 Round6 相同的调用（`-w read -o 8388608 -T 1 -b 1 -t 60 -n 1 -g 0 -l 0 -M cpu`，`URMA_PERF_ADDR_MODE=seq`，seed 20261115） |
| G3-6 | urma_perf rand：同上但 `URMA_PERF_ADDR_MODE=rand`，加 `--range-bytes 5497558138880`（对齐 Mooncake 池容量） |
| G3-7（可选） | urma_perf rand 全 namespace（不加 `--range-bytes`，复现 Round6 的 327 µs 口径） |

每臂记录：起止时间、实际命令/env、benchmark summary（avg/p50/p99/QPS）、V3 文件路径+大小、target 日志时间窗、跑中他人负载采样。
- Mooncake 臂的 client 进程必须**正常退出**（自然退出或 SIGTERM，禁止 SIGKILL）才触发 V3 落盘。
- 若启动时报 "buffer sink requires PATH" 或 O_EXCL 失败 → 记录并停，不自行换方案。

## 3. 聚合与分析（原始文件不上传）

- V3 文件留在 **initiator 节点（node1）的 `~/gap/...`**；回执给 `~/gap` 下的相对路径与 md5。
- 用本仓脚本生成每臂聚合表：
  ```
  python3 scripts/decode_urma_stage_v3.py <v3文件> --out <arm>_agg.txt
  ```
- 回执给出每臂：`decoded/valid/dropped`、`roundtrip_us` 与各分段（`rx_buffer/buffer_exec/bdev/bdev_post/data/residual/outside`）的 `mean/p50/p90/p99/p99.9/max`（µs）、benchmark summary 的 `avg/p50/p99`、target 聚合 dump 最后两个 10 s 块原文。
- 另给对照：同臂 traced E2E 与 Round6 未打点值（Mooncake seq 467 µs / rand 656 µs；urma_perf seq 246 µs / rand 327 µs）之差，用于判断打点开销。

## 4. 收尾与回退

- 停 client / urma_perf（自然退出，等 V3 落盘）；target 用 SIGTERM 停（**不要 SIGKILL**），确认 `/tmp/nvmf_tgt.log` 尾部完整。
- 停我方 master（记录 PID，SIGTERM）；**旧 master 全程不动**。
- 若本轮做过 disk takeover：`target_nvme_takeover.sh -r` 还盘，确认盘回 nvme、4457 不监听、vfio 设备数 0。
- 回退：旧 master 不动；若 target 起不来或 prefill 失败 → 停手回报，不重启旧 master、不擅改端口。
- 结束态：target 停、盘还原、我方 master 停、旧 master 原样；在回执里写明"prefill 已覆盖盘上旧数据，旧 master 的 keys 不可用"。

## 5. 约束

- 共用机红线：**仅在用户明确"独占"后**按 PID 停资源占用者；禁 pkill/killall；不 reboot；不 rmmod；不动他人 master/client。
- **工作目录铁规**：node1/node3 上所有写入只在 `~/gap` 内；gap 外只读，严禁修改/删除/移动/创建（见《工作目录铁规》）。
- 不改代码、不重编；只用 GAP-05 验证过的现有二进制（md5 以 GAP-05 回执为准）。
- 资料最小化：V3 原始文件不传；每臂聚合表 ≤40 行。
- 任何一步与预期不符（段丢失、V3 不落盘、dropped 过多、他人负载超标）→ 停止并回报，不自行改方案。

## 回执必答的一句话（第一行）

各臂是否全部完成；每臂 V3 的 `count`/`dropped`；Mooncake 与 urma_perf 在 `roundtrip`、`bdev`（W9）、`data`（C2H）三项上的均值与 p99 差值。
