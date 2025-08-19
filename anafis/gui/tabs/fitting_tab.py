"""
Fitting tab implementation with data bus integration.
"""

import logging
from typing import Optional, cast
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QGroupBox,
)
from PyQt6.QtCore import pyqtSlot

from anafis.gui.shared.base_tab import DataBusEnabledTab, FittingTabMixin
from anafis.gui.shared.data_transforms import deserialize_dataframe
from anafis.core.data_structures import (
    TabState,
    DataPayload,
    FittingParameters,
    FittingResults,
    FittingData,
    SerializedDataFrame,
)
from anafis.core.fitting_logic import perform_fitting


logger = logging.getLogger(__name__)


class FittingTab(DataBusEnabledTab, FittingTabMixin):
    """Fitting tab with data bus integration."""

    def __init__(self, tab_id: str, parent: Optional[QWidget] = None, tab_name: Optional[str] = None):
        super().__init__(tab_id=tab_id, tab_type="fitting", parent=parent, tab_name=tab_name)

        self.current_data: Optional[pd.DataFrame] = None
        self.fitting_results: Optional[FittingResults] = None

        self._setup_ui()
        self._setup_connections()

        # Set up data bus subscriptions
        self.setup_default_subscriptions()
        self.finalize_initialization()

        logger.debug(f"Fitting tab {tab_id} initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Status header
        self.status_label = QLabel("Waiting for data...")
        layout.addWidget(self.status_label)

        # Data info group
        data_group = QGroupBox("Data Information")
        data_layout = QVBoxLayout(data_group)

        self.data_info_label = QLabel("No data loaded")
        data_layout.addWidget(self.data_info_label)

        layout.addWidget(data_group)

        # Fitting parameters group
        params_group = QGroupBox("Fitting Parameters")
        params_layout = QVBoxLayout(params_group)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Linear", "Quadratic", "Exponential", "Power"])
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        params_layout.addLayout(model_layout)

        # Max iterations
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("Max Iterations:"))
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(10, 10000)
        self.max_iter_spin.setValue(1000)
        iter_layout.addWidget(self.max_iter_spin)
        iter_layout.addStretch()
        params_layout.addLayout(iter_layout)

        # Tolerance
        tol_layout = QHBoxLayout()
        tol_layout.addWidget(QLabel("Tolerance:"))
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setDecimals(6)
        self.tolerance_spin.setRange(1e-10, 1e-2)
        self.tolerance_spin.setValue(1e-6)
        self.tolerance_spin.setSingleStep(1e-6)
        tol_layout.addWidget(self.tolerance_spin)
        tol_layout.addStretch()
        params_layout.addLayout(tol_layout)

        layout.addWidget(params_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.fit_button = QPushButton("Run Fitting")
        self.fit_button.setEnabled(False)
        button_layout.addWidget(self.fit_button)

        self.export_results_button = QPushButton("Export Results")
        self.export_results_button.setEnabled(False)
        button_layout.addWidget(self.export_results_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Results display
        results_group = QGroupBox("Fitting Results")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)

        layout.addWidget(results_group)

        layout.addStretch()

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        self.fit_button.clicked.connect(self.run_fitting)
        self.export_results_button.clicked.connect(self.export_results)

        # Data bus connections
        self.data_received.connect(self._handle_data_received_ui)
        self.bus_error.connect(self._handle_bus_error_ui)

    @pyqtSlot()
    def run_fitting(self) -> None:
        """Run curve fitting on current data."""
        if self.current_data is None or self.current_data.empty:
            self.results_text.setText("Error: No data available for fitting")
            return

        try:
            model_type = self.model_combo.currentText().lower()
            max_iter = self.max_iter_spin.value()
            tolerance = self.tolerance_spin.value()

            # Call the pure fitting function from the core logic
            self.fitting_results = perform_fitting(
                data=self.current_data,
                model_type=model_type,
                max_iterations=max_iter,
                tolerance=tolerance,
            )

            # Display results
            results_text = f"""Fitting Results:

Model: {model_type.title()}
Equation: {self.fitting_results['equation']}
R² = {self.fitting_results['r_squared']:.4f}
RMSE = {self.fitting_results['rmse']:.4f}
Iterations: {self.fitting_results['iterations_used']}
Converged: {self.fitting_results['converged']}

Parameters used:
- Max iterations: {max_iter}
- Tolerance: {tolerance:.2e}
            """

            self.results_text.setText(results_text)
            self.export_results_button.setEnabled(True)
            self.status_label.setText("Fitting completed successfully")

            logger.info(f"Fitting completed in tab {self.tab_id}: {model_type} model")

        except Exception as e:
            error_msg = f"Error during fitting: {e}"
            self.results_text.setText(error_msg)
            logger.error(f"Fitting error in tab {self.tab_id}: {e}")

    @pyqtSlot()
    def export_results(self) -> None:
        """Export fitting results to other tabs."""
        if not self.fitting_results:
            return

        success = self.publish_data(
            data_type="fitting_results",
            data=self.fitting_results,
            metadata={
                "source_tab": self.tab_id,
                "model_type": self.fitting_results["model_type"],
            },
        )

        if success:
            self.status_label.setText("Results exported to data bus")
            logger.info(f"Fitting results exported from tab {self.tab_id}")
        else:
            self.status_label.setText("Failed to export results")

    def set_data(self, data: pd.DataFrame) -> None:
        """Set the current data for fitting."""
        self.current_data = data
        self._update_data_info()
        self.fit_button.setEnabled(not data.empty)

        # Clear previous results
        self.fitting_results = None
        self.results_text.clear()
        self.export_results_button.setEnabled(False)

    def _update_data_info(self) -> None:
        """Update the data information display."""
        if self.current_data is None or self.current_data.empty:
            self.data_info_label.setText("No data loaded")
        else:
            rows, cols = self.current_data.shape
            info = f"Data points: {rows}\nColumns: {', '.join(self.current_data.columns)}"
            self.data_info_label.setText(info)

    @pyqtSlot(DataPayload)
    def _handle_data_received_ui(self, message: DataPayload) -> None:
        """Handle data received through UI (slot for signal)."""
        self.status_label.setText(f"Received {message['data_type']} from {message['source_tab_id']}")

    @pyqtSlot(str)
    def _handle_bus_error_ui(self, error_message: str) -> None:
        """Handle data bus errors in UI (slot for signal)."""
        self.status_label.setText(f"Bus error: {error_message}")

    def on_data_received(self, message: DataPayload) -> None:
        """Handle received data from other tabs."""
        data_type = message["data_type"]
        source_tab = message["source_tab_id"]

        try:
            if data_type == "fitting_data":
                # Receive prepared fitting data
                raw_data = message["data"]
                if isinstance(raw_data, dict) and "data" in raw_data:
                    fitting_data_payload = cast(FittingData, raw_data)
                    df = deserialize_dataframe(fitting_data_payload["data"])
                    self.set_data(df)
                    self.status_label.setText(f"Received fitting data from {source_tab}")
                    logger.info(f"Received fitting data in tab {self.tab_id} from {source_tab}")
                else:
                    logger.warning(f"Received 'fitting_data' with unexpected payload type: {type(raw_data)}")

            elif data_type == "dataframe":
                # Receive raw dataframe
                raw_df_payload = message["data"]
                if isinstance(raw_df_payload, dict):
                    df = deserialize_dataframe(cast(SerializedDataFrame, raw_df_payload))
                    self.set_data(df)
                    self.status_label.setText(f"Received dataframe from {source_tab}")
                    logger.info(f"Received dataframe in tab {self.tab_id} from {source_tab}")
                else:
                    logger.warning(f"Received 'dataframe' with unexpected payload type: {type(raw_df_payload)}")

            elif data_type == "parameters":
                # Receive fitting parameters
                raw_params_payload = message["data"]
                if isinstance(raw_params_payload, dict):
                    self._apply_parameters(cast(FittingParameters, raw_params_payload))
                    logger.info(f"Applied parameters in tab {self.tab_id} from {source_tab}")
                else:
                    logger.warning(f"Received 'parameters' with unexpected payload type: {type(raw_params_payload)}")

        except Exception as e:
            logger.error(f"Error handling received data in fitting tab {self.tab_id}: {e}")

    def _apply_parameters(self, params: FittingParameters) -> None:
        """Apply received parameters to fitting settings."""
        try:
            if "model_type" in params:
                model_items = [self.model_combo.itemText(i) for i in range(self.model_combo.count())]
                model_type = params["model_type"].title()
                if model_type in model_items:
                    self.model_combo.setCurrentText(model_type)

            if "max_iterations" in params:
                max_iter = int(params["max_iterations"])
                if self.max_iter_spin.minimum() <= max_iter <= self.max_iter_spin.maximum():
                    self.max_iter_spin.setValue(max_iter)

            if "tolerance" in params:
                tolerance = float(params["tolerance"])
                if self.tolerance_spin.minimum() <= tolerance <= self.tolerance_spin.maximum():
                    self.tolerance_spin.setValue(tolerance)

            self.status_label.setText("Parameters updated")

        except (ValueError, TypeError) as e:
            logger.warning(f"Error applying parameters in fitting tab: {e}")

    def get_exportable_data(self) -> Optional[FittingResults]:
        """Get data that can be exported to other tabs."""
        return self.fitting_results

    def get_state(self) -> TabState:
        """Get current state for persistence."""
        state = super().get_state()

        # Add fitting-specific state
        state["model_type"] = self.model_combo.currentText()
        state["max_iterations"] = self.max_iter_spin.value()
        state["tolerance"] = self.tolerance_spin.value()

        if self.current_data is not None:
            state["has_data"] = True
            state["data_shape"] = self.current_data.shape
        else:
            state["has_data"] = False

        if self.fitting_results:
            state["has_results"] = True
        else:
            state["has_results"] = False

        return state
