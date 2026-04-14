# -*- coding: utf-8 -*-
"""
secure_config.py - 安全的配置管理模块
支持环境变量、加密存储和配置文件
参考Nanobot的安全设计理念
"""

import os
import json
import base64
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path


class SecureConfigManager:
    """安全配置管理器"""
    
    def __init__(self, config_file: str = None, 
                 env_prefix: str = "AGENT_"):
        # 使用绝对路径，确保从任何目录运行都能找到配置文件
        if config_file is None:
            # 获取脚本所在目录
            script_dir = Path(__file__).parent
            config_file = str(script_dir / "config.json")
        
        self.config_file = config_file
        self.env_prefix = env_prefix
        self._cache = {}
    
    def get_api_key(self) -> str:
        """
        获取API密钥（优先级：环境变量 > 加密配置 > 明文配置）
        
        Returns:
            API密钥字符串
        """
        # 1. 优先从环境变量读取
        env_key = f"{self.env_prefix}API_KEY"
        api_key = os.getenv(env_key)
        if api_key:
            return api_key
        
        # 2. 从加密配置读取
        encrypted_key = self._get_encrypted_value("api_key_encrypted")
        if encrypted_key:
            return self._decrypt(encrypted_key)
        
        # 3. 从明文配置读取（向后兼容）
        config = self._load_config()
        api_key = config.get("api_key", "")
        
        if api_key and api_key != "lm-studio":
            # 首次使用时自动加密
            self._encrypt_and_save("api_key", api_key)
        
        return api_key or "lm-studio"
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取完整配置（合并环境变量和配置文件）
        
        Returns:
            配置字典
        """
        # 加载基础配置
        config = self._load_config()
        
        # 环境变量覆盖（优先级更高）
        env_mappings = {
            f"{self.env_prefix}API_BASE": "api_base",
            f"{self.env_prefix}MODEL": "model",
            f"{self.env_prefix}API_KEY": "api_key",
            f"{self.env_prefix}DEBUG": "debug_mode",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 类型转换
                if config_key == "debug_mode":
                    config[config_key] = value.lower() in ('true', '1', 'yes')
                else:
                    config[config_key] = value
        
        return config
    
    def set_config(self, key: str, value: Any, encrypt: bool = False):
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
            encrypt: 是否加密存储（用于敏感信息）
        """
        config = self._load_config()
        
        if encrypt:
            # 加密存储
            encrypted = self._encrypt(str(value))
            config[f"{key}_encrypted"] = encrypted
            # 删除明文（如果存在）
            config.pop(key, None)
        else:
            config[key] = value
            # 删除加密版本（如果存在）
            config.pop(f"{key}_encrypted", None)
        
        self._save_config(config)
        self._cache.clear()
    
    def _encrypt(self, plaintext: str) -> str:
        """
        简单加密（Base64 + 盐值哈希）
        注意：这不是强加密，仅防止明文泄露
        生产环境应使用cryptography库
        """
        # 生成盐值（基于机器标识）
        salt = self._get_machine_salt()
        
        # 简单混淆（实际应使用AES等强加密）
        combined = f"{salt}:{plaintext}"
        encoded = base64.b64encode(combined.encode()).decode()
        
        return encoded
    
    def _decrypt(self, ciphertext: str) -> str:
        """解密"""
        try:
            decoded = base64.b64decode(ciphertext.encode()).decode()
            salt, plaintext = decoded.split(":", 1)
            
            # 验证盐值
            expected_salt = self._get_machine_salt()
            if salt != expected_salt:
                raise ValueError("盐值不匹配，可能是在其他机器上加密的")
            
            return plaintext
        except Exception as e:
            raise ValueError(f"解密失败: {e}")
    
    def _encrypt_and_save(self, key: str, value: str):
        """加密并保存配置项"""
        encrypted = self._encrypt(value)
        config = self._load_config()
        config[f"{key}_encrypted"] = encrypted
        config.pop(key, None)  # 删除明文
        self._save_config(config)
    
    def _get_encrypted_value(self, key: str) -> Optional[str]:
        """获取加密值"""
        config = self._load_config()
        return config.get(key)
    
    def _get_machine_salt(self) -> str:
        """生成基于机器的盐值"""
        # 使用用户名+主机名作为盐值
        username = os.getenv("USERNAME") or os.getenv("USER") or "unknown"
        hostname = os.getenv("COMPUTERNAME") or os.getenv("HOSTNAME") or "unknown"
        
        salt_str = f"{username}@{hostname}"
        return hashlib.sha256(salt_str.encode()).hexdigest()[:16]
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file in self._cache:
            return self._cache[self.config_file]
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告: 加载配置文件失败: {e}")
            config = {}
        
        self._cache[self.config_file] = config
        return config
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self._cache[self.config_file] = config
        except IOError as e:
            raise IOError(f"保存配置文件失败: {e}")
    
    def migrate_to_secure(self):
        """
        迁移现有配置到安全模式
        将明文API密钥转换为加密存储
        """
        config = self._load_config()
        
        migrated = False
        
        # 检查是否有明文API密钥
        if "api_key" in config and config["api_key"] not in ("", "lm-studio"):
            api_key = config.pop("api_key")
            config["api_key_encrypted"] = self._encrypt(api_key)
            migrated = True
        
        if migrated:
            self._save_config(config)
            print("✓ 配置已迁移到安全模式")
        else:
            print("无需迁移")


# 全局配置管理器实例
config_manager = SecureConfigManager()


def get_secure_api_key() -> str:
    """获取API密钥（安全方式）"""
    return config_manager.get_api_key()


def get_secure_config() -> Dict[str, Any]:
    """获取完整配置（安全方式）"""
    return config_manager.get_config()


if __name__ == "__main__":
    # 测试
    manager = SecureConfigManager()
    
    print("测试安全配置管理:")
    print(f"API Key: {manager.get_api_key()}")
    print(f"完整配置: {manager.get_config()}")
    
    # 迁移测试
    manager.migrate_to_secure()
