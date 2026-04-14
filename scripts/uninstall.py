#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JwClaw 卸载脚本
"""

import os
import sys
from pathlib import Path


def get_install_dir():
    """获取安装目录"""
    if sys.platform == "win32":
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base_dir = Path.home() / ".local" / "share"
    return base_dir / "jwclaw"


def get_bin_dir():
    """获取可执行文件目录"""
    if sys.platform == "win32":
        return get_install_dir().parent / "jwclaw" / "bin"
    else:
        return Path.home() / ".local" / "bin"


def remove_from_path_windows(bin_dir):
    """从 Windows PATH 中移除"""
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Environment",
            0,
            winreg.KEY_READ | winreg.KEY_WRITE
        )
        
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
            paths = current_path.split(';')
            new_paths = [p for p in paths if str(bin_dir).lower() not in p.lower()]
            new_path = ';'.join(new_paths)
            
            if new_path != current_path:
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                print("✅ 已从 PATH 中移除")
            else:
                print("ℹ️  PATH 中未找到")
                
        except WindowsError:
            print("ℹ️  PATH 为空")
        
        winreg.CloseKey(key)
        
    except Exception as e:
        print(f"⚠️  从 PATH 移除失败: {e}")


def remove_from_path_unix(bin_dir):
    """从 Unix shell 配置中移除"""
    bin_str = str(bin_dir)
    
    for rc_file in [".zshrc", ".bashrc", ".bash_profile"]:
        rc_path = Path.home() / rc_file
        if rc_path.exists():
            content = rc_path.read_text(encoding='utf-8')
            if bin_str in content or 'jwclaw' in content.lower():
                lines = content.split('\n')
                new_lines = []
                skip_next = False
                
                for line in lines:
                    if 'jwclaw' in line.lower() or (skip_next and line.strip() == ''):
                        skip_next = '# JwClaw' in line
                        continue
                    new_lines.append(line)
                
                rc_path.write_text('\n'.join(new_lines), encoding='utf-8')
                print(f"✅ 已从 {rc_file} 中移除")


def main():
    print("=" * 50)
    print("🗑️  JwClaw 卸载程序")
    print("=" * 50)
    print()
    
    install_dir = get_install_dir()
    bin_dir = get_bin_dir()
    
    if not install_dir.exists():
        print(f"❌ 未找到安装目录: {install_dir}")
        print("JwClaw 可能未安装或已被卸载")
        sys.exit(1)
    
    print(f"安装目录: {install_dir}")
    print(f"启动器目录: {bin_dir}")
    print()
    
    response = input("确认卸载? [y/N]: ").strip().lower()
    if response not in ('y', 'yes'):
        print("已取消卸载")
        sys.exit(0)
    
    print()
    print("🗑️  正在卸载...")
    
    # 1. 从 PATH 移除
    print("📝 清理环境变量...")
    if sys.platform == "win32":
        remove_from_path_windows(bin_dir)
    else:
        remove_from_path_unix(bin_dir)
    
    # 2. 删除文件
    print("🗑️  删除文件...")
    import shutil
    
    if install_dir.exists():
        shutil.rmtree(install_dir)
        print(f"✅ 已删除: {install_dir}")
    
    # 删除启动器
    if sys.platform == "win32":
        for launcher in ["jwclaw.bat", "jwclaw.ps1"]:
            launcher_path = bin_dir / launcher
            if launcher_path.exists():
                launcher_path.unlink()
                print(f"✅ 已删除: {launcher_path}")
    else:
        launcher_path = bin_dir / "jwclaw"
        if launcher_path.exists():
            launcher_path.unlink()
            print(f"✅ 已删除: {launcher_path}")
    
    print()
    print("=" * 50)
    print("✅ 卸载完成!")
    print("=" * 50)
    print()
    print("提示: 请重启终端或运行 'refreshenv'(Windows) / 'source ~/.bashrc'(Linux/macOS)")


if __name__ == "__main__":
    main()

