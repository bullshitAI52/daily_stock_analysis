@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo    A股分析系统 - Windows 环境安装脚本
echo ==========================================

:: 1. 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+ 并添加到 PATH 环境变量。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b
)

:: 2. 创建虚拟环境
if not exist "venv" (
    echo [1/3] 正在创建虚拟环境...
    python -m venv venv
) else (
    echo [1/3] 虚拟环境已存在，跳过创建。
)

:: 3. 激活环境并安装依赖
echo [2/3] 正在激活虚拟环境并安装依赖...
call venv\Scripts\activate

echo 正在安装依赖 (使用清华镜像源)...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
    echo.
    echo [错误] 依赖安装失败，请检查网络连接。
    pause
    exit /b
)

echo.
echo [3/3] 安装完成！
echo.
echo ==========================================
echo    环境准备就绪！
echo    请双击 run.bat 启动程序
echo ==========================================
pause
