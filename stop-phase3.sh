#!/bin/bash
echo "=== 🛑 停止区块链智能安防平台 ==="

# 端口清理函数
cleanup_port() {
    local port=$1
    local service_name=$2
    
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "🔄 停止 $service_name (端口 $port)..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
        if ! lsof -ti:$port > /dev/null 2>&1; then
            echo "✅ $service_name 已停止"
        else
            echo "⚠️  $service_name 可能仍在运行"
        fi
    else
        echo "ℹ️  $service_name 未运行"
    fi
}

# 按端口清理所有服务
cleanup_port 5173 "Frontend"
cleanup_port 8000 "Backend API"
cleanup_port 8545 "Ganache"

# 如果提供了PID，也尝试按PID停止
if [ $# -gt 0 ]; then
    echo "🔄 按PID停止进程..."
    kill $@ 2>/dev/null || true
fi

echo "✅ 系统已停止"
