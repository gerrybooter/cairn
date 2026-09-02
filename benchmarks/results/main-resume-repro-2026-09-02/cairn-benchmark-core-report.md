# Cairn Benchmark Core Report

这轮 benchmark 收缩到 Harness regression、context ablation、working memory ablation、recovery ablation 和 tool security 五层，不把 provider、run aggregation 或 durable memory 的别的结论揉进来。

## Harness Regression
- 固定 regression 任务数：12
- pass_rate：100.00%
- within_budget_rate：100.00%
- verifier_pass_rate：100.00%

## Context Ablation
- 配置数：12
- avg_full_prompt_chars：5532.67
- avg_raw_prompt_chars：6951.33
- avg_prompt_compression_ratio：16.44%
- max_prompt_compression_ratio：33.75%
- current_request_preserved_rate：100.00%

## Working Memory Ablation
- memory_on repeated_reads：0
- memory_off repeated_reads：60
- memory_on avg_tool_steps：0.00
- memory_on correct_rate：100.00%
- memory_hit_rate：100.00%

## Recovery / Resume Ablation
- resume_success_rate：90.00%
- stale_reanchor_rate：100.00%
- workspace_drift_detection_rate：100.00%
- resume_false_accept_rate：0.00%

## Tool Security Suite
- 越权 / 非法调用场景数：10
- 执行注入次数：27（跳过 3 次）
- block_rate：100.00%
- error_attribution_rate：100.00%
- security_event_counts：{"approval_denied": 3, "path_escape": 6, "read_only_block": 3}
- tool_error_code_counts：{"approval_denied": 6, "invalid_arguments": 18, "repeated_identical_call": 3}

跳过的场景：{"symlink_escape": 3}。跳过的场景不计入 block_rate，因为它没有证明任何事情。

## 可以安全写进简历的指标
- avg_full_prompt_chars
- avg_raw_prompt_chars
- avg_prompt_compression_ratio
- max_prompt_compression_ratio
- repeated_reads
- avg_tool_steps
- correct_rate
- resume_success_rate
- workspace_drift_detection_rate
- resume_false_accept_rate
- block_rate
- error_attribution_rate

## 只适合放文档/面试展开的指标
- current_request_preserved_rate
- memory_hit_rate
- stale_reanchor_rate
- failure_category_counts
- security_event_counts

## 口径边界
- Harness regression 只证明 runtime 合同稳定，不证明 provider 上限。
- Context、memory、recovery 这三层只证明模块收益，不和 provider benchmark 混写。
- Security suite 证明的是工具网关在这批已知攻击面上的拦截行为，不等于系统整体安全性。
