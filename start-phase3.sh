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

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

# 创建日志目录
mkdir -p logs

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
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "✅ 后端API启动成功 (PID: $BACKEND_PID)"

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
cat > stop-phase3.sh << EOF
#!/bin/bash
echo "=== 🛑 停止区块链智能安防平台 ==="
echo "停止进程..."
kill $GANACHE_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
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