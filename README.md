# Codon Verifier Framework

> 基于 Verifier + Surrogate + GRPO 的密码子优化框架，集成 Evo2 和 CodonTransformer

## 🚀 快速开始

### Docker 方式（推荐）

需要 NVIDIA GPU + nvidia-docker

```bash
# 一键启动
./docker_quick_start.sh

# 或手动构建
docker-compose build
docker-compose up -d

# 进入容器
docker-compose exec codon-verifier bash

# 验证安装
python verify_installation.py
```

### 本地安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> ⚠️ **注意**: Evo2 需要特定的 CUDA 环境（FP8 支持），强烈推荐使用 Docker

## 📚 文档

详细文档见 [`docs/`](docs/) 目录：

- **[完整使用文档](docs/README.md)** - 安装、训练、推理、API 参考
- **[算法框架梳理](docs/algorithm_rectification_framework.md)** - 技术架构与设计思路
- **[Docker 配置指南](docs/docker_setup.md)** - Docker 环境详细说明
- **[多宿主数据集指南](docs/MULTIHOST_DATASET_GUIDE.md)** - 新增：使用UniProt多宿主数据集
- **[数据集快速开始](docs/DATASET_QUICKSTART.md)** - 新增：5分钟上手多宿主数据
- **[CodonTransformer故障排除](docs/TROUBLESHOOTING_CODONTRANSFORMER.md)** - CodonTransformer安装问题修复

## 🔬 核心功能

### 1. 训练代理模型（Surrogate）

#### 基础训练（单宿主）

```bash
python codon_verifier/train_surrogate.py \
  --data toy_dataset.jsonl \
  --out ecoli_surrogate.pkl
```

#### 🆕 多宿主训练（推荐）

支持 E. coli, Human, Mouse, S. cerevisiae, P. pastoris 等多个宿主：

```bash
# 统一多宿主模型
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/multihost.pkl \
  --mode unified \
  --balance-hosts

# 宿主特定模型
python -m codon_verifier.train_surrogate_multihost \
  --data data/converted/merged_dataset.jsonl \
  --out models/host_specific/ \
  --mode host-specific \
  --hosts E_coli Human Mouse
```

> 📖 详见 [多宿主数据集指南](docs/MULTIHOST_DATASET_GUIDE.md)

### 2. 生成优化序列

```bash
# 零数据模式（规则 + Evo2）
python codon_verifier/generate_demo.py \
  --aa MAAAAAAA \
  --host E_coli \
  --n 500 \
  --forbid GAATTC GGATCC \
  --top 100

# 小数据加强（融合 Surrogate）
python codon_verifier/generate_demo.py \
  --aa MAAAAAAA \
  --host E_coli \
  --n 500 \
  --surrogate ecoli_surrogate.pkl \
  --top 100
```

### 3. GRPO 策略训练

```bash
python codon_verifier/grpo_train.py \
  --aa MAAAAAAA \
  --groups 8 \
  --steps 50 \
  --temperature 1.0 \
  --host E_coli
```

### 4. 离线评估

```bash
python codon_verifier/evaluate_offline.py \
  --dna ATGGCTGCT... \
  --motif GAATTC \
  --motif GGATCC
```

## 🧬 集成外部模型

### Evo2 核酸语言模型

```bash
# Docker 环境已预装 Evo2
# 启用 Evo2 特征
export USE_EVO2_LM=1

python codon_verifier/run_demo_features.py
```

### CodonTransformer

```bash
# Docker 环境已预装 CodonTransformer
python codon_verifier/generate_demo.py \
  --source ct \
  --method transformer \
  --temperature 0.8
```

## 🐳 Docker 镜像组成

基于 `nvcr.io/nvidia/pytorch:25.04-py3`：

- ✅ **Evo2**: GPU 加速序列生成（FP8 支持）
- ✅ **CodonTransformer**: 多物种密码子优化
- ✅ **ViennaRNA**: RNA 二级结构预测
- ✅ **LightGBM**: 高性能代理模型
- ✅ **PyTorch + CUDA 12.x**: 深度学习框架
- ✅ **JupyterLab**: 交互式开发环境

## 📊 数据格式

JSONL 格式，每行一条记录：

```json
{
  "sequence": "ATGGCTGCT...",
  "protein_aa": "MAAAA...",
  "host": "E_coli",
  "expression": {
    "value": 123.4,
    "unit": "RFU",
    "assay": "bulk_fluor"
  },
  "extra_features": {
    "plDDT_mean": 83.1,
    "msa_depth": 120
  }
}
```

## 🛠️ 开发

### 运行测试

```bash
# 在容器内
python verify_installation.py
```

### 启动 JupyterLab

```bash
# 在容器内
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

然后访问 `http://localhost:8888`

### 查看 GPU 状态

```bash
nvidia-smi
```

## 📝 引用

如使用 CodonTransformer，请引用：

```bibtex
@article{Fallahpour_Gureghian_Filion_Lindner_Pandi_2025,
  title={CodonTransformer: a multispecies codon optimizer using context-aware neural networks},
  journal={Nature Communications},
  author={Fallahpour, Adibvafa and Gureghian, Vincent and Filion, Guillaume J. and Lindner, Ariel B. and Pandi, Amir},
  year={2025},
  volume={16},
  pages={3205},
  doi={10.1038/s41467-025-58588-7}
}
```

## 📞 支持

- **问题反馈**: 提交 GitHub Issue
- **完整文档**: 见 [`docs/README.md`](docs/README.md)

## 📄 许可证

本项目遵循 MIT 许可证（或您的项目许可证）

---

**快速链接**:
- [CodonTransformer GitHub](https://github.com/adibvafa/CodonTransformer)
- [Evo2 文档](https://github.com/ArcInstitute/evo2)
- [ViennaRNA 官网](https://www.tbi.univie.ac.at/RNA/)
