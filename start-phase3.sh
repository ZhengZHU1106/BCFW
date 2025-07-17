#!/bin/bash

# 区块链智能安防平台 - Phase 3 启动脚本
# 启动完整的前后端系统

echo "=== 🚀 启动区块链智能安防平台 Phase 3 ==="

# 检查前置条件
echo "📋 检查前置条件..."

if ! command -v ganache &> /dev/null; then
    echo "❌ Ganache 未安装. 请运行: npm install -g ganache"
    exit 1
fi

# 智能检测 Python3 版本和 uvicorn
detect_python_with_uvicorn() {
    # 按优先级检测可用的Python版本
    local python_candidates=(
        "python3"                                    # 默认python3
        "/opt/homebrew/opt/python@3.13/bin/python3.13"  # Homebrew Python 3.13
        "/opt/homebrew/bin/python3"                 # Homebrew 默认python3
        "/usr/bin/python3"                          # 系统python3
        "python3.13" "python3.12" "python3.11" "python3.10" "python3.9"  # 各版本
    )
    
    for python_cmd in "${python_candidates[@]}"; do
        if command -v "$python_cmd" &> /dev/null; then
            local version_info=$($python_cmd --version 2>&1)
            echo "🔍 检测到 Python: $python_cmd ($version_info)"
            
            # 检查uvicorn是否可用
            if "$python_cmd" -m uvicorn --version &> /dev/null 2>&1; then
                echo "✅ $python_cmd 中 uvicorn 可用"
                echo "$python_cmd"  # 只返回命令路径
                return 0
            else
                echo "⚠️  $python_cmd 中 uvicorn 不可用，尝试安装..."
                
                # 尝试安装uvicorn
                if "$python_cmd" -m pip install "uvicorn[standard]" --user &> /dev/null 2>&1; then
                    echo "✅ 成功为 $python_cmd 安装 uvicorn"
                    echo "$python_cmd"
                    return 0
                else
                    echo "❌ 无法为 $python_cmd 安装 uvicorn，继续尝试其他版本..."
                fi
            fi
        fi
    done
    
    echo "❌ 未找到可用的Python3和uvicorn组合"
    echo "请安装Python3并运行: python3 -m pip install 'uvicorn[standard]' --user"
    exit 1
}

echo "🐍 检测Python环境..."
PYTHON_CMD=$(detect_python_with_uvicorn 2>&1 | tail -n 1)
echo "✅ 将使用: $PYTHON_CMD"

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 端口冲突检查和清理函数
check_and_cleanup_port() {
    local port=$1
    local service_name=$2
    
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "⚠️  端口 $port 被占用（$service_name），正在清理..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
        if lsof -ti:$port > /dev/null 2>&1; then
            echo "❌ 端口 $port 清理失败，请手动终止占用进程"
            exit 1
        fi
        echo "✅ 端口 $port 清理成功"
    fi
}

# 检查和清理必要端口
echo "🔍 检查端口占用情况..."
check_and_cleanup_port 8545 "Ganache"
check_and_cleanup_port 8000 "Backend API"
check_and_cleanup_port 5173 "Frontend"

echo "✅ 前置条件检查完成"

# 启动服务
echo ""
echo "🔗 启动 Ganache 区块链..."
ganache --mnemonic "bulk tonight audit hover toddler orange boost twenty biology flower govern soldier" \
        --blockTime 5 \
        --host 127.0.0.1 \
        --port 8545 \
        --accounts 10 \
        --defaultBalanceEther 1000 \
        > logs/ganache.log 2>&1 &

GANACHE_PID=$!
echo "✅ Ganache 启动成功 (PID: $GANACHE_PID)"

# 等待Ganache启动
echo "⏳ 等待Ganache准备就绪..."
sleep 5

# 启动后端
echo ""
echo "🔧 启动后端API服务..."
# 设置PYTHONPATH确保导入正确
export PYTHONPATH="$(pwd):$PYTHONPATH"
"$PYTHON_CMD" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端API启动成功 (PID: $BACKEND_PID) 使用 $PYTHON_CMD"
echo "📍 PYTHONPATH已设置为: $(pwd)"

# 等待后端启动
echo "⏳ 等待后端准备就绪..."
sleep 8

# 启动前端
echo ""
echo "🎨 启动前端开发服务器..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✅ 前端开发服务器启动成功 (PID: $FRONTEND_PID)"

# 等待前端启动
echo "⏳ 等待前端准备就绪..."
sleep 5

# 显示服务状态
echo ""
echo "=== 🎉 系统启动完成 ==="
echo ""
echo "📊 服务状态："
echo "  🔗 Ganache 区块链:    http://127.0.0.1:8545"
echo "  🔧 后端API:          http://localhost:8000"
echo "  🎨 前端界面:         http://localhost:5173"
echo ""
echo "📋 进程信息："
echo "  Ganache PID:  $GANACHE_PID"
echo "  Backend PID:  $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "📝 日志文件："
echo "  Ganache:  logs/ganache.log"
echo "  Backend:  logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo "🔧 测试命令："
echo "  系统状态: curl http://localhost:8000/api/system/status"
echo "  攻击模拟: curl -X POST http://localhost:8000/api/attack/simulate"
echo "  完整测试: ./test_phase2_fixed.sh"
echo ""
echo "⚠️  停止系统："
echo "  kill $GANACHE_PID $BACKEND_PID $FRONTEND_PID"
echo ""
echo "🎯 请在浏览器中访问: http://localhost:5173"
echo ""

# 创建停止脚本
cat > stop-phase3.sh << 'EOF'
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
EOF

chmod +x stop-phase3.sh

echo "💡 提示: 运行 ./stop-phase3.sh 来停止所有服务"
echo ""
echo "🔄 系统正在运行中... (按 Ctrl+C 停止脚本监控)"

# 保持脚本运行
trap "echo ''; echo '🛑 停止系统...'; ./stop-phase3.sh; exit 0" INT

# 持续监控服务状态
while true; do
    sleep 30
    if ! kill -0 $GANACHE_PID 2>/dev/null; then
        echo "❌ Ganache 进程意外停止"
        break
    fi
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend 进程意外停止"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Frontend 进程意外停止"
        break
    fi
done

echo "🛑 系统监控结束"