# -*- coding: utf-8 -*-
"""
JwClaw Core - 极简Agent核心
零框架依赖，仅使用openai客户端
"""

import json
import os
import re
from typing import Callable, Dict, List, Optional
from openai import OpenAI


class Tool:
    """工具定义"""
    
    def __init__(self, name: str, description: str, func: Callable, params: dict = None):
        self.name = name
        self.description = description
        self.func = func
        self.params = params or {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "查询参数"}
            },
            "required": ["query"]
        }
    
    def execute(self, **kwargs) -> str:
        try:
            return str(self.func(**kwargs))
        except Exception as e:
            return f"错误: {e}"
    
    def to_schema(self) -> dict:
        """转换为OpenAI Function Calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.params
            }
        }


class Agent:
    """极简ReAct Agent"""
    
    def __init__(self, client: OpenAI, model: str, system_prompt: str = None):
        self.client = client
        self.model = model
        self.tools: Dict[str, Tool] = {}
        self.messages: List[dict] = []
        self.max_iterations = 5
        
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def register_skills(self, skills_dir: str = "skills"):
        """从目录加载skills"""
        if not os.path.exists(skills_dir):
            return
        
        for name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, name, "SKILL.md")
            if os.path.exists(skill_path):
                tool = self._parse_skill(name, skill_path)
                if tool:
                    self.register_tool(tool)
    
    def _parse_skill(self, name: str, path: str) -> Optional[Tool]:
        """解析SKILL.md为Tool"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 提取描述 - 优先从YAML frontmatter提取
            desc_match = re.search(r'description:\s*[\'"]([^\'"]+)[\'"]', content)
            if not desc_match:
                # 尝试从 ## 描述 或 ## Description 提取
                desc_match = re.search(r'##\s*(?:描述|Description)\s*\n+([^\n]+)', content, re.IGNORECASE)
            description = desc_match.group(1) if desc_match else f"执行 {name}"
            
            # 提取执行代码 - 查找 "## 执行代码" 或 "## Execution" 后的代码块
            code_match = None
            
            # 优先查找标记为"执行代码"的代码块
            exec_section = re.search(r'##\s*(?:执行代码|Execution|执行)\s*\n+```python\n(.*?)```', content, re.DOTALL | re.IGNORECASE)
            if exec_section:
                code_match = exec_section
            else:
                # 查找 "# skill:" 标记后的第一个代码块（旧格式兼容）
                skill_section = re.search(r'#\s*skill:\s*\w+.*?```python\n(.*?)```', content, re.DOTALL | re.IGNORECASE)
                if skill_section:
                    code_match = skill_section
            
            if not code_match:
                return None
            
            code = code_match.group(1)
            
            # 动态创建执行函数
            def make_exec(skill_code):
                def execute(query: str = "", **kwargs):
                    local_vars = {
                        "args": [query] if query else [],
                        "kwargs": kwargs,
                        "result": None
                    }
                    exec(skill_code, local_vars)
                    return local_vars.get("result", "执行完成")
                return execute
            
            return Tool(name, description, make_exec(code))
        except Exception as e:
            print(f"[WARN] 加载skill失败 {name}: {e}")
            return None
    
    def run(self, user_input: str) -> str:
        """执行用户输入"""
        self.messages.append({"role": "user", "content": user_input})
        
        for i in range(self.max_iterations):
            # 调用LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=[t.to_schema() for t in self.tools.values()] if self.tools else None,
                stream=False
            )
            
            message = response.choices[0].message
            
            # 检查是否调用工具
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 [{tool_name}] {tool_args}")
                
                # 执行工具
                if tool_name in self.tools:
                    result = self.tools[tool_name].execute(**tool_args)
                else:
                    result = f"未知工具: {tool_name}"
                
                # 截断显示
                display_result = result[:200] + "..." if len(result) > 200 else result
                print(f"📤 {display_result}")
                
                # 添加工具调用和结果到历史
                self.messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{"id": tool_call.id, "type": "function", "function": {"name": tool_name, "arguments": tool_call.function.arguments}}]
                })
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            else:
                # 直接回复
                reply = message.content
                self.messages.append({"role": "assistant", "content": reply})
                return reply
        
        return "达到最大迭代次数"
    
    def clear(self):
        """清空对话历史（保留system）"""
        if self.messages and self.messages[0]["role"] == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages = []


# 内置工具
def shell_tool(command: str) -> str:
    """执行shell命令"""
    import subprocess
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout or result.stderr or "执行完成"
    except Exception as e:
        return f"执行失败: {e}"


def create_default_tools() -> List[Tool]:
    """创建默认工具集"""
    return [
        Tool("shell", "执行系统shell命令", shell_tool, {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"}
            },
            "required": ["command"]
        })
    ]
