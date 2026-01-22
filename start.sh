#!/bin/bash
# ==========================================
# 🚀 A股分析系统一键启动脚本
# ==========================================

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}正在启动 A股自选股智能分析系统...${NC}"

# 1. 检查是否在正确目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}错误：未找到 docker-compose.yml 文件！${NC}"
    echo "请确保您在 /opt/stock-analyzer-new/daily_stock_analysis 目录下运行此脚本"
    exit 1
fi

# 2. 拉取最新代码 (可选，如果不想自动更新可注释掉)
echo "正在检查代码更新..."
git pull

# 3. 启动服务
echo "正在启动 Docker 服务..."
# 强制重新构建以确保代码最新
docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
    echo -e "WebUI 地址: ${GREEN}http://HostIP:8088${NC}"
    
    # 4. 询问是否查看日志
    read -p "是否查看运行日志？(y/n) " view_logs
    if [[ "$view_logs" == "y" ]]; then
        docker-compose logs -f
    fi
else
    echo -e "${RED}❌ 服务启动失败，请检查报错信息${NC}"
fi
