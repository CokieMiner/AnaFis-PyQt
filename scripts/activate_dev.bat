@echo off
echo Activating ANAFIS development environment...
call ..\venv\Scripts\activate.bat
echo.
echo Development environment activated!
echo.
echo Available commands:
echo   python -m anafis.app --help          # Show application options
echo   python -m anafis.app --no-gui        # Test without GUI
echo   python -m anafis.app --debug         # Run with debug logging
echo   pytest                               # Run tests
echo   pytest --cov=anafis                  # Run tests with coverage
echo   python scripts/test.py --all         # Run all quality checks
echo   black anafis tests                   # Format code
echo   flake8 anafis tests                  # Lint code
echo   mypy anafis                          # Type check
echo.
echo Quick test: python scripts/test_installation.py
echo.