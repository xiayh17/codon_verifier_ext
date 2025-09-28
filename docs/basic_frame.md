- codon_verifier/metrics.py
  - CAI（基于宿主密码子使用频率）
  - tAI（近似版）（基于提供的 tRNA “权重”/拷贝数，家族内max归一）
  - GC 全局 & 滑窗 GC
  - 同聚物/串联重复 检测
  - 稀有密码子连续片段（以家族相对适应度分位数判定）
  - 禁忌位点扫描（如限制性内切酶）
  - 密码子对偏好分（提供表则算，否则返回0）
  - 5′ 起始区“结构代理”（RNAfold 不可用时的简易替代；上线后可换真ΔG）
- codon_verifier/reward.py
  - 将 代理表达模型输出（μ, σ）、规则可验证分 合成总奖励：
R = w_surrogate * (μ − λ·σ) + w_rules * total_rules
- codon_verifier/codon_utils.py
  - 标准遗传密码、CDS校验、家族相对适应度计算等工具
- codon_verifier/hosts/tables.py
  - E. coli 的一个用于演示的玩具密码子使用表与 tRNA 权重（请替换为真实表）
- codon_verifier/run_demo.py
  - 一键演示如何对一条 DNA 序列打分（含禁忌位点例子）
快速上手
1. 解压后，在同级目录运行：
python -m codon_verifier.run_demo
你会看到每个子指标与 reward 总分的打印输出。
2. 在你自己的流程里：
from codon_verifier.reward import combine_reward

res = combine_reward(
    dna=<你的CDS，无终止子>,
    usage=<宿主codon使用表: dict[codon]->freq>,
    surrogate_mu=<代理模型预测平均>,
    surrogate_sigma=<预测不确定性>,
    trna_w=<宿主tRNA权重: dict[codon]->weight，可选>,
    cpb=<密码子对表，可选>,
    motifs=["GAATTC","GGATCC",...],  # 禁忌位点
    w_surrogate=1.0, w_rules=1.0, lambda_uncertainty=1.0
)
如何替换成“真实世界”配置
- CAI 使用表：将宿主的密码子使用频率（建议来自宿主高表达基因集的 RSCU/频率）填到 usage 中。若来源是 RSCU，先转为“家族内频率”（脚本里 relative_adaptiveness_from_usage 会再做 w_i 计算）。
- tAI 权重：可用 tRNA 基因拷贝数/富集度构建，并考虑 wobble/选择效率（目前提供近似家族归一，也可把已经处理好的 tAI 权重直接传入）。
- 5′ 结构能 ΔG：上线时，可将 five_prime_structure_proxy 替换为对 ViennaRNA RNAfold 的调用，把真实 ΔG（例如 ATG 下游 45 nt 的最小自由能）作为规则分的一部分。
- 密码子对偏好 (CPB)：若你有宿主 codon-pair bias 表（如 AAA-CCC -> score），传入即可计分。
- 禁忌位点：把所有不希望出现的酶切位点、真核潜在剪切信号、重复元件“序列”列入 motifs 列表即可。
与RL的对接（接口对齐）
- 组内采样 G 条候选后，对每一条 dna_i：
  1. 代理模型 → 得 μ_i, σ_i
  2. combine_reward(dna_i, usage, μ_i, σ_i, ...) → 得 reward_i
- 用 GRPO/PPO 做“组内相对优势”更新（这部分在现有 RL 管线里接即可；这边留出干净的 reward 接口）。