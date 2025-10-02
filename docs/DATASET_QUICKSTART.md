# 多宿主数据集快速开始 🚀

> 5分钟上手新的多宿主UniProt数据集

## 📦 数据集下载

假设你已经下载并解压了数据集到 `data/2025_bio-os_data/`：

```
data/2025_bio-os_data/
├── dataset/
│   ├── Ec.tsv       (18,780条 - 大肠杆菌)
│   ├── Human.tsv    (13,421条 - 人类)
│   ├── mouse.tsv    (13,253条 - 小鼠)
│   ├── Sac.tsv      (6,384条 - 酿酒酵母)
│   └── Pic.tsv      (320条 - 毕赤酵母)
└── Tests.xlsx       (505条无标数据)
```

## ⚡ 3步开始使用

### 步骤1: 转换数据（1分钟）

```bash
python -m codon_verifier.data_converter \
  --input data/2025_bio-os_data/dataset/ \
  --output data/converted/ \
  --filter-reviewed \
  --merge
```

✅ 输出: `data/converted/merged_dataset.jsonl`

### 步骤2: 训练模型（2-5分钟）

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/multihost.pkl \
  --mode unified \
  --balance-hosts \
  --max-samples 3000
```

✅ 输出: `models/multihost.pkl`

### 步骤3: 使用模型优化（< 1分钟）

```bash
python -m codon_verifier.generate_demo \
  --aa MAAAAAAAAAA \
  --host E_coli \
  --surrogate models/multihost.pkl \
  --n 500 \
  --top 100
```

✅ 输出: 优化后的密码子序列

## 🎯 支持的宿主

| 宿主名称 | 标识符 | 数据量 | 推荐场景 |
|---------|--------|--------|----------|
| 大肠杆菌 | `E_coli` | 18,780 | 原核表达系统 |
| 人类 | `Human` | 13,421 | 哺乳动物表达 |
| 小鼠 | `Mouse` | 13,253 | 模式动物 |
| 酿酒酵母 | `S_cerevisiae` | 6,384 | 真核表达系统 |
| 毕赤酵母 | `P_pastoris` | 320 | 工业表达系统 |

## 📊 训练策略对比

### 策略A: 统一模型（推荐初学者）

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/unified.pkl \
  --mode unified \
  --balance-hosts
```

**优点**: 
- ✅ 训练简单，一个模型适用所有宿主
- ✅ 利用跨宿主知识迁移
- ✅ 宿主数据少时仍能工作

**缺点**:
- ❌ 宿主特异性略差

### 策略B: 宿主特定模型（推荐生产环境）

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/host_specific/ \
  --mode host-specific \
  --hosts E_coli Human Mouse
```

**优点**:
- ✅ 每个宿主性能最优
- ✅ 适合生产部署

**缺点**:
- ❌ 需要更多数据
- ❌ 训练时间更长

## 🔥 高级用法

### 只使用高质量数据

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/high_quality.pkl \
  --mode unified \
  --reviewed-only \
  --min-length 100 \
  --max-length 2000
```

### 针对特定宿主训练

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/ecoli_only.pkl \
  --mode unified \
  --hosts E_coli \
  --max-samples 5000
```

### 平衡多宿主数据

```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/balanced.pkl \
  --mode unified \
  --balance-hosts \
  --max-per-host 2000
```

## 📝 Python API 示例

```python
from codon_verifier.data_converter import convert_dataset_directory
from codon_verifier.train_surrogate_multihost import train_unified_model
from codon_verifier.data_loader import DataConfig

# 1. 转换数据
convert_dataset_directory(
    dataset_dir="data/2025_bio-os_data/dataset",
    output_dir="data/converted",
    filter_reviewed=True,
    merge_output=True
)

# 2. 配置训练
config = DataConfig(
    balance_hosts=True,
    filter_reviewed_only=True,
    max_samples_per_host=2000,
)

# 3. 训练模型
metrics = train_unified_model(
    data_paths=["data/converted/merged_dataset.jsonl"],
    output_model_path="models/my_model.pkl",
    data_config=config,
    max_samples=8000
)

print(f"R² = {metrics['r2_mu']:.3f}")
print(f"MAE = {metrics['mae_mu']:.3f}")
```

## 🛠️ 完整工作流示例

运行示例脚本：

```bash
# Shell脚本
bash examples/multihost_dataset_example.sh

# Python脚本
python examples/multihost_python_example.py
```

## 🔍 检查训练结果

训练完成后，检查模型性能：

```bash
# 查看模型文件
ls -lh models/*.pkl

# 使用模型推理
python -m codon_verifier.surrogate_infer_demo \
  --model models/multihost.pkl \
  --seq ATGGCTGCTGCTGCT
```

## ❓ 常见问题

### Q: 转换数据时出现很多WARNING?

**A**: 这是正常的。数据集中部分条目可能有序列长度不匹配等问题，会自动跳过。

### Q: 训练时显示"No valid records"?

**A**: 可能是过滤条件太严格。尝试：
- 移除 `--reviewed-only`
- 降低 `--min-length`
- 增加 `--max-length`

### Q: 统一模型 vs 宿主特定模型，哪个更好?

**A**: 
- **数据少（< 3000）**: 用统一模型
- **数据多（> 5000）**: 用宿主特定模型
- **需要跨宿主**: 用统一模型
- **生产环境**: 用宿主特定模型

### Q: 如何添加新的宿主?

**A**: 编辑 `codon_verifier/hosts/tables.py`，添加新的密码子使用表。

## 📚 下一步

- 📖 阅读[完整文档](MULTIHOST_DATASET_GUIDE.md)
- 🔬 查看[算法框架](algorithm_rectification_framework.md)
- 💻 探索[示例代码](../examples/)
- 🎯 尝试[GRPO训练](../codon_verifier/grpo_train.py)

## 💡 提示

1. **从小数据集开始**: 先用 `--max-samples 1000` 快速验证流程
2. **使用 `--filter-reviewed`**: 提高数据质量
3. **平衡宿主数据**: 使用 `--balance-hosts` 避免偏差
4. **保存模型**: 训练时间较长，记得保存好模型文件

## 🎉 完成！

现在你已经掌握了多宿主数据集的基本使用。开始优化你的蛋白质序列吧！

