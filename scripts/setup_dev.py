#!/usr/bin/env python3
"""
Development environment setup script for ANAFIS.

This script creates a virtual environment and installs all dependencies
needed for development and testing.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def create_venv(venv_path):
    """Create a virtual environment."""
    print(f"Creating virtual environment at {venv_path}")
    venv.create(venv_path, with_pip=True)
    print("Virtual environment created successfully")


def get_venv_python(venv_path):
    """Get the path to the Python executable in the virtual environment."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_venv_pip(venv_path):
    """Get the path to the pip executable in the virtual environment."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def upgrade_pip(venv_path):
    """Upgrade pip in the virtual environment."""
    pip_path = get_venv_pip(venv_path)
    print("Upgrading pip...")
    run_command([str(pip_path), "install", "--upgrade", "pip"])


def install_dependencies(venv_path, project_root):
    """Install project dependencies."""
    pip_path = get_venv_pip(venv_path)

    print("Installing project in development mode...")
    run_command([str(pip_path), "install", "-e", ".[dev]"], cwd=project_root)

    print("Installing additional development tools...")
    dev_packages = [
        "ipython",  # Better REPL
        "jupyter",  # Notebooks for experimentation
        "tox",      # Testing across Python versions
    ]

    for package in dev_packages:
        print(f"Installing {package}...")
        run_command([str(pip_path), "install", package])


def create_activation_scripts(venv_path, project_root):
    """Create convenient activation scripts."""

    # Windows batch file
    if sys.platform == "win32":
        activate_script = project_root / "activate_dev.bat"
        with open(activate_script, 'w') as f:
            f.write(f"""@echo off
echo Activating ANAFIS development environment...
call "{venv_path}\\Scripts\\activate.bat"
echo.
echo Development environment activated!
echo.
echo Available commands:
echo   python -m anafis.app --help    # Run ANAFIS
echo   pytest                         # Run tests
echo   pytest --cov=anafis           # Run tests with coverage
echo   black anafis tests             # Format code
echo   flake8 anafis tests            # Lint code
echo   mypy anafis                    # Type check
echo.
""")
        print(f"Created activation script: {activate_script}")

    # Unix shell script
    activate_script = project_root / "activate_dev.sh"
    with open(activate_script, 'w') as f:
        f.write(f"""#!/bin/bash
echo "Activating ANAFIS development environment..."
source "{venv_path}/bin/activate"
echo
echo "Development environment activated!"
echo
echo "Available commands:"
echo "  python -m anafis.app --help    # Run ANAFIS"
echo "  pytest                         # Run tests"
echo "  pytest --cov=anafis           # Run tests with coverage"
echo "  black anafis tests             # Format code"
echo "  flake8 anafis tests            # Lint code"
echo "  mypy anafis                    # Type check"
echo
""")

    # Make shell script executable
    if sys.platform != "win32":
        os.chmod(activate_script, 0o755)
        print(f"Created activation script: {activate_script}")


def main():
    """Main setup function."""
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"

    print("ANAFIS Development Environment Setup")
    print("=" * 40)
    print(f"Project root: {project_root}")
    print(f"Virtual environment: {venv_path}")
    print()

    # Check Python version
    if sys.version_info < (3, 10):
        print("Error: Python 3.10 or higher is required")
        sys.exit(1)

    print(f"Python version: {sys.version}")
    print()

    # Remove existing venv if it exists
    if venv_path.exists():
        print("Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_path)

    # Create virtual environment
    create_venv(venv_path)

    # Upgrade pip
    upgrade_pip(venv_path)

    # Install dependencies
    install_dependencies(venv_path, project_root)

    # Create activation scripts
    create_activation_scripts(venv_path, project_root)

    print()
    print("=" * 40)
    print("Setup complete!")
    print()
    print("To activate the development environment:")
    if sys.platform == "win32":
        print(f"  activate_dev.bat")
    else:
        print(f"  source activate_dev.sh")
    print()
    print("Or manually:")
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate.bat")
    else:
        print(f"  source {venv_path}/bin/activate")
    print()
    print("Then you can run:")
    print("  python -m anafis.app --help")
    print("  pytest")
    print("  pytest --cov=anafis")


if __name__ == "__main__":
    main()