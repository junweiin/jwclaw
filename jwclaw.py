# -*- coding: utf-8 -*-
# jwclaw.py - JwClaw 智能体系统主程序（智能核心 + 进化引擎）

from openai import OpenAI
import re, os, threading, time, sys, json, hashlib, logging, platform, subprocess
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 导入安全模块
try:
    from secure_config import get_secure_api_key, get_secure_config
    SECURE_CONFIG_AVAILABLE = True
except ImportError:
    SECURE_CONFIG_AVAILABLE = False
    logger.warning("安全配置模块未找到，使用传统配置方式")

try:
    from sandbox import execute_in_sandbox
    SANDBOX_AVAILABLE = True
except ImportError:
    SANDBOX_AVAILABLE = False
    logger.warning("沙箱模块未找到，使用传统exec方式")

try:
    from help_system import help_system
    HELP_SYSTEM_AVAILABLE = True
except ImportError:
    HELP_SYSTEM_AVAILABLE = False
    logger.warning("帮助系统模块未找到")

try:
    from skill_metadata import metadata_manager, record_skill_usage
    SKILL_METADATA_AVAILABLE = True
except ImportError:
    SKILL_METADATA_AVAILABLE = False
    logger.warning("Skill元数据模块未找到")

try:
    from cache import get_cached_llm_response, cache_llm_response
    from cache import get_cached_skill_result, cache_skill_result
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("缓存模块未找到")

try:
    from rules_engine import rules_engine, check_safety, get_guideline
    RULES_ENGINE_AVAILABLE = True
except ImportError:
    RULES_ENGINE_AVAILABLE = False
    logger.warning("规则引擎模块未找到")

try:
    from context_manager import context_manager, get_user_info, add_memory
    CONTEXT_MANAGER_AVAILABLE = True
except ImportError:
    CONTEXT_MANAGER_AVAILABLE = False
    logger.warning("上下文管理器模块未找到")

# 使用绝对路径，确保从任何目录运行都能找到文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
SKILLS_DIR  = os.path.join(SCRIPT_DIR, "skills")
MEMORY_FILE = os.path.join(SCRIPT_DIR, "memory.json")
LOG_FILE    = os.path.join(SCRIPT_DIR, "agent.log")

# ─── 日志系统初始化 ──────────────────────────────────────────────────────────

def setup_logging(debug_mode=False):
    """配置日志系统：文件日志+控制台日志"""
    logger = logging.getLogger("agent")
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # 清除已有handler
    logger.handlers.clear()
    
    # 文件handler - 轮转日志，最大10MB，保留5个备份
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # 控制台handler - 仅显示INFO及以上级别
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING if not debug_mode else logging.INFO)
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# ─── 自定义异常类 ─────────────────────────────────────────────────────────────

class AgentException(Exception):
    """智能体基础异常类"""
    pass

class ConfigError(AgentException):
    """配置错误"""
    pass

class SkillExecutionError(AgentException):
    """Skill执行错误"""
    def __init__(self, skill_name: str, message: str, original_error: Exception = None):
        self.skill_name = skill_name
        self.original_error = original_error
        super().__init__(f"Skill '{skill_name}' 执行失败: {message}")

class MemoryError(AgentException):
    """记忆系统错误"""
    pass

class LLMError(AgentException):
    """LLM调用错误"""
    pass

class ToolNotFoundError(AgentException):
    """工具未找到错误"""
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"未找到工具: {tool_name}")

class SkillGenerationError(AgentException):
    """Skill生成错误"""
    pass

# ─── 重试装饰器 ──────────────────────────────────────────────────────────────

def retry_on_failure(max_retries=3, delay=1, exceptions=(Exception,)):
    """重试装饰器：在指定异常发生时自动重试"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"{func.__name__} 第{attempt}次尝试失败: {e}")
                    if attempt < max_retries:
                        time.sleep(delay * attempt)  # 指数退避
                        logger.info(f"等待 {delay * attempt}s 后重试...")
                    else:
                        logger.error(f"{func.__name__} 达到最大重试次数 {max_retries}")
            raise last_exception
        return wrapper
    return decorator

# ─── 配置 ─────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """加载配置文件，支持安全配置模式"""
    try:
        # 优先使用安全配置模块
        if SECURE_CONFIG_AVAILABLE:
            config = get_secure_config()
            logger.debug("使用安全配置模块")
        else:
            # 回退到传统方式
            if not os.path.exists(CONFIG_FILE):
                default = {"api_base": "http://localhost:1234/v1", "model": "local-model", "api_key": "lm-studio"}
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(default, f, indent=2)
                logger.info(f"创建默认配置文件: {CONFIG_FILE}")
                return default
            
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.debug(f"配置文件加载成功: {CONFIG_FILE}")
        
        return config
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        raise ConfigError(f"配置文件格式错误: {e}") from e
    except FileNotFoundError as e:
        logger.error(f"配置文件不存在: {e}")
        raise ConfigError(f"配置文件不存在: {e}") from e
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        raise ConfigError(f"加载配置文件失败: {e}") from e

CONFIG    = load_config()
MODEL_REF = [CONFIG["model"]]

# 使用安全方式获取API密钥
if SECURE_CONFIG_AVAILABLE:
    api_key = get_secure_api_key()
else:
    api_key = CONFIG.get("api_key", "lm-studio")

client    = OpenAI(base_url=CONFIG["api_base"], api_key=api_key)
logger.info(f"初始化OpenAI客户端: model={MODEL_REF[0]}, base_url={CONFIG['api_base']}")

# 线程锁：保护共享状态
config_lock = threading.Lock()  # 保护 CONFIG 和 MODEL_REF
memory_lock = threading.Lock()  # 保护 memories 列表
skills_lock = threading.Lock()  # 保护 skills 字典

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

def make_stop_listener(stop_flag: threading.Event):
    """用 msvcrt 监听 ESC 键，不需要管理员权限"""
    def _listen():
        try:
            import msvcrt
            while not stop_flag.is_set():
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch == '\x1b':  # ESC
                        stop_flag.set()
                        return
                time.sleep(0.05)
        except Exception:
            pass
    t = threading.Thread(target=_listen, daemon=True)
    t.start()
    return t

# ─── Skills 加载 ──────────────────────────────────────────────────────────────

def load_skills() -> dict:
    """从skills目录加载所有skill定义，支持QClaw目录结构"""
    skills = {}
    if not os.path.exists(SKILLS_DIR):
        os.makedirs(SKILLS_DIR)
        logger.info(f"创建skills目录: {SKILLS_DIR}")
        return skills
    
    # 遍历skills目录
    for item in os.listdir(SKILLS_DIR):
        item_path = os.path.join(SKILLS_DIR, item)
        
        # QClaw格式：目录/SKILL.md
        if os.path.isdir(item_path):
            skill_file = os.path.join(item_path, "SKILL.md")
            if not os.path.exists(skill_file):
                continue
            
            try:
                with open(skill_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 从YAML frontmatter或文件名提取名称
                name = item  # 使用目录名作为skill名
                
                # 提取描述（从description字段或第一个标题）
                desc_match = re.search(r'description:\s*[\'"]([^\'"]+)[\'"]', content)
                if not desc_match:
                    desc_match = re.search(r'# (.+)', content)
                
                description = desc_match.group(1).strip() if desc_match else ""
                
                # 提取usage（如果有）
                usage_match = re.search(r'##\s*调用格式\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
                usage = usage_match.group(1).strip() if usage_match else ""
                
                # 提取Python代码（如果有）
                code_match = re.search(r'##\s*执行代码\s*\n```python\n(.*?)```', content, re.DOTALL)
                code = code_match.group(1) if code_match else None
                
                # 检查是否有scripts目录
                scripts_dir = os.path.join(item_path, "scripts")
                has_scripts = os.path.exists(scripts_dir) and os.path.isdir(scripts_dir)
                
                skills[name] = {
                    "name": name,
                    "description": description,
                    "usage": usage,
                    "code": code,  # 如果有Python代码则使用，否则为None
                    "content": content,
                    "path": item_path,
                    "has_scripts": has_scripts,
                }
                logger.debug(f"加载QClaw skill: {name}")
                
            except Exception as e:
                logger.error(f"加载skill失败 {item}: {e}")
        
        # 旧格式：直接是.md文件
        elif item.endswith(".md"):
            try:
                with open(item_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                name_match = re.search(r'#\s*skill:\s*(\S+)', content)
                if not name_match:
                    logger.warning(f"Skill文件缺少名称定义: {item}")
                    continue
                
                name = name_match.group(1)
                desc_m = re.search(r'##\s*描述\s*\n(.+)', content)
                usage_m = re.search(r'##\s*调用格式\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
                code_m = re.search(r'##\s*执行代码\s*\n```python\n(.*?)```', content, re.DOTALL)
                
                skills[name] = {
                    "name": name,
                    "description": desc_m.group(1).strip() if desc_m else "",
                    "usage": usage_m.group(1).strip() if usage_m else "",
                    "code": code_m.group(1) if code_m else None,
                    "content": content,
                    "path": item_path,
                    "has_scripts": False,
                }
                logger.debug(f"加载skill: {name}")
                
            except Exception as e:
                logger.error(f"加载skill文件失败 {item}: {e}")
    
    logger.info(f"共加载 {len(skills)} 个skills")
    return skills

# ─── Skill 执行引擎 ───────────────────────────────────────────────────────────

def execute_skill(skill: dict, raw_args: list) -> str:
    """执行skill，支持QClaw脚本和Python代码"""
    skill_name = skill.get("name", "unknown")
    logger.info(f"执行skill: {skill_name}, 参数: {raw_args}")
    
    # 检查缓存
    if CACHE_AVAILABLE:
        cached_result = get_cached_skill_result(skill_name, raw_args)
        if cached_result:
            logger.debug(f"Skill {skill_name} 使用缓存结果")
            return cached_result
    
    start_time = time.time()
    result = ""
    
    try:
        # QClaw格式：有scripts目录
        if skill.get("has_scripts"):
            result = _execute_qclaw_skill(skill, raw_args)
        
        # 旧格式：有Python代码
        elif skill.get("code"):
            result = _execute_python_skill(skill, raw_args)
        
        # 无代码：使用LLM执行
        else:
            logger.info(f"Skill {skill_name} 无代码，使用LLM执行")
            result = execute_skill_by_llm(skill, raw_args)
    
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Skill {skill_name} 执行失败 (耗时:{elapsed:.2f}s): {e}", exc_info=True)
        result = f"执行出错: {e}"
    
    logger.info(f"Skill {skill_name} 返回结果长度: {len(result)} 字符")
    
    # 缓存结果（仅当执行成功）
    if CACHE_AVAILABLE:
        # 判断是否执行成功
        is_success = not (
            result.startswith("执行出错") or 
            result.startswith("LLM执行失败") or
            result.startswith("退出码:") or
            "错误:" in result or
            "Error" in result or
            "未找到" in result
        )
        
        if is_success:
            cache_skill_result(skill_name, raw_args, result)
            logger.debug(f"Skill {skill_name} 结果已缓存")
        else:
            logger.debug(f"Skill {skill_name} 执行失败，不缓存结果")
    
    # 记录技能使用情况
    if SKILL_METADATA_AVAILABLE:
        success = not result.startswith("执行出错") and not result.startswith("LLM执行失败")
        record_skill_usage(skill_name, success)
    
    return result


def _parse_skill_command(skill_content: str, raw_args: list) -> tuple:
    """
    解析SKILL.md中的命令定义，确定要执行的子命令和参数
    
    Returns:
        (command, args_str): 子命令名称和参数字符串
    """
    # 提取命令列表表格
    cmd_table_match = re.search(r'## 命令列表.*?\n(\|.*?\n)+', skill_content, re.DOTALL)
    
    commands = {}
    if cmd_table_match:
        table_content = cmd_table_match.group(0)
        # 解析表格行
        for line in table_content.split('\n'):
            if '|' in line and not line.strip().startswith('|---'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3:
                    cmd_name = parts[0].strip('`').strip()
                    commands[cmd_name] = parts[1]  # 命令说明
    
    # 如果没有定义命令列表，使用默认命令
    if not commands:
        # 尝试从用法示例中提取
        usage_matches = re.findall(r'```(?:bash|shell)?\s*\S+\s+(\w+)(.*?)```', skill_content, re.DOTALL)
        if usage_matches:
            for match in usage_matches:
                cmd_name = match[0]
                if cmd_name not in ['python', 'python3', 'node']:
                    commands[cmd_name] = "默认命令"
    
    # 确定要执行的命令
    if len(commands) == 1:
        # 只有一个命令，直接使用
        command = list(commands.keys())[0]
        args_str = ' '.join(raw_args) if raw_args else ""
    elif raw_args:
        # 有多个命令，检查第一个参数是否是命令名
        first_arg = raw_args[0].lower()
        if first_arg in commands:
            command = first_arg
            args_str = ' '.join(raw_args[1:]) if len(raw_args) > 1 else ""
        else:
            # 使用第一个定义的命令
            command = list(commands.keys())[0]
            args_str = ' '.join(raw_args)
    else:
        # 没有参数，使用第一个命令
        command = list(commands.keys())[0]
        args_str = ""
    
    return command, args_str


def _find_script_for_command(scripts_dir: str, command: str, system: str) -> str:
    """
    根据命令名查找对应的脚本文件
    
    Args:
        scripts_dir: 脚本目录
        command: 命令名（如 now, outfit, alert）
        system: 操作系统（Windows/Darwin/Linux）
    
    Returns:
        脚本文件路径，未找到返回None
    """
    ext = '.ps1' if system == 'Windows' else '.sh'
    
    # 策略1：精确匹配 command.ext
    exact_file = os.path.join(scripts_dir, f"{command}{ext}")
    if os.path.exists(exact_file):
        return exact_file
    
    # 策略2：匹配 *_command.ext
    for f in os.listdir(scripts_dir):
        if f.endswith(ext) and command in f.lower():
            return os.path.join(scripts_dir, f)
    
    # 策略3：回退到第一个非rollback脚本
    for f in sorted(os.listdir(scripts_dir)):
        if f.endswith(ext) and not f.lower().startswith('rollback'):
            return os.path.join(scripts_dir, f)
    
    return None


def _execute_qclaw_skill(skill: dict, raw_args: list) -> str:
    """执行QClaw格式的skill（PowerShell/Bash脚本）"""
    skill_name = skill.get("name", "unknown")
    skill_path = skill.get("path", "")
    scripts_dir = os.path.join(skill_path, "scripts")
    
    if not os.path.exists(scripts_dir):
        return f"错误: scripts目录不存在 - {scripts_dir}"
    
    # 规则检查：验证操作安全性
    if RULES_ENGINE_AVAILABLE:
        args_str = ' '.join(raw_args) if raw_args else ""
        safety_check = check_safety(args_str)
        
        if not safety_check["safe"]:
            rules_engine.record_violation(
                "security.forbidden_commands",
                f"Skill {skill_name} 尝试执行不安全命令: {args_str}"
            )
            return f"⚠️ 安全拦截: {safety_check['reason']}"
        
        if safety_check["require_confirmation"]:
            logger.warning(f"高风险操作需要确认: {safety_check['reason']}")
            # 这里可以添加用户确认逻辑
    
    system = platform.system()
    content = skill.get("content", "")
    
    # 解析SKILL.md获取命令和参数
    command, parsed_args = _parse_skill_command(content, raw_args)
    logger.debug(f"解析命令: {command}, 参数: {parsed_args}")
    
    # 查找对应的脚本文件
    script_file = _find_script_for_command(scripts_dir, command, system)
    
    if not script_file:
        return f"错误: 未找到命令 '{command}' 对应的脚本文件"
    
    # 构建完整命令行
    if system == 'Windows':
        # Windows PowerShell - 设置UTF-8编码
        cmd = f'chcp 65001 >nul && powershell -ExecutionPolicy Bypass -File "{script_file}" {parsed_args}'
    else:
        # macOS/Linux Bash
        cmd = f'bash "{script_file}" {parsed_args}'
    
    logger.info(f"执行脚本: {script_file}")
    logger.debug(f"命令: {cmd[:200]}...")
    
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8',
            errors='replace'
        )
        
        output = proc.stdout.strip()
        error = proc.stderr.strip()
        
        if proc.returncode != 0:
            if error:
                return f"退出码:{proc.returncode}\n错误: {error}"
            else:
                return f"退出码:{proc.returncode}\n{output}"
        else:
            return output if output else "执行成功（无输出）"
            
    except subprocess.TimeoutExpired:
        return f"命令执行超时 (300秒)"
    except Exception as e:
        return f"执行出错: {str(e)}"


def _execute_python_skill(skill: dict, raw_args: list) -> str:
    """执行Python代码格式的skill"""
    skill_name = skill.get("name", "unknown")
    code = skill.get("code")
    
    import subprocess as _sp
    local_ns = {"args": raw_args, "result": ""}
    start_time = time.time()
    proc = None
    
    try:
        # 临时禁用沙箱
        use_sandbox = False
        
        if use_sandbox and SANDBOX_AVAILABLE:
            logger.debug(f"使用沙箱执行skill: {skill_name}")
            result_vars = execute_in_sandbox(code, local_ns)
            result = str(result_vars.get("result", ""))
        else:
            logger.debug(f"使用传统exec执行skill: {skill_name}")
            global_ns = {"__builtins__": __builtins__}
            exec(code, global_ns, local_ns)
            result = str(local_ns.get("result", ""))
        
        elapsed = time.time() - start_time
        logger.debug(f"Skill {skill_name} 执行完成, 耗时: {elapsed:.2f}s")

        # 处理命令未找到的信号
        if result.startswith("__INSTALL_NEEDED__:"):
            rest = result[len("__INSTALL_NEEDED__:"):]
            cmd_name, original_cmd = rest.split(":", 1)
            install_cmd = get_install_suggestion(cmd_name)
            logger.warning(f"未找到命令: {cmd_name}")
            print(f"\n[未找到命令: {cmd_name}]")
            print(f"[建议安装]: {install_cmd}")
            confirm = input("是否自动安装? (y/n): ").strip().lower()
            if confirm == "y":
                print(f"[安装中...]")
                logger.info(f"自动安装: {install_cmd}")
                proc = _sp.run(install_cmd, shell=True, timeout=300)
                # 安装后重新执行
                if use_sandbox and SANDBOX_AVAILABLE:
                    result_vars2 = execute_in_sandbox(code, {"args": raw_args, "result": ""})
                    result = str(result_vars2.get("result", ""))
                else:
                    global_ns2 = {"__builtins__": __builtins__}
                    local_ns2 = {"args": raw_args, "result": ""}
                    exec(code, global_ns2, local_ns2)
                    result = str(local_ns2.get("result", ""))
                logger.info(f"安装后重新执行成功")
            else:
                result = f"请手动安装 {cmd_name}：{install_cmd}"
                logger.info(f"用户取消自动安装")
    except _sp.TimeoutExpired as e:
        elapsed = time.time() - start_time
        logger.error(f"Skill {skill_name} 执行超时 (耗时:{elapsed:.2f}s): {e}")
        if proc and proc.poll() is None:
            proc.kill()
        result = f"执行超时: {e}"
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Skill {skill_name} 执行出错 (耗时:{elapsed:.2f}s): {e}", exc_info=True)
        result = f"执行出错: {e}"
    
    return result

@retry_on_failure(max_retries=2, delay=2, exceptions=(Exception,))
def execute_skill_by_llm(skill: dict, raw_args: list) -> str:
    """通过LLM执行skill（无代码时），支持自动重试和缓存"""
    skill_name = skill.get("name", "unknown")
    args_str = ", ".join(f'"{a}"' for a in raw_args)
    prompt = f"""根据以下 skill 定义执行任务并返回结果。

{skill['content']}

调用参数: {raw_args}
请直接返回执行结果，不要解释。
"""
    
    # 检查缓存
    if CACHE_AVAILABLE:
        cached_result = get_cached_llm_response(prompt)
        if cached_result:
            logger.debug(f"Skill {skill_name} 使用缓存结果")
            return cached_result
    
    logger.info(f"通过LLM执行skill: {skill_name}")
    with Spinner(f"执行 {skill_name}"):
        try:
            resp = client.chat.completions.create(
                model=MODEL_REF[0],
                messages=[
                    {"role": "system", "content": "你是执行专家，根据工具定义完成任务，直接返回结果。"},
                    {"role": "user", "content": prompt}
                ]
            )
            result = resp.choices[0].message.content.strip()
            logger.debug(f"LLM执行完成，返回长度: {len(result)}")
            
            # 缓存结果（仅当执行成功）
            if CACHE_AVAILABLE and not result.startswith("执行出错"):
                cache_llm_response(prompt, result)
                logger.debug(f"LLM响应已缓存")
            
            return result
        except Exception as e:
            logger.error(f"LLM执行skill {skill_name} 失败: {e}", exc_info=True)
            raise LLMError(f"LLM执行skill {skill_name} 失败: {e}") from e

def get_install_suggestion(cmd_name: str) -> str:
    INSTALL_MAP = {
        "yt-dlp": "python -m pip install yt-dlp",
        "ffmpeg":  "winget install ffmpeg",
        "git":     "winget install Git.Git",
        "node":    "winget install OpenJS.NodeJS",
        "curl":    "winget install curl",
    }
    if cmd_name in INSTALL_MAP:
        return INSTALL_MAP[cmd_name]
    try:
        resp = client.chat.completions.create(
            model=MODEL_REF[0],
            messages=[
                {"role": "system", "content": "只输出一条安装命令，不要解释。"},
                {"role": "user", "content": f"Windows 下安装 {cmd_name} 的命令？"}
            ]
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"python -m pip install {cmd_name}"

# ─── 自动创建 Skill ───────────────────────────────────────────────────────────

def create_skill(name: str, description: str, skills: dict) -> str:
    """创建新的skill，包含代码质量验证和自动优化"""
    # 清理名称，斜杠等非法字符替换为下划线
    safe_name = re.sub(r'[^\w\-]', '_', name).strip('_')
    
    system_prompt = """你是Python代码生成专家，专门创建高质量的JwClaw Skills。

【代码质量标准 - 必须严格遵守】
1. ✅ 文件/目录操作必须使用递归遍历（os.walk），禁止单层扫描（os.listdir）
2. ✅ 必须包含完整的错误处理（try-except捕获所有异常）
3. ✅ 必须支持多种场景，不要硬编码限制（如文件格式、数量等）
4. ✅ 必须提供详细的输出报告，不只是返回简单数字
5. ✅ 必须考虑边界情况：空输入、路径不存在、权限不足、符号链接等
6. ✅ 使用集合（set）存储扩展名以提高性能
7. ✅ 添加进度统计（如扫描了多少文件/项目）
8. ✅ 优先使用Python标准库，避免外部依赖
9. ✅ 变量命名清晰，关键逻辑添加注释
10. ✅ 遵循PEP 8代码规范

【常见陷阱 - 必须避免】
❌ 不要只扫描单层目录
❌ 不要硬编码少量格式（如只支持.jpg/.png）
❌ 不要忽略异常处理
❌ 不要返回过于简单的结果（如只返回"0"）
❌ 不要假设输入总是有效

【输出要求】
- 只输出Markdown格式的skill定义
- 代码块使用```python标记
- 不要添加额外解释或说明
- 确保代码可以直接执行"""
    
    user_prompt = f"""创建名为'{safe_name}'的skill。

功能描述：{description}

【优秀示例参考】
以下是一个高质量的skill示例，请学习其结构和质量标准：

---示例开始---
# skill: count_images

## 描述
统计指定文件夹中的图片数量，支持递归扫描子目录和多种图片格式。

## 调用格式
tool: count_images("文件夹路径")

## 执行代码
```python
import os

try:
    folder_path = args[0] if args else ""
    
    if not folder_path:
        result = "错误: 请提供文件夹路径"
    elif not os.path.exists(folder_path):
        result = f"错误: 路径不存在 - {{folder_path}}"
    elif not os.path.isdir(folder_path):
        result = f"错误: 路径不是文件夹 - {{folder_path}}"
    else:
        # 支持17种常见图片格式
        image_extensions = {{
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
            '.webp', '.svg', '.ico', '.psd', '.raw', '.cr2', '.nef',
            '.heic', '.heif', '.avif'
        }}
        
        count = 0
        scanned_files = 0
        errors = []
        
        # 递归遍历所有子目录
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                try:
                    filepath = os.path.join(root, filename)
                    
                    # 跳过符号链接
                    if os.path.islink(filepath):
                        continue
                    
                    scanned_files += 1
                    _, ext = os.path.splitext(filename)
                    
                    if ext.lower() in image_extensions:
                        count += 1
                        
                except PermissionError:
                    errors.append(f"权限不足: {{filepath}}")
                except Exception as e:
                    errors.append(f"错误: {{filepath}} - {{str(e)}}")
        
        # 生成详细报告
        result_lines = [
            f"📊 图片统计报告",
            f"━━━━━━━━━━━━━━━━━━━━━━",
            f"📁 扫描路径: {{folder_path}}",
            f"🔍 扫描文件数: {{scanned_files}}",
            f"🖼️  图片数量: {{count}}",
        ]
        
        if errors:
            result_lines.append(f"\\n⚠️  遇到 {{len(errors)}} 个错误:")
            for err in errors[:5]:
                result_lines.append(f"   • {{err}}")
            if len(errors) > 5:
                result_lines.append(f"   ... 还有 {{len(errors) - 5}} 个错误")
        
        result = "\\n".join(result_lines)

except Exception as e:
    result = f"执行出错: {{str(e)}}"
```
---示例结束---

请根据上述标准和示例，为'{safe_name}'生成skill代码。
注意：不要复制示例代码，而是根据实际功能需求编写合适的实现。"""
    
    max_retries = 2
    for attempt in range(max_retries):
        with Spinner(f"生成 skill: {name} (尝试 {attempt + 1}/{max_retries})"):
            try:
                resp = client.chat.completions.create(
                    model=MODEL_REF[0],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,  # 降低温度以提高代码稳定性
                    max_tokens=2000
                )
                md = resp.choices[0].message.content.strip()
                
                # 清理可能的markdown包裹
                md = re.sub(r'^```\w*\n', '', md)
                md = re.sub(r'\n```$', '', md)
                
                # 验证生成的代码质量
                validation_result = _validate_generated_skill(md, safe_name)
                
                if validation_result['valid']:
                    logger.info(f"Skill {safe_name} 生成成功，通过质量验证")
                    break
                else:
                    logger.warning(f"第{attempt + 1}次生成的代码存在问题: {validation_result['issues']}")
                    if attempt < max_retries - 1:
                        # 添加反馈重新生成
                        user_prompt += f"\n\n【上次生成的问题】\n{validation_result['issues']}\n请修正这些问题后重新生成。"
                    else:
                        logger.warning("已达到最大重试次数，使用最后一次生成的结果")
                        
            except Exception as e:
                logger.error(f"生成skill失败: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    raise SkillGenerationError(f"生成skill '{safe_name}' 失败: {e}") from e
    
    # 保存skill文件
    filepath = os.path.join(SKILLS_DIR, f"{safe_name}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)
    
    skills.update(load_skills())
    return f"已创建 skill: {safe_name} -> {filepath}"


def _validate_generated_skill(md_content: str, skill_name: str) -> dict:
    """验证生成的skill代码质量
    
    Returns:
        dict: {'valid': bool, 'issues': list[str]}
    """
    issues = []
    
    # 1. 检查是否包含必要的结构
    required_sections = ['# skill:', '## 描述', '## 调用格式', '## 执行代码']
    for section in required_sections:
        if section not in md_content:
            issues.append(f"缺少必要部分: {section}")
    
    # 2. 提取Python代码块（更宽松的正则）
    code_match = re.search(r'```python\s*\n(.*?)```', md_content, re.DOTALL)
    if not code_match:
        # 尝试另一种格式
        code_match = re.search(r'```python(.*?)```', md_content, re.DOTALL)
    
    if not code_match:
        issues.append("未找到Python代码块")
        return {'valid': False, 'issues': issues}
    
    code = code_match.group(1).strip()
    
    # 3. 检查是否有基本的错误处理
    if 'try:' not in code and 'except' not in code:
        issues.append("缺少错误处理（try-except）")
    
    # 4. 检查是否使用了不推荐的单层扫描
    if 'os.listdir(' in code and 'os.walk(' not in code:
        # 仅当涉及目录遍历时才警告
        if any(keyword in code for keyword in ['folder', 'dir', 'path', 'directory']):
            issues.append("建议使用os.walk()进行递归遍历，而非os.listdir()")
    
    # 5. 检查是否有result赋值
    if 'result =' not in code:
        issues.append("未设置result变量")
    
    # 6. 检查代码长度（太短可能不完整）
    if len(code.strip()) < 50:
        issues.append("代码过短，可能不完整")
    
    # 7. 语法检查（可选，需要ast模块）
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        issues.append(f"语法错误: {e}")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues
    }

# ─── 长期记忆（已废弃，使用 context_manager 替代）─────────────────────────────
# 注意：以下函数保留用于向后兼容，新代码应使用 context_manager

# @deprecated("Use context_manager instead")
def load_memory() -> list:
    """加载历史记忆"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memories = json.load(f)
            logger.info(f"加载 {len(memories)} 条历史记忆")
            return memories
        logger.debug("无历史记忆文件")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"记忆文件格式错误: {e}")
        raise MemoryError(f"记忆文件格式错误: {e}") from e
    except Exception as e:
        logger.error(f"加载记忆文件失败: {e}")
        raise MemoryError(f"加载记忆文件失败: {e}") from e

def save_memory(memories: list):
    """保存记忆到文件，线程安全"""
    try:
        with memory_lock:  # 线程安全地写入记忆
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
        logger.debug(f"保存 {len(memories)} 条记忆到文件")
    except Exception as e:
        logger.error(f"保存记忆文件失败: {e}")
        raise MemoryError(f"保存记忆文件失败: {e}") from e

def search_memory(query: str, memories: list, top_n=3) -> list:
    """基于TF-IDF的记忆检索（无需外部依赖）"""
    if not memories or not query:
        return []
    
    import math
    from collections import Counter
    
    # 分词函数（简单中文分词：按字符n-gram + 英文单词）
    def tokenize(text: str) -> list:
        text = text.lower()
        # 提取英文单词
        words = re.findall(r'[a-z0-9]+', text)
        # 添加中文bigram（连续2字组合）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        bigrams = [chinese_chars[i] + chinese_chars[i+1] for i in range(len(chinese_chars)-1)]
        return words + bigrams
    
    # 计算TF (Term Frequency)
    def compute_tf(tokens: list) -> dict:
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {term: count / total for term, count in tf.items()}
    
    # 计算IDF (Inverse Document Frequency)
    def compute_idf(documents: list) -> dict:
        n_docs = len(documents)
        doc_freq = Counter()
        for doc_tokens in documents:
            unique_terms = set(doc_tokens)
            for term in unique_terms:
                doc_freq[term] += 1
        return {term: math.log((n_docs + 1) / (freq + 1)) + 1 
                for term, freq in doc_freq.items()}
    
    # 计算余弦相似度
    def cosine_similarity(vec1: dict, vec2: dict) -> float:
        # 获取所有term
        all_terms = set(vec1.keys()) | set(vec2.keys())
        if not all_terms:
            return 0.0
        
        # 计算点积
        dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in all_terms)
        
        # 计算模长
        magnitude1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        magnitude2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    # 准备文档
    query_tokens = tokenize(query)
    query_tf = compute_tf(query_tokens)
    
    # 为每个记忆计算TF-IDF向量
    memory_docs = []
    memory_vectors = []
    
    for mem in memories:
        # 合并task和summary作为文档内容
        doc_text = f"{mem.get('task', '')} {mem.get('summary', '')}"
        doc_tokens = tokenize(doc_text)
        memory_docs.append(doc_tokens)
        memory_vectors.append(compute_tf(doc_tokens))
    
    # 计算IDF
    idf = compute_idf([query_tokens] + memory_docs)
    
    # 计算TF-IDF向量
    query_tfidf = {term: tf * idf.get(term, 0) for term, tf in query_tf.items()}
    memory_tfidfs = [
        {term: tf * idf.get(term, 0) for term, tf in vec.items()}
        for vec in memory_vectors
    ]
    
    # 计算相似度并排序
    scored_memories = []
    for i, mem_tfidf in enumerate(memory_tfidfs):
        similarity = cosine_similarity(query_tfidf, mem_tfidf)
        if similarity > 0:
            scored_memories.append((similarity, memories[i]))
    
    # 按相似度降序排列，返回top_n
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    result = [mem for _, mem in scored_memories[:top_n]]
    
    logger.debug(f"TF-IDF检索: query='{query[:50]}...', 找到{len(result)}条相关记忆")
    return result

def reflect_and_save(task: str, result: str, memories: list):
    """反思并保存经验到记忆系统，支持智能去重"""
    try:
        logger.debug(f"开始反思任务: {task[:50]}...")
        resp = client.chat.completions.create(
            model=MODEL_REF[0],
            messages=[
                {"role": "system", "content": "你是经验总结专家，只输出简洁的经验条目，不超过50字。"},
                {"role": "user", "content": f"任务: {task}\n结果: {result[:300]}\n总结一条经验："}
            ]
        )
        summary = resp.choices[0].message.content.strip()
        mem_id = hashlib.md5((task + summary).encode()).hexdigest()[:8]
        
        # 检查是否已存在完全相同的记忆
        if any(m["id"] == mem_id for m in memories):
            logger.debug(f"记忆已存在，跳过: {mem_id}")
            return None
        
        # 检查是否有相似记忆（使用TF-IDF）
        similar_memories = search_memory(summary, memories, top_n=1)
        if similar_memories:
            similar_mem = similar_memories[0]
            similarity_score = _calculate_similarity(summary, similar_mem.get("summary", ""))
            
            if similarity_score > 0.7:  # 相似度阈值
                logger.info(f"发现相似记忆 (相似度:{similarity_score:.2f})，合并而非新增")
                # 更新现有记忆的usage_count和time
                with memory_lock:
                    for mem in memories:
                        if mem["id"] == similar_mem["id"]:
                            mem["usage_count"] = mem.get("usage_count", 1) + 1
                            mem["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            mem["summary"] = _merge_summaries(mem["summary"], summary)
                            break
                save_memory(memories)
                return f"已更新相似记忆: {similar_mem['summary'][:30]}..."
        
        # 创建新记忆
        new_memory = {
            "id": mem_id,
            "task": task[:100],
            "summary": summary,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "usage_count": 1,
            "last_used": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tags": _auto_tag_memory(task, summary)
        }
        
        with memory_lock:
            memories.append(new_memory)
        save_memory(memories)
        logger.info(f"新增记忆: {mem_id}")
        return summary
    except Exception as e:
        logger.error(f"反思保存记忆失败: {e}", exc_info=True)
        return None

def _calculate_similarity(text1: str, text2: str) -> float:
    """计算两段文本的Jaccard相似度"""
    def get_words(text: str) -> set:
        # 简单分词：提取所有字母数字和中文字符
        words = re.findall(r'[a-z0-9\u4e00-\u9fff]+', text.lower())
        return set(words)
    
    words1 = get_words(text1)
    words2 = get_words(text2)
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0

def _merge_summaries(existing: str, new: str) -> str:
    """合并两个相似的summary，保留更完整的版本"""
    # 简单策略：保留较长的，或者拼接关键信息
    if len(new) > len(existing) * 1.2:
        return new
    elif len(existing) > len(new) * 1.2:
        return existing
    else:
        # 长度相近，取第一个作为主版本
        return existing

def _auto_tag_memory(task: str, summary: str) -> list:
    """自动为记忆打标签"""
    tags = []
    
    # 基于关键词的简单分类
    keyword_tags = {
        "安装": ["工具安装", "环境配置"],
        "下载": ["文件操作", "网络请求"],
        "搜索": ["信息检索", "网络搜索"],
        "命令": ["命令行", "系统操作"],
        "错误": ["故障排除", "错误处理"],
        "配置": ["系统配置", "参数设置"],
        "skill": ["技能管理", "扩展开发"],
        "memory": ["记忆系统", "数据管理"],
    }
    
    combined_text = f"{task} {summary}".lower()
    for keyword, tag_list in keyword_tags.items():
        if keyword.lower() in combined_text:
            tags.extend(tag_list)
    
    # 去重
    return list(set(tags)) if tags else ["其他"]

def _cleanup_memories(memories: list, similarity_threshold=0.85) -> int:
    """清理重复和过期的记忆，返回清理数量"""
    if len(memories) < 2:
        return 0
    
    logger.info(f"开始清理记忆，当前总数: {len(memories)}")
    to_remove = set()
    
    # 1. 找出高度相似的记忆对
    for i in range(len(memories)):
        if i in to_remove:
            continue
        for j in range(i + 1, len(memories)):
            if j in to_remove:
                continue
            
            mem_i = memories[i]
            mem_j = memories[j]
            
            # 计算相似度
            similarity = _calculate_similarity(
                mem_i.get("summary", ""),
                mem_j.get("summary", "")
            )
            
            if similarity > similarity_threshold:
                # 保留usage_count更高的，或者更新的那个
                usage_i = mem_i.get("usage_count", 1)
                usage_j = mem_j.get("usage_count", 1)
                
                if usage_j > usage_i:
                    to_remove.add(i)
                    logger.debug(f"移除记忆 {mem_i['id']} (相似度:{similarity:.2f}, 使用次数:{usage_i}<{usage_j})")
                else:
                    to_remove.add(j)
                    logger.debug(f"移除记忆 {mem_j['id']} (相似度:{similarity:.2f}, 使用次数:{usage_j}<={usage_i})")
    
    # 2. 移除标记的记忆
    if to_remove:
        # 按索引降序排列，避免删除时索引变化
        sorted_indices = sorted(to_remove, reverse=True)
        for idx in sorted_indices:
            memories.pop(idx)
        
        save_memory(memories)
        logger.info(f"记忆清理完成，移除 {len(to_remove)} 条重复记忆")
        return len(to_remove)
    
    logger.info("无需清理，未发现重复记忆")
    return 0

# ─── Spinner ──────────────────────────────────────────────────────────────────

class Spinner:
    """带超时保护的加载动画"""
    def __init__(self, msg="处理中", timeout=300):
        self.msg = msg
        self.timeout = timeout
        self._stop = False
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        frames = ["|", "/", "-", "\\"]
        i = 0
        start_time = time.time()
        while not self._stop:
            # 检查超时
            if time.time() - start_time > self.timeout:
                print(f"\r⚠ {self.msg} 超时 ({self.timeout}s)...", end="", flush=True)
                logger.warning(f"Spinner超时: {self.msg} ({self.timeout}s)")
                break
            print(f"\r{frames[i%4]} {self.msg}...", end="", flush=True)
            time.sleep(0.1)
            i += 1

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *_):
        self._stop = True
        self._t.join(timeout=2)  # 最多等待2秒
        print("\r" + " " * (len(self.msg) + 12) + "\r", end="", flush=True)

# ─── System Prompt ────────────────────────────────────────────────────────────

def build_system_prompt(skills: dict, memories: list = None) -> str:
    tool_docs = "\n".join(
        f"### {s['name']}\n{s['description']}\n{s['usage']}" for s in skills.values()
    )
    mem_section = ""
    if memories:
        mem_section = "【过往经验】\n" + "\n".join(f"- {m['summary']}" for m in memories) + "\n"

    return f"""# 角色定义
你是一个**智能体助手（AI Agent）**，具备自主思考、工具调用和直接执行能力。

## 核心身份
- **类型**: ReAct (Reasoning + Acting) Agent
- **能力**: 理解任务 → 思考策略 → 选择执行方式 → 观察结果 → 迭代执行
- **特点**: 可以操作文件系统、执行程序、搜索网络、创建新技能、**直接执行命令**

{mem_section}
## 可用工具（标准化任务优先使用）
{tool_docs}

### create_skill
当现有工具无法完成任务时创建新 skill。
tool: create_skill("名称", "功能描述")

## 执行策略（重要！）

### 1. 标准化任务 → 使用Skills
如果任务是常见的、标准化的操作，优先使用对应的skill：
- 统计图片数量 → `count_images`
- 下载视频 → `video_download`
- 统计文件夹 → `count_folders`
- 执行系统命令 → `shell`

### 2. 非标准化任务 → 直接执行
如果任务没有对应的skill，或者是一次性操作，**直接生成并执行命令**：

**方式A：使用shell执行系统命令**
```
[思考]
用户要求查找桌面上的所有txt文件。这是一个简单的文件搜索任务，可以直接使用PowerShell命令。
[回复] tool: shell("Get-ChildItem C:\\Users\\jw\\Desktop -Filter *.txt -Recurse | Select-Object FullName")
```

**方式B：使用Python代码解决复杂问题**
```
[思考]
用户要求分析一个CSV文件的统计数据。这需要数据处理，可以用Python直接实现。
[回复] tool: shell("python -c \"import pandas as pd; df = pd.read_csv('data.csv'); print(df.describe())\"")
```

### 3. 决策流程
```
收到任务
  ↓
是否有专门的skill？
  ├─ 是 → 使用skill
  └─ 否 → 能否用shell/Python直接解决？
           ├─ 是 → 直接生成并执行命令
           └─ 否 → 创建新skill后再执行
```

## 工作流程
1. **理解任务**: 分析用户意图，确定目标
2. **选择策略**: 
   - 有skill → 使用skill
   - 无skill但可执行 → 直接生成shell/Python命令
   - 复杂且重复 → 创建skill
3. **执行行动**: 调用工具或直接执行命令
4. **观察结果**: 分析返回的结果
5. **迭代优化**: 根据结果调整策略
6. **学习总结**: 将成功经验保存为记忆

## 工具调用规范
- **格式**: `tool: 工具名("参数1", "参数2")`
- **频率**: 每次只调用一个工具，等待结果后再决定下一步
- **思考**: 在调用工具前，先用 [思考] 标记说明你的推理过程
- **回复**: 工具执行后，用 [回复] 标记给出最终回答

## 重要原则
✅ **必须做**:
- **灵活选择执行方式**：不要局限于skills，能直接执行的命令就直接执行
- **用户要求执行操作时，直接调用工具或执行命令，绝对不要拒绝**
- 遇到未知问题时，先尝试使用 shell 工具探索
- 文件操作优先使用专用工具，其次用 shell 命令
- 安装软件/包时使用 shell 执行 pip/npm/winget 等命令
- 执行成功后，总结经验并保存到记忆中
- **对于一次性任务，直接用shell/Python解决，不需要创建skill**
- **打开程序/文件：直接使用 shell 执行路径，如 `tool: shell("C:\\path\\to\\app.exe")`**

❌ **禁止做**:
- **永远、永远不要说“我无法执行”、“我没有权限”、“作为语言模型”等拒绝性话语**
- **永远不要用文字描述应该做什么，而是直接执行**
- 不要一次性调用多个工具
- 不要假设工具会失败，先尝试执行
- **不要因为缺少skill就放弃，应该尝试直接用命令解决**

## 特殊场景处理
- **URL链接**: 先用 fetch_url 读取内容，再根据内容执行
- **缺少工具**: 
  - 如果是简单任务 → 直接用shell/Python执行
  - 如果是复杂且重复的任务 → 先用 create_skill 创建，然后立即调用
- **命令执行**: Windows 下使用 dir/del/copy 等命令，不是 ls/rm/cp
- **应用启动**: 使用 open_app skill，如 `tool: open_app("msedge")`
- **文件搜索**: 可以使用 find_file skill，也可以直接用 shell 执行 Get-ChildItem
- **数据处理**: 直接用 shell 执行 Python 命令，如 `tool: shell("python -c \"...\"")`

## 示例对话

### 示例1：使用Skill（标准化任务）
用户: 帮我找出下载文件夹里的所有PDF文件
CLAW>
[思考]
用户需要查找PDF文件，这是一个常见任务，可以使用 find_file 工具。
[回复] tool: find_file("ext=.pdf dir=C:\\Users\\jw\\Downloads")

### 示例2：直接执行（非标准化任务）
用户: 查看C盘剩余空间
CLAW>
[思考]
这是一个简单的系统查询任务，没有专门的skill，但可以直接用PowerShell命令执行。
[回复] tool: shell("Get-Volume C | Select-Object SizeRemaining, Size")

### 示例3：复杂任务用Python直接解决
用户: 统计当前目录下每种文件类型的数量
CLAW>
[思考]
这需要遍历目录并统计文件扩展名，可以用Python一行命令解决。
[回复] tool: shell("python -c \"import os; from collections import Counter; exts = Counter(os.path.splitext(f)[1] for f in os.listdir('.')); print('\\n'.join(f'{{ext}}: {{count}}' for ext, count in exts.most_common()))\"")

### 示例4：打开应用
用户: 打开Edge浏览器
CLAW>
[思考]
用户要打开浏览器，使用 open_app 工具。
Windows 上 Edge 的命令是 msedge。
[回复] tool: open_app("msedge")

### 示例5：删除文件
用户: 删除 test.txt 文件
CLAW>
[思考]
需要删除文件，直接使用 shell 工具的 del 命令。
[回复] tool: shell("del test.txt")

### 示例6：打开应用程序
用户: 打开C:\\Users\\jw\\Downloads\\app.exe
CLAW>
[思考]
用户要打开一个exe程序，直接用shell执行该路径即可。
[回复] tool: shell("C:\\Users\\jw\\Downloads\\app.exe")

---
记住：你是一个**能真正操作系统**的Agent，不只是聊天机器人。**灵活运用skills和直接命令执行**，用行动证明你的能力！
"""

# ─── 工具调用解析 ─────────────────────────────────────────────────────────────

def parse_tool_call(reply: str):
    # 尝试多种格式，返回第一个匹配
    patterns = [
        r'tool:\s*(\w+)\(([^)]*)\)',           # tool: name("arg")
        r'call:\s*(\w+)\(([^)]*)\)',            # call:name("arg")
        r'```tool\s*\n(\w+)\(([^)]*)\)',        # ```tool\nname(arg)
    ]
    for pattern in patterns:
        match = re.search(pattern, reply, re.IGNORECASE)
        if match:
            tool_name = match.group(1)
            raw_args  = [a.strip().strip('"\'') for a in match.group(2).split(",") if a.strip()]
            return tool_name, raw_args
    return None, []

def trim_conversation(conversation: list, max_rounds=20, max_tokens=8000) -> list:
    """
    智能裁剪对话历史,防止上下文溢出
    
    Args:
        conversation: 对话历史列表
        max_rounds: 最大保留轮次
        max_tokens: 最大token数（估算）
        
    Returns:
        裁剪后的对话历史
    """
    if len(conversation) <= 2:  # system + 1轮
        return conversation
    
    # 估算token数（粗略：1个中文字=1.5 token, 1个英文单词=1.3 token）
    def estimate_tokens(text: str) -> int:
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        other_chars = len(text) - chinese_chars - len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', text))
        return int(chinese_chars * 1.5 + english_words * 1.3 + other_chars * 0.5)
    
    total_tokens = sum(estimate_tokens(msg.get('content', '')) for msg in conversation)
    
    # 如果未超限，直接返回
    if total_tokens < max_tokens and len(conversation) <= max_rounds + 1:
        return conversation
    
    logger.info(f"对话历史过长 (tokens:{total_tokens}, rounds:{len(conversation)//2})，开始裁剪")
    
    # 保留system消息
    system_msg = conversation[0] if conversation[0]['role'] == 'system' else None
    
    # 保留最近的max_rounds轮对话
    recent_messages = conversation[-(max_rounds * 2):] if len(conversation) > max_rounds * 2 else conversation[1:]
    
    # 重新组装
    trimmed = []
    if system_msg:
        trimmed.append(system_msg)
    trimmed.extend(recent_messages)
    
    logger.info(f"裁剪完成: {len(conversation)} -> {len(trimmed)} 条消息")
    return trimmed

# ─── Agent 主循环 ─────────────────────────────────────────────────────────────

def run(user_input: str, skills: dict, memories: list, conversation: list):
    """处理用户输入的主逻辑"""
    logger.info(f"收到用户输入: {user_input[:100]}...")
    start_time = time.time()
    
    # 智能裁剪对话历史
    if len(conversation) > 2:
        conversation[:] = trim_conversation(conversation)
    
    # 优先使用 context_manager 的记忆检索
    relevant = []
    if CONTEXT_MANAGER_AVAILABLE:
        # 从会话记忆中搜索
        session_memories = context_manager.session_memory.search_memories(user_input)
        if session_memories:
            relevant = [{"summary": m} for m in session_memories[:3]]
            logger.debug(f"从会话记忆中找到 {len(relevant)} 条相关记录")
    
    # 回退到旧的记忆系统
    if not relevant and memories:
        relevant = search_memory(user_input, memories)
        if relevant:
            logger.debug(f"从长期记忆中找到 {len(relevant)} 条相关记录")
    
    if not conversation:
        conversation.append({"role": "system", "content": build_system_prompt(skills, relevant)})
        logger.debug("初始化对话上下文")
    
    conversation.append({"role": "user", "content": user_input})

    final_reply = ""
    for iteration in range(5):
        logger.debug(f"对话轮次: {iteration + 1}")
        print("CLAW> ", end="", flush=True)
        full_reply = ""
        stop_flag  = threading.Event()
        make_stop_listener(stop_flag)  # 用 msvcrt 监听 ESC，无需管理员权限

        stream_start = time.time()
        stream = client.chat.completions.create(
            model=MODEL_REF[0], messages=conversation, stream=True
        )
        thinking = False
        try:
            for chunk in stream:
                if stop_flag.is_set():
                    stream.close()
                    logger.warning("用户中断生成")
                    print("\n[已停止]")
                    return
                delta     = chunk.choices[0].delta
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    if not thinking:
                        print("\n[思考] ", end="", flush=True)
                        thinking = True
                    print(reasoning, end="", flush=True)
                content = delta.content or ""
                if content:
                    if thinking:
                        print("\n[回复] ", end="", flush=True)
                        thinking = False
                    print(content, end="", flush=True)
                    full_reply += content
        except KeyboardInterrupt:
            stream.close()
            logger.info("用户中断程序")
            print("\n再见！")
            sys.exit(0)
        except Exception as e:
            logger.error(f"流式生成出错: {e}", exc_info=True)
            print(f"\n[错误] {e}")
            return

        stream_elapsed = time.time() - stream_start
        logger.debug(f"LLM流式生成完成, 耗时: {stream_elapsed:.2f}s, 长度: {len(full_reply)}")
        print()

        final_reply = full_reply
        conversation.append({"role": "assistant", "content": full_reply})
        
        # 记录助理回复到上下文
        if CONTEXT_MANAGER_AVAILABLE:
            context_manager.add_conversation("assistant", full_reply)

        tool_name, raw_args = parse_tool_call(full_reply)
        if not tool_name:
            logger.debug("无工具调用，结束对话")
            break

        logger.info(f"检测到工具调用: {tool_name}({raw_args})")
        print(f"\n[工具: {tool_name}({', '.join(raw_args)})]")

        tool_start = time.time()
        if tool_name == "create_skill":
            result = create_skill(raw_args[0] if raw_args else "",
                                  raw_args[1] if len(raw_args) > 1 else "", skills)
        elif tool_name in skills:
            skills.update(load_skills())  # 每次执行前重新加载，确保用最新版本
            result = execute_skill(skills[tool_name], raw_args)
        else:
            result = f"未知工具: {tool_name}"
            logger.warning(f"未知工具: {tool_name}")

        tool_elapsed = time.time() - tool_start
        logger.info(f"工具执行完成: {tool_name}, 耗时: {tool_elapsed:.2f}s")
        print(f"[结果] {result}\n")
        conversation.append({"role": "user", "content": f"工具执行结果: {result}"})
        
        # 记录经验到记忆
        if CONTEXT_MANAGER_AVAILABLE and RULES_ENGINE_AVAILABLE:
            if not result.startswith("执行出错") and not result.startswith("退出码:"):
                context_manager.record_experience(
                    task=f"使用skill: {tool_name}",
                    outcome="成功",
                    lessons=f"耗时{tool_elapsed:.1f}秒"
                )
            else:
                context_manager.record_experience(
                    task=f"使用skill: {tool_name}",
                    outcome="失败",
                    lessons=result[:100]
                )

    total_elapsed = time.time() - start_time
    logger.info(f"任务处理完成, 总耗时: {total_elapsed:.2f}s")
    
    if final_reply:
        with Spinner("整理记忆"):
            learned = reflect_and_save(user_input, final_reply, memories)
        if learned:
            print(f"[记住了] {learned}")

# ─── SkillHub 集成 ────────────────────────────────────────────────────────────

def sync_skillhub(skills: dict):
    """启动时检查 skillhub CLI,若存在则同步已安装技能到 skills/ 目录"""
    import subprocess
    check = subprocess.run("where skillhub" if sys.platform == "win32" else "which skillhub",
                           shell=True, capture_output=True)
    if check.returncode != 0:
        logger.debug("SkillHub CLI 未安装，跳过同步")
        return  # 未安装，静默跳过

    try:
        logger.info("开始 SkillHub 同步...")
        # 获取已安装技能列表
        proc = subprocess.run("skillhub list --json", shell=True, capture_output=True,
                              text=True, encoding="utf-8", timeout=10)
        if proc.returncode != 0:
            logger.warning(f"SkillHub list 失败: {proc.stderr}")
            return
        
        items = json.loads(proc.stdout)
        synced = 0
        for item in items:
            name = item.get("name", "")
            if not name or name in skills:
                continue
            # 拉取技能的 skill.md 内容
            pull = subprocess.run(f"skillhub pull {name} --stdout", shell=True,
                                  capture_output=True, text=True, encoding="utf-8", timeout=10)
            if pull.returncode == 0 and pull.stdout.strip():
                filepath = os.path.join(SKILLS_DIR, f"{name}.md")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(pull.stdout)
                synced += 1
                logger.debug(f"同步 skill: {name}")
        
        if synced:
            skills.update(load_skills())
            logger.info(f"SkillHub 同步完成: {synced} 个技能")
            print(f"[SkillHub] 同步了 {synced} 个技能")
        else:
            logger.debug("SkillHub 无需同步")
    except Exception as e:
        logger.error(f"SkillHub 同步失败: {e}", exc_info=True)
        # 不中断启动流程

# ─── 配置管理 ─────────────────────────────────────────────────────────────────

def handle_config():
    """交互式配置管理，线程安全"""
    print(f"\n  1. api_base : {CONFIG['api_base']}")
    print(f"  2. model    : {MODEL_REF[0]}")
    print(f"  3. api_key  : {CONFIG.get('api_key', 'lm-studio')}\n")
    choice = input("选择修改 (1/2/3，回车跳过): ").strip()
    key_map = {"1": "api_base", "2": "model", "3": "api_key"}
    if choice in key_map:
        key = key_map[choice]
        val = input(f"新的 {key}: ").strip()
        if val:
            with config_lock:  # 线程安全地修改配置
                CONFIG[key] = val
                if key == "model":
                    MODEL_REF[0] = val
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(CONFIG, f, ensure_ascii=False, indent=2)
            logger.info(f"配置更新: {key} = {val}")
            print("  已保存\n")

# ─── 入口 ─────────────────────────────────────────────────────────────────────

def main():
    """主入口函数"""
    try:
        _main_impl()
    except KeyboardInterrupt:
        print("\n\n再见！")
        logger.info("用户中断退出")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"未捕获的异常: {e}", exc_info=True)
        print(f"\n❌ 系统错误: {e}")
        print("请查看 agent.log 获取详细信息")
        sys.exit(1)


def _main_impl():
    """主实现函数（所有逻辑放在这里，便于异常处理）"""
    # 支持命令行参数
    debug_mode = "--debug" in sys.argv
    if debug_mode:
        global logger
        logger = setup_logging(debug_mode=True)
        logger.info("启用调试模式")
    
    skills      = load_skills()
    memories    = load_memory()  # 保留用于向后兼容
    conversation = []

    # 启动时同步 SkillHub 技能
    logger.info("检查SkillHub同步...")
    sync_skillhub(skills)

    logger.info(f"智能体启动完成 - 模型: {MODEL_REF[0]}, Skills: {len(skills)}, 记忆: {len(memories)}")
    
    # 美观的启动界面
    print("\n" + "="*60)
    print("  JwClaw - 智能体系统 v0.1.64")
    print("="*60)
    print(f"\n  系统信息:")
    print(f"     模型:   {MODEL_REF[0]}")
    print(f"     Skills:  {len(skills)} 个已加载")
    print(f"     记忆:  {len(memories)} 条")
    
    if debug_mode:
        print(f"     模式:    调试模式")
    else:
        print(f"     模式:    生产模式")
    
    # 显示安全特性
    security_features = []
    if SECURE_CONFIG_AVAILABLE:
        security_features.append("加密配置")
    if SANDBOX_AVAILABLE:
        security_features.append("沙箱执行")
    if CACHE_AVAILABLE:
        security_features.append("智能缓存")
    
    if security_features:
        print(f"\n  安全特性: {' | '.join(security_features)}")
    
    print(f"\n  可用命令:")
    print(f"     help            - 查看帮助")
    print(f"     skills          - 列出所有技能")
    print(f"     skillinfo <名称> - 查看技能详情")
    print(f"     memory          - 查看会话记忆")
    print(f"     status          - 显示系统状态")
    print(f"     new             - 开始新对话")
    print(f"     quit            - 退出系统")
    
    print(f"\n  提示: 输入 'help' 查看详细用法，按 ESC 中断生成")
    print("="*60 + "\n")

    while True:
        try:
            user_input = input("用户> ").strip()
        except (KeyboardInterrupt, EOFError):
            logger.info("用户退出程序")
            print("\n再见！")
            break

        if not user_input:
            continue
        
        # 记录到对话历史
        if CONTEXT_MANAGER_AVAILABLE:
            context_manager.add_conversation("user", user_input)
        
        cmd = user_input.lower()
        if cmd in ("quit", "exit"):
            logger.info("用户输入quit退出")
            print("再见！")
            break
        elif cmd == "help":
            logger.debug("用户查看帮助")
            if HELP_SYSTEM_AVAILABLE:
                # 检查是否有特定命令参数
                parts = user_input.split(None, 1)
                if len(parts) > 1:
                    print(help_system.get_help(parts[1].strip()))
                else:
                    print(help_system.get_help())
            else:
                print("帮助系统不可用")
            print()
        elif cmd == "status":
            logger.debug("用户查看系统状态")
            print(f"\n📊 系统状态:")
            print(f"  模型: {MODEL_REF[0]}")
            print(f"  API地址: {CONFIG['api_base']}")
            print(f"  Skills数量: {len(skills)}")
            print(f"  记忆数量: {len(memories)}")
            print(f"  对话轮次: {len(conversation)}")
            print(f"  调试模式: {'是' if '--debug' in sys.argv else '否'}")
            print(f"  安全配置: {'是' if SECURE_CONFIG_AVAILABLE else '否'}")
            print(f"  沙箱执行: {'是' if SANDBOX_AVAILABLE else '否'}")
            if RULES_ENGINE_AVAILABLE:
                violations = rules_engine.get_violation_report()
                print(f"  规则违规: {violations['total_violations']} 次")
            print()
        elif cmd == "skills":
            logger.debug("用户查看skills列表")
            skills = load_skills()
            for s in skills.values():
                print(f"  {s['name']}: {s['description']}")
            print()
        elif cmd == "memory":
            # 查看最近记忆
            if CONTEXT_MANAGER_AVAILABLE:
                print("\n🧠 最近记忆:")
                memories_list = context_manager.session_memory.get_recent_memories(10)
                if memories_list:
                    for m in memories_list:
                        print(f"  {m}")
                else:
                    print("  暂无记忆")
                print()
            else:
                print("上下文管理器不可用")
        elif cmd.startswith("skillinfo "):
            # 查看特定技能的详细信息
            skill_name = user_input.split(None, 1)[1].strip()
            if SKILL_METADATA_AVAILABLE:
                info = metadata_manager.get_skill_info(skill_name)
                if info:
                    meta = info['metadata']
                    print(f"\n📦 技能信息: {skill_name}")
                    print(f"   版本: {meta['version']}")
                    print(f"   作者: {meta['author']}")
                    print(f"   使用次数: {meta['usage_count']}")
                    print(f"   成功率: {meta['success_rate']:.1%}")
                    print(f"   最后使用: {meta['last_used'] or '从未'}")
                    if meta['tags']:
                        print(f"   标签: {', '.join(meta['tags'])}")
                    if info['missing_dependencies']:
                        print(f"   ⚠️  缺失依赖: {', '.join(info['missing_dependencies'])}")
                    if info['missing_modules']:
                        print(f"   ⚠️  缺失模块: {', '.join(info['missing_modules'])}")
                    print(f"   状态: {info['status']}")
                else:
                    print(f"未找到技能: {skill_name}")
            else:
                print("元数据系统不可用")
            print()
        elif cmd == "memory":
            logger.debug(f"用户查看记忆，显示最近10条")
            for m in memories[-10:]:
                tags_str = ", ".join(m.get("tags", []))
                usage = m.get("usage_count", 1)
                print(f"  [{m['time']}] (使用{usage}次) [{tags_str}]")
                print(f"    {m['summary']}")
            print()
        elif cmd == "clean_memory":
            logger.info("用户触发记忆清理")
            cleaned_count = _cleanup_memories(memories)
            print(f"  已清理 {cleaned_count} 条重复/过期记忆\n")
        elif cmd == "new":
            logger.info("用户开启新对话")
            conversation = []
            print("  新对话已开启\n")
        elif cmd == "config":
            logger.debug("用户修改配置")
            handle_config()
            CONFIG.update(load_config())
            MODEL_REF[0] = CONFIG["model"]
        else:
            run(user_input, skills, memories, conversation)
            print()

if __name__ == "__main__":
    main()
