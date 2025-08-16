#!/usr/bin/env python3
"""
Test the ANAFIS installation and basic functionality.
"""

import sys
import importlib
from pathlib import Path


def test_python_version():
    """Test Python version requirement."""
    print("PYTHON: Testing Python version...")
    if sys.version_info < (3, 10):
        print(f"ERROR: Python 3.10+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"OK: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def test_import(module_name, description):
    """Test importing a module."""
    try:
        importlib.import_module(module_name)
        print(f"OK: {description}")
        return True
    except ImportError as e:
        print(f"ERROR: {description} - {e}")
        return False


def test_anafis_imports():
    """Test ANAFIS core imports."""
    print("\nPACKAGES: Testing ANAFIS core imports...")

    tests = [
        ("anafis", "ANAFIS package"),
        ("anafis.core.logging_config", "Logging configuration"),
        ("anafis.core.config", "Configuration management"),
        ("anafis.core.data_structures", "Data structures"),
        ("anafis.app", "Application entry point"),
    ]

    success = True
    for module, desc in tests:
        if not test_import(module, desc):
            success = False

    return success


def test_dependencies():
    """Test required dependencies."""
    print("\nDEPENDENCIES: Testing dependencies...")

    # Core dependencies
    core_deps = [
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("scipy", "SciPy"),
        ("sympy", "SymPy"),
        ("matplotlib", "Matplotlib"),
        ("networkx", "NetworkX"),
    ]

    # Optional dependencies (may not be installed)
    optional_deps = [
        ("PyQt6", "PyQt6"),
        ("lmfit", "LMFit"),
        ("emcee", "emcee"),
        ("pint", "Pint"),
        ("h5py", "HDF5"),
        ("vispy", "VisPy"),
        ("numexpr", "NumExpr"),
        ("babel", "Babel"),
    ]

    success = True

    # Test core dependencies
    for module, desc in core_deps:
        if not test_import(module, desc):
            success = False

    # Test optional dependencies (don't fail if missing)
    print("\nOPTIONAL: Testing optional dependencies...")
    for module, desc in optional_deps:
        test_import(module, desc)

    return success


def test_basic_functionality():
    """Test basic ANAFIS functionality."""
    print("\nTESTING:  Testing basic functionality...")

    try:
        # Test logging setup
        from anafis.core.logging_config import quick_setup
        logger = quick_setup(debug=False)
        logger.info("Test log message")
        print("OK: Logging system")

        # Test configuration
        from anafis.core.config import create_default_config, validate_config
        config = create_default_config()
        is_valid, errors = validate_config(config)
        if is_valid:
            print("OK: Configuration system")
        else:
            print(f"ERROR: Configuration validation failed: {errors}")
            return False

        # Test data structures
        from anafis.core.data_structures import create_spreadsheet_state, create_application_state
        sheet_state = create_spreadsheet_state()
        app_state = create_application_state()
        print("OK: Data structures")

        return True

    except Exception as e:
        print(f"ERROR: Basic functionality test failed: {e}")
        return False


def test_application_entry():
    """Test application entry point."""
    print("\nAPP: Testing application entry point...")

    try:
        from anafis.app import parse_arguments, get_version

        # Test version
        version = get_version()
        print(f"OK: Application version: {version}")

        # Test argument parsing
        import sys
        old_argv = sys.argv
        sys.argv = ["anafis", "--help"]

        try:
            args = parse_arguments()
        except SystemExit:
            # --help causes SystemExit, which is expected
            pass
        finally:
            sys.argv = old_argv

        print("OK: Argument parsing")
        return True

    except Exception as e:
        print(f"ERROR: Application entry test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("TEST: ANAFIS Installation Test")
    print("=" * 40)

    tests = [
        test_python_version,
        test_anafis_imports,
        test_dependencies,
        test_basic_functionality,
        test_application_entry,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"ERROR: Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 40)
    print("SUMMARY: Test Summary")
    print("=" * 40)

    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"SUCCESS: All tests passed! ({passed}/{total})")
        print("\nYou can now run:")
        print("  python -m anafis.app --help")
        print("  python -m anafis.app --no-gui")
        print("  pytest")
        return 0
    else:
        print(f"WARNING:  Some tests failed ({passed}/{total})")
        print("\nPlease install missing dependencies:")
        print("  pip install -e .[dev]")
        return 1


if __name__ == "__main__":
    sys.exit(main())