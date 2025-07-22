# BCFW - 区块链智能安防平台单容器部署
# 使用最新稳定版本环境，减少依赖冲突

# 第一阶段：构建前端
FROM node:22-slim AS frontend-builder

# 设置工作目录
WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖（包括dev依赖，构建需要）
RUN npm ci

# 复制前端源码
COPY frontend/ ./

# 构建前端（处理ARM64架构的Rollup问题）
RUN npm rebuild && npm run build

# 第二阶段：主运行环境
FROM ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # Python 3.11 和包管理
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    # Node.js 22 (最新LTS)
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    # 构建工具
    build-essential \
    # 系统工具
    htop \
    # 网络工具
    netcat-openbsd \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建应用目录
WORKDIR /app

# 创建Python软链接
RUN rm -f /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/python3.11 /usr/bin/python3 && \
    ln -s /usr/bin/python3.11 /usr/bin/python

# 安装最新版本的pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# 复制Python依赖文件并安装
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 安装Ganache CLI (最新版本)
RUN npm install -g ganache@latest

# 复制后端代码
COPY backend/ ./backend/

# 复制智能合约和脚本
COPY contracts/ ./contracts/
COPY scripts/ ./scripts/

# 复制系统管理脚本
COPY system.sh ./

# 复制构建好的前端文件
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 创建前端静态文件服务脚本
RUN echo '#!/bin/bash\ncd /app/frontend/dist && python3 -m http.server 5173 --bind 0.0.0.0' > /app/serve-frontend.sh && \
    chmod +x /app/serve-frontend.sh

# 复制启动脚本
COPY docker-entrypoint.sh /app/

# 设置权限
RUN chmod +x /app/docker-entrypoint.sh

# 创建数据目录（用于持久化）
RUN mkdir -p /app/data/ganache /app/data/db /app/logs

# 暴露端口
# 5173: 前端界面
# 8000: 后端API
# 8545: Ganache区块链RPC
EXPOSE 5173 8000 8545

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health && \
        curl -f http://localhost:5173 && \
        nc -z localhost 8545 || exit 1

# 设置入口点（只使用docker-entrypoint.sh，不使用supervisor）
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# 默认命令（保持运行）
CMD []