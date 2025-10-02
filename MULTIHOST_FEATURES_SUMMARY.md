# 多宿主数据集功能总结

## 🎯 新增功能概述

本次更新为Codon Verifier框架添加了完整的多宿主UniProt数据集支持，使其能够充分利用来自不同生物体的52,158条蛋白质数据进行训练。

## ✨ 核心特性

### 1. 数据转换工具 (`data_converter.py`)

**功能**:
- 将UniProt TSV格式转换为框架使用的JSONL格式
- 自动处理多种生物体（E. coli, Human, Mouse, Yeast等）
- 智能表达水平估计（基于蛋白质元数据）
- 数据质量过滤和验证

**使用示例**:
```bash
python -m codon_verifier.data_converter \
  --input data/dataset/ \
  --output data/converted/ \
  --filter-reviewed \
  --merge
```

**关键特性**:
- ✅ 批量转换整个目录
- ✅ 自动映射生物体名称到宿主标识
- ✅ 序列长度和一致性验证
- ✅ 支持合并多个文件
- ✅ 详细的转换统计和日志

### 2. 扩展宿主表 (`hosts/tables.py`)

**新增宿主**:
- **Human** (人类): 高表达基因密码子使用表
- **Mouse** (小鼠): 模式动物优化表
- **S_cerevisiae** (酿酒酵母): 真核表达系统
- **P_pastoris** (毕赤酵母): 工业表达系统

**API改进**:
```python
from codon_verifier.hosts.tables import get_host_tables, HOST_TABLES

# 获取特定宿主的密码子表
usage, trna_w = get_host_tables("Human")

# 查看所有支持的宿主
print(HOST_TABLES.keys())  
# dict_keys(['E_coli', 'Human', 'Mouse', 'S_cerevisiae', 'P_pastoris'])
```

### 3. 智能数据加载器 (`data_loader.py`)

**功能**:
- 多宿主数据加载和组织
- 智能采样和平衡策略
- 质量过滤和筛选
- 训练/验证集划分（支持分层）

**配置选项**:
```python
from codon_verifier.data_loader import DataLoader, DataConfig

config = DataConfig(
    # 采样策略
    max_samples_per_host=2000,
    min_sequence_length=50,
    max_sequence_length=2000,
    
    # 质量过滤
    filter_reviewed_only=True,
    exclude_low_confidence=True,
    
    # 数据混合
    balance_hosts=True,
    host_weights={'E_coli': 0.3, 'Human': 0.5, 'Mouse': 0.2}
)

loader = DataLoader(config)
```

**主要方法**:
- `load_multi_host()`: 加载并按宿主组织数据
- `sample_balanced()`: 平衡采样
- `load_and_mix()`: 完整的加载和混合流程
- `create_train_val_split()`: 分层划分数据集

### 4. 多宿主训练脚本 (`train_surrogate_multihost.py`)

**训练模式**:

#### 模式A: 统一模型
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/*.jsonl \
  --out models/unified.pkl \
  --mode unified \
  --balance-hosts
```

**优点**:
- 跨宿主知识迁移
- 目标宿主数据少时仍可用
- 更好的泛化能力

#### 模式B: 宿主特定模型
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/*.jsonl \
  --out models/host_specific/ \
  --mode host-specific \
  --hosts E_coli Human Mouse
```

**优点**:
- 最高的宿主特异性
- 每个宿主性能最优
- 适合生产部署

**高级选项**:
- `--balance-hosts`: 平衡各宿主样本数
- `--max-per-host`: 限制每宿主样本数
- `--reviewed-only`: 只使用SwissProt审阅数据
- `--min-length` / `--max-length`: 序列长度过滤

## 📊 数据使用策略

### 策略1: 宿主平衡采样

**目的**: 避免数据不平衡导致的偏差

**实现**:
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/*.jsonl \
  --out models/balanced.pkl \
  --balance-hosts \
  --max-per-host 2000
```

**效果**:
- 各宿主贡献相同数量的样本
- 防止大肠杆菌数据主导模型
- 提高跨宿主泛化能力

### 策略2: 质量优先

**目的**: 使用高质量数据提升模型性能

**实现**:
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/*.jsonl \
  --out models/high_quality.pkl \
  --reviewed-only \
  --min-length 100 \
  --max-length 2000
```

**效果**:
- 只使用SwissProt审阅的数据
- 过滤极端长度序列
- 减少噪声，提高稳定性

### 策略3: 迁移学习

**目的**: 先学习通用知识，再针对目标宿主优化

**实现**:
```bash
# 步骤1: 训练通用模型
python -m codon_verifier.train_surrogate_multihost \
  --data data/all_hosts.jsonl \
  --out models/base.pkl \
  --mode unified

# 步骤2: 针对目标宿主微调
python -m codon_verifier.train_surrogate_multihost \
  --data data/human_only.jsonl \
  --out models/human_finetuned.pkl \
  --hosts Human
```

**效果**:
- 充分利用所有数据
- 针对目标宿主优化
- 数据少的宿主也能获得好性能

### 策略4: 混合专家

**目的**: 为每个宿主提供专门优化的模型

**实现**:
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/all.jsonl \
  --out models/experts/ \
  --mode host-specific
```

**效果**:
- 每个宿主独立优化
- 最佳的宿主特异性
- 生产环境推荐

## 📦 文件结构

```
codon_verifier/
├── data_converter.py          # 新增：TSV→JSONL转换
├── data_loader.py             # 新增：智能数据加载
├── train_surrogate_multihost.py  # 新增：多宿主训练
├── hosts/
│   └── tables.py              # 扩展：新增4个宿主表
└── ...

docs/
├── MULTIHOST_DATASET_GUIDE.md    # 新增：完整使用指南
└── DATASET_QUICKSTART.md         # 新增：快速开始

examples/
├── multihost_dataset_example.sh  # 新增：Shell示例
└── multihost_python_example.py   # 新增：Python示例
```

## 🔄 完整工作流

```
1. 数据准备
   ↓
   [TSV文件] → data_converter.py → [JSONL文件]
   
2. 数据加载
   ↓
   [JSONL] → DataLoader → [过滤+平衡的数据集]
   
3. 模型训练
   ↓
   [数据集] → train_surrogate_multihost.py → [模型文件]
   
4. 应用优化
   ↓
   [模型] → generate_demo.py / grpo_train.py → [优化序列]
```

## 📈 性能提升

### 数据量对比

| 原框架 | 新框架 |
|--------|--------|
| 3条玩具数据 | 52,158条真实数据 |
| 仅E. coli | 5个宿主 |
| 无质量标记 | SwissProt审阅标记 |

### 功能对比

| 功能 | 原框架 | 新框架 |
|------|--------|--------|
| 数据转换 | ❌ 无 | ✅ 自动化 |
| 多宿主支持 | ⚠️ 基础 | ✅ 完整 |
| 数据过滤 | ❌ 无 | ✅ 多种策略 |
| 平衡采样 | ❌ 无 | ✅ 支持 |
| 宿主特定训练 | ❌ 无 | ✅ 支持 |
| 文档 | ⚠️ 基础 | ✅ 完整 |

## 🎓 使用建议

### 场景1: 学习和研究

**推荐配置**:
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/*.jsonl \
  --out models/research.pkl \
  --mode unified \
  --max-samples 3000
```

### 场景2: 工业应用

**推荐配置**:
```bash
python -m codon_verifier.train_surrogate_multihost \
  --data data/*.jsonl \
  --out models/production/ \
  --mode host-specific \
  --reviewed-only \
  --balance-hosts
```

### 场景3: 数据探索

**推荐配置**:
```python
from codon_verifier.data_loader import DataLoader, DataConfig

loader = DataLoader(DataConfig(
    balance_hosts=False,  # 保持原始分布
    filter_reviewed_only=False,
))

host_data = loader.load_multi_host(
    file_paths=["data/*.jsonl"],
    target_hosts=None  # 加载所有宿主
)

# 分析数据分布
for host, records in host_data.items():
    print(f"{host}: {len(records)} records")
```

## 🚀 快速开始

3条命令开始使用：

```bash
# 1. 转换数据
python -m codon_verifier.data_converter \
  --input data/dataset/ \
  --output data/converted/ \
  --filter-reviewed --merge

# 2. 训练模型
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/multihost.pkl \
  --mode unified \
  --balance-hosts

# 3. 使用优化
python -m codon_verifier.generate_demo \
  --aa MAAAAAAAAAA \
  --host E_coli \
  --surrogate models/multihost.pkl
```

## 📚 相关文档

- [完整使用指南](docs/MULTIHOST_DATASET_GUIDE.md)
- [快速开始教程](docs/DATASET_QUICKSTART.md)
- [主README](README.md)
- [算法框架](docs/algorithm_rectification_framework.md)

## 🔮 未来扩展

计划中的功能：

- [ ] 数据增强：反向互补、同义密码子替换
- [ ] 更多宿主：CHO细胞、昆虫细胞等
- [ ] 在线学习：持续更新模型
- [ ] 集成学习：组合多个模型
- [ ] 可视化工具：数据分布、模型性能分析

## 🙏 致谢

本功能基于以下数据和工具：
- UniProt数据库
- CoCoPUTs密码子使用表
- Kazusa密码子数据库

---

**版本**: 1.0  
**日期**: 2025-10-02  
**作者**: Codon Verifier Team

