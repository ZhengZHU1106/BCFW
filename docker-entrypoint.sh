#!/bin/bash

# BCFW 容器启动脚本
# 负责初始化和启动所有服务

set -e

echo "🚀 启动 BCFW 区块链智能安防平台容器..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 等待函数
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    log_info "等待 $service_name 服务启动 ($host:$port)..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            log_success "$service_name 服务已启动"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "$service_name 服务启动超时"
    return 1
}

# 检查HTTP服务
check_http_service() {
    local url=$1
    local service_name=$2
    local max_attempts=15
    local attempt=1
    
    log_info "检查 $service_name HTTP服务 ($url)..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            log_success "$service_name HTTP服务正常"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_warning "$service_name HTTP服务检查超时，但将继续启动"
    return 1
}

# 清理函数（优雅关闭）
cleanup() {
    log_info "接收到停止信号，正在优雅关闭服务..."
    
    # 停止supervisor
    if pgrep supervisord > /dev/null; then
        supervisorctl stop all
        killall supervisord 2>/dev/null || true
    fi
    
    # 停止其他进程
    pkill -f ganache 2>/dev/null || true
    pkill -f uvicorn 2>/dev/null || true
    pkill -f "python.*http.server" 2>/dev/null || true
    
    log_info "服务已停止"
    exit 0
}

# 注册信号处理器
trap cleanup SIGTERM SIGINT

# 第一步：检查环境
log_info "检查运行环境..."

# 检查Python
if ! command -v python3 >/dev/null 2>&1; then
    log_error "Python3 未安装"
    exit 1
fi

# 检查Node.js
if ! command -v node >/dev/null 2>&1; then
    log_error "Node.js 未安装"
    exit 1
fi

# 检查Ganache
if ! command -v ganache >/dev/null 2>&1; then
    log_error "Ganache 未安装"
    exit 1
fi

log_success "环境检查通过"

# 第二步：初始化目录权限
log_info "设置目录权限..."
chmod +x /app/system.sh 2>/dev/null || true
mkdir -p /app/logs /app/data
log_success "目录权限设置完成"

# 第三步：启动Ganache区块链
log_info "启动 Ganache 区块链网络..."

# 检查端口是否被占用
if nc -z localhost 8545 2>/dev/null; then
    log_warning "端口8545已被占用，尝试停止现有进程..."
    pkill -f ganache || true
    sleep 2
fi

nohup ganache \
    --mnemonic "bulk tonight audit hover toddler orange boost twenty biology flower govern soldier" \
    --blockTime 5 \
    --host 0.0.0.0 \
    --port 8545 \
    --accounts 10 \
    --defaultBalanceEther 1000 \
    > /app/logs/ganache.log 2>&1 &

GANACHE_PID=$!
echo $GANACHE_PID > /app/data/ganache.pid

# 等待Ganache启动
if wait_for_service "localhost" "8545" "Ganache"; then
    log_success "Ganache 区块链网络启动成功 (PID: $GANACHE_PID)"
else
    log_error "Ganache 启动失败"
    exit 1
fi

# 第四步：部署智能合约
log_info "部署 MultiSig 智能合约..."
cd /app
if node scripts/deploy_multisig_simple.js > /app/logs/contract-deploy.log 2>&1; then
    log_success "智能合约部署成功"
else
    log_warning "智能合约部署失败，查看日志: /app/logs/contract-deploy.log"
fi

# 第五步：启动后端API服务
log_info "启动 FastAPI 后端服务..."

# 检查端口是否被占用
if nc -z localhost 8000 2>/dev/null; then
    log_warning "端口8000已被占用，尝试停止现有进程..."
    pkill -f uvicorn || true
    sleep 2
fi

cd /app
nohup python3 -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > /app/logs/backend.log 2>&1 &

BACKEND_PID=$!
echo $BACKEND_PID > /app/data/backend.pid

# 等待后端启动
if wait_for_service "localhost" "8000" "Backend API"; then
    check_http_service "http://localhost:8000/health" "Backend API"
    log_success "后端API服务启动成功 (PID: $BACKEND_PID)"
else
    log_error "后端API启动失败"
    exit 1
fi

# 第六步：启动前端服务
log_info "启动前端Web服务..."

# 检查端口是否被占用
if nc -z localhost 5173 2>/dev/null; then
    log_warning "端口5173已被占用，尝试停止现有进程..."
    pkill -f "http.server 5173" || true
    sleep 2
fi

cd /app/frontend/dist
nohup python3 -m http.server 5173 --bind 0.0.0.0 \
    > /app/logs/frontend.log 2>&1 &

FRONTEND_PID=$!
echo $FRONTEND_PID > /app/data/frontend.pid

# 等待前端启动
if wait_for_service "localhost" "5173" "Frontend Web"; then
    log_success "前端Web服务启动成功 (PID: $FRONTEND_PID)"
else
    log_error "前端Web服务启动失败"
    exit 1
fi

# 第七步：最终健康检查
log_info "执行系统健康检查..."
sleep 5

# 检查所有关键服务
services_ok=true

if ! nc -z localhost 8545; then
    log_error "Ganache 区块链服务检查失败"
    services_ok=false
fi

if ! curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    log_error "后端API健康检查失败"
    services_ok=false
fi

if ! nc -z localhost 5173; then
    log_error "前端Web服务检查失败"
    services_ok=false
fi

if [ "$services_ok" = true ]; then
    log_success "🎉 BCFW系统启动完成！"
    echo ""
    echo "📊 访问地址:"
    echo "   - 前端界面: http://localhost:5173"
    echo "   - 后端API: http://localhost:8000"
    echo "   - API文档: http://localhost:8000/docs"
    echo "   - Ganache RPC: http://localhost:8545"
    echo ""
    echo "📋 日志位置:"
    echo "   - Ganache: /app/logs/ganache.log"
    echo "   - 后端: /app/logs/backend.log"
    echo "   - 前端: /app/logs/frontend.log"
    echo "   - 合约部署: /app/logs/contract-deploy.log"
    echo ""
    log_info "系统正在运行，按 Ctrl+C 停止..."
else
    log_error "系统启动不完整，请检查日志"
    exit 1
fi

# 如果提供了参数，执行参数命令，否则保持运行
if [ $# -eq 0 ]; then
    # 无参数时，保持容器运行并监控服务
    while true; do
        # 检查关键进程是否还在运行
        if ! kill -0 $GANACHE_PID 2>/dev/null; then
            log_error "Ganache 进程意外停止"
            exit 1
        fi
        
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            log_error "Backend 进程意外停止"
            exit 1
        fi
        
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            log_error "Frontend 进程意外停止"
            exit 1
        fi
        
        sleep 30
    done
else
    # 有参数时，执行指定的命令
    exec "$@"
fi