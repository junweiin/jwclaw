# JwClaw 模型管理使用指南

## 🎯 功能概述

`model_manager` skill允许你管理多个LLM模型配置，包括：
- 查看所有可用模型
- 切换当前使用的模型
- 添加新的模型配置
- 查看当前模型信息

---

## 📋 使用方法

### 1. 列出所有可用模型

```
用户> 列出可用的模型

CLAW> tool: model_manager("list")
```

**输出示例：**
```
📋 可用模型列表:
==================================================
1. google/gemma-4-e2b ✅ (当前)
   API: http://192.168.2.114:1234/v1
   说明: Gemma 4 E2B - 本地LM Studio

2. gpt-4
   API: https://api.openai.com/v1
   说明: OpenAI GPT-4
```

---

### 2. 查看当前使用的模型

```
用户> 当前使用的是什么模型

CLAW> tool: model_manager("current")
```

**输出示例：**
```
🎯 当前使用的模型:

名称: google/gemma-4-e2b
API地址: http://192.168.2.114:1234/v1
API密钥: lm-studio
说明: Gemma 4 E2B - 本地LM Studio
```

---

### 3. 切换到其他模型

```
用户> 切换到gpt-4模型

CLAW> tool: model_manager("switch", "gpt-4")
```

**输出示例：**
```
✅ 已切换到模型: gpt-4

API地址: https://api.openai.com/v1
说明: OpenAI GPT-4

⚠️  注意: 需要重启JwClaw才能生效
```

---

### 4. 添加新模型

```
用户> 添加一个新模型

CLAW> tool: model_manager("add", "{\"name\": \"claude-3\", \"api_base\": \"https://api.anthropic.com/v1\", \"api_key\": \"sk-ant-xxx\", \"description\": \"Anthropic Claude 3\"}")
```

**输出示例：**
```
✅ 已添加模型: claude-3

API地址: https://api.anthropic.com/v1
说明: Anthropic Claude 3
```

---

## 💡 常见用例

### 用例1：在本地和云端模型之间切换

```
# 查看可用模型
用户> 有哪些模型可用

# 切换到本地模型（快速响应）
用户> 切换到google/gemma-4-e2b

# 切换到云端模型（更强大）
用户> 切换到gpt-4
```

### 用例2：添加OpenAI模型

```
用户> 添加OpenAI GPT-3.5模型

CLAW> tool: model_manager("add", "{\"name\": \"gpt-3.5-turbo\", \"api_base\": \"https://api.openai.com/v1\", \"api_key\": \"sk-your-key\", \"description\": \"GPT-3.5 Turbo\"}")
```

### 用例3：添加多个备用模型

```
# 添加Claude
tool: model_manager("add", "{\"name\": \"claude-3-opus\", \"api_base\": \"https://api.anthropic.com/v1\", \"api_key\": \"sk-ant-xxx\", \"description\": \"Claude 3 Opus\"}")

# 添加Gemini
tool: model_manager("add", "{\"name\": \"gemini-pro\", \"api_base\": \"https://generativelanguage.googleapis.com/v1beta\", \"api_key\": \"your-api-key\", \"description\": \"Google Gemini Pro\"}")
```

---

## 🔧 配置文件说明

### models.json

模型配置存储在 `models.json` 文件中：

```json
{
  "models": [
    {
      "name": "google/gemma-4-e2b",
      "api_base": "http://192.168.2.114:1234/v1",
      "api_key": "lm-studio",
      "description": "Gemma 4 E2B - 本地LM Studio"
    },
    {
      "name": "gpt-4",
      "api_base": "https://api.openai.com/v1",
      "api_key": "sk-xxx",
      "description": "OpenAI GPT-4"
    }
  ],
  "current": "google/gemma-4-e2b"
}
```

### config.json

当前使用的模型配置会同步到 `config.json`：

```json
{
  "api_base": "http://192.168.2.114:1234/v1",
  "model": "google/gemma-4-e2b",
  "api_key": "lm-studio"
}
```

---

## ⚠️ 注意事项

1. **重启生效**
   - 切换模型后，需要重启JwClaw才能生效
   - Web UI也需要重启

2. **API密钥安全**
   - 不要将包含真实API密钥的配置文件上传到公开仓库
   - 建议使用环境变量或加密存储

3. **模型兼容性**
   - 确保添加的模型支持OpenAI兼容的API格式
   - 某些模型可能需要特殊的参数配置

4. **网络访问**
   - 云端模型需要网络连接
   - 本地模型需要相应的服务正在运行（如LM Studio）

---

## 🎨 最佳实践

### 1. 为不同任务配置不同模型

```json
{
  "models": [
    {
      "name": "fast-local",
      "api_base": "http://localhost:1234/v1",
      "api_key": "lm-studio",
      "description": "快速本地模型 - 用于简单任务"
    },
    {
      "name": "smart-cloud",
      "api_base": "https://api.openai.com/v1",
      "api_key": "sk-xxx",
      "description": "智能云端模型 - 用于复杂推理"
    }
  ]
}
```

### 2. 使用描述性名称

```
✅ 好: "gpt-4-turbo-local"
❌ 差: "model1"
```

### 3. 定期清理不用的模型

手动编辑 `models.json` 删除不再使用的模型配置。

---

## 🚀 高级用法

### 通过Web UI管理模型

在Web UI中，你可以：
1. 输入 `列出模型` 查看所有可用模型
2. 输入 `切换到xxx` 快速切换
3. 输入 `当前模型` 查看详细信息

### 批量添加模型

创建一个JSON文件，然后批量导入：

```python
import json

models = [
    {"name": "gpt-4", "api_base": "...", "api_key": "...", "description": "..."},
    {"name": "claude-3", "api_base": "...", "api_key": "...", "description": "..."}
]

# 添加到models.json
with open('models.json', 'r') as f:
    data = json.load(f)

data["models"].extend(models)

with open('models.json', 'w') as f:
    json.dump(data, f, indent=2)
```

---

## 📝 故障排除

### Q1: 切换模型后没有生效
**A**: 需要重启JwClaw。关闭当前运行的实例，重新启动。

### Q2: 添加模型时提示JSON错误
**A**: 检查JSON格式是否正确，确保所有引号都已转义。

### Q3: 找不到models.json文件
**A**: 首次使用model_manager时会自动创建该文件。

### Q4: 模型列表为空
**A**: 至少需要一个模型配置。检查models.json是否存在且格式正确。

---

## 🎯 总结

`model_manager` skill让你能够：
- ✅ 轻松管理多个LLM模型
- ✅ 快速切换以适应不同需求
- ✅ 灵活添加新的模型配置
- ✅ 保持配置的持久化存储

**开始使用吧！** 🚀
