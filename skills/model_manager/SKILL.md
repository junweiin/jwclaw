# skill: model_manager

## 描述
管理LLM模型配置，包括查看、切换和添加模型。支持多个模型的配置和快速切换。

## 调用格式
tool: model_manager("操作", "参数")

操作类型：
- "list" - 列出所有可用模型
- "switch" - 切换到指定模型
- "add" - 添加新模型配置
- "current" - 显示当前使用的模型

## 执行代码
```python
import json
import os

try:
    # 获取操作类型
    action = args[0].strip() if args else "list"
    param = args[1].strip() if len(args) > 1 else ""
    
    # 配置文件路径
    config_path = r"C:\Users\jw\Desktop\agent\config.json"
    models_path = r"C:\Users\jw\Desktop\agent\models.json"
    
    # 加载当前配置
    with open(config_path, 'r', encoding='utf-8') as f:
        current_config = json.load(f)
    
    # 加载模型列表（如果存在）
    if os.path.exists(models_path):
        with open(models_path, 'r', encoding='utf-8') as f:
            models = json.load(f)
    else:
        # 初始化模型列表
        models = {
            "models": [
                {
                    "name": "google/gemma-4-e2b",
                    "api_base": "http://192.168.2.114:1234/v1",
                    "api_key": "lm-studio",
                    "description": "Gemma 4 E2B - 本地LM Studio"
                }
            ],
            "current": "google/gemma-4-e2b"
        }
        with open(models_path, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
    
    # 执行操作
    if action == "list":
        # 列出所有模型
        result_lines = ["📋 可用模型列表:", "=" * 50]
        for i, model in enumerate(models["models"], 1):
            current_marker = " ✅ (当前)" if model["name"] == models["current"] else ""
            result_lines.append(f"{i}. {model['name']}{current_marker}")
            result_lines.append(f"   API: {model['api_base']}")
            if model.get('description'):
                result_lines.append(f"   说明: {model['description']}")
            result_lines.append("")
        
        result = "\n".join(result_lines)
    
    elif action == "current":
        # 显示当前模型
        current_model_name = models["current"]
        current_model = next((m for m in models["models"] if m["name"] == current_model_name), None)
        
        if current_model:
            result = f"🎯 当前使用的模型:\n\n"
            result += f"名称: {current_model['name']}\n"
            result += f"API地址: {current_model['api_base']}\n"
            result += f"API密钥: {current_model['api_key']}\n"
            if current_model.get('description'):
                result += f"说明: {current_model['description']}"
        else:
            result = f"⚠️  当前模型 '{current_model_name}' 未在列表中找到"
    
    elif action == "switch":
        # 切换模型
        if not param:
            result = "❌ 错误: 请指定要切换的模型名称"
        else:
            # 查找模型
            target_model = next((m for m in models["models"] if m["name"] == param or m["name"].lower() == param.lower()), None)
            
            if target_model:
                # 更新当前配置
                current_config["model"] = target_model["name"]
                current_config["api_base"] = target_model["api_base"]
                current_config["api_key"] = target_model["api_key"]
                
                # 保存配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(current_config, f, indent=2, ensure_ascii=False)
                
                # 更新模型列表中的当前模型
                models["current"] = target_model["name"]
                with open(models_path, 'w', encoding='utf-8') as f:
                    json.dump(models, f, indent=2, ensure_ascii=False)
                
                result = f"✅ 已切换到模型: {target_model['name']}\n\n"
                result += f"API地址: {target_model['api_base']}\n"
                if target_model.get('description'):
                    result += f"说明: {target_model['description']}\n\n"
                result += "⚠️  注意: 需要重启JwClaw才能生效"
            else:
                available = ", ".join([m["name"] for m in models["models"]])
                result = f"❌ 错误: 找不到模型 '{param}'\n\n可用模型: {available}"
    
    elif action == "add":
        # 添加新模型（需要JSON格式的参数）
        if not param:
            result = "❌ 错误: 请提供模型配置的JSON字符串\n\n示例:\n{\"name\": \"gpt-4\", \"api_base\": \"https://api.openai.com/v1\", \"api_key\": \"sk-xxx\", \"description\": \"GPT-4\"}"
        else:
            try:
                new_model = json.loads(param)
                
                # 验证必需字段
                required_fields = ["name", "api_base", "api_key"]
                missing = [f for f in required_fields if f not in new_model]
                
                if missing:
                    result = f"❌ 错误: 缺少必需字段: {', '.join(missing)}"
                else:
                    # 检查是否已存在
                    existing = next((m for m in models["models"] if m["name"] == new_model["name"]), None)
                    if existing:
                        result = f"⚠️  模型 '{new_model['name']}' 已存在，将更新配置"
                        models["models"].remove(existing)
                    
                    # 添加新模型
                    models["models"].append(new_model)
                    
                    # 保存
                    with open(models_path, 'w', encoding='utf-8') as f:
                        json.dump(models, f, indent=2, ensure_ascii=False)
                    
                    result = f"✅ 已添加模型: {new_model['name']}\n\n"
                    result += f"API地址: {new_model['api_base']}\n"
                    if new_model.get('description'):
                        result += f"说明: {new_model['description']}"
            except json.JSONDecodeError as e:
                result = f"❌ 错误: JSON格式无效 - {str(e)}"
    
    else:
        result = f"❌ 未知操作: {action}\n\n可用操作: list, switch, add, current"
        
except Exception as e:
    result = f"❌ 执行出错: {str(e)}"
```
