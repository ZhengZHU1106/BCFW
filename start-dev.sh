#!/bin/bash

echo "🚀 启动区块链智能安防平台开发环境"
echo "=" * 50

# 检查Ganache是否已安装
if ! command -v ganache &> /dev/null; then
    echo "📦 安装Ganache..."
    npm install -g ganache
fi

echo "🔗 启动Ganache区块链..."
echo "助记词: bulk tonight audit hover toddler orange boost twenty biology flower govern soldier"
echo "RPC: http://127.0.0.1:8545"
echo ""

# 启动Ganache（后台运行）
ganache \
  --mnemonic "bulk tonight audit hover toddler orange boost twenty biology flower govern soldier" \
  --blockTime 5 \
  --host 127.0.0.1 \
  --port 8545 \
  --accounts 10 \
  --defaultBalanceEther 1000 \
  --deterministic \
  --quiet &

GANACHE_PID=$!
echo "Ganache进程ID: $GANACHE_PID"

# 等待Ganache启动
sleep 3

echo "🧪 测试连接..."
cd test && python3 test_ganache_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 开发环境启动成功！"
    echo ""
    echo "📚 可用命令:"
    echo "   后端服务: npm run backend"
    echo "   前端服务: npm run frontend" 
    echo "   停止区块链: kill $GANACHE_PID"
    echo ""
    echo "按 Ctrl+C 停止开发环境"
    
    # 保持脚本运行
    trap "echo ''; echo '🛑 停止开发环境...'; kill $GANACHE_PID; exit" INT
    wait $GANACHE_PID
else
    echo "❌ 连接测试失败，停止Ganache"
    kill $GANACHE_PID
    exit 1
fi