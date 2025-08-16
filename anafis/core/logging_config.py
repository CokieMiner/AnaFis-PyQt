"""
Functional logging configuration for ANAFIS.

This module provides pure functions for setting up and configuring
the application's logging system using Python's built-in logging module.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def create_log_formatter(include_timestamp: bool = True,
                        include_module: bool = True) -> logging.Formatter:
    """
    Create a log formatter with configurable components.

    Args:
        include_timestamp: Whether to include timestamp in log messages
        include_module: Whether to include module name in log messages

    Returns:
        Configured logging.Formatter instance
    """
    format_parts = []

    if include_timestamp:
        format_parts.append("%(asctime)s")

    format_parts.extend([
        "%(levelname)-8s",
        "%(name)s"
    ])

    if include_module:
        format_parts.append("%(module)s:%(lineno)d")

    format_parts.append("%(message)s")

    format_string = " - ".join(format_parts)

    return logging.Formatter(
        fmt=format_string,
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def create_console_handler(level: int = logging.INFO,
                          formatter: Optional[logging.Formatter] = None) -> logging.StreamHandler:
    """
    Create a console handler for logging output.

    Args:
        level: Logging level for the handler
        formatter: Optional formatter, creates default if None

    Returns:
        Configured console handler
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if formatter is None:
        formatter = create_log_formatter(include_timestamp=False)

    handler.setFormatter(formatter)
    return handler


def create_file_handler(log_file_path: Path,
                       level: int = logging.DEBUG,
                       max_bytes: int = 10 * 1024 * 1024,  # 10MB
                       backup_count: int = 5,
                       formatter: Optional[logging.Formatter] = None) -> logging.handlers.RotatingFileHandler:
    """
    Create a rotating file handler for logging output.

    Args:
        log_file_path: Path to the log file
        level: Logging level for the handler
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        formatter: Optional formatter, creates default if None

    Returns:
        Configured rotating file handler
    """
    # Ensure log directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    handler.setLevel(level)

    if formatter is None:
        formatter = create_log_formatter(include_timestamp=True, include_module=True)

    handler.setFormatter(formatter)
    return handler


def get_default_log_directory() -> Path:
    """
    Get the default directory for log files.

    Returns:
        Path to the default log directory
    """
    if sys.platform == "win32":
        # Windows: Use AppData/Local
        import os
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        return Path(app_data) / "ANAFIS" / "logs"
    else:
        # Unix-like: Use ~/.local/share
        return Path.home() / ".local" / "share" / "anafis" / "logs"


def create_logger_config(name: str,
                        level: int = logging.INFO,
                        console_output: bool = True,
                        file_output: bool = True,
                        log_directory: Optional[Path] = None) -> Dict[str, Any]:
    """
    Create a logger configuration dictionary.

    Args:
        name: Logger name
        level: Base logging level
        console_output: Whether to enable console output
        file_output: Whether to enable file output
        log_directory: Directory for log files, uses default if None

    Returns:
        Dictionary containing logger configuration
    """
    if log_directory is None:
        log_directory = get_default_log_directory()

    config = {
        'name': name,
        'level': level,
        'handlers': [],
        'log_directory': log_directory
    }

    if console_output:
        config['handlers'].append({
            'type': 'console',
            'level': logging.INFO,
            'formatter': create_log_formatter(include_timestamp=False)
        })

    if file_output:
        log_file = log_directory / f"{name}.log"
        config['handlers'].append({
            'type': 'file',
            'path': log_file,
            'level': logging.DEBUG,
            'formatter': create_log_formatter(include_timestamp=True, include_module=True)
        })

    return config


def setup_logger(config: Dict[str, Any]) -> logging.Logger:
    """
    Set up a logger based on configuration dictionary.

    Args:
        config: Logger configuration from create_logger_config()

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(config['name'])
    logger.setLevel(config['level'])

    # Clear any existing handlers
    logger.handlers.clear()

    # Add configured handlers
    for handler_config in config['handlers']:
        if handler_config['type'] == 'console':
            handler = create_console_handler(
                level=handler_config['level'],
                formatter=handler_config['formatter']
            )
        elif handler_config['type'] == 'file':
            handler = create_file_handler(
                log_file_path=handler_config['path'],
                level=handler_config['level'],
                formatter=handler_config['formatter']
            )
        else:
            continue

        logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def setup_application_logging(debug_mode: bool = False,
                            log_directory: Optional[Path] = None) -> logging.Logger:
    """
    Set up the main application logger with standard configuration.

    Args:
        debug_mode: Whether to enable debug-level logging
        log_directory: Custom log directory, uses default if None

    Returns:
        Configured application logger
    """
    level = logging.DEBUG if debug_mode else logging.INFO

    config = create_logger_config(
        name='anafis',
        level=level,
        console_output=True,
        file_output=True,
        log_directory=log_directory
    )

    logger = setup_logger(config)

    # Log startup information
    logger.info("ANAFIS logging system initialized")
    logger.info(f"Log level: {logging.getLevelName(level)}")
    logger.info(f"Log directory: {config['log_directory']}")

    return logger


def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        module_name: Name of the module (typically __name__)

    Returns:
        Logger instance for the module
    """
    return logging.getLogger(f"anafis.{module_name}")


# Convenience function for quick logger setup
def quick_setup(debug: bool = False) -> logging.Logger:
    """
    Quick setup function for basic logging configuration.

    Args:
        debug: Whether to enable debug logging

    Returns:
        Configured application logger
    """
    return setup_application_logging(debug_mode=debug)