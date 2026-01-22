# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# 收集所有需要的 metadata
datas = []
# datas += copy_metadata('sqlalchemy')
# datas += copy_metadata('tushare')
# datas += copy_metadata('akshare')

# 添加非代码文件
datas += [
    ('.env.example', '.'),
    ('README.md', '.'),
    ('scripts', 'scripts'),  # 如果有脚本依赖
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pandas', 
        'sqlalchemy',
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.ext.declarative',
        'tushare',
        'akshare',
        'schedule',
        'tenacity',
        'lark_oapi',
        'google.generativeai',
        'openai',
        'tavily',
        'requests',
        'bs4',
        'lxml',
        'openpyxl',
        'xlsxwriter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='stock_analysis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='stock_analysis',
)
