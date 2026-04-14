# JwClaw 快速入门指南

## 5分钟快速开始

### 第1步：安装Python

确保已安装Python 3.8+：
```bash
python --version
```

### 第2步：克隆项目

```bash
git clone https://github.com/your-username/jwclaw.git
cd jwclaw
```

### 第3步：安装依赖

```bash
pip install -r requirements.txt
```

### 第4步：配置API

编辑 `config.json`：

```json
{
  "api_base": "http://localhost:1234/v1",
  "model": "google/gemma-4-e2b",
  "api_key": "lm-studio"
}
```

**推荐使用LM Studio（本地运行，无需网络）：**
1. 下载：https://lmstudio.ai/
2. 下载模型（如Gemma 4）
3. 启动本地服务器（默认端口1234）

### 第5步：启动

```bash
# Windows
jwclaw.bat

# macOS/Linux
python3 jwclaw.py
```

### 第6步：开始使用

```
用户> 你好
CLAW> 你好！我是JwClaw智能体助手，有什么可以帮助你的吗？

用户> 桌面有多少个文件夹
CLAW> [思考] 这是常见任务，使用count_folders skill。
      [回复] tool: count_folders("C:\Users\jw\Desktop")
      
      📁 文件夹统计报告
      ━━━━━━━━━━━━━━━━━━━━━━
      📂 扫描路径: C:\Users\jw\Desktop
      📁 文件夹数量: 9
```

---

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `help` | 查看帮助 |
| `skills` | 列出所有技能 |
| `skillinfo <名称>` | 查看技能详情 |
| `memory` | 查看会话记忆 |
| `status` | 显示系统状态 |
| `new` | 开始新对话 |
| `quit` | 退出系统 |

---

## 典型用例

### 文件系统
```
桌面有多少个文件夹
下载文件夹里有多少张图片
找出Downloads目录下的所有PDF文件
```

### 系统查询
```
查看C盘剩余空间
列出正在运行的进程
查看本机IP地址
```

### 应用程序
```
打开Edge浏览器
打开C:\Program Files\App\app.exe
安装Python
```

### 网络任务
```
下载这个B站视频 https://www.bilibili.com/video/BV1xx
搜索最新的AI新闻
读取 https://example.com 的内容
```

---

## 故障排除

### 问题1：启动失败
```
KeyError: 'model'
```
**解决：** 检查`config.json`格式是否正确

### 问题2：工具未知
```
未知工具: xxx
```
**解决：** 重启JwClaw重新加载Skills

### 问题3：API连接失败
```
Connection refused
```
**解决：** 确认API服务已启动，检查`api_base`配置

---

## 下一步

- 📖 阅读完整文档：[README.md](README.md)
- 🔧 创建自己的Skill：[开发指南](README.md#-开发指南)
- ❓ 常见问题：[FAQ](README.md#-常见问题)
- 💬 报告问题：[GitHub Issues](https://github.com/your-username/jwclaw/issues)

---

**祝你使用愉快！** 🎉
