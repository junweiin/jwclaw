# -*- coding: utf-8 -*-
"""
help_system.py - 交互式帮助系统
提供命令帮助、技能说明和使用示例
"""

from typing import Dict, List, Optional


class HelpSystem:
    """帮助系统管理器"""
    
    def __init__(self):
        self.commands = self._init_commands()
        self.tips = self._init_tips()
    
    def _init_commands(self) -> Dict[str, dict]:
        """初始化命令帮助"""
        return {
            "help": {
                "description": "显示帮助信息",
                "usage": "help [命令名]",
                "examples": [
                    "help           # 显示所有命令",
                    "help skills    # 显示skills命令详情"
                ]
            },
            "skills": {
                "description": "查看已安装的技能列表",
                "usage": "skills",
                "examples": [
                    "skills         # 列出所有技能"
                ]
            },
            "memory": {
                "description": "查看历史记忆（最近10条）",
                "usage": "memory",
                "examples": [
                    "memory         # 显示记忆列表"
                ]
            },
            "clean_memory": {
                "description": "清理重复和过期的记忆",
                "usage": "clean_memory",
                "examples": [
                    "clean_memory   # 自动清理重复记忆"
                ]
            },
            "new": {
                "description": "开启新对话（清除上下文）",
                "usage": "new",
                "examples": [
                    "new            # 重置对话历史"
                ]
            },
            "config": {
                "description": "查看和修改配置",
                "usage": "config",
                "examples": [
                    "config         # 交互式配置管理"
                ]
            },
            "quit": {
                "description": "退出程序",
                "usage": "quit / exit",
                "examples": [
                    "quit           # 退出助手",
                    "exit           # 同上"
                ]
            },
            "status": {
                "description": "显示系统状态信息",
                "usage": "status",
                "examples": [
                    "status         # 显示模型、技能数、记忆数等"
                ]
            },
            "skillinfo": {
                "description": "查看技能的详细信息",
                "usage": "skillinfo <技能名>",
                "examples": [
                    "skillinfo shell        # 查看shell技能详情",
                    "skillinfo video_download  # 查看下载技能详情"
                ]
            }
        }
    
    def _init_tips(self) -> List[str]:
        """初始化使用技巧"""
        return [
            "💡 提示: 使用自然语言描述任务，助手会自动选择合适工具",
            "💡 提示: 输入 'help' 查看所有可用命令",
            "💡 提示: 输入 'skills' 查看已安装的技能",
            "💡 提示: 按 ESC 键可以中断正在生成的回复",
            "💡 提示: 使用 'new' 命令开启新对话，清除上下文",
            "💡 提示: 记忆系统会自动学习你的使用经验",
            "💡 提示: 定期运行 'clean_memory' 清理重复记忆",
            "💡 提示: 可以通过创建 skill 文件扩展助手能力",
        ]
    
    def get_help(self, command: Optional[str] = None) -> str:
        """
        获取帮助信息
        
        Args:
            command: 特定命令名，None则显示所有命令
            
        Returns:
            帮助文本
        """
        if command:
            return self._get_command_help(command)
        else:
            return self._get_all_commands_help()
    
    def _get_command_help(self, command: str) -> str:
        """获取特定命令的帮助"""
        cmd_info = self.commands.get(command.lower())
        
        if not cmd_info:
            return f"❌ 未知命令: {command}\n\n输入 'help' 查看所有可用命令"
        
        lines = [
            f"📖 命令: {command}",
            f"   说明: {cmd_info['description']}",
            f"   用法: {cmd_info['usage']}",
            "",
            "   示例:"
        ]
        
        for example in cmd_info['examples']:
            lines.append(f"     {example}")
        
        return "\n".join(lines)
    
    def _get_all_commands_help(self) -> str:
        """获取所有命令的帮助"""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       🤖 智能体助手 - 命令帮助       ║",
            "╚══════════════════════════════════════╝",
            "",
            "📋 可用命令:",
            ""
        ]
        
        for cmd_name, cmd_info in sorted(self.commands.items()):
            lines.append(f"  • {cmd_name:<15} {cmd_info['description']}")
        
        lines.extend([
            "",
            "💡 使用技巧:",
        ])
        
        # 随机显示3个技巧
        import random
        tips = random.sample(self.tips, min(3, len(self.tips)))
        for tip in tips:
            lines.append(f"  {tip}")
        
        lines.extend([
            "",
            "📝 更多信息请查看 OPTIMIZATION_REPORT.md",
            ""
        ])
        
        return "\n".join(lines)
    
    def get_random_tip(self) -> str:
        """获取随机提示"""
        import random
        return random.choice(self.tips)
    
    def get_skill_usage_help(self, skill_name: str, skill_info: dict) -> str:
        """
        获取技能使用说明
        
        Args:
            skill_name: 技能名称
            skill_info: 技能信息字典
            
        Returns:
            使用说明文本
        """
        lines = [
            f"🔧 技能: {skill_name}",
            f"   说明: {skill_info.get('description', '无描述')}",
            ""
        ]
        
        usage = skill_info.get('usage', '')
        if usage:
            lines.append(f"   用法:")
            for line in usage.split('\n'):
                lines.append(f"     {line}")
        
        return "\n".join(lines)


# 全局帮助系统实例
help_system = HelpSystem()


def show_help(command: Optional[str] = None) -> str:
    """显示帮助（便捷函数）"""
    return help_system.get_help(command)


if __name__ == "__main__":
    # 测试
    print(show_help())
    print("\n" + "="*60 + "\n")
    print(show_help("skills"))
