@echo off
chcp 65001 >nul
setlocal

echo ==========================================
echo    A股分析系统 - 启动脚本
echo ==========================================

:: 检查虚拟环境
if not exist "venv" (
    echo [提示] 未找到虚拟环境，正在尝试运行安装脚本...
    call install.bat
)

:: 激活虚拟环境
call venv\Scripts\activate

:: 设置 WebUI 端口
set PORT=8000

echo [信息] 正在启动系统...
echo [信息] WebUI 将在浏览器中自动打开: http://localhost:%PORT%

:: 异步打开浏览器 (等待 3 秒后打开)
start "" mshta vbscript:CreateObject("WScript.Shell").Run("powershell -c Start-Sleep -s 3; Start-Process 'http://localhost:%PORT%'",0,false)(window.close)

:: 启动主程序
python src/main.py --webui-only

pause
