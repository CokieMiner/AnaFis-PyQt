"""
Main application entry point for ANAFIS.

This module provides the main function and basic application setup
for the ANAFIS desktop application.
"""

import sys
import argparse
from pathlib import Path

import logging

from anafis import __version__
from anafis.gui.gui import create_gui_application, run_application

# Import core functionality
from anafis.core.logging_config import setup_application_logging
from anafis.core.config import get_user_config, validate_config, reset_to_defaults
from anafis.core.data_structures import ApplicationConfig


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description=("ANAFIS - Advanced Numerical Analysis and Fitting " "Interface System"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  anafis                    # Start with default settings
  anafis --debug           # Start with debug logging
  anafis --config-dir /path # Use custom config directory
  anafis --reset-config    # Reset to default configuration
        """,
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument("--config-dir", type=Path, help="Custom configuration directory")

    parser.add_argument("--log-dir", type=Path, help="Custom log directory")

    parser.add_argument("--reset-config", action="store_true", help="Reset configuration to defaults")

    parser.add_argument("--no-gui", action="store_true", help="Run without GUI (for testing/debugging)")

    parser.add_argument("--version", action="version", version=f"ANAFIS {get_version()}")

    return parser.parse_args()


def get_version() -> str:
    """
    Get the application version.

    Returns:
        Version string
    """
    return __version__


def setup_application(
    args: argparse.Namespace,
) -> tuple[logging.Logger, ApplicationConfig]:
    """
    Set up the application with logging and configuration.

    Args:
        args: Parsed command line arguments

    Returns:
        Tuple of (logger, config)
    """
    # Set up logging
    logger = setup_application_logging(debug_mode=args.debug, log_directory=Path(".logs"))

    logger.info(f"Starting ANAFIS version {get_version()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")

    # Load or reset configuration
    if args.reset_config:
        logger.info("Resetting configuration to defaults")
        config = reset_to_defaults()
    else:
        logger.info("Loading user configuration")
        config = get_user_config()

    # Validate configuration
    is_valid, errors = validate_config(config)
    if not is_valid:
        logger.warning("Configuration validation failed:")
        for error in errors:
            logger.warning(f"  - {error}")
        logger.info("Using default values for invalid settings")

    # Update debug mode from config if not set via command line
    if not args.debug and config.advanced.debug_mode:
        logger.info("Debug mode enabled via configuration")
        # Re-setup logging with debug mode
        logger = setup_application_logging(debug_mode=True, log_directory=args.log_dir)

    logger.info("Application setup complete")
    return logger, config


def main() -> int:
    """
    Main application entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Set up application (logging, config)
        logger, config = setup_application(args)

        # Create GUI application (unless no-gui mode)
        app = None if args.no_gui else create_gui_application(logger, config)

        # Run the application
        exit_code = run_application(app, logger, config)

        logger.info(f"Application exiting with code {exit_code}")
        return exit_code

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
