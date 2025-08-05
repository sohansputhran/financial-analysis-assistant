import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple

# =============================================================================
# 1. SYSTEM VALIDATION FUNCTIONS
# =============================================================================

def check_python_version() -> bool:
    """Check if Python version is 3.9 or higher."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} is not supported")
        print("Please upgrade to Python 3.9 or higher")
        return False
    
    # WHY THIS MATTERS:
    # - Our project uses modern Python features (type hints, dataclasses, etc.)
    # - Some dependencies require Python 3.9+
    # - Prevents mysterious errors later

def check_git() -> bool:
    """Check if Git is installed."""
    try:
        # Run 'git --version' command silently
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print("✓ Git is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Git is not installed or not in PATH")
        return False
    
    # WHY THIS MATTERS:
    # - Git hooks for code quality depend on Git
    # - Version control is essential for collaboration
    # - Some Python packages might be installed from Git repos

# =============================================================================
# 2. VIRTUAL ENVIRONMENT SETUP
# =============================================================================

def create_virtual_environment() -> bool:
    """Create virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True
    
    try:
        # Create virtual environment using current Python interpreter
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create virtual environment: {e}")
        return False
    
    # WHY THIS MATTERS:
    # - Isolates project dependencies from system Python
    # - Prevents version conflicts between projects
    # - Makes deployment more predictable

# =============================================================================
# 3. DEPENDENCY INSTALLATION
# =============================================================================

def install_requirements() -> bool:
    """Install requirements from requirements.txt."""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("✗ requirements.txt not found")
        return False
    
    # Determine pip executable path (different on Windows vs Unix)
    if sys.platform == "win32":
        pip_executable = Path("venv/Scripts/pip")
    else:
        pip_executable = Path("venv/bin/pip")
    
    if not pip_executable.exists():
        print("✗ Virtual environment pip not found")
        return False
    
    try:
        # Install all requirements using virtual environment's pip
        subprocess.run([
            str(pip_executable), "install", "-r", "requirements.txt"
        ], check=True)
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False
    
    # WHY THIS MATTERS:
    # - Installs all necessary Python packages
    # - Uses virtual environment pip (not system pip)
    # - Handles dependency resolution automatically

# =============================================================================
# 4. CONFIGURATION FILE SETUP
# =============================================================================

def create_env_file() -> bool:
    """Create .env file from .env.example if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if not env_example.exists():
        print("✗ .env.example not found")
        return False
    
    try:
        # Copy template to actual .env file
        shutil.copy(env_example, env_file)
        print("✓ .env file created from .env.example")
        print("⚠️  Please edit .env file and add your API keys")
        return True
    except Exception as e:
        print(f"✗ Failed to create .env file: {e}")
        return False
    
    # WHY THIS MATTERS:
    # - Creates configuration file from template
    # - Prevents committing sensitive API keys to Git
    # - Provides all necessary configuration options

# =============================================================================  
# 5. DIRECTORY STRUCTURE CREATION
# =============================================================================

def create_directories() -> bool:
    """Create necessary project directories."""
    directories = [
        "data",              # Main data storage
        "data/cache",        # Cached API responses and files
        "data/reports",      # Generated reports
        "data/sample_data",  # Example data for testing
        "logs",              # Application logs
        "tests/__pycache__", # Python cache for tests
        "src/__pycache__"    # Python cache for source
    ]
    
    try:
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        print("✓ Project directories created")
        return True
    except Exception as e:
        print(f"✗ Failed to create directories: {e}")
        return False
    
    # WHY THIS MATTERS:
    # - Creates directory structure expected by the application
    # - Prevents runtime errors when app tries to write files
    # - Organizes data and logs properly

# =============================================================================
# 6. DEVELOPMENT TOOLS SETUP
# =============================================================================

def setup_git_hooks() -> bool:
    """Set up Git hooks for code quality."""
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("⚠️  Git repository not initialized, skipping hooks setup")
        return True
    
    # Pre-commit hook script content
    pre_commit_content = """#!/bin/sh
# Pre-commit hook for code quality checks

# Run black formatter
echo "Running Black formatter..."
black src/ --check
if [ $? -ne 0 ]; then
    echo "Code formatting issues found. Run 'black src/' to fix."
    exit 1
fi

# Run flake8 linter
echo "Running Flake8 linter..."
flake8 src/
if [ $? -ne 0 ]; then
    echo "Linting issues found. Please fix them before committing."
    exit 1
fi

echo "Pre-commit checks passed!"
"""
    
    try:
        pre_commit_hook = hooks_dir / "pre-commit"
        pre_commit_hook.write_text(pre_commit_content)
        os.chmod(pre_commit_hook, 0o755)  # Make executable
        print("✓ Git pre-commit hook installed")
        return True
    except Exception as e:
        print(f"⚠️  Failed to install Git hooks: {e}")
        return True  # Not critical, so don't fail setup
    
    # WHY THIS MATTERS:
    # - Automatically runs code quality checks before commits
    # - Prevents bad code from entering the repository
    # - Maintains consistent code style across the team

# =============================================================================
# 7. MAIN ORCHESTRATION FUNCTION
# =============================================================================

def validate_setup() -> List[Tuple[str, bool]]:
    """Validate the complete setup."""
    checks = [
        ("Python version", check_python_version()),
        ("Git installation", check_git()),
        ("Virtual environment", create_virtual_environment()),
        ("Requirements installation", install_requirements()),
        ("Environment file", create_env_file()),
        ("Directory structure", create_directories()),
        ("Git hooks", setup_git_hooks()),
    ]
    
    return checks

def main():
    """Main setup function."""
    print("🚀 Setting up Financial Analysis Assistant...")
    print("=" * 50)
    
    # Run all setup checks in order
    checks = validate_setup()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 Setup Summary:")
    
    success_count = 0
    for check_name, success in checks:
        status = "✓" if success else "✗"
        print(f"{status} {check_name}")
        if success:
            success_count += 1
    
    print(f"\n{success_count}/{len(checks)} checks passed")
    
    # Provide next steps or error guidance
    if success_count == len(checks):
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file and add your API keys")
        print("2. Activate virtual environment:")
        if sys.platform == "win32":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("3. Run the application:")
        print("   streamlit run src/main.py")
    else:
        print("\n⚠️  Setup completed with issues. Please resolve the failed checks.")
        sys.exit(1)  # Exit with error code for CI/CD systems

if __name__ == "__main__":
    main()

# =============================================================================
# WHAT HAPPENS WHEN YOU RUN THIS SCRIPT
# =============================================================================

"""
EXAMPLE OUTPUT:

🚀 Setting up Financial Analysis Assistant...
==================================================
✓ Python 3.11.2 is supported
✓ Git is installed
✓ Virtual environment created
✓ Requirements installed successfully
✓ .env file created from .env.example
⚠️  Please edit .env file and add your API keys
✓ Project directories created
✓ Git pre-commit hook installed

==================================================
📋 Setup Summary:
✓ Python version
✓ Git installation
✓ Virtual environment
✓ Requirements installation
✓ Environment file
✓ Directory structure
✓ Git hooks

7/7 checks passed

🎉 Setup completed successfully!

Next steps:
1. Edit .env file and add your API keys
2. Activate virtual environment:
   source venv/bin/activate
3. Run the application:
   streamlit run src/main.py
"""