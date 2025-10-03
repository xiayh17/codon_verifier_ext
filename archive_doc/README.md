# 文档归档 / Documentation Archive

本目录包含项目开发过程中的历史文档，主要用于参考和追溯项目演进历史。

This directory contains historical documentation from the project development process, mainly for reference and tracing project evolution.

---

## 📁 文档分类 / Document Categories

### 🔧 构建与问题解决 / Build & Problem Solving

| 文档 | 描述 | 日期 |
|------|------|------|
| `BUILD_FIX.md` | Docker 构建路径问题修复说明 | 2025-10-02 |
| `BUILD_SUCCESS.md` | 所有服务构建成功报告 | 2025-10-02 |
| `SOLUTION_SUMMARY.md` | setuptools 冲突完整解决方案总结 | 2025-10-02 |

**关键内容**：
- Docker 构建上下文路径问题的诊断与修复
- setuptools 版本冲突问题及微服务架构解决方案
- CodonTransformer editable 安装失败的解决方法

### 📝 开发日志 / Development Logs

| 文档 | 描述 | 日期 |
|------|------|------|
| `LOG.md` | 开发过程记录和调试日志 | 2025-10-02 |
| `CHANGES_SUMMARY.txt` | 多宿主数据集功能变更总结 | 2025-10-02 |

**关键内容**：
- 微服务架构实施过程
- 多宿主数据集功能添加过程
- 问题诊断和解决步骤

### 📊 实施报告 / Implementation Reports

| 文档 | 描述 | 日期 |
|------|------|------|
| `IMPLEMENTATION_REPORT.md` | 多宿主数据集功能完整实施报告 | 2025-10-02 |
| `READY_TO_USE.md` | 初始系统就绪指南（已被 QUICKSTART.md 替代） | 2025-10-02 |

**关键内容**：
- 多宿主数据集功能的完整实现细节
- 新增模块说明（data_converter, data_loader, train_surrogate_multihost）
- 文件清单和代码统计
- 性能评估和使用建议

### 🔬 设计文档 / Design Documents

| 文档 | 描述 | 日期 |
|------|------|------|
| `all_design.md` | 总体设计方案 | 早期 |
| `basic_frame.md` | 基础框架设计 | 早期 |
| `extension_frame.md` | 扩展框架设计 | 早期 |
| `framework_design.md` | 详细框架设计文档 | 早期 |

**关键内容**：
- 早期框架设计思路
- Policy-Verifier-RL 三件套设计
- GRPO 训练方案
- 奖励函数设计

### 🛠️ 环境配置 / Environment Setup

| 文档 | 描述 | 日期 |
|------|------|------|
| `Data_Convert.md` | 环境配置和数据转换说明 | 2025-10-02 |

**关键内容**：
- 虚拟环境配置步骤
- TSV 到 JSONL 数据转换
- 生物体识别和 fallback 逻辑修复
- Host 分布统计

---

## 🔍 为什么归档？/ Why Archived?

这些文档被归档的原因：

1. **已被替代**：功能已被更完善的文档替代
   - `READY_TO_USE.md` → 现在使用 `QUICKSTART.md`
   
2. **历史记录**：记录了开发过程，但不是当前使用文档
   - `BUILD_FIX.md`, `BUILD_SUCCESS.md`, `LOG.md`
   
3. **早期设计**：早期设计文档，部分内容已过时或已实现
   - `all_design.md`, `basic_frame.md`, `extension_frame.md`, `framework_design.md`
   
4. **一次性报告**：完成特定功能的实施报告
   - `IMPLEMENTATION_REPORT.md`, `CHANGES_SUMMARY.txt`

---

## 📖 当前文档位置 / Current Documentation

如果您在寻找当前的使用文档，请参考：

### 根目录文档
- `README.md` - 项目主文档
- `QUICKSTART.md` - 快速开始指南（微服务架构）
- `ARCHITECTURE.md` - 架构设计文档
- `MIGRATION_GUIDE.md` - 迁移指南（单体→微服务）
- `MULTIHOST_FEATURES_SUMMARY.md` - 多宿主功能总结
- `README.microservices.md` - 微服务详细文档

### docs/ 目录
- `docs/README.md` - 完整使用文档
- `docs/MULTIHOST_DATASET_GUIDE.md` - 多宿主数据集完整指南
- `docs/DATASET_QUICKSTART.md` - 数据集快速开始
- `docs/docker_setup.md` - Docker 环境配置
- `docs/algorithm_rectification_framework.md` - 算法框架梳理
- `docs/code_architecture.md` - 代码架构说明

---

## 💡 使用建议 / Usage Recommendations

### 适合查阅归档文档的情况：

1. **了解项目演进**：想知道项目是如何从单体架构演进到微服务架构的
2. **问题排查**：遇到类似问题时，查看历史解决方案
3. **设计参考**：了解早期设计思路和决策过程
4. **学习经验**：学习项目开发过程中的经验教训

### 日常使用：

请直接查看根目录和 `docs/` 目录下的当前文档。

---

## 📅 归档时间 / Archive Date

2025-10-02

## 👤 归档人 / Archived By

AI Assistant

---

**注意**：归档文档保留用于参考，但可能包含过时信息。请优先使用当前文档。

**Note**: Archived documents are kept for reference but may contain outdated information. Please prioritize current documentation.

