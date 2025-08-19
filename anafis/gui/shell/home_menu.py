from typing import Optional, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from anafis.gui.shell.notebook import Notebook


class HomeMenuWidget(QWidget):
    def __init__(self, parent: Optional["Notebook"] = None) -> None:
        super().__init__(parent)
        self.parent_notebook = parent
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Quick New section
        quick_new_label = QLabel("Quick New")
        quick_new_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(quick_new_label)

        btn_spreadsheet = QPushButton("New Spreadsheet")
        btn_spreadsheet.clicked.connect(self._on_new_spreadsheet_clicked)
        layout.addWidget(btn_spreadsheet)

        btn_fitting = QPushButton("New Fitting")
        btn_fitting.clicked.connect(self._on_new_fitting_clicked)
        layout.addWidget(btn_fitting)

        btn_solver = QPushButton("New Solver")
        btn_solver.clicked.connect(self._on_new_solver_clicked)
        layout.addWidget(btn_solver)

        btn_montecarlo = QPushButton("New Monte-Carlo")
        btn_montecarlo.clicked.connect(self._on_new_montecarlo_clicked)
        layout.addWidget(btn_montecarlo)

        self.setLayout(layout)

    def _on_new_spreadsheet_clicked(self) -> None:
        if self.parent_notebook:
            self.parent_notebook.new_tab("spreadsheet")

    def _on_new_fitting_clicked(self) -> None:
        if self.parent_notebook:
            self.parent_notebook.new_tab("fitting")

    def _on_new_solver_clicked(self) -> None:
        if self.parent_notebook:
            self.parent_notebook.new_tab("solver")

    def _on_new_montecarlo_clicked(self) -> None:
        if self.parent_notebook:
            self.parent_notebook.new_tab("montecarlo")
