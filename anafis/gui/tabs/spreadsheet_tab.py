"""
Spreadsheet tab implementation with data bus integration.
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSlot

from ..shared.base_tab import DataBusEnabledTab, SpreadsheetTabMixin
from ..shared.data_transforms import (
    DataPayload, serialize_dataframe, deserialize_dataframe,
    transform_spreadsheet_to_fitting
)


logger = logging.getLogger(__name__)


class SpreadsheetTab(DataBusEnabledTab, SpreadsheetTabMixin):
    """Spreadsheet tab with data bus integration."""
    
    def __init__(self, tab_id: str, parent: Optional[QWidget] = None):
        super().__init__(tab_id=tab_id, tab_type="spreadsheet", parent=parent)
        
        self.current_data: Optional[pd.DataFrame] = None
        
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
        
        self.load_csv_button = QPushButton("Load CSV")
        header_layout.addWidget(self.load_csv_button)
        
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
        self.load_csv_button.clicked.connect(self.load_csv_file)
        self.export_to_fitting_button.clicked.connect(self.export_to_fitting)
        
        # Data bus connections
        self.data_received.connect(self._handle_data_received_ui)
        self.bus_error.connect(self._handle_bus_error_ui)

    @pyqtSlot()
    def load_csv_file(self) -> None:
        """Load CSV file into spreadsheet."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                df = pd.read_csv(file_path)
                self.set_data(df)
                self.status_label.setText(f"Loaded: {file_path}")
                
                # Publish raw dataframe data
                self.publish_data(
                    data_type="dataframe",
                    data=serialize_dataframe(df),
                    metadata={"source_file": file_path}
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV file: {e}")
                logger.error(f"Error loading CSV file {file_path}: {e}")

    @pyqtSlot()
    def export_to_fitting(self) -> None:
        """Export current data to fitting tabs."""
        if self.current_data is None or self.current_data.empty:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
        
        # Find numerical columns for fitting
        numerical_cols = [col for col in self.current_data.columns 
                         if pd.api.types.is_numeric_dtype(self.current_data[col])]
        
        if len(numerical_cols) < 2:
            QMessageBox.warning(
                self, "Warning", 
                "Need at least 2 numerical columns for fitting export"
            )
            return
        
        # Use first two numerical columns as x, y by default
        x_col, y_col = numerical_cols[0], numerical_cols[1]
        
        try:
            fitting_data = transform_spreadsheet_to_fitting(
                self.current_data,
                x_column=x_col,
                y_column=y_col
            )
            
            success = self.publish_data(
                data_type="fitting_data",
                data=fitting_data,
                metadata={
                    "source_tab": self.tab_id,
                    "transformation": "spreadsheet_to_fitting"
                }
            )
            
            if success:
                self.status_label.setText(
                    f"Exported fitting data: {x_col} vs {y_col}"
                )
            else:
                QMessageBox.warning(
                    self, "Warning", "Failed to publish fitting data"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to export to fitting: {e}"
            )
            logger.error(f"Error exporting to fitting: {e}")

    def set_data(self, data: pd.DataFrame) -> None:
        """Set the current data and update UI."""
        self.current_data = data
        self._update_table()
        self._update_info_label()
        self.export_to_fitting_button.setEnabled(not data.empty)

    def _update_table(self) -> None:
        """Update the data table widget."""
        if self.current_data is None or self.current_data.empty:
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            return
        
        # Set table dimensions
        self.data_table.setRowCount(len(self.current_data))
        self.data_table.setColumnCount(len(self.current_data.columns))
        
        # Set headers
        self.data_table.setHorizontalHeaderLabels(
            [str(col) for col in self.current_data.columns]
        )
        
        # Populate data (limit to first 1000 rows for performance)
        display_rows = min(len(self.current_data), 1000)
        for i in range(display_rows):
            for j, col in enumerate(self.current_data.columns):
                value = self.current_data.iloc[i, j]
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(i, j, item)
        
        # Add note if data was truncated
        if len(self.current_data) > 1000:
            self.status_label.setText(
                f"Showing first 1000 rows of {len(self.current_data)} total rows"
            )

    def _update_info_label(self) -> None:
        """Update the info label with data statistics."""
        if self.current_data is None or self.current_data.empty:
            self.info_label.setText("No data loaded")
        else:
            rows, cols = self.current_data.shape
            numerical_cols = sum(1 for col in self.current_data.columns 
                               if pd.api.types.is_numeric_dtype(self.current_data[col]))
            self.info_label.setText(
                f"Data: {rows} rows × {cols} columns ({numerical_cols} numerical)"
            )

    @pyqtSlot(dict)
    def _handle_data_received_ui(self, message: Dict[str, Any]) -> None:
        """Handle data received through UI (slot for signal)."""
        self.status_label.setText(
            f"Received {message['data_type']} from {message['source_tab_id']}"
        )

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
                df = deserialize_dataframe(message["data"])
                self.set_data(df)
                logger.info(f"Imported dataframe from {message['source_tab_id']}")
            
            elif data_type == "csv_import":
                # Handle CSV import requests
                file_path = message["data"].get("file_path")
                if file_path:
                    df = pd.read_csv(file_path)
                    self.set_data(df)
                    logger.info(f"Imported CSV {file_path} via data bus")
            
            elif data_type == "parameters":
                # Handle parameter updates (could affect data display)
                params = message["data"]
                logger.info(f"Received parameters from {message['source_tab_id']}: {params}")
            
        except Exception as e:
            logger.error(f"Error handling received data in spreadsheet tab: {e}")

    def get_exportable_data(self) -> Optional[Dict[str, Any]]:
        """Get data that can be exported to other tabs."""
        if self.current_data is None or self.current_data.empty:
            return None
        
        return serialize_dataframe(self.current_data)

    def get_state(self) -> Dict[str, Any]:
        """Get current state for persistence."""
        state = {
            "type": "spreadsheet",
            "tab_id": self.tab_id,
            "subscriptions": self.subscriptions
        }
        
        if self.current_data is not None:
            state["has_data"] = True
            state["data_shape"] = self.current_data.shape
        else:
            state["has_data"] = False
        
        return state
