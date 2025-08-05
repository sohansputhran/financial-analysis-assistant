# setup.py - Detailed Breakdown

from setuptools import setup, find_packages

# 1. READ PROJECT METADATA FROM FILES
# Instead of hardcoding, read from external files for consistency
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()  # Use README as package description

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    # Parse requirements.txt, ignoring empty lines and comments

# 2. PACKAGE SETUP CONFIGURATION
setup(
    # BASIC PACKAGE INFO
    name="financial-analysis-assistant",       # Package name (for pip install)
    version="0.1.0",                           # Current version (semantic versioning)
    author="Sohan Sanjeeva Puthran",           # Package author
    author_email="puthran.sohan@gmail.com",    # Contact email
    license="MIT",                             # License type (MIT in this case)

    # DESCRIPTIONS
    description="AI-powered financial analysis tool using Streamlit and Gemini AI",
    long_description=long_description,         # Detailed description from README
    long_description_content_type="text/markdown",  # README format
    
    # PROJECT LINKS
    url="https://github.com/sohansputhran/financial-analysis-assistant",
    
    # PACKAGE DISCOVERY
    packages=find_packages(),  # Automatically find all packages (folders with __init__.py)
    # This finds: src/, config/, tests/, etc.
    
    # PACKAGE CLASSIFICATION (for PyPI)
    classifiers=[
        "Development Status :: 3 - Alpha",           # Project maturity
        "Intended Audience :: Financial and Insurance Industry",  # Target users
        "License :: OSI Approved :: MIT License",    # License type
        "Operating System :: OS Independent",        # OS compatibility
        "Programming Language :: Python :: 3",      # Language
        "Programming Language :: Python :: 3.9",    # Supported versions
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    
    # PYTHON VERSION REQUIREMENTS
    python_requires=">=3.9",  # Minimum Python version needed
    
    # DEPENDENCIES
    install_requires=requirements,  # Main dependencies from requirements.txt
    
    # OPTIONAL DEPENDENCIES (install with pip install package[dev])
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    
    # COMMAND LINE SCRIPTS
    entry_points={
        "console_scripts": [
            "financial-analysis=src.main:main",  # Creates 'financial-analysis' command
        ],
    },
)