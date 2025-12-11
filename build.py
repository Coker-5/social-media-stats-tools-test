#!/usr/bin/env python3
"""
一键打包脚本
"""
import os
import shutil
import platform

# 自动检测操作系统
is_windows = platform.system() == "Windows"
separator = ";" if is_windows else ":"

# 清理旧的打包文件
if os.path.exists("dist"):
    shutil.rmtree("dist", ignore_errors=True)
if os.path.exists("build"):
    shutil.rmtree("build", ignore_errors=True)

# 执行打包命令
cmd = f'pyinstaller --onefile --add-data="config/config.json{separator}config" starter.py'
print(f"执行命令: {cmd}")
os.system(cmd)

# 检查是否成功
if os.path.exists("dist"):
    exe_name = "starter.exe" if is_windows else "starter"
    exe_path = os.path.join("dist", exe_name)

    if os.path.exists(exe_path):
        print(f"✅ 打包成功！")
        print(f"📁 可执行文件: {exe_path}")
        print("\n📦 分享给别人的文件:")
        print(f"  1. {exe_path}")
        print(f"  2. config/ 文件夹 (包含 config.json)")
        print("\n📁 最终文件夹结构:")
        print("  ├── starter (或 starter.exe)")
        print("  └── config/")
        print("      └── config.json")
    else:
        print("❌ 打包失败，未找到可执行文件")
else:
    print("❌ 打包失败")