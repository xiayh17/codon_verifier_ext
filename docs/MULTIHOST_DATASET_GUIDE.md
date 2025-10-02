# 多宿主数据集使用指南

> 本指南介绍如何使用新的多宿主UniProt数据集进行密码子优化训练

## 📚 数据集概述

### 数据来源

数据集包含52,158条蛋白质序列，来自5个不同的生物体：

| 文件 | 生物体 | 记录数 | 宿主标识 |
|------|--------|--------|----------|
| `Ec.tsv` | 大肠杆菌 (E. coli) | 18,780 | `E_coli` |
| `Human.tsv` | 人类 | 13,421 | `Human` |
| `mouse.tsv` | 小鼠 | 13,253 | `Mouse` |
| `Sac.tsv` | 酿酒酵母 | 6,384 | `S_cerevisiae` |
| `Pic.tsv` | 毕赤酵母 | 320 | `P_pastoris` |

### 数据字段

每条记录包含以下信息：

- **Entry**: UniProt ID
- **Reviewed**: 是否经过审阅（SwissProt）
- **Protein names**: 蛋白质名称
- **Gene Names**: 基因名称
- **Organism**: 来源生物体
- **Length**: 序列长度
- **Subcellular location**: 亚细胞定位
- **RefSeq_nn**: 核酸序列（CDS）
- **RefSeq_aa**: 蛋白质序列

## 🚀 快速开始

### 1. 数据转换

将TSV格式转换为框架使用的JSONL格式：

```bash
# 转换单个文件
python -m codon_verifier.data_converter \
  --input data/dataset/Ec.tsv \
  --output data/converted/Ec.jsonl

# 批量转换整个目录
python -m codon_verifier.data_converter \
  --input data/dataset/ \
  --output data/converted/ \
  --merge  # 合并为单个文件

# 只使用审阅过的条目（推荐）
python -m codon_verifier.data_converter \
  --input data/dataset/ \
  --output data/converted/ \
  --filter-reviewed \
  --max-records 10000
```

**转换选项：**

- `--filter-reviewed`: 只包含SwissProt审阅的高质量数据
- `--max-records`: 限制每个文件的记录数
- `--merge`: 将所有文件合并为一个

### 2. 训练统一模型

训练一个跨所有宿主的统一模型：

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/unified_multihost.pkl \
  --mode unified \
  --balance-hosts \
  --max-samples 5000
```

**训练选项：**

- `--mode unified`: 统一模型（推荐用于跨宿主迁移）
- `--balance-hosts`: 平衡各宿主的样本数
- `--hosts E_coli Human`: 只使用指定宿主
- `--reviewed-only`: 只使用审阅过的数据

### 3. 训练宿主特定模型

为每个宿主训练独立的模型：

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/host_specific/ \
  --mode host-specific \
  --hosts E_coli Human Mouse
```

### 4. 使用模型进行优化

```bash
# 使用统一模型
python -m codon_verifier.generate_demo \
  --aa MAAAAAAAAAA \
  --host E_coli \
  --surrogate models/unified_multihost.pkl \
  --n 500 \
  --top 100

# 使用宿主特定模型
python -m codon_verifier.generate_demo \
  --aa MAAAAAAAAAA \
  --host Human \
  --surrogate models/host_specific/Human_surrogate.pkl \
  --n 500 \
  --top 100
```

## 📊 数据策略优化

### 策略1: 宿主平衡采样

确保各宿主的样本数均衡，避免大肠杆菌数据过多导致的偏差：

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/*.jsonl \
  --out models/balanced.pkl \
  --mode unified \
  --balance-hosts \
  --max-per-host 2000
```

**优势：**
- 防止数据不平衡
- 提高跨宿主泛化能力
- 适合迁移学习

### 策略2: 高质量数据筛选

只使用审阅过的、序列长度适中的高质量数据：

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/high_quality.pkl \
  --mode unified \
  --reviewed-only \
  --min-length 100 \
  --max-length 2000
```

**优势：**
- 数据质量高
- 减少噪声
- 训练更稳定

### 策略3: 宿主特定 + 迁移学习

先训练统一模型，再针对特定宿主微调：

```bash
# 1. 训练统一模型（使用所有数据）
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/unified_base.pkl \
  --mode unified \
  --max-samples 10000

# 2. 针对特定宿主精调（使用宿主特定数据）
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/Human.jsonl \
  --out models/human_finetuned.pkl \
  --mode unified \
  --hosts Human
```

**优势：**
- 利用跨宿主知识
- 针对目标宿主优化
- 数据利用率高

### 策略4: 混合专家模型

训练多个宿主特定模型，根据目标宿主选择：

```python
from codon_verifier.train_surrogate_multihost import train_host_specific_models
from codon_verifier.data_loader import DataConfig

config = DataConfig(
    filter_reviewed_only=True,
    max_samples_per_host=3000,
)

metrics = train_host_specific_models(
    data_paths=["data/converted/merged_dataset.jsonl"],
    output_dir="models/host_specific/",
    data_config=config,
    target_hosts=['E_coli', 'Human', 'Mouse', 'S_cerevisiae']
)
```

**优势：**
- 每个模型专注于特定宿主
- 最高的宿主特定性能
- 适合生产环境

## 🔬 Python API 使用

### 基础使用

```python
from codon_verifier.data_converter import convert_tsv_to_jsonl
from codon_verifier.data_loader import DataLoader, DataConfig
from codon_verifier.train_surrogate_multihost import train_unified_model

# 1. 转换数据
convert_tsv_to_jsonl(
    "data/Ec.tsv",
    "data/Ec.jsonl",
    filter_reviewed=True
)

# 2. 配置数据加载
config = DataConfig(
    balance_hosts=True,
    max_samples_per_host=1000,
    filter_reviewed_only=True,
)

# 3. 训练模型
metrics = train_unified_model(
    data_paths=["data/Ec.jsonl", "data/Human.jsonl"],
    output_model_path="models/my_model.pkl",
    data_config=config,
)

print(f"R² score: {metrics['r2_mu']:.3f}")
print(f"MAE: {metrics['mae_mu']:.3f}")
```

### 高级数据加载

```python
from codon_verifier.data_loader import DataLoader, DataConfig

loader = DataLoader(DataConfig(
    min_sequence_length=50,
    max_sequence_length=2000,
    balance_hosts=True,
    host_weights={'E_coli': 0.3, 'Human': 0.5, 'Mouse': 0.2}
))

# 加载并混合多宿主数据
records = loader.load_and_mix(
    file_paths=["data/converted/Ec.jsonl", 
                "data/converted/Human.jsonl",
                "data/converted/mouse.jsonl"],
    target_hosts={'E_coli', 'Human', 'Mouse'},
    total_samples=5000
)

# 划分训练/验证集（保持宿主分布）
from codon_verifier.data_loader import create_train_val_split

train, val = create_train_val_split(
    records,
    val_fraction=0.15,
    stratify_by_host=True
)

# 保存处理后的数据
loader.save_jsonl(train, "data/train.jsonl")
loader.save_jsonl(val, "data/val.jsonl")
```

### 模型预测

```python
from codon_verifier.surrogate import load_and_predict
from codon_verifier.hosts.tables import get_host_tables

# 加载宿主表
usage, trna_w = get_host_tables("Human")

# 预测
sequences = ["ATGGCTGCTGCTGCT", "ATGGCCGCCGCCGCC"]
predictions = load_and_predict(
    "models/unified_multihost.pkl",
    sequences,
    usage=usage,
    trna_w=trna_w
)

for seq, pred in zip(sequences, predictions):
    print(f"Sequence: {seq}")
    print(f"  μ = {pred['mu']:.2f}")
    print(f"  σ = {pred['sigma']:.2f}")
```

## 💡 最佳实践

### 1. 数据预处理建议

```bash
# 推荐的数据准备流程
python -m codon_verifier.data_converter \
  --input data/2025_bio-os_data/dataset/ \
  --output data/processed/ \
  --filter-reviewed \        # 只用高质量数据
  --max-records 15000 \      # 每个文件限制数量
  --merge                    # 合并为单文件
```

### 2. 训练配置建议

**小数据场景（< 5000样本）：**
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/processed/merged_dataset.jsonl \
  --out models/small_data.pkl \
  --mode unified \
  --balance-hosts \
  --reviewed-only
```

**中等数据场景（5000-20000样本）：**
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/processed/*.jsonl \
  --out models/medium_data.pkl \
  --mode unified \
  --balance-hosts \
  --max-per-host 4000 \
  --test-size 0.15
```

**大数据场景（> 20000样本）：**
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/processed/*.jsonl \
  --out models/host_specific/ \
  --mode host-specific \      # 宿主特定模型更好
  --reviewed-only \
  --min-length 50 \
  --max-length 2000
```

### 3. 模型选择建议

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| 目标宿主数据少 | 统一模型 | 利用其他宿主数据迁移学习 |
| 目标宿主数据充足 | 宿主特定模型 | 更高的宿主特异性 |
| 需要跨宿主优化 | 统一模型 | 更好的泛化能力 |
| 生产环境 | 混合专家模型 | 平衡性能和特异性 |

### 4. 表达水平估计说明

由于原始数据不包含实验表达水平，我们使用以下启发式方法估计：

- **基础分数**: 50
- **SwissProt审阅**: +20
- **亚细胞定位**: 
  - 细胞质/核糖体: +15-30
  - 膜蛋白: -10
- **序列长度**: 
  - 100-500aa: +10
  - <50 或 >1000aa: -10

**注意**: 这是粗略估计，建议：
1. 如有实验数据，应替换估计值
2. 使用 `confidence` 字段筛选数据
3. 主要依赖序列特征（CAI, TAI等）而非表达值

## 🔧 故障排除

### 问题1: 转换时序列长度不匹配

```
WARNING: Skipping Entry: sequence length mismatch
```

**原因**: DNA序列长度不是3的倍数，或与蛋白序列不对应

**解决**: 这是正常的，数据质量问题会自动跳过

### 问题2: 未知宿主

```
WARNING: Unknown organism: XXX, using E_coli as fallback
```

**原因**: 数据包含未配置的生物体

**解决**: 
1. 检查 `data_converter.py` 中的 `ORGANISM_MAP`
2. 添加新的宿主映射
3. 或使用 `--hosts` 参数明确指定

### 问题3: 训练数据不足

```
ValueError: No valid records processed
```

**原因**: 过滤条件太严格

**解决**:
```bash
# 放宽条件
python -m codon_verifier.train_surrogate_multihost \
  --data data/*.jsonl \
  --out models/model.pkl \
  --mode unified \
  --min-length 30 \          # 降低最小长度
  --max-length 5000 \        # 提高最大长度
  # 移除 --reviewed-only    # 不限制审阅状态
```

### 问题4: 内存不足

**原因**: 数据量太大

**解决**:
```bash
# 限制样本数
python -m codon_verifier.train_surrogate_multihost \
  --data data/*.jsonl \
  --out models/model.pkl \
  --max-samples 10000 \      # 限制总样本
  --max-per-host 2000        # 限制每宿主样本
```

## 📈 性能优化建议

### 数据增强策略（未来）

当前框架为未来数据增强预留了接口：

```python
from codon_verifier.data_loader import DataLoader, DataConfig

config = DataConfig(
    augment_reverse_complement=True,  # 反向互补增强（待实现）
    augment_synonym_swap=0.1,         # 同义密码子替换（待实现）
)
```

### 特征工程建议

如果有额外的蛋白质特征（如AlphaFold预测结构），可以添加：

```python
record = {
    "sequence": "ATG...",
    "protein_aa": "M...",
    "host": "E_coli",
    "expression": {"value": 100.0},
    "extra_features": {
        "plDDT_mean": 85.0,        # AlphaFold置信度
        "msa_depth": 120,          # MSA深度
        "conservation_mean": 0.42, # 保守性
        # 自定义特征会自动使用
        "custom_feature_1": 1.23,
    }
}
```

## 📚 参考

- [主文档](README.md)
- [算法框架](algorithm_rectification_framework.md)
- [API文档](docs/)
- [示例代码](examples/)

## 🎯 总结

新的多宿主数据集接口提供了：

✅ **灵活的数据转换**: TSV → JSONL，支持批量处理  
✅ **智能数据加载**: 多宿主、平衡采样、质量过滤  
✅ **多种训练模式**: 统一模型、宿主特定、混合策略  
✅ **完整的工作流**: 转换 → 加载 → 训练 → 预测  
✅ **生产就绪**: 详细文档、示例代码、错误处理

建议从小数据集开始实验，逐步扩展到完整数据集。

