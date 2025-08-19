import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QWidget,
    QLabel,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
)
from PyQt6.QtGui import QIcon

from anafis.core.config import ApplicationConfig, save_config
from anafis.core.data_structures import (
    Language,
    Theme,
    GeneralConfig,
    ComputationConfig,
)

logger = logging.getLogger(__name__)


class ConfigDialog(QDialog):
    def __init__(self, current_config: ApplicationConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ANAFIS Configuration")
        self.setWindowIcon(QIcon(":/icons/anafis.png"))  # Assuming an icon exists

        self._config = current_config
        self._new_config = current_config  # This will hold changes

        self._setup_ui()
        self._load_config_to_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget(self)
        main_layout.addWidget(self.tab_widget)

        # General Tab
        self._general_tab = QWidget()
        self._setup_general_tab_ui()
        self.tab_widget.addTab(self._general_tab, "General")

        # Computation Tab
        self._computation_tab = QWidget()
        self._setup_computation_tab_ui()
        self.tab_widget.addTab(self._computation_tab, "Computation")

        # Add more tabs as needed (Interface, Updates, Advanced)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def _setup_general_tab_ui(self) -> None:
        layout = QVBoxLayout(self._general_tab)

        # Language
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        for lang in Language:
            self.lang_combo.addItem(lang.name.capitalize(), lang.value)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # Theme
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        for theme in Theme:
            self.theme_combo.addItem(theme.name.capitalize(), theme.value)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # Auto-save interval
        auto_save_layout = QHBoxLayout()
        auto_save_layout.addWidget(QLabel("Auto-save Interval (seconds):"))
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(30, 3600)
        self.auto_save_spin.setSingleStep(30)
        auto_save_layout.addWidget(self.auto_save_spin)
        auto_save_layout.addStretch()
        layout.addLayout(auto_save_layout)

        layout.addStretch()

    def _setup_computation_tab_ui(self) -> None:
        layout = QVBoxLayout(self._computation_tab)

        # Numerical Precision
        precision_layout = QHBoxLayout()
        precision_layout.addWidget(QLabel("Numerical Precision:"))
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(1, 50)
        precision_layout.addWidget(self.precision_spin)
        precision_layout.addStretch()
        layout.addLayout(precision_layout)

        # Max Iterations
        max_iter_layout = QHBoxLayout()
        max_iter_layout.addWidget(QLabel("Max Iterations:"))
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(1, 10000)
        max_iter_layout.addWidget(self.max_iter_spin)
        max_iter_layout.addStretch()
        layout.addLayout(max_iter_layout)

        # Convergence Tolerance
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("Convergence Tolerance:"))
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setDecimals(10)
        self.tolerance_spin.setRange(1e-12, 1.0)
        self.tolerance_spin.setSingleStep(1e-6)
        tolerance_layout.addWidget(self.tolerance_spin)
        tolerance_layout.addStretch()
        layout.addLayout(tolerance_layout)

        layout.addStretch()

    def _load_config_to_ui(self) -> None:
        # General
        self.lang_combo.setCurrentIndex(self.lang_combo.findData(self._config.general.language.value))
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(self._config.general.theme.value))
        self.auto_save_spin.setValue(self._config.general.auto_save_interval)

        # Computation
        self.precision_spin.setValue(self._config.computation.numerical_precision)
        self.max_iter_spin.setValue(self._config.computation.max_iterations)
        self.tolerance_spin.setValue(self._config.computation.convergence_tolerance)

    def _save_ui_to_config(self) -> None:
        # Create new config objects from UI values
        new_general = GeneralConfig(
            language=Language(self.lang_combo.currentData()),
            theme=Theme(self.theme_combo.currentData()),
            auto_save_interval=self.auto_save_spin.value(),
            # Copy other fields from original config
            startup_behavior=self._config.general.startup_behavior,
            recent_files_limit=self._config.general.recent_files_limit,
            show_splash_screen=self._config.general.show_splash_screen,
            check_updates_on_startup=self._config.general.check_updates_on_startup,
        )
        new_computation = ComputationConfig(
            numerical_precision=self.precision_spin.value(),
            max_iterations=self.max_iter_spin.value(),
            convergence_tolerance=self.tolerance_spin.value(),
            # Copy other fields from original config
            default_fitting_method=self._config.computation.default_fitting_method,
            use_gpu_acceleration=self._config.computation.use_gpu_acceleration,
            gpu_device_id=self._config.computation.gpu_device_id,
            parallel_processing=self._config.computation.parallel_processing,
            max_workers=self._config.computation.max_workers,
        )

        # Create the new ApplicationConfig
        self._new_config = ApplicationConfig(
            general=new_general,
            computation=new_computation,
            interface=self._config.interface,  # Keep original for now
            updates=self._config.updates,  # Keep original for now
            advanced=self._config.advanced,  # Keep original for now
            config_version=self._config.config_version,
        )

    def accept(self) -> None:
        self._save_ui_to_config()
        if save_config(self._new_config):
            super().accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save configuration.")

    def get_new_config(self) -> ApplicationConfig:
        return self._new_config
