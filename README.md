# Streetview Analysis Pipeline

本地街景分析流程：中心点位筛选、道路侧向照片识别、人工验证，以及后续 VLM 评分与分析。

目前已实现并验证的是**数据筛选、标注、视觉分类和模型评估**。VLM 评分与结果分析为后续阶段，尚未实现；全量清洗也尚未执行。

## 当前任务与交付

每个点位有四张以 `经度_纬度_角度_附加字段.png` 命名的图片，角度为 0、90、180、270。只处理中心点位名单中的坐标，为每点位选择两张朝向道路两侧的照片。

角度不能直接解释为道路前后左右。模型比较 0/180 与 90/270 两对，人工界面允许选任意两张。`side_a`、`side_b` 只是两个引用名称，不表示实际左侧或右侧。

交付形式为**筛选清单与读取脚本**。图片保留在本地原始 ZIP 中，后续 VLM 可以按清单直接读取图像字节，不必重复打包传图。

## 结果概览

| 阶段 | 样本 | 方法 | 结果 |
|---|---|---|---|
| 初次试验 | 50 点位 | CLIP 零样本、相反方向配对 | 44/50 一致，88%；确定程度未系统记录 |
| 新样本验证 | 100 点位 | 固定 CLIP 零样本 | 确定组77/84，91.7%；勉强组8/16，50% |
| 分类器试验 | 上述84个确定点位 | 固定CLIP特征＋逻辑回归，按点位5折验证 | 折外预测81/84，96.4%；原方案77/84 |
| 独立留出验证 | 全新30点位，排除此前150点位及相同图片 | 冻结的84点位分类器 | 确定组24/25，96%；勉强组2/5，40% |

这里的一致率要求同点位两张均与人工选择匹配，忽略 a/b 顺序。勉强组的不一致不能直接视为确定的模型错误。小样本表现不代表全量准确率保证。

## 仓库结构

- `scripts/`：采样、数据检查、标注服务器、特征提取、训练、评估与读取脚本。
- `web/`：50、100、30点位三轮本地标注界面，无图片或标注数据。
- `docs/methodology.md`：方法、验证划分、交付字段与局限。
- `docs/iteration_log.md`：按实际发生顺序记录迭代，不伪造Git提交历史。
- `docs/roadmap.md`：全量清洗、复核和后续VLM分析计划。
- `results/aggregate_metrics.json`：不含逐点坐标的汇总结果。

现有实验脚本保留固定样本数及轮次目录，以便追溯。它们不是已经完成的通用批处理产品。

## 本地运行

测试环境为 Python 3.12、Apple M2 Pro、16GB统一内存，使用 PyTorch MPS。其他平台可使用CPU，依赖版本兼容性需要验证。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 指向你本地的私有工作目录与四个原始ZIP所在目录。
export STREETVIEW_WORKSPACE="$PWD/workspace"
export STREETVIEW_ARCHIVE_DIR="$STREETVIEW_WORKSPACE/raw"
python scripts/install_annotation_assets.py
python scripts/inspect_data.py --centers "$STREETVIEW_WORKSPACE/raw/中心点位.xls"

# 第一轮：生成样本，打开本地界面；先完成人工标注。
python scripts/prepare_sample.py
python scripts/annotation_server.py --port 8765 --open-browser
# 在另一个终端继承相同环境配置，完成标注后：
python scripts/evaluate_clip.py

# 第二轮：先预测，再标注，保持页面不显示模型答案。
python scripts/prepare_validation100.py
python scripts/predict_validation100.py
STREETVIEW_ANNOTATION_DIR="$STREETVIEW_WORKSPACE/annotation100" \
  python scripts/annotation_server.py --port 8768 --open-browser
# 完成标注后：
python scripts/compare_validation100.py
python scripts/train_lightweight.py

# 第三轮：分类器独立留出验证。
python scripts/prepare_validation30.py
python scripts/predict_validation30.py
STREETVIEW_ANNOTATION_DIR="$STREETVIEW_WORKSPACE/annotation30" \
  python scripts/annotation_server.py --port 8769 --open-browser
# 完成标注后：
python scripts/compare_validation30.py
```

首次CLIP运行需要下载官方权重。后续脚本使用缓存模型，推理在本地完成。新工作目录没有私有图像与标注时，不能直接复现研究指标。

最终读取示例：

```bash
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/annotation30/annotations.csv"
python scripts/read_selected.py "$STREETVIEW_WORKSPACE/annotation30/annotations.csv" --output "$STREETVIEW_WORKSPACE/selected_images"
```

读取脚本只处理 `status=confirmed` 的两张图；`needs_review` 记录仅为候选，需复核后用于正式分析。

## 数据边界

公开仓库只包含代码、方法、界面模板和汇总指标。原始图片、中心点位表、坐标清单、人工标注、逐点预测、图像特征、权重、生成报告及本地环境均不提交。

本仓库未赋予原始数据任何再分发许可。模型与依赖的使用遵循各自条款。
