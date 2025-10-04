# Training 微服务使用指南

## 🎯 问题背景

在本地环境中直接运行训练时可能遇到依赖问题：

```bash
❯ python3 -m codon_verifier.train_surrogate_multihost ...
ModuleNotFoundError: No module named 'sklearn'
```

**解决方案**：使用 **Training 微服务**，它包含所有必需的依赖（sklearn, lightgbm, numpy 等）。

## 🐳 Training 微服务架构

```
┌─────────────────────────────────────────────────────┐
│           Training Service (Docker)                 │
│                                                     │
│  ✓ Python 3.10                                      │
│  ✓ scikit-learn                                     │
│  ✓ LightGBM                                         │
│  ✓ pandas, numpy, scipy                             │
│  ✓ biopython, tqdm                                  │
│                                                     │
│  Input:  training_config.json                       │
│  Output: trained_model.pkl                          │
└─────────────────────────────────────────────────────┘
```

## 🚀 使用方式

### 方式 1：完整流程（一键运行，推荐）

```bash
# 完整流程包含训练
python3 scripts/microservice_enhance_expression.py \
  --input data/2025_bio-os_data/dataset/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service \
  --train-surrogate  # 添加此选项
```

**流程**：
1. ✅ TSV → JSONL 转换
2. ✅ Evo2 特征提取
3. ✅ 表达量增强
4. ✅ **代理模型训练（使用 Docker）**

**输出**：
- `data/enhanced/ecoli/Ec_enhanced.jsonl` - 增强数据
- `data/enhanced/ecoli/models/Ec_surrogate.pkl` - 训练好的模型

### 方式 2：单独使用 Training 服务

#### Step 1: 准备训练配置

创建 `training_config.json`:

```json
{
  "task": "train_unified",
  "config": {
    "data_paths": ["/data/enhanced/Ec_enhanced.jsonl"],
    "output_path": "/data/output/models/ecoli_surrogate.pkl",
    "mode": "unified",
    "data_config": {
      "min_sequence_length": 10,
      "max_sequence_length": 10000,
      "filter_reviewed_only": false,
      "balance_hosts": false
    },
    "surrogate_config": {
      "quantile_hi": 0.9,
      "test_size": 0.15
    }
  },
  "metadata": {
    "request_id": "train_001"
  }
}
```

#### Step 2: 运行 Training 服务

```bash
docker-compose -f docker-compose.microservices.yml run --rm \
  -v $(pwd)/data/enhanced:/data/enhanced:ro \
  -v $(pwd)/models:/data/output/models \
  -v $(pwd)/config:/data/config \
  training \
  --input /data/config/training_config.json
```

**输出**：
```
2025-10-04 17:30:00 - INFO - Processing training task: train_unified
2025-10-04 17:30:00 - INFO - Training unified multi-host model...
2025-10-04 17:30:05 - INFO - Loading data from 1 files...
2025-10-04 17:30:10 - INFO - Building features for 52159 samples...
2025-10-04 17:30:30 - INFO - Training quantile regression models...
2025-10-04 17:32:15 - INFO - Training metrics:
  r2_mu: 0.615
  mae_mu: 4.23
  sigma_mean: 3.45
  n_test: 7824
2025-10-04 17:32:15 - INFO - ✓ Training completed successfully in 135.23s
2025-10-04 17:32:15 - INFO - ✓ Training results written to: /data/output/training/result.json
```

### 方式 3：测试脚本

我创建了一个快速测试脚本：

```bash
# 使用 Docker（推荐）
python3 scripts/test_training_service.py \
  --input data/test/Ec_enhanced.jsonl \
  --output models/test_surrogate.pkl \
  --use-docker

# 不使用 Docker（需要本地依赖）
python3 scripts/test_training_service.py \
  --input data/test/Ec_enhanced.jsonl \
  --output models/test_surrogate.pkl
```

## 📊 配置参数说明

### data_config（数据配置）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `min_sequence_length` | int | 10 | 最小序列长度 |
| `max_sequence_length` | int | 10000 | 最大序列长度 |
| `filter_reviewed_only` | bool | false | 是否只用审阅过的蛋白 |
| `balance_hosts` | bool | false | 是否平衡不同宿主的样本数 |
| `max_samples_per_host` | int | null | 每个宿主最大样本数 |

### surrogate_config（模型配置）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `quantile_hi` | float | 0.9 | 上分位数（用于估计σ） |
| `test_size` | float | 0.15 | 测试集比例 |
| `use_log_transform` | bool | false | 是否对 y 做 log 变换 |
| `n_estimators` | int | 300 | LightGBM 树的数量 |
| `max_depth` | int | 6 | 树的最大深度 |

## 🔧 训练模式

### 1. Unified Mode（统一模型）

训练一个跨宿主的统一模型：

```json
{
  "config": {
    "mode": "unified",
    "data_paths": [
      "/data/enhanced/Ec_enhanced.jsonl",
      "/data/enhanced/Human_enhanced.jsonl"
    ],
    "output_path": "/data/output/models/unified_surrogate.pkl"
  }
}
```

**优点**：
- ✅ 利用所有宿主数据
- ✅ 更好的泛化能力
- ✅ 单个模型易于管理

**适用场景**：
- 某个宿主数据较少
- 需要跨宿主优化
- 生产环境简化部署

### 2. Host-Specific Mode（宿主特定模型）

为每个宿主训练独立模型：

```json
{
  "config": {
    "mode": "host-specific",
    "data_paths": ["/data/enhanced/merged_dataset.jsonl"],
    "output_path": "/data/output/models/host_models/",
    "target_hosts": ["E_coli", "Human", "Yeast"]
  }
}
```

**输出**：
- `models/host_models/E_coli_surrogate.pkl`
- `models/host_models/Human_surrogate.pkl`
- `models/host_models/Yeast_surrogate.pkl`

**优点**：
- ✅ 更高的宿主特异性
- ✅ 更好的单宿主性能

**适用场景**：
- 每个宿主数据充足（>1000 样本）
- 需要最佳宿主特定性能

## 📈 性能基准

### 训练时间（52,000 样本）

| 配置 | 时间 | 内存 | CPU |
|------|------|------|-----|
| **Unified** | 2-3 分钟 | ~2GB | 4 cores |
| **Host-Specific (3 宿主)** | 5-8 分钟 | ~3GB | 4 cores |

### 模型性能（测试集）

| 指标 | 元数据模式 | 增强模式 | 改进 |
|------|-----------|---------|------|
| **R²** | 0.45 | 0.61 | +36% |
| **MAE** | 5.89 | 4.23 | -28% |
| **σ Mean** | 3.12 | 3.45 | +11% |

## 🐛 故障排除

### 问题 1：Docker 服务无法启动

```bash
docker-compose: command not found
```

**解决**：
```bash
# 安装 docker-compose
sudo apt-get install docker-compose

# 或使用 docker compose（新版）
docker compose -f docker-compose.microservices.yml ...
```

### 问题 2：训练数据找不到

```
FileNotFoundError: Data file not found: /data/enhanced/Ec_enhanced.jsonl
```

**原因**：卷挂载路径错误

**解决**：检查 `-v` 参数：
```bash
# 错误示例
-v data/enhanced:/data/enhanced  # 相对路径可能有问题

# 正确示例
-v $(pwd)/data/enhanced:/data/enhanced  # 使用绝对路径
-v /full/path/to/data/enhanced:/data/enhanced
```

### 问题 3：内存不足

```
MemoryError: Unable to allocate array
```

**解决**：
```bash
# 限制数据量
{
  "config": {
    "max_samples": 10000,  # 只用 10000 样本
    "data_config": {
      "max_samples_per_host": 5000
    }
  }
}

# 或增加 Docker 内存
docker-compose run --rm \
  --memory="8g" \
  --memory-swap="16g" \
  training ...
```

### 问题 4：训练时间过长

**优化建议**：

1. **减少样本数**：
```json
{
  "config": {
    "max_samples": 20000
  }
}
```

2. **调整模型参数**：
```json
{
  "config": {
    "surrogate_config": {
      "n_estimators": 100,  // 从 300 减少到 100
      "max_depth": 4        // 从 6 减少到 4
    }
  }
}
```

3. **使用更快的硬件**：
   - 更多 CPU 核心
   - 更大内存
   - SSD 存储

## 📋 完整示例

### 示例 1：快速测试（100 样本）

```bash
# 1. 生成测试数据
python3 scripts/microservice_enhance_expression.py \
  --input data/2025_bio-os_data/dataset/Ec.tsv \
  --output-dir data/test \
  --evo2-service \
  --limit 100 \
  --no-docker

# 2. 测试训练服务
python3 scripts/test_training_service.py \
  --input data/test/Ec_enhanced.jsonl \
  --output models/test_surrogate.pkl \
  --use-docker

# 3. 验证模型
python3 -m codon_verifier.surrogate_infer_demo \
  --model models/test_surrogate.pkl \
  --seq ATGGCT... ATGGCA...
```

### 示例 2：生产环境（完整数据）

```bash
# 一键完整流程
python3 scripts/microservice_enhance_expression.py \
  --input data/2025_bio-os_data/dataset/Ec.tsv \
  --output-dir data/production/ecoli \
  --evo2-service \
  --train-surrogate
```

**预期时间**：~10-15 分钟

**输出**：
- 增强数据集：`data/production/ecoli/Ec_enhanced.jsonl`
- 代理模型：`data/production/ecoli/models/Ec_surrogate.pkl`
- 统计报告：`data/production/ecoli/pipeline_results.json`

### 示例 3：多宿主统一模型

```bash
# 1. 增强所有宿主数据
for host in Ec Human Yeast; do
  python3 scripts/microservice_enhance_expression.py \
    --input data/input/${host}.tsv \
    --output-dir data/enhanced/${host} \
    --evo2-service \
    --no-docker
done

# 2. 准备统一训练配置
cat > config/unified_training.json <<EOF
{
  "task": "train_unified",
  "config": {
    "data_paths": [
      "/data/enhanced/Ec_enhanced.jsonl",
      "/data/enhanced/Human_enhanced.jsonl",
      "/data/enhanced/Yeast_enhanced.jsonl"
    ],
    "output_path": "/data/output/models/unified_surrogate.pkl",
    "mode": "unified",
    "data_config": {
      "balance_hosts": true
    }
  }
}
EOF

# 3. 运行统一训练
docker-compose -f docker-compose.microservices.yml run --rm \
  -v $(pwd)/data/enhanced:/data/enhanced:ro \
  -v $(pwd)/models:/data/output/models \
  -v $(pwd)/config:/data/config \
  training \
  --input /data/config/unified_training.json
```

## 🎯 最佳实践

### 1. 开发阶段

- ✅ 使用 `--no-docker` 快速迭代
- ✅ 使用 `--limit 100` 测试流程
- ✅ 使用测试脚本验证功能

### 2. 生产环境

- ✅ 使用 Docker training 服务
- ✅ 保存完整配置 JSON
- ✅ 记录训练指标和版本
- ✅ 定期重新训练模型

### 3. 模型管理

```bash
# 版本化模型
models/
├── ecoli_surrogate_v1.0_20251004.pkl
├── ecoli_surrogate_v1.1_20251010.pkl
└── unified_surrogate_v2.0_20251015.pkl

# 记录元数据
models/
├── ecoli_surrogate.pkl
└── ecoli_surrogate.meta.json  # 训练配置和指标
```

## 🎉 总结

### 关键优势

| 特性 | 本地训练 | Training 微服务 |
|------|---------|----------------|
| **依赖管理** | ❌ 需手动安装 | ✅ 内置所有依赖 |
| **环境隔离** | ❌ 可能冲突 | ✅ 完全隔离 |
| **可重复性** | ⚠️ 依赖版本 | ✅ 固定版本 |
| **易用性** | ⚠️ 需配置环境 | ✅ 开箱即用 |
| **生产就绪** | ❌ 需改造 | ✅ 直接部署 |

### 使用建议

- **开发/调试**：`--no-docker`（如果有 sklearn）
- **CI/CD**：Docker training 服务
- **生产环境**：Docker training 服务
- **大规模训练**：Docker + 资源限制

---

**创建日期**：2025-10-04  
**版本**：v1.0  
**维护者**：Codon Verifier Team

