## 🔧 环境配置说明

根据您的项目结构，有**两种环境可选**：

### 📦 **方案 1: 本地虚拟环境（推荐用于数据转换）**

**适用场景**：
- ✅ TSV 到 JSON 数据转换
- ✅ 训练代理模型（Surrogate）
- ✅ 基础数据处理
- ❌ **不适合** Evo2（需要特定 CUDA 环境）

**启用步骤**：

[3 tools called]

太好了！✅ **虚拟环境已成功创建并配置完成！**

## 📋 环境配置总结

### ✅ **已完成的配置**

```bash
虚拟环境路径: /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext/.venv

已安装的依赖：
✅ Python: 3.13.5
✅ NumPy: 2.3.3
✅ scikit-learn: 1.7.2
✅ LightGBM: 4.6.0
✅ ViennaRNA: 2.7.0
```

---

## 🚀 如何使用环境

### **方案 1: 本地虚拟环境（当前已配置 ✅）**

#### **激活环境**

每次需要运行 Python 脚本时，先激活虚拟环境：

```bash
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext
source .venv/bin/activate
```

#### **运行 TSV 转换**

激活环境后，就可以运行数据转换了：

```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 转换单个文件
python -m codon_verifier.data_converter \
  --input data/2025_bio-os_data/dataset/Ec.tsv \
  --output data/converted/Ec.jsonl

# 3. 批量转换整个目录（推荐）
python -m codon_verifier.data_converter \
  --input data/2025_bio-os_data/dataset/ \
  --output data/converted/ \
  --filter-reviewed \
  --merge
```

#### **退出环境**

完成工作后：

```bash
deactivate
```

---

### **方案 2: Docker 环境（适用于完整功能）**

如果您需要使用 Evo2、CodonTransformer 等需要 GPU 的功能：

#### **启动 Docker 环境**

```bash
# 方式1: 使用快速启动脚本
./docker_quick_start.sh

# 方式2: 手动启动
docker-compose up -d
docker-compose exec codon-verifier bash
```

#### **在 Docker 中运行转换**

进入 Docker 容器后：

```bash
# 转换数据
python -m codon_verifier.data_converter \
  --input data/2025_bio-os_data/dataset/ \
  --output data/converted/ \
  --filter-reviewed \
  --merge
```

---

## 💡 推荐工作流程

### **对于 TSV 到 JSON 转换**

**推荐使用：本地虚拟环境** ✅

```bash
# 一次性设置（已完成✅）
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext
source .venv/bin/activate

# 运行转换
python -m codon_verifier.data_converter \
  --input data/2025_bio-os_data/dataset/ \
  --output data/converted/ \
  --filter-reviewed \
  --merge

# 查看结果
ls -lh data/converted/
head -n 3 data/converted/merged_dataset.jsonl
```

### **对于完整训练和推理**

**推荐使用：Docker 环境** 🐳

---

## 📊 环境对比

| 功能 | 本地虚拟环境 | Docker 环境 |
|------|------------|------------|
| TSV → JSON 转换 | ✅ **推荐** | ✅ |
| 训练代理模型 | ✅ | ✅ |
| 基础数据处理 | ✅ | ✅ |
| Evo2 推理 | ❌ | ✅ |
| CodonTransformer | ❌ | ✅ |
| GPU 加速 | ❌ | ✅ |
| 安装简单 | ✅ | ⚠️ 需要 Docker |
| 资源占用 | 低 | 高 |

---

## 🎯 快速开始：现在就转换数据

您现在就可以开始转换数据了！

```bash
# 1. 激活环境（在新终端中运行）
cd /mnt/c/Users/xiayh17/Projects/coursepicker_starter/coursepicker/codon_verifier_ext
source .venv/bin/activate

# 2. 转换数据
python -m codon_verifier.data_converter \
  --input data/2025_bio-os_data/dataset/ \
  --output data/converted/ \
  --filter-reviewed \
  --merge

# 3. 查看结果
echo "转换完成！查看结果："
ls -lh data/converted/
wc -l data/converted/merged_dataset.jsonl
```

我来查看一下数据转换脚本中处理生物体识别和fallback的逻辑。

[3 tools called]

我发现了问题！在 `data_converter.py` 中，第154-164行的生物体识别逻辑有缺陷。当遇到未知生物体时，代码直接使用 `E_coli`（大肠杆菌）作为fallback，但这对于酵母来说是不合理的。

让我查看一下 Pic.tsv 文件的内容来确认：

[1 tool called]

确认了！这些都是酵母（Yeast），但因为物种名称不在 `ORGANISM_MAP` 中，所以被错误地使用了 `E_coli`（大肠杆菌）作为fallback。

我来修改 `data_converter.py`，让它能够智能地根据生物体类型选择合适的fallback：

[1 tool called]

很好！现在我已经修改了逻辑，让它能够智能地识别生物体类型并选择合适的fallback：

1. **酵母类生物** - 使用 `S_cerevisiae`（酿酒酵母）作为fallback
2. **人类相关** - 使用 `Human` 作为fallback  
3. **小鼠相关** - 使用 `Mouse` 作为fallback
4. **其他（细菌等）** - 使用 `E_coli` 作为fallback

让我重新运行数据转换来验证修改：

[1 tool called]

完美！现在 fallback 逻辑已经修复了。我们可以看到：

✅ **之前（错误）**: 
```
Unknown organism: Wickerhamomyces canadensis (Yeast) (Pichia canadensis), using E_coli as fallback
```

✅ **现在（正确）**: 
```
Unknown organism: Wickerhamomyces canadensis (Yeast) (Pichia canadensis), using S_cerevisiae as fallback (yeast)
```

让我查看完整的转换结果：

[1 tool called]

太好了！修复成功。让我验证一下转换后的数据，确认 host 字段是否正确设置为 `S_cerevisiae`：

[2 tools called]

完美！✅ 所有的 Pichia 属及其相关酵母现在都正确地使用 `S_cerevisiae` 作为 host 了。

让我统计一下各个 host 的分布情况：

[1 tool called]

太好了！现在数据分布合理了：

**Host 分布统计**：
- `E_coli`: 18,780 条（大肠杆菌）
- `Human`: 13,421 条（人类）
- `Mouse`: 13,253 条（小鼠）
- **`S_cerevisiae`: 6,550 条**（酵母，包括原始的酿酒酵母 + Pichia 属等其他酵母）
- `P_pastoris`: 154 条（毕赤酵母）

## 修复总结

**问题**：Pichia 属的各种酵母被错误地识别为未知生物体，并使用 `E_coli`（大肠杆菌）作为 fallback，这在生物学上是不合理的。

**解决方案**：修改了 `codon_verifier/data_converter.py` 中的生物体识别逻辑（154-177行），添加了智能 fallback 机制：

1. **酵母类** → 使用 `S_cerevisiae` fallback（包括关键词：yeast, pichia, saccharomyces, candida, komagataella, hansenula, scheffersomyces, wickerhamomyces, cyberlindnera, ogataea, millerozyma）
2. **人类** → 使用 `Human` fallback  
3. **小鼠** → 使用 `Mouse` fallback
4. **其他** → 使用 `E_coli` fallback（主要是细菌）

现在所有的酵母生物体都会使用更合理的 `S_cerevisiae` 作为 codon usage 的参考！🎉