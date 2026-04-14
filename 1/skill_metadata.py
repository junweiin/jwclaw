# -*- coding: utf-8 -*-
"""
skill_metadata.py - Skill元数据管理
支持版本控制、依赖声明和能力描述
"""

import re
import os
from typing import Dict, List, Optional
from datetime import datetime


class SkillMetadata:
    """Skill元数据类"""
    
    def __init__(self, name: str):
        self.name = name
        self.version = "1.0.0"
        self.description = ""
        self.author = "Unknown"
        self.created_at = datetime.now().strftime("%Y-%m-%d")
        self.updated_at = self.created_at
        self.dependencies: List[str] = []  # 依赖的其他skills
        self.required_modules: List[str] = []  # 需要的Python模块
        self.tags: List[str] = []  # 标签
        self.usage_count = 0
        self.success_rate = 0.0
        self.last_used: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "dependencies": self.dependencies,
            "required_modules": self.required_modules,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "last_used": self.last_used,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SkillMetadata':
        """从字典创建"""
        meta = cls(data.get("name", "unknown"))
        meta.version = data.get("version", "1.0.0")
        meta.description = data.get("description", "")
        meta.author = data.get("author", "Unknown")
        meta.created_at = data.get("created_at", datetime.now().strftime("%Y-%m-%d"))
        meta.updated_at = data.get("updated_at", meta.created_at)
        meta.dependencies = data.get("dependencies", [])
        meta.required_modules = data.get("required_modules", [])
        meta.tags = data.get("tags", [])
        meta.usage_count = data.get("usage_count", 0)
        meta.success_rate = data.get("success_rate", 0.0)
        meta.last_used = data.get("last_used")
        return meta
    
    def increment_usage(self, success: bool = True):
        """增加使用计数"""
        self.usage_count += 1
        self.last_used = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 更新成功率（移动平均）
        if self.success_rate == 0:
            self.success_rate = 1.0 if success else 0.0
        else:
            alpha = 0.1  # 平滑因子
            self.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * self.success_rate
    
    def check_dependencies(self, available_skills: List[str]) -> List[str]:
        """
        检查依赖是否满足
        
        Returns:
            缺失的依赖列表
        """
        missing = []
        for dep in self.dependencies:
            if dep not in available_skills:
                missing.append(dep)
        return missing
    
    def check_modules(self) -> List[str]:
        """
        检查必需的Python模块是否已安装
        
        Returns:
            缺失的模块列表
        """
        missing = []
        for module in self.required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)
        return missing


class SkillMetadataManager:
    """Skill元数据管理器"""
    
    METADATA_FILE = "skills_metadata.json"
    
    def __init__(self):
        self.metadata: Dict[str, SkillMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """加载元数据"""
        import json
        
        if os.path.exists(self.METADATA_FILE):
            try:
                with open(self.METADATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for name, meta_dict in data.items():
                    self.metadata[name] = SkillMetadata.from_dict(meta_dict)
            except Exception as e:
                print(f"警告: 加载元数据失败: {e}")
                self.metadata = {}
    
    def save_metadata(self):
        """保存元数据"""
        import json
        
        data = {name: meta.to_dict() for name, meta in self.metadata.items()}
        
        try:
            with open(self.METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"错误: 保存元数据失败: {e}")
    
    def get_or_create(self, skill_name: str) -> SkillMetadata:
        """获取或创建元数据"""
        if skill_name not in self.metadata:
            self.metadata[skill_name] = SkillMetadata(skill_name)
        return self.metadata[skill_name]
    
    def update_from_skill_file(self, skill_name: str, content: str):
        """
        从skill文件内容解析元数据
        
        支持的元数据格式（在skill.md顶部）:
        ```
        # skill: name
        
        ## 元数据
        - version: 1.0.0
        - author: Your Name
        - dependencies: skill1, skill2
        - modules: os, sys, requests
        - tags: tool, utility
        ```
        """
        meta = self.get_or_create(skill_name)
        
        # 解析元数据块
        metadata_match = re.search(r'##\s*元数据\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if metadata_match:
            metadata_block = metadata_match.group(1)
            
            # 解析version
            version_match = re.search(r'-\s*version:\s*(.+)', metadata_block)
            if version_match:
                meta.version = version_match.group(1).strip()
            
            # 解析author
            author_match = re.search(r'-\s*author:\s*(.+)', metadata_block)
            if author_match:
                meta.author = author_match.group(1).strip()
            
            # 解析dependencies
            deps_match = re.search(r'-\s*dependencies:\s*(.+)', metadata_block)
            if deps_match:
                meta.dependencies = [d.strip() for d in deps_match.group(1).split(',')]
            
            # 解析modules
            modules_match = re.search(r'-\s*modules:\s*(.+)', metadata_block)
            if modules_match:
                meta.required_modules = [m.strip() for m in modules_match.group(1).split(',')]
            
            # 解析tags
            tags_match = re.search(r'-\s*tags:\s*(.+)', metadata_block)
            if tags_match:
                meta.tags = [t.strip() for t in tags_match.group(1).split(',')]
        
        # 更新description（从原有的描述部分）
        desc_match = re.search(r'##\s*描述\s*\n(.+)', content)
        if desc_match:
            meta.description = desc_match.group(1).strip()
        
        meta.updated_at = datetime.now().strftime("%Y-%m-%d")
        self.save_metadata()
    
    def record_usage(self, skill_name: str, success: bool = True):
        """记录技能使用"""
        meta = self.get_or_create(skill_name)
        meta.increment_usage(success)
        self.save_metadata()
    
    def get_skill_info(self, skill_name: str) -> Optional[dict]:
        """获取技能详细信息"""
        meta = self.metadata.get(skill_name)
        if not meta:
            return None
        
        # 检查依赖 - 延迟导入避免循环依赖
        try:
            from jwclaw import load_skills
            available_skills = list(load_skills().keys())
        except ImportError:
            available_skills = []
        
        missing_deps = meta.check_dependencies(available_skills)
        missing_modules = meta.check_modules()
        
        return {
            "metadata": meta.to_dict(),
            "missing_dependencies": missing_deps,
            "missing_modules": missing_modules,
            "status": "ready" if not missing_deps and not missing_modules else "incomplete"
        }
    
    def list_skills_summary(self) -> List[dict]:
        """列出所有技能的摘要信息"""
        summaries = []
        for name, meta in sorted(self.metadata.items()):
            summaries.append({
                "name": name,
                "version": meta.version,
                "usage_count": meta.usage_count,
                "success_rate": f"{meta.success_rate:.1%}",
                "tags": meta.tags,
                "last_used": meta.last_used or "从未使用"
            })
        return summaries


# 全局元数据管理器实例
metadata_manager = SkillMetadataManager()


def get_skill_metadata(skill_name: str) -> Optional[dict]:
    """获取技能元数据（便捷函数）"""
    return metadata_manager.get_skill_info(skill_name)


def record_skill_usage(skill_name: str, success: bool = True):
    """记录技能使用（便捷函数）"""
    metadata_manager.record_usage(skill_name, success)


if __name__ == "__main__":
    # 测试
    manager = SkillMetadataManager()
    
    # 创建测试元数据
    meta = manager.get_or_create("test_skill")
    meta.version = "1.0.0"
    meta.author = "Test Author"
    meta.dependencies = ["shell"]
    meta.tags = ["test", "demo"]
    
    manager.save_metadata()
    
    # 显示摘要
    print("技能摘要:")
    for summary in manager.list_skills_summary():
        print(f"  {summary}")
