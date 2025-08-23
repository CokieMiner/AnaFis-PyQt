#!/usr/bin/env python3
"""
Convenience script to run ANAFIS with various options.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def main():
    """Main runner function."""
    parser = argparse.ArgumentParser(
        description="ANAFIS Application Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_anafis.py                 # Run normally
  python scripts/run_anafis.py --debug        # Run with debug logging
  python scripts/run_anafis.py --no-gui       # Run without GUI (testing)
  python scripts/run_anafis.py --reset-config # Reset configuration
        """,
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument("--no-gui", action="store_true", help="Run without GUI (for testing)")

    parser.add_argument("--reset-config", action="store_true", help="Reset configuration to defaults")

    parser.add_argument("--config-dir", type=Path, help="Custom configuration directory")

    parser.add_argument("--log-dir", type=Path, help="Custom log directory")

    args = parser.parse_args()

    # Build command
    cmd = [sys.executable, "-m", "anafis.app"]

    if args.debug:
        cmd.append("--debug")

    if args.no_gui:
        cmd.append("--no-gui")

    if args.reset_config:
        cmd.append("--reset-config")

    if args.config_dir:
        cmd.extend(["--config-dir", str(args.config_dir)])

    if args.log_dir:
        cmd.extend(["--log-dir", str(args.log_dir)])

    # Run the application
    project_root = Path(__file__).parent.parent

    print("Starting ANAFIS...")
    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error running application: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
