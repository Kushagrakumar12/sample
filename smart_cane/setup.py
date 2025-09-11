"""
Smart Cane System Setup Script

Installation script for the Smart Cane navigation and safety system.
"""

from setuptools import setup, find_packages
import os

# Read README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Smart Cane System - Advanced Navigation and Safety System for Visually Impaired Users"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="smart-cane-system",
    version="1.0.0",
    author="Smart Cane Development Team",
    author_email="dev@smartcane.com",
    description="Advanced Navigation and Safety System for Visually Impaired Users",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Kushagrakumar12/sample",
    
    packages=find_packages(),
    include_package_data=True,
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Natural Language :: English",
    ],
    
    python_requires=">=3.8",
    install_requires=read_requirements(),
    
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=1.0",
        ],
        "gpu": [
            "torch>=1.9.0",
            "torchvision>=0.10.0",
        ],
        "cloud": [
            "azure-cognitiveservices-speech>=1.20.0",
            "google-cloud-speech>=2.0.0",
        ]
    },
    
    package_data={
        "smart_cane": [
            "config/*.json",
            "models/*.txt",
            "assets/sounds/*",
            "assets/icons/*",
        ]
    },
    
    entry_points={
        "console_scripts": [
            "smart-cane=smart_cane.main:main",
            "smart-cane-gui=smart_cane.main:main",
            "smart-cane-cli=smart_cane.main:main",
        ],
    },
    
    project_urls={
        "Bug Reports": "https://github.com/Kushagrakumar12/sample/issues",
        "Source": "https://github.com/Kushagrakumar12/sample",
        "Documentation": "https://github.com/Kushagrakumar12/sample/wiki",
    },
    
    keywords=[
        "accessibility", "navigation", "computer-vision", "voice-assistance",
        "assistive-technology", "mobility", "blind", "visually-impaired",
        "obstacle-detection", "gps", "smart-cane", "safety"
    ],
    
    zip_safe=False,
)