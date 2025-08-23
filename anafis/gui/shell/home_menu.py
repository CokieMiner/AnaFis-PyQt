from typing import Optional, TYPE_CHECKING
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QFrame,
    QListWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from anafis import __version__

if TYPE_CHECKING:
    from anafis.gui.shell.notebook import Notebook


class HomeMenuWidget(QWidget):
    def __init__(self, parent: Optional["Notebook"] = None) -> None:
        super().__init__(parent)
        self.parent_notebook = parent
        self.init_ui()
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2e2e2e;
                color: #e0e0e0;
                font-size: 14px;
            }
            QLabel#SectionLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 10px;
            }
            QPushButton#ModernButton {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                border-radius: 5px;
                padding: 15px;
                text-align: left;
                min-width: 200px;
            }
            QPushButton#ModernButton:hover {
                background-color: #5a5a5a;
            }
            QListWidget {
                border: 1px solid #4a4a4a;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
        """
        )

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(70, 50, 50, 50)
        main_layout.setSpacing(30)

        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Icon
        icon_path = Path("anafis/assets/icon.png")
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            icon_label = QLabel()
            icon_label.setPixmap(
                pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
            title_layout.addWidget(icon_label)

        app_name_label = QLabel(
            f'<span style="font-size:72px; font-weight:bold; color:#ffffff;">AnaFis</span> '
            f'<span style="font-size:16px; color:#c0c0c0;">v{__version__}</span>'
        )
        title_layout.addWidget(app_name_label)
        title_layout.addStretch()

        main_layout.addLayout(title_layout)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(40)

        # Quick New Section
        quick_new_widget = self._create_quick_new_widget()
        grid_layout.addWidget(quick_new_widget, 0, 0)

        # Recent Files Section
        recent_files_widget = self._create_recent_files_widget()
        grid_layout.addWidget(recent_files_widget, 0, 1)

        main_layout.addLayout(grid_layout)
        self.setLayout(main_layout)

    def _create_quick_new_widget(self) -> QWidget:
        widget = QFrame()
        layout = QVBoxLayout(widget)

        label = QLabel("Quick New")
        label.setObjectName("SectionLabel")
        layout.addWidget(label)

        buttons = [
            ("spreadsheet", "New Spreadsheet", "📄"),
            ("fitting", "New Fitting", "📈"),
            ("solver", "New Solver", "🧮"),
            ("montecarlo", "New Monte-Carlo", "🎲"),
        ]

        for name, text, icon in buttons:
            btn = self._create_modern_button(text, icon, name)
            layout.addWidget(btn)

        layout.addStretch()
        return widget

    def _create_modern_button(self, text: str, icon_char: str, tab_name: str) -> QPushButton:
        btn = QPushButton(f"{icon_char} {text}")
        btn.setObjectName("ModernButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_new_tab_clicked(tab_name))
        return btn

    def _create_recent_files_widget(self) -> QWidget:
        widget = QFrame()
        layout = QVBoxLayout(widget)

        label = QLabel("Recent Files")
        label.setObjectName("SectionLabel")
        layout.addWidget(label)

        list_widget = QListWidget()

        # Placeholder for recent files logic
        # TODO: Load recent files from a persistent store (e.g., QSettings, a config file)
        recent_files = ["pendulum_data.csv", "g_measurement.anafis", "transistor_curves.xlsx"]

        if not recent_files:
            placeholder_item = QListWidgetItem("No recent files")
            placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags)
            list_widget.addItem(placeholder_item)
        else:
            for file_path in recent_files:
                item = QListWidgetItem(f"📄 {file_path}")
                list_widget.addItem(item)

        layout.addWidget(list_widget)
        return widget

    def _on_new_tab_clicked(self, tab_type: str) -> None:
        if self.parent_notebook:
            self.parent_notebook.new_tab(tab_type)
