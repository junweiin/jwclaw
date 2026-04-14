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
    # 包名到导入名的映射
    package_import_map = {
        'flask': 'flask',
        'flask-socketio': 'flask_socketio',
        'python-socketio': 'socketio',
        'simple-websocket': 'simple_websocket'
    }
    
    missing_packages = []
    for package, import_name in package_import_map.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("\n" + "="*60)
        print("  [PKG] 检测到缺失的依赖包")
        print("="*60)
        print(f"\n缺失的包: {', '.join(missing_packages)}")
        print("\n正在自动安装...")
        print("-"*60)
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            
            print("\n[OK] 依赖安装成功！")
            print("="*60 + "\n")
            
            # 重新导入
            for package in missing_packages:
                import_name = package_import_map.get(package, package.replace('-', '_'))
                try:
                    __import__(import_name)
                except ImportError:
                    pass
                    
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] 依赖安装失败: {e}")
            print("\n请手动运行以下命令安装:")
            print(f"pip install {' '.join(missing_packages)}")
            input("\n按任意键退出...")
            sys.exit(1)

# 执行依赖检查
check_and_install_dependencies()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit as _emit

# 使用 socketio.emit 替代 emit，确保在多线程环境中正常工作
def emit(event, data):
    """线程安全的 emit 函数"""
    socketio.emit(event, data)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jwclaw import (
    load_config, load_skills, load_memory, 
    build_system_prompt, run as agent_run,
    reload_config, parse_tool_call, execute_skill  # 添加这两个函数的导入
)
import jwclaw  # 导入整个模块以获取最新的client和MODEL_REF

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
stop_flag = threading.Event()  # 停止标志
history_lock = threading.Lock()  # 保护 conversation_history
cache_lock = threading.Lock()    # 保护 skills_cache 和 memories_cache
MAX_HISTORY_LENGTH = 100  # 最大对话历史长度，防止内存泄漏

def initialize_system():
    """初始化系统"""
    global skills_cache, memories_cache, config_cache
    
    print("[LOAD] 正在加载系统...")
    
    # 加载配置
    config_cache = load_config()
    print(f"[OK] 配置加载完成")
    
    # 加载Skills
    skills_cache = load_skills()
    print(f"[OK] 已加载 {len(skills_cache)} 个Skills")
    
    # 加载记忆
    memories_cache = load_memory()
    print(f"[OK] 已加载 {len(memories_cache)} 条记忆")
    
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

@app.route('/api/history')
def get_history():
    """获取对话历史"""
    with history_lock:
        # 过滤掉system消息，只返回用户和助手的对话
        history = [
            msg for msg in conversation_history 
            if msg['role'] in ['user', 'assistant']
        ]
    return jsonify(history)

@app.route('/api/models')
def get_models():
    """获取模型列表"""
    models_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models.json')
    
    if os.path.exists(models_path):
        with open(models_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data.get('models', []))
    else:
        # 返回默认模型
        return jsonify([{
            "name": config_cache.get('model', 'unknown'),
            "api_base": config_cache.get('api_base', ''),
            "api_key": config_cache.get('api_key', ''),
            "description": "当前使用的模型"
        }])

@app.route('/api/model/switch', methods=['POST'])
def switch_model():
    """切换模型"""
    try:
        data = request.json
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({"success": False, "error": "请指定模型名称"})
        
        models_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models.json')
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        
        # 加载模型列表
        if os.path.exists(models_path):
            with open(models_path, 'r', encoding='utf-8') as f:
                models_data = json.load(f)
        else:
            return jsonify({"success": False, "error": "模型配置文件不存在"})
        
        # 查找目标模型
        target_model = next((m for m in models_data['models'] if m['name'] == model_name), None)
        
        if not target_model:
            return jsonify({"success": False, "error": f"找不到模型: {model_name}"})
        
        # 更新config.json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['model'] = target_model['name']
        config['api_base'] = target_model['api_base']
        config['api_key'] = target_model['api_key']
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 更新models.json中的current
        models_data['current'] = model_name
        with open(models_path, 'w', encoding='utf-8') as f:
            json.dump(models_data, f, indent=2, ensure_ascii=False)
        
        # 🚀 关键改进：动态重载配置，无需重启
        print(f"\n[RELOAD] 正在重载配置...")
        with jwclaw.config_lock:
            print(f"   切换前: model={jwclaw.MODEL_REF[0]}, base_url={jwclaw.client.base_url}")
        new_config = reload_config()
        with jwclaw.config_lock:
            print(f"   切换后: model={jwclaw.MODEL_REF[0]}, base_url={jwclaw.client.base_url}")
        print(f"✅ 配置重载成功！当前模型: {new_config.get('model')}")
        
        # 更新全局缓存
        global config_cache
        config_cache = new_config
        
        return jsonify({
            "success": True, 
            "message": f"已切换到 {model_name}（立即生效）"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/model/add', methods=['POST'])
def add_model():
    """添加新模型"""
    try:
        data = request.json
        name = data.get('name')
        api_base = data.get('api_base')
        api_key = data.get('api_key')
        description = data.get('description', '')
        
        if not name or not api_base or not api_key:
            return jsonify({"success": False, "error": "缺少必填字段"})
        
        models_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models.json')
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        
        # 加载或创建模型列表
        if os.path.exists(models_path):
            with open(models_path, 'r', encoding='utf-8') as f:
                models_data = json.load(f)
        else:
            # 如果models.json不存在，从 config.json创建初始模型列表
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            models_data = {
                "models": [
                    {
                        "name": config.get('model', 'unknown'),
                        "api_base": config.get('api_base', ''),
                        "api_key": config.get('api_key', ''),
                        "description": "默认模型"
                    }
                ],
                "current": config.get('model', 'unknown')
            }
        
        # 检查是否已存在
        existing = next((m for m in models_data['models'] if m['name'] == name), None)
        if existing:
            return jsonify({"success": False, "error": f"模型 {name} 已存在"})
        
        # 添加新模型
        new_model = {
            "name": name,
            "api_base": api_base,
            "api_key": api_key,
            "description": description
        }
        models_data['models'].append(new_model)
        
        # 保存
        with open(models_path, 'w', encoding='utf-8') as f:
            json.dump(models_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True, "message": f"已添加模型: {name}"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/model/edit', methods=['POST'])
def edit_model():
    """编辑模型"""
    try:
        data = request.json
        original_name = data.get('original_name')
        name = data.get('name')
        api_base = data.get('api_base')
        api_key = data.get('api_key')
        description = data.get('description', '')
        
        if not original_name or not name or not api_base or not api_key:
            return jsonify({"success": False, "error": "缺少必填字段"})
        
        models_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models.json')
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        
        # 加载模型列表
        if not os.path.exists(models_path):
            return jsonify({"success": False, "error": "模型配置文件不存在"})
        
        with open(models_path, 'r', encoding='utf-8') as f:
            models_data = json.load(f)
        
        # 查找原模型
        model_index = next((i for i, m in enumerate(models_data['models']) if m['name'] == original_name), None)
        if model_index is None:
            return jsonify({"success": False, "error": f"找不到模型: {original_name}"})
        
        # 如果修改了名称，检查新名称是否与其他模型冲突
        if name != original_name:
            existing = next((m for m in models_data['models'] if m['name'] == name), None)
            if existing:
                return jsonify({"success": False, "error": f"模型 {name} 已存在"})
        
        # 更新模型信息
        models_data['models'][model_index] = {
            "name": name,
            "api_base": api_base,
            "api_key": api_key,
            "description": description
        }
        
        # 如果当前使用的是该模型，且名称改变了，需要更新current和config.json
        current_model = models_data.get('current')
        config_changed = False
        
        if current_model == original_name:
            # 更新config.json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查是否有变化
            if (config.get('model') != name or
                config.get('api_base') != api_base or
                config.get('api_key') != api_key):
                config_changed = True
            
            config['model'] = name
            config['api_base'] = api_base
            config['api_key'] = api_key
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 如果名称改变，也更新models.json的current
            if name != original_name:
                models_data['current'] = name
        
        # 保存models.json
        with open(models_path, 'w', encoding='utf-8') as f:
            json.dump(models_data, f, indent=2, ensure_ascii=False)
        
        # 🚀 如果编辑的是当前模型且配置有变化，动态重载
        if config_changed:
            print(f"\n[RELOAD] 检测到当前模型配置变更，正在重载...")
            new_config = reload_config()
            print(f"[OK] 配置重载成功！当前模型: {new_config.get('model')}")
            
            # 更新全局缓存
            global config_cache
            config_cache = new_config
        
        return jsonify({"success": True, "message": f"已更新模型: {name}"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/model/delete', methods=['POST'])
def delete_model():
    """删除模型"""
    try:
        data = request.json
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({"success": False, "error": "请指定模型名称"})
        
        models_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models.json')
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        
        # 加载模型列表
        if not os.path.exists(models_path):
            return jsonify({"success": False, "error": "模型配置文件不存在"})
        
        with open(models_path, 'r', encoding='utf-8') as f:
            models_data = json.load(f)
        
        # 查找模型
        model_index = next((i for i, m in enumerate(models_data['models']) if m['name'] == model_name), None)
        if model_index is None:
            return jsonify({"success": False, "error": f"找不到模型: {model_name}"})
        
        # 检查是否是当前使用的模型
        current_model = models_data.get('current')
        if current_model == model_name:
            return jsonify({"success": False, "error": "不能删除当前正在使用的模型，请先切换到其他模型"})
        
        # 删除模型
        deleted_model = models_data['models'].pop(model_index)
        
        # 保存
        with open(models_path, 'w', encoding='utf-8') as f:
            json.dump(models_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True, "message": f"已删除模型: {deleted_model['name']}"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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

@socketio.on('stop_generation')
def handle_stop_generation():
    """处理停止生成请求"""
    print("\n⏹ 用户请求停止生成")
    stop_flag.set()
    emit('generation_stopped', {'message': '已停止生成'})

@socketio.on('send_message')
def handle_message(data):
    """处理用户消息 - 与CLI保持一致的完整Agent逻辑"""
    global conversation_history, skills_cache  # 声明全局变量
    
    user_message = data.get('message', '').strip()
    
    if not user_message:
        emit('error', {'message': '消息不能为空'})
        return
    
    print(f"\n👤 用户: {user_message}")
    
    # 发送思考状态
    emit('thinking', {'status': True})
    
    # 清除之前的停止标志
    stop_flag.clear()
    
    # 初始化变量（避免作用域问题）
    full_reply = ""
    max_iterations = 5
    iteration = 0
    reached_max_iterations = False
    
    try:
        # 添加用户消息到对话历史
        with history_lock:
            conversation_history.append({"role": "user", "content": user_message})
            # 限制历史长度，保留system消息和最近的N条消息
            if len(conversation_history) > MAX_HISTORY_LENGTH:
                system_msg = conversation_history[0]
                conversation_history = [system_msg] + conversation_history[-(MAX_HISTORY_LENGTH-1):]
        
        # 最多5轮迭代（与CLI一致）
        for iteration in range(max_iterations):
            # 检查是否被用户中断
            if stop_flag.is_set():
                print("⏹ 检测到停止信号，中断生成")
                stop_flag.clear()  # 清除标志，为下次使用做准备
                emit('thinking', {'status': False})
                emit('message_complete', {'reply': full_reply})
                return
            
            print(f"\n[ITER] 对话轮次: {iteration + 1}")
            full_reply = ""
            
            # 调用LLM（从 jwclaw 模块获取最新的 client 和 MODEL_REF）
            with jwclaw.config_lock:
                current_client = jwclaw.client
                current_model = jwclaw.MODEL_REF[0]
            
            print(f"[DEBUG] 使用模型: {current_model}")
            print(f"[DEBUG] API地址: {current_client.base_url}")
            print(f"[DEBUG] 对话历史消息数: {len(conversation_history)}")
            
            # 检查对话历史是否为空或格式错误
            if not conversation_history or len(conversation_history) == 0:
                print("[ERROR] 对话历史为空")
                emit('reply_content', {'content': '错误: 对话历史为空', 'type': 'stream'})
                emit('thinking', {'status': False})
                emit('message_complete', {'reply': '错误: 对话历史为空'})
                return
            
            # 打印第一条消息（system prompt）
            if conversation_history:
                first_msg = conversation_history[0]
                print(f"[DEBUG] 第一条消息角色: {first_msg.get('role', 'unknown')}")
                print(f"[DEBUG] 第一条消息长度: {len(first_msg.get('content', ''))}")
                # 检查system prompt中是否包含工具列表
                system_content = first_msg.get('content', '')
                if 'web_search' in system_content:
                    print(f"[DEBUG] system prompt包含web_search工具")
                else:
                    print(f"[WARN] system prompt未包含web_search工具")
            
            try:
                stream = current_client.chat.completions.create(
                    model=current_model,
                    messages=conversation_history,
                    stream=True
                )
            except Exception as e:
                print(f"[ERROR] LLM调用失败: {e}")
                emit('reply_content', {'content': f'LLM调用失败: {str(e)}', 'type': 'stream'})
                emit('thinking', {'status': False})
                emit('message_complete', {'reply': f'LLM调用失败: {str(e)}'})
                return
            
            # 流式输出
            chunk_count = 0
            content_count = 0
            has_reasoning = False  # 标记是否收到 reasoning_content
            
            for chunk in stream:
                chunk_count += 1
                # 检查是否被用户中断
                if stop_flag.is_set():
                    print("⏹ 流式生成中被中断")
                    stream.close()
                    stop_flag.clear()
                    emit('thinking', {'status': False})
                    emit('message_complete', {'reply': full_reply})
                    return
                
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, 'reasoning_content', None)
                content = delta.content or ""
                
                # 记录是否收到 reasoning_content（用于调试）
                if reasoning and not has_reasoning:
                    has_reasoning = True
                    print(f"[WARN] 收到 reasoning_content，模型可能不支持 disable_thinking")
                
                if content:
                    content_count += 1
                    if content_count <= 3 or content_count % 10 == 0:
                        print(f"[DEBUG] 收到内容 #{content_count}: '{content[:50]}...'")
                    
                    # 发送内容到前端
                    try:
                        emit('reply_content', {'content': content, 'type': 'stream'})
                    except Exception as e:
                        print(f"[ERROR] 发送reply_content失败: {e}")
                    
                    full_reply += content
            
            print(f"[OK] LLM回复完成 - chunks: {chunk_count}, content: {content_count}, has_reasoning: {has_reasoning}, total_length: {len(full_reply)}")
            
            # 如果LLM没有返回任何内容，给出提示
            if not full_reply:
                print("[WARN] LLM返回空内容，可能是模型配置问题")
                print(f"[DEBUG] 当前模型: {current_model}, 对话历史长度: {len(conversation_history)}")
                full_reply = "抱歉，我暂时无法处理您的请求。请检查模型配置是否正确。"
                # 不在这里发送 reply_content，让 message_complete 统一处理
            
            # 如果LLM返回默认问候语，可能是system prompt没有生效
            if full_reply == "你好！有什么我可以帮助你的吗？":
                print("[WARN] LLM返回默认问候语，system prompt可能未生效")
                print(f"[DEBUG] 当前模型: {current_model}")
                print(f"[DEBUG] 对话历史第一条: {conversation_history[0] if conversation_history else 'None'}")
            
            # 添加到对话历史
            with history_lock:
                conversation_history.append({"role": "assistant", "content": full_reply})
                # 限制历史长度
                if len(conversation_history) > MAX_HISTORY_LENGTH:
                    system_msg = conversation_history[0]
                    conversation_history = [system_msg] + conversation_history[-(MAX_HISTORY_LENGTH-1):]
            
            # 检测工具调用
            tool_name, raw_args = parse_tool_call(full_reply)
            
            if not tool_name:
                # 没有工具调用，结束对话
                print("[OK] 无工具调用，对话结束")
                emit('thinking', {'status': False})
                emit('message_complete', {'reply': full_reply})
                break
            
            # 有工具调用，执行工具
            print(f"[TOOL] 检测到工具调用: {tool_name}({raw_args})")
            emit('tool_call', {
                'tool': tool_name,
                'args': raw_args
            })
            
            # 执行工具
            result = ""
            if tool_name == 'create_skill':
                result = "Skill创建功能在Web UI中暂不支持，请使用CLI模式"
            elif tool_name in skills_cache:
                try:
                    # 每次执行前重新加载skills，确保用最新版本
                    try:
                        with cache_lock:
                            skills_cache = load_skills()
                    except Exception as reload_err:
                        print(f"[WARN] 重新加载skills失败，使用缓存: {reload_err}")
                        # 继续使用旧的skills_cache
                    
                    print(f"[EXEC] 执行技能: {tool_name}")
                    with cache_lock:
                        result = execute_skill(skills_cache[tool_name], raw_args)
                    print(f"[OK] 执行成功，结果长度: {len(result)}")
                except Exception as e:
                    print(f"[ERROR] 执行失败: {e}")
                    import traceback
                    traceback.print_exc()
                    result = f"[ERROR] 工具执行错误: {str(e)}"
            else:
                print(f"[WARN] 未知工具: {tool_name}")
                result = f"❌ 未知工具: {tool_name}"
            
            # 发送工具结果
            emit('tool_result', {
                'tool': tool_name,
                'result': result
            })
            
            # 将工具结果添加到对话历史，让LLM继续
            with history_lock:
                conversation_history.append({
                    "role": "user", 
                    "content": f"工具执行结果: {result}"
                })
                # 限制历史长度
                if len(conversation_history) > MAX_HISTORY_LENGTH:
                    system_msg = conversation_history[0]
                    conversation_history = [system_msg] + conversation_history[-(MAX_HISTORY_LENGTH-1):]
            
            print(f"📤 工具结果已返回给LLM，继续下一轮...")
        else:
            # for-else: 只有在循环完整执行（没有被break）时才执行
            reached_max_iterations = True
        
        # 如果达到最大迭代次数
        if reached_max_iterations:
            print("⚠️  达到最大迭代次数(5轮)")
            emit('thinking', {'status': False})
            emit('message_complete', {'reply': full_reply})
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'执行出错: {str(e)}'})
        emit('thinking', {'status': False})

@socketio.on('clear_history')
def handle_clear_history():
    """清空对话历史"""
    global conversation_history, skills_cache, memories_cache
    
    # 重新加载最新数据，避免使用过期的缓存
    try:
        with cache_lock:
            skills_cache = load_skills()
            memories_cache = load_memory()
            print(f"[OK] 重新加载 {len(skills_cache)} 个skills")
    except Exception as e:
        print(f"[WARN] 重新加载数据失败: {e}，使用现有缓存")
    
    with history_lock:
        system_prompt = build_system_prompt(skills_cache, memories_cache)
        conversation_history = [{
            "role": "system",
            "content": system_prompt
        }]
        # 检查system prompt是否包含web_search
        if 'web_search' in system_prompt:
            print("[DEBUG] 新system prompt包含web_search工具")
        else:
            print("[WARN] 新system prompt未包含web_search工具")
    
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
    
    # 自动打开浏览器
    try:
        import webbrowser
        print("🔗 正在打开浏览器...")
        webbrowser.open('http://localhost:5000')
    except Exception as e:
        print(f"⚠️  无法自动打开浏览器: {e}")
        print("请手动访问: http://localhost:5000")
    
    # 启动Flask应用
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()
