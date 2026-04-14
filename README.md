# JwClaw 极简智能体

<div align="center">

![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**轻量级、无框架依赖的 AI Agent，默认 CLI 交互，Skill 优先执行**

[快速开始](#-快速开始) • [安装](#-安装) • [使用](#-使用指南) • [开发 Skill](#-开发指南)

</div>

---

## 📖 简介

JwClaw 是一个极简主义的 AI Agent，零框架依赖，仅使用 OpenAI 客户端。支持 ReAct 架构、Skills 扩展，默认 CLI 交互。

### ✨ 主要特点

- 🚀 **极简架构** - 零框架依赖，仅 `openai>=1.0.0`
- 🎯 **Skill 优先** - 自动识别并调用合适的 Skill 完成任务
- 🔧 **易于扩展** - 通过 Markdown 格式 SKILL.md 定义新功能
- 💻 **CLI 优先** - 默认命令行交互，轻量高效
- 📦 **易于安装** - `pip install jwclaw` 一键安装
- 🌍 **跨平台** - 支持 Windows、macOS、Linux

---

## 🚀 快速开始

### 前置要求

- **Python 3.8+**
- **OpenAI 兼容的 API 服务**（如 LM Studio、Ollama、LocalAI 等）

### 安装

```bash
# PyPI 安装（推荐）
pip install jwclaw

# 或从 GitHub 安装
pip install git+https://github.com/junweiin/jwclaw.git
```

### 配置

编辑 `config.json`（首次运行自动创建）：

```json
{
  "api_base": "http://localhost:1234/v1",
  "model": "your-model-name",
  "api_key": "lm-studio"
}
```

### 运行

```bash
jwclaw
```

### 卸载

```bash
pip uninstall jwclaw
```

---

## 📖 使用指南

### 基本交互

启动后直接输入自然语言指令：

```
> 今天有什么新闻
🔧 [news] {'query': '今天的新闻'}
📰 最新新闻
==================================================
1. 科技新闻标题...
   📎 IT之家

2. 财经新闻标题...
   📎 新浪财经
```

### 内置命令

| 命令 | 说明 |
|------|------|
| `/clear` | 清空对话历史 |
| `/tools` | 列出所有工具 |
| `/exit` | 退出程序 |

### 内置 Skills

| Skill | 功能 |
|-------|------|
| `shell` | 执行系统命令 |
| `news` | RSS 新闻聚合 |
| `web_search` | 网络搜索 |
| `weather_advisor` | 天气查询 |
| `xlsx` | Excel 处理 |

---

## 🔧 开发指南

### 创建新 Skill

在 `skills/my_skill/SKILL.md` 创建文件：

```markdown
---
name: my_skill
description: "我的自定义技能"
---

## 执行代码
```python
query = args[0] if args else ""
result = f"处理结果: {query}"
```
```

自动生效，无需重启。

### Skill 代码规范

- 使用 `args[0]` 获取输入参数
- 使用 `result` 变量返回结果
- 添加 try-except 错误处理

---

## 🎯 核心架构

```
用户输入 → LLM 推理 → 工具调用 → 执行 → 返回结果
```

- **单文件核心** - `core.py` ~200 行
- **Function Calling API** - 替代正则解析
- **自动 Skill 发现** - 启动时自动加载

---

## 📁 项目结构

```
jwclaw/
├── src/jwclaw/          # 核心代码
│   ├── __init__.py
│   ├── __main__.py      # CLI 入口
│   └── core.py          # Agent 核心
├── skills/              # Skills 目录
├── config.json          # 配置文件
└── workspace/           # 工作目录
```

---

## ❓ 常见问题

### Q1: 启动时提示缺少 openai

```bash
pip install openai
```

### Q2: 无法连接到 API

检查 `config.json` 中的 `api_base` 是否正确。

### Q3: Skill 未生效

确保 SKILL.md 文件格式正确，包含 `## 执行代码` 区块。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🔗 链接

- **GitHub**: https://github.com/junweiin/jwclaw
- **PyPI**: https://pypi.org/project/jwclaw/
