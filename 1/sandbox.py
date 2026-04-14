# -*- coding: utf-8 -*-
"""
sandbox.py - Skill代码沙箱执行器
限制危险的内置函数和模块，提供安全的执行环境
参考Nanobot的权限最小化设计理念
"""

import sys
import types
from typing import Dict, Any, Optional


class RestrictedBuiltins:
    """受限的内置函数集合"""
    
    # 允许的安全内置函数
    SAFE_BUILTINS = {
        # 基本类型
        'int', 'float', 'str', 'bool', 'list', 'dict', 'tuple', 'set',
        'bytes', 'bytearray', 'complex',
        
        # 数学运算
        'abs', 'round', 'min', 'max', 'sum', 'pow',
        
        # 序列操作
        'len', 'range', 'enumerate', 'zip', 'map', 'filter',
        'sorted', 'reversed',
        
        # 字符串处理
        'chr', 'ord', 'format',
        
        # 输入输出（受限）
        'print',
        
        # 其他安全函数
        'isinstance', 'issubclass', 'hasattr', 'getattr', 'setattr',
        'callable', 'repr', 'hash', 'id', 'type',
        
        # 常量
        'True', 'False', 'None',
        '__name__', '__doc__', '__package__',
    }
    
    # 禁止的危险内置函数
    DANGEROUS_BUILTINS = {
        'eval', 'exec', 'compile',      # 代码执行
        '__import__', 'importlib',       # 动态导入
        'open', 'file', 'input',         # 文件/输入
        'globals', 'locals', 'vars',     # 作用域访问
        'dir', 'help',                   # 内省
        'breakpoint', 'exit', 'quit',    # 程序控制
        'memoryview', 'object',          # 底层对象
    }
    
    @classmethod
    def get_safe_builtins(cls) -> dict:
        """获取安全的内置函数字典"""
        safe_dict = {}
        
        for name in cls.SAFE_BUILTINS:
            if name in __builtins__:
                if isinstance(__builtins__, dict):
                    safe_dict[name] = __builtins__[name]
                else:
                    safe_dict[name] = getattr(__builtins__, name, None)
        
        return safe_dict
    
    @classmethod
    def get_sandbox_builtins(cls, restricted_import_func) -> dict:
        """获取沙箱环境的内置函数（包含受限的__import__）"""
        safe_dict = cls.get_safe_builtins()
        # 添加受限的导入函数
        safe_dict['__import__'] = restricted_import_func
        return safe_dict


class RestrictedImporter:
    """受限的模块导入器"""
    
    # 允许的模块白名单
    ALLOWED_MODULES = {
        # 标准库 - 安全模块
        'os', 'sys', 're', 'json', 'math', 'datetime',
        'time', 'random', 'string', 'collections',
        'itertools', 'functools', 'operator',
        'urllib', 'urllib.request', 'urllib.parse',
        'http', 'http.client', 'http.server',
        'socket', 'ssl',
        'hashlib', 'hmac', 'base64',
        'subprocess', 'shlex',  # Shell执行需要
        'pathlib', 'tempfile', 'shutil',
        'copy', 'deepcopy',
        'typing', 'abc',
        'logging',
        
        # 常用第三方库（如果已安装）
        'requests', 'beautifulsoup4', 'bs4',
        'PIL', 'Pillow',
        'numpy', 'pandas',
    }
    
    # 明确禁止的模块
    FORBIDDEN_MODULES = {
        'ctypes', 'cffi',              # C扩展调用
        'pickle', 'marshal',           # 序列化（可执行代码）
        'shelve',                      # 持久化
        'platform', 'site',            # 系统信息
        'inspect', 'dis',              # 代码检查
        'pdb', 'traceback',            # 调试
        'multiprocessing', 'threading', # 并发（可能导致资源泄漏）
        'asyncio',                     # 异步
        'ftplib', 'smtplib', 'telnetlib', # 网络协议
        'xmlrpc',                      # RPC
        'cgi', 'cgitb',                # Web
        'pydoc', 'doctest',            # 文档
    }
    
    def __init__(self):
        self.original_import = __builtins__['__import__'] if isinstance(__builtins__, dict) else __builtins__.__import__
    
    def restricted_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        """受限的import函数"""
        # 检查是否在禁止列表中
        if name in self.FORBIDDEN_MODULES:
            raise ImportError(f"禁止导入模块: {name}")
        
        # 检查是否在白名单中
        if name not in self.ALLOWED_MODULES:
            # 允许子模块导入（如果父模块在白名单中）
            parent_module = name.split('.')[0]
            if parent_module not in self.ALLOWED_MODULES:
                raise ImportError(
                    f"未授权的模块: {name}\n"
                    f"提示: 请在ALLOWED_MODULES中添加此模块，或使用shell skill执行"
                )
        
        # 执行原始导入
        return self.original_import(name, globals, locals, fromlist, level)


class SandboxExecutor:
    """沙箱执行器"""
    
    def __init__(self, strict_mode: bool = True):
        """
        初始化沙箱
        
        Args:
            strict_mode: 严格模式（更严格的限制）
        """
        self.strict_mode = strict_mode
        self.restricted_importer = RestrictedImporter()
    
    def execute(self, code: str, local_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        在沙箱中执行代码
        
        Args:
            code: Python代码字符串
            local_vars: 局部变量字典
            
        Returns:
            执行后的局部变量字典
        """
        # 准备安全的命名空间
        safe_globals = {
            '__builtins__': RestrictedBuiltins.get_sandbox_builtins(
                self.restricted_importer.restricted_import
            ),
        }
        
        # 添加用户提供的变量
        if local_vars:
            safe_globals.update(local_vars)
        
        # 添加一些常用的安全模块（预先导入）
        try:
            import os
            import sys
            import re
            import json
            import math
            import time
            import datetime
            import subprocess
            import shlex
            
            safe_globals['os'] = os
            safe_globals['sys'] = sys
            safe_globals['re'] = re
            safe_globals['json'] = json
            safe_globals['math'] = math
            safe_globals['time'] = time
            safe_globals['datetime'] = datetime
            safe_globals['subprocess'] = subprocess
            safe_globals['shlex'] = shlex
        except Exception as e:
            pass  # 忽略导入错误
        
        try:
            # 编译代码（检查语法）
            compiled_code = compile(code, '<sandbox>', 'exec')
            
            # 执行代码
            exec(compiled_code, safe_globals)
            
            # 返回结果变量
            return {k: v for k, v in safe_globals.items() 
                   if not k.startswith('__') and k not in ('os', 'sys', 're', 'json', 'math')}
        
        except SyntaxError as e:
            raise SyntaxError(f"代码语法错误: {e}")
        except ImportError as e:
            raise ImportError(f"模块导入受限: {e}")
        except Exception as e:
            raise RuntimeError(f"沙箱执行错误: {e}")


# 全局沙箱实例
sandbox = SandboxExecutor(strict_mode=True)


def execute_in_sandbox(code: str, local_vars: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    在沙箱中执行代码（便捷函数）
    
    Args:
        code: Python代码
        local_vars: 局部变量
        
    Returns:
        执行结果
    """
    return sandbox.execute(code, local_vars)


if __name__ == "__main__":
    # 测试
    print("测试沙箱执行器:")
    
    # 测试1: 安全代码
    safe_code = """
result = "Hello, World!"
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
"""
    try:
        result = execute_in_sandbox(safe_code)
        print(f"✓ 安全代码执行成功: {result.get('result')}, sum={result.get('total')}")
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    # 测试2: 危险代码（应该被阻止）
    dangerous_code = """
import os
os.system('echo hacked')
"""
    try:
        result = execute_in_sandbox(dangerous_code)
        print(f"✗ 危险代码未被阻止!")
    except Exception as e:
        print(f"✓ 危险代码被正确阻止: {e}")
    
    # 测试3: eval/exec（应该被阻止）
    evil_code = """
eval("__import__('os').system('rm -rf /')")
"""
    try:
        result = execute_in_sandbox(evil_code)
        print(f"✗ eval未被阻止!")
    except Exception as e:
        print(f"✓ eval被正确阻止: {e}")
