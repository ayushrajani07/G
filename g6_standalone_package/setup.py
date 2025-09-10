#!/usr/bin/env python3
"""
Setup script for G6 Options Analytics Platform - Standalone Package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            # Remove comments and version constraints for basic requirements
            req = line.split('#')[0].strip()
            if req:
                requirements.append(req)

setup(
    name="g6-options-analytics",
    version="3.0.0",
    author="G6 Development Team", 
    author_email="info@g6platform.com",
    description="Professional Options Trading Platform for Indian Markets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ayushrajani07/G",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0", 
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.17.0",
            "grafana-api>=1.0.3",
        ],
        "cloud": [
            "boto3>=1.28.0",
            "azure-storage-blob>=12.17.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "g6-platform=g6_platform.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "g6_platform": [
            "config/*.json",
            "config/*.yaml", 
            "templates/*.json",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/ayushrajani07/G/issues",
        "Source": "https://github.com/ayushrajani07/G",
        "Documentation": "https://github.com/ayushrajani07/G/blob/main/README.md",
    },
    keywords="options trading analytics NSE BSE NIFTY BANKNIFTY financial markets",
    zip_safe=False,
)