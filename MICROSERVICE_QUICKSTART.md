# 🚀 微服务方式增强表达量 - 快速开始

## 一行命令完成全流程

```bash
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service
```

这会自动完成：
1. ✅ TSV → JSONL 转换
2. ✅ Evo2 特征提取（微服务）
3. ✅ 表达量增强
4. ✅ 生成统计报告

## 📋 前置要求

```bash
# 1. 构建 Docker 镜像（首次运行，5-10分钟）
docker-compose -f docker-compose.microservices.yml build

# 2. 验证 GPU（如果使用真实 Evo2）
docker-compose -f docker-compose.microservices.yml run --rm evo2 nvidia-smi
```

## ⚡ 3 种使用模式

### 模式 1：启发式后端（默认，无需 GPU）

```bash
# 快速测试（1000 条）
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/test \
  --evo2-service \
  --limit 1000

# 完整数据集（~5分钟）
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service
```

### 模式 2：真实 Evo2 模型（需要 GPU）

```bash
# 设置环境变量
export USE_EVO2_LM=1

# 运行（~15分钟）
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli_real \
  --evo2-service
```

### 模式 3：包含模型训练

```bash
# 完整流程 + 代理模型训练（~30分钟）
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service \
  --train-surrogate
```

## 📂 输出文件

```
data/enhanced/ecoli/
├── Ec.jsonl                    # 转换后的数据
├── Ec_evo2_features.json       # Evo2 提取的特征
├── Ec_enhanced.jsonl           # ✨ 增强后的数据（重点）
├── models/
│   └── Ec_surrogate.pkl        # 代理模型（可选）
└── pipeline_results.json       # 流程统计
```

## 📊 典型输出

```
==============================================================
PIPELINE COMPLETED SUCCESSFULLY
==============================================================
Total time: 342.56s

Output files:
  1_convert: data/enhanced/ecoli/Ec.jsonl
  2_evo2_features: data/enhanced/ecoli/Ec_evo2_features.json
  3_enhance_expression: data/enhanced/ecoli/Ec_enhanced.jsonl

Enhanced with Evo2: 52159 (100.0%)
Mean absolute change: 8.34
High confidence records: 41% (vs 23% before)
==============================================================
```

## 🔧 常用选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `--input` | 输入 TSV 文件 | `data/input/Ec.tsv` |
| `--output-dir` | 输出目录 | `data/enhanced/ecoli` |
| `--evo2-service` | 使用 Evo2 微服务 | （标志） |
| `--limit` | 限制记录数（测试） | `--limit 1000` |
| `--train-surrogate` | 训练代理模型 | （标志） |
| `--no-docker` | 本地运行（开发） | （标志） |

## 🐛 常见问题

### Q1: 如何不使用 Evo2 服务？

```bash
# 只用元数据模式（最快）
python scripts/enhance_expression_estimates.py \
  --input data/converted/Ec.jsonl \
  --output data/enhanced/Ec_baseline.jsonl \
  --mode metadata_only
```

### Q2: 如何并行处理多个文件？

```bash
# 并行运行多个流程
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service &

python scripts/microservice_enhance_expression.py \
  --input data/input/Human.tsv \
  --output-dir data/enhanced/human \
  --evo2-service &

wait  # 等待所有任务完成
```

### Q3: 处理速度太慢？

```bash
# 1. 使用限制测试
--limit 1000  # 只处理 1000 条

# 2. 本地运行跳过 Docker 开销
--no-docker

# 3. 使用更快的启发式后端（默认）
# 或升级 GPU 使用真实 Evo2
```

## 🎯 下一步

```bash
# 1. 查看增强效果
head -n 5 data/enhanced/ecoli/Ec_enhanced.jsonl

# 2. 用增强数据训练代理模型
python -m codon_verifier.train_surrogate_multihost \
  --data data/enhanced/ecoli/Ec_enhanced.jsonl \
  --out models/ecoli_surrogate.pkl

# 3. 在优化中使用
python codon_verifier/grpo_train.py \
  --aa MAAAAAAA \
  --surrogate models/ecoli_surrogate.pkl \
  --host E_coli
```

## 📚 详细文档

- **完整指南**: `docs/MICROSERVICE_EXPRESSION_ENHANCEMENT.md`
- **表达量估计**: `docs/EXPRESSION_ESTIMATION.md`
- **微服务架构**: `ARCHITECTURE.md`

---

**提示**：首次运行建议使用 `--limit 100` 快速测试流程是否正常！

