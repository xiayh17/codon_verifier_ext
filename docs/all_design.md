## 总览（与当前代码一致）

本仓库已实现“生成 → 评估 → 强化学习（GRPO）”闭环原型，核心由以下模块组成：

- 策略 `HostConditionalCodonPolicy`：按宿主的逐氨基酸多项式策略，支持温度采样与参考策略正则（`codon_verifier/policy.py`）。
- 规则与约束 `metrics.rules_score`：GC/滑窗GC、CAI/tAI、5′结构代理与可选 ViennaRNA ΔG、禁忌位点、稀有密码子连串、同聚体、codon-pair、简单多样性等（`codon_verifier/metrics.py`）。
- 奖励整合 `reward.combine_reward`：R = w_sur·(μ − λσ) + w_rules·total_rules（`codon_verifier/reward.py`）。
- LM 特征 `lm_features.py`：默认基于宿主密码子使用的轻量替代；如启用 Evo 2，则切换为 nt-LM 打分（`codon_verifier/lm_features.py` + `codon_verifier/evo2_adapter.py`）。
- 代理模型 `surrogate.py`：量化回归基线（μ、σ≈q_hi−μ），含训练/推理与特征工程（`train_surrogate.py`、`surrogate_infer_demo.py`）。
- GRPO 训练脚本：组内标准化优势，按参考策略做正则的最小闭环训练脚本（`codon_verifier/grpo_train.py`）。
- 演示与离线评测：`run_demo.py`、`run_demo_features.py`、`evaluate_offline.py`。

可选与外部依赖：

- ViennaRNA RNAfold（可选）：用于 5′ ΔG 计算；缺失时退化为结构代理分。
- LightGBM（可选）：存在则使用 LGBM 的 quantile；否则退化为 sklearn GBR quantile。
- Evo 2（可选）：设置 `USE_EVO2_LM=1` 且满足本地包或 NIM 环境变量后，LM 特征改由 Evo 2 计算。

---

## 数据模式（JSONL）

与现有训练/推理脚本兼容的数据行示例：

```json
{
  "sequence": "ATG...",
  "protein_aa": "M...",
  "host": "E_coli",
  "expression": {"value": 123.4},
  "extra_features": {
    "plDDT_mean": 78.5,
    "length": 186,
    "lm_host_score": 0.82
  }
}
```

- 必填：`sequence`、`protein_aa`、`host`、`expression.value`。
- 可选：`extra_features`（可混入 `FeatureBundle.to_dict()` 与 `lm_features` 产出的 `lm_*` 指标）。

说明：`train_surrogate.py` 会读取上述字段构造特征；`surrogate_infer_demo.py` 与 RL 演示会复用相同特征定义，保持一致性。

---

## 奖励与规则（Verifier）

- 组合形式（已实现）：`R = w_surrogate·(μ − λ·σ) + w_rules·total_rules`。
- 规则集合（`metrics.rules_score` 已实现）：
  - GC 全局项与窗口化项；
  - CAI/tAI；
  - 5′ 结构代理分与可选 5′ ΔG（ViennaRNA，找不到则返回 NaN 并自动忽略该子项）；
  - 禁忌位点命中数（可设硬约束）与稀有密码子连串、同聚体长度；
  - codon-pair bias 分；
  - 简单多样性项（与参考集合的最小 identity 超阈惩罚，默认阈值 0.98）。
- 默认权重见 `metrics.rules_score(..., weights=...)`，可在调用处自定义。

---

## 语言模型特征（Evo 2 可选）

- 默认：基于宿主密码子使用频率得到 `lm_host_*` / `lm_cond_*`，键名与真实 LM 对齐。
- 切换到 Evo 2：设置环境变量 `USE_EVO2_LM=1`，并满足以下任一：
  - 本地安装 `evo2` 包（`evo2_adapter` 自动使用本地后端）。
  - 配置 NIM：设置 `NVCF_RUN_KEY` 与 `EVO2_NIM_URL`。
- `evo2_adapter` 会返回 `loglik/avg_loglik/perplexity/geom` 并映射为 `lm_*` 键，保持下游无感切换。

---

## GRPO 训练与策略更新（最小闭环）

- 脚本：
  - `python -m codon_verifier.grpo_train --aa AASEQ --steps 50 --groups 8 --temperature 1.0 --motif GAATTC --motif GGATCC --w_rules 1.0 --w_sur 1.0 --lambda_unc 1.0`
- 行为：每步对同一 `AA` 采样 G 条候选，计算组内标准化优势并更新策略；
- 备注：当前脚本内未直接载入代理模型，`surrogate_mu/sigma` 使用占位 0.0。若需联通代理，可在脚本中用 `surrogate.load_and_predict` 对批量候选补齐 μ、σ 后传给 `combine_reward`。

---

## 快速上手（Runbook）

- 规则评估（离线）：
  - `python -m codon_verifier.evaluate_offline --dna ATG... GCT... --motif GAATTC --motif GGATCC`
- Demo（合并特征与奖励）：
  - `python -m codon_verifier.run_demo`
  - `python -m codon_verifier.run_demo_features`
- 代理模型训练：
  - `python -m codon_verifier.train_surrogate --data toy_dataset.jsonl --out ecoli_surrogate.pkl`
- 代理模型推理：
  - `python -m codon_verifier.surrogate_infer_demo --model ecoli_surrogate.pkl --seq ATG...`
- GRPO 训练：
  - `python -m codon_verifier.grpo_train --aa MA... --steps 50 --groups 8`

可选依赖与环境：

- 使用 Evo 2：`USE_EVO2_LM=1`，并配置本地包或 `NVCF_RUN_KEY` + `EVO2_NIM_URL`。
- 使用 ViennaRNA ΔG：安装 Python `RNA` 或命令行 `RNAfold`（自动检测）。
- 使用 LightGBM：安装 `lightgbm`，否则将退化为 sklearn GBR。

---

## 风险与对策（实践提示）

- 奖励投机：提高 `λ` 抑制高不确定性样本；限制子项上限，避免“只堆 CAI/ΔG”。
- 分布外：当 LM/结构分偏离明显时降低温度或回退仅规则优化。
- 5′ 结构单一关注：结合 ΔG 与结构代理，多窗口观测并加入稀有节律平滑项。

---

## 模块与文件对照（速查）

- 策略：`codon_verifier/policy.py`
- 规则与指标：`codon_verifier/metrics.py`
- 奖励组合：`codon_verifier/reward.py`
- LM 特征与 Evo 2：`codon_verifier/lm_features.py`、`codon_verifier/evo2_adapter.py`
- 代理模型与训练/推理：`codon_verifier/surrogate.py`、`codon_verifier/train_surrogate.py`、`codon_verifier/surrogate_infer_demo.py`
- 训练与评估脚本：`codon_verifier/grpo_train.py`、`codon_verifier/evaluate_offline.py`、`codon_verifier/run_demo.py`、`codon_verifier/run_demo_features.py`

---

## 与 DeepSeek-R1 思路的对齐点

- 可验证奖励为先：以规则性指标为主，并以 μ−λσ 抑制不确定性带来的投机；
- 组内相对优势：一次采样多条候选，使用标准化优势更新，避免显式价值网络；
- 多阶段可扩展：虽然当前仓库未内置 SFT/拒采阶段，但接口设计与特征定义可直接承接后续扩展。
