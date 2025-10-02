# Docker 环境配置指南

本文档介绍如何使用 Docker 搭建包含 Evo2、CodonTransformer 和 Codon Verifier 框架的完整开发环境。

## 📋 前置要求

### 硬件要求
- **GPU**: NVIDIA GPU，compute capability >= 8.9（如 H100）
  - Evo2 需要 FP8 支持以获得最佳性能
  - 对于较低算力的 GPU，可能需要调整模型精度设置

### 软件要求
- Docker >= 20.10
- Docker Compose >= 1.29
- NVIDIA Docker Runtime（nvidia-docker2）
- NVIDIA 驱动 >= 525.60.13（支持 CUDA 12.x）

### 验证 GPU 支持
```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## 🚀 快速开始

### 方法一：使用 Docker Compose（推荐）

1. **构建镜像**
   ```bash
   docker-compose build
   ```

2. **启动容器**
   ```bash
   docker-compose up -d
   ```

3. **进入容器**
   ```bash
   docker-compose exec codon-verifier bash
   ```

4. **停止容器**
   ```bash
   docker-compose down
   ```

5. **🔧 修复CodonTransformer（如果安装失败）**
   
   如果CodonTransformer安装失败（setuptools版本冲突），在容器内运行：
   ```bash
   bash /workdir/fix_codontransformer.sh
   ```
   
   详见 [CodonTransformer故障排除](TROUBLESHOOTING_CODONTRANSFORMER.md)

### 方法二：使用 Docker 命令

1. **构建镜像**
   ```bash
   docker build -t codon-verifier:latest .
   ```

2. **运行容器（交互式）**
   ```bash
   docker run --gpus all -it --rm \
     -v $(pwd):/workdir \
     -v $HOME/.cache/huggingface:/workdir/.cache/huggingface \
     -p 8888:8888 \
     codon-verifier:latest
   ```

3. **运行容器（后台）**
   ```bash
   docker run --gpus all -d \
     --name codon-verifier-dev \
     -v $(pwd):/workdir \
     -v $HOME/.cache/huggingface:/workdir/.cache/huggingface \
     -p 8888:8888 \
     codon-verifier:latest \
     tail -f /dev/null
   ```

## 🔧 启动 JupyterLab

在容器内启动 JupyterLab：

```bash
# 方法 1: 在容器内执行
docker-compose exec codon-verifier jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

# 方法 2: 修改 docker-compose.yml 的 command
# command: jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

然后在浏览器访问：`http://localhost:8888`

## 📦 已安装组件

### 核心框架
- **Evo2**: 最新版本（GPU 加速序列生成模型）
- **CodonTransformer**: 从 GitHub 主分支安装（可编辑模式）
- **Codon Verifier**: 您的自定义框架（自动挂载）

### Python 依赖
- **科学计算**: numpy, scipy, pandas, scikit-learn
- **机器学习**: PyTorch, transformers, lightgbm
- **生物信息**: Biopython, ViennaRNA
- **开发工具**: Jupyter, matplotlib, seaborn, tqdm

### 系统工具
- ViennaRNA 2.6.4（包含 RNAfold 等工具）
- Git, wget, curl
- 完整的编译工具链（build-essential）

## 🗂️ 目录结构与挂载

```
/workdir/                          # 容器工作目录
├── codon_verifier/               # 您的框架（挂载）
├── docs/                         # 文档（挂载）
├── requirements.txt              # 依赖列表（挂载）
├── .cache/
│   ├── huggingface/             # HuggingFace 模型缓存
│   └── CodonTransformer/        # CodonTransformer 缓存
└── ...

/opt/CodonTransformer/            # CodonTransformer 源码（可编辑）
```

## 🧪 验证安装

进入容器后运行：

```bash
# 验证 Python 环境
python --version
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"

# 验证 Evo2
python -c "import evo2; print('Evo2 installed successfully')"

# 验证 CodonTransformer
python -c "import CodonTransformer; print('CodonTransformer installed successfully')"

# 验证 ViennaRNA
RNAfold --version

# 验证您的框架
python -c "from codon_verifier import generator; print('Codon Verifier framework loaded')"
```

## 🔄 模型缓存管理

### HuggingFace 模型
- **自动下载**: 首次使用时自动下载到 `/workdir/.cache/huggingface`
- **持久化**: 通过 volume 映射到宿主机 `$HOME/.cache/huggingface`
- **手动下载**（可选）:
  ```bash
  # 在容器内预下载 Evo2 模型
  python -c "from evo2 import Evo2; model = Evo2('evo2_7b')"
  ```

### CodonTransformer 模型
- 缓存位置：`/workdir/.cache/CodonTransformer`
- 通过 Docker volume 持久化

## 🐛 常见问题排查

### GPU 不可用
```bash
# 检查容器内 GPU
nvidia-smi

# 如果失败，检查 nvidia-docker 安装
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### ViennaRNA Python 绑定失败
- Dockerfile 已配置 fallback：如果 Python 绑定安装失败，会自动使用 CLI 工具
- 验证 CLI 可用：`RNAfold --version`

### 模型下载慢
```bash
# 使用镜像站（在容器内）
export HF_ENDPOINT=https://hf-mirror.com
```

### 权限问题
```bash
# 如果挂载目录权限不对，在容器内：
chown -R $(id -u):$(id -g) /workdir
```

## 🔐 高级配置

### 自定义环境变量

编辑 `docker-compose.yml` 添加环境变量：

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0,1  # 指定使用的 GPU
  - HF_ENDPOINT=https://hf-mirror.com  # HuggingFace 镜像
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # CUDA 内存配置
```

### 多 GPU 配置

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0', '1']  # 指定 GPU ID
          capabilities: [gpu]
```

### 开发模式挂载

如需修改 CodonTransformer 源码：

```yaml
volumes:
  - ./CodonTransformer:/opt/CodonTransformer  # 挂载本地克隆
```

## 📚 参考资料

- [Evo2 官方文档](https://github.com/evo-design/evo)
- [CodonTransformer GitHub](https://github.com/adibvafa/CodonTransformer)
- [NVIDIA Docker 文档](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [ViennaRNA 文档](https://www.tbi.univie.ac.at/RNA/)

## 💡 使用技巧

### 运行演示脚本
```bash
# 在容器内
cd /workdir
python codon_verifier/run_demo.py
```

### 训练代理模型
```bash
python codon_verifier/train_surrogate.py
```

### 启动 GRPO 训练
```bash
python codon_verifier/grpo_train.py --config configs/grpo_config.yaml
```

### 批量评估
```bash
python codon_verifier/evaluate_offline.py --input toy_dataset.jsonl
```
