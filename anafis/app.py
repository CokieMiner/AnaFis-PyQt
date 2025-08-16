"""
Main application entry point for ANAFIS.

This module provides the main function and basic application setup
for the ANAFIS desktop application.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Import core functionality
from anafis.core.logging_config import setup_application_logging, get_module_logger
from anafis.core.config import get_user_config, save_user_config, validate_config


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="ANAFIS - Advanced Numerical Analysis and Fitting Interface System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  anafis                    # Start with default settings
  anafis --debug           # Start with debug logging
  anafis --config-dir /path # Use custom config directory
  anafis --reset-config    # Reset to default configuration
        """
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--config-dir",
        type=Path,
        help="Custom configuration directory"
    )

    parser.add_argument(
        "--log-dir",
        type=Path,
        help="Custom log directory"
    )

    parser.add_argument(
        "--reset-config",
        action="store_true",
        help="Reset configuration to defaults"
    )

    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run without GUI (for testing/debugging)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"ANAFIS {get_version()}"
    )

    return parser.parse_args()


def get_version() -> str:
    """
    Get the application version.

    Returns:
        Version string
    """
    try:
        from anafis import __version__
        return __version__
    except ImportError:
        return "0.1.0-dev"


def setup_application(args: argparse.Namespace) -> tuple[object, object]:
    """
    Set up the application with logging and configuration.

    Args:
        args: Parsed command line arguments

    Returns:
        Tuple of (logger, config)
    """
    # Set up logging
    logger = setup_application_logging(
        debug_mode=args.debug,
        log_directory=args.log_dir
    )

    logger.info(f"Starting ANAFIS version {get_version()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")

    # Load or reset configuration
    if args.reset_config:
        logger.info("Resetting configuration to defaults")
        from anafis.core.config import reset_to_defaults
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
        logger = setup_application_logging(
            debug_mode=True,
            log_directory=args.log_dir
        )

    logger.info("Application setup complete")
    return logger, config


def create_gui_application(logger: object, config: object) -> Optional[object]:
    """
    Create and configure the GUI application.

    Args:
        logger: Application logger
        config: Application configuration

    Returns:
        QApplication instance or None if GUI creation fails
    """
    try:
        # Import PyQt6 here to avoid import errors in no-gui mode
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTranslator, QLocale
        from PyQt6.QtGui import QIcon

        logger.info("Creating GUI application")

        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("ANAFIS")
        app.setApplicationVersion(get_version())
        app.setOrganizationName("ANAFIS Development Team")
        app.setOrganizationDomain("anafis.org")

        # Set up internationalization
        translator = QTranslator()
        locale = config.general.language.value
        if translator.load(f"anafis_{locale}", ":/translations/"):
            app.installTranslator(translator)
            logger.info(f"Loaded translation for locale: {locale}")
        else:
            logger.warning(f"Could not load translation for locale: {locale}")

        # Set application icon (when available)
        try:
            icon = QIcon(":/icons/anafis.png")
            app.setWindowIcon(icon)
        except Exception as e:
            logger.debug(f"Could not load application icon: {e}")

        # Apply theme settings
        if config.general.theme.value != "system":
            logger.info(f"Applying theme: {config.general.theme.value}")
            # Theme application will be implemented in later tasks

        logger.info("GUI application created successfully")
        return app

    except ImportError as e:
        logger.error(f"Failed to import GUI libraries: {e}")
        logger.error("Please ensure PyQt6 is installed")
        return None
    except Exception as e:
        logger.error(f"Failed to create GUI application: {e}")
        return None


def run_application(app: Optional[object], logger: object, config: object) -> int:
    """
    Run the main application.

    Args:
        app: QApplication instance (None for no-gui mode)
        logger: Application logger
        config: Application configuration

    Returns:
        Exit code
    """
    if app is None:
        logger.info("Running in no-GUI mode")
        logger.info("Application would start here (GUI not implemented yet)")
        return 0

    try:
        logger.info("Starting GUI application")

        # Create main window (will be implemented in later tasks)
        logger.info("Main window creation not yet implemented")
        logger.info("This is the foundation task - GUI will be added in subsequent tasks")

        # For now, just show that the application can start
        logger.info("Application foundation is working correctly")
        logger.info("Press Ctrl+C to exit")

        # Simple event loop for testing
        import time
        try:
            while True:
                app.processEvents()
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")

        return 0

    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1


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