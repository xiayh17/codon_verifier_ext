- 加上 ViennaRNA ΔG 调用封装（可选 CUDA 并行批量跑）
- 提供 S. cerevisiae / P. pastoris 的示例 usage/tRNA 表模板
- 接入 codon-pair bias 的公开表（若有合适来源）
- 一个简易的 LightGBM 代理模型骨架（读你整理的文献数据表 → 训练 → 产出 μ, σ）
把 AlphaFold / ESM / Evo 特征接口与缓存规范补上并整合进打分器了，同时加入一个示例脚本演示如何把这些特征接入奖励函数。
- 新增模块：
  - codon_verifier/features.py
    - assemble_feature_bundle(aa, alphafold_pdb=None, esm_npz=None, evo_json=None, extras_json=None)：可从
      - AlphaFold PDB（从B-factor列解析 pLDDT 的均值与最小值），
      - ESM/ProtTrans 的 .npz（取全序列均值向量维度与L2范数），
      - Evo 的 .json（如 msa_depth, conservation_mean），
      - 以及任意 extras.json
  组装一个 FeatureBundle。
    - FeatureBundle.to_dict() 会转为纯 dict，用于规则打分器。
    - 还内置了基于 Kyte–Doolittle 的平均疏水性与长度特征。
  - codon_verifier/cache.py
    - 提供按 (AA序列 + 宿主) 的哈希缓存：save_features / load_features，默认目录 /mnt/data/codon_feature_cache（可用环境变量 CODON_VERIFIER_CACHE 改）。
  - codon_verifier/lm_features.py
    - combined_lm_features / score_nt_lm：封装宿主特异 nt-LM（默认回退为基于密码子使用频率的简易模型），输出 loglik、perplexity、归一化得分等字段，方便直接替换为 Evo2 真正的语言模型。
- 规则打分整合：
  - metrics.py 新增 extra_feature_terms(extra: dict)，将 plDDT_mean、msa_depth、conservation_mean、kd_hydropathy_mean 等压到 [0,1] 后合成 feat_struct_term。
  - rules_score(...) 现支持 lm_features / extra_features 参数：lm_features 可承接 Evo2（或本地近似）的 loglik / perplexity / 归一化分数，权重字典新增 lm_host 与 lm_cond，默认强调宿主兼容性与条件一致性。
- 奖励函数透传：
  - reward.combine_reward(...) 支持 lm_features 与 extra_features，自动合并后传给 rules_score，并把原始 LM 明细写入输出，便于代理模型训练与诊断。
- 新增演示脚本：
  - codon_verifier/run_demo_features.py：演示如何组装 FeatureBundle → 缓存 → 加入 combine_reward 的 extra_features 字段。
已经重新打包好：
下载 codon_verifier_with_features.zip
用法速记
from codon_verifier.features import assemble_feature_bundle
from codon_verifier.cache import save_features, load_features
from codon_verifier.reward import combine_reward
from codon_verifier.lm_features import combined_lm_features

# 1) 组装特征（文件路径可选，缺省就只算AA派生的长度/疏水性）
fb = assemble_feature_bundle(
    aa=protein_aa,
    alphafold_pdb="path/to/alphafold_model.pdb",  # 可选
    esm_npz="path/to/esm_embedding.npz",          # 可选（键为 'emb' 或 'mean'）
    evo_json="path/to/evo_stats.json",            # 可选（包含 msa_depth/conservation_mean）
    extras_json="path/to/extras.json"             # 可选（任意额外标量）
)
feat_dict = fb.to_dict()
save_features(protein_aa, host="E_coli", feats=feat_dict)  # 按需缓存

# 2) 奖励计算时合并语言模型特征
lm_feats = combined_lm_features(cds_dna, aa=protein_aa, host="E_coli")
extra = dict(feat_dict)
extra.update(lm_feats)
res = combine_reward(
    dna=cds_dna,
    usage=HOST_USAGE,
    surrogate_mu=mu, surrogate_sigma=sigma,
    trna_w=HOST_TRNA, cpb=HOST_CPB, motifs=FORBIDDEN_SITES,
    lm_features=lm_feats,
    extra_features=extra,      # 或 load_features(...) 后再补充 LM 特征
    w_surrogate=1.0, w_rules=1.0, lambda_uncertainty=1.0
)
说明与后续可拓展
- AlphaFold：当前从PDB的 B-factor 解析 pLDDT（AlphaFold标准输出），若你直接有 .json 也可以用 extras_json 传值。
- ESM/ProtTrans：示例读取 .npz，默认找 mean 向量或对 emb 做序列均值；也可改成 .pt 自定义加载。
- Evo（MSA/保守性）：evo_json 读取键值；你生成好数值（如以 PSI-BLAST / JackHMMER / MMseqs2 求 MSA 深度与位点保守性后取均值）。
- 特征→打分：目前把结构/进化特征只作为辅助正则（feat_struct_term），不直接参与可微/可验证路径。建议在代理模型里把这些特征作为协变量学习 μ, σ，从而通过 (μ − λσ) 主导奖励。
- 阈值/权重：metrics.rules_score 的 weights 可自定义（例如提高 5′ 结构项或下调 feat_struct 的影响）。
- ViennaRNA ΔG：随时可以把 five_prime_structure_proxy 替换为真实 ΔG，或在 extras_json 里加入 dg_5prime，然后在 extra_feature_terms 中纳入该项。

把 LightGBM 风格的代理模型骨架读 parquet/JSONL → 特征工程 → 训练 → 输出 μ,σ）接入包里并更新压缩包，训练→预测→与 Verifier 的 combine_reward 无缝衔接
新增内容
- codon_verifier/surrogate.py
  - SurrogateModel：双模型量化回归（mu=中位数，hi=上分位），sigma ≈ hi − mu
    - 若检测到 LightGBM：用 LGBMRegressor(objective='quantile', alpha=...)
    - 否则回退 **sklearn.GradientBoostingRegressor(loss='quantile')`
  - build_feature_vector(...)：从 DNA + extra_features 抽取特征（CAI/tAI、GC、滑窗GC统计、5′结构代理、稀有密码子连串、同聚物长度、codon直方图61维、结构/进化协变量等）
  - train_and_save(...)、load_and_predict(...)：端到端训练/推理API
- 训练与推理脚本：
  - codon_verifier/train_surrogate.py（JSONL → 训练 → .pkl）
  - codon_verifier/surrogate_infer_demo.py（加载 .pkl → 对若干 CDS 输出 μ, σ）
快速使用
1. 准备 JSONL（每行一条）
{"sequence":"ATG...","protein_aa":"M...","host":"E_coli",
 "expression":{"value":123.4,"unit":"RFU","assay":"bulk_fluor"},
 "extra_features":{"plDDT_mean":83.1,"msa_depth":120,"conservation_mean":0.42}}
2. 训练
python -m codon_verifier.train_surrogate --data your_dataset.jsonl --out ecoli_surrogate.pkl
输出包括 r2_mu, mae_mu, sigma_mean, n_samples 等训练指标。
3. 推理
python -m codon_verifier.surrogate_infer_demo --model ecoli_surrogate.pkl --seq ATG... ATG...
得到：
[{"mu": 0.73, "sigma": 0.08}, {"mu": 0.65, "sigma": 0.10}]
4. 与 Verifier 接口打通
训练好后，将 μ, σ 传给奖励函数：
from codon_verifier.reward import combine_reward
from codon_verifier.hosts.tables import E_COLI_USAGE, E_COLI_TRNA
from codon_verifier.surrogate import load_and_predict

pred = load_and_predict("ecoli_surrogate.pkl", [dna], usage=E_COLI_USAGE, trna_w=E_COLI_TRNA)[0]
res = combine_reward(
    dna=dna, usage=E_COLI_USAGE,
    surrogate_mu=pred["mu"], surrogate_sigma=pred["sigma"],
    trna_w=E_COLI_TRNA, motifs=["GAATTC","GGATCC"], extra_features=extra_dict,
    w_surrogate=1.0, w_rules=1.0, lambda_uncertainty=1.0
)
备注
- LightGBM 非必需；若你的环境未装，会自动使用 sklearn 的量化Boosting回归达成等价功能。
- 特征集是模块化的；若要加入 ViennaRNA ΔG、codon-pair bias 表、或更多蛋白协变量，只需在 build_feature_vector 中添加并重训即可。
- 若你的 JSONL 单位不一致，建议在数据准备阶段统一或另加 expression_norm 字段。
