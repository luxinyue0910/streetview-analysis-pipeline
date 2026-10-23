# 后续阶段

## Current status: selected scoring method, full run not started

The selected method is Flash with prompt v2 + frozen DINOv2 + a supervised
regression/probability mixture. Deliver one-decimal scores and retain continuous
scores. The [method report](scoring_method_2026-10-23.md) and
[experiment history](scoring_iterations_2026-10-23.md) supersede the historical
plans below. The 200-point test has been evaluated; the 500-point validation set
has not been used. The user explicitly deferred full-dataset scoring.

Next, only when authorized: prepare resumable batch execution with the frozen
components, check image/reference mapping, preserve both score precisions and
raw-response provenance, and handle missing images or failed calls explicitly.
Do not retune on the evaluated 200-point test or report training-point fitted
scores as generalization evidence. Safety remains the main quality limitation.

## Historical October 20 plan: VLM scoring pilots

Two local Qwen scoring experiments are complete and summarized in the
[pilot report](vlm_pilot_2026-10-20.md). Versioned prompt fragments and aggregate
results are published. Production batch scoring remains unimplemented. Next:
evaluate compact prompts on a larger fixed training-only sample with Qwen3.8
Flash and Qwen3-VL Plus, review evidence/anchor and visibility errors, then run
the untouched validation set. Historical planning text below predates these
pilots; no full-dataset VLM scoring result is claimed.

The [v2 trial](vlm_organized_pilot_2026-10-20.md) did not show a consistent gain
after PDF rule grouping. Before further tuning, measure output variability and
diagnose visual facts separately from rubric-to-score mapping. No v3 experiment
has been run or validated yet.

## 全量中心数据初筛

全量入口 `scripts/select_full_dataset.py` 已实现：处理13,660个中心点位的54,640张图片，每点位选出两张。沿用已验证的冻结分类器，批量读取原ZIP，SQLite保存进度，支持断点续跑与重复图片评分缓存。

输出清单应保留模型版本、分数、复核状态和人工覆盖来源。确定的人工作答优先于模型选择。勉强标注与已知错误不能自动当成正式确认结果。

## 复核与验收

用分差、方法间不一致等信号排序疑难点位，另做随机抽查以发现大分差错误。当前使用分类器分差小于0.3作为初始复核规则，另将与零样本选择不同的点位纳入复核。该阈值仅为工作队列启发式，不宣称任何自动通过区间已获质量保证。

验收包括：每个中心点位有两个可读取的图片引用、方向选择与人工复核可追溯、缺图或异常显式记录。原始数据不修改。最终交付为清单＋读取脚本，无需重新上传图片。

## VLM评分与分析

先定义评分维度、评分尺度、缺失与异常规则，以及是否需要区分实际道路左右。side_a/b可分别评分，但并不自带真实左右语义。

计划加入评分任务配置、模型版本与提示词记录、断点续跑、结果缓存和质量抽查。图像由清单读取；评分完成后按点位或道路等级汇总，并单独分析勉强视角。具体VLM尚未选定，评分代码尚未实现。
