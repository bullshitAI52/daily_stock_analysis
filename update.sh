#!/bin/bash

# A股自选股智能分析系统 - 一键更新脚本
# 使用方法: ./update.sh

echo "======================================="
echo "   🚀 开始更新 A股自选股智能分析系统"
echo "======================================="

# 1. 更新代码
echo "git pulling..."
git pull
if [ $? -ne 0 ]; then
    echo "❌ 代码更新失败，请检查网络或 git 状态"
    exit 1
fi
echo "✅ 代码已更新到最新版本"

# 2. 检查并安装依赖 (防止 requirements.txt 有变更)
echo "Checking dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 依赖检查完成"
fi

# 3. 重启建议
echo "======================================="
echo "✅ 更新完成！请根据您的运行方式重启服务："
echo "======================================="

echo "👉 方式 A: 如果您正在使用终端运行 (python main.py)"
echo "   请按 Ctrl+C 停止当前程序，然后再次重新运行即可。"
echo ""
echo "👉 方式 B: 如果您使用 Docker"
echo "   请运行: docker-compose up -d --build"
echo ""
echo "👉 方式 C: 如果您使用 Systemd 后台服务"
echo "   请运行: sudo systemctl restart stock-analyzer"
echo ""
echo "👉 方式 D: 如果您使用 nohup 后台运行"
echo "   请运行: ps -ef | grep main.py | awk '{print \$2}' | xargs kill -9"
echo "   然后: nohup python main.py > output.log 2>&1 &"
