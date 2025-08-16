"""
Tests for logging configuration functionality.
"""

import pytest
import logging
import tempfile
from pathlib import Path

from anafis.core.logging_config import (
    create_log_formatter, create_console_handler, create_file_handler,
    get_default_log_directory, create_logger_config, setup_logger,
    setup_application_logging, get_module_logger, quick_setup
)


class TestLogFormatter:
    """Test log formatter creation."""

    def test_basic_formatter(self):
        """Test basic formatter creation."""
        formatter = create_log_formatter()
        assert isinstance(formatter, logging.Formatter)
        assert "%(asctime)s" in formatter._fmt
        assert "%(levelname)" in formatter._fmt

    def test_formatter_without_timestamp(self):
        """Test formatter without timestamp."""
        formatter = create_log_formatter(include_timestamp=False)
        assert "%(asctime)s" not in formatter._fmt
        assert "%(levelname)" in formatter._fmt

    def test_formatter_without_module(self):
        """Test formatter without module information."""
        formatter = create_log_formatter(include_module=False)
        assert "%(module)s" not in formatter._fmt
        assert "%(levelname)" in formatter._fmt


class TestConsoleHandler:
    """Test console handler creation."""

    def test_basic_console_handler(self):
        """Test basic console handler creation."""
        handler = create_console_handler()
        assert isinstance(handler, logging.StreamHandler)
        assert handler.level == logging.INFO

    def test_console_handler_with_level(self):
        """Test console handler with custom level."""
        handler = create_console_handler(level=logging.DEBUG)
        assert handler.level == logging.DEBUG

    def test_console_handler_with_formatter(self):
        """Test console handler with custom formatter."""
        formatter = create_log_formatter(include_timestamp=False)
        handler = create_console_handler(formatter=formatter)
        assert handler.formatter == formatter


class TestFileHandler:
    """Test file handler creation."""

    def test_basic_file_handler(self):
        """Test basic file handler creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            handler = create_file_handler(log_file)

            assert isinstance(handler, logging.handlers.RotatingFileHandler)
            assert handler.level == logging.DEBUG
            assert log_file.exists()  # File should be created

    def test_file_handler_directory_creation(self):
        """Test that file handler creates directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "subdir" / "test.log"
            handler = create_file_handler(log_file)

            assert log_file.parent.exists()
            assert log_file.exists()

    def test_file_handler_with_custom_settings(self):
        """Test file handler with custom settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            handler = create_file_handler(
                log_file,
                level=logging.WARNING,
                max_bytes=1024,
                backup_count=3
            )

            assert handler.level == logging.WARNING
            assert handler.maxBytes == 1024
            assert handler.backupCount == 3


class TestLoggerConfig:
    """Test logger configuration functions."""

    def test_create_logger_config(self):
        """Test logger configuration creation."""
        config = create_logger_config("test_logger")

        assert config['name'] == "test_logger"
        assert config['level'] == logging.INFO
        assert len(config['handlers']) == 2  # Console and file by default
        assert isinstance(config['log_directory'], Path)

    def test_logger_config_console_only(self):
        """Test logger config with console output only."""
        config = create_logger_config(
            "test_logger",
            console_output=True,
            file_output=False
        )

        assert len(config['handlers']) == 1
        assert config['handlers'][0]['type'] == 'console'

    def test_logger_config_file_only(self):
        """Test logger config with file output only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = create_logger_config(
                "test_logger",
                console_output=False,
                file_output=True,
                log_directory=Path(temp_dir)
            )

            assert len(config['handlers']) == 1
            assert config['handlers'][0]['type'] == 'file'


class TestLoggerSetup:
    """Test logger setup functionality."""

    def test_setup_logger(self):
        """Test logger setup from configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = create_logger_config(
                "test_setup_logger",
                log_directory=Path(temp_dir)
            )

            logger = setup_logger(config)

            assert logger.name == "test_setup_logger"
            assert len(logger.handlers) == 2
            assert not logger.propagate

    def test_setup_application_logging(self):
        """Test application logging setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = setup_application_logging(
                debug_mode=True,
                log_directory=Path(temp_dir)
            )

            assert logger.name == "anafis"
            assert logger.level == logging.DEBUG
            assert len(logger.handlers) >= 1

    def test_get_module_logger(self):
        """Test module logger creation."""
        logger = get_module_logger("test_module")
        assert logger.name == "anafis.test_module"

    def test_quick_setup(self):
        """Test quick setup function."""
        logger = quick_setup(debug=True)
        assert logger.name == "anafis"
        assert isinstance(logger, logging.Logger)


class TestDefaultLogDirectory:
    """Test default log directory detection."""

    def test_get_default_log_directory(self):
        """Test default log directory detection."""
        log_dir = get_default_log_directory()
        assert isinstance(log_dir, Path)
        assert "anafis" in str(log_dir).lower() or "ANAFIS" in str(log_dir)


class TestLoggerIntegration:
    """Test logger integration and functionality."""

    def test_logger_output(self):
        """Test that logger actually produces output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "integration_test.log"

            config = create_logger_config(
                "integration_test",
                console_output=False,
                file_output=True,
                log_directory=Path(temp_dir)
            )

            logger = setup_logger(config)

            # Log some messages
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")

            # Force flush
            for handler in logger.handlers:
                handler.flush()

            # Check that log file contains messages
            log_content = log_file.read_text()
            assert "Test info message" in log_content
            assert "Test warning message" in log_content
            assert "Test error message" in log_content

    def test_logger_levels(self):
        """Test logger level filtering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = create_logger_config(
                "level_test",
                level=logging.WARNING,
                console_output=False,
                file_output=True,
                log_directory=Path(temp_dir)
            )

            logger = setup_logger(config)

            # Log messages at different levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            # Force flush
            for handler in logger.handlers:
                handler.flush()

            # Check that only warning and error messages are logged
            log_file = Path(temp_dir) / "level_test.log"
            log_content = log_file.read_text()

            assert "Debug message" not in log_content
            assert "Info message" not in log_content
            assert "Warning message" in log_content
            assert "Error message" in log_content