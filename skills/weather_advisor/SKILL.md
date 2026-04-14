---
name: weather-advisor
description: "天气顾问。智能天气顾问。实时天气查询、未来7天预报、穿衣建议与出行活动推荐 Keywords: 天气查询, weather, 穿衣建议, 出行提醒."
---

## 概述

智能天气顾问。实时天气查询、未来7天预报、穿衣建议与出行活动推荐 适用于查看实时天气信息等场景。

## 适用范围

**适用场景**：
- 查看实时天气信息
- 获取穿衣建议
- 了解极端天气预警

**不适用场景**：
- 需要实时硬件控制或低延迟响应的场景
- 涉及敏感个人隐私数据的未授权处理

**触发关键词**: 天气查询, weather, 穿衣建议, 出行提醒

## 前置条件

```bash
pip install requests
```

> ⚠️ 首次使用前请确认依赖已安装，否则脚本将无法运行。

## 核心能力

### 能力1：实时天气——温度/湿度/风力/空气质量
实时天气——温度/湿度/风力/空气质量

### 能力2：穿衣建议——基于天气的着装推荐
穿衣建议——基于天气的着装推荐

### 能力3：出行提醒——极端天气预警与活动建议
出行提醒——极端天气预警与活动建议


## 命令列表

| 命令 | 说明 | 用法 |
|------|------|------|
| `now` | 查看天气 | `python3 scripts/weather_advisor_tool.py now [参数]` |
| `outfit` | 穿衣建议 | `python3 scripts/weather_advisor_tool.py outfit [参数]` |
| `alert` | 天气预警 | `python3 scripts/weather_advisor_tool.py alert [参数]` |


## 处理步骤

### Step 1：查看天气

**目标**：查看当前天气

**为什么这一步重要**：这是整个工作流的数据采集/初始化阶段，确保后续步骤基于准确的输入。

**执行**：
```bash
python3 scripts/weather_advisor_tool.py now --city Beijing
```

**检查点**：确认输出包含预期数据，无报错信息。

### Step 2：穿衣建议

**目标**：获取穿衣建议

**为什么这一步重要**：核心处理阶段，将原始数据转化为有价值的输出。

**执行**：
```bash
python3 scripts/weather_advisor_tool.py outfit --city Beijing --activity outdoor
```

**检查点**：确认生成结果格式正确，内容完整。

### Step 3：天气预警

**目标**：查看天气预警

**为什么这一步重要**：最终输出阶段，将处理结果以可用的形式呈现。

**执行**：
```bash
python3 scripts/weather_advisor_tool.py alert --city Beijing --days 3
```

**检查点**：确认最终输出符合预期格式和质量标准。

## 验证清单

- [ ] 依赖已安装：`pip install requests`
- [ ] Step 1 执行无报错，输出数据完整
- [ ] Step 2 处理结果符合预期格式
- [ ] Step 3 最终输出质量达标
- [ ] 无敏感信息泄露（API Key、密码等）

## 输出格式

```markdown
# 📊 天气顾问报告

**生成时间**: YYYY-MM-DD HH:MM

## 核心发现
1. [关键发现1]
2. [关键发现2]
3. [关键发现3]

## 数据概览
| 指标 | 数值 | 趋势 | 评级 |
|------|------|------|------|
| 指标A | XXX | ↑ | ⭐⭐⭐⭐ |
| 指标B | YYY | → | ⭐⭐⭐ |

## 详细分析
[基于实际数据的多维度分析内容]

## 行动建议
| 优先级 | 建议 | 预期效果 |
|--------|------|----------|
| 🔴 高 | [具体建议] | [量化预期] |
| 🟡 中 | [具体建议] | [量化预期] |
```

## 参考资料

### 原有链接
- [OpenWeatherMap](https://openweathermap.org/)

### GitHub
- [weather-api](https://github.com/topics/weather-api)

### 小红书
- [天气穿搭指南](https://www.xiaohongshu.com/explore/weather-outfit)

## 注意事项

- 所有分析基于脚本获取的实际数据，**不编造数据**
- 数据缺失字段标注"数据不可用"而非猜测
- 建议结合人工判断使用，AI分析仅供参考
- 首次使用请先安装依赖：`pip install requests`
- 如遇到API限流，请适当增加请求间隔

## 执行代码
```python
import subprocess
import sys
import os
from pathlib import Path

try:
    # 解析参数
    query = args[0].strip() if args and args[0].strip() else "今天天气"
    
    # 确定城市（默认北京）
    city = "Beijing"
    if len(args) > 1 and args[1].strip():
        city = args[1].strip()
    
    # 确定命令类型
    command = "now"
    if "穿衣" in query or "outfit" in query.lower() or "穿" in query:
        command = "outfit"
    elif "预警" in query or "alert" in query.lower() or "警" in query:
        command = "alert"
    
    # 动态查找脚本路径
    # 从当前执行环境推断 skills 目录位置
    possible_paths = [
        # 相对于当前工作目录
        Path("skills/weather_advisor/scripts/weather_advisor_tool.py"),
        Path("weather_advisor/scripts/weather_advisor_tool.py"),
        # 相对于脚本位置（如果知道）
        Path(__file__).parent / "scripts" / "weather_advisor_tool.py" if '__file__' in dir() else None,
    ]
    
    script_path = None
    for p in possible_paths:
        if p and p.exists():
            script_path = str(p.resolve())
            break
    
    # 如果找不到，使用相对路径尝试
    if not script_path:
        script_path = "skills/weather_advisor/scripts/weather_advisor_tool.py"
    
    # 检查脚本是否存在
    if not os.path.exists(script_path):
        # 脚本不存在，提供备用方案 - 使用在线天气服务链接
        result_lines = [
            f"🌤️  天气查询",
            f"━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"⚠️  本地天气工具未配置",
            f"",
            f"您可以通过以下方式查看天气:",
            f"",
            f"📎 中国天气网: http://www.weather.com.cn/",
            f"📎 百度天气: https://www.baidu.com/s?wd={city}+天气",
            f"📎 Bing天气: https://www.bing.com/search?q=weather+{city}",
            f"",
            f"💡 提示: 如需启用本地天气查询，请确保文件存在:",
            f"   skills/weather_advisor/scripts/weather_advisor_tool.py",
        ]
        result = "\n".join(result_lines)
    else:
        # 执行Python脚本
        cmd = [sys.executable, script_path, command, "--city", city]
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        
        if process.returncode == 0:
            # 解析JSON结果并格式化输出
            import json
            try:
                data = json.loads(process.stdout)
                if data.get("status") == "success":
                    current = data.get("current", {})
                    city_name = data.get("city", "未知城市")
                    timestamp = data.get("timestamp", "")
                    
                    result_lines = [
                        f"🌤️  {city_name} 实时天气",
                        f"━━━━━━━━━━━━━━━━━━━━━━",
                        f"📅 时间: {timestamp}",
                        f"🌡️  温度: {current.get('temperature', 'N/A')}",
                        f"💨 体感: {current.get('feels_like', 'N/A')}",
                        f"💧 湿度: {current.get('humidity', 'N/A')}",
                        f"🌬️  风速: {current.get('wind_speed', 'N/A')}",
                        f"☁️  天气: {current.get('weather', 'N/A')}",
                        f"🌧️  降水: {current.get('precipitation', 'N/A')}",
                    ]
                    result = "\n".join(result_lines)
                else:
                    result = f"❌ 查询失败: {data.get('message', '未知错误')}"
            except json.JSONDecodeError:
                result = process.stdout.strip()
        else:
            error_msg = process.stderr.strip() if process.stderr else "未知错误"
            result = f"❌ 执行失败: {error_msg}\n\n提示: 请确保已安装依赖 `pip install requests`"
            
except Exception as e:
    result = f"❌ 执行出错: {str(e)}"
```
