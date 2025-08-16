# ANAFIS - Advanced Numerical Analysis and Fitting Interface System

ANAFIS is a detachable-notebook desktop application designed for scientific computing and data analysis. The application provides a multi-tab interface where each major capability (Spreadsheet, Curve-Fitting, Wolfram-like Solver, Monte-Carlo Simulator) operates as its own closable and detachable tab.

## Features

- **Multi-tab Interface**: Organize different analysis tools in separate workspaces
- **Detachable Tabs**: Tear off tabs into independent windows for multi-monitor workflows
- **Spreadsheet Tool**: Formula evaluation with unit support and dependency tracking
- **Curve Fitting**: Multiple algorithms (ODR, MCMC, Levenberg-Marquardt) with visualization
- **Equation Solver**: Wolfram-like symbolic mathematics with step-by-step solutions
- **Monte Carlo Simulation**: Generate synthetic datasets with parameter distributions
- **Inter-tab Communication**: Share data between analysis tools seamlessly
- **GPU Acceleration**: Automatic GPU detection and utilization where beneficial
- **Internationalization**: Multi-language support with hot-reloading

## Installation

### Requirements

- Python 3.10 or higher
- PyQt6
- Scientific computing libraries (NumPy, SciPy, Pandas, SymPy, etc.)

### Quick Setup (Recommended)

```bash
git clone https://github.com/anafis/anafis.git
cd anafis
python setup.py
```

This will create a virtual environment and install all dependencies.

### Manual Installation

#### From Source
```bash
git clone https://github.com/anafis/anafis.git
cd anafis
pip install -e .
```

#### Development Installation
```bash
git clone https://github.com/anafis/anafis.git
cd anafis
pip install -e ".[dev]"
```

#### Using requirements.txt
```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Basic Usage

```bash
# Start ANAFIS with default settings
anafis

# Start with debug logging
anafis --debug

# Reset configuration to defaults
anafis --reset-config
```

### Command Line Options

- `--debug`: Enable debug logging
- `--config-dir PATH`: Use custom configuration directory
- `--log-dir PATH`: Use custom log directory
- `--reset-config`: Reset configuration to defaults
- `--no-gui`: Run without GUI (for testing)
- `--version`: Show version information

## Development

### Project Structure

```
anafis/
├── anafis/                 # Main application package
│   ├── core/              # Core functionality (logging, config, data structures)
│   ├── gui/               # GUI components (to be implemented)
│   ├── services/          # Business logic services (to be implemented)
│   └── app.py             # Main application entry point
├── tests/                 # Test suite
├── docs/                  # Documentation
├── scripts/               # Development and utility scripts
│   ├── setup_venv.py      # Virtual environment setup
│   ├── test_installation.py # Installation verification
│   ├── activate_dev.*     # Environment activation scripts
│   └── *.py               # Other utility scripts
├── setup.py               # Convenience setup script
├── activate.*             # Convenience activation scripts
└── pyproject.toml         # Project configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=anafis

# Run specific test categories
pytest -m "not slow"        # Skip slow tests
pytest -m "gui"             # Run only GUI tests
pytest tests/core/          # Run only core tests
```

### Code Quality

The project uses several tools for code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pre-commit**: Git hooks for quality checks

```bash
# Format code
black anafis tests

# Run linting
flake8 anafis tests

# Type checking
mypy anafis
```

## Architecture

ANAFIS follows a functional programming approach with immutable data structures:

- **Pure Functions**: Business logic implemented as side-effect-free functions
- **Immutable State**: Application state managed through NamedTuples and dataclasses
- **PyQt6 Integration**: Minimal classes for GUI, maximum functional core
- **Library Reuse**: Leverages existing Python scientific libraries

### Core Components

- **Data Structures**: Immutable state containers for each analysis tool
- **Logging System**: Functional logging configuration with file and console output
- **Configuration Management**: Persistent settings with validation
- **Services Layer**: Pure functions for scientific computations
- **GUI Layer**: PyQt6 widgets with functional state management

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Run code quality checks (`black`, `flake8`, `mypy`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- Scientific computing powered by [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), and [Pandas](https://pandas.pydata.org/)
- Symbolic mathematics using [SymPy](https://www.sympy.org/)
- Curve fitting with [lmfit](https://lmfit.github.io/lmfit-py/) and [emcee](https://emcee.readthedocs.io/)
- Unit handling via [Pint](https://pint.readthedocs.io/)
- Visualization with [Matplotlib](https://matplotlib.org/) and [VisPy](https://vispy.org/)

## Status

This project is currently in active development. The foundation (Task 1) has been completed, including:

- ✅ Project structure and dependencies
- ✅ Core immutable data structures
- ✅ Logging system
- ✅ Configuration management
- ✅ Testing framework setup

Upcoming tasks include GUI implementation, scientific computing services, and feature integration.