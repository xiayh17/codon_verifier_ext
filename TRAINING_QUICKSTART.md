# 🚀 Training 微服务 - 快速开始

## ❌ 遇到的问题

```bash
❯ python3 -m codon_verifier.train_surrogate_multihost ...
ModuleNotFoundError: No module named 'sklearn'
```

## ✅ 解决方案：使用 Training 微服务

Training 微服务内置所有依赖（sklearn, lightgbm, pandas, numpy），无需本地安装！

## 🎯 三种使用方式

### 方式 1：一键完整流程（最简单）

```bash
# 包含数据增强 + 模型训练
python3 scripts/microservice_enhance_expression.py \
  --input data/2025_bio-os_data/dataset/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service \
  --train-surrogate  # 添加此选项即可
```

**输出**：
- `data/enhanced/ecoli/Ec_enhanced.jsonl` - 增强数据
- `data/enhanced/ecoli/models/Ec_surrogate.pkl` - 训练好的模型

**时间**：~10-15 分钟（52,000 样本）

### 方式 2：快速测试（100 样本）

```bash
# Step 1: 生成测试数据（30秒）
python3 scripts/microservice_enhance_expression.py \
  --input data/2025_bio-os_data/dataset/Ec.tsv \
  --output-dir data/test \
  --evo2-service \
  --limit 100 \
  --no-docker

# Step 2: 测试训练（使用 Docker，2分钟）
python3 scripts/test_training_service.py \
  --input data/test/Ec_enhanced.jsonl \
  --output models/test_surrogate.pkl \
  --use-docker
```

### 方式 3：手动 Docker 命令（高级）

```bash
# 准备配置文件
cat > config/training.json <<EOF
{
  "task": "train_unified",
  "config": {
    "data_paths": ["/data/enhanced/Ec_enhanced.jsonl"],
    "output_path": "/data/output/models/surrogate.pkl",
    "mode": "unified"
  }
}
EOF

# 运行 training 服务
docker-compose -f docker-compose.microservices.yml run --rm \
  -v $(pwd)/data/enhanced:/data/enhanced:ro \
  -v $(pwd)/models:/data/output/models \
  -v $(pwd)/config:/data/config \
  training \
  --input /data/config/training.json
```

## 📊 对比

| 方法 | 依赖 | 速度 | 适用场景 |
|------|------|------|---------|
| **本地训练** | ❌ 需安装 sklearn | 快 | 有依赖环境 |
| **Training 微服务** | ✅ 内置依赖 | 中等 | **推荐** |
| **完整流程** | ✅ 一键完成 | 慢 | 生产环境 |

## 🎉 推荐流程

### 新手（首次使用）

```bash
# 1. 快速测试（2分钟）
python3 scripts/test_training_service.py \
  --input data/test/Ec_enhanced.jsonl \
  --output models/test.pkl \
  --use-docker

# 2. 完整运行（10分钟）
python3 scripts/microservice_enhance_expression.py \
  --input data/2025_bio-os_data/dataset/Ec.tsv \
  --output-dir data/production \
  --evo2-service \
  --train-surrogate
```

### 有经验用户

```bash
# 直接运行完整流程
python3 scripts/microservice_enhance_expression.py \
  --input data/2025_bio-os_data/dataset/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service \
  --train-surrogate
```

## 🐛 常见问题

### Q: Docker 未安装？

**A**: 使用 `--no-docker` 选项（但需要本地安装 sklearn, lightgbm）

```bash
# 安装依赖
pip install scikit-learn lightgbm pandas numpy

# 运行
python3 scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/enhanced/ecoli \
  --evo2-service \
  --train-surrogate \
  --no-docker  # 本地运行
```

### Q: 训练太慢？

**A**: 使用测试模式

```bash
# 只处理 1000 条数据
python3 scripts/microservice_enhance_expression.py \
  --input data/input/Ec.tsv \
  --output-dir data/test \
  --evo2-service \
  --train-surrogate \
  --limit 1000  # 限制数据量
```

### Q: 如何验证模型？

**A**: 使用推理 demo

```bash
python3 -m codon_verifier.surrogate_infer_demo \
  --model models/test_surrogate.pkl \
  --seq ATGGCTGCT... ATGGCAAAA...
```

## 📚 详细文档

- **完整指南**：`TRAINING_MICROSERVICE_GUIDE.md`
- **微服务流程**：`MICROSERVICE_QUICKSTART.md`
- **表达量增强**：`docs/EXPRESSION_ESTIMATION.md`

---

**关键点**：使用 `--train-surrogate` 选项，微服务会自动处理所有依赖问题！🚀

