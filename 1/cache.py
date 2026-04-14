# -*- coding: utf-8 -*-
"""
cache.py - 简单缓存系统
用于缓存LLM响应和技能执行结果
"""

import hashlib
import time
import json
import os
from typing import Any, Optional


class SimpleCache:
    """简单的内存+文件缓存"""
    
    def __init__(self, cache_dir: str = "cache", ttl: int = 3600):
        """
        初始化缓存
        
        Args:
            cache_dir: 缓存目录
            ttl: 默认存活时间（秒）
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.memory_cache: dict = {}
        
        # 创建缓存目录
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _generate_key(self, key: str) -> str:
        """生成缓存键的哈希值"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在或过期返回None
        """
        cache_key = self._generate_key(key)
        
        # 先查内存缓存
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if time.time() - entry['timestamp'] < entry['ttl']:
                return entry['value']
            else:
                del self.memory_cache[cache_key]
        
        # 再查文件缓存
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    entry = json.load(f)
                
                if time.time() - entry['timestamp'] < entry['ttl']:
                    # 加载到内存
                    self.memory_cache[cache_key] = entry
                    return entry['value']
                else:
                    # 过期删除
                    os.remove(cache_file)
            except Exception:
                pass
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 存活时间（秒），None则使用默认值
        """
        cache_key = self._generate_key(key)
        ttl = ttl if ttl is not None else self.ttl
        
        entry = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
        
        # 保存到内存
        self.memory_cache[cache_key] = entry
        
        # 保存到文件
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False)
        except Exception as e:
            print(f"警告: 保存缓存失败: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        cache_key = self._generate_key(key)
        
        # 删除内存缓存
        self.memory_cache.pop(cache_key, None)
        
        # 删除文件缓存
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception:
                pass
    
    def clear(self):
        """清空所有缓存"""
        self.memory_cache.clear()
        
        # 删除所有缓存文件
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    try:
                        os.remove(os.path.join(self.cache_dir, filename))
                    except Exception:
                        pass
    
    def cleanup(self):
        """清理过期缓存"""
        now = time.time()
        
        # 清理内存缓存
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if now - entry['timestamp'] >= entry['ttl']
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # 清理文件缓存
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            entry = json.load(f)
                        
                        if now - entry['timestamp'] >= entry['ttl']:
                            os.remove(cache_file)
                    except Exception:
                        pass
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        memory_count = len(self.memory_cache)
        
        file_count = 0
        total_size = 0
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_count += 1
                    cache_file = os.path.join(self.cache_dir, filename)
                    total_size += os.path.getsize(cache_file)
        
        return {
            "memory_entries": memory_count,
            "file_entries": file_count,
            "total_size_bytes": total_size,
            "total_size_kb": round(total_size / 1024, 2)
        }


# 获取脚本所在目录，确保缓存目录位置正确
_script_dir = os.path.dirname(os.path.abspath(__file__))

# 全局缓存实例
llm_cache = SimpleCache(cache_dir=os.path.join(_script_dir, "cache", "llm"), ttl=7200)  # LLM缓存2小时
skill_cache = SimpleCache(cache_dir=os.path.join(_script_dir, "cache", "skills"), ttl=3600)  # 技能缓存1小时


def cache_llm_response(prompt: str, response: str, ttl: int = 7200):
    """缓存LLM响应"""
    llm_cache.set(f"llm:{prompt}", response, ttl)


def get_cached_llm_response(prompt: str) -> Optional[str]:
    """获取缓存的LLM响应"""
    return llm_cache.get(f"llm:{prompt}")


def cache_skill_result(skill_name: str, args: list, result: str, ttl: int = 3600):
    """缓存技能执行结果"""
    key = f"skill:{skill_name}:{str(args)}"
    skill_cache.set(key, result, ttl)


def get_cached_skill_result(skill_name: str, args: list) -> Optional[str]:
    """获取缓存的技能结果"""
    key = f"skill:{skill_name}:{str(args)}"
    return skill_cache.get(key)


if __name__ == "__main__":
    # 测试
    cache = SimpleCache()
    
    # 测试缓存
    cache.set("test_key", "test_value", ttl=60)
    result = cache.get("test_key")
    print(f"缓存读取: {result}")
    
    # 测试统计
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")
    
    # 测试清理
    cache.cleanup()
    print("缓存清理完成")
