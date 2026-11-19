# 交接文件（单向：开发指挥 Agent → 测试执行 Agent）

- 仓库：`https://github.com/liangxu2000/mooncake-spdk-gap-handover`（public，匿名 HTTPS 可拉取）
- 首次接入：`git clone https://github.com/liangxu2000/mooncake-spdk-gap-handover.git`
- 之后每轮：`cd mooncake-spdk-gap-handover && git pull`
- 权限：**只 pull，不要 push**；本仓不接收反向提交
- 回执：按下方《回执格式》在会话里输出，由用户转交
- 最后更新：2026-11-19
- 当前任务：**R7-01（待执行）**

## 协作约定

1. **方向单向**：本文件只由开发指挥 Agent 更新并 push；测试执行 Agent 只 pull。
2. **任务编号**：`R7-01`、`R7-02`…（Round7 系列）；状态：`待执行` / `执行中` / `待回执` / `已关闭`。
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

## 背景与总目标（供理解任务用，回执不必复述）

项目总目标：**消除 Mooncake 与裸 SPDK 在 8 MiB 读上的 ~200 µs 时延差距**。这是同事交接的原始问题，
也是最终交付物——不是写分析报告，而是把差距消掉。参照值以用户指定的 Round5 诊断文件为准（见任务 G1）。

你的 11-19 交接文档（Round6 事实清单）是当前基线；Round6 已量出差距，并拿到部分 target 侧分段账本与客户端 RPC RTT
（数字以你的文档 §4 为准，本仓不重复）。

Round7 的路径：**先定位、后消除**。第一步是在同一 target 配置、同一测量窗口、同一套打点下，对 Mooncake 与裸 SPDK
的 seq / rand 各臂同时取 target 侧分段与客户端侧分段，把 ~200 µs 差距定位到具体层、具体段；定位清楚后再选优化项。

R7-01 是 Round7 的只读前置任务：把设计 Round7 所需的开关、风险、口径查清楚。**本任务不跑任何压测。**

## 任务历史

| 编号 | 日期 | 内容 | 状态 | 回执摘要 |
| --- | --- | --- | --- | --- |
| R7-01 | 2026-11-19 | 只读情报：Round7 设计前置（打点开关 / target 重新拉起的数据安全 / 客户端阶段通道 / 对照口径 / worker 旋钮 / 本地 Round5 诊断文件 / 源码版本与二进制归属） | 已关闭 | 同一 `nvmf_tgt`（md5 `95ce0bfd…`）；两路 target 参数 4 处不同（`-s`/taskset/`-L`/`-I`）；master 心跳实际关闭（3600s×999999），500k keys 元数据仍在（4.19 TB，精确 500000×8 MiB）；Round6 无 prefill；客户端仅阈值采样/≤8192 行 CSV；裸 SPDK=`urma_perf -T1 -b1`、rand 覆盖全 namespace；H 节未答（并入 R7-02） |
| R7-02 | 2026-11-19 | 只读：补 H 节（源码/二进制归属 + 2 个未提交文件 diff）+ 打点能力核对（target 聚合 / LEGACY / stage buffer 在三个二进制中是否可用）+ Round7 参数匹配事实（`-I` 实际值、两条 `-L` 库 md5、taskset、ns 容量、最近启动命令行） | 待执行 | — |

---

# R7-01（已关闭 · 2026-11-19）· 只读情报收集：Round7 设计前置

> 回执已收（见任务历史摘要）。H 节未答，并入 R7-02。

> **性质：纯只读**。不改任何文件、不启停任何进程、不碰盘/vfio、不重启。不需要独占窗口。
> 若某个问项必须写操作才能取证：跳过，在回执里记 `[未获取] 需要写操作`。
> 机器：node2、node4（即你 11-19 交接文档中的两台）。
> Round6 中你已经读全的配置与结果不必重读；本任务只查下方问项。

> **开发侧已从公开源码核实（SPDK `e12b7cb21` / Mooncake `706551a8`），下列问项只需核对本机部署与源码一致，不必重新探索：**
> - target 聚合分段：`SPDK_URMA_TARGET_DUMP_SEC=<秒>`（transport 创建时读取，周期 dump；`target_nvme_takeover.sh -s <秒>` 即此开关），代码常开，无需特殊编译。
> - per-IO 跨端账本（Round7 用）：initiator 设 `SPDK_URMA_STAGE_TRACE_US=<µs>` 后每个请求才带 `trace_seq`；两侧设 `SPDK_URMA_STAGE_{READER,TARGET}_SINK=buffer` + `_PATH`（文件，O_EXCL）+ `_CAPACITY`（记录数，192 B/条）后，进程退出时落二进制文件（头/尾魔数 `URMA3B01` / `URMA3END`，side=1 initiator / 2 target）。
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
- **F3** Round6 每个 Mooncake arm 的总耗时（driver.log 的 rc 与总时长），用于估算 Round7 窗口。

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

Round7 能否在 ①不重做 prefill ②两套测试同 target 二进制同参数 ③两端都开阶段计时 这三个前提下开跑；不能的部分，缺什么。

---

# R7-02（待执行 · 2026-11-19）· 只读：补 H 节 + Round7 实验前置核对

> **纯只读**：不启动/停止任何进程、不碰盘/vfio、不跑压测、不修改文件（`/tmp` 探针脚本用完即删）。
> 你 R7-01 的回执 A–G 已收到；本任务补齐未答的 H 节，并加 I/J 两节，为 R7-03（需用户独占窗口的实测）定参数与账本方案。
> 目的只有三个：①确认机器代码/二进制与公开 commit 的差异；②确认三套打点在三个被测二进制里各自是否可用；③拿到参数匹配所需的事实。
> 机器：node2、node4（共用机、非独占，红线同《协作约定》§6）。

## H. 源码版本与二进制归属（若 R7-01 已做过，直接复用结果）

- **H1** node2 / node4 上 SPDK 源码树位置；每棵树的 `git rev-parse HEAD`、`git status --porcelain`、`git remote -v`、`git branch --show-current`（或 `git describe --all`）。确认是否为 `e12b7cb21` / `urma_enable_v2`，两节点是否同一棵树。
- **H2** 两个未提交修改文件：`examples/nvme/urma_perf/urma_perf.c`、`include/spdk_internal/trace_defs.h` 的 `git diff --stat` + 完整 diff（≤200 行；超长给 hunk 标题 + 关键 hunk）+ 两文件 `md5sum`。
- **H3** 二进制归属：`nvmf_tgt`、`urma_perf` 的路径 + `md5sum` + `ls -l` 时间；用构建目录 .o/ninja 时间或 strings 特征判断它们是否由 H1 这棵树 + H2 的修改编出（不重编）。
- **H4** Mooncake 源码树（node2 的 `mooncake-930`）：`git rev-parse HEAD`、`git status --porcelain`、`git remote -v`；是否也有未提交修改（若有，同 H2 给 diff）。
- **H5** 部署文档一致性：`docs/yin/mooncake_nof_deployment.md` 记录的是旧配对（`urma_modified_v6` + `nof-urma-v2`）；只列出该文档中**仍在使用、但可能与当前代码不符**的启动参数或 env（≤10 条，给文档行号），不贴全文。

## I. 打点能力核对（决定 R7-03 用哪套客户端账本）

- **I1** `nvmf_tgt` 二进制 strings 检查：`URMA3B01`、`SPDK_URMA_STAGE_TARGET_SINK`、`SPDK_URMA_TARGET_DUMP_SEC` 是否出现（各给 是/否 + 1 行样例）。
- **I2** `urma_perf` 二进制 strings 检查：`URMA3B01`、`SPDK_URMA_STAGE_READER_SINK`、`SPDK_URMA_STAGE_TRACE_US`。
- **I3** Mooncake 客户端实际链接的 SPDK：`ldd` 解析出的库路径 + md5；对这些库做与 I2 相同的 strings 检查。若客户端是多进程（client/master），指明哪一个进程负责 NoF 读写。
- **I4** 汇总一张表：三套通道（target 聚合 dump / LEGACY `URMA_SLOW_IO` 慢 IO / stage buffer V3）在 **nvmf_tgt、urma_perf、Mooncake 客户端** 三处各自可用与否。只给事实，不给建议。

## J. Round7 参数匹配所需事实（只读）

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
