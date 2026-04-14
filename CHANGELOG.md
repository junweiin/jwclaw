# 更新日志

所有重要的项目更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- 添加更多预置Skills
- 实现异步I/O支持
- 添加Web界面
- 支持多语言

---

## [0.1.64] - 2024-04-14

### ✨ 新增
- 添加`video_download` skill，支持B站、YouTube等视频下载
- 添加`count_folders` skill，统计文件夹数量
- 增强Agent执行策略，支持直接使用shell命令
- 添加示例6：打开应用程序

### 🔧 改进
- 优化`build_system_prompt`，强化"禁止拒绝"原则
- 所有文件路径改为绝对路径，支持从任意目录启动
- QClaw格式的Skill现在可以提取并执行Python代码
- 增强错误提示信息

### 🐛 修复
- 修复f-string花括号转义问题
- 修复中文逗号导致的SyntaxError
- 修复Skill加载时code字段为None的问题
- 修复配置文件路径问题

### 📝 文档
- 完善README.md，添加完整的部署和使用指南
- 添加QUICKSTART.md快速入门指南
- 添加CONTRIBUTING.md贡献指南
- 添加.gitignore文件
- 添加LICENSE文件
- 添加requirements.txt

---

## [0.1.63] - 2024-04-13

### ✨ 新增
- 实现ReAct Agent架构
- 添加20+预置Skills
- 实现智能记忆系统（TF-IDF检索）
- 添加规则引擎
- 实现智能缓存机制
- 添加安全执行沙箱

### 🔧 改进
- 优化Skill加载机制
- 增强错误处理
- 改进日志系统
- 优化性能

### 🐛 修复
- 修复并发安全问题
- 修复资源泄漏
- 修复记忆系统重复问题

---

## [0.1.0] - 2024-04-01

### ✨ 首次发布
- 基础Agent框架
- 基本Skills系统
- 简单的记忆功能
- 命令行交互界面

---

## 版本说明

### 版本号格式：主版本.次版本.修订版本

- **主版本**：不兼容的API修改
- **次版本**：向下兼容的功能性新增
- **修订版本**：向下兼容的问题修正

### 变更类型

- **新增** (Added)：新功能
- **改进** (Changed)：现有功能的变更
- **弃用** (Deprecated)：即将移除的功能
- **移除** (Removed)：已移除的功能
- **修复** (Fixed)：Bug修复
- **安全** (Security)：安全性修复

---

## 相关链接

- [GitHub Releases](https://github.com/your-username/jwclaw/releases)
- [Issue Tracker](https://github.com/your-username/jwclaw/issues)
- [项目主页](https://github.com/your-username/jwclaw)

---

**维护者**: JwClaw Team  
**最后更新**: 2024-04-14
