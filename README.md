
# JwClaw 智能体系统

<div align="center">

![Version](https://img.shields.io/badge/version-0.1.64-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**一个功能强大的本地AI智能体系统，支持ReAct架构、Skills扩展、智能记忆和安全执行**

[快速开始](#-快速开始) • [功能特性](#-核心特性) • [使用文档](#-使用指南) • [开发指南](#-开发指南) • [常见问题](#-常见问题)

</div>

---

## 📖 简介

JwClaw是一个基于ReAct（Reasoning + Acting）架构的本地AI智能体系统。它能够理解自然语言指令，自主选择合适的工具或命令来完成任务，并通过智能记忆系统不断学习和进化。

### ✨ 主要特点

- 🧠 **智能决策** - 自动判断使用Skills还是直接执行命令
- 🔧 **灵活扩展** - 支持QClaw格式的Skills，易于创建和分享
- 💾 **持久记忆** - TF-IDF检索 + 会话记忆 + 用户画像
- 🔒 **安全执行** - Shell命令白名单 + 沙箱隔离 + 加密配置
- ⚡ **高性能** - 智能缓存机制，减少重复计算
- 🌍 **跨平台** - 支持Windows、macOS、Linux

---

## 🚀 快速开始

### 前置要求

- **Python 3.8+**
- **OpenAI兼容的API服务**（如LM Studio、Ollama、LocalAI等）

### 安装方式

#### 方式一：pip 安装（推荐）

```bash
pip install jwclaw
```

安装后直接使用：
```bash
jwclaw              # 启动交互模式
jwclaw --help       # 查看帮助
```

#### 方式二：从源码安装

```bash
git clone https://github.com/junweiin/jwclaw.git
cd jwclaw
pip install -e .    # 开发模式安装
# 或
python setup.py install
```

#### 方式三：手动安装

```bash
git clone https://github.com/junweiin/jwclaw.git
cd jwclaw
python scripts/install.py
```

### 配置API

编辑 `config.json` 文件（首次运行会自动创建）：

```json
{
  "api_base": "http://localhost:1234/v1",
  "model": "google/gemma-4-e2b",
  "api_key": "lm-studio"
}
```

**常用API服务配置示例：**

| 服务 | api_base | 说明 |
|------|----------|------|
| LM Studio | `http://localhost:1234/v1` | 本地运行，推荐 |
| Ollama | `http://localhost:11434/v1` | 本地运行 |
| OpenAI | `https://api.openai.com/v1` | 需要API Key |

#### 4. 启动程序

**方式一：直接运行（开发/测试）**

```bash
python main.py
```

**方式二：安装到系统（推荐）**

```bash
# 安装
python install.py

# 之后可以在任意位置使用
jwclaw              # 启动交互模式
jwclaw --help       # 查看帮助

# 卸载
python uninstall.py
```

---

## 🎯 核心特性

### 1. ReAct Agent架构

JwClaw采用**推理+行动**的工作模式：

```
用户输入 → 理解任务 → 选择策略 → 执行动作 → 观察结果 → 迭代优化
```

**执行策略：**
- ✅ 标准化任务 → 使用Skills（如统计图片、下载视频）
- ✅ 非标准化任务 → 直接执行shell/Python命令
- ✅ 复杂重复任务 → 创建新Skill

### 2. Skills系统

预置20+个Skills，覆盖常见任务：

| Skill | 功能 | 示例 |
|-------|------|------|
| `shell` | 执行系统命令 | `tool: shell("dir")` |
| `file_manager` | 文件管理 | `tool: file_manager("read file.txt")` |
| `web_search` | 网络搜索 | `tool: web_search("query")` |
| `weather-advisor` | 天气查询 | `tool: weather-advisor("now")` |

**Skills格式（QClaw标准）：**

```
skills/my-skill/
├── SKILL.md          # Skill定义（必需）
└── scripts/          # 外部脚本（可选）
    ├── command.ps1   # Windows脚本
    └── command.sh    # Linux/Mac脚本
```

### 3. 智能记忆系统

- **会话记忆** - 当前对话的短期记忆
- **长期记忆** - 持久化存储，支持TF-IDF检索
- **用户画像** - 从USER.md加载个性化信息
- **经验记录** - 自动保存成功/失败的经验

### 4. 安全机制

- ✅ **命令白名单** - 禁止危险命令（rm -rf /等）
- ✅ **沙箱执行** - 隔离Skill代码执行环境
- ✅ **加密配置** - API密钥加密存储
- ✅ **权限控制** - 防止越权操作

### 5. 性能优化

- 🚀 **LLM响应缓存** - 避免重复调用
- 🚀 **Skill结果缓存** - 加速常见任务
- 🚀 **懒加载机制** - 按需加载Skills
- 🚀 **异步I/O** - 非阻塞操作

---

## 📖 使用指南

### 基本交互

启动后，直接输入自然语言指令：

```
用户> 桌面有多少个文件夹
CLAW> 
[思考]
这是常见任务，使用count_folders skill。
[回复] tool: count_folders("C:\Users\jw\Desktop")

[工具: count_folders(C:\Users\jw\Desktop)]
[结果] 
📁 文件夹统计报告
━━━━━━━━━━━━━━━━━━━━━━
📂 扫描路径: C:\Users\jw\Desktop
🔍 扫描模式: 仅直接子文件夹
📊 扫描项目数: 23
📁 文件夹数量: 9
```

### 内置命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `help` | 查看帮助 | `help` |
| `skills` | 列出所有技能 | `skills` |
| `skillinfo <名称>` | 查看技能详情 | `skillinfo shell` |
| `memory` | 查看会话记忆 | `memory` |
| `status` | 显示系统状态 | `status` |
| `new` | 开始新对话 | `new` |
| `quit` | 退出系统 | `quit` |

### 典型用例

#### 1. 文件系统操作

```
# 统计文件
用户> 下载文件夹里有多少张图片
用户> 桌面有多少个文件夹

# 文件搜索
用户> 找出Downloads目录下的所有PDF文件

# 文件管理
用户> 删除test.txt文件
```

#### 2. 系统查询

```
# 磁盘空间
用户> 查看C盘剩余空间

# 进程管理
用户> 列出正在运行的进程

# 网络信息
用户> 查看本机IP地址
```

#### 3. 应用程序

```
# 打开应用
用户> 打开Edge浏览器
用户> 打开C:\Program Files\App\app.exe

# 安装软件
用户> 安装Python
用户> 安装yt-dlp
```

#### 4. 网络任务

```
# 下载视频
用户> 下载这个B站视频 https://www.bilibili.com/video/BV1xx

# 网页搜索
用户> 搜索最新的AI新闻

# 获取网页内容
用户> 读取 https://example.com 的内容
```

#### 5. 数据处理

```
# 统计分析
用户> 统计当前目录下每种文件类型的数量

# 文本处理
用户> 计算log.txt中ERROR出现的次数
```

---

## 🔧 配置说明

### config.json

```json
{
  "api_base": "http://localhost:1234/v1",
  "model": "google/gemma-4-e2b",
  "api_key": "lm-studio"
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `api_base` | string | ✅ | API服务端点 |
| `model` | string | ✅ | 模型名称 |
| `api_key` | string | ❌ | API密钥（默认lm-studio） |

### USER.md

创建用户画像文件，让Agent更了解你：

```markdown
# USER.md - About Your Human

## 基本信息
- 姓名: 张三
- 职业: 软件工程师
- 位置: 北京

## 偏好设置
- 编程语言: Python, JavaScript
- 操作系统: Windows 11
- 常用工具: VS Code, Git

## 特殊说明
- 工作目录: C:\Projects
- 下载目录: C:\Users\张三\Downloads
```

### 环境变量（可选）

```bash
# Windows PowerShell
$env:AGENT_API_KEY="your-api-key"
$env:AGENT_MODEL="gpt-4"

# Linux/macOS
export AGENT_API_KEY="your-api-key"
export AGENT_MODEL="gpt-4"
```

---

## 🛠️ 开发指南

### 创建新Skill

#### 方法1：手动创建

1. 在`skills/`目录下创建文件夹：

```bash
mkdir skills/my-skill
```

2. 创建`SKILL.md`文件：

```markdown
# skill: my-skill

## 描述
简要描述这个skill的功能

## 调用格式
tool: my-skill("参数1", "参数2")

## 执行代码
```python
import os

try:
    # 获取参数
    param1 = args[0] if args else ""
    
    # 实现逻辑
    result = f"处理结果: {param1}"
    
except Exception as e:
    result = f"执行出错: {str(e)}"
```

#### 方法2：使用create_skill工具

```
用户> 创建一个统计视频数量的skill
CLAW>
[思考]
用户使用create_skill工具...
[回复] tool: create_skill("count_videos", "统计文件夹中的视频文件数量")
```

### Skill最佳实践

✅ **推荐做法：**
- 使用`os.walk()`递归遍历目录
- 添加完整的错误处理（try-except）
- 支持多种文件格式/场景
- 提供详细的输出报告
- 考虑边界情况（空输入、权限不足等）

❌ **避免做法：**
- 只扫描单层目录（使用`os.listdir`）
- 硬编码少量格式
- 忽略异常处理
- 返回过于简单的结果

### 调试技巧

#### 1. 启用调试模式

```bash
python jwclaw.py --debug
```

会输出详细的日志到控制台和`agent.log`。

#### 2. 查看日志文件

```bash
# Windows
type agent.log

# Linux/macOS
tail -f agent.log
```

#### 3. 清除缓存

如果遇到问题，尝试清除缓存：

```bash
# Windows PowerShell
Remove-Item cache\skills\* -Force
Remove-Item cache\llm\* -Force

# Linux/macOS
rm -rf cache/skills/* cache/llm/*
```

### 项目结构

```
jwclaw/
├── jwclaw.py              # 主程序 ⭐
├── config.json            # 配置文件
├── USER.md                # 用户画像
├── memory.json            # 长期记忆
├── agent_rules.json       # 规则引擎配置
│
├── skills/                # Skills目录
│   ├── shell/
│   │   └── SKILL.md
│   ├── count_images/
│   │   └── SKILL.md
│   └── ...
│
├── workspace/
│   └── memory/            # 会话记忆
│
├── cache/                 # 智能缓存
│   ├── llm/               # LLM响应缓存
│   └── skills/            # Skill结果缓存
│
├── agent.log              # 运行日志
│
└── [核心模块]
    ├── rules_engine.py    # 规则引擎
    ├── context_manager.py # 上下文管理
    ├── cache.py           # 缓存系统
    ├── secure_config.py   # 安全配置
    ├── sandbox.py         # 沙箱执行
    ├── skill_metadata.py  # Skill元数据
    └── help_system.py     # 帮助系统
```

---

## ❓ 常见问题

### Q1: 启动时提示"KeyError: 'model'"

**原因：** `config.json`文件不存在或格式错误。

**解决：** 检查`config.json`是否包含必需的字段：
```json
{
  "api_base": "http://localhost:1234/v1",
  "model": "your-model",
  "api_key": "your-key"
}
```

### Q2: 工具执行返回"未知工具: xxx"

**原因：** Skill文件丢失或未正确加载。

**解决：**
1. 检查`skills/`目录下是否有对应的skill文件夹
2. 确保文件夹内有`SKILL.md`文件
3. 重启JwClaw重新加载Skills

### Q3: Agent拒绝执行命令，说"我无法执行"

**原因：** Prompt不够明确，或者LLM模型未遵循指令。

**解决：**
1. 检查`build_system_prompt`函数中的"禁止拒绝"原则
2. 尝试更换更强的LLM模型
3. 在对话中明确指示Agent执行

### Q4: 如何配置全局命令？

**Windows：**
```powershell
# 添加到PATH
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\path\to\jwclaw", "User")

# 或创建别名
Add-Content -Path $PROFILE -Value "Set-Alias jwclaw 'C:\path\to\jwclaw\jwclaw.bat'"
```

**Linux/macOS：**
```bash
# 添加到~/.bashrc或~/.zshrc
export PATH="$PATH:/path/to/jwclaw"
alias jwclaw="/path/to/jwclaw/jwclaw.py"
```

### Q5: 如何提高响应速度？

1. **使用本地模型** - LM Studio、Ollama等
2. **启用缓存** - 已默认启用
3. **减少上下文** - 定期使用`new`命令开始新对话
4. **优化Skills** - 避免复杂的递归操作

### Q6: 支持哪些LLM模型？

任何OpenAI兼容的API都支持：
- ✅ LM Studio（推荐，本地运行）
- ✅ Ollama（本地运行）
- ✅ OpenAI GPT-3.5/4
- ✅ Anthropic Claude
- ✅ Google Gemini
- ✅ 其他兼容OpenAI API的服务

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 提交Issue

请提供：
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 系统环境（OS、Python版本等）
- 相关日志（`agent.log`）

### 提交Pull Request

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 开发规范

- 遵循PEP 8代码规范
- 添加必要的注释
- 更新相关文档
- 确保测试通过

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供LLM API标准
- [QClaw](https://github.com/openclaw/openclaw) - Skills格式参考
- [LM Studio](https://lmstudio.ai/) - 本地LLM运行方案
- 所有贡献者和用户

---

## 📞 联系方式

- 📧 Email: your-email@example.com
- 💬 Issues: [GitHub Issues](https://github.com/your-username/jwclaw/issues)
- 🌐 Website: [项目主页](https://github.com/your-username/jwclaw)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个Star！**

Made with ❤️ by JwClaw Team

</div>
