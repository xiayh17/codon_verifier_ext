# Codon Verifier: Verifier + Surrogate + Simple GRPO Policy

## 文档速览

- [整改算法框架梳理文档](algorithm_rectification_framework.md)：以费曼式讲解串联目标澄清、现状诊断、风险识别、路线规划与闭环落地，配套多幅 Mermaid 思维导图帮助快速建立整体图景。

## 安装

```bash
PYTHON=$(command -v python3 || command -v python) && "$PYTHON" -m venv .venv && . .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -r /mnt/c/Users/xiayh17/Projects/codon_verifier_ext/requirements.txt
```

激活环境（在每次新 Shell 中执行）:

source /mnt/c/Users/xiayh17/Projects/codon_verifier_ext/.venv/bin/activate

验证环境与依赖: 

python -V
python -c "import numpy, sklearn, lightgbm, ViennaRNA; print('deps ok')"

退出虚拟环境:

deactivate

如需重新安装依赖:

source /mnt/c/Users/xiayh17/Projects/codon_verifier_ext/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r /mnt/c/Users/xiayh17/Projects/codon_verifier_ext/requirements.txt

变更依赖后更新锁定文件（可选）:

python -m pip freeze > /mnt/c/Users/xiayh17/Projects/codon_verifier_ext/requirements.txt

重要路径
项目路径: /mnt/c/Users/xiayh17/Projects/codon_verifier_ext
虚拟环境: /mnt/c/Users/xiayh17/Projects/codon_verifier_ext/.venv

- 核心依赖: numpy, scikit-learn, joblib
- 可选依赖: lightgbm（更强的代理模型）, ViennaRNA Python API（包名 `ViennaRNA`，导入 `RNA`）或安装命令行 `RNAfold`（ΔG 备选）

注意: 若以包方式运行示例，请确保项目目录名为 `codon_verifier`（避免空格）。或者将其父目录加入 `PYTHONPATH`。

## 数据格式 (JSONL)

每行一条：
{
  "sequence": "ATG...",
  "protein_aa": "M...",
  "host": "E_coli",
  "expression": {"value": 123.4, "unit": "RFU", "assay": "bulk_fluor"},
  "extra_features": {"plDDT_mean": 83.1, "msa_depth": 120, "conservation_mean": 0.42}
}

训练（代理模型 Surrogate）

```bash
python -m codon_verifier.train_surrogate --data toy_dataset.jsonl --out ecoli_surrogate.pkl
```

推理

```bash
python -m codon_verifier.surrogate_infer_demo --model ecoli_surrogate.pkl --seq ATGGCTGCTGCT
```

与 Verifier 融合

```python
from codon_verifier.reward import combine_reward
from codon_verifier.hosts.tables import E_COLI_USAGE, E_COLI_TRNA
from codon_verifier.surrogate import load_and_predict

dna = "ATG" + "GCT"*20
pred = load_and_predict("ecoli_surrogate.pkl", [dna], usage=E_COLI_USAGE, trna_w=E_COLI_TRNA)[0]

res = combine_reward(
    dna=dna, usage=E_COLI_USAGE,
    surrogate_mu=pred["mu"], surrogate_sigma=pred["sigma"],
    trna_w=E_COLI_TRNA, motifs=["GAATTC","GGATCC"], extra_features=None
)
print(res)
```

```bash
python -m codon_verifier.run_demo
python -m codon_verifier.run_demo_features
```

新增：

1) 约束解码（在线禁止位点）与演示

```bash
python -m codon_verifier.run_demo
```

`run_demo.py` 现在使用约束解码从 AA 序列生成 DNA，并应用硬约束过滤（如 EcoRI/BamHI）。

2) GRPO 风格训练脚本（简化版 Policy 学习）

```bash
python -m codon_verifier.grpo_train --aa MAAAAAAA --groups 8 --steps 50 --temperature 1.0 \
  --w_rules 1.0 --w_sur 0.0 --lambda_unc 1.0 --host E_coli
```

- Policy: `HostConditionalCodonPolicy`（按宿主、按 AA 的类多项式策略），支持对参考策略的 L2 正则（近似 KL）。
- Verifier: 使用规则分数（CAI/tAI、GC、5′ 区域结构、禁忌位点、重复、codon-pair）+ 可选 ΔG 项和多样性惩罚。
- 代理模型：脚本里占位（μ,σ=0），可通过 `surrogate.load_and_predict` 接入真实代理并作为奖励项。

3) 离线评测汇总

```bash
python -m codon_verifier.evaluate_offline --dna ATG... ATG... --motif GAATTC --motif GGATCC
```

- 输出每条序列的规则项细分与总分，并汇总违规率/平均 CAI/GC。
- 若安装了 ViennaRNA（Python 或 CLI），将报告 5′ ΔG 与对应奖励项。

---

## toy_dataset.jsonl (内容示例)

```json
{"sequence":"ATGGCTGCTGCTGCTGCTGCT","protein_aa":"MAAAAAAA","host":"E_coli","expression":{"value":100.0,"unit":"RFU","assay":"toy"},"extra_features":{"plDDT_mean":85.0,"msa_depth":50,"conservation_mean":0.3}}
{"sequence":"ATGGCCGCCGCCGCCGCCGCC","protein_aa":"MAAAAAAA","host":"E_coli","expression":{"value":150.0,"unit":"RFU","assay":"toy"},"extra_features":{"plDDT_mean":90.0,"msa_depth":80,"conservation_mean":0.5}}
{"sequence":"ATGGCGGCGGCGGCGGCGGCG","protein_aa":"MAAAAAAA","host":"E_coli","expression":{"value":200.0,"unit":"RFU","assay":"toy"},"extra_features":{"plDDT_mean":70.0,"msa_depth":30,"conservation_mean":0.2}}
```

---

## 设计要点对齐

- Verifier：实现 CAI/tAI、GC/滑窗 GC、5′ 结构代理、ΔG（ViennaRNA）、禁忌位点、重复、codon-pair、多样性惩罚；支持硬约束（命中禁忌则置 `-inf`）。
- Surrogate：量化回归（中位数 μ 和上分位 q_hi 估计 σ），可接入特征工程（AA 物化、结构/进化特征）。
- RL 管线：提供 GRPO 风格多样采样与相对优势更新的脚手架（简化政策、参考策略正则，便于扩展至 Transformer）。

ΔG 说明：
- 若安装 Python `ViennaRNA`（`import RNA`），优先使用其 API；否则尝试 `RNAfold --noPS`；若均不可用，将回退到启发式 5′ 结构代理。
