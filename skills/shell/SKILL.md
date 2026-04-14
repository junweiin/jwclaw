# skill: shell

## 描述
执行系统Shell命令（PowerShell/Bash），用于文件操作、系统查询、程序启动等任务。

## 调用格式
tool: shell("命令内容")

## 参数说明
- 命令内容: 要执行的Shell命令字符串

## 注意事项
- Windows系统使用PowerShell语法
- macOS/Linux系统使用Bash语法
- 命令会在安全沙箱中执行，禁止危险操作

## 执行代码
```python
import subprocess
import platform

try:
    command = args[0] if args else ""
    
    if not command:
        result = "错误: 请提供要执行的命令"
    else:
        system = platform.system()
        
        # 根据系统选择执行方式
        if system == "Windows":
            # Windows使用PowerShell
            cmd = f'powershell -NoProfile -Command "{command}"'
        else:
            # macOS/Linux使用Bash
            cmd = f'bash -c "{command}"'
        
        # 执行命令
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8',
            errors='replace'
        )
        
        if proc.returncode == 0:
            result = proc.stdout.strip() if proc.stdout.strip() else "执行成功（无输出）"
        else:
            error_msg = proc.stderr.strip() if proc.stderr.strip() else "未知错误"
            result = f"退出码:{proc.returncode}\n错误: {error_msg}"
            
except subprocess.TimeoutExpired:
    result = "执行超时（超过300秒）"
except Exception as e:
    result = f"执行出错: {str(e)}"
```
