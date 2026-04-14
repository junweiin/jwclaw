"""
JwClaw - 极简智能体

一个轻量级、无框架依赖的 AI Agent，默认 CLI 交互，Skill 优先执行。
"""

__version__ = "0.3.0"
__author__ = "JwClaw Team"

from .core import Agent, Tool, create_default_tools

__all__ = ["Agent", "Tool", "create_default_tools"]
