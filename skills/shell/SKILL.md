# skill: shell

## 描述
在本地终端执行系统命令，完成文件操作、程序运行、系统查询等任务。支持Windows PowerShell、CMD以及Linux/macOS的bash命令。

## 调用格式
tool: shell("命令")

## 执行代码
```python
import subprocess
import sys
import os

try:
    # 获取要执行的命令
    command = args[0] if args else ""
    
    if not command:
        result = "错误: 请提供要执行的命令"
    else:
        # 安全检查：禁止执行危险命令
        dangerous_commands = [
            'rm -rf /', 'del /s /q C:\\', 'format c:', 'format d:', 'mkfs',
            ':(){ :|:& };:', 'chmod 777 /', 'sudo rm -rf'
        ]
        
        for dangerous in dangerous_commands:
            if dangerous.lower() in command.lower():
                result = f"⚠️  安全警告: 禁止执行危险命令 '{dangerous}'"
                break
        else:
            # 确定使用的shell
            if sys.platform == 'win32':
                # Windows系统使用PowerShell，添加-NoProfile提高速度
                shell_cmd = ['powershell', '-NoProfile', '-Command', command]
            else:
                # Linux/macOS使用bash
                shell_cmd = ['/bin/bash', '-c', command]
            
            try:
                # 执行命令，设置超时和输出限制
                process = subprocess.run(
                    shell_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30秒超时
                    encoding='utf-8',
                    errors='replace'  # 处理编码问题
                )
                
                # 构建结果报告
                output_lines = []
                
                if process.returncode == 0:
                    output_lines.append(f"✅ 命令执行成功")
                    output_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
                    
                    if process.stdout:
                        output_lines.append(f"\n📤 输出:")
                        # 限制输出长度，避免过长
                        stdout = process.stdout.strip()
                        if len(stdout) > 2000:
                            output_lines.append(stdout[:2000])
                            output_lines.append(f"\n... (输出过长，已截断)")
                        else:
                            output_lines.append(stdout)
                    else:
                        output_lines.append("(无输出)")
                else:
                    output_lines.append(f"❌ 命令执行失败 (退出码: {process.returncode})")
                    output_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
                    
                    if process.stderr:
                        output_lines.append(f"\n⚠️  错误信息:")
                        stderr = process.stderr.strip()
                        if len(stderr) > 1000:
                            output_lines.append(stderr[:1000])
                            output_lines.append(f"\n... (错误信息过长，已截断)")
                        else:
                            output_lines.append(stderr)
                
                result = "\n".join(output_lines)
                
            except subprocess.TimeoutExpired:
                result = "⏱️  命令执行超时（超过30秒），已自动终止"
            except FileNotFoundError:
                result = f"❌ 命令未找到: {command.split()[0]}\n提示: 请确认该命令已安装且在PATH中"
            except PermissionError:
                result = "⚠️  权限不足: 需要管理员权限才能执行此命令"
            except Exception as e:
                result = f"❌ 执行出错: {str(e)}"

except Exception as e:
    result = f"致命错误: {str(e)}"
```
