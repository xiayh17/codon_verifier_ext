# ⚡ 快速开始 - 一页搞定

## 🎯 您现在就可以运行的命令

### 1️⃣ 快速测试（1分钟，推荐首次运行）

```bash
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext

docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_quick.json
```

**结果**: 训练1000个样本，验证流程正常

---

### 2️⃣ 查看结果

```bash
cat data/output/training/training_real_quick_result.json | python3 -m json.tool
```

**看什么**: 
- `"status": "success"` - 训练成功
- `"n_samples"` - 样本数量
- `"r2_mu"` - R²分数（越接近1越好）

---

### 3️⃣ 生产训练（5-10分钟）

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_balanced.json
```

**结果**: 训练15000个样本的平衡多宿主模型

---

## 📊 5个训练方案速查

```bash
# 方案1: 快速测试 (1000样本, 1-2分钟)
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_quick.json

# 方案2: 平衡训练 (15000样本, 5-10分钟) ⭐推荐
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_balanced.json

# 方案3: 主要宿主 (15000样本, 8-15分钟)
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_main_hosts.json

# 方案4: 宿主特定 (各5000样本, 10-20分钟)
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_host_specific.json

# 方案5: 完整训练 (52158样本, 15-30分钟)
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_full.json
```

---

## 🎨 使用交互式脚本

```bash
./scripts/run_all_training.sh
```

然后按提示选择 1-6

---

## 📁 文件位置

```
训练配置: data/input/training_real_*.json
训练结果: data/output/training/*_result.json
训练模型: data/output/models/*.pkl
```

---

## 🔍 常用命令

```bash
# 查看所有训练结果
ls -lh data/output/training/

# 查看训练模型
ls -lh data/output/models/

# 实时监控训练
docker-compose -f docker-compose.microservices.yml logs -f training

# 检查数据
wc -l data/converted/merged_dataset.jsonl
```

---

## 💡 推荐流程

```bash
# 完整3步流程
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext

# 步骤1: 快速测试
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_quick.json

# 步骤2: 查看结果
cat data/output/training/training_real_quick_result.json | python3 -m json.tool

# 步骤3: 生产训练
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_balanced.json
```

---

## 📚 详细文档

- **中文快速上手**: `开始训练.md`
- **中文详细指南**: `RUN_TRAINING.md`
- **英文文档**: `START_TRAINING.md`, `README.training.md`

---

## 🚀 现在就开始！

复制粘贴这个命令：

```bash
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext && docker-compose -f docker-compose.microservices.yml run --rm training --input /data/input/training_real_quick.json
```

**就这么简单！** 🎉

