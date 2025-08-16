#!/usr/bin/env python3
"""
Test runner script for ANAFIS.

This script provides convenient test running with various options.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="ANAFIS Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test.py                    # Run all tests
  python scripts/test.py --fast            # Skip slow tests
  python scripts/test.py --coverage        # Run with coverage
  python scripts/test.py --gui             # Run only GUI tests
  python scripts/test.py --core            # Run only core tests
  python scripts/test.py --lint            # Run linting only
  python scripts/test.py --type-check      # Run type checking only
  python scripts/test.py --all             # Run everything
        """
    )

    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Run only GUI tests"
    )

    parser.add_argument(
        "--core",
        action="store_true",
        help="Run only core tests"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )

    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run linting (flake8)"
    )

    parser.add_argument(
        "--format",
        action="store_true",
        help="Format code with black"
    )

    parser.add_argument(
        "--type-check",
        action="store_true",
        help="Run type checking (mypy)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all checks (tests, linting, type checking)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    success = True

    print("ANAFIS Test Runner")
    print("=" * 30)
    print()

    # Format code if requested
    if args.format or args.all:
        print("Formatting code with black...")
        cmd = ["black", "anafis", "tests", "scripts"]
        if not run_command(cmd, cwd=project_root):
            success = False
        print()

    # Run linting if requested
    if args.lint or args.all:
        print("Running linting with flake8...")
        cmd = ["flake8", "anafis", "tests"]
        if not run_command(cmd, cwd=project_root):
            success = False
        print()

    # Run type checking if requested
    if args.type_check or args.all:
        print("Running type checking with mypy...")
        cmd = ["mypy", "anafis"]
        if not run_command(cmd, cwd=project_root):
            success = False
        print()

    # Run tests if not doing only linting/type checking
    if not (args.lint and not args.all) and not (args.type_check and not args.all):
        print("Running tests...")

        # Build pytest command
        cmd = ["pytest"]

        if args.verbose:
            cmd.append("-v")

        if args.coverage or args.all:
            cmd.extend(["--cov=anafis", "--cov-report=term-missing", "--cov-report=html"])

        # Test selection
        if args.fast:
            cmd.extend(["-m", "not slow"])
        elif args.gui:
            cmd.extend(["-m", "gui"])
        elif args.core:
            cmd.append("tests/core/")
        elif args.integration:
            cmd.extend(["-m", "integration"])

        if not run_command(cmd, cwd=project_root):
            success = False
        print()

    # Summary
    if success:
        print("✅ All checks passed!")
        return 0
    else:
        print("❌ Some checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())