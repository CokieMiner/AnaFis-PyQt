"""
Functional configuration management for ANAFIS.

This module provides pure functions for managing application configuration
using functional programming patterns and immutable data structures.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional, cast, Literal, Tuple, Union
from dataclasses import asdict
from enum import Enum
from anafis.core.data_structures import (
    Theme,
    ApplicationConfig,
    ComputationConfig,
    GeneralConfig,
    InterfaceConfig,
    UpdateConfig,
    AdvancedConfig,
    Language,
    UpdateChannel,
    ConfigDict,
    JSON_VALUE,
)


def create_application_config(
    general: GeneralConfig = GeneralConfig(),
    computation: ComputationConfig = ComputationConfig(),
    interface: InterfaceConfig = InterfaceConfig(),
    updates: UpdateConfig = UpdateConfig(),
    advanced: AdvancedConfig = AdvancedConfig(),
    config_version: str = "1.0",
) -> ApplicationConfig:
    """Create new ApplicationConfig with defaults."""
    return ApplicationConfig(general, computation, interface, updates, advanced, config_version)


def get_default_config_directory() -> Path:
    """
    Get the default directory for configuration files.

    Returns:
        Path to the default configuration directory
    """
    if sys.platform == "win32":
        # Windows: Use AppData/Roaming
        import os

        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        return Path(app_data) / "ANAFIS"
    elif sys.platform == "darwin":
        # macOS: Use ~/Library/Application Support
        return Path.home() / "Library" / "Application Support" / "ANAFIS"
    else:
        # Linux/Unix: Use ~/.config
        return Path.home() / ".config" / "anafis"


def get_config_file_path(config_dir: Optional[Path] = None) -> Path:
    """
    Get the path to the main configuration file.

    Args:
        config_dir: Custom configuration directory, uses default if None

    Returns:
        Path to the configuration file
    """
    if config_dir is None:
        config_dir = get_default_config_directory()

    return config_dir / "config.json"


def create_default_config() -> ApplicationConfig:
    """
    Create a default application configuration.

    Returns:
        ApplicationConfig with default values
    """
    return create_application_config()


def config_to_dict(config: ApplicationConfig) -> ConfigDict:
    """
    Convert ApplicationConfig to a dictionary for serialization.

    Args:
        config: ApplicationConfig instance

    Returns:
        Dictionary representation of the configuration
    """
    config_dict: ConfigDict = {
        "general": {},
        "computation": {},
        "interface": {},
        "updates": {},
        "advanced": {},
        "config_version": config.config_version,
    }

    # Process each section to convert Enums to their values
    for section_name in ConfigDict.__annotations__.keys():
        if section_name == "config_version":
            continue
        section_data = getattr(config, section_name)
        section_dict = asdict(section_data)  # Convert dataclass to dict

        for key, value in section_dict.items():
            if isinstance(value, Enum):
                enum_str_value: str = value.value  # Explicitly type as str
                section_dict[key] = enum_str_value
            elif isinstance(value, dict):
                # Handle nested dictionaries (like floating_tool_shortcuts)
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, Enum):
                        nested_enum_str_value: str = nested_value.value  # Explicitly type as str
                        value[nested_key] = nested_enum_str_value
        config_dict[cast(Literal["general", "computation", "interface", "updates", "advanced"], section_name)] = (
            section_dict
        )

    return config_dict


def dict_to_config(config_dict: ConfigDict) -> ApplicationConfig:
    """
    Convert a dictionary to ApplicationConfig.

    Args:
        config_dict: Dictionary representation of configuration

    Returns:
        ApplicationConfig instance
    """

    def convert_enums(section_name: str, section_dict: Dict[str, JSON_VALUE]) -> Dict[str, Union[JSON_VALUE, Enum]]:
        """Convert string values back to enums where appropriate."""
        converted: Dict[str, Union[JSON_VALUE, Enum]] = {k: v for k, v in section_dict.items()}

        # Define enum mappings for each section
        enum_mappings = {
            "general": {"language": Language, "theme": Theme},
            "updates": {"update_channel": UpdateChannel},
        }

        if section_name in enum_mappings:
            for field, enum_class in cast(Dict[str, type[Enum]], enum_mappings[section_name]).items():
                if field in converted:
                    try:
                        value = converted[field]
                        if isinstance(value, (str, int, float)):
                            converted[field] = enum_class(value)
                    except (ValueError, TypeError):
                        # Keep original value if enum conversion fails
                        pass

        return converted

    # Extract sections with enum conversion
    general_dict = convert_enums("general", config_dict.get("general", {}))
    computation_dict = config_dict.get("computation", {})
    interface_dict = config_dict.get("interface", {})
    updates_dict = convert_enums("updates", config_dict.get("updates", {}))
    advanced_dict = config_dict.get("advanced", {})

    # Create section instances
    general = _dict_to_general_config(general_dict)
    computation = _dict_to_computation_config(computation_dict)
    interface = _dict_to_interface_config(interface_dict)
    updates = _dict_to_update_config(updates_dict)
    advanced = _dict_to_advanced_config(advanced_dict)

    config_version = config_dict.get("config_version", "1.0")

    return create_application_config(general, computation, interface, updates, advanced, config_version)


def _dict_to_general_config(data: Dict[str, Union[JSON_VALUE, Enum]]) -> GeneralConfig:
    return GeneralConfig(
        language=Language(data.get("language", Language.ENGLISH.value)),
        theme=Theme(data.get("theme", Theme.SYSTEM.value)),
        startup_behavior=cast(str, data.get("startup_behavior", "restore_session")),
        auto_save_interval=cast(int, data.get("auto_save_interval", 300)),
        recent_files_limit=cast(int, data.get("recent_files_limit", 10)),
        show_splash_screen=cast(bool, data.get("show_splash_screen", True)),
        check_updates_on_startup=cast(bool, data.get("check_updates_on_startup", True)),
    )


def _dict_to_computation_config(data: Dict[str, JSON_VALUE]) -> ComputationConfig:
    return ComputationConfig(
        default_fitting_method=cast(str, data.get("default_fitting_method", "lm")),
        numerical_precision=cast(int, data.get("numerical_precision", 15)),
        max_iterations=cast(int, data.get("max_iterations", 1000)),
        convergence_tolerance=cast(float, data.get("convergence_tolerance", 1e-8)),
        use_gpu_acceleration=cast(bool, data.get("use_gpu_acceleration", True)),
        gpu_device_id=cast(Optional[int], data.get("gpu_device_id", None)),
        parallel_processing=cast(bool, data.get("parallel_processing", True)),
        max_workers=cast(Optional[int], data.get("max_workers", None)),
    )


def _dict_to_interface_config(data: Dict[str, JSON_VALUE]) -> InterfaceConfig:
    return InterfaceConfig(
        tab_detach_enabled=cast(bool, data.get("tab_detach_enabled", True)),
        tab_close_confirmation=cast(bool, data.get("tab_close_confirmation", True)),
        show_tooltips=cast(bool, data.get("show_tooltips", True)),
        animation_enabled=cast(bool, data.get("animation_enabled", True)),
        status_bar_visible=cast(bool, data.get("status_bar_visible", True)),
        toolbar_visible=cast(bool, data.get("toolbar_visible", True)),
        floating_tool_shortcuts=cast(Dict[str, str], data.get("floating_tool_shortcuts", {})),
        plot_default_style=cast(str, data.get("plot_default_style", "seaborn-v0_8")),
        plot_dpi=cast(int, data.get("plot_dpi", 100)),
    )


def _dict_to_update_config(data: Dict[str, Union[JSON_VALUE, Enum]]) -> UpdateConfig:
    return UpdateConfig(
        auto_check_enabled=cast(bool, data.get("auto_check_enabled", True)),
        check_interval_hours=cast(int, data.get("check_interval_hours", 24)),
        update_channel=UpdateChannel(data.get("update_channel", UpdateChannel.STABLE.value)),
        auto_download=cast(bool, data.get("auto_download", False)),
        notify_beta_releases=cast(bool, data.get("notify_beta_releases", False)),
        github_api_token=cast(Optional[str], data.get("github_api_token", None)),
    )


def _dict_to_advanced_config(data: Dict[str, JSON_VALUE]) -> AdvancedConfig:
    return AdvancedConfig(
        debug_mode=cast(bool, data.get("debug_mode", False)),
        log_level=cast(str, data.get("log_level", "INFO")),
        memory_limit_mb=cast(Optional[int], data.get("memory_limit_mb", None)),
        cache_size_mb=cast(int, data.get("cache_size_mb", 100)),
        enable_profiling=cast(bool, data.get("enable_profiling", False)),
        experimental_features=cast(bool, data.get("experimental_features", False)),
        custom_plugin_paths=cast(Tuple[str, ...], data.get("custom_plugin_paths", ())),
    )


def save_config(config: ApplicationConfig, config_file: Optional[Path] = None) -> bool:
    """
    Save configuration to file.

    Args:
        config: ApplicationConfig to save
        config_file: Path to config file, uses default if None

    Returns:
        True if successful, False otherwise
    """
    if config_file is None:
        config_file = get_config_file_path()

    try:
        # Ensure config directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary and save
        config_dict = config_to_dict(config)

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        # In a real application, this would use the logging system
        print(f"Error saving configuration: {e}")
        return False


def load_config(config_file: Optional[Path] = None) -> ApplicationConfig:
    """
    Load configuration from file.

    Args:
        config_file: Path to config file, uses default if None

    Returns:
        ApplicationConfig instance (default config if file doesn't exist)
    """
    if config_file is None:
        config_file = get_config_file_path()

    # Return default config if file doesn't exist
    if not config_file.exists():
        return create_default_config()

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        return dict_to_config(config_dict)

    except Exception as e:
        # In a real application, this would use the logging system
        print(f"Error loading configuration: {e}")
        return create_default_config()


def update_config(
    current_config: ApplicationConfig, section: str, updates_dict: Dict[str, JSON_VALUE]
) -> ApplicationConfig:
    """
    Create a new configuration with updated values in a specific section.

    Args:
        current_config: Current ApplicationConfig
        section: Section name to update ('general', 'computation', etc.)
        updates: Dictionary of field updates

    Returns:
        New ApplicationConfig with updates applied
    """
    # Get current section
    current_section = getattr(current_config, section)

    # Convert to dict, apply updates, and create new section
    section_dict = asdict(current_section)
    section_dict.update(updates_dict)

    # Create new section instance
    section_classes = {
        "general": GeneralConfig,
        "computation": ComputationConfig,
        "interface": InterfaceConfig,
        "updates": UpdateConfig,
        "advanced": AdvancedConfig,
    }

    new_section = section_classes[section](**section_dict)

    # Create new config with updated section
    general = current_config.general
    computation = current_config.computation
    interface = current_config.interface
    updates = current_config.updates
    advanced = current_config.advanced
    config_version = current_config.config_version

    # Apply the updated section
    if section == "general":
        general = new_section
    elif section == "computation":
        computation = new_section
    elif section == "interface":
        interface = new_section
    elif section == "updates":
        updates = new_section
    elif section == "advanced":
        advanced = new_section

    return create_application_config(
        general=general,
        computation=computation,
        interface=interface,
        updates=updates,
        advanced=advanced,
        config_version=config_version,
    )


def validate_config(config: ApplicationConfig) -> tuple[bool, list[str]]:
    """
    Validate configuration values.

    Args:
        config: ApplicationConfig to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Validate general config
    if config.general.auto_save_interval < 30:
        errors.append("Auto-save interval must be at least 30 seconds")

    if config.general.recent_files_limit < 1:
        errors.append("Recent files limit must be at least 1")

    # Validate computation config
    if config.computation.numerical_precision < 1 or config.computation.numerical_precision > 50:
        errors.append("Numerical precision must be between 1 and 50")

    if config.computation.max_iterations < 1:
        errors.append("Max iterations must be at least 1")

    if config.computation.convergence_tolerance <= 0:
        errors.append("Convergence tolerance must be positive")

    # Validate interface config
    if config.interface.plot_dpi < 50 or config.interface.plot_dpi > 300:
        errors.append("Plot DPI must be between 50 and 300")

    # Validate update config
    if config.updates.check_interval_hours < 1:
        errors.append("Update check interval must be at least 1 hour")

    # Validate advanced config
    if config.advanced.cache_size_mb < 10:
        errors.append("Cache size must be at least 10 MB")

    return len(errors) == 0, errors


# Convenience functions for common operations


def get_user_config() -> ApplicationConfig:
    """Load user configuration from the default location."""
    return load_config()


def save_user_config(config: ApplicationConfig) -> bool:
    """Save user configuration to the default location."""
    return save_config(config)


def reset_to_defaults() -> ApplicationConfig:
    """Create and save a default configuration."""
    default_config = create_default_config()
    save_user_config(default_config)
    return default_config
