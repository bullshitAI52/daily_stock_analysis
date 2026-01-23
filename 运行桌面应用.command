#!/bin/bash

# 获取脚本所在目录
CD="$(cd "$(dirname "$0")" && pwd)"

# 应用路径
APP_PATH="$CD/desktop/src-tauri/target/release/bundle/macos/desktop.app"

# 如果应用不存在，提示用户
if [ ! -d "$APP_PATH" ]; then
    echo "❌ 应用未找到，请先构建桌面应用"
    echo "路径: $APP_PATH"
    exit 1
fi

# 先杀掉可能在运行的旧进程
echo "🧹 清理旧进程..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
pkill -f "python.*webui" 2>/dev/null || true

# 移除隔离属性
echo "🔧 正在移除隔离属性..."
xattr -cr "$APP_PATH"

# 打开应用
echo "🚀 正在启动桌面应用..."
open "$APP_PATH"

echo "✅ 应用已启动！请等待几秒让后端服务启动"
echo "💡 提示：应用将在浏览器窗口中打开，右上角有 '⚙️ 设置 API' 按钮"
