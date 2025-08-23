"""
Core data structures for ANAFIS.
"""

from typing import NamedTuple, Dict, Optional, List, Union, TypedDict, Callable
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import pandas as pd
import networkx as nx

JSON_VALUE = Union[str, int, float, bool, None]


@dataclass(frozen=True)
class Parameter:
    """Represents a parameter for fitting."""

    name: str
    value: float
    vary: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def __post_init__(self) -> None:
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            raise ValueError("min_value cannot be greater than max_value")
        if self.min_value is not None and self.value < self.min_value:
            raise ValueError("value cannot be less than min_value")
        if self.max_value is not None and self.value > self.max_value:
            raise ValueError("value cannot be greater than max_value")


class MessageMetadata(TypedDict, total=False):
    source_file: str
    source_tab: str
    transformation: str
    model_type: str
    description: str


class FittingMethod(Enum):
    LEVENBERG_MARQUARDT = "lm"
    ODR = "odr"
    MCMC = "mcmc"


class FittingResults(TypedDict, total=False):
    type: str
    model_type: str
    coefficients: List[float]
    coefficients_uncertainties: List[float]
    equation: str
    r_squared: float
    rmse: float
    iterations_used: int
    converged: bool


class FittingState(NamedTuple):
    """
    Immutable state for the fitting tab.
    """

    source_data: Optional[pd.DataFrame] = None
    model_formula: str = ""
    method: FittingMethod = FittingMethod.LEVENBERG_MARQUARDT
    parameters: Dict[str, Parameter] = {}
    results: Optional[FittingResults] = None


class SpreadsheetState(NamedTuple):
    """
    Immutable state for the spreadsheet tab.
    """

    data: Optional[pd.DataFrame] = None
    formulas: Dict[str, str] = {}
    units: Dict[str, str] = {}
    dependencies: Optional[nx.DiGraph] = None


class ImportSettings(TypedDict, total=False):
    file_type: str
    delimiter: str
    sheet_name: str
    header: bool
    skiprows: int
    nrows: Optional[int]


class HandlerConfig(TypedDict, total=False):
    type: str
    level: int
    formatter: logging.Formatter
    path: Path


class LoggerConfig(TypedDict, total=False):
    name: str
    level: int
    handlers: List[HandlerConfig]
    log_directory: Path


class PendingPublication(TypedDict):
    data_type: str
    data: "TabData"
    metadata: Optional[MessageMetadata]


class BusStatistics(TypedDict):
    is_active: bool
    total_registered_tabs: int
    active_tabs: int
    total_messages_processed: int
    message_history_size: int
    active_filters: int
    total_subscriptions: int


class RegisteredTabs(TypedDict):
    tab_type: str
    is_active: bool
    message_count: int
    last_activity: Optional[str]
    subscriptions: List[str]


class DataPayload(TypedDict, total=False):
    source_tab_id: str
    source_tab_type: str
    data_type: str
    data: "TabData"
    metadata: MessageMetadata
    timestamp: str
    version: str


class SerializedDataFrame(TypedDict):
    type: str
    data: List[Dict[str, JSON_VALUE]]
    columns: List[str]
    dtypes: Dict[str, str]
    index: List[object]
    shape: tuple[int, ...]


class SerializedNumpyArray(TypedDict):
    type: str
    data: List[JSON_VALUE]
    dtype: str
    shape: tuple[int, ...]


class FittingData(TypedDict):
    type: str
    data: SerializedDataFrame
    source_columns: Dict[str, Optional[str]]
    original_shape: List[int]
    cleaned_shape: List[int]


class MonteCarloResults(TypedDict):
    type: str
    simulation_data: Union[SerializedDataFrame, pd.DataFrame]
    parameters: Dict[str, JSON_VALUE]


class TabState(TypedDict, total=False):
    type: str
    tab_id: str
    tab_name: Optional[str]
    detached: bool
    subscriptions: List[str]
    model_type: str
    max_iterations: int
    tolerance: float
    has_data: bool
    data_shape: tuple[int, int]
    has_results: bool


class FittingParameters(TypedDict, total=False):
    model_type: str
    max_iterations: int
    tolerance: float


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
    PORTUGUESE = "pt"
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
    floating_tool_shortcuts: Dict[str, str] = field(
        default_factory=lambda: {
            "uncertainty_calculator": "F9",
            "quick_solver": "Alt+S",
            "unit_converter": "Ctrl+U",
        }
    )
    plot_default_style: str = "seaborn-v0_8"
    plot_dpi: int = 100


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


class ConfigDict(TypedDict):
    general: Dict[str, JSON_VALUE]
    computation: Dict[str, JSON_VALUE]
    interface: Dict[str, JSON_VALUE]
    updates: Dict[str, JSON_VALUE]
    advanced: Dict[str, JSON_VALUE]
    config_version: str


class TabRegistration:
    """Information about a registered tab."""

    def __init__(self, tab_id: str, tab_type: str, callback: Optional[Callable] = None):
        self.tab_id = tab_id
        self.tab_type = tab_type
        self.callback = callback
        self.is_active = True
        self.message_count = 0
        self.last_activity: Optional[str] = None


TabData = Union[
    pd.DataFrame,
    Dict[str, JSON_VALUE],
    List[JSON_VALUE],
    str,
    float,
    int,
    FittingResults,
    FittingData,
    SerializedDataFrame,
    ApplicationConfig,
]


class DataSummary(TypedDict, total=False):
    type: str
    shape: List[int]
    columns: List[str]
    dtypes: Dict[str, str]
    memory_usage: int
