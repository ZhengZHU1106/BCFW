#!/bin/bash
# BCFW 项目清理脚本
# 用途: 清理临时文件、Python缓存和旧备份
# 使用: ./scripts/cleanup_project.sh [--deep]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================"
echo "🧹 BCFW 项目清理脚本"
echo "========================================"
echo ""

# 参数解析
DEEP_CLEAN=false
if [[ "$1" == "--deep" ]]; then
    DEEP_CLEAN=true
    echo "⚠️  深度清理模式（包含node_modules）"
else
    echo "✅ 安全清理模式"
fi
echo ""

# 1. 清理Python缓存
echo "🐍 清理Python缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo "   ✅ Python缓存已清理"

# 2. 清理旧备份（保留最新1个）
if [ -d ".backups" ]; then
    echo "📦 清理旧备份..."
    cd .backups
    BACKUP_COUNT=$(ls -1 | wc -l)
    if [ "$BACKUP_COUNT" -gt 1 ]; then
        ls -t | tail -n +2 | xargs rm -rf
        KEPT=$(ls -1)
        echo "   ✅ 已保留最新备份: $KEPT"
    else
        echo "   ℹ️  仅有1个备份，无需清理"
    fi
    cd "$PROJECT_ROOT"
fi

# 3. 清理临时日志
echo "📝 清理临时日志..."
rm -f /tmp/system_start*.log
rm -f /tmp/devlechain_password.txt
rm -f /tmp/devlechain_pwd
rm -f /tmp/bootstrap.log
rm -f /tmp/check_*.py
rm -f /tmp/diagnose_*.py
rm -f /tmp/cleanup_summary.md
echo "   ✅ 临时日志已清理"

# 4. 清理旧数据库备份
if [ -f "backend/security_platform.db" ]; then
    echo "💾 发现旧数据库文件..."
    read -p "   删除 backend/security_platform.db? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f backend/security_platform.db
        echo "   ✅ 旧数据库已删除"
    else
        echo "   ℹ️  已跳过"
    fi
fi

# 5. 深度清理（可选）
if [ "$DEEP_CLEAN" = true ]; then
    echo ""
    echo "⚠️  深度清理模式"

    # 清理node_modules
    if [ -d "frontend/node_modules" ]; then
        echo "📦 清理node_modules..."
        read -p "   删除 frontend/node_modules (137 MB)? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf frontend/node_modules
            echo "   ✅ node_modules已删除"
            echo "   ℹ️  恢复命令: cd frontend && npm install"
        else
            echo "   ℹ️  已跳过"
        fi
    fi

    # 清理前端构建产物
    if [ -d "frontend/dist" ]; then
        rm -rf frontend/dist
        echo "   ✅ 前端构建产物已清理"
    fi

    # 清理PDF
    if [ -f "survey_blockchain.pdf" ]; then
        echo "📄 发现PDF文档..."
        read -p "   删除 survey_blockchain.pdf (2.1 MB)? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f survey_blockchain.pdf
            echo "   ✅ PDF文档已删除"
        else
            echo "   ℹ️  已跳过"
        fi
    fi
fi

echo ""
echo "========================================"
echo "✅ 清理完成！"
echo "========================================"

# 显示清理后的磁盘使用情况
echo ""
echo "📊 当前项目大小:"
du -sh "$PROJECT_ROOT" 2>/dev/null || true

echo ""
echo "💡 提示:"
echo "   - 定期清理: ./scripts/cleanup_project.sh"
echo "   - 深度清理: ./scripts/cleanup_project.sh --deep"
echo "   - 重置环境: ./scripts/reset_poa_demo.sh"
