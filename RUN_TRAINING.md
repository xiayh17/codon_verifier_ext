# 🚀 使用真实数据训练模型 - 运行指南

## 📊 您的数据集信息

- **数据文件**: `data/converted/merged_dataset.jsonl`
- **总样本数**: 52,158
- **文件大小**: 124 MB
- **宿主分布**:
  ```
  E_coli        : 18,780 (36.0%)
  Human         : 13,421 (25.7%)
  Mouse         : 13,253 (25.4%)
  S_cerevisiae  :  6,550 (12.6%)
  P_pastoris    :    154 ( 0.3%)
  ```

---

## 🎯 训练方案（推荐按顺序）

我已经为您准备了5个训练配置，从快速测试到完整训练：

### 方案1️⃣: 快速测试（推荐先运行）⚡

**用途**: 验证训练流程正常工作  
**样本数**: ~1,000（每个宿主200个）  
**用时**: 1-2分钟  
**输出**: `quick_test_model.pkl`

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_quick.json
```

### 方案2️⃣: 平衡训练（推荐生产使用）⭐

**用途**: 平衡各宿主的样本，获得通用性好的模型  
**样本数**: ~15,000（每个宿主最多3,000个）  
**用时**: 5-10分钟  
**输出**: `balanced_multihost_model.pkl`

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_balanced.json
```

### 方案3️⃣: 主要宿主训练 🎯

**用途**: 只训练最常用的三个宿主  
**样本数**: ~15,000（E_coli、Human、Mouse各5,000个）  
**用时**: 8-15分钟  
**输出**: `main_hosts_model.pkl`

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_main_hosts.json
```

### 方案4️⃣: 宿主特定模型 🔬

**用途**: 为每个宿主训练独立的专用模型  
**样本数**: 每个宿主最多5,000个  
**用时**: 10-20分钟  
**输出**: 4个独立模型文件

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_host_specific.json
```

### 方案5️⃣: 完整训练（最强性能）💪

**用途**: 使用全部52,158个样本训练  
**样本数**: 52,158（全部）  
**用时**: 15-30分钟  
**输出**: `full_multihost_model.pkl`

```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_full.json
```

---

## 📋 完整运行步骤

### 步骤1: 确认准备就绪 ✅

```bash
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext

# 检查数据文件存在
ls -lh data/converted/merged_dataset.jsonl

# 检查训练配置文件
ls -lh data/input/training_real_*.json

# 确认训练服务已构建（如果还没有）
docker-compose -f docker-compose.microservices.yml build training
```

### 步骤2: 快速测试（必做）⚡

```bash
# 运行快速测试（1-2分钟）
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_quick.json

# 查看训练结果
cat data/output/training/training_real_quick_result.json | python3 -m json.tool
```

**预期输出**:
```json
{
  "status": "success",
  "output": {
    "metrics": {
      "r2_mu": 0.75,
      "mae_mu": 0.42,
      "n_samples": 1000,
      "n_features": 90,
      "host_distribution": {
        "E_coli": 200,
        "Human": 200,
        "Mouse": 200,
        "S_cerevisiae": 200,
        "P_pastoris": 154
      }
    }
  }
}
```

### 步骤3: 选择并运行生产训练 🎯

根据您的需求选择方案：

**选项A: 平衡训练（推荐）**
```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_balanced.json
```

**选项B: 完整训练（最佳性能）**
```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_full.json
```

**选项C: 宿主特定模型**
```bash
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_host_specific.json
```

### 步骤4: 查看训练结果 📊

```bash
# 查看所有训练结果
ls -lh data/output/training/

# 查看最新的训练日志
cat data/output/training/training_real_*_result.json | python3 -m json.tool

# 查看训练好的模型
ls -lh models/ data/output/models/
```

### 步骤5: 验证模型（可选）✨

```bash
# 使用训练好的模型进行测试
python3 -c "
import pickle
model_path = 'data/output/models/balanced_multihost_model.pkl'
with open(model_path, 'rb') as f:
    model = pickle.load(f)
print(f'✓ 模型加载成功')
print(f'特征数量: {len(model.feature_keys)}')
"
```

---

## 🔍 监控训练进度

### 实时查看日志

打开另一个终端窗口：

```bash
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext

# 实时查看训练容器日志
docker-compose -f docker-compose.microservices.yml logs -f training
```

### 检查系统资源

```bash
# 查看Docker容器状态
docker ps -a

# 查看资源使用情况
docker stats
```

---

## 📈 训练结果对比

| 方案 | 样本数 | 用时 | 适用场景 |
|------|--------|------|----------|
| 快速测试 | ~1,000 | 1-2分钟 | 验证流程 |
| 平衡训练 | ~15,000 | 5-10分钟 | **生产推荐** |
| 主要宿主 | ~15,000 | 8-15分钟 | E_coli/Human/Mouse |
| 宿主特定 | 各5,000 | 10-20分钟 | 每个宿主独立模型 |
| 完整训练 | 52,158 | 15-30分钟 | 最佳性能 |

---

## 💡 使用建议

### 首次使用

1. ✅ 先运行**快速测试**验证一切正常
2. ✅ 然后运行**平衡训练**获得生产可用模型
3. ✅ 根据实际效果决定是否运行完整训练

### 生产环境

- 推荐使用**平衡训练**或**完整训练**
- 如果只关注特定宿主，使用**主要宿主训练**
- 如果需要最高精度，使用**宿主特定模型**

### 性能优化

- 平衡训练通常已经足够好（15,000样本）
- 完整训练可能过拟合，除非确实需要
- 宿主特定模型适合生产环境中专注单一宿主的场景

---

## 🎨 自定义训练配置

如果需要自定义配置，可以编辑JSON文件：

```bash
# 复制并修改配置
cp data/input/training_real_balanced.json data/input/my_custom_training.json
nano data/input/my_custom_training.json

# 运行自定义训练
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/my_custom_training.json
```

### 可调整的参数

- `max_samples_per_host`: 每个宿主的最大样本数
- `balance_hosts`: 是否平衡各宿主样本数
- `target_hosts`: 指定训练的宿主列表
- `max_samples`: 总样本数上限
- `quantile_hi`: 分位数阈值（默认0.9）
- `test_size`: 测试集比例（默认0.15）

---

## 🐛 故障排除

### 问题1: 训练中断或失败

```bash
# 查看详细日志
docker-compose -f docker-compose.microservices.yml logs training

# 检查错误信息
cat data/output/training/*_result.json | grep -i error
```

### 问题2: 内存不足

减少样本数：
```json
"config": {
  "max_samples": 5000,  // 减少到5000
  "data_config": {
    "max_samples_per_host": 1000  // 减少每个宿主的样本
  }
}
```

### 问题3: 训练时间太长

使用快速测试配置或减少样本数。

---

## 📚 训练后续步骤

训练完成后，您可以：

1. **使用模型进行预测**
   ```bash
   python3 codon_verifier/surrogate_infer_demo.py \
     --model data/output/models/balanced_multihost_model.pkl \
     --sequence "ATGCGATCGATCG..."
   ```

2. **集成到CodonVerifier服务**
   ```bash
   docker-compose -f docker-compose.microservices.yml run --rm codon_verifier \
     --input /data/input/verify_task.json \
     --model /data/output/models/balanced_multihost_model.pkl
   ```

3. **进行性能评估**
   ```bash
   python3 codon_verifier/evaluate_offline.py \
     --model data/output/models/balanced_multihost_model.pkl \
     --test-data data/converted/merged_dataset.jsonl
   ```

---

## ✨ 一键运行脚本

如果想更简单，使用便捷脚本：

```bash
# 快速测试
./scripts/train_with_microservices.sh --mode quick

# 完整训练  
./scripts/train_with_microservices.sh --mode full

# 自定义配置
./scripts/train_with_microservices.sh --config data/input/training_real_balanced.json
```

但需要先修改脚本以支持这些新模式，或者直接使用docker-compose命令。

---

## 🎉 开始训练！

**推荐的完整流程**:

```bash
# 1. 快速测试（必做）
echo "步骤1: 快速测试..."
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_quick.json

# 2. 查看测试结果
echo "步骤2: 查看结果..."
cat data/output/training/training_real_quick_result.json | python3 -m json.tool

# 3. 运行平衡训练（推荐）
echo "步骤3: 平衡训练..."
docker-compose -f docker-compose.microservices.yml run --rm training \
  --input /data/input/training_real_balanced.json

# 4. 查看最终结果
echo "步骤4: 查看最终结果..."
cat data/output/training/training_real_balanced_result.json | python3 -m json.tool
ls -lh data/output/models/

echo "✅ 训练完成！"
```

---

**祝训练顺利！** 🚀

如有问题，请查看 `README.training.md` 或 `START_TRAINING.md` 获取更多帮助。

