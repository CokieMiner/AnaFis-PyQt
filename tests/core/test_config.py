"""
Tests for configuration management functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path

from anafis.core.config import (
    GeneralConfig, ComputationConfig, InterfaceConfig, UpdateConfig,
    AdvancedConfig, ApplicationConfig, Theme, Language, UpdateChannel,
    get_default_config_directory, get_config_file_path, create_default_config,
    config_to_dict, dict_to_config, save_config, load_config, update_config,
    validate_config, get_user_config, save_user_config, reset_to_defaults
)


class TestConfigDataClasses:
    """Test configuration dataclasses."""

    def test_general_config_defaults(self):
        """Test GeneralConfig default values."""
        config = GeneralConfig()
        assert config.language == Language.ENGLISH
        assert config.theme == Theme.SYSTEM
        assert config.startup_behavior == "restore_session"
        assert config.auto_save_interval == 300
        assert config.recent_files_limit == 10
        assert config.show_splash_screen is True
        assert config.check_updates_on_startup is True

    def test_computation_config_defaults(self):
        """Test ComputationConfig default values."""
        config = ComputationConfig()
        assert config.default_fitting_method == "lm"
        assert config.numerical_precision == 15
        assert config.max_iterations == 1000
        assert config.convergence_tolerance == 1e-8
        assert config.use_gpu_acceleration is True
        assert config.parallel_processing is True

    def test_interface_config_defaults(self):
        """Test InterfaceConfig default values."""
        config = InterfaceConfig()
        assert config.tab_detach_enabled is True
        assert config.tab_close_confirmation is True
        assert config.show_tooltips is True
        assert config.animation_enabled is True
        assert config.floating_tool_shortcuts is not None
        assert "F9" in config.floating_tool_shortcuts.values()

    def test_update_config_defaults(self):
        """Test UpdateConfig default values."""
        config = UpdateConfig()
        assert config.auto_check_enabled is True
        assert config.check_interval_hours == 24
        assert config.update_channel == UpdateChannel.STABLE
        assert config.auto_download is False

    def test_advanced_config_defaults(self):
        """Test AdvancedConfig default values."""
        config = AdvancedConfig()
        assert config.debug_mode is False
        assert config.log_level == "INFO"
        assert config.cache_size_mb == 100
        assert config.enable_profiling is False


class TestApplicationConfig:
    """Test ApplicationConfig NamedTuple."""

    def test_default_creation(self):
        """Test ApplicationConfig creation with defaults."""
        config = ApplicationConfig()
        assert isinstance(config.general, GeneralConfig)
        assert isinstance(config.computation, ComputationConfig)
        assert isinstance(config.interface, InterfaceConfig)
        assert isinstance(config.updates, UpdateConfig)
        assert isinstance(config.advanced, AdvancedConfig)
        assert config.config_version == "1.0"

    def test_creation_with_custom_sections(self):
        """Test ApplicationConfig creation with custom sections."""
        general = GeneralConfig(language=Language.SPANISH, theme=Theme.DARK)
        computation = ComputationConfig(numerical_precision=10)

        config = ApplicationConfig(
            general=general,
            computation=computation
        )

        assert config.general.language == Language.SPANISH
        assert config.general.theme == Theme.DARK
        assert config.computation.numerical_precision == 10

    def test_immutability(self):
        """Test that ApplicationConfig is immutable."""
        config = ApplicationConfig()

        # Should not be able to modify the config directly
        with pytest.raises(AttributeError):
            config.general = GeneralConfig()


class TestConfigPaths:
    """Test configuration path functions."""

    def test_get_default_config_directory(self):
        """Test default config directory detection."""
        config_dir = get_default_config_directory()
        assert isinstance(config_dir, Path)
        assert "anafis" in str(config_dir).lower() or "ANAFIS" in str(config_dir)

    def test_get_config_file_path(self):
        """Test config file path generation."""
        config_file = get_config_file_path()
        assert isinstance(config_file, Path)
        assert config_file.name == "config.json"

    def test_get_config_file_path_custom_dir(self):
        """Test config file path with custom directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_dir = Path(temp_dir)
            config_file = get_config_file_path(custom_dir)
            assert config_file.parent == custom_dir
            assert config_file.name == "config.json"


class TestConfigSerialization:
    """Test configuration serialization and deserialization."""

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = create_default_config()
        config_dict = config_to_dict(config)

        assert isinstance(config_dict, dict)
        assert "general" in config_dict
        assert "computation" in config_dict
        assert "interface" in config_dict
        assert "updates" in config_dict
        assert "advanced" in config_dict
        assert config_dict["config_version"] == "1.0"

        # Check that enums are converted to values
        assert config_dict["general"]["language"] == "en"
        assert config_dict["general"]["theme"] == "system"

    def test_dict_to_config(self):
        """Test converting dictionary to config."""
        original_config = create_default_config()
        config_dict = config_to_dict(original_config)
        restored_config = dict_to_config(config_dict)

        assert isinstance(restored_config, ApplicationConfig)
        assert restored_config.general.language == Language.ENGLISH
        assert restored_config.general.theme == Theme.SYSTEM
        assert restored_config.computation.numerical_precision == 15

    def test_roundtrip_serialization(self):
        """Test that serialization roundtrip preserves data."""
        original_config = ApplicationConfig(
            general=GeneralConfig(language=Language.FRENCH, theme=Theme.DARK),
            computation=ComputationConfig(numerical_precision=12),
            updates=UpdateConfig(update_channel=UpdateChannel.BETA)
        )

        # Convert to dict and back
        config_dict = config_to_dict(original_config)
        restored_config = dict_to_config(config_dict)

        assert restored_config.general.language == Language.FRENCH
        assert restored_config.general.theme == Theme.DARK
        assert restored_config.computation.numerical_precision == 12
        assert restored_config.updates.update_channel == UpdateChannel.BETA


class TestConfigFileOperations:
    """Test configuration file save/load operations."""

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.json"

            # Create and save config
            original_config = ApplicationConfig(
                general=GeneralConfig(language=Language.GERMAN),
                computation=ComputationConfig(max_iterations=500)
            )

            success = save_config(original_config, config_file)
            assert success is True
            assert config_file.exists()

            # Load config
            loaded_config = load_config(config_file)
            assert loaded_config.general.language == Language.GERMAN
            assert loaded_config.computation.max_iterations == 500

    def test_load_nonexistent_config(self):
        """Test loading config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_file = Path(temp_dir) / "nonexistent.json"

            config = load_config(nonexistent_file)
            assert isinstance(config, ApplicationConfig)
            # Should return default config
            assert config.general.language == Language.ENGLISH

    def test_save_config_creates_directory(self):
        """Test that save_config creates directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "subdir" / "config.json"

            config = create_default_config()
            success = save_config(config, config_file)

            assert success is True
            assert config_file.exists()
            assert config_file.parent.exists()

    def test_load_invalid_json(self):
        """Test loading config with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "invalid.json"

            # Write invalid JSON
            config_file.write_text("{ invalid json }")

            # Should return default config on error
            config = load_config(config_file)
            assert isinstance(config, ApplicationConfig)
            assert config.general.language == Language.ENGLISH


class TestConfigUpdate:
    """Test configuration update functionality."""

    def test_update_config_section(self):
        """Test updating a configuration section."""
        original_config = create_default_config()

        updated_config = update_config(
            original_config,
            "general",
            {"language": Language.SPANISH, "theme": Theme.DARK}
        )

        # Check that updates were applied
        assert updated_config.general.language == Language.SPANISH
        assert updated_config.general.theme == Theme.DARK

        # Check that other sections are unchanged
        assert updated_config.computation.numerical_precision == original_config.computation.numerical_precision

        # Check that original config is unchanged
        assert original_config.general.language == Language.ENGLISH

    def test_update_computation_section(self):
        """Test updating computation section."""
        original_config = create_default_config()

        updated_config = update_config(
            original_config,
            "computation",
            {"numerical_precision": 20, "max_iterations": 2000}
        )

        assert updated_config.computation.numerical_precision == 20
        assert updated_config.computation.max_iterations == 2000
        assert updated_config.general.language == original_config.general.language


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config(self):
        """Test validation of valid configuration."""
        config = create_default_config()
        is_valid, errors = validate_config(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_auto_save_interval(self):
        """Test validation with invalid auto-save interval."""
        config = ApplicationConfig(
            general=GeneralConfig(auto_save_interval=10)  # Too low
        )

        is_valid, errors = validate_config(config)
        assert is_valid is False
        assert any("Auto-save interval" in error for error in errors)

    def test_invalid_numerical_precision(self):
        """Test validation with invalid numerical precision."""
        config = ApplicationConfig(
            computation=ComputationConfig(numerical_precision=100)  # Too high
        )

        is_valid, errors = validate_config(config)
        assert is_valid is False
        assert any("Numerical precision" in error for error in errors)

    def test_multiple_validation_errors(self):
        """Test validation with multiple errors."""
        config = ApplicationConfig(
            general=GeneralConfig(auto_save_interval=10, recent_files_limit=0),
            computation=ComputationConfig(max_iterations=0)
        )

        is_valid, errors = validate_config(config)
        assert is_valid is False
        assert len(errors) >= 3  # At least 3 validation errors


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_default_config(self):
        """Test default config creation."""
        config = create_default_config()
        assert isinstance(config, ApplicationConfig)
        assert config.general.language == Language.ENGLISH
        assert config.computation.numerical_precision == 15

    def test_reset_to_defaults(self):
        """Test resetting to default configuration."""
        # This test would normally save to the user's config directory,
        # so we'll just test that it returns a default config
        config = reset_to_defaults()
        assert isinstance(config, ApplicationConfig)
        assert config.general.language == Language.ENGLISH