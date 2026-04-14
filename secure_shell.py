# -*- coding: utf-8 -*-
"""
secure_shell.py - 安全的Shell命令执行模块
参考Nanobot的安全设计理念，提供命令注入防护
"""

import subprocess
import shlex
import re
import sys
from typing import List, Tuple, Optional


class SecureShellExecutor:
    """安全的Shell命令执行器"""
    
    # 白名单命令（允许直接执行）
    SAFE_COMMANDS = {
        # Python相关
        "python", "python3", "pip", "pip3",
        
        # 版本控制和包管理
        "yt-dlp", "ffmpeg", "git", "node", "npm", "npx",
        
        # 系统查询
        "where", "which", "echo", "dir", "ls", "pwd", "whoami",
        "ipconfig", "ifconfig", "ping", "curl", "wget",
        "cat", "type", "find", "tree", "tasklist", "taskkill",
        
        # 包管理器
        "winget", "choco", "skillhub",
        
        # 文件操作
        "del", "rm", "rmdir", "rd", "move", "mv", "cp", "copy",
        "mkdir", "md", "cd", "ren", "rename",
        
        # Windows CMD内置命令
        "cmd", "powershell", "pwsh",
        
        # 其他工具
        "cls", "clear", "date", "time", "hostname",
    }
    
    # 危险命令模式（需要二次确认）
    DANGEROUS_PATTERNS = [
        r'\brm\s+-rf\s+/',           # rm -rf /
        r'\brm\s+-rf\s+~',           # rm -rf ~
        r'\bdel\s+/[fqs]\s+[a-z]:\\', # del /f C:\
        r'\bformat\b',                # format
        r'\bshutdown\b',              # shutdown
        r'\brd\s+/s\s+/q\s+[a-z]:\\', # rd /s /q C:\
        r'\bchmod\s+777\b',          # chmod 777
        r'\bsudo\b.*\brm\b',         # sudo rm
        r'>\s*/dev/null',            # 重定向到/dev/null
        r'\|\s*sh\b',                # | sh (管道执行)
        r';\s*rm\b',                 # ; rm (命令拼接)
        r'&&\s*rm\b',                # && rm
    ]
    
    # 工作空间限制（可选）
    def __init__(self, restrict_to_workspace: bool = False, workspace_path: str = None):
        self.restrict_to_workspace = restrict_to_workspace
        self.workspace_path = workspace_path
    
    def validate_command(self, cmd: str) -> Tuple[bool, str, str]:
        """
        验证命令安全性
        
        Returns:
            (is_safe, risk_level, message)
            - is_safe: 是否安全
            - risk_level: 'safe' | 'warning' | 'dangerous'
            - message: 提示信息
        """
        if not cmd or not cmd.strip():
            return False, 'dangerous', '命令为空'
        
        cmd_stripped = cmd.strip()
        
        # 1. 检查危险模式
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, cmd_stripped, re.IGNORECASE):
                return False, 'dangerous', f'检测到危险命令模式: {pattern}'
        
        # 2. 提取命令名
        try:
            # 尝试使用shlex分割（更安全）
            parts = shlex.split(cmd_stripped)
            cmd_name = parts[0].lower() if parts else ''
        except ValueError:
            # shlex失败时回退到简单分割
            cmd_name = cmd_stripped.split()[0].lower().split('/')[-1].split('\\')[-1]
        
        # 3. 检查工作空间限制
        if self.restrict_to_workspace and self.workspace_path:
            if not self._is_within_workspace(cmd_stripped):
                return False, 'dangerous', f'命令超出工作空间范围: {self.workspace_path}'
        
        # 4. 判断安全级别
        if cmd_name in self.SAFE_COMMANDS:
            return True, 'safe', f'[安全命令]: {cmd_stripped}'
        elif self._is_likely_safe(cmd_name):
            return True, 'safe', f'[可信命令]: {cmd_stripped}'
        else:
            return False, 'warning', f'[未知命令]: {cmd_stripped}，需要确认'
    
    def _is_likely_safe(self, cmd_name: str) -> bool:
        """判断命令是否可能是安全的（启发式）"""
        # 常见的前缀检查
        safe_prefixes = ['py', 'pip', 'npm', 'node', 'git']
        return any(cmd_name.startswith(p) for p in safe_prefixes)
    
    def _is_within_workspace(self, cmd: str) -> bool:
        """检查命令是否在工作空间范围内"""
        # 简单实现：检查路径参数
        path_pattern = r'[A-Z]:\\[^"\']+' if sys.platform == 'win32' else r'/[^"\']+' 
        paths = re.findall(path_pattern, cmd, re.IGNORECASE)
        
        if not paths:
            return True  # 没有路径参数，认为安全
        
        for path in paths:
            if not path.startswith(self.workspace_path):
                return False
        return True
    
    def execute(self, cmd: str, timeout: int = 120, 
                require_confirmation: bool = True) -> str:
        """
        执行命令
        
        Args:
            cmd: 命令字符串
            timeout: 超时时间（秒）
            require_confirmation: 是否需要用户确认
            
        Returns:
            执行结果
        """
        # 验证命令
        is_safe, risk_level, message = self.validate_command(cmd)
        
        print(f"\n{message}")
        
        # 根据风险级别决定是否需要确认
        if risk_level == 'dangerous':
            print("⚠️  这是危险命令！")
            confirm = input("确认执行? (输入 YES 确认): ").strip()
            if confirm != 'YES':
                return "用户取消执行危险命令"
        elif risk_level == 'warning' and require_confirmation:
            confirm = input("确认执行? (y/n): ").strip().lower()
            if confirm != 'y':
                return "用户取消执行"
        
        # 执行命令（Windows下使用shell模式以支持内置命令）
        try:
            # Windows下始终使用shell=True以支持dir、del等内置命令
            if sys.platform == 'win32':
                use_shell = True
                cmd_list = cmd
            else:
                # Unix/Linux尝试列表形式（更安全）
                try:
                    cmd_list = shlex.split(cmd)
                    use_shell = False
                except ValueError:
                    cmd_list = cmd
                    use_shell = True
            
            proc = subprocess.run(
                cmd_list,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
            
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            
            if proc.returncode != 0:
                if err:
                    return f"退出码:{proc.returncode}\n错误: {err}"
                else:
                    return f"退出码:{proc.returncode}\n{out}"
            else:
                return out if out else "执行成功（无输出）"
                
        except subprocess.TimeoutExpired:
            return f"命令执行超时 ({timeout}秒)"
        except FileNotFoundError:
            return f"命令未找到: {cmd.split()[0]}"
        except Exception as e:
            return f"执行出错: {str(e)}"


# 全局执行器实例
executor = SecureShellExecutor()


def run_shell_secure(cmd: str) -> str:
    """
    安全执行shell命令（供skill调用）
    
    Args:
        cmd: 命令字符串
        
    Returns:
        执行结果
    """
    return executor.execute(cmd)


# 向后兼容的接口
def run_shell(cmd: str) -> str:
    """旧接口，调用新的安全执行器"""
    return run_shell_secure(cmd)


if __name__ == "__main__":
    # 测试
    test_commands = [
        "echo hello",
        "python --version",
        "rm -rf /",  # 危险命令
        "ls -la",
    ]
    
    for cmd in test_commands:
        print(f"\n{'='*60}")
        print(f"测试命令: {cmd}")
        result = run_shell_secure(cmd)
        print(f"结果: {result[:200]}")
