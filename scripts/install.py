#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JwClaw 安装脚本
自动注册到系统 PATH，使命令全局可用
"""

import os
import sys
import shutil
from pathlib import Path


def get_install_dir():
    """获取安装目录"""
    if sys.platform == "win32":
        # Windows: 使用 %LOCALAPPDATA%\JwClaw
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        # macOS/Linux: 使用 ~/.local/share/jwclaw
        base_dir = Path.home() / ".local" / "share"
    
    install_dir = base_dir / "jwclaw"
    return install_dir


def get_bin_dir():
    """获取可执行文件目录"""
    if sys.platform == "win32":
        # Windows: 使用 %LOCALAPPDATA%\JwClaw\bin
        return get_install_dir() / "bin"
    else:
        # macOS/Linux: 使用 ~/.local/bin
        return Path.home() / ".local" / "bin"


def copy_files(install_dir):
    """复制项目文件到安装目录"""
    print(f"📁 安装目录: {install_dir}")
    install_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取项目根目录（scripts/../）
    source_dir = Path(__file__).parent.parent.resolve()
    
    # 需要复制的文件和目录
    items_to_copy = [
        "src",
        "requirements.txt",
        "config.json",
        "skills",
        "workspace",
    ]
    
    for item in items_to_copy:
        source = source_dir / item
        target = install_dir / item
        
        if source.exists():
            if source.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(source, target)
                print(f"  📂 {item}/")
            else:
                shutil.copy2(source, target)
                print(f"  📄 {item}")
        else:
            print(f"  ⚠️  跳过: {item} (不存在)")
    
    return install_dir


def create_launcher(bin_dir, install_dir):
    """创建启动器脚本"""
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    if sys.platform == "win32":
        # Windows: 创建 jwclaw.bat
        launcher = bin_dir / "jwclaw.bat"
        launcher_content = f'''@echo off
python -m jwclaw %*
'''
        launcher.write_text(launcher_content, encoding='utf-8')
        print(f"  📄 创建: {launcher}")
        
        # 同时创建 PowerShell 版本
        ps_launcher = bin_dir / "jwclaw.ps1"
        ps_content = f'''python -m jwclaw $args
'''
        ps_launcher.write_text(ps_content, encoding='utf-8')
        print(f"  📄 创建: {ps_launcher}")
        
    else:
        # macOS/Linux: 创建 jwclaw shell 脚本
        launcher = bin_dir / "jwclaw"
        launcher_content = f'''#!/bin/bash
python3 -m jwclaw "$@"
'''
        launcher.write_text(launcher_content, encoding='utf-8')
        launcher.chmod(0o755)  # 添加执行权限
        print(f"  📄 创建: {launcher}")


def add_to_path(bin_dir):
    """添加到系统 PATH"""
    bin_str = str(bin_dir)
    
    if sys.platform == "win32":
        # Windows: 修改注册表或用户环境变量
        try:
            import winreg
            
            # 打开用户环境变量
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Environment",
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            )
            
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except WindowsError:
                current_path = ""
            
            # 检查是否已存在
            if bin_str.lower() not in current_path.lower():
                new_path = f"{current_path};{bin_str}" if current_path else bin_str
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                print(f"✅ 已添加到 PATH: {bin_dir}")
                print("⚠️  请重启终端或运行 'refreshenv' 使更改生效")
            else:
                print(f"ℹ️  已存在于 PATH: {bin_dir}")
            
            winreg.CloseKey(key)
            
        except Exception as e:
            print(f"⚠️  自动添加 PATH 失败: {e}")
            print(f"请手动添加以下路径到系统 PATH:")
            print(f"  {bin_dir}")
    else:
        # macOS/Linux: 修改 shell 配置文件
        shell_rc = None
        shell = os.environ.get("SHELL", "")
        
        if "zsh" in shell:
            shell_rc = Path.home() / ".zshrc"
        elif "bash" in shell:
            shell_rc = Path.home() / ".bashrc"
        else:
            # 尝试检测
            for rc_file in [".zshrc", ".bashrc", ".bash_profile"]:
                rc_path = Path.home() / rc_file
                if rc_path.exists():
                    shell_rc = rc_path
                    break
        
        if shell_rc:
            rc_content = shell_rc.read_text(encoding='utf-8') if shell_rc.exists() else ""
            path_export = f'export PATH="{bin_str}:$PATH"'
            
            if bin_str not in rc_content:
                with open(shell_rc, 'a', encoding='utf-8') as f:
                    f.write(f"\n# JwClaw\n{path_export}\n")
                print(f"✅ 已添加到 {shell_rc}")
                print(f"请运行: source {shell_rc}")
            else:
                print(f"ℹ️  已存在于 {shell_rc}")
        else:
            print(f"⚠️  无法检测 shell 配置文件")
            print(f"请手动添加以下路径到 PATH:")
            print(f"  {bin_str}")


def install_dependencies(install_dir):
    """安装依赖"""
    req_file = install_dir / "requirements.txt"
    if req_file.exists():
        print("📦 安装依赖...")
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ 依赖安装完成")
        else:
            print(f"⚠️  依赖安装失败: {result.stderr}")


def main():
    print("=" * 50)
    print("🤖 JwClaw 安装程序")
    print("=" * 50)
    print()
    
    # 检查 Python 版本
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        sys.exit(1)
    
    # 获取目录
    install_dir = get_install_dir()
    bin_dir = get_bin_dir()
    
    print(f"系统: {sys.platform}")
    print(f"Python: {sys.version.split()[0]}")
    print()
    
    # 确认安装
    response = input(f"将安装到: {install_dir}\n确认安装? [Y/n]: ").strip().lower()
    if response and response not in ('y', 'yes'):
        print("已取消安装")
        sys.exit(0)
    
    print()
    print("🚀 开始安装...")
    print()
    
    # 1. 复制文件
    print("📋 复制文件...")
    copy_files(install_dir)
    print()
    
    # 2. 安装依赖
    install_dependencies(install_dir)
    print()
    
    # 3. 创建启动器
    print("🔧 创建启动器...")
    create_launcher(bin_dir, install_dir)
    print()
    
    # 4. 添加到 PATH
    print("📝 配置环境变量...")
    add_to_path(bin_dir)
    print()
    
    print("=" * 50)
    print("✅ 安装完成!")
    print("=" * 50)
    print()
    print("使用方法:")
    print("  jwclaw              # 启动交互模式")
    print("  jwclaw --help       # 查看帮助")
    print()
    print("配置文件:")
    print(f"  {install_dir / 'config.json'}")
    print()
    print("如需卸载，删除以下目录:")
    print(f"  {install_dir}")
    if sys.platform != "win32":
        print(f"  并从 ~/.bashrc 或 ~/.zshrc 中移除 PATH 配置")


if __name__ == "__main__":
    main()
