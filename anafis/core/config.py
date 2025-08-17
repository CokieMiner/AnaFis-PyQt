"""
Functional configuration management for ANAFIS.

This module provides pure functions for managing application configuration
using functional programming patterns and immutable data structures.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum


class Theme(Enum):
    """Application theme options."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class Language(Enum):
    """Supported languages."""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    JAPANESE = "ja"


class UpdateChannel(Enum):
    """Update channel options."""

    STABLE = "stable"
    BETA = "beta"
    DEVELOPMENT = "dev"


@dataclass(frozen=True)
class GeneralConfig:
    """General application configuration."""

    language: Language = Language.ENGLISH
    theme: Theme = Theme.SYSTEM
    startup_behavior: str = "restore_session"  # "restore_session", "home_only", "blank"
    auto_save_interval: int = 300  # seconds
    recent_files_limit: int = 10
    show_splash_screen: bool = True
    check_updates_on_startup: bool = True


@dataclass(frozen=True)
class ComputationConfig:
    """Computation and algorithm configuration."""

    default_fitting_method: str = "lm"  # Levenberg-Marquardt
    numerical_precision: int = 15  # decimal places
    max_iterations: int = 1000
    convergence_tolerance: float = 1e-8
    use_gpu_acceleration: bool = True
    gpu_device_id: Optional[int] = None
    parallel_processing: bool = True
    max_workers: Optional[int] = None  # None = auto-detect


@dataclass(frozen=True)
class InterfaceConfig:
    """User interface configuration."""

    tab_detach_enabled: bool = True
    tab_close_confirmation: bool = True
    show_tooltips: bool = True
    animation_enabled: bool = True
    status_bar_visible: bool = True
    toolbar_visible: bool = True
    floating_tool_shortcuts: Dict[str, str] = None
    plot_default_style: str = "seaborn-v0_8"
    plot_dpi: int = 100

    def __post_init__(self):
        """Set default shortcuts if not provided."""
        if self.floating_tool_shortcuts is None:
            object.__setattr__(
                self,
                "floating_tool_shortcuts",
                {
                    "uncertainty_calculator": "F9",
                    "quick_solver": "Alt+S",
                    "unit_converter": "Ctrl+U",
                },
            )


@dataclass(frozen=True)
class UpdateConfig:
    """Update system configuration."""

    auto_check_enabled: bool = True
    check_interval_hours: int = 24
    update_channel: UpdateChannel = UpdateChannel.STABLE
    auto_download: bool = False
    notify_beta_releases: bool = False
    github_api_token: Optional[str] = None  # For higher rate limits


@dataclass(frozen=True)
class AdvancedConfig:
    """Advanced configuration options."""

    debug_mode: bool = False
    log_level: str = "INFO"
    memory_limit_mb: Optional[int] = None
    cache_size_mb: int = 100
    enable_profiling: bool = False
    experimental_features: bool = False
    custom_plugin_paths: tuple = ()


class ApplicationConfig(NamedTuple):
    """
    Immutable application configuration container.

    This structure contains all configuration sections and provides
    a single source of truth for application settings.
    """

    general: GeneralConfig
    computation: ComputationConfig
    interface: InterfaceConfig
    updates: UpdateConfig
    advanced: AdvancedConfig
    config_version: str


def create_application_config(
    general=None,
    computation=None,
    interface=None,
    updates=None,
    advanced=None,
    config_version="1.0",
):
    """Create new ApplicationConfig with defaults."""
    if general is None:
        general = GeneralConfig()
    if computation is None:
        computation = ComputationConfig()
    if interface is None:
        interface = InterfaceConfig()
    if updates is None:
        updates = UpdateConfig()
    if advanced is None:
        advanced = AdvancedConfig()

    return ApplicationConfig(
        general, computation, interface, updates, advanced, config_version
    )


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


def config_to_dict(config: ApplicationConfig) -> Dict[str, Any]:
    """
    Convert ApplicationConfig to a dictionary for serialization.

    Args:
        config: ApplicationConfig instance

    Returns:
        Dictionary representation of the configuration
    """

    def enum_serializer(obj):
        """Convert enums to their values."""
        if isinstance(obj, Enum):
            return obj.value
        return obj

    result = {}

    # Convert each section to dict
    for field_name in config._fields:
        if field_name == "config_version":
            result[field_name] = config.config_version
        else:
            section = getattr(config, field_name)
            section_dict = asdict(section)

            # Convert enums to values
            for key, value in section_dict.items():
                if isinstance(value, Enum):
                    section_dict[key] = value.value
                elif isinstance(value, dict):
                    # Handle nested dictionaries
                    for nested_key, nested_value in value.items():
                        if isinstance(nested_value, Enum):
                            value[nested_key] = nested_value.value

            result[field_name] = section_dict

    return result


def dict_to_config(config_dict: Dict[str, Any]) -> ApplicationConfig:
    """
    Convert a dictionary to ApplicationConfig.

    Args:
        config_dict: Dictionary representation of configuration

    Returns:
        ApplicationConfig instance
    """

    def convert_enums(
        section_name: str, section_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert string values back to enums where appropriate."""
        converted = section_dict.copy()

        # Define enum mappings for each section
        enum_mappings = {
            "general": {"language": Language, "theme": Theme},
            "updates": {"update_channel": UpdateChannel},
        }

        if section_name in enum_mappings:
            for field, enum_class in enum_mappings[section_name].items():
                if field in converted:
                    try:
                        converted[field] = enum_class(converted[field])
                    except ValueError:
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
    general = GeneralConfig(**general_dict)
    computation = ComputationConfig(**computation_dict)
    interface = InterfaceConfig(**interface_dict)
    updates = UpdateConfig(**updates_dict)
    advanced = AdvancedConfig(**advanced_dict)

    config_version = config_dict.get("config_version", "1.0")

    return create_application_config(
        general, computation, interface, updates, advanced, config_version
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
    current_config: ApplicationConfig, section: str, updates: Dict[str, Any]
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
    section_dict.update(updates)

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
    config_dict = current_config._asdict()
    config_dict[section] = new_section

    return create_application_config(**config_dict)


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
    if (
        config.computation.numerical_precision < 1
        or config.computation.numerical_precision > 50
    ):
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
