# skill: open_app

## 描述
打开应用程序或文件。支持Windows、macOS和Linux系统。可以打开浏览器、文档、文件夹等。

## 调用格式
tool: open_app("应用名称或路径")

## 命令列表
| 命令 | 说明 | 参数 |
|------|------|------|
| open_app | 打开应用程序或文件 | 应用名称或路径 |

参数说明：
- 应用名称：如 "chrome", "edge", "notepad", "code" 等
- 完整路径：如 "C:\Program Files\App\app.exe"

## 执行代码
```python
import subprocess
import sys
import os
import platform

try:
    app_name = args[0].strip() if args else ""
    
    if not app_name:
        result = "❌ 错误: 请提供要打开的应用程序名称或路径"
    else:
        system = platform.system()
        
        # Windows系统
        if system == "Windows":
            # 常见应用的映射
            app_mapping = {
                "chrome": "chrome",
                "edge": "msedge",
                "firefox": "firefox",
                "notepad": "notepad",
                "code": "code",
                "vscode": "code",
                "word": "winword",
                "excel": "excel",
                "powerpoint": "powerpnt",
                "calc": "calc",
            }
            
            # 检查是否是已知应用名
            app_cmd = app_mapping.get(app_name.lower(), app_name)
            
            # 如果是完整路径，直接使用
            if os.path.exists(app_name):
                cmd = f'start "" "{app_name}"'
            else:
                # 使用start命令打开应用
                cmd = f'start "" {app_cmd}'
            
            process = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if process.returncode == 0:
                result = f"✅ 已打开: {app_name}"
            else:
                error_msg = process.stderr.strip() if process.stderr else "未知错误"
                result = f"❌ 打开失败: {error_msg}\n\n提示: 请检查应用名称是否正确，或使用完整路径"
        
        # macOS系统
        elif system == "Darwin":
            if os.path.exists(app_name):
                cmd = ["open", app_name]
            else:
                cmd = ["open", "-a", app_name]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if process.returncode == 0:
                result = f"✅ 已打开: {app_name}"
            else:
                result = f"❌ 打开失败: {process.stderr.strip()}"
        
        # Linux系统
        else:
            cmd = ["xdg-open", app_name]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if process.returncode == 0:
                result = f"✅ 已打开: {app_name}"
            else:
                result = f"❌ 打开失败: {process.stderr.strip()}"
                
except Exception as e:
    result = f"❌ 执行出错: {str(e)}"
```
