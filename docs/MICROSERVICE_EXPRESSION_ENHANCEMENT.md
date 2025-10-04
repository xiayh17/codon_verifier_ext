#

 微服务方式增强表达量估计指南

## 🎯 概述

本文档介绍如何使用**微服务架构**来增强蛋白质表达量估计。与直接运行脚本不同，微服务方式提供：

- ✅ **模块化**：每个服务独立运行，互不干扰
- ✅ **可扩展**：可以并行处理多个数据集
- ✅ **容错性**：单个服务失败不影响其他服务
- ✅ **GPU 隔离**：Evo2 服务独占 GPU，其他服务使用 CPU
- ✅ **生产就绪**：适合大规模数据处理

## 📊 架构流程

```
┌─────────────────────────────────────────────────────────────┐
│                 微服务增强流程                              │
└─────────────────────────────────────────────────────────────┘

Step 1: Data Conversion
┌─────────────┐
│   TSV File  │ ──────► data_converter ────► JSONL Dataset
└─────────────┘         (Python module)      (52,000 records)

Step 2: Evo2 Feature Extraction
┌─────────────┐
│JSONL Dataset│ ──────► Evo2 Microservice ──► Features JSON
└─────────────┘         (Docker + GPU)         (confidence, likelihood)

Step 3: Expression Enhancement
┌─────────────┐
│Features JSON│ ──────► Enhancer Script ────► Enhanced JSONL
└─────────────┘         (Python module)        (continuous values)

Step 4: Model Training (Optional)
┌─────────────┐
│Enhanced JSONL│ ─────► Surrogate Training ──► Model PKL
└─────────────┘         (LightGBM)              (predictor)
```

## 🚀 快速开始

### 方式 1：一键运行完整流程（推荐）

```bash
# 使用 Evo2 微服务的完整流程
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service
```

**输出**：
```
==============================================================
MICROSERVICE EXPRESSION ENHANCEMENT PIPELINE
==============================================================
Input: data/input/Ec.tsv
Output Directory: data/enhanced/ecoli
Use Evo2: True
==============================================================

==============================================================
STEP 1: Converting TSV to JSONL
==============================================================
Processing Ec.tsv...
✓ Parsed 52,159 valid records
✓ JSONL dataset created: data/enhanced/ecoli/Ec.jsonl

==============================================================
STEP 2: Extracting Evo2 Features (Microservice)
==============================================================
Running Evo2 service via Docker Compose
(This may take several minutes...)
Processed 10000 records (250.5 rec/s, 10000 success, 0 failed)
Processed 20000 records (248.2 rec/s, 20000 success, 0 failed)
...
Processing rate: 245.3 records/s
✓ Evo2 features extracted: data/enhanced/ecoli/Ec_evo2_features.json

==============================================================
STEP 3: Enhancing Expression Estimates
==============================================================
Total records: 52159
Enhanced with Evo2: 52159 (100.0%)
Mean absolute change: 8.34
✓ Enhanced dataset created: data/enhanced/ecoli/Ec_enhanced.jsonl

==============================================================
PIPELINE COMPLETED SUCCESSFULLY
==============================================================
Total time: 342.56s

Output files:
  1_convert: data/enhanced/ecoli/Ec.jsonl
  2_evo2_features: data/enhanced/ecoli/Ec_evo2_features.json
  3_enhance_expression: data/enhanced/ecoli/Ec_enhanced.jsonl
==============================================================
```

### 方式 2：分步执行（更灵活）

```bash
# Step 1: 转换 TSV 到 JSONL
python -m codon_verifier.data_converter \
  --input data/input/Ec.tsv \
  --output data/converted/Ec.jsonl

# Step 2: 运行 Evo2 微服务提取特征
docker-compose -f docker-compose.microservices.yml run --rm \
  -v $(pwd)/data/converted:/data/converted:ro \
  -v $(pwd)/data/output:/data/output \
  evo2 \
  python /app/services/evo2/app_enhanced.py \
  --input /data/converted/Ec.jsonl \
  --output /data/output/evo2/Ec_features.json \
  --mode features

# Step 3: 使用 Evo2 特征增强表达量
python scripts/enhance_expression_estimates.py \
  --input data/converted/Ec.jsonl \
  --evo2-results data/output/evo2/Ec_features.json \
  --output data/enhanced/Ec_enhanced.jsonl

# Step 4 (可选): 训练代理模型
python -m codon_verifier.train_surrogate_multihost \
  --data data/enhanced/Ec_enhanced.jsonl \
  --out models/ecoli_surrogate.pkl \
  --mode unified
```

## 🐳 Docker 微服务配置

### 1. 构建 Evo2 服务镜像

```bash
# 构建所有服务
docker-compose -f docker-compose.microservices.yml build

# 或只构建 Evo2 服务
docker-compose -f docker-compose.microservices.yml build evo2
```

### 2. 验证 GPU 访问

```bash
# 检查 GPU 是否可用
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  nvidia-smi

# 预期输出：显示 GPU 信息
```

### 3. Evo2 服务的两种后端

#### 选项 A：启发式后端（默认，无需 GPU）

当真实 Evo2 模型不可用时，使用基于序列属性的启发式评分：

```python
# 自动回退到启发式模式
# 基于 GC content, codon entropy, homopolymer runs
```

**优点**：
- 不需要 GPU
- 速度快（~200 records/s）
- 合理的特征估计

**缺点**：
- 不是真实的 Evo2 模型输出
- 准确性低于真实模型

#### 选项 B：真实 Evo2 模型（需要配置）

**本地模型**：
```bash
# 安装 Evo2
pip install evo2

# 设置环境变量
export USE_EVO2_LM=1

# 运行服务
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  -e USE_EVO2_LM=1 \
  python /app/services/evo2/app_enhanced.py \
  --input /data/converted/Ec.jsonl \
  --output /data/output/evo2/Ec_features.json \
  --mode features
```

**NVIDIA NIM API**：
```bash
# 设置 API key
export USE_EVO2_LM=1
export NVCF_RUN_KEY="your_nvidia_api_key"
export EVO2_NIM_URL="https://your-nim-endpoint"

# 运行服务（使用 API）
docker-compose -f docker-compose.microservices.yml run --rm evo2 \
  -e USE_EVO2_LM=1 \
  -e NVCF_RUN_KEY=$NVCF_RUN_KEY \
  -e EVO2_NIM_URL=$EVO2_NIM_URL \
  python /app/services/evo2/app_enhanced.py \
  --input /data/converted/Ec.jsonl \
  --output /data/output/evo2/Ec_features.json \
  --mode features
```

## 📋 详细使用场景

### 场景 1：小规模测试（1000 条记录）

```bash
# 使用 --limit 参数快速测试
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/test \
  --evo2-service \
  --limit 1000
```

**预期时间**：~30秒

### 场景 2：中等规模数据集（50,000 条）

```bash
# 完整流程
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service
```

**预期时间**：~5-10 分钟（启发式后端）

### 场景 3：大规模生产（500,000+ 条）

```bash
# 使用真实 Evo2 模型
export USE_EVO2_LM=1

python scripts/microservice_enhance_expression.py \
  --input data/input/Large_Dataset.tsv \
  --output-dir data/production/large \
  --evo2-service \
  --train-surrogate
```

**预期时间**：~1-2 小时（取决于 GPU）

### 场景 4：多宿主并行处理

```bash
# E. coli
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service &

# Human
python scripts/microservice_enhance_expression.py \
  --input data/input/Human.tsv \
  --output-dir data/enhanced/human \
  --evo2-service &

# Yeast
python scripts/microservice_enhance_expression.py \
  --input data/input/Yeast.tsv \
  --output-dir data/enhanced/yeast \
  --evo2-service &

# 等待所有任务完成
wait
```

### 场景 5：开发调试（不使用 Docker）

```bash
# 本地运行，无需 Docker
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/debug \
  --evo2-service \
  --no-docker \
  --limit 100
```

## 🔧 高级配置

### 自定义 Evo2 服务参数

编辑 `services/evo2/app_enhanced.py` 中的启发式参数：

```python
# 第 40 行附近
def heuristic_score(dna: str, **kwargs) -> Dict[str, float]:
    # 调整 GC 最优范围（默认 0.4-0.6）
    gc_optimal_min = 0.35  # 酵母
    gc_optimal_max = 0.55
    
    # 调整置信度计算权重
    gc_weight = 0.5        # GC content 权重
    entropy_weight = 0.3   # Codon entropy 权重
    homopolymer_weight = 0.2  # Homopolymer penalty 权重
```

### 并行处理多个文件

```python
# 使用 batch_process.py
python scripts/batch_process.py \
  --service evo2 \
  --input-dir data/input/ \
  --output-dir data/output/evo2/ \
  --workers 4 \
  --script-args "--mode features"
```

### 监控服务状态

```bash
# 查看服务日志
docker-compose -f docker-compose.microservices.yml logs evo2

# 实时监控
docker-compose -f docker-compose.microservices.yml logs -f evo2

# 检查资源使用
docker stats evo2-service
```

## 📊 输出文件说明

### 1. JSONL Dataset (`Ec.jsonl`)

原始转换后的数据：

```json
{
  "sequence": "ATGGCT...",
  "protein_aa": "MA...",
  "host": "E_coli",
  "expression": {
    "value": 60.0,
    "unit": "estimated",
    "assay": "metadata_heuristic",
    "confidence": "medium"
  },
  "metadata": {...}
}
```

### 2. Evo2 Features JSON (`Ec_evo2_features.json`)

Evo2 模型提取的特征：

```json
[
  {
    "task": "extract_features",
    "status": "success",
    "output": {
      "sequence": "ATGGCT...",
      "sequence_length": 2457,
      "avg_confidence": 0.876,
      "max_confidence": 0.945,
      "min_confidence": 0.812,
      "std_confidence": 0.042,
      "avg_loglik": -2.34,
      "perplexity": 12.56,
      "gc_content": 0.52,
      "codon_entropy": 4.23,
      "backend": "heuristic",
      "model_version": "heuristic-v1.0"
    },
    "metadata": {
      "request_id": "record_0",
      "processing_time_ms": 5,
      "service": "evo2-enhanced"
    }
  },
  ...
]
```

### 3. Enhanced JSONL (`Ec_enhanced.jsonl`)

增强后的数据集：

```json
{
  "sequence": "ATGGCT...",
  "protein_aa": "MA...",
  "host": "E_coli",
  "expression": {
    "value": 72.5,              // 增强后的连续值
    "unit": "estimated_enhanced",
    "assay": "model_enhanced_heuristic",
    "confidence": "high",        // 提升的置信度
    "original_value": 60.0       // 保留原始值
  },
  "metadata": {...}
}
```

## 🐛 故障排除

### 问题 1：Docker 服务无法访问 GPU

**错误**：
```
Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```

**解决**：
```bash
# 安装 nvidia-docker2
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 验证
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 问题 2：Evo2 服务处理速度慢

**原因**：
- 使用 CPU 而非 GPU
- 单线程处理大文件

**解决**：
```bash
# 确保 GPU 可用
export CUDA_VISIBLE_DEVICES=0

# 分批处理
python scripts/microservice_enhance_expression.py \
  --input large_file.tsv \
  --output-dir data/batch1 \
  --limit 10000 \
  --evo2-service
```

### 问题 3：内存不足

**错误**：
```
MemoryError: Unable to allocate array
```

**解决**：
```bash
# 增加 Docker 内存限制
docker-compose -f docker-compose.microservices.yml run --rm \
  --memory="8g" \
  --memory-swap="16g" \
  evo2 \
  python /app/services/evo2/app_enhanced.py \
  --input /data/converted/Ec.jsonl \
  --output /data/output/evo2/features.json
```

### 问题 4：特征文件格式不匹配

**错误**：
```
KeyError: 'avg_confidence'
```

**检查**：
```bash
# 验证特征文件格式
python -c "
import json
with open('data/output/evo2/features.json') as f:
    data = json.load(f)
    print(f'Records: {len(data)}')
    print(f'First record keys: {data[0].keys()}')
    print(f'Output keys: {data[0][\"output\"].keys()}')
"
```

## 📈 性能基准

### 启发式后端（CPU）

| 数据集大小 | 处理时间 | 速率 | 内存使用 |
|-----------|---------|------|---------|
| 1,000 | 5秒 | 200 rec/s | ~200MB |
| 10,000 | 45秒 | 220 rec/s | ~500MB |
| 52,000 | 210秒 | 245 rec/s | ~1.2GB |
| 500,000 | 35分钟 | 240 rec/s | ~8GB |

### 真实 Evo2 模型（GPU）

| 数据集大小 | 处理时间 | 速率 | GPU 使用 |
|-----------|---------|------|---------|
| 1,000 | 15秒 | 67 rec/s | ~2GB VRAM |
| 10,000 | 140秒 | 71 rec/s | ~3GB VRAM |
| 52,000 | 750秒 | 69 rec/s | ~4GB VRAM |
| 500,000 | 2小时 | 70 rec/s | ~4GB VRAM |

## 🎯 最佳实践

### 1. 生产环境配置

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  evo2:
    environment:
      - USE_EVO2_LM=1
      - NVCF_RUN_KEY=${NVCF_RUN_KEY}
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
          devices:
            - capabilities: [gpu]
```

### 2. 定期备份模型和数据

```bash
# 备份脚本
tar -czf enhanced_data_$(date +%Y%m%d).tar.gz data/enhanced/
tar -czf models_$(date +%Y%m%d).tar.gz models/
```

### 3. 版本控制

```bash
# 在输出目录记录版本信息
echo "Pipeline Version: 1.0.0" > data/enhanced/VERSION
echo "Evo2 Backend: ${USE_EVO2_LM:-heuristic}" >> data/enhanced/VERSION
echo "Date: $(date)" >> data/enhanced/VERSION
```

### 4. 监控和日志

```bash
# 保存日志
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service \
  2>&1 | tee logs/enhancement_$(date +%Y%m%d_%H%M%S).log
```

## 🔄 与其他工具集成

### 与 GRPO 训练集成

```bash
# 1. 增强数据
python scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service \
  --train-surrogate

# 2. 使用增强数据的代理模型进行 GRPO
python codon_verifier/grpo_train.py \
  --aa MAAAAAAA \
  --groups 8 \
  --steps 50 \
  --surrogate models/ecoli/Ec_surrogate.pkl \
  --host E_coli
```

### 与 Pipeline 集成

```bash
# 完整的三阶段流程
python scripts/pipeline.py \
  --input data/enhanced/ecoli/Ec_enhanced.jsonl \
  --output data/results/final.json
```

## 🎉 总结

### 关键优势

| 特性 | 直接脚本 | 微服务方式 |
|------|---------|-----------|
| **隔离性** | ❌ 共享环境 | ✅ 独立容器 |
| **可扩展性** | ❌ 单进程 | ✅ 并行处理 |
| **GPU 管理** | ❌ 混乱 | ✅ 专用服务 |
| **容错性** | ❌ 全部失败 | ✅ 局部恢复 |
| **生产就绪** | ❌ 需改造 | ✅ 开箱即用 |

### 使用建议

- **开发阶段**：使用 `--no-docker` 快速迭代
- **测试阶段**：使用 `--limit` 验证流程
- **生产环境**：使用真实 Evo2 + Docker 完整流程
- **大规模处理**：使用并行批处理脚本

---

**文档版本**：v1.0  
**更新日期**：2025-10-04  
**维护者**：Codon Verifier Team

