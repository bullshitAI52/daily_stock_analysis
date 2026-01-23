#!/bin/bash
# 进入脚本所在的目录（即项目目录）
cd "$(dirname "$0")"

# 激活虚拟环境
source venv/bin/activate

# 检查端口占用并清理
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 后台等待 2 秒后打开浏览器
(sleep 2 && open http://127.0.0.1:8000) &

# 启动 Python WebUI
echo "正在启动股票分析系统..."
echo "如浏览器未自动打开，请访问: http://127.0.0.1:8000"
python src/webui.py

# 保持窗口不关闭（可选，方便看日志）
# read -p "按回车键退出..."
