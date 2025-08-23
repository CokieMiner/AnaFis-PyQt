#!/usr/bin/env python3
"""
Quick virtual environment setup for ANAFIS.

This script creates a virtual environment and installs the project
for immediate testing and development.
"""

import sys
import subprocess
import venv
from pathlib import Path


def main():
    """Set up virtual environment and install project."""

    # Check Python version
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)

    print("Setting up ANAFIS development environment...")
    print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print()

    project_root = Path(__file__).parent.parent  # Go up one level from scripts/
    venv_path = project_root / "venv"

    # Remove existing venv if it exists
    if venv_path.exists():
        print("Removing existing virtual environment...")
        import shutil

        try:
            shutil.rmtree(venv_path)
        except PermissionError:
            print("WARNING: Cannot remove existing venv (may be active). Please deactivate and try again.")
            print("Or manually delete the 'venv' folder and run this script again.")
            sys.exit(1)

    # Create virtual environment
    print("Creating virtual environment...")
    venv.create(venv_path, with_pip=True)

    # Get paths to executables
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
        activate_script = venv_path / "Scripts" / "activate.bat"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
        activate_script = venv_path / "bin" / "activate"

    # Upgrade pip
    print("Upgrading pip...")
    try:
        subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    except subprocess.CalledProcessError:
        print("WARNING: Pip upgrade failed, continuing with existing version...")

    # Install project in development mode
    print("Installing ANAFIS in development mode...")
    subprocess.run([str(pip_exe), "install", "-e", ".[dev]"], cwd=project_root, check=True)

    print()
    print("Setup complete!")
    print()
    print("To activate the virtual environment:")
    if sys.platform == "win32":
        print(f"   {activate_script}")
    else:
        print(f"   source {activate_script}")
    print()
    print("Then you can:")
    print("   python -m anafis.app --help          # See application options")
    print("   python -m anafis.app --no-gui        # Test without GUI")
    print("   python -m anafis.app --debug         # Run with debug logging")
    print("   pytest                               # Run tests")
    print("   pytest --cov=anafis                  # Run tests with coverage")
    print("   python scripts/test.py --all         # Run all quality checks")
    print()
    print("Happy coding!")


if __name__ == "__main__":
    main()
