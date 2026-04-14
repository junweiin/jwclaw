#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JwClaw - 极简智能体
默认CLI交互，Skill优先执行
"""

import json
import os
import sys
from pathlib import Path

# 配置路径
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = SCRIPT_DIR / "config.json"


def load_config() -> dict:
    """加载配置"""
    default = {
        "api_base": "http://localhost:1234/v1",
        "model": "local-model",
        "api_key": "lm-studio"
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**default, **json.load(f)}
        except Exception as e:
            print(f"[WARN] 配置加载失败: {e}")
    
    # 创建默认配置
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default, f, indent=2, ensure_ascii=False)
    
    return default


def create_system_prompt(tools_info: str) -> str:
    """创建system prompt"""
    return f"""你是一个智能助手，帮助用户完成各种任务。

可用工具：
{tools_info}

规则：
1. 优先使用工具完成任务
2. 每次只调用一个工具
3. 用中文简洁回复
4. 不要说自己无法做什么，直接尝试使用工具"""


def main():
    # 延迟导入，提高启动速度
    from openai import OpenAI
    from .core import Agent, create_default_tools
    
    # 加载配置
    config = load_config()
    
    # 创建客户端
    client = OpenAI(
        base_url=config["api_base"],
        api_key=config["api_key"]
    )
    
    # 创建Agent
    agent = Agent(
        client=client,
        model=config["model"],
        system_prompt=None  # 稍后设置
    )
    
    # 注册默认工具
    for tool in create_default_tools():
        agent.register_tool(tool)
    
    # 注册skills
    skills_dir = SCRIPT_DIR / "skills"
    agent.register_skills(str(skills_dir))
    
    # 构建system prompt
    tools_info = "\n".join([
        f"- {name}: {tool.description}"
        for name, tool in agent.tools.items()
    ])
    agent.messages.insert(0, {
        "role": "system",
        "content": create_system_prompt(tools_info)
    })
    
    # 启动CLI
    print("=" * 50)
    print("🤖 JwClaw 智能体")
    print("=" * 50)
    print(f"模型: {config['model']}")
    print(f"API: {config['api_base']}")
    print(f"工具: {len(agent.tools)} 个")
    print("-" * 50)
    print("命令: /clear 清空对话, /exit 退出")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            # 命令处理
            if user_input.startswith("/"):
                cmd = user_input[1:].lower()
                if cmd in ["exit", "quit", "退出"]:
                    print("👋 再见!")
                    break
                elif cmd == "clear":
                    agent.clear()
                    print("🗑️ 对话已清空")
                    continue
                elif cmd == "tools":
                    print("\n".join([f"- {n}: {t.description}" for n, t in agent.tools.items()]))
                    continue
                else:
                    print(f"未知命令: {cmd}")
                    continue
            
            # 执行
            reply = agent.run(user_input)
            print(f"\n{reply}")
            
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
