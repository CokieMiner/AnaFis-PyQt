# ANAFIS Scripts

This directory contains utility scripts for development, building, and deployment.

## Development Scripts

- `setup_venv.py` - Virtual environment setup and dependency installation
- `setup_dev.py` - Advanced development environment setup
- `test_installation.py` - Installation verification and testing
- `activate_dev.bat` / `activate_dev.sh` - Environment activation scripts

## Utility Scripts

- `test.py` - Test runner with various options
- `run_anafis.py` - Application runner with convenience options

## Usage

### From Project Root
```bash
# Setup
python setup.py                    # Runs scripts/setup_venv.py
./activate.sh                      # Runs scripts/activate_dev.sh

# Testing
python scripts/test_installation.py
python scripts/test.py --all
```

### From Scripts Directory
```bash
cd scripts
python setup_venv.py
python test_installation.py
./activate_dev.sh
```