#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JwClaw 安装配置
支持 pip install 安装
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取 requirements
req_file = Path(__file__).parent / "requirements.txt"
requirements = []
if req_file.exists():
    requirements = [
        line.strip()
        for line in req_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="jwclaw",
    version="0.3.0",
    author="JwClaw Team",
    description="极简智能体 - 轻量级、无框架依赖的 AI Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/junweiin/jwclaw",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={
        "jwclaw": ["../skills/**/*", "../workspace/**/*"],
    },
    install_requires=requirements,
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "jwclaw=jwclaw.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="ai agent llm skill react cli",
    project_urls={
        "Bug Reports": "https://github.com/junweiin/jwclaw/issues",
        "Source": "https://github.com/junweiin/jwclaw",
    },
)
