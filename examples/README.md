# 多宿主数据集示例

本目录包含使用新的多宿主UniProt数据集的示例代码。

## 📁 文件列表

### 1. `multihost_dataset_example.sh`

完整的Shell脚本工作流示例，包括：
- 数据转换
- 统一模型训练
- 宿主特定模型训练
- 模型使用

**运行方式**:
```bash
bash examples/multihost_dataset_example.sh
```

**前置条件**:
- 已下载并解压数据集到 `data/2025_bio-os_data/dataset/`
- 已安装所有依赖

### 2. `multihost_python_example.py`

Python API使用示例，展示：
- 数据转换API
- 数据加载和混合
- 统一模型训练
- 宿主特定模型训练
- 模型预测

**运行方式**:
```bash
python examples/multihost_python_example.py
```

**说明**:
- 部分示例默认被注释，需要取消注释才能运行
- 这是为了避免在没有数据的情况下报错
- 可以逐步运行各个示例函数

## 🚀 快速开始

### 方式1: 使用Shell脚本（推荐新手）

```bash
# 确保数据集在正确位置
ls data/2025_bio-os_data/dataset/

# 运行完整流程
bash examples/multihost_dataset_example.sh
```

### 方式2: 使用Python脚本（推荐开发者）

```bash
# 编辑脚本，取消注释需要运行的示例
vim examples/multihost_python_example.py

# 运行
python examples/multihost_python_example.py
```

### 方式3: 手动运行（推荐学习）

```bash
# 步骤1: 转换数据
python -m codon_verifier.data_converter \
  --input data/2025_bio-os_data/dataset/ \
  --output data/converted/ \
  --filter-reviewed \
  --merge

# 步骤2: 训练模型
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/multihost.pkl \
  --mode unified \
  --balance-hosts \
  --max-samples 3000

# 步骤3: 使用模型
python -m codon_verifier.generate_demo \
  --aa MAAAAAAAAAA \
  --host E_coli \
  --surrogate models/multihost.pkl \
  --n 500 \
  --top 100
```

## 📊 示例输出

### 数据转换输出

```
2025-10-02 10:00:00 - INFO - Processing Ec.tsv...
2025-10-02 10:00:05 - INFO - Processing Human.tsv...
2025-10-02 10:00:10 - INFO - Processing mouse.tsv...

=== Summary ===
Total valid records: 45123
Total skipped: 7035

Conversion complete: {
  "total_rows": 52158,
  "valid_records": 45123,
  "skipped": 7035,
  "filtered": 0
}
```

### 训练输出

```
2025-10-02 10:05:00 - INFO - Loading multi-host data...
2025-10-02 10:05:02 - INFO -   E_coli: 18780 records
2025-10-02 10:05:02 - INFO -   Human: 13421 records
2025-10-02 10:05:02 - INFO -   Mouse: 13253 records

2025-10-02 10:05:05 - INFO - Sampling balanced dataset...
2025-10-02 10:05:05 - INFO - Sampled 2000 records from E_coli
2025-10-02 10:05:05 - INFO - Sampled 2000 records from Human
2025-10-02 10:05:05 - INFO - Sampled 2000 records from Mouse

2025-10-02 10:10:00 - INFO - Training complete

TRAINING COMPLETE
============================================================
{
  "r2_mu": 0.742,
  "mae_mu": 8.34,
  "sigma_mean": 4.56,
  "n_test": 900,
  "model_path": "models/multihost.pkl",
  "n_samples": 6000,
  "n_features": 87,
  "host_distribution": {
    "E_coli": 2000,
    "Human": 2000,
    "Mouse": 2000
  }
}
```

## 💡 使用提示

### 1. 数据位置

确保数据集在以下位置：
```
data/2025_bio-os_data/
└── dataset/
    ├── Ec.tsv
    ├── Human.tsv
    ├── mouse.tsv
    ├── Sac.tsv
    └── Pic.tsv
```

### 2. 输出目录

脚本会自动创建以下目录：
```
outputs/
├── converted/       # 转换后的JSONL文件
└── models/         # 训练的模型文件
    ├── unified_multihost.pkl
    └── host_specific/
        ├── E_coli_surrogate.pkl
        ├── Human_surrogate.pkl
        └── Mouse_surrogate.pkl
```

### 3. 资源需求

| 操作 | 内存 | 时间 | 磁盘 |
|------|------|------|------|
| 数据转换 | < 1GB | 1-2分钟 | 100MB |
| 训练（3000样本） | 2-4GB | 3-5分钟 | 10MB |
| 训练（完整数据） | 8-16GB | 15-30分钟 | 50MB |

### 4. 故障排除

**问题**: 找不到数据文件
```bash
# 检查数据文件
ls -lh data/2025_bio-os_data/dataset/

# 如果不存在，请下载并解压数据集
```

**问题**: 内存不足
```bash
# 使用更少的样本
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/small.pkl \
  --max-samples 1000  # 减少样本数
```

**问题**: 训练时间太长
```bash
# 使用更少的样本和更少的估计器
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/fast.pkl \
  --max-samples 2000
```

## 📚 相关文档

- [多宿主数据集完整指南](../docs/MULTIHOST_DATASET_GUIDE.md)
- [快速开始教程](../docs/DATASET_QUICKSTART.md)
- [主README](../README.md)

## 🤝 贡献

如果你有更好的示例或使用技巧，欢迎：
1. 创建新的示例脚本
2. 改进现有示例
3. 添加使用案例
4. 提交Pull Request

---

**需要帮助？** 查看[完整文档](../docs/MULTIHOST_DATASET_GUIDE.md)或提交Issue

