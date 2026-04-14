# -*- coding: utf-8 -*-
"""
context_manager.py - 增强的上下文管理器
管理用户画像、会话历史、长期记忆和工作记忆
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("agent")


class UserProfile:
    """用户画像"""
    
    def __init__(self):
        # 使用绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.USER_FILE = os.path.join(script_dir, "USER.md")
        self.profile = {}
        self._load_profile()
    
    def _load_profile(self):
        """从USER.md加载用户信息"""
        if os.path.exists(self.USER_FILE):
            try:
                with open(self.USER_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析简单的Markdown格式
                self.profile = self._parse_user_md(content)
                logger.info(f"已加载用户画像: {len(self.profile)} 个字段")
            except Exception as e:
                logger.error(f"加载用户画像失败: {e}")
                self.profile = {}
        else:
            self.profile = {}
            logger.info("USER.md不存在，创建默认模板")
            self._create_default_template()
    
    def _parse_user_md(self, content: str) -> dict:
        """解析USER.md文件"""
        profile = {}
        current_section = "general"
        profile[current_section] = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            # 检测章节标题
            if line.startswith('## '):
                current_section = line[3:].strip()
                profile[current_section] = {}
                continue
            
            # 检测键值对
            if ':' in line and not line.startswith('#'):
                key, _, value = line.partition(':')
                key = key.strip().strip('-').strip()
                value = value.strip()
                
                if key and value:
                    profile[current_section][key] = value
        
        return profile
    
    def _create_default_template(self):
        """创建默认USER.md模板"""
        template = """# USER.md - About Your Human

## 基本信息

- **姓名:** [你的姓名]
- **称呼:** [希望你如何被称呼]
- **时区:** Asia/Shanghai

## 联系方式

- 邮箱: [your-email@example.com]
- 手机: [可选]

## 账号与服务配置

- [常用服务配置，不含密钥]

## 开发偏好

- 主力语言: [如 Python/TypeScript]
- IDE: [如 VSCode/WebStorm]
- OS: [如 Windows/macOS/Linux]

## 工作上下文

- 当前项目: [项目名称]
- 角色: [如 开发工程师]

## 常用工具

- [你常用的工具和命令]

## 备注

[其他值得记住的信息]
"""
        
        try:
            with open(self.USER_FILE, 'w', encoding='utf-8') as f:
                f.write(template)
            logger.info(f"已创建USER.md模板")
        except Exception as e:
            logger.error(f"创建USER.md失败: {e}")
    
    def get_info(self, category: str = None, key: str = None) -> any:
        """
        获取用户信息
        
        Args:
            category: 类别（如"联系方式"）
            key: 键名（如"邮箱"）
            
        Returns:
            用户信息
        """
        if category and key:
            return self.profile.get(category, {}).get(key, "")
        elif category:
            return self.profile.get(category, {})
        else:
            return self.profile
    
    def update_info(self, category: str, key: str, value: str):
        """更新用户信息"""
        if category not in self.profile:
            self.profile[category] = {}
        
        old_value = self.profile[category].get(key, "")
        self.profile[category][key] = value
        
        # 保存到文件
        self._save_to_file()
        
        logger.info(f"用户信息已更新: {category}.{key} = {value}")
        return old_value
    
    def _save_to_file(self):
        """保存回USER.md"""
        # 简化实现：直接重写文件
        # 实际应该智能合并，保留用户手动编辑的内容
        lines = ["# USER.md - About Your Human\n"]
        
        for category, items in self.profile.items():
            lines.append(f"\n## {category}\n")
            if isinstance(items, dict):
                for key, value in items.items():
                    lines.append(f"- {key}: {value}")
            else:
                lines.append(str(items))
        
        try:
            with open(self.USER_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        except Exception as e:
            logger.error(f"保存USER.md失败: {e}")


class SessionMemory:
    """会话记忆管理"""
    
    # 使用脚本所在目录作为基准，确保路径正确
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    MEMORY_DIR = os.path.join(_script_dir, "workspace", "memory")
    
    def __init__(self):
        self.today_memory = []
        self._load_today_memory()
    
    def _load_today_memory(self):
        """加载今天的记忆"""
        today = datetime.now().strftime("%Y-%m-%d")
        memory_file = os.path.join(self.MEMORY_DIR, f"{today}.md")
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析记忆条目
                self.today_memory = [
                    line.strip()
                    for line in content.split('\n')
                    if line.strip() and not line.startswith('#')
                ]
                
                logger.info(f"已加载今日记忆: {len(self.today_memory)} 条")
            except Exception as e:
                logger.error(f"加载记忆失败: {e}")
                self.today_memory = []
        else:
            self.today_memory = []
    
    def add_memory(self, content: str, category: str = "general"):
        """
        添加记忆
        
        Args:
            content: 记忆内容
            category: 类别（work/learning/personal/general）
        """
        timestamp = datetime.now().strftime("%H:%M")
        memory_entry = f"- [{timestamp}] [{category.upper()}] {content}"
        
        self.today_memory.append(memory_entry)
        
        # 保存到文件
        self._save_to_file()
        
        logger.debug(f"记忆已添加: {content[:50]}...")
    
    def get_recent_memories(self, count: int = 10) -> List[str]:
        """获取最近的记忆"""
        return self.today_memory[-count:]
    
    def search_memories(self, keyword: str) -> List[str]:
        """搜索记忆"""
        keyword_lower = keyword.lower()
        return [
            m for m in self.today_memory
            if keyword_lower in m.lower()
        ]
    
    def _save_to_file(self):
        """保存到文件"""
        os.makedirs(self.MEMORY_DIR, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        memory_file = os.path.join(self.MEMORY_DIR, f"{today}.md")
        
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                f.write(f"# {today} - 工作记忆\n\n")
                for memory in self.today_memory:
                    f.write(memory + "\n")
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")


class ContextManager:
    """统一的上下文管理器"""
    
    def __init__(self):
        self.user_profile = UserProfile()
        self.session_memory = SessionMemory()
        self.conversation_history = []  # 当前对话历史
        self.max_history_length = 50  # 最大对话轮次
    
    def get_user_context(self) -> dict:
        """获取用户上下文"""
        return {
            "profile": self.user_profile.profile,
            "recent_memories": self.session_memory.get_recent_memories(5),
            "conversation_turns": len(self.conversation_history)
        }
    
    def add_conversation(self, role: str, content: str):
        """添加对话到历史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 限制历史长度
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        if not self.conversation_history:
            return "无对话历史"
        
        # 简单实现：返回最近3轮对话
        recent = self.conversation_history[-6:]  # 3轮 = 6条消息
        summary_lines = []
        
        for msg in recent:
            role_cn = "用户" if msg["role"] == "user" else "助理"
            preview = msg["content"][:100]
            summary_lines.append(f"{role_cn}: {preview}...")
        
        return "\n".join(summary_lines)
    
    def record_experience(self, task: str, outcome: str, lessons: str = ""):
        """记录经验"""
        experience = f"任务: {task} | 结果: {outcome}"
        if lessons:
            experience += f" | 教训: {lessons}"
        
        self.session_memory.add_memory(experience, category="experience")
        logger.info(f"经验已记录: {task}")
    
    def clear_conversation(self):
        """清空对话历史（新对话）"""
        self.conversation_history.clear()
        logger.info("对话历史已清空")


# 全局上下文管理器实例
context_manager = ContextManager()


def get_user_info(category: str = None, key: str = None):
    """获取用户信息（便捷函数）"""
    return context_manager.user_profile.get_info(category, key)


def add_memory(content: str, category: str = "general"):
    """添加记忆（便捷函数）"""
    context_manager.session_memory.add_memory(content, category)


if __name__ == "__main__":
    # 测试
    cm = ContextManager()
    
    # 测试用户画像
    print("=== 用户画像 ===")
    print(cm.get_user_context())
    
    # 测试添加记忆
    print("\n=== 添加记忆 ===")
    cm.session_memory.add_memory("完成了Agent核心系统开发", category="work")
    cm.session_memory.add_memory("学习了PowerShell脚本编写", category="learning")
    
    print("\n最近记忆:")
    for memory in cm.session_memory.get_recent_memories():
        print(f"  {memory}")
    
    # 测试对话历史
    print("\n=== 对话历史 ===")
    cm.add_conversation("user", "帮我整理桌面")
    cm.add_conversation("assistant", "好的，正在执行文件整理...")
    
    print(cm.get_conversation_summary())
