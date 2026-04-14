# 贡献指南

感谢你对JwClaw项目的关注！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 报告Bug

如果你发现了Bug，请创建Issue并包含：

1. **问题描述** - 清晰简洁地描述问题
2. **复现步骤** - 如何重现这个问题
3. **预期行为** - 你期望发生什么
4. **实际行为** - 实际发生了什么
5. **环境信息**：
   - 操作系统（Windows/macOS/Linux）
   - Python版本
   - JwClaw版本
6. **相关日志** - `agent.log`中的错误信息

### 提出新功能

如果你有新的功能想法：

1. 先搜索Issues，确认没有重复提议
2. 创建Feature Request Issue
3. 详细描述功能需求和用例
4. 说明这个功能的价值

### 提交代码

#### 1. Fork仓库

点击GitHub页面右上角的"Fork"按钮

#### 2. 克隆到本地

```bash
git clone https://github.com/your-username/jwclaw.git
cd jwclaw
```

#### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

**分支命名规范：**
- `feature/xxx` - 新功能
- `fix/xxx` - Bug修复
- `docs/xxx` - 文档更新
- `refactor/xxx` - 代码重构

#### 4. 进行修改

遵循以下规范：

**代码风格：**
- 遵循PEP 8规范
- 使用4空格缩进
- 行长度不超过100字符
- 添加必要的注释

**提交信息：**
```
类型: 简短描述

详细说明（可选）

- 修改点1
- 修改点2

相关Issue: #123
```

**类型包括：**
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

#### 5. 测试

确保你的修改：
- ✅ 不破坏现有功能
- ✅ 通过所有测试
- ✅ 添加了必要的测试用例

#### 6. 提交

```bash
git add .
git commit -m "feat: 添加新功能xxx"
git push origin feature/your-feature-name
```

#### 7. 创建Pull Request

1. 访问你的Fork仓库
2. 点击"Compare & pull request"
3. 填写PR描述
4. 等待审核

### PR审核流程

1. **自动检查** - CI运行测试
2. **代码审查** - 维护者审查代码
3. **反馈修改** - 根据建议修改
4. **合并** - 审核通过后合并

---

## 📋 开发规范

### 代码规范

#### Python代码

```python
# ✅ 推荐
def calculate_sum(numbers: list) -> int:
    """计算数字列表的总和
    
    Args:
        numbers: 数字列表
        
    Returns:
        总和
    """
    return sum(numbers)

# ❌ 避免
def calc(nums):
    return sum(nums)
```

#### 命名规范

- **变量/函数**: `snake_case`
- **类名**: `PascalCase`
- **常量**: `UPPER_CASE`
- **私有成员**: `_leading_underscore`

### Skill开发规范

#### SKILL.md结构

```markdown
# skill: my-skill

## 描述
清晰描述skill的功能和用途

## 调用格式
tool: my-skill("参数1", "参数2")

参数说明：
- 参数1: 说明
- 参数2: 说明

## 执行代码
```python
import os

try:
    # 获取参数
    param1 = args[0] if args else ""
    
    # 验证参数
    if not param1:
        result = "错误: 请提供参数"
    else:
        # 实现逻辑
        result = f"结果: {param1}"
        
except Exception as e:
    result = f"执行出错: {str(e)}"
```

#### 最佳实践

✅ **应该做：**
- 使用递归遍历（`os.walk`）而非单层扫描
- 添加完整的错误处理
- 支持多种场景和格式
- 提供详细的输出报告
- 考虑边界情况

❌ **不应该做：**
- 硬编码路径或格式
- 忽略异常处理
- 返回过于简单的结果
- 假设输入总是有效

### 文档规范

#### README更新

如果添加了新功能，记得更新：
- README.md中的功能列表
- 使用示例
- API文档（如果有）

#### 注释规范

```python
# ✅ 好的注释
def connect_db(host: str, port: int) -> Connection:
    """连接数据库
    
    Args:
        host: 数据库主机地址
        port: 数据库端口
        
    Returns:
        数据库连接对象
        
    Raises:
        ConnectionError: 连接失败时
    """
    pass

# ❌ 不好的注释
def connect_db(h, p):  # 连接db
    pass
```

---

## 🧪 测试指南

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_skill.py

# 带覆盖率报告
python -m pytest --cov=jwclaw tests/
```

### 编写测试

```python
import unittest
from jwclaw import load_skills

class TestSkills(unittest.TestCase):
    def test_load_skills(self):
        """测试Skill加载"""
        skills = load_skills()
        self.assertGreater(len(skills), 0)
        
    def test_shell_skill(self):
        """测试shell skill"""
        skills = load_skills()
        self.assertIn('shell', skills)

if __name__ == '__main__':
    unittest.main()
```

---

## 📝 文档贡献

### 改进文档

- 修正拼写/语法错误
- 补充缺失的说明
- 添加更多示例
- 翻译文档

### 文档结构

```
docs/
├── README.md           # 主文档
├── QUICKSTART.md       # 快速入门
├── CONTRIBUTING.md     # 贡献指南（本文件）
└── API.md              # API文档（如有）
```

---

## 💬 社区交流

- **Issues**: [GitHub Issues](https://github.com/your-username/jwclaw/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/jwclaw/discussions)
- **Email**: your-email@example.com

---

## 🎯 优先处理的Issue

查看标记为`good first issue`和`help wanted`的Issue，这些适合新手贡献：

- [Good First Issues](https://github.com/your-username/jwclaw/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- [Help Wanted](https://github.com/your-username/jwclaw/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)

---

## 📜 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺：

- 尊重不同观点和经验
- 接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性别化的语言或图像
- 人身攻击或侮辱性评论
- 公开或私下骚扰
- 未经许可发布他人隐私信息
- 其他不道德或不专业的行为

---

## 🙏 致谢

感谢所有为JwClaw做出贡献的人！

你的每一次贡献都让这个项目变得更好！❤️

---

**最后更新**: 2024-04-14
