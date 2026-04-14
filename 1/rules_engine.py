# -*- coding: utf-8 -*-
"""
rules_engine.py - Agent行为规则引擎
定义和管理Agent的核心行为规则，确保安全、合规、高效运行
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("agent")


class AgentRules:
    """Agent规则引擎"""
    
    def __init__(self):
        # 使用绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.RULES_FILE = os.path.join(script_dir, "agent_rules.json")
        self.rules = {}
        self.violations = []  # 违规记录
        self._load_rules()
    
    def _load_rules(self):
        """加载规则配置"""
        if os.path.exists(self.RULES_FILE):
            try:
                with open(self.RULES_FILE, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
                logger.info(f"规则引擎已加载: {len(self.rules)} 条规则")
            except Exception as e:
                logger.error(f"加载规则失败: {e}")
                self._init_default_rules()
        else:
            self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则"""
        self.rules = {
            # ========== 安全规则 ==========
            "security": {
                "forbidden_commands": [
                    "rm -rf /",
                    "format C:",
                    "del /s /q C:\\*",
                    "shutdown -s -t 0",
                ],
                "forbidden_operations": [
                    "delete_system_files",
                    "modify_registry_critical",
                    "disable_security_software",
                ],
                "require_confirmation": [
                    "delete_multiple_files",
                    "modify_system_settings",
                    "install_software",
                ],
                "max_file_operations": 100,  # 单次最多操作文件数
                "protected_directories": [
                    "C:\\Windows",
                    "C:\\Program Files",
                    "C:\\ProgramData",
                ]
            },
            
            # ========== 行为规则 ==========
            "behavior": {
                "language": "zh-CN",  # 回复语言：中文
                "response_style": "concise",  # 简洁明了
                "always_think_before_act": True,  # 行动前先思考
                "prefer_local_skills": True,  # 优先使用本地skills
                "never_say_cannot": True,  # 永不说不行，尝试替代方案
                "auto_save_experience": True,  # 自动保存成功经验
            },
            
            # ========== 执行规则 ==========
            "execution": {
                "max_retries": 3,  # 最大重试次数
                "timeout_seconds": 300,  # 默认超时5分钟
                "parallel_tasks": False,  # 不并行执行任务
                "cache_successful_results": True,  # 缓存成功结果
                "log_all_operations": True,  # 记录所有操作
            },
            
            # ========== 学习规则 ==========
            "learning": {
                "save_success_patterns": True,  # 保存成功模式
                "record_failure_reasons": True,  # 记录失败原因
                "memory_decay_days": 90,  # 记忆衰减天数
                "min_usage_count_to_keep": 2,  # 最少使用次数才保留
                "auto_cleanup_memory": True,  # 自动清理无效记忆
            },
            
            # ========== 隐私规则 ==========
            "privacy": {
                "never_store_passwords": True,  # 绝不存储密码
                "never_store_api_keys_plain": True,  # API密钥必须加密
                "encrypt_sensitive_data": True,  # 敏感数据加密
                "ask_before_sharing": True,  # 分享前询问
            }
        }
        
        self._save_rules()
        logger.info("已初始化默认规则")
    
    def _save_rules(self):
        """保存规则配置"""
        try:
            with open(self.RULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存规则失败: {e}")
    
    def check_command_safety(self, command: str) -> dict:
        """
        检查命令安全性
        
        Returns:
            {
                "safe": bool,
                "risk_level": "low" | "medium" | "high" | "critical",
                "reason": str,
                "require_confirmation": bool
            }
        """
        cmd_lower = command.lower()
        
        # 检查禁止命令
        for forbidden in self.rules["security"]["forbidden_commands"]:
            if forbidden.lower() in cmd_lower:
                return {
                    "safe": False,
                    "risk_level": "critical",
                    "reason": f"检测到禁止命令: {forbidden}",
                    "require_confirmation": False
                }
        
        # 检查保护目录
        for protected_dir in self.rules["security"]["protected_directories"]:
            if protected_dir.lower() in cmd_lower:
                return {
                    "safe": False,
                    "risk_level": "high",
                    "reason": f"尝试访问受保护目录: {protected_dir}",
                    "require_confirmation": True
                }
        
        # 风险评估
        risk_keywords = {
            "critical": ["delete", "remove", "destroy", "format"],
            "high": ["modify", "change", "update", "install"],
            "medium": ["create", "copy", "move"],
        }
        
        for level, keywords in risk_keywords.items():
            if any(kw in cmd_lower for kw in keywords):
                return {
                    "safe": True,
                    "risk_level": level,
                    "reason": f"操作风险等级: {level}",
                    "require_confirmation": level in ["high", "critical"]
                }
        
        return {
            "safe": True,
            "risk_level": "low",
            "reason": "常规操作",
            "require_confirmation": False
        }
    
    def check_operation_allowed(self, operation: str, context: dict = None) -> dict:
        """
        检查操作是否允许
        
        Args:
            operation: 操作类型
            context: 上下文信息
            
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "suggestions": list
            }
        """
        # 检查禁止操作
        if operation in self.rules["security"]["forbidden_operations"]:
            return {
                "allowed": False,
                "reason": f"操作被禁止: {operation}",
                "suggestions": []
            }
        
        # 检查需要确认的操作
        if operation in self.rules["security"]["require_confirmation"]:
            return {
                "allowed": True,
                "reason": "操作需要用户确认",
                "suggestions": ["请向用户请求确认"]
            }
        
        return {
            "allowed": True,
            "reason": "操作允许",
            "suggestions": []
        }
    
    def get_behavior_guideline(self, situation: str) -> str:
        """
        根据情境获取行为指导
        
        Args:
            situation: 情境描述
            
        Returns:
            行为指导建议
        """
        behavior = self.rules["behavior"]
        
        guidelines = []
        
        if "language" in situation.lower():
            guidelines.append(f"使用{behavior['language']}回复")
        
        if "skill" in situation.lower() or "tool" in situation.lower():
            if behavior["prefer_local_skills"]:
                guidelines.append("优先使用本地已安装的skills")
            guidelines.append("不要跳过missing的skill，先尝试安装")
        
        if "cannot" in situation.lower() or "unable" in situation.lower():
            if behavior["never_say_cannot"]:
                guidelines.append("不要说'无法执行'，提供替代方案")
        
        if "experience" in situation.lower() or "success" in situation.lower():
            if behavior["auto_save_experience"]:
                guidelines.append("将成功经验保存到记忆中")
        
        return "; ".join(guidelines) if guidelines else "按默认规则执行"
    
    def record_violation(self, rule_name: str, details: str):
        """记录违规行为"""
        violation = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": rule_name,
            "details": details
        }
        self.violations.append(violation)
        
        # 只保留最近100条违规记录
        if len(self.violations) > 100:
            self.violations = self.violations[-100:]
        
        logger.warning(f"规则违规: {rule_name} - {details}")
    
    def get_violation_report(self) -> dict:
        """获取违规报告"""
        return {
            "total_violations": len(self.violations),
            "recent_violations": self.violations[-10:],
            "most_common_rules": self._get_most_violated_rules()
        }
    
    def _get_most_violated_rules(self) -> List[dict]:
        """获取最常违规的规则"""
        from collections import Counter
        rule_counts = Counter(v["rule"] for v in self.violations)
        return [
            {"rule": rule, "count": count}
            for rule, count in rule_counts.most_common(5)
        ]
    
    def update_rule(self, category: str, key: str, value):
        """更新规则"""
        if category in self.rules:
            self.rules[category][key] = value
            self._save_rules()
            logger.info(f"规则已更新: {category}.{key} = {value}")
        else:
            logger.error(f"规则类别不存在: {category}")
    
    def get_all_rules(self) -> dict:
        """获取所有规则"""
        return self.rules.copy()


# 全局规则引擎实例
rules_engine = AgentRules()


def check_safety(command: str) -> dict:
    """检查命令安全性（便捷函数）"""
    return rules_engine.check_command_safety(command)


def get_guideline(situation: str) -> str:
    """获取行为指导（便捷函数）"""
    return rules_engine.get_behavior_guideline(situation)


if __name__ == "__main__":
    # 测试
    engine = AgentRules()
    
    # 测试命令安全检查
    test_commands = [
        "dir C:\\Users",
        "rm -rf /",
        "del C:\\Windows\\system32\\*.dll",
        "pip install requests",
    ]
    
    print("=== 命令安全检查 ===")
    for cmd in test_commands:
        result = engine.check_command_safety(cmd)
        print(f"\n命令: {cmd}")
        print(f"  安全: {result['safe']}")
        print(f"  风险: {result['risk_level']}")
        print(f"  原因: {result['reason']}")
    
    # 测试行为指导
    print("\n\n=== 行为指导 ===")
    situations = [
        "用户使用英文提问",
        "本地有可用skill",
        "任务执行失败",
    ]
    
    for situation in situations:
        guideline = engine.get_behavior_guideline(situation)
        print(f"\n情境: {situation}")
        print(f"  指导: {guideline}")
