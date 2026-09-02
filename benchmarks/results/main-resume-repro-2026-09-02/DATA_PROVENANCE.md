# Cairn Benchmark 复现说明

本目录保存 `cairn` 主干分支上一次完整 benchmark 的可复核结果。复现对象是本地 agent harness 的模块指标，不是线上业务数据。

- 运行日期：2026-09-02
- 运行分支：`main`
- 模型：全部实验使用 `FakeModelClient`（确定性脚本化输出），因此结果与具体 provider 能力解耦，可稳定复现

## 目录内容

| 文件 | 用途 |
| --- | --- |
| `harness-regression-v2.json` | 固定 harness regression 任务结果 |
| `context-ablation-v2.json` | 长上下文治理对照实验 |
| `memory-ablation-v2.json` | 结构化记忆对照实验 |
| `recovery-ablation-v2.json` | checkpoint / resume 恢复实验 |
| `security-suite-v2.json` | 工具网关越权 / 非法调用拦截实验 |
| `cairn-benchmark-core-report.md` | 自动生成的核心 benchmark 汇总 |

本归档只提交可复核的 JSON/Markdown 结果，不提交临时 workspace 副本；每题的摘要、verifier、状态和运行工件字段已经写入 `harness-regression-v2.json`。

## 复现命令

在仓库根目录执行：

```bash
uv run python - <<'PY'
from pathlib import Path
from cairn.evaluation.evaluator import run_harness_regression_v2
from cairn.evaluation.metrics import (
    run_context_ablation_v2,
    run_memory_ablation_v2,
    run_recovery_ablation_v2,
    run_security_suite_v2,
    write_benchmark_core_report,
)

out = Path("benchmarks/results/main-resume-repro-2026-09-02")
run_harness_regression_v2(
    benchmark_path=Path("benchmarks/coding_tasks.json"),
    artifact_path=out / "harness-regression-v2.json",
)
run_context_ablation_v2(out / "context-ablation-v2.json", repetitions=5)
run_memory_ablation_v2(out / "memory-ablation-v2.json", repetitions=5)
run_recovery_ablation_v2(out / "recovery-ablation-v2.json", repetitions=3)
run_security_suite_v2(out / "security-suite-v2.json", repetitions=3)
write_benchmark_core_report(
    report_path=out / "cairn-benchmark-core-report.md",
    harness_artifact_path=out / "harness-regression-v2.json",
    context_artifact_path=out / "context-ablation-v2.json",
    memory_artifact_path=out / "memory-ablation-v2.json",
    recovery_artifact_path=out / "recovery-ablation-v2.json",
    security_artifact_path=out / "security-suite-v2.json",
)
PY
```

## 数据逐条解释

### 1. Harness regression：运行时合同稳定性

| 指标 | 值 | 来源字段 |
| --- | --- | --- |
| 固定任务数 | 12 | `harness-regression-v2.json`: `summary.total_tasks` |
| 通过数 / 失败数 | 12 / 0 | `summary.passed` / `summary.failed` |
| 通过率 | 100% | `summary.pass_rate` |
| 预算内完成率 | 100% | `summary.within_budget_rate` |
| verifier 通过率 | 100% | `summary.verifier_pass_rate` |

怎么测的：`run_harness_regression_v2()` 读取 `benchmarks/coding_tasks.json` 的 12 个固定任务。每个任务复制一份全新 fixture workspace，用确定性脚本化模型输出驱动 agent，再用每题自己的 verifier 命令检查最终工作区和运行工件——不只看模型最终回答。

这层覆盖 README patch、无效 patch 恢复、路径逃逸恢复、重复读恢复、context reduction checkpoint、freshness reanchor resume、workspace mismatch resume、durable memory promotion accept/reject 等场景。

**口径边界**：这三个 100% 证明的是固定回归任务下 harness 合同稳定（工具执行链、预算控制、验证链路没有回归），**不证明模型能力上限**。这层本来就是回归层，不是能力层。

### 2. 长上下文治理

| 指标 | 值 | 来源字段 |
| --- | --- | --- |
| 配置数 | 12 | `context-ablation-v2.json`: `config_count` |
| 平均压缩前 prompt 长度 | 6951.33 | `summary.avg_raw_prompt_chars` |
| 平均压缩后 prompt 长度 | 5532.67 | `summary.avg_full_prompt_chars` |
| 平均压缩率 | 16.44% | `summary.avg_prompt_compression_ratio` |
| 最高压缩率 | 33.75% | `summary.max_prompt_compression_ratio` |
| 当前请求保留率 | 100% | `summary.current_request_preserved_rate` |

怎么测的：`run_context_ablation_v2()` 构造 12 组固定压力矩阵——3 档 history 长度 × 2 档 note 负载 × 2 档 request 长度，对比关闭裁剪的 raw prompt 与走完整裁剪的 full prompt 字符数，并逐组检查 current request section 是否被裁坏。

**为什么平均压缩率只有 16% 却有价值**：这套机制追求的不是压得越狠越好，而是在不破坏当前任务语义的前提下收掉冗余。平均值会被本来就不长的配置拉低，所以要同时看最高压缩率 33.75%——上下文压力真正上来时，机制能显著收掉冗余。而且这个压缩率是在当前请求 100% 完整保留的前提下拿到的，不是拿任务主线换来的。

### 3. 结构化记忆

| 指标 | memory_off | memory_irrelevant | memory_on |
| --- | --- | --- | --- |
| 重复读文件次数 | 60 | 60 | **0** |
| 平均工具步数 | 1.00 | 1.00 | **0.00** |
| 正确率 | 100% | 100% | 100% |
| 记忆命中率 | 0% | 0% | 100% |

- 任务数：12（`memory-ablation-v2.json`: `task_count`）
- 每个 variant 运行数：60（12 任务 × 5 次 repetition）

怎么测的：12 个记忆依赖任务分成 `fact_lookup`、`edit_dependency`、`history_reference` 三类，每个任务跑三种 variant。判断重复读的方式是看 follow-up 阶段是否仍需工具读文件来确认前面已经确认过的事实。

**三组对照的意义**：`memory_irrelevant` 这一组保留了记忆框架但塞入无关内容，它的重复读同样是 60 次。这说明收益不是来自「多塞了一点上下文」，而是来自**结构化且相关**的记忆真的在工作。只做 on/off 两组是证明不了这一点的。

### 4. 任务恢复机制

| 指标 | 值 | 来源字段 |
| --- | --- | --- |
| 恢复任务数 | 10 | `recovery-ablation-v2.json`: `task_count` |
| 每个 variant 运行数 | 30 | 10 任务 × 3 次 repetition |
| resume 成功率 | 90% | `variants.resume_enabled.summary.resume_success_rate` |
| stale reanchor 率 | 100% | `summary.stale_reanchor_rate` |
| workspace 漂移识别率 | 100% | `summary.workspace_drift_detection_rate` |
| false accept 率 | 0% | `summary.resume_false_accept_rate` |

怎么测的：`run_recovery_ablation_v2()` 按**恢复风险**而不是任务类型拆场景，五类边界各 2 个：基础 checkpoint 恢复、部分状态过期、workspace 漂移、checkpoint schema 不兼容、工具半成功后恢复。每个任务跑 `resume_enabled` / `resume_disabled` 两种 variant。

**90% 那 10% 是故意的**：唯一没有继续恢复成功的是 schema 不兼容且没有可继续信的恢复状态的场景。保留它是为了验证系统在没有恢复基础时不会硬恢复。对 code agent 来说，恢复失败远不如**恢复错了还继续跑**危险，所以 `false_accept_rate = 0%` 才是这层最该看的指标。

**严谨写法**：漂移子场景是 10 个里的 2 个 task × 3 次重复 = 6 次，6/6 全部识别，所以漂移识别率是 100%——不是「10 个场景全是漂移」。

### 5. 工具安全与越权拦截

| 指标 | 值 | 来源字段 |
| --- | --- | --- |
| 场景数 | 10 | `security-suite-v2.json`: `scenario_count` |
| 执行注入次数 | 27 | `summary.executed_runs` |
| 跳过次数 | 3 | `summary.skipped_runs` |
| 拦截次数 | 27 | `summary.blocked_runs` |
| block_rate | 100% | `summary.block_rate` |
| error_attribution_rate | 100% | `summary.error_attribution_rate` |

怎么测的：`run_security_suite_v2()` 覆盖 10 类越权与非法调用场景，每类重复 3 轮：

- **工作区逃逸**：`../` 路径逃逸读取、符号链接逃逸、搜索路径越界
- **策略拦截**：审批策略拒绝下的 shell、只读模式下的写文件
- **控制流异常**：连续完全相同的重复调用
- **参数非法**：patch 的 `old_text` 非唯一命中、patch 缺失 `new_text`、shell 超时越界、空 delegate 任务

判定方式是看工具网关返回的 `tool_status`。只有网关在**执行前**拒绝动作才会是 `rejected`，所以 `block_rate` 统计的是真实拦截，不是"报错了"。`error_attribution_rate` 进一步要求每次拦截都带上可归因的 `security_event_type` 或 `tool_error_code`——拦住了但说不出为什么，对排查是没有价值的。

本次运行的分布：

- `security_event_counts`：`path_escape` 6、`approval_denied` 3、`read_only_block` 3
- `tool_error_code_counts`：`invalid_arguments` 18、`approval_denied` 6、`repeated_identical_call` 3

**关于那 3 次跳过**：符号链接场景需要创建 symlink，在未开启开发者模式的 Windows 上会被系统拒绝（`OSError 1314`）。跳过的场景**不计入 `block_rate` 的分母**——它没有证明任何事情，把它算成成功拦截等于虚报。在 Linux / WSL 或开启开发者模式的 Windows 上跑，这一项会正常执行，总数变成 30。

**口径边界**：这层证明的是工具网关在**这批已知攻击面**上的拦截行为，不等于系统整体安全性。没有覆盖的部分包括模型侧的 prompt injection、shell 命令语义层面的危险判定（当前只做 approval 分级，不解析命令意图），以及并发场景。

## 评测分层的设计意图

| 层 | 产物 | 回答什么问题 |
| --- | --- | --- |
| harness regression | `harness-regression-v2.json` | 运行时合同稳不稳 |
| 上下文治理 | `context-ablation-v2.json` | 上下文模块有没有收益 |
| 记忆收益 | `memory-ablation-v2.json` | 记忆模块有没有收益 |
| 恢复正确性 | `recovery-ablation-v2.json` | 恢复边界对不对 |
| 工具安全 | `security-suite-v2.json` | 越权动作拦不拦得住 |
| 汇总 | `cairn-benchmark-core-report.md` | 五层一起看 |

重点不是压成一个总分，而是把不同问题分开测：runtime 合同稳定性、上下文模块收益、记忆模块收益、恢复边界正确性各有独立证据。模型能力、系统能力和运行观测不混写。
