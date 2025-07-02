#!/usr/bin/env python3
"""
Setup script for OllamaX-AI
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ollamax-ai",
    version="1.0.0",
    author="OllamaX-AI Team",
    author_email="contact@ollamax-ai.dev",
    description="God-level, offline, self-healing, multi-modal AI red team + software engineering platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ollamax-ai/ollamax-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Topic :: Software Development",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.11.0",
            "isort>=5.12.0",
            "mypy>=1.7.0",
            "flake8>=6.1.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ollamax-ai=main:app",
        ],
    },
    include_package_data=True,
    package_data={
        "ollamax-ai": [
            "configs/*.json",
            "ui/frontend/dist/*",
            "ui/frontend/dist/**/*",
        ],
    },
)