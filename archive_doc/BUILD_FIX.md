# 🔧 构建路径问题修复说明

## 问题

在构建 Docker 镜像时遇到错误：
```
failed to compute cache key: "/codon_verifier": not found
```

## 原因

Docker 构建上下文（build context）设置不正确：
- **旧配置**: `context: ./services/codon_verifier` 
- **问题**: Dockerfile 中的 `COPY ../../codon_verifier` 超出了构建上下文范围

Docker 不允许访问构建上下文之外的文件（安全限制）。

## 解决方案

### 修改 1: docker-compose.microservices.yml

将所有服务的构建上下文改为项目根目录：

```yaml
# 之前
services:
  codon_verifier:
    build:
      context: ./services/codon_verifier  # ❌ 太窄
      dockerfile: Dockerfile

# 之后
services:
  codon_verifier:
    build:
      context: .                          # ✅ 项目根目录
      dockerfile: services/codon_verifier/Dockerfile
```

### 修改 2: 各服务的 Dockerfile

调整 COPY 路径以匹配新的构建上下文：

```dockerfile
# services/evo2/Dockerfile
# 之前: COPY app.py /app/
# 之后: COPY services/evo2/app.py /app/

# services/codon_transformer/Dockerfile  
# 之前: COPY app.py /app/
# 之后: COPY services/codon_transformer/app.py /app/

# services/codon_verifier/Dockerfile
# 之前: COPY ../../codon_verifier /app/codon_verifier
# 之后: COPY codon_verifier /app/codon_verifier
# 之前: COPY app.py /app/
# 之后: COPY services/codon_verifier/app.py /app/
```

## 验证修复

现在可以正常构建了：

```bash
# 构建所有服务
docker-compose -f docker-compose.microservices.yml build

# 或单独构建某个服务
docker-compose -f docker-compose.microservices.yml build codon_verifier
```

## 为什么这样设计？

### 优点
✅ 可以访问项目根目录的所有文件  
✅ 可以复制 `codon_verifier/` 目录到镜像  
✅ 路径清晰明确  
✅ 符合 Docker 最佳实践

### 注意事项
⚠️ 构建上下文变大了（包含整个项目）  
✅ 可以通过 `.dockerignore` 优化（排除不需要的文件）

## 优化建议（可选）

创建 `.dockerignore` 文件排除不必要的文件：

```bash
# .dockerignore
**/__pycache__
**/*.pyc
**/*.pyo
**/.git
**/.gitignore
**/README*.md
**/docs/
**/logs/
**/data/output/
**/.cache/
```

这样可以加快构建速度，减小构建上下文大小。

## 现在可以使用了！

```bash
# 构建
docker-compose -f docker-compose.microservices.yml build

# 测试运行
docker-compose -f docker-compose.microservices.yml run --rm codon_verifier --help
```

