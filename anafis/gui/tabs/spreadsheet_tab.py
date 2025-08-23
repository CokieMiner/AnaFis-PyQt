"""
Spreadsheet tab implementation with data bus integration.
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
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSlot

from anafis.gui.shared.base_tab import DataBusEnabledTab, SpreadsheetTabMixin
from anafis.gui.shared.data_transforms import (
    serialize_dataframe,
    deserialize_dataframe,
    transform_spreadsheet_to_fitting,
)
from anafis.gui.shared.import_dialog import ImportDialog
from anafis.core.data_structures import SpreadsheetState, DataPayload, SerializedDataFrame, TabState, MessageMetadata


logger = logging.getLogger(__name__)


def update_spreadsheet_data(state: SpreadsheetState, new_data: pd.DataFrame) -> SpreadsheetState:
    """Pure function to update the spreadsheet state with new data."""
    return state._replace(data=new_data)


class SpreadsheetTab(DataBusEnabledTab, SpreadsheetTabMixin):
    """Spreadsheet tab with data bus integration."""

    def __init__(self, tab_id: str, parent: Optional[QWidget] = None, tab_name: Optional[str] = None):
        super().__init__(tab_id=tab_id, tab_type="spreadsheet", parent=parent, tab_name=tab_name)

        self.state = SpreadsheetState()

        self._setup_ui()
        self._setup_connections()

        # Set up data bus subscriptions
        self.setup_default_subscriptions()
        self.finalize_initialization()

        logger.debug(f"Spreadsheet tab {tab_id} initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Header with controls
        header_layout = QHBoxLayout()

        self.info_label = QLabel("No data loaded")
        header_layout.addWidget(self.info_label)

        header_layout.addStretch()

        self.import_button = QPushButton("Import File")
        header_layout.addWidget(self.import_button)

        self.export_to_fitting_button = QPushButton("Export to Fitting")
        self.export_to_fitting_button.setEnabled(False)
        header_layout.addWidget(self.export_to_fitting_button)

        layout.addLayout(header_layout)

        # Data table
        self.data_table = QTableWidget()
        layout.addWidget(self.data_table)

        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        self.import_button.clicked.connect(self.import_file)
        self.export_to_fitting_button.clicked.connect(self.export_to_fitting)

        # Data bus connections
        self.data_received.connect(self._handle_data_received_ui)
        self.bus_error.connect(self._handle_bus_error_ui)

    @pyqtSlot()
    def import_file(self) -> None:
        """Open import dialog to load a file."""
        dialog = ImportDialog(self)
        if dialog.exec():
            df = dialog.get_data()
            if df is not None:
                self.state = update_spreadsheet_data(self.state, df)
                self._update_ui_from_state()
                self.status_label.setText(f"Loaded: {dialog.file_path}")

                # Publish raw dataframe data
                metadata_dict = {}
                if dialog.file_path is not None:
                    metadata_dict["source_file"] = dialog.file_path

                self.publish_data(
                    data_type="dataframe",
                    data=serialize_dataframe(df),
                    metadata=cast(MessageMetadata, metadata_dict),
                )

    @pyqtSlot()
    def export_to_fitting(self) -> None:
        """Export current data to fitting tabs."""
        if self.state.data is None or self.state.data.empty:
            QMessageBox.warning(self, "Warning", "No data to export")
            return

        # Find numerical columns for fitting
        numerical_cols = [col for col in self.state.data.columns if pd.api.types.is_numeric_dtype(self.state.data[col])]

        if len(numerical_cols) < 2:
            QMessageBox.warning(self, "Warning", "Need at least 2 numerical columns for fitting export")
            return

        # Use first two numerical columns as x, y by default
        x_col, y_col = numerical_cols[0], numerical_cols[1]

        try:
            fitting_data = transform_spreadsheet_to_fitting(self.state.data, x_column=x_col, y_column=y_col)

            success = self.publish_data(
                data_type="fitting_data",
                data=fitting_data,
                metadata={
                    "source_tab": self.tab_id,
                    "transformation": "spreadsheet_to_fitting",
                },
            )

            if success:
                self.status_label.setText(f"Exported fitting data: {x_col} vs {y_col}")
            else:
                QMessageBox.warning(self, "Warning", "Failed to publish fitting data")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export to fitting: {e}")
            logger.error(f"Error exporting to fitting: {e}")

    def _update_ui_from_state(self) -> None:
        """Update the UI from the current state."""
        self._update_table()
        self._update_info_label()
        self.export_to_fitting_button.setEnabled(self.state.data is not None and not self.state.data.empty)

    def _update_table(self) -> None:
        """Update the data table widget."""
        if self.state.data is None or self.state.data.empty:
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            return

        # Set table dimensions
        self.data_table.setRowCount(len(self.state.data))
        self.data_table.setColumnCount(len(self.state.data.columns))

        # Set headers
        self.data_table.setHorizontalHeaderLabels([str(col) for col in self.state.data.columns])

        # Populate data (limit to first 1000 rows for performance)
        display_rows = min(len(self.state.data), 1000)
        for i in range(display_rows):
            for j, col in enumerate(self.state.data.columns):
                value = self.state.data.iloc[i, j]
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(i, j, item)

        # Add note if data was truncated
        if len(self.state.data) > 1000:
            self.status_label.setText(f"Showing first 1000 rows of {len(self.state.data)} total rows")

    def _update_info_label(self) -> None:
        """Update the info label with data statistics."""
        if self.state.data is None or self.state.data.empty:
            self.info_label.setText("No data loaded")
        else:
            rows, cols = self.state.data.shape
            numerical_cols = sum(
                1 for col in self.state.data.columns if pd.api.types.is_numeric_dtype(self.state.data[col])
            )
            self.info_label.setText(f"Data: {rows} rows × {cols} columns ({numerical_cols} numerical)")

    @pyqtSlot(dict)
    def _handle_data_received_ui(self, message: DataPayload) -> None:
        """Handle data received through UI (slot for signal)."""
        self.status_label.setText(f"Received {message['data_type']} from {message['source_tab_id']}")

    @pyqtSlot(str)
    def _handle_bus_error_ui(self, error_message: str) -> None:
        """Handle data bus errors in UI (slot for signal)."""
        self.status_label.setText(f"Bus error: {error_message}")
        QMessageBox.warning(self, "Data Bus Error", error_message)

    def on_data_received(self, message: DataPayload) -> None:
        """Handle received data from other tabs."""
        data_type = message["data_type"]

        try:
            if data_type == "dataframe":
                # Import dataframe data
                raw_df_payload = message["data"]
                if isinstance(raw_df_payload, dict):
                    df = deserialize_dataframe(cast(SerializedDataFrame, raw_df_payload))
                    self.state = update_spreadsheet_data(self.state, df)
                    self._update_ui_from_state()
                    logger.info(f"Imported dataframe from {message['source_tab_id']}")
                else:
                    logger.warning(f"Received 'dataframe' with unexpected payload type: {type(raw_df_payload)}")

            elif data_type == "csv_import":
                # Handle CSV import requests
                raw_csv_payload = message["data"]
                if isinstance(raw_csv_payload, dict):
                    file_path = raw_csv_payload.get("file_path")
                    if isinstance(file_path, str):
                        # This part might need settings from the message
                        df = pd.read_csv(file_path)
                        self.state = update_spreadsheet_data(self.state, df)
                        self._update_ui_from_state()
                        logger.info(f"Imported CSV {file_path} via data bus")
                    else:
                        logger.warning(f"Received 'csv_import' with missing or invalid 'file_path': {type(file_path)}")
                else:
                    logger.warning(f"Received 'csv_import' with unexpected payload type: {type(raw_csv_payload)}")

            elif data_type == "parameters":
                # Handle parameter updates (could affect data display)
                params = message["data"]
                logger.info(f"Received parameters from {message['source_tab_id']}: {params}")

        except Exception as e:
            logger.error(f"Error handling received data in spreadsheet tab: {e}")

    def get_exportable_data(self) -> Optional[SerializedDataFrame]:
        """Get data that can be exported to other tabs."""
        if self.state.data is None or self.state.data.empty:
            return None

        return serialize_dataframe(self.state.data)

    def get_state(self) -> TabState:
        """Get current state for persistence."""
        state = super().get_state()

        # Add spreadsheet-specific state
        if self.state.data is not None:
            state["has_data"] = True
            state["data_shape"] = self.state.data.shape
        else:
            state["has_data"] = False

        return state
