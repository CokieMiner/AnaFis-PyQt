"""
Main GUI setup for the ANAFIS application.

This module is responsible for creating the main application window,
the notebook for tabs, and other main GUI components.
"""

import sys
import logging
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator
from PyQt6.QtGui import QIcon

from anafis import __version__
from anafis.core.config import ApplicationConfig
from anafis.gui.shell.notebook import Notebook


def create_gui_application(logger: logging.Logger, config: ApplicationConfig) -> Optional[QApplication]:
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


def get_version() -> str:
    """
    Get the application version.

    Returns:
        Version string
    """
    return __version__


def run_application(app: Optional[QApplication], logger: logging.Logger, config: ApplicationConfig) -> int:
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

    main_window = None
    try:
        logger.info("Starting GUI application")
        main_window = Notebook(config=config)
        main_window.load_session()
        main_window.showMaximized()
        return app.exec()

    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    finally:
        if main_window:
            main_window.save_session()
