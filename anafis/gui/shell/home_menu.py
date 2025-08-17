from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from typing import Optional


class HomeMenuWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
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
        btn_spreadsheet.clicked.connect(
            lambda: self.parent_notebook.new_tab("spreadsheet")
        )
        layout.addWidget(btn_spreadsheet)

        btn_fitting = QPushButton("New Fitting")
        btn_fitting.clicked.connect(lambda: self.parent_notebook.new_tab("fitting"))
        layout.addWidget(btn_fitting)

        btn_solver = QPushButton("New Solver")
        btn_solver.clicked.connect(lambda: self.parent_notebook.new_tab("solver"))
        layout.addWidget(btn_solver)

        btn_montecarlo = QPushButton("New Monte-Carlo")
        btn_montecarlo.clicked.connect(
            lambda: self.parent_notebook.new_tab("montecarlo")
        )
        layout.addWidget(btn_montecarlo)

        self.setLayout(layout)
