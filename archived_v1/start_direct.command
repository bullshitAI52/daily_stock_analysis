#!/bin/bash

# 获取脚本所在目录并进入
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}   A股分析系统 - Mac (Python直接运行版)   ${NC}"
echo -e "${BLUE}=========================================${NC}"

echo "当前工作目录: $(pwd)"

# 1. 检查 Python 环境
echo -e "\n${BLUE}[1/4] 正在检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误：未找到 Python 3！${NC}"
    echo "请安装 Python 3.8 或以上版本。"
    echo "下载地址: https://www.python.org/downloads/"
    read -p "按任意键退出..."
    exit 1
fi
python3 --version

# 2. 检查并配置虚拟环境
echo -e "\n${BLUE}[2/4] 正在检查并配置虚拟环境...${NC}"
VENV_DIR="$DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 检查并安装依赖
echo -e "正在安装依赖 (需要网络)..."
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 依赖安装失败，请检查网络连接。${NC}"
    read -p "按任意键退出..."
    exit 1
fi

# 3. 检查代码更新
echo -e "\n${BLUE}[3/4] 正在检查代码更新...${NC}"
git pull

# 4. 启动程序
echo -e "\n${BLUE}[4/4] 正在启动系统...${NC}"
echo -e "${GREEN}WebUI 将在浏览器中自动打开：http://localhost:8000${NC}"

# 设置 WebUI 端口，防止冲突 (默认8000)
export PORT=8000

# 自动打开浏览器 (延迟2秒)
(sleep 3 && open "http://localhost:$PORT") &

# 启动主程序 (WebUI模式)
python v2_enhanced/main.py --webui-only

# 退出提示
echo -e "\n${RED}程序已退出。${NC}"
read -p "按任意键关闭..."
