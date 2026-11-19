# 交接文件（单向：开发指挥 Agent → 测试执行 Agent）

- 仓库：`https://github.com/liangxu2000/mooncake-spdk-gap-handover`（public，匿名 HTTPS 可拉取）
- 首次接入：`git clone https://github.com/liangxu2000/mooncake-spdk-gap-handover.git`
- 之后每轮：`cd mooncake-spdk-gap-handover && git pull`
- 权限：**只 pull，不要 push**；本仓不接收反向提交
- 回执：按下方《回执格式》在会话里输出，由用户转交
- 最后更新：2026-11-19
- 当前任务：**GAP-09（小工作集快速预实验 150k，可执行）**；GAP-08 的 500k prefill 已按用户要求中止，master/target 保持运行

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
   > - **范围区分（2026-11-19）**：node2 / node4 仍为公用机，按上述约束；**node1 / node3 已由用户宣布独占**——独占期内停占用资源的进程无需逐次请示（按 PID，先 TERM 后 KILL；禁 pkill/killall），**重启等危险操作仍需先问**。

   - 默认只读；不启停进程、不碰盘/vfio、不改文件、不重启、不装卸驱动。
   - 需要写临时探针脚本时沿用 base64 方式写到 `/tmp`，用后立即删除。
   - 禁止 pkill/killall；不动非本方进程（含"看起来空转"的进程）。
   - 不 reboot；不 rmmod 底层驱动。
   - 所有远程命令非交互（`sudo -n`），不等待输入。
7. **长任务**：预计超过 30 min 的任务，每 ~15 min 输出一行进度（阶段 / 已完成问项 / 阻塞）。
8. **不猜原则**：任务书中凡要求取证的点，一律以实测或源码为准；无法取得的，按 `[未获取]` 记录并说明，不要下结论。
9. **长命令状态汇报**：编译、压测、长脚本执行期间，按 §7 定期报进度，不要长时间无输出。

## 任务拆分原则（2026-11-19 用户强调，优先级最高）

- **一单一阶段、一个验收点**：每个任务只覆盖一个阶段（如"只起 master"、"只注册"、"只 prefill"、"只跑一组臂"）。
- 测试 agent **只执行任务书里的逐条命令与验收**：不选型、不自行改参数、不扩大范围、不做设计判断。
- 任何不确定/冲突 → 停在 `[未获取]` / `[冲突]` 并回报，由开发侧决定。
- 拿到回执、核对通过后再发下一单；**禁止把构建 + 起服务 + prefill + 多臂 + 分析塞进一单**（无人值守连跑是例外，需用户明确要求且任务书自带幂等/断点/兜底）。
- 历史大任务（如 GAP-07 原稿）里未执行的部分一律作废，按拆分后的小单重新下发。

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
- **独占与高风险授权（2026-11-19 用户宣布）**：node1/node3 现为本方独占。**独占期内，停任何占用资源的进程都无需逐次请示（按 PID，先 TERM 后 KILL）**；GAP-06 的 vfio 接管/还原与本方 target/master 启停也已整体授权。仍禁止：pkill/killall、reboot、rmmod udma、动系统服务/sshd/网络；异常即停并回报；**授权范围之外的新类型高风险动作（如重启）仍需先问**。
- **启动前必须做端口占用检查**；任一端口被他人占用 → 停手回报，不得抢占、不得改回同事的端口。
- 已核实的源码事实（供预检对照）：
  - master 三个端口都有显式 flag：`--rpc_port` / `--http_metadata_server_port` / `--metrics_port`（`mooncake-store/src/master.cpp:134/410/547`）。
  - SPDK `target_nvme_takeover.sh:96` 把 `LISTEN_PORT` 写死为 4420 → **用脚本副本改 4457**，不改原脚本，记录原/新脚本 md5。
  - TE RPC 端口范围 `MC_MIN_RPC_PORT / MC_MAX_RPC_PORT` 经 `mooncake-transfer-engine/src/config.cpp:842` 的 `ValidatePortRange` 校验，**排除 32768–60999（临时端口段）**；50156 落在该段内 → 若客户端走这两个 env，50156 会被拒绝并回落到 15000–17000。50156 到底由哪个开关控制，必须在预检里核实；若无法设置，回执提出替代（如 15556 / 16556，同样以 6 结尾），由用户定。

## 工作目录铁规（2026-11-19 用户定，node1/node3 生效）

- 在 node1 与 node3 上各自创建 **`~/gap`**（用户指定 `~/gap`）作为唯一工作目录；用户已授权创建。
- **所有写入只允许发生在 `~/gap` 内**：脚本、日志、结果、V3 文件、临时文件。`/tmp` 仅限一次性探针且用完即删，长期产物一律放 `~/gap`。
- **`~/gap` 之外一律只读，且只允许"复制进 gap"**：需要用的二进制、库、脚本、数据先复制到 `~/gap`，之后**一律执行/加载 gap 内副本**；**禁止直接执行或加载 gap 外的项目构件**（二进制、库、脚本）；系统基础库（libc 等）除外。严禁修改、删除、移动、创建任何 gap 外的文件或目录。
- 回执/台账里的产物路径写 `~/gap/...` 形式，不写绝对 home 路径。

## 环境重建原则（2026-11-19 开发侧定，GAP-05/06 执行）

前提：node1/node3 的 `~/gap` 为空；但两台机器和 node2/node4 上已有可复用的构件。**优先"只读搬"，其次"编译"，最后"自己写小工具"**；所有落盘只在 `~/gap`，原目录只读。

1. **能搬就搬**（只读源 → 写入 gap）：
   - target：node3 现有 `nvmf_tgt`（V3 完整，md5 `e7440ae0…`）；启动脚本从 node2/node4 复制到 node3 的 gap，副本改 `LISTEN_PORT=4457`。
   - initiator（裸 SPDK）：node2/node4 上带 V3 的 `urma_perf` 复制到 node1 的 gap；ABI 不兼容则走第 3 条。
   - Mooncake：node3 的 e3bd 构建（client/master + 依赖）复制到 node1 的 gap（client）与 node3 的 gap（master）；`LD_LIBRARY_PATH` 指向 gap 内副本，避免依赖 gap 外路径。
2. **能跑就用**：`--help` / `ldd` / 最小冒烟（不连 target）验证；记录 md5 与运行条件。
3. **跑不起来才编**（fallback）：从 node2/node4 复制现有 SPDK 源码树（含未提交修改）到 node1 的 gap 编译 `urma_perf`；不改源码。Mooncake 若需重编，同样复制源码到 gap 编译；记录编译配置与耗时。
4. **没有现成驱动就写小工具**：Mooncake 侧若无现成 bench，在 gap 里写一个最小驱动（调 Mooncake 客户端 API），实现 500k key、8 MiB GET、seq/rand、4 线程、60 s、warmup；同时负责 prefill（写 500k × 8 MiB）。工具只放 gap，不进任何同事仓库。
5. **打点缺口如实记录**：若 Mooncake 客户端拿不到 V3/慢 IO 账本，就用 target 聚合 dump + 客户端 E2E + 可行的 Mooncake 慢请求通道；把"客户端账本缺失"写进匹配矩阵与回执，**不用其他层的数据冒充**。
6. **不碰 gap 外**：构建产物、日志、结果、脚本副本全在 gap。

## 代码基线与变更管理（2026-11-19 开发侧定）

现状：GitHub 只有 commit（SPDK `e12b7cb21` / Mooncake `706551a8`），机器上有未提交修改；node1 是更旧的 `6ceebf91`；node3 的树无 `.git`（部分无源码）。**因此"直接改机器上的代码"不可接受——无法证明改的是哪个基线，也无法回退。**

**代码版本门（2026-11-19 用户强调，优先级最高）**：任何二进制/源码，若其版本不能由 `commit + 完整 diff` 证明，**一律不得用于实测或修改**。以下**全部暂停使用**，直到用户确认版本：
- node3 的 e3bd 构建（`nvmf_tgt e7440ae0…`、`mooncake_master/client`）：**无 `.git`、源码不全 → 来源不明**。
- node1 `~/nds/...` 下的 `stress_cluster_bench` 与构建残留：**属于别的项目，版本未确认**。
- GAP-05 借来的 liburma（`/home/g00953922/...`）：**第三方目录、版本未确认**。
- node2 的 `urma_perf`（`c39b3489…`）：来源链 = `e12b7cb21` + 本地修改，但**5 个 SPDK diff 未采集**，暂不算"可证明"。

**解决路径（2026-11-19 用户定；GAP-06 已完成适配验证）**：
- **代码基线 = GitHub 最新代码**：SPDK `170cbb94…`、Mooncake `af253a2…`。
- **补丁范围（开发侧决定）**：只应用 **`examples/nvme/urma_perf/urma_perf.c` 的随机读改动**（+145 行；含 `URMA_PERF_ADDR_MODE`、`URMA_PERF_RANDOM_SEED`、`--range-bytes`、`--lba-plan`）。**不带**其余 5 个文件（p99 门控/追踪旁路，读路径不依赖，且最新代码已有自己的 p99 trace 设施）与 node2 独有的 `lib/nvmf/urma.c` WRITE 打点。若构建因此报缺符号 → 停手回报，不擅自扩大补丁面。
- 随机口径：GAP-07 使用 **`URMA_PERF_ADDR_MODE=rand` + `URMA_PERF_RANDOM_SEED=20261115`**（与 Round6 历史方法一致）；`--lba-plan` 仅作备用，不用于本轮。
- 全部在 `~/gap` 内 clone/build/运行，**只运行 gap 内产物**。
1. **SPDK**（`yyyuanhao426-hash/spdk`）：以 `e12b7cb21` 为基，提交 node2/node4 工作区的全部修改（至少 7 个文件 + 未跟踪的 `lib/nvme/nvme_p99_v7.h`），push 到分支；给 **分支名 + commit**。
2. **Mooncake**（`LeeJace993/Mooncake`）：以 `706551a8` 为基，提交 `mooncake-930` 工作区的全部修改（7 处，含 2 个未跟踪构建脚本），push 到分支；给 **分支名 + commit**。
3. 附：`git submodule status` 输出、构建用的 cmake/flags、以及**当前二进制对应的 commit**（用于核对）。
拿到以上信息后，GAP-06 改为：gap 内 clone/checkout → 编译 → `strings` 验证特征 → 实测。

规则：
1. **诊断完成前不改代码**（GAP-06 只测量）。
2. **改动前先冻结基线**：对将要修改的每一棵树，采集并归档到 `~/gap/baseline/`：
   - `git rev-parse HEAD`、`git status --porcelain`、**全部** `git diff`（`base64 -w0` 分文件 + patch md5）、未跟踪文件清单+md5、构建配置（`build/mk/config`、编译器版本）、二进制 md5。
   - 无 `.git` 的树：记录整树清单与逐文件 md5；确认是否有可用源码。
3. **基线选择按层**：
   - target / NoF 数据面 → SPDK。优先 `e12b7cb21` + node2/node4 的**全部**本地修改（目前只取了 2 个文件的 diff，还缺 5 个）。node3 的 `e7440ae0` 二进制若无法证明来自该基线 → **重建后先复测基线**，达标再进入对照。
   - 客户端 / master → Mooncake。优先 `706551a8` + node2 树的 7 处本地修改；node3 的 e3bd 构建源码只截到 `mooncake-store/src`，需确认完整性。
4. **所有修改以补丁形式**（diff + base64 + md5）在 `~/gap` 的副本上打，**不改任何原位目录**；回退 = 用归档恢复 + md5 校验。
5. **无法证明源码一致时**：要么重建并重测基线，要么只做运行时/参数层调整，不碰源码。
6. GAP-06 的 §0.10 先做**只读代码冻结**并产出 `baseline/MANIFEST.md`；任何源码修改之前必须以该清单为基准。

## 背景与总目标（供理解任务用，回执不必复述）

项目总目标：**消除 Mooncake 与裸 SPDK 在 8 MiB 读上的 ~200 µs 时延差距**。这是同事交接的原始问题，
也是最终交付物——不是写分析报告，而是把差距消掉。参照值以用户指定的 Round5 诊断文件为准（见任务 G1）。

你的 11-19 交接文档（Round6 事实清单）是当前基线；Round6 已量出差距，并拿到部分 target 侧分段账本与客户端 RPC RTT
（数字以你的文档 §4 为准，本仓不重复）。

我们的路径：**先定位、后消除**。第一步是在同一 target 配置、同一测量窗口、同一套打点下，对 Mooncake 与裸 SPDK
的 seq / rand 各臂同时取 target 侧分段与客户端侧分段，把 ~200 µs 差距定位到具体层、具体段；定位清楚后再选优化项。

`GAP-01` 是只读前置任务：把设计首轮实测（`GAP-06`）所需的开关、风险、口径查清楚。**该任务不跑任何压测。**

> **代码 provenance（2026-11-19 核实）**：GitHub 上的两个 commit 均可拉取（SPDK `e12b7cb21` / `urma_enable_v2`；Mooncake `706551a8` / `nof-gdr-supercache-snapshot-930`）。但 **node2/node4 机器上还有未提交修改**：SPDK 工作区至少 7 个文件（`urma_perf.c` +145 行、`trace_defs.h` +6 行已取证；`nvme_pcie_common.c`、`nvme_pcie_internal.h`、`nvme_qpair.c`、`target_nvme_takeover.sh`、`lib/nvmf/urma.c`（node2 +44 行）未展开）；Mooncake 树 7 处（docs、go.mod/go.sum、`client_service.cpp`、`master_service.cpp` 等）。**因此"GitHub 代码 = 机器代码"不成立**。node1/node3 是另一套：node1 SPDK HEAD `6ceebf91`（更旧、无 stage buffer）；node3 的树无 `.git`，来源无法由上 commit 证明。

## 任务历史

| 编号 | 日期 | 内容 | 状态 | 回执摘要 |
| --- | --- | --- | --- | --- |
| GAP-01（原 R7-01） | 2026-11-19 | 只读情报：首轮实测设计前置（打点开关 / target 重新拉起的数据安全 / 客户端阶段通道 / 对照口径 / worker 旋钮 / 同事 Round5 诊断文件 / 源码版本与二进制归属） | 已关闭 | 同一 `nvmf_tgt`（md5 `95ce0bfd…`）；两路 target 参数 4 处不同（`-s`/taskset/`-L`/`-I`）；master 心跳实际关闭（3600s×999999），500k keys 元数据仍在（4.19 TB，精确 500000×8 MiB）；同事 Round6 无 prefill；客户端仅阈值采样/≤8192 行 CSV；裸 SPDK=`urma_perf -T1 -b1`、rand 覆盖全 namespace；H 节未答（并入 GAP-02） |
| GAP-02（原 R7-02） | 2026-11-19 | 只读：补 H 节（源码/二进制归属 + 未提交文件 diff）+ 打点能力核对 + 实测参数匹配事实 | 已关闭 | 三套打点在三个二进制均可用（V3 env 串在，魔数不显）；两节点 `nvmf_tgt` 非同一文件（被测 target 在 node4）；`-L`/`-I` 实际相同，实质差异只剩 `-s` 与 taskset；源码树 7 处未提交改动（node2 多 `urma.c` +44 行）；Mooncake 客户端运行期 liburma 为第三条路径（md5 `87d4fb60…`）；ns 容量 84.5 TB = Mooncake 工作集的 15.4 倍；V3 源码在 HEAD（宏拼接，回执"源码已不在磁盘"的判断需更正） |
| GAP-03 | 2026-11-19 | 只读条件审计：把同事全部实验逐臂提取「客户端/target/master 节点、数据路径是否跨节点、参数与库」，标出同节点/条件不可比的数字 | 已关闭 | 归档结果中**没有** initiator=target 同节点的 8 MiB gap 对比（R5/R6/R11 均 node2→node4，R11 有 includes_same_host=False）；r7bi 系列 target 在 node2 且无测量输出，不可用；`0.4667 ms vs 259.92 µs` 因 strip 256 vs 128 + taskset/-s 不同**不可比**；R6 rand 655.6 vs 327.2 因随机范围 15.4× **不可比**；R6 seq 466.6 vs 245.7 仅差 taskset/-s；可用基线=Round6 框架内 Mooncake 各臂与 R6 SPDK 各臂自身 |
| GAP-04 | 2026-11-19 | 新环境接入与只读侦察：node1/node3 连接与角色、硬件/盘/URMA、代码与二进制（含 V3 打点）、端口占用、工作集与容量 | 已关闭 | 两台可登录、不同物理机；文档角色 node1=initiator/client、node3=target/master；node3 的 `nvmf_tgt` 带完整 V3（md5 `e7440ae0…`），**node1 的 `urma_perf` 与我方 Mooncake 客户端均不带 V3**；盘各 11×7.68 TB；4457 空闲；node3 的 50056/8086/9006/50156 被**本方 23 h 遗留进程**占用；工作集=0；node3 大页 9.06 GB（iobuf 需 ~8.06 GB，余量小）；两台 liburma `5c021f7f…`（≠ node2/4） |
| GAP-05 | 2026-11-19 | 工具补齐与可行性验证（只读 + 仅写 `~/gap`）：e3bd 栈盘点、跨机复制并 `--help` 验证 urma_perf / Mooncake client、确认 50156 开关、大页核算 | 已关闭 | node1 已有带 V3 的 `urma_perf`（`~/gap/bin` + `~/gap/lib`，`--help` rc=0）；复制版 e3bd client/master 通过 `LD_BIND_NOW`；**node1 本机已有 `stress_cluster_bench`（推翻 GAP-04"无 bench"结论）**；50156 = client `-port`；node3 大页 4640 页（需 4641，脚本自动上调；4 NUMA 各 1160 页）；node3 四端口已释放 |
| GAP-06 | 2026-11-19 | 随机读补丁获取与适配性验证（只读 + 仅写 `~/gap`）：从 node2/node4 取完整 diff/commit + 独立 patch 文件，clone 最新 SPDK（`170cbb94…`）并 `git apply --check`，报告能否直接应用/需移植的 hunk | 已关闭 | 补丁=同事工作区 diff（base `e12b7cb`，6 文件 329+/6− + 未跟踪 `nvme_p99_v7.h`），无提交/无独立 patch；**随机读只在 `urma_perf.c`（+145 行）**；默认 apply 仅 usage 1 行上下文失败（`dmabuf`→`cpu`），`-C1` 全通过（小移植）；最新 tip 已自带 V3/`DUMP_SEC`/`TRACE_US`；node1 无外网，源码经 Windows 中转 |
| GAP-07 | 2026-11-19 | 构建 + target 启动（原大任务，后续已拆分） | 已关闭（阶段性） | 6/6 产物构建成功：`urma_perf` `c653c0a6…`、`stress_cluster_bench` `f5425d77…`、`nvmf_tgt` `6668b490…`、`mooncake_master` `ec8ef785…`、`nof_register` `bfe476ea…`；补丁只含 `urma_perf.c`（patch `eea4ca39…`，应用后 `614b008c…`）；target 已在 `4457` 起来（RAID0/strip 256/11 盘，timing dump 正常）；§1b 起未执行 |
| GAP-08 | 2026-11-19 | **无人值守连跑（用户明确要求）**：master → NoF 注册 → prefill 3.81TiB → 核心 4 臂 → 次要 2 臂 → 分析 → 收尾；带 marker 断点续跑、逐步落盘、硬阻塞即停 | 已中止（用户时间原因） | master（50056/8086/9006，PID 3280372）与注册（5 TiB，4457）成功；bench 重建 `USE_UB=ON` 后 prefill 实测 ~1.9 GB/s，500k/3.81TiB 需 ~37 min，**用户不接受 → 中止，转 GAP-09（150k 快速预实验）**；master/target 保持运行 |
| GAP-09 | 2026-11-19 | 120 秒/臂、300k × 8MiB（≈2.29 TiB）快速实验：停 prefill → 10s 读检查（失败则补灌）→ 核心 4 臂（120s）→ 分析；裸 SPDK 读完整 5 TiB 池 → 两臂均不绕回；标注"非 500k 口径、范围差异" | 待执行 | — |
| GAP-07 | 2026-11-19 | 构建 + 首轮实测（待 GAP-06）：gap 内 clone 最新 SPDK/Mooncake → 应用/移植补丁 → 编译 → 验证 → target(4457)/master(50056/8086/9006) + 注册 + 3.81 TiB prefill → 6 臂 × 60 s | 待执行 | — |

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

# GAP-05（已关闭 · 2026-11-19）· 工具补齐与可行性验证（只读 + 仅写 `~/gap`）

> 回执已收（见任务历史摘要）。三处需要记住的事实：①**node1 本机已有 `stress_cluster_bench`**（不是没有 bench）；②Mooncake 客户端与 bench 都**只有 LEGACY 慢 IO、没有 V3 buffer**；③node3 大页总够但**每 NUMA 仅 1160 页**，iobuf 可能需按节点补页。

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

# GAP-06（已关闭 · 2026-11-19）· 随机读补丁获取与适配性验证（只读 + 仅写 `~/gap`）

> 回执已收。三个关键事实：①补丁只存在于同事工作区；②**随机读只在 `urma_perf.c`**，p99 门控是旁路文件；③node1 无外网，后续源码/子模块必须经 Windows 中转。

> 背景：最新 SPDK（`urma_enable_v2` tip `170cbb94…`）的 `urma_perf.c` 没有随机读；同事说他的目录里有补丁。用户要求从同事目录取回。
> 约束：node2/node4 只读；所有落盘只在 node1 的 `~/gap`；**不启动任何服务、不 build、不跑流量**（本任务只做取补丁 + `git apply --check`）。
> 目标：拿到补丁本体，判断能否直接应用到最新代码；不能则列出冲突，供开发侧决定移植方案。

## 1. 取补丁（node2 / node4 只读）

- **1.1** 在两棵 SPDK 树上：`git rev-parse HEAD`、`git status --porcelain`、`git log -S"URMA_PERF_ADDR_MODE" --all --oneline`、`git log -S"--range-bytes" --all --oneline`（先找是否已有提交，而不是只工作区 diff）。
- **1.2** 取完整 diff：`git diff -- examples/nvme/urma_perf/urma_perf.c include/spdk_internal/trace_defs.h`；未跟踪文件（如 `lib/nvme/nvme_p99_v7.h`）给清单 + md5；若 `urma_perf.c` 依赖它，一并取。
- **1.3** 在同事目录里搜索独立 patch 文件：`grep -l "range-bytes\|URMA_PERF_ADDR_MODE"`（限 `*.patch` / `*.diff`），找到就取。
- **1.4** 产物：patch 与 diff 存 `~/gap/patches/`，每个文件 `base64 -w0` + md5；回执给 md5、行数、base commit、关键 hunk 摘要（≤10 行）。**不要把整份源码贴回来。**

## 2. 适配性验证（node1 的 `~/gap` 内）

- **2.1** `~/gap` 内 clone SPDK 最新 tip（`urma_enable_v2`，记录 `git rev-parse HEAD`；当前应为 `170cbb94…`）。
- **2.2** `git apply --check` 同事的 patch；报告成功/失败。
- **2.3** 若失败：给每个失败文件的 hunk 位置与冲突原因（≤20 行），判断是"小移植"还是"大改"。
- **2.3b** 同时报告：最新 `urma_perf.c` 里与随机/范围/seed/LBA 相关的现有开关（grep 结果），确认补丁要加什么。
- **2.4** 若找到的是**已提交的 commit**，优先 `git format-patch -1` 取该 commit 的 patch。

## 3. 结论

- 一句话：补丁能否直接应用到最新代码；不能则缺哪几个 hunk / 需改哪几个函数。
- 不 build、不跑、不启动任何东西。

## 回执必答（第一行）

补丁来源（工作区 diff / 哪个 commit / 独立 patch 文件）+ md5；能否直接 `git apply --check` 到最新 SPDK；若不能，冲突在哪些文件/函数。

---

# GAP-07（已关闭 · 阶段性 2026-11-19）· 构建 + target 启动（原大任务，后续阶段已拆分）

> **执行情况**：Stage A 六个产物全部构建成功；§1 target 已在 4457 起来并通过打点验收；按用户指令停手，§1b 及之后**未执行**。
> **以下 §1b 起为历史计划，已作废；后续按 GAP-08 起的小单逐条下发，不要按本文件续跑。**

> **前置（GAP-06 完成后）**：代码基线 = **GitHub 最新代码**（SPDK `urma_enable_v2` tip，Mooncake `nof-gdr-supercache-snapshot-930` tip）+ **随机读补丁**（从同事目录取，应用到 `~/gap` 内副本）；**全部在 `~/gap` 内 clone + 编译，只运行 gap 内产物**。
> **构建前置**：工具链、DPDK/UMDK 依赖、外网可达性先核实；构建失败 → 停手回报，不擅自换源码。
>
> **以下为实测部分。**
>
> **门槛状态**：用户已宣布 node1/node3 独占（2026-11-19）；高风险操作（按 PID 停进程、vfio 接管/还原、启停本方 target/master）已整体授权。仍禁：pkill/killall、reboot、rmmod udma、动系统服务/他人进程；异常即停并回报。
> 目标：在 node1/node3 上建立**自有基线**并定位 Mooncake 与裸 SPDK 的 8 MiB 读差距。**本轮会编译**（gap 内、最新源码 + 随机读补丁）；除补丁外不改代码、不做优化。
> 机器：**node1 = initiator/client，node3 = target/master**；两台不同物理机，数据跨机。
> 预计占机 60–90 min（含 target/master 启动、NoF 注册、3.81 TiB prefill）。
>
> **GAP-05 定稿决策（2026-11-19）**：
> 1. **Mooncake 臂驱动 = `stress_cluster_bench`**（`segment_read` / `segment_write`）；不启动 `mooncake_client` 服务。
> 2. **客户端账本口径（不对称，必须写进匹配矩阵）**：Mooncake 臂只有 **LEGACY 慢 IO**（`SPDK_URMA_STAGE_TRACE_US` + `URMA_SLOW_IO`，SINK=0，无 V3 buffer）；裸 SPDK 臂用 **V3 全量逐请求**（`SINK=buffer`）。
> 3. **liburma 统一**：所有 initiator 进程 `LD_LIBRARY_PATH=~/gap/lib`（`5cbe9f65…`）；target 用其自身 ldd 解析的库（记录 md5）。
> 4. **大页**：允许 takeover 脚本自动上调 `nr_hugepages`；若 NUMA 本地页不足导致启动失败，可按节点补页（记录前后值，可回退）。
> 5. **基线口径**：本环境（target `e7440ae0…`、liburma `5cbe9f65…`、e3bd build）与 Round6 不同，**数字不与 Round6 并列**；本轮 Mooncake vs urma_perf 的差值是唯一 gap 结论，历史数字只作漂移/量级参考。
> 6. **GAP-03 审计**已证明历史数字对条件不全同（strip/taskset/-s/范围），不参与结论。

## 0. 预检（只读；未授权时到此为止）

- **0.0 条件台账（每臂一行，贯穿全程）**：动手前先建台账文件（`conditions.csv` + `meta.md`），逐臂记录：
  节点角色与 IP（initiator / target / master）、**数据是否跨节点**；盘列表与顺序、BDF、strip；target 参数（`-m/-C/-I/-O/-L` 路径+md5、taskset、`-s`、transport、listener）；客户端 env（workers、chunk bytes、qpairs、liburma 路径+md5、打点 env）；负载参数（I/O 大小、seq/rand、seed、随机范围/`--range-bytes`、QD/批次、时长、warmup、measure mode）；跑前/跑中他人负载采样；起止时间与命令原文。
  **回执必须附台账；缺台账的臂，其数字不进 gap 结论。**
- **0.0b 匹配矩阵**：列一张表 `参数 | Mooncake 臂 | urma_perf 臂 | 是否一致 | 处理`，覆盖：节点角色、盘/顺序、strip、iobuf、max_io_size、C、mask、taskset、`-s`、transport、I/O 大小、QD、随机范围、warmup、时长。不一致的必须标 `有意变量` 或 `无法匹配（原因）`；**未在矩阵中列出的差异，不得用于结论**。
- **0.1 独占判定与处置**：node1/node3 可疑进程 10 s `/proc` 差值与绑核空闲率；他人负载 >1% 单核时，按 PID 停掉占用者（用户已授权，先 TERM 后 KILL；禁 pkill/killall），记录证据；不动系统服务。记录 load、`mpstat`。
- **0.2 构建与库（在 gap 内编译后核对）**：
  - 在 node3 的 `~/gap/target/` 用最新 SPDK 源码构建 `nvmf_tgt`；`ldd` 记录 liburma / liburma_common 路径 + md5；`-L` 指向 gap 内副本（系统库除外）。
  - URMA 设备名以最新源码/文档为准，与 initiator 的 `-device_name` 一致；记录。
  - `strings` 复核我们构建的 target 含 `SPDK_URMA_STAGE_TARGET_SINK` / `SPDK_URMA_TARGET_DUMP_SEC`；**不含则停手回报**。
- **0.3 bench 语义核对（只读）**：打出 `stress_cluster_bench --help` 全文（或从源码确认），逐项确认：`-master_server`、`-master_admin_port`（必须 9006）、`-metadata_server`（必须 `http://<node3>:8086/metadata`）、`-protocol ub`、`-device_name`、`-scenario segment_read/segment_write`、`-replica_num 0`、`-nof_replica_num 1`、`-nof_qpairs_per_segment 4`、`-batch_size 1`、`-shuffle_seed`、`-duration`、`-num_keys`、`-value_size`、`-warmup_keys`、`-nof_segments`、`-global_segment_size` 的语义。**若有任一项与§2 命令不符 → 停手回报，不改方案。**
- **0.3b bench 在 `~/gap` 内自行构建**：从 Mooncake 最新源码（`nof-gdr-supercache-snapshot-930` tip）在 `~/gap/mooncake/` 构建 `stress_cluster_bench`，产物与依赖放 `~/gap/bench/`；记录 md5。**命令只用 `~/gap/bench/stress_cluster_bench`**，不执行任何 gap 外二进制。`cwd=~/gap/...`，日志只写 gap。构建失败 → 停手回报。
- **0.4 NoF 注册工具（在 gap 内构建）**：从 Mooncake 最新源码构建 `nof_register` / `nof_unregister` 到 `~/gap/`（记录产物 md5）；`--help` 取关键参数；确认注册命令能把 target `4457` 注册到 master `50056`。注册前 master 应为空（新 master）。
- **0.5 大页与 NUMA（只读）**：node3 `HugePages_*` 与**每个 NUMA 节点**的空闲页；按 iobuf `8192,8192,1024,8388608`（≈8256 MiB）与 taskset `2-7`（属 node0）判断单 NUMA 是否够；不够时按节点补页（记录前后值，可回退）。
- **0.6 内存**：node1/node3 `free -g`；V3 只用于 urma_perf 臂（每进程按 12,000,000 条 ≈ 2.3 GB 预留）。
- **0.7 端口与 target 状态**：4457/50056/8086/9006/50156 全空闲；target 未运行、vfio 设备数 0、无旧 listener。
- **0.8 master 与 keys（必读）**：本轮在 **node3** 起我方新 master（50056/8086/9006）；旧进程已停、无 snapshot → **500k keys 需本轮 prefill**。用户 2026-11-19 已接受 prefill 覆盖盘上旧数据。
- **0.9 命令预写**：开始前把每臂的完整命令、env、预期输出文件写进 `meta.md`；执行中任何偏离 → 停手回报，不临场改参数。
- **0.10 构建清单冻结**：记录本次构建的确切来源——SPDK repo/分支/commit、Mooncake repo/分支/commit、随机读补丁文件 + md5、构建命令/CMake flags/编译器版本、各产物 md5 与 `strings` 特征；写入 `~/gap/baseline/MANIFEST.md`。**这就是以后修改代码的基线。**

## A. 构建（Stage A；失败即停，不进入实测）

> 前置事实（GAP-06）：**node1 已确认无外网**（GitHub/gitee 均不通）；**node3 尚未测过**；SPDK 最新源码已由 Windows 侧中转放入 `~/gap/spdk`（`170cbb94…`）；补丁在 `~/gap/patches/colleague_spdk.diff`（md5 `b70aa91c…`）；`git apply --check -C1` 通过，默认上下文有 1 行失败（usage 里 `default: dmabuf` vs 最新 `default: cpu`）。

- **A1 依赖预检**：node1/node3 上 `gcc --version`、`cmake --version`、`make --version`、`python3 --version`；DPDK（`/usr/local/lib/libdpdk*` 或 `pkg-config --modversion libdpdk`）、numa、isa-l；Mooncake 需要的 cmake/依赖。**缺什么列清单；能从 Windows 侧获取的走中转；不擅自装系统包。**
- **A2 源码与子模块**：**先分别测 node1 / node3 的出网**（`curl -m 8 -I https://github.com`、DNS 解析，各给结果）；**node1 已知不通、node3 未测**。能直连的节点就直接 clone（记录所用路径）；不能直连的走 Windows 侧 `--recurse-submodules` 拉齐后打包中转进 gap。SPDK 子模块（dpdk/isa-l 等，如需）与 Mooncake 子模块（pybind11 等）同法处理；记录各 repo 与子模块 commit。**不得使用 gap 外的源码。**
- **A3 打补丁**：在 `~/gap/spdk` 上**只应用 `urma_perf.c`**（用 `-C1` 或把补丁上下文改成最新 `default: cpu`）；应用后 `git diff --stat` 应只有 `examples/nvme/urma_perf/urma_perf.c`；保存"实际应用的补丁"与 md5。
- **A4 编译**：
  - node1：`./configure`（DPDK 路径按 A1）→ `make -j` → `build/examples/urma_perf`；`--help` 应出现 `--range-bytes` / `--lba-plan`；`strings` 应含 `SPDK_URMA_STAGE_READER_SINK` / `SPDK_URMA_STAGE_TRACE_US` / `URMA_SLOW_IO`。
  - node3：同源编译 `build/bin/nvmf_tgt`；`strings` 应含 `SPDK_URMA_TARGET_DUMP_SEC` / `SPDK_URMA_STAGE_TARGET_SINK`。
  - Mooncake：node1 构建 `stress_cluster_bench`（放 `~/gap/bench/`）；node3 构建 `mooncake_master` 与 `nof_register`。
  - 记录：configure/CMake 参数、编译器版本、产物 md5、构建耗时。
- **A5 冻结清单**：把 A2/A3/A4 的 commit、补丁 md5、构建参数、产物 md5 写入 `~/gap/baseline/MANIFEST.md`（即 §0.10）。
- **Gate**：任一构建失败或缺依赖无法在 gap 内解决 → 停手回报，不进入 §1。**不要用旧二进制顶替。**

## 1. 启动 target（仅在授权后；参数与 Mooncake 侧完全一致；listener=4457）

- 在 node3 的 `~/gap/target/` 内 clone SPDK 最新代码 + 应用/移植随机补丁（如需）→ `./configure && make -j` 构建 `build/bin/nvmf_tgt`；记录 flags、编译器版本、产物 md5。
- 在 gap 内准备 `target_nvme_takeover.sh`（从源码树复制），**只把 `LISTEN_PORT` 改为 4457**；记录脚本 md5 与 1 行 diff；用 `-w ~/gap/target`。
- 运行库：`ldd` 检查；如 liburma 来自 gap 外，复制到 `~/gap/lib` 并以 `LD_LIBRARY_PATH` 指向 gap（系统库除外）。
- 用 gap 内 target 启动：外层 `taskset -c 2-7`；`-R 256 -m 0xfc -C 64 -O 8388608 -I 8192,8192,1024,8388608 -N <§0.2 确认的设备名> -L <§0.2 确认的库目录> -p urma -s 10 -y`
  盘序：11 块数据盘，按脚本现算的顺序（记录成员盘与顺序）。
- 若 target 上已有旧 listener（4420/4421）→ 先 `nvmf_subsystem_remove_listener` 再加 4457；记录命令原文。
- 记录：完整命令行原文、PID、启动时间、listener、`nvmf_tgt` md5、`/tmp/nvmf_tgt.log` 路径。
- 验收：**4457** 监听；`/tmp/nvmf_tgt.log` 出现 URMA target timing 头部。
- **不动旧 master。**

## 1b. 启动我方 master（node3，新端口）

- 在 node3 的 `~/gap/mooncake/` 内 clone Mooncake 最新代码 → 构建 `mooncake_master`（记录 cmake flags、产物 md5）。
- 在 node3 起 gap 内 master：`~/gap/mooncake/mooncake_master --rpc_port=50056 --http_metadata_server_port=8086 --metrics_port=9006 --nof_heartbeat_interval_sec=120 --nof_heartbeat_failures_threshold=5`（心跳参数只作健壮性；记录原文）。日志写 `~/gap/...`。
- 验收：三个端口监听；`curl :9006/metrics` 可读。

## 1c. 注册 NoF 段

- 用 §0.4 的工具把 target `4457` 注册到 master `50056`；若已有容量 0 的同名记录，先 unregister 再 register（记录命令原文）。
- 验收：metrics 里 `nof_segment_total_capacity_bytes{... trsvcid:4457 ...} > 0`，端点/设备名正确。

## 1d. prefill（500k × 8 MiB = 3.81 TiB）

- 用 `~/gap/bench/stress_cluster_bench -scenario segment_write -role writer`：
  `-protocol ub -device_name <设备> -master_server <node3>:50056 -master_admin_port 9006 -metadata_server http://<node3>:8086/metadata -value_size 8388608 -num_keys 500000 -num_threads 16 -batch_size 8 -replica_num 0 -nof_replica_num 1 -nof_qpairs_per_segment 4 -global_segment_size 0 -local_buffer_size 536870912`
- 若 `-global_segment_size 0` 导致 setup 失败 → 回落默认 4 GB 并记录。
- 记录写入量、耗时、失败数；验收 `master_nof_allocated_bytes = 4,194,304,000,000`（允许等价误差）。超过 30 min 或失败 → 停手回报。

## 2. 测量臂（每臂 60 s；顺序如下）

**Mooncake 臂公共 env（LEGACY 口径，SINK=0）**：
```
LD_LIBRARY_PATH=~/gap/lib
SPDK_URMA_STAGE_TRACE_US=500
SPDK_URMA_TRACE=1
```
（阈值 500 µs 只打印慢 IO；60 s 内日志 >500 MB → 停手回报。`SPDK_URMA_TRACE=1` 保留每轮最后 8192 条 tx/rx CSV。）

**urma_perf 臂公共 env（V3 全量口径）**：
```
LD_LIBRARY_PATH=~/gap/lib
SPDK_URMA_STAGE_TRACE_US=1
SPDK_URMA_STAGE_READER_SINK=buffer
SPDK_URMA_STAGE_READER_PATH=~/gap/<本轮>/<arm>.v3
SPDK_URMA_STAGE_READER_CAPACITY=12000000
```
target 侧：`-s 10`（聚合 dump 进 target 日志）。

| 臂 | 命令/配置 |
| --- | --- |
| G6-1 | `~/gap/bench/stress_cluster_bench -scenario segment_read`，4 线程，顺序：`-role reader -protocol ub -device_name <设备> -master_server <node3>:50056 -master_admin_port 9006 -metadata_server http://<node3>:8086/metadata -value_size 8388608 -num_keys 500000 -num_threads 4 -batch_size 1 -warmup_keys 64 -duration 60 -shuffle_seed 0 -replica_num 0 -nof_replica_num 1 -nof_qpairs_per_segment 4 -local_buffer_size 536870912 -global_segment_size 0` |
| G6-2 | 同 G6-1，`-shuffle_seed 20261115` |
| G6-3 | 同 G6-1，`-num_threads 1` |
| G6-4 | 同 G6-2，`-num_threads 1` |
| G6-5 | `urma_perf -w read -o 8388608 -T 1 -b 1 -t 60 -n 1 -g 0 -l 0 -M cpu`，`URMA_PERF_ADDR_MODE=seq`（若该 env 不存在 → 顺序 LBA CSV + `--lba-plan`） |
| G6-6 | 同 G6-5，rand：`URMA_PERF_ADDR_MODE=rand URMA_PERF_RANDOM_SEED=20261115 --range-bytes 4194304000000`（若 env 不存在 → 固定种子随机 LBA CSV + `--lba-plan`） |
| G6-7（可选） | 同 G6-6，不加 `--range-bytes`（全 namespace，仅量级参考） |

每臂记录：起止时间、完整命令/env、bench/urma_perf 输出（avg/p50/p90/p99/p99.9/max、QPS）、V3 文件路径+大小、target 日志时间窗、跑前/跑中他人负载采样、日志大小。
- Mooncake bench / urma_perf 必须**正常退出**（SIGTERM 可，禁 SIGKILL），否则 V3/CSV 不落盘。
- 若出现 undefined symbol、buffer sink 报错、`-global_segment_size 0` setup 失败 → 记录并停（`-global_segment_size` 可回落默认 4 GB 并记录），不自行改其它参数。

## 3. 聚合与分析（原始文件不上传）

- V3 文件留在 **initiator 节点（node1）的 `~/gap/...`**；回执给 `~/gap` 下的相对路径与 md5。
- **urma_perf 臂**：用本仓脚本生成聚合表：
  ```
  python3 scripts/decode_urma_stage_v3.py <v3文件> --out <arm>_agg.txt
  ```
  回执给 `decoded/valid/dropped`、`roundtrip_us` 与各分段（`rx_buffer/buffer_exec/bdev/bdev_post/data/residual/outside`）的 `mean/p50/p90/p99/p99.9/max`（µs）。
- **Mooncake 臂**：给 bench 自己打印的时延统计（avg/p50/p90/p99/p99.9/max、QPS）；给 `URMA_SLOW_IO` 行数与其中 `target_us/bdev_us/data_us/outside_us/residual_us` 的分布（用 awk 汇总，≤30 行）；给 `SPDK_URMA_TRACE` CSV 的行数（如有）。
- 每臂都给 target 聚合 dump 最后两个 10 s 块原文（`W9 exec->cpl` 与 `push JFC wait (C2H)`）。
- **跨层算式**：`客户端+网络 = E2E − target_us`（用各自的均值与 p99 分别算）；不得把 Mooncake 的 LEGACY 慢 IO 分布与 urma_perf 的 V3 全量分布直接并列，写进匹配矩阵的"口径"列。
- **不与 Round6 数字并列**；历史数字只作量级参考。

## 4. 收尾与回退

- 停 client / urma_perf（自然退出，等 V3 落盘）；target 用 SIGTERM 停（**不要 SIGKILL**），确认 `/tmp/nvmf_tgt.log` 尾部完整。
- 停我方 master（记录 PID，SIGTERM）；不动他人进程。
- 若本轮做过 disk takeover：`target_nvme_takeover.sh -r` 还盘，确认盘回 nvme、4457 不监听、vfio 设备数 0。
- 回退：旧 master 不动；若 target 起不来或 prefill 失败 → 停手回报，不重启旧 master、不擅改端口。
- 结束态：target 停、盘还原、我方 master 停；本轮 prefill 前工作集为 0，无旧 keys 被覆盖。

## 5. 约束

- 用户已宣布独占（2026-11-19）：**按 PID 停进程已授权**；仍禁 pkill/killall、reboot、rmmod udma、动系统服务/他人进程。
- **常备坑（2026-11-19 实测）**：`target_nvme_takeover.sh -r`（还盘）**必须带 `-y`**；否则 `confirm()` 会等 stdin，非交互下永久挂死（本次已挂 6 分钟后按 PID 清除）。
- **工作目录铁规**：node1/node3 上所有写入只在 `~/gap` 内；gap 外只读，严禁修改/删除/移动/创建（见《工作目录铁规》）。
- 本轮**允许在 `~/gap` 内从确认源码编译**（唯一例外）；**只运行 gap 内自行构建的产物**，不执行 gap 外的工具/二进制。除随机读补丁外不改代码、不做性能优化。
- 资料最小化：V3 原始文件不传；每臂聚合表 ≤40 行。
- 任何一步与预期不符（段丢失、V3 不落盘、dropped 过多、他人负载超标）→ 停止并回报，不自行改方案。

## 回执必答的一句话（第一行）

构建是否全部成功（各产物 md5、补丁 md5、构建耗时）；各臂是否全部完成；prefill 耗时；Mooncake 与 urma_perf 的 E2E、target `bdev`（W9）、`data`（C2H）三项的均值与 p99 差值；各自客户端账本口径（LEGACY vs V3）与样本量。

---

# GAP-08（已中止 · 2026-11-19）· 无人值守连跑：master → 注册 → prefill → 核心 4 臂 → 次要 2 臂 → 收尾

> **中止原因（2026-11-19 用户定）**：500k × 8 MiB 的 prefill 实测 ~1.9 GB/s，需 ~37 min，用户不接受。改为 **GAP-09：120 秒/臂、300k keys（≈2.29 TiB）**；master / target / 5 TiB 注册保持不动，不重新注册。

> **本次为用户明确要求的无人值守连跑（"一单一阶段"的例外）**：按固定顺序自动执行，**每步完成立即落盘、写进度、写 marker**；不等待用户输入。
> **最重要数据先跑**：master → 注册 → prefill → 核心 4 臂（Mooncake seq/rand 4t、urma_perf seq/rand）→ 次要 2 臂（Mooncake 1t）→ 可选第 7 臂。
> 机器：node1（initiator）/ node3（target/master）；target 当前在 4457 运行（PID 3243095），**不得重启**。
> 约束：只用 `~/gap` 内产物；gap 外只读；按 PID 停进程（禁 pkill/killall）；不 reboot、不 rmmod udma；`-r` 还盘必须带 `-y`。
> **硬阻塞**（target 消失/端口丢失/master 起不来/注册失败/prefill 失败）→ 写 `BLOCKED.md` 并停；**不改参数、不换二进制、不重启 target**。

## 0. 前置检查（只读）

- target：`ss -ltnp | grep :4457`；`cat ~/gap/run/nvmf_tgt.pid`；`tail -5 ~/gap/logs/nvmf_tgt.log`（应有 timing dump）。
- 端口：50056/8086/9006 空闲（若已被我方 master 占用，进入幂等分支）。
- 资源：`free -g`；`df -h ~/gap`（≥10 GB）。
- **设备名**：`sudo -n tr '\0' '\n' < /proc/3243095/environ | grep SPDK_URMA_DEV_NAME` → 记 `DEV`；取不到 → BLOCKED。
- **NQN**：`python3 ~/gap/spdk/scripts/rpc.py -s ~/gap/run/spdk.sock nvmf_get_subsystems`，解析第一项 `subnqn` → 记 `NQN`；失败 → BLOCKED。
- 结果目录：`~/gap/results/GAP-08/{logs,markers}`；初始化 `PROGRESS.md`。

## 1. 幂等与断点

- marker：`~/gap/results/GAP-08/markers/<step>.ok`（master / register / prefill / arm_A1..A7 / analyze / cleanup）。
- 有 marker 且验收仍成立 → 跳过；marker 在但验收不成立 → 删 marker 按未完成处理，PROGRESS 记录。
- 每步完成：`PROGRESS.md` 追加一行（时间、步骤、关键数值、产物路径+md5），再写 marker。
- 单臂失败：重试 1 次；仍失败 → 记 `FAILED` 并继续下一臂（不阻塞）。

## 2. 起 master（验收后写 master.ok）

- 命令（逐字）：
  `~/gap/mooncake_src/src/build/mooncake-store/src/mooncake_master --rpc_port=50056 --http_metadata_server_port=8086 --metrics_port=9006 --enable_http_metadata_server=true --nof_heartbeat_interval_sec=120 --nof_heartbeat_failures_threshold=5`
  （**已接受偏差 D1**：原任务书漏了 `--enable_http_metadata_server=true`，导致 8086 不监听；补上后验收通过。已运行的 master 无需重启。）
- `LD_LIBRARY_PATH` 用构建记录/MANIFEST 中的 gap 内路径；`ldd` 无 not found（系统库除外）；记录。
- 日志 `~/gap/results/GAP-08/logs/mooncake_master.log`；PID 写同目录 `mooncake_master.pid`。
- 验收：50056/8086/9006 LISTEN；`curl -s 127.0.0.1:9006/metrics | grep master_nof_allocated_bytes` 可读（预期 0）。

## 3. 注册 NoF 段（验收后写 register.ok）

- 看列表：`~/gap/mooncake_src/src/build/mooncake-store/src/nof_unregister 141.61.84.149:50056 --list`
- 若有 `trsvcid:4457` 且容量 0 的旧记录：`nof_unregister 141.61.84.149:50056 4457`（只删匹配 4457 的项）。
- 注册：`~/gap/mooncake_src/src/build/mooncake-store/src/nof_register "$NQN" 1 141.61.84.149 4457 URMA 141.61.84.149:50056 5497558138880`
  （nqn、nsid、traddr、trsvcid、trtype、master、size=5 TiB；失败则停并原样回报错误）
- 验收：metrics `nof_segment_total_capacity_bytes{... trsvcid:4457 ...}` > 0；记录原值。

## 3b. 重建 bench（用户已授权 · 2026-11-19）

- **原因**：Stage A 构建时 `USE_UB=OFF`，bench 不支持 `-protocol ub`（URMA/UB 传输未编译，`multi_transport.cpp:505 Unsupported transport ub`）。
- 在同一源码、同一 build 目录上追加 `-DUSE_UB=ON`（保留 `-DUSE_NOF=ON`、`-DUSE_NOF_URMA=ON` 及其它现有 cache 值）：
  ```
  cmake -S ~/gap/mooncake_src/src -B ~/gap/mooncake_src/mc_g7/build -DUSE_UB=ON
  cmake --build ~/gap/mooncake_src/mc_g7/build --target stress_cluster_bench -j
  ```
  （build 目录按实际路径；记录完整命令与 CMakeCache 的 `USE_UB/USE_NOF/USE_NOF_URMA/USE_CUDA/USE_NOF_GPU_DIRECT`）
- 验收：新产物 md5、`--help` 正常、`-protocol ub` 不再报 Unsupported；把新 flags 与 md5 写入 `MANIFEST.md`。
- **只重建 node1 的 bench**；master / target / nof_register 不动。

## 4. prefill（验收后写 prefill.ok；上限 30 min）

- **运行身份（已接受偏差 D2）**：所有 initiator 侧进程（bench / urma_perf）用 `sudo -n` 以 root 运行（非 root 时 DPDK 因 IOVA=PA 初始化失败，已实测）；环境变量用 `sudo -n env VAR=...` 显式传递；记录最终命令。

- 命令（逐字，env 见下；**root 执行**）：
  `sudo -n env LD_LIBRARY_PATH=<gap 内构建库路径> SPDK_URMA_DEV_NAME=$DEV SPDK_URMA_CAPSULE_TRANSPORT=urma SPDK_URMA_MAX_IO_SIZE=8388608 ~/gap/bench/stress_cluster_bench -scenario segment_write -role writer -protocol ub -device_name "$DEV" -master_server 141.61.84.149:50056 -master_admin_port 9006 -metadata_server http://141.61.84.149:8086/metadata -value_size 8388608 -num_keys 500000 -num_threads 16 -batch_size 8 -replica_num 0 -nof_replica_num 1 -nof_qpairs_per_segment 4 -global_segment_size 0 -local_buffer_size 536870912`
- env：`LD_LIBRARY_PATH` 按 §2；`SPDK_URMA_DEV_NAME=$DEV`、`SPDK_URMA_CAPSULE_TRANSPORT=urma`、`SPDK_URMA_MAX_IO_SIZE=8388608`。若 `-global_segment_size 0` setup 失败 → 回落 4 GB 并记录。
- 日志 `.../logs/prefill.log`；记录开始/结束、写入量、失败数。
- 验收：`master_nof_allocated_bytes` ≈ 4,194,304,000,000（记录实际值）；超时/失败 → BLOCKED。

## 5. 测量臂（每臂 60 s；完成一臂立即落盘+marker，再跑下一臂）

> **历史参照（用户提供的 Round5 命令文档，本地）**：Mooncake 用 `run_nof_bench.py`（`--seed 42`、`--warmup-keys 64`、`--capacity 5497558138880`=5 TiB、strip 128）；裸 SPDK 用 `run_exp.sh -S 128 ...`。本轮 bench 工具不同、strip 256，**不与 Round5/6 数字并列**，仅用于核对参数口径（key 数、容量、warmup、慢 IO 阈值 500 µs 均已对齐）。

- **所有臂命令均以 `sudo -n env <下列 env> ` 前缀执行（root，见 D2）**；记录最终命令。
- Mooncake 公共 env：`LD_LIBRARY_PATH`（§2）、`SPDK_URMA_DEV_NAME=$DEV`、`SPDK_URMA_CAPSULE_TRANSPORT=urma`、`SPDK_URMA_MAX_IO_SIZE=8388608`、`SPDK_URMA_STAGE_TRACE_US=500`、`SPDK_URMA_TRACE=1`。
- urma_perf 公共 env：`LD_LIBRARY_PATH=~/gap/lib:~/gap/spdk/build/lib`、`SPDK_URMA_DEV_NAME=$DEV`、`SPDK_URMA_CAPSULE_TRANSPORT=urma`、`SPDK_URMA_STAGE_TRACE_US=1`、`SPDK_URMA_STAGE_READER_SINK=buffer`、`SPDK_URMA_STAGE_READER_PATH=~/gap/results/GAP-08/<arm>.v3`、`SPDK_URMA_STAGE_READER_CAPACITY=12000000`。
- A1 Mooncake seq 4t：`~/gap/bench/stress_cluster_bench -scenario segment_read -role reader -protocol ub -device_name "$DEV" -master_server 141.61.84.149:50056 -master_admin_port 9006 -metadata_server http://141.61.84.149:8086/metadata -value_size 8388608 -num_keys 500000 -num_threads 4 -batch_size 1 -warmup_keys 64 -duration 60 -shuffle_seed 0 -replica_num 0 -nof_replica_num 1 -nof_qpairs_per_segment 4 -local_buffer_size 536870912 -global_segment_size 0`
- A2：同 A1，`-shuffle_seed 42`（与同事 Round5/6 Mooncake 的 `--seed 42` 对齐；urma_perf 仍用 20261115）
- A3 urma_perf seq：`~/gap/spdk/build/examples/urma_perf -w read -o 8388608 -T 1 -b 1 -t 60 -n 1 -g 0 -l 0 -M cpu`，env `URMA_PERF_ADDR_MODE=seq`
- A4 urma_perf rand：同 A3，env `URMA_PERF_ADDR_MODE=rand URMA_PERF_RANDOM_SEED=20261115`，加 `--range-bytes 4194304000000`
- A5：同 A1，`-num_threads 1`
- A6：同 A2，`-num_threads 1`
- A7（可选）：同 A4，去掉 `--range-bytes`（全 namespace）
- 每臂记录：起止、完整命令/env、stdout 日志（tee 到 `logs/<arm>.log`）、V3 路径+大小+md5、target 日志时间窗、`URMA_SLOW_IO` 行数；写 marker。

## 6. 分析（写 analyze.ok）

- A3/A4/A7：`python3 ~/gap/scripts/decode_urma_stage_v3.py <v3> --out ~/gap/results/GAP-08/<arm>_agg.txt`（脚本从交接仓取，放到 node1 的 `~/gap/scripts/`；不得从 gap 外执行）。
- Mooncake 臂：`grep -c URMA_SLOW_IO logs/<arm>.log`；awk 汇总 `target_us/bdev_us/data_us/outside_us/residual_us`（≤20 行）。
- target：按每臂时间窗截取最后两个 10 s dump 块（W9 与 push JFC）。
- 生成 `SUMMARY.md`：每臂 E2E（bench/urma 输出）+ target W9/C2H + 慢 IO 计数；**只列数据，不做解释**。

## 7. 收尾（写 cleanup.ok；仅在核心 A1–A4 全部完成时执行）

- 停 bench/urma（自然退出）；停 master（pidfile，SIGTERM）；target SIGTERM；`target_nvme_takeover.sh -r -y` 还盘（**必须 -y**）；验 4457 不监听、vfio 设备数 0。
- 若 A1–A4 有失败或中途 BLOCKED：**不还盘、不停 target/master**，写 `BLOCKED.md`（现场、已完成臂、失败原因），等开发侧。
- 回执给：各步骤状态、prefill 耗时与分配量、每臂数值摘要、产物路径+md5、结束态。

## 回执必答（第一行）

master/注册/prefill 是否成功；A1–A4 是否完成；每臂 E2E 与 target W9/C2H 关键值；是否已收尾。

---

# GAP-09（待执行 · 2026-11-19）· 120 秒/臂、300k keys（≈2.29 TiB）快速实验

> **用户决定（2026-11-19）**：每臂 **120 秒**；数据量按 120 秒的读量选：**300,000 keys × 8 MiB = 2,516,582,400,000 B（≈2.29 TiB）**。
> **选值依据（不绕回是硬前提）**：
> - Mooncake 臂：120 s × 顺序 ~16.4 GB/s ≈ 1.97 TB（随机 ~1.42 TB）< 300k×8MiB=2.52 TB → **不绕回（余量 28%/78%）**；且 2.52 TB > 物理内存 2.26 TB。
> - 裸 SPDK 臂：读取范围设为**完整 5 TiB 注册池**（同事原始方法也是读全 namespace）；120 s × 顺序 ~34.1 GB/s ≈ 4.10 TB（随机 ~3.08 TB）< 5.50 TB → **不绕回（余量 34%/79%）**。
> - 口径差异：裸 SPDK 读的 5 TiB 范围大于 Mooncake 的 2.52 TB 数据区，**必须写进匹配矩阵**。
> 预计 prefill：2.52 TB ÷ 1.9 GB/s ≈ 22 min（若中止的 500k prefill 已覆盖前 300k，10 s 读检查会直接通过，无需重灌）。**标注"非 500k 口径"，不与同事基线并列**。
> 前置：master（50056/8086/9006）、target（4457）、5 TiB 注册**保持不动**；只停当前 prefill。
> 约束：gap-only、PID 停进程（禁 pkill）、root 运行（D2）、每步落盘。

## 0. 停止当前 prefill

- `ps -eo pid,args | grep stress_cluster_bench` → 记 PID；`kill -TERM`；10 s 后仍在则 `kill -KILL`；记录停止时刻与当时的 `master_nof_allocated_bytes`。
- **不动 master / target / 注册**。

## 1. 10 秒读检查（300k keys）

- 用 300k 做 10 s 顺序读（root；env 同 GAP-08 §5 的 Mooncake 臂；`-duration 10`，其余参数同 A1 但 `-num_keys 300000`）。
- 记录 `failed` 数：
  - `failed=0` → 直接 §2；
  - `failed>0` → §1b。

## 1b. 补灌 300k（仅 failed>0 时）

- `segment_write -num_keys 300000 -num_threads 32 -batch_size 16`（其余参数同 GAP-08 prefill 命令）；记录耗时与速率；完成后重跑 §1 的 10 s 检查；仍 failed>0 → 停手回报。

## 2. 核心 4 臂（每臂 120 s；`-num_keys 300000`）

- A1 Mooncake seq 4t：同 GAP-08 A1 命令，但 `-num_keys 300000`、`-duration 120`、`-shuffle_seed 0`
- A2 Mooncake rand 4t：同 A1，`-shuffle_seed 42`
- A3 urma_perf seq：`-w read -o 8388608 -T 1 -b 1 -t 120 -n 1 -g 0 -l 0 -M cpu`，`URMA_PERF_ADDR_MODE=seq`，`--range-bytes 5497558138880`（完整 5 TiB 注册池，不绕回）
- A4 urma_perf rand：同 A3，`URMA_PERF_ADDR_MODE=rand URMA_PERF_RANDOM_SEED=20261115`，`--range-bytes 5497558138880`
- 公共 env、V3/LEGACY、落盘、marker 同 GAP-08 §5。`--range-bytes` 假设数据从段首顺序分配；记录实际 `master_nof_allocated_bytes` 并标注该假设。
- A5/A6（Mooncake 1t）时间够再跑；不做 A7。

## 3. 分析与回执

- A3/A4 用解码脚本出聚合表；Mooncake 臂给 bench 统计 + `URMA_SLOW_IO` 计数 + target 最后两个 10 s dump。
- 标注：**300k keys / 2.29 TiB，非 500k 口径；裸 SPDK 臂读完整 5 TiB 池（范围大于 Mooncake 数据区，口径差异记录）；两臂均不绕回**。
- **不清理**：master/target 保持运行，便于之后决定是否扩到 500k。

## 回执必答（第一行）

10 s 检查的 failed 数；是否补灌；A1–A4 是否完成；E2E 与 target W9/C2H 关键值。
