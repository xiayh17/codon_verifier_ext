# 整体算法框架（面向审议）

本文面向“从代码出发”的可行性审议，概述本仓库当前可运行的端到端算法框架：数据模式、模块映射、训练/评估流程、奖励定义与风险对策，并提供可直接执行的 Runbook。

## 1. 问题与目标

- **输入**：蛋白序列 `AA` 与宿主 `host`。
- **输出**：满足生化/合成约束且对目标宿主更优的同义编码 DNA 序列。
- **优化目标（奖励）**：综合“可验证规则分数”与“实验表达量代理（含不确定性惩罚）”。

## 2. 系统总览（与代码映射）

- **策略（Policy）**：按宿主、按氨基酸的类多项式策略，支持温度采样与参考策略正则。
  - 代码：`codon_verifier/policy.py` 中 `HostConditionalCodonPolicy`
- **验证器（Verifier/Rules）**：可验证的规则打分与硬约束（禁忌位点、GC、CAI/tAI、5′结构、重复、codon-pair、多样性等）。
  - 代码：`codon_verifier/metrics.py`（核心规则）
  - 奖励整合：`codon_verifier/reward.py` 的 `combine_reward`
- **语言模型特征（LM features）**：在未接入外部核酸 LM 时，使用基于宿主密码子使用表的轻量替代特征，提供 `lm_host_*` 与 `lm_cond_*` 指标。
  - 代码：`codon_verifier/lm_features.py`
- **代理模型（Surrogate）**：量化回归（中位数 μ 与上分位 hi，σ≈hi−μ），输出表达量的点估计与不确定性。
  - 代码：`codon_verifier/surrogate.py`
  - 训练脚本：`codon_verifier/train_surrogate.py`
  - 推理示例：`codon_verifier/surrogate_infer_demo.py`
- **训练脚手架（GRPO 风格）**：组内相对优势更新，定期刷新参考策略，演示端到端 RL 优化流程。
  - 代码：`codon_verifier/grpo_train.py`
- **离线评测**：批量计算规则分数，输出 JSON 摘要。
  - 代码：`codon_verifier/evaluate_offline.py`
- **示例与约束解码**：从 AA 到 DNA 的在线约束解码演示（禁忌位点实时过滤）。
  - 代码：`codon_verifier/run_demo.py`、`codon_verifier/codon_utils.py`
- **宿主表**：E. coli 的密码子使用率与 tRNA 权重示例。
  - 代码：`codon_verifier/hosts/tables.py`

## 3. 数据模式（JSONL）

每行一个样本：

```json
{"sequence":"ATG...","protein_aa":"M...","host":"E_coli","expression":{"value":123.4,"unit":"RFU","assay":"bulk_fluor"},"extra_features":{"plDDT_mean":83.1,"msa_depth":120,"conservation_mean":0.42}}
```

说明：`sequence` 为 DNA（不含终止密码子）；`protein_aa` 必填；`host` 当前示例为 `E_coli`；`extra_features` 可包含结构/进化协变量（在 `metrics.py` 与 `surrogate.py` 中参与计算）。

## 4. 奖励定义（与硬约束）

在 `reward.combine_reward` 中：

- 公式：`R = w_surrogate * (μ − λ·σ) + w_rules * total_rules`。
- `total_rules` 来自 `metrics.rules_score`，聚合：
  - `CAI/tAI`、整体 `GC` 与滑窗 GC、5′ 结构代理、可选 5′ ΔG（ViennaRNA）、禁忌位点、稀有密码子串、同聚物、codon-pair、多样性项、LM 特征项、结构/进化特征项。
- 硬约束：若启用 `enforce_hard_constraints=True` 且命中禁忌位点，直接置 `reward = -inf`（过滤候选）。

### 4.1 公式直觉（简明版）

- `μ (mu)`：代理模型对表达量的“中位数”估计，理解为“保守的好坏分”。
- `σ (sigma)`：不确定性，越大表示模型越拿不准。用 `μ − λ·σ` 惩罚高不确定样本，防“奖励投机”。
- `λ (lambda)`：不确定性惩罚系数，越大越保守。
- `w_surrogate` / `w_rules`：两大项的权重。前者偏向“学到的经验”，后者偏向“可验证规则”。
- `total_rules`：各规则子项（CAI/tAI、GC、结构、禁忌位点等）归一化后加权求和。
- `weights`（规则子项权重）：平衡不同规则的重要性，避免“只堆某一项”。
- `enforce_hard_constraints`：硬约束开关。命中禁忌位点等直接判非法，不参与比较。
- `lm_host_term / lm_cond_term`：基于宿主/条件的 LM 简易得分，近似“语言合理度”。
- `dG_term / struct5_proxy`：5′ 端结构相关项，鼓励更易翻译启动的 mRNA 构象。

与训练相关的两个直觉：

- `temperature`（采样温度）：越高越探索，越低越专注高概率密码子。
- 组相对优势（GRPO）：把同一轮生成的一组候选的奖励做组内标准化得到 `A_i`，仅让“超出组内平均”的样本推动策略，避免额外的价值网络。

## 5. 端到端流程（对标代码）

1) 特征准备（可选）
- `features.assemble_feature_bundle(aa)` 生成结构/进化特征，作为 `extra_features` 供规则/代理使用。

2) 代理模型训练/推理
- 训练：`python -m codon_verifier.train_surrogate --data toy_dataset.jsonl --out ecoli_surrogate.pkl`
- 推理：`python -m codon_verifier.surrogate_infer_demo --model ecoli_surrogate.pkl --seq ATG...`
- 代码：`surrogate.SurrogateModel` 量化回归（LightGBM 优先，回退 sklearn），`load_and_predict` 输出 `μ, σ`。

3) 策略采样与约束解码
- `policy.HostConditionalCodonPolicy.sample_sequence(...)` 或 `codon_utils.constrained_decode(...)`，支持禁忌位点在线过滤与温度采样。

4) 奖励计算
- `reward.combine_reward(...)` 聚合代理项与规则项，执行硬约束过滤。

5) GRPO 风格更新
- `grpo_train.py`：
  - 组采样 `G` 个候选，计算组内标准化优势 `A_i`；
  - `policy.update_from_samples(...)` 对所选密码子做 per-token logit 更新，并加上参考策略 L2 正则（KL 近似）；
  - 每 `k` 步刷新参考策略以稳定训练。
- 目前脚本中 `μ, σ` 以占位值示意；若要启用真实代理，只需在采样后调用 `surrogate.load_and_predict` 并将返回值传入 `combine_reward`。

6) 离线评测
- `python -m codon_verifier.evaluate_offline --dna ATG... ATG... --motif GAATTC --motif GGATCC`
- 输出每条序列的各子项分数、违规统计与集合摘要（平均 CAI/GC、违规率等）。

## 6. 可行性评估

- **可执行性**：
  - 规则打分与硬约束、约束解码、离线评测、代理训练/推理均已实现并可运行；
  - GRPO 脚手架具备端到端流程与参考正则，便于替换为更强策略（如 Transformer）。
- **依赖**：
  - 必需：`numpy`、`scikit-learn`、`joblib`；
  - 可选：`lightgbm`（更强代理）；`ViennaRNA` Python 包或 CLI `RNAfold`（5′ ΔG）；
  - 未接入但兼容：外部核酸语言模型（替换 `lm_features.py`）。
- **数据需求**：
  - 代理训练需要包含 `expression.value` 的数据；单位来源可在训练前做归一化/分层处理；
  - 规则与 RL 演示不依赖真实表达量（但可接入代理增强一致性）。

## 7. 风险与对策

- **代理外推风险（OOD）**：`μ − λσ` 抑制不确定样本；建议引入分位数/保序分布估计或一致性检查。
- **规则投机（CAI 堆叠）**：规则项已做多目标与上限；建议对 `weights` 做网格/贝叶斯优化并监控多样性项。
- **RL 不稳定**：已加入参考策略正则与周期性刷新；建议增大组大小、启用温度退火与学习率调度。
- **ΔG 依赖不可用**：自动回退到结构代理项；不影响主流程可运行性。
- **数据泄露/偏差**：对 `expression` 做分层抽样与交叉验证；记录数据来源与单位转换规则。

## 8. Runbook（可直接执行）

1) 安装依赖（如无 GPU 要求，可仅装必需项）

```bash
python -m pip install -r requirements.txt
```

2) 训练代理（示例数据）

```bash
python -m codon_verifier.train_surrogate --data toy_dataset.jsonl --out ecoli_surrogate.pkl
```

3) 约束解码 + 奖励演示

```bash
python -m codon_verifier.run_demo
```

4) GRPO 脚手架（仅规则奖励；若接入代理，将 `--w_sur` 调整 > 0）

```bash
python -m codon_verifier.grpo_train --aa MAAAAAAA --groups 8 --steps 50 \
  --temperature 1.0 --w_rules 1.0 --w_sur 0.0 --lambda_unc 1.0 --host E_coli
```

5) 离线评测

```bash
python -m codon_verifier.evaluate_offline --dna ATGGCTGCTGCT --motif GAATTC --motif GGATCC
```

（可选）在 GRPO 中接入代理：在采样得到 `dna` 后调用 `surrogate.load_and_predict` 获取 `μ, σ` 并传入 `combine_reward`。

## 9. 审议要点清单

- **目标**：是否明确“更优表达且可合成”的二元目标？权重与阈值是否合理？
- **规则集**：子项是否覆盖业务约束；硬约束与软惩罚的取舍是否合适？
- **代理**：特征是否充分；评估指标（R²/MAE/不确定性）是否达标；是否存在分布外风险？
- **训练**：采样规模、温度、参考正则与刷新频率设置是否稳定？
- **评测**：离线指标与线上指标是否一致；是否提供回溯与对比工具？

— 以上内容均与当前代码实现一一对应，可在不改动架构的前提下逐步增强（接入更强策略或语言模型、扩展宿主、细化规则与代理）。
