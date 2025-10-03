# 📚 Codon Verifier Framework - 文档索引

本文档提供项目完整文档的导航和概览。

---

## 🚀 快速开始 / Quick Start

| 文档 | 适用场景 | 预计时间 |
|------|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | 使用微服务架构快速启动 | 3-5 分钟 |
| [docs/DATASET_QUICKSTART.md](docs/DATASET_QUICKSTART.md) | 使用多宿主数据集快速开始 | 5-10 分钟 |
| [README.md](README.md) | 完整项目概览和基础使用 | 10-15 分钟 |

**新用户推荐路径**：
1. 阅读 `README.md` 了解项目全貌
2. 根据需求选择：
   - 使用 Docker 微服务 → `QUICKSTART.md`
   - 使用多宿主数据训练 → `docs/DATASET_QUICKSTART.md`

---

## 📖 核心文档 / Core Documentation

### 项目概览
- **[README.md](README.md)** ⭐
  - 项目介绍和核心功能
  - 快速开始指南
  - 数据格式说明
  - 主要功能模块概览

### 架构设计
- **[ARCHITECTURE.md](ARCHITECTURE.md)**
  - 微服务架构设计详解
  - 服务间通信机制
  - 数据交换格式
  - 目录结构说明

- **[docs/algorithm_rectification_framework.md](docs/algorithm_rectification_framework.md)**
  - 算法框架梳理
  - 技术架构与设计思路
  - 费曼式讲解配 Mermaid 图

- **[docs/code_architecture.md](docs/code_architecture.md)**
  - 代码架构说明
  - 模块设计详解
  - 接口定义

---

## 🐳 微服务架构文档 / Microservices Documentation

| 文档 | 内容 | 适用人群 |
|------|------|----------|
| [QUICKSTART.md](QUICKSTART.md) | 3 分钟快速上手 | 新用户 |
| [README.microservices.md](README.microservices.md) | 详细使用文档 | 深度用户 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 架构设计细节 | 开发者 |
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | 单体→微服务迁移 | 老用户 |

**微服务特性**：
- ✅ 无依赖冲突（每个服务独立环境）
- ✅ 高效批处理（并行处理提升 10x）
- ✅ 故障隔离（一个服务崩溃不影响其他）
- ✅ 独立扩展和更新

---

## 🧬 多宿主数据集文档 / Multi-Host Dataset Documentation

| 文档 | 内容 | 适用人群 |
|------|------|----------|
| [docs/DATASET_QUICKSTART.md](docs/DATASET_QUICKSTART.md) | 5 分钟快速开始 | 新用户 |
| [docs/MULTIHOST_DATASET_GUIDE.md](docs/MULTIHOST_DATASET_GUIDE.md) | 完整使用指南 | 所有用户 |
| [MULTIHOST_FEATURES_SUMMARY.md](MULTIHOST_FEATURES_SUMMARY.md) | 功能特性总结 | 了解功能 |

**支持的宿主**：
- E. coli（大肠杆菌）- 18,780 条数据
- Human（人类）- 13,421 条数据
- Mouse（小鼠）- 13,253 条数据
- S. cerevisiae（酿酒酵母）- 6,384 条数据
- P. pastoris（毕赤酵母）- 320 条数据

**四种数据策略**：
1. 宿主平衡采样
2. 质量优先筛选
3. 迁移学习
4. 混合专家模型

---

## 🛠️ 环境配置文档 / Environment Setup

| 文档 | 内容 |
|------|------|
| [docs/docker_setup.md](docs/docker_setup.md) | Docker 环境详细配置 |
| [README.md](README.md) - 安装部分 | 本地安装和 Docker 安装 |

**推荐环境**：
- Docker（推荐）：一键部署，包含所有依赖
- 本地虚拟环境：适合基础功能和数据转换

---

## 📊 功能文档 / Feature Documentation

### 数据处理
- **数据转换**：`docs/MULTIHOST_DATASET_GUIDE.md` - 第 2 节
- **数据加载**：`docs/MULTIHOST_DATASET_GUIDE.md` - 第 4 节
- **数据格式**：`README.md` - 数据格式部分

### 模型训练
- **单宿主训练**：`README.md` - 训练代理模型部分
- **多宿主训练**：`docs/MULTIHOST_DATASET_GUIDE.md` - 第 3 节
- **GRPO 训练**：`README.md` - GRPO 策略训练部分

### 序列生成
- **基础生成**：`README.md` - 生成优化序列部分
- **约束解码**：`docs/README.md` - 约束解码部分
- **批量生成**：`README.microservices.md` - 批处理部分

### 评估与验证
- **离线评估**：`README.md` - 离线评估部分
- **规则评分**：`docs/README.md` - Verifier 部分

---

## 🔧 开发文档 / Development Documentation

### API 参考
- **Python API**：`docs/MULTIHOST_DATASET_GUIDE.md` - 第 4 节
- **命令行接口**：各个功能文档的使用示例部分
- **数据接口**：`README.md` - 数据格式部分

### 示例代码
- **Shell 示例**：`examples/multihost_dataset_example.sh`
- **Python 示例**：`examples/multihost_python_example.py`
- **示例说明**：`examples/README.md`

### 扩展开发
- **添加新宿主**：`docs/MULTIHOST_DATASET_GUIDE.md` - 最佳实践部分
- **自定义策略**：`docs/algorithm_rectification_framework.md`
- **集成外部工具**：`README.md` - 集成外部模型部分

---

## 🎯 按使用场景查找文档 / Find Documentation by Use Case

### 场景 1：我想快速开始使用这个框架
1. [README.md](README.md) - 了解项目
2. [QUICKSTART.md](QUICKSTART.md) - 快速启动

### 场景 2：我有多宿主数据想训练模型
1. [docs/DATASET_QUICKSTART.md](docs/DATASET_QUICKSTART.md) - 快速开始
2. [docs/MULTIHOST_DATASET_GUIDE.md](docs/MULTIHOST_DATASET_GUIDE.md) - 详细指南

### 场景 3：我想批量处理大量序列
1. [README.microservices.md](README.microservices.md) - 微服务详细文档
2. [ARCHITECTURE.md](ARCHITECTURE.md) - 架构说明（批处理部分）

### 场景 4：我在使用旧版本，想迁移到新架构
1. [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 完整迁移指南
2. [ARCHITECTURE.md](ARCHITECTURE.md) - 新架构理解

### 场景 5：我想深入了解算法原理
1. [docs/algorithm_rectification_framework.md](docs/algorithm_rectification_framework.md) - 算法框架
2. [docs/code_architecture.md](docs/code_architecture.md) - 代码架构
3. [docs/README.md](docs/README.md) - 详细技术文档

### 场景 6：我遇到了问题
1. [docs/MULTIHOST_DATASET_GUIDE.md](docs/MULTIHOST_DATASET_GUIDE.md) - 故障排除部分
2. [README.md](README.md) - 支持部分
3. [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 常见问题

---

## 📂 文档目录结构 / Documentation Structure

```
codon_verifier_ext/
├── README.md                           # 项目主文档 ⭐
├── DOCUMENTATION_INDEX.md              # 本文档 📚
├── QUICKSTART.md                       # 快速开始（微服务）
├── ARCHITECTURE.md                     # 架构设计
├── MIGRATION_GUIDE.md                  # 迁移指南
├── README.microservices.md             # 微服务详细文档
├── MULTIHOST_FEATURES_SUMMARY.md       # 多宿主功能总结
│
├── docs/                               # 详细文档目录
│   ├── README.md                       # 完整使用文档
│   ├── MULTIHOST_DATASET_GUIDE.md      # 多宿主数据集指南 ⭐
│   ├── DATASET_QUICKSTART.md           # 数据集快速开始
│   ├── docker_setup.md                 # Docker 配置
│   ├── algorithm_rectification_framework.md  # 算法框架
│   └── code_architecture.md            # 代码架构
│
├── examples/                           # 示例代码
│   ├── README.md                       # 示例说明
│   ├── multihost_dataset_example.sh    # Shell 示例
│   └── multihost_python_example.py     # Python 示例
│
└── archive_doc/                        # 历史文档归档
    └── README.md                       # 归档说明
```

---

## 📈 文档版本与更新 / Version & Updates

| 版本 | 日期 | 主要更新 |
|------|------|---------|
| v1.0 | 2025-10-02 | 初始版本，整理所有文档 |
| v1.1 | 2025-10-02 | 添加多宿主数据集文档 |
| v1.2 | 2025-10-02 | 完成文档整理和归档 |

---

## 🔗 外部资源 / External Resources

### 相关项目
- [CodonTransformer GitHub](https://github.com/adibvafa/CodonTransformer)
- [Evo2 文档](https://github.com/ArcInstitute/evo2)
- [ViennaRNA 官网](https://www.tbi.univie.ac.at/RNA/)

### 学习资源
- [CodonTransformer DeepWiki](https://deepwiki.com/Adibvafa/CodonTransformer)
- [Docker 官方文档](https://docs.docker.com/)
- [LightGBM 文档](https://lightgbm.readthedocs.io/)

---

## 💡 文档使用提示 / Documentation Tips

### 文档标记说明
- ⭐ 必读文档
- 🚀 快速开始
- 📖 详细文档
- 🔧 技术文档
- 💡 最佳实践

### 阅读顺序建议

**新手用户**：
1. README.md
2. QUICKSTART.md
3. docs/DATASET_QUICKSTART.md
4. 根据需要查阅其他文档

**高级用户**：
1. ARCHITECTURE.md
2. docs/MULTIHOST_DATASET_GUIDE.md
3. docs/algorithm_rectification_framework.md
4. docs/code_architecture.md

**开发者**：
1. docs/code_architecture.md
2. ARCHITECTURE.md
3. examples/ 下的示例代码
4. docs/algorithm_rectification_framework.md

---

## 📝 贡献文档 / Contributing to Documentation

如果您发现文档有误或需要改进：
1. 提交 GitHub Issue 说明问题
2. 或者直接提交 Pull Request 修改文档

---

## 📞 获取帮助 / Get Help

- **问题反馈**：提交 GitHub Issue
- **功能请求**：在 Issue 中详细描述需求
- **文档改进建议**：欢迎提出

---

**最后更新**：2025-10-02  
**维护者**：Codon Verifier Team

---

**快速链接 / Quick Links**：
- [返回主 README](README.md)
- [快速开始](QUICKSTART.md)
- [完整文档](docs/README.md)
- [历史文档](archive_doc/README.md)

