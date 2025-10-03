基于 CodonTransformer 做一个“生成→评估→强化学习”的闭环，并把“通用推理 + RL”思路（可类比 DeepSeek-R1 的 GRPO、多阶段训练与可验证奖励）落到分子生物学可验证指标上。
下面给出一套可以直接落地的端到端方案（含数据格式、奖励函数、训练流程与离线/在线评测），并标出关键工程细节与潜在坑点。
总览：Policy–Verifier–RL 三件套
- Policy（生成器）：以 CodonTransformer 为底座，做条件生成：输入(蛋白序列AA、宿主host、可选结构与上下文)，输出一批同义编码 DNA 候选。
- Verifier（评估器）：一组可验证且可微或可打分的模块，产出标量奖励。包含：
  1. 实验表达量代理模型（host-specific surrogate）
  2. 可验证的生化/合成约束（CAI/tAI、5′端ΔG、GC/禁忌位点、重复、codon pair bias 等）
  3. 不确定性与新颖性控制（防奖励投机）
- RL 优化器：借鉴 GRPO（group relative policy optimization）做多样采样+相对优势更新；参考 DeepSeek-R1 的“规则可验证奖励 +（必要时）模型奖励”与多阶段管线思路。 

---
1. 目标数据格式（训练与评估统一）
建议统一成 Parquet/JSONL，每行一条构建：
sequence_dna: "ATG..."
protein_aa: "M...."                  # 必填
host: "E_coli" | "S_cerevisiae" | "P_pastoris"  # 必填
expression:
  value: float                       # 原始单位
  unit: "RFU" | "mg_L" | "reads" | "a.u."
  assay: "bulk_fluor" | "FACS" | "WB" | "MS" | "RNAseq"
context:
  promoter: "lacUV5" | "AOX1" | ...
  5utr: "RBS_seq" | "Kozak"
  vector: "pET28a" | ...
  marker: "Kan" | ...
  conditions: {temp: 30, inducer: "IPTG", time_h: 16, media: "TB", ...}
  is_synthetic: true|false
meta:
  source_pub: "doi/URL"
  split: "train"|"dev"|"test"       # 预先分层抽样
规范化：针对不同实验单位，提供 expression_norm 字段（如 per-cell 或 per-OD、对照归一、log1p）。

---
2. 评估器（Verifier）设计 = 代理模型 + 规则与约束 + 不确定性
1.1 Host-specific 代理模型（Reward_surrogate）
- 目的：把真实实验表达量学习成 f_host(AA, DNA, context) → ẑ；RL 时作为主要奖励信号。
- 特征（按重要性优先）
序列局部：前 30–60 nt 的 one-hot、k-mer、codon identity、codon pair、dinuc（CpG/UpA）
结构：5′ 端窗口（-4~+45nt）mRNA ΔG（如 ViennaRNA 计算），回避强发卡
使用偏好：CAI/tAI、低频密码子率、%MinMax、CFD
全局：GC%（全局&滑窗）、长同聚物/重复、禁忌位点（限制性内切酶、真核剪接信号等）
上下文：启动子/RBS/载体/培养条件（one-hot）
蛋白属性（AA 序列派生）：长度、疏水性指数、信号肽/跨膜段、可溶性预测（如 protein-sol）、分泌 vs 细胞内
结构增强（可选）：AlphaFold/ESM/Evoformer 的 pLDDT、SASA、二级结构比例、跨膜拓扑等（用作协变量，不参与梯度）
- 模型：优先用树模型/NGBoost/LightGBM做强基线；再上Transformer/小型GNN融合序列与结构特征；多宿主Mixture-of-Experts头。
- 标定：用 isotonic/Platt 做输出标定，报告 Spearman ρ、R²、MAE。
1.2 规则性子奖励与硬约束（Reward_rules / Constraints）
这些指标可直接验证，适合做规则奖励（DeepSeek-R1 的“rule-based rewards”理念）：
- mRNA 5′ 结构：目标窗口 ΔG ≥ 阈值（越松散越好）；超阈奖励，低于阈值惩罚
- CAI/tAI：按宿主权重计算；超阈奖励、极端最大化给饱和上限（避免过拟合）
- GC% & 滑窗 GC：落区间奖励；越界惩罚（非线性）
- 低频/稀有密码子：连续稀有串惩罚；codon pair bias 惩罚
- 重复/同聚物/反向重复：长度超阈惩罚
- 禁忌位点：硬约束（置负无穷或重采样）
- 多样性/新颖性：与已知/训练集合的 Levenshtein/identity 相似度惩罚，鼓励同义多样化
1.3 不确定性与 OOD 保护（Reward_uncertainty）
- 代理模型输出 μ, σ，用 μ − λ·σ 作为奖励基线，抑制奖励投机（reward hacking）。
- 训练/RL 采样时启用 conformal 或 deep ensembles 提供区间，超出分布时降权。

---
3. 奖励整合（可直接实现）
对每个采样候选 (x_i)：
[
 R(x_i) ;=; w_1 \cdot \underbrace{\mathrm{scale}\big(f_{\text{host}}(x_i)\big)}{\text{代理表达量}}
 ;+; w_2 \cdot \underbrace{\Phi{\text{rules}}(x_i)}{\text{规则可验证}}
 ;-; w_3 \cdot \underbrace{\mathrm{Unc}(x_i)}{\text{不确定性惩罚}}
 ]
- scale(·)：对不同实验来源做 rank/quantile 归一，保障跨数据集可比性。
- Φ_rules：各子项归一化后加权和（带阈值与上限，避免“只堆 CAI”）。
- 可加 host-consistency 正则（候选密码子频谱与宿主参考分布的 KL 距离惩罚），类比 DeepSeek-R1 的语言一致性奖励想法。

---
4. 训练管线（对标 DeepSeek-R1 的多阶段思路）
目标是“先会写，再写好”：先让模型懂基本优化，再用可验证奖励做强化，最后微调稳态分布。DeepSeek-R1 采用了多阶段（RL + SFT/拒绝采样）的策略，我们也做类比改造。
Stage A｜监督暖启动（SFT）
- 数据：已有优化工具/文献里的“高表达”序列（含 host 标签）。
- 目标：最小化 NLL，学习host-conditional 的合理初分布；加入硬约束过滤器确保训练样本可合成。
Stage B｜离线对比学习/拒绝采样
- 从 Policy 采样 N 条候选，跑 Verifier 打分，保留前 p% 做SFT 重训练（拒采），类似 DeepSeek-R1 的rejection sampling 增强。
Stage C｜RL（GRPO/PPO-family）
- 每条输入（AA, host, context），Policy 一次采样 G 个候选；用 Verifier 产生 ({r_i}_{i=1..G})，计算组内标准化优势 A_i（与 GRPO 一致）。
- 目标：最大化期望奖励并用 KL 到参考策略 正则化（控制漂移），避免崩溃。
- 采样温度：先高后低；每若干步更新参考策略（与 R1 一致）。
- 混合奖励源：严格用规则可验证奖励为主，必要时再加模型奖励（代理模型），并配合不确定性惩罚，降低“奖励投机”。
Stage D｜稳定化与蒸馏（可选）
- 将 RL 后策略再做小步 SFT到离线高分集合上，或蒸馏到小模型供推理部署（降低采样成本）。

---
5. 条件输入与解码策略
- 条件化：
[#HOST=Ec] [#PROM=AOX1] [#SECRETE] [#LEN=xxx] <AA> ....
 通过离散控制 token统一注入宿主/上下文；可选把 AlphaFold/ESM 特征编码为连续前缀向量（adapter）。
- 解码：
Top-p/温度+约束搜索（禁忌位点、滑窗GC、5′ΔG 在线检查）；支持多样性解码（粒子群/多束）→ 每条输入产出 K 条多样候选，交给 Verifier 排序。

---
6. 评测与A/B实验
离线指标（dataset-level）
- 代理模型：Spearman ρ、R²（host 分层）；OOD split 测一致性。
- 可验证规则：违反率（GC/ΔG/禁忌位点/重复）、CAI/tAI 分布、序列多样性。
- 端到端打分：对比 Baseline（经典优化器/简单CAI最大化）与 Policy+RL 的 Verifier 总分。
体外/体内最小闭环（优先 E. coli & S. cerevisiae）
- 每宿主挑选 10–20 个蛋白，生成 3–5 条候选/蛋白，平行合成+同一载体与启动子，统一测定（FACS/plate）。
- 分析：RL 版本在中位数提升、Top-1 命中率、Top-k 命中率、**鲁棒性（不同生长条件）**上的优势。
- 统计：使用 paired test 与多重校正报告显著性。

---
7. 风险与对策（关键）
- 奖励投机（hacking）：极端提高 CAI/ΔG 但真实表达不升
 → 代理奖励和规则奖励分权重；μ−λσ 惩罚；对抗验证（训练一个“检测投机”判别器）。
- 分布外蛋白/上下文：新结构域、膜蛋白
 → 提前标定 OOD 检测；超出置信域降温/回退到规则优化。
- 跨宿主迁移：Ec→Sc/Pp 表现不稳
 → host-expert heads + 共享干路 + 宿主特异 Adapter；训练时分层采样平衡宿主。
- 5′ 端结构偏置过强
 → 引入翻译延伸速率 proxy（稀有分布/暂停热点）与多窗口ΔG，避免只看起始区。

---
8. 实施清单（工程可执行）
9. 数据层：整理成上面 schema，单位归一 & 分层 split；构建 host codon usage/tRNA 表与 ViennaRNA 批处理。
10. 代理模型：先上 LightGBM/NGBoost 基线（特征工程脚本），做标定与不确定性；产出 μ,σ。
11. 规则库：实现 CAI/tAI、ΔG、GC/滑窗、禁忌位点、重复、codon-pair；一键出可视化报告。
12. 训练：
  - SFT：host-conditional CodonTransformer（加约束过滤器）
  - 拒采：N→Top-p 反馈再 SFT
  - RL(GRPO)：每输入采样 G=8~16，组内标准化优势A_i，KL 到参考策略；每 N 步更新 ref。
13. 推理与打分：约束解码 + Verifier 排序；导出 top-K。
14. 评测：离线全指标 + 小规模体内验证方案。

---
15. 与 DeepSeek-R1 思路的对齐点
- 可验证奖励优先：我们把“正确性可自动判定”的规则奖励（ΔG/禁忌/GC/CAI/tAI 等）放在核心位置，和 R1 在可判定任务上用规则奖励一致。
- GRPO 组内相对优势：一次采样多条候选，用组内归一优势更新，简化价值网络，利于大规模 RL。 
- 多阶段流水线：SFT→拒绝采样→RL→（蒸馏/稳态化），对应 R1 的多阶段训练思想。

## Usage

Train surrogate: python -m codon_verifier.train_surrogate --data toy_dataset.jsonl --out ecoli_surrogate.pkl
Constrained demo: python -m codon_verifier.run_demo
GRPO scaffold: python -m codon_verifier.grpo_train --aa MAAAAAAA --groups 8 --steps 50
Offline eval: python -m codon_verifier.evaluate_offline --dna ATG...
Added ΔG, diversity, hard constraints; implemented constrained decoding, simple policy + GRPO scaffold, and offline evaluation; updated docs and requirements.