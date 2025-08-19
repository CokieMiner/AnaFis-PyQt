from typing import Optional, cast
import pandas as pd

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QWidget,
)
from PyQt6.QtCore import Qt

from anafis.core.data.io import load_dataframe
from anafis.core.data_structures import ImportSettings


class ImportDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import Data from File")
        self.setMinimumSize(800, 600)

        self.file_path: Optional[str] = None
        self.dataframe: Optional[pd.DataFrame] = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # File Path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("File Path:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)
        self.browse_button = QPushButton("Browse...")
        path_layout.addWidget(self.browse_button)
        layout.addLayout(path_layout)

        # Import Settings
        settings_group = QGroupBox("Import Settings")
        settings_layout = QVBoxLayout(settings_group)

        # File Type
        ft_layout = QHBoxLayout()
        ft_layout.addWidget(QLabel("File Type:"))
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["Autodetect", "CSV", "TXT", "Excel"])
        ft_layout.addWidget(self.file_type_combo)
        ft_layout.addStretch()
        settings_layout.addLayout(ft_layout)

        # Delimiter
        del_layout = QHBoxLayout()
        del_layout.addWidget(QLabel("Delimiter:"))
        self.delimiter_edit = QLineEdit(",")
        self.delimiter_edit.setFixedWidth(50)
        del_layout.addWidget(self.delimiter_edit)
        del_layout.addStretch()
        settings_layout.addLayout(del_layout)

        # Sheet Name
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("Sheet Name:"))
        self.sheet_name_edit = QLineEdit("Sheet1")
        sheet_layout.addWidget(self.sheet_name_edit)
        sheet_layout.addStretch()
        settings_layout.addLayout(sheet_layout)

        self.header_checkbox = QCheckBox("First row as header")
        self.header_checkbox.setChecked(True)
        settings_layout.addWidget(self.header_checkbox)

        # Start Row/Col
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start at row:"))
        self.start_row_spin = QSpinBox()
        self.start_row_spin.setRange(1, 1000000)
        start_layout.addWidget(self.start_row_spin)
        start_layout.addWidget(QLabel("Start at column:"))
        self.start_col_spin = QSpinBox()
        self.start_col_spin.setRange(1, 1000000)
        start_layout.addWidget(self.start_col_spin)
        start_layout.addStretch()
        settings_layout.addLayout(start_layout)

        layout.addWidget(settings_group)

        # Data Preview
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_table = QTableWidget()
        preview_layout.addWidget(self.preview_table)
        layout.addWidget(preview_group)

        # Bottom Buttons
        button_layout = QHBoxLayout()
        self.help_button = QPushButton("Help")
        button_layout.addWidget(self.help_button, 0, Qt.AlignmentFlag.AlignLeft)
        button_layout.addStretch()
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_button)
        self.import_button = QPushButton("Import")
        self.import_button.setDefault(True)
        button_layout.addWidget(self.import_button)
        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        self.browse_button.clicked.connect(self._browse_file)
        self.import_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Update preview when settings change
        self.file_type_combo.currentIndexChanged.connect(self._update_preview)
        self.delimiter_edit.textChanged.connect(self._update_preview)
        self.sheet_name_edit.textChanged.connect(self._update_preview)
        self.header_checkbox.stateChanged.connect(self._update_preview)
        self.start_row_spin.valueChanged.connect(self._update_preview)
        self.start_col_spin.valueChanged.connect(self._update_preview)

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import File",
            "",
            "All Files (*);;CSV Files (*.csv);;Text Files (*.txt);;Excel Files (*.xlsx *.xls)",
        )
        if file_path:
            self.file_path = file_path
            self.path_edit.setText(file_path)
            self._update_preview()

    def _get_current_settings(self) -> ImportSettings:
        return cast(
            ImportSettings,
            {
                "file_type": self.file_type_combo.currentText().lower(),
                "delimiter": self.delimiter_edit.text(),
                "sheet_name": self.sheet_name_edit.text(),
                "header": self.header_checkbox.isChecked(),
                "skiprows": self.start_row_spin.value() - 1,
            },
        )

    def _update_preview(self) -> None:
        if not self.file_path:
            return

        try:
            settings = self._get_current_settings()
            settings["nrows"] = 100  # Preview first 100 rows
            self.dataframe = load_dataframe(self.file_path, settings)
            self._populate_preview_table()

        except Exception as e:
            self.preview_table.clear()
            self.preview_table.setRowCount(1)
            self.preview_table.setColumnCount(1)
            self.preview_table.setItem(0, 0, QTableWidgetItem(f"Error: {e}"))

    def _populate_preview_table(self) -> None:
        if self.dataframe is None:
            return

        self.preview_table.setRowCount(self.dataframe.shape[0])
        self.preview_table.setColumnCount(self.dataframe.shape[1])
        self.preview_table.setHorizontalHeaderLabels(self.dataframe.columns.astype(str))

        for i in range(self.dataframe.shape[0]):
            for j in range(self.dataframe.shape[1]):
                self.preview_table.setItem(i, j, QTableWidgetItem(str(self.dataframe.iat[i, j])))

    def get_data(self) -> Optional[pd.DataFrame]:
        if not self.file_path:
            return None

        try:
            return load_dataframe(self.file_path, self._get_current_settings())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import file: {e}")
            return None
