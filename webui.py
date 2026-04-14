#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JwClaw Web UI - 基于Flask的Web界面
"""

import os
import sys
import json
import subprocess
import threading

# 自动安装依赖
def check_and_install_dependencies():
    """检查并安装缺失的依赖"""
    required_packages = [
        'flask',
        'flask-socketio',
        'python-socketio',
        'simple-websocket'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("\n" + "="*60)
        print("  📦 检测到缺失的依赖包")
        print("="*60)
        print(f"\n缺失的包: {', '.join(missing_packages)}")
        print("\n正在自动安装...")
        print("-"*60)
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            
            print("\n✅ 依赖安装成功！")
            print("="*60 + "\n")
            
            # 重新导入
            for package in missing_packages:
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    pass
                    
        except subprocess.CalledProcessError as e:
            print(f"\n❌ 依赖安装失败: {e}")
            print("\n请手动运行以下命令安装:")
            print(f"pip install {' '.join(missing_packages)}")
            input("\n按任意键退出...")
            sys.exit(1)

# 执行依赖检查
check_and_install_dependencies()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jwclaw import (
    load_config, load_skills, load_memories, 
    build_system_prompt, run as agent_run
)

# 初始化Flask应用
app = Flask(__name__, 
            template_folder='webui/templates',
            static_folder='webui/static')
app.config['SECRET_KEY'] = 'jwclaw-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局状态
conversation_history = []
skills_cache = None
memories_cache = None
config_cache = None

def initialize_system():
    """初始化系统"""
    global skills_cache, memories_cache, config_cache
    
    print("🔄 正在加载系统...")
    
    # 加载配置
    config_cache = load_config()
    print(f"✅ 配置加载完成")
    
    # 加载Skills
    skills_cache = load_skills()
    print(f"✅ 已加载 {len(skills_cache)} 个Skills")
    
    # 加载记忆
    memories_cache = load_memories()
    print(f"✅ 已加载 {len(memories_cache)} 条记忆")
    
    # 初始化对话历史
    if not conversation_history:
        conversation_history.append({
            "role": "system", 
            "content": build_system_prompt(skills_cache, memories_cache)
        })

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify({
        "status": "running",
        "skills_count": len(skills_cache) if skills_cache else 0,
        "memories_count": len(memories_cache) if memories_cache else 0,
        "model": config_cache.get('model', 'unknown') if config_cache else 'unknown'
    })

@app.route('/api/skills')
def get_skills():
    """获取Skills列表"""
    if skills_cache:
        skills_list = [
            {
                "name": name,
                "description": skill.get('description', '')[:100]
            }
            for name, skill in skills_cache.items()
        ]
        return jsonify(skills_list)
    return jsonify([])

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print("📱 客户端已连接")
    emit('status', {'message': '已连接到JwClaw'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print("📱 客户端已断开")

@socketio.on('send_message')
def handle_message(data):
    """处理用户消息"""
    user_message = data.get('message', '').strip()
    
    if not user_message:
        emit('error', {'message': '消息不能为空'})
        return
    
    print(f"\n👤 用户: {user_message}")
    
    # 发送思考状态
    emit('thinking', {'status': True})
    
    try:
        # 运行Agent
        full_reply = ""
        
        # 这里需要修改agent_run函数以支持流式输出
        # 暂时使用简化版本
        from jwclaw import client, MODEL_REF
        
        # 添加用户消息到对话历史
        conversation_history.append({"role": "user", "content": user_message})
        
        # 调用LLM
        stream = client.chat.completions.create(
            model=MODEL_REF[0],
            messages=conversation_history,
            stream=True
        )
        
        # 流式输出
        thinking = False
        for chunk in stream:
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, 'reasoning_content', None)
            content = delta.content or ""
            
            if reasoning:
                if not thinking:
                    emit('thinking_content', {'content': '\n[思考] ', 'type': 'start'})
                    thinking = True
                emit('thinking_content', {'content': reasoning, 'type': 'stream'})
            
            if content:
                if thinking:
                    emit('thinking_content', {'content': '\n[回复] ', 'type': 'separator'})
                    thinking = False
                emit('reply_content', {'content': content, 'type': 'stream'})
                full_reply += content
        
        # 完成
        emit('thinking', {'status': False})
        emit('message_complete', {'reply': full_reply})
        
        # 添加到对话历史
        conversation_history.append({"role": "assistant", "content": full_reply})
        
        # 检查是否有工具调用
        from jwclaw import parse_tool_call, execute_skill
        tool_name, raw_args = parse_tool_call(full_reply)
        
        if tool_name:
            emit('tool_call', {
                'tool': tool_name,
                'args': raw_args
            })
            
            # 执行工具
            if tool_name == 'create_skill':
                result = "Skill创建功能在Web UI中暂不支持"
            elif tool_name in skills_cache:
                result = execute_skill(skills_cache[tool_name], raw_args)
            else:
                result = f"未知工具: {tool_name}"
            
            emit('tool_result', {
                'tool': tool_name,
                'result': result
            })
            
            # 添加工具结果到对话
            conversation_history.append({
                "role": "user", 
                "content": f"工具执行结果: {result}"
            })
            
            # 继续对话
            continue_conversation()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        emit('error', {'message': f'执行出错: {str(e)}'})
        emit('thinking', {'status': False})

def continue_conversation():
    """继续对话（处理工具调用后的响应）"""
    try:
        from jwclaw import client, MODEL_REF
        
        stream = client.chat.completions.create(
            model=MODEL_REF[0],
            messages=conversation_history,
            stream=True
        )
        
        full_reply = ""
        thinking = False
        
        for chunk in stream:
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, 'reasoning_content', None)
            content = delta.content or ""
            
            if reasoning:
                if not thinking:
                    emit('thinking_content', {'content': '\n[思考] ', 'type': 'start'})
                    thinking = True
                emit('thinking_content', {'content': reasoning, 'type': 'stream'})
            
            if content:
                if thinking:
                    emit('thinking_content', {'content': '\n[回复] ', 'type': 'separator'})
                    thinking = False
                emit('reply_content', {'content': content, 'type': 'stream'})
                full_reply += content
        
        emit('thinking', {'status': False})
        emit('message_complete', {'reply': full_reply})
        conversation_history.append({"role": "assistant", "content": full_reply})
        
    except Exception as e:
        print(f"❌ 继续对话出错: {e}")
        emit('error', {'message': f'错误: {str(e)}'})

@socketio.on('clear_history')
def handle_clear_history():
    """清空对话历史"""
    global conversation_history
    conversation_history = [{
        "role": "system",
        "content": build_system_prompt(skills_cache, memories_cache)
    }]
    emit('history_cleared', {'message': '对话历史已清空'})

def main():
    """启动Web UI"""
    print("\n" + "="*60)
    print("  JwClaw Web UI")
    print("="*60)
    
    # 初始化系统
    initialize_system()
    
    print("\n🌐 Web UI 启动中...")
    print("📍 访问地址: http://localhost:5000")
    print("⚠️  按 Ctrl+C 停止服务\n")
    
    # 启动Flask应用
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()
