# BCFW Docker 部署指南

区块链智能安防平台的一键Docker部署方案。

## 🚀 快速开始

### 前提条件
- 安装 Docker (20.10+)
- 安装 Docker Compose (可选)

### 方式一：单容器部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd BCFW

# 2. 构建镜像
docker build -t bcfw:latest .

# 3. 运行容器
docker run -d \
  --name bcfw-platform \
  -p 5173:5173 \
  -p 8000:8000 \
  -p 8545:8545 \
  bcfw:latest

# 4. 查看状态
docker logs -f bcfw-platform
```

### 方式二：使用 Docker Compose

```bash
# 1. 一键启动
docker-compose up --build -d

# 2. 查看日志
docker-compose logs -f

# 3. 停止服务
docker-compose down
```

## 📊 访问地址

启动成功后，访问以下地址：

- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Ganache RPC**: http://localhost:8545

## 🔍 系统监控

### 健康检查
```bash
# 检查容器状态
docker ps

# 检查服务健康
curl http://localhost:8000/health
curl http://localhost:5173
```

### 日志查看
```bash
# 查看实时日志
docker logs -f bcfw-platform

# 查看特定服务日志
docker exec bcfw-platform cat /app/logs/ganache.log
docker exec bcfw-platform cat /app/logs/backend.log
docker exec bcfw-platform cat /app/logs/frontend.log
```

## ⚙️ 配置选项

### 环境变量
```bash
docker run -d \
  --name bcfw-platform \
  -p 5173:5173 \
  -p 8000:8000 \
  -p 8545:8545 \
  -e NODE_ENV=production \
  -e PYTHONUNBUFFERED=1 \
  bcfw:latest
```

### 数据持久化（可选）
```bash
docker run -d \
  --name bcfw-platform \
  -p 5173:5173 \
  -p 8000:8000 \
  -p 8545:8545 \
  -v $(pwd)/docker-data:/app/data \
  -v $(pwd)/docker-logs:/app/logs \
  bcfw:latest
```

## 🛠️ 开发模式

### 本地开发调试
```bash
# 挂载源码目录
docker run -d \
  --name bcfw-dev \
  -p 5173:5173 \
  -p 8000:8000 \
  -p 8545:8545 \
  -v $(pwd)/backend:/app/backend \
  -v $(pwd)/frontend/src:/app/frontend/src \
  bcfw:latest
```

### 进入容器调试
```bash
# 进入容器
docker exec -it bcfw-platform bash

# 查看进程
ps aux

# 手动启动服务
supervisorctl status
supervisorctl restart backend
```

## 📋 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :5173
   lsof -i :8000
   lsof -i :8545
   
   # 修改端口映射
   docker run -p 15173:5173 -p 18000:8000 -p 18545:8545 bcfw:latest
   ```

2. **服务启动失败**
   ```bash
   # 查看详细启动日志
   docker logs bcfw-platform
   
   # 检查特定服务
   docker exec bcfw-platform supervisorctl status
   ```

3. **智能合约部署失败**
   ```bash
   # 重新部署合约
   docker exec bcfw-platform node scripts/deploy_multisig_simple.js
   
   # 查看部署日志
   docker exec bcfw-platform cat /app/logs/contract-deploy.log
   ```

4. **内存不足**
   ```bash
   # 增加内存限制
   docker run --memory=2g bcfw:latest
   ```

### 重置系统
```bash
# 停止并删除容器
docker stop bcfw-platform
docker rm bcfw-platform

# 删除镜像（可选）
docker rmi bcfw:latest

# 清理数据卷（可选）
docker-compose down -v
```

## 🔧 自定义构建

### 修改基础镜像
```dockerfile
# 使用不同的基础镜像
FROM node:22-alpine AS frontend-builder
# ... 前端构建

FROM ubuntu:24.04
# ... 主环境
```

### 优化镜像大小
```bash
# 多阶段构建
docker build --target production -t bcfw:slim .

# 使用Alpine Linux
docker build -f Dockerfile.alpine -t bcfw:alpine .
```

## 🌐 网络配置

### 自定义网络
```bash
# 创建专用网络
docker network create bcfw-network

# 运行在指定网络
docker run --network=bcfw-network bcfw:latest
```

### 反向代理（生产环境）
```yaml
# nginx.conf
upstream bcfw-backend {
    server localhost:8000;
}

upstream bcfw-frontend {
    server localhost:5173;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://bcfw-backend;
    }
    
    location / {
        proxy_pass http://bcfw-frontend;
    }
}
```

## 📈 性能优化

### 资源限制
```bash
docker run \
  --memory=1g \
  --cpus="1.0" \
  --memory-swap=2g \
  bcfw:latest
```

### 缓存优化
```bash
# 使用构建缓存
docker build --cache-from bcfw:latest -t bcfw:v1.1 .

# 预拉取基础镜像
docker pull node:22-slim
docker pull ubuntu:22.04
```

## 🔒 安全建议

### 生产环境配置
```bash
# 使用非root用户
docker run --user 1000:1000 bcfw:latest

# 只读文件系统
docker run --read-only --tmpfs /tmp bcfw:latest

# 网络隔离
docker run --network=bcfw-network --no-internet bcfw:latest
```

### 镜像安全扫描
```bash
# 扫描漏洞
docker scan bcfw:latest

# 使用安全基础镜像
docker build --build-arg BASE_IMAGE=ubuntu:22.04 -t bcfw:secure .
```

---

**注意**: 这是一个演示原型，生产环境使用前请进行充分的安全评估和测试。