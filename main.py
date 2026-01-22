#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
【兼容性启动脚本】
用于向后兼容旧的部署方式（如直接运行 python main.py）。
新版代码已迁移至 src/ 目录，此脚本会将调用转发到 src/main.py。

推荐使用新的启动脚本：
- Windows: run.bat
- Mac/Linux: ./start.sh
"""
import sys
import os
from pathlib import Path

# 将 src 目录添加到 Python 搜索路径
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    try:
        # 导入 src.main 模块的主函数
        from main import main
        
        # 运行主函数
        sys.exit(main())
        
    except ImportError as e:
        print(f"Error: 无法加载核心模块。请确保 src/ 目录完整。\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: 程序运行异常: {e}")
        sys.exit(1)
