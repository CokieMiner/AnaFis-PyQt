from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from typing import Optional, Dict, Any


class MonteCarloTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Monte-Carlo Tab Content"))
        self.setLayout(layout)

    def get_state(self) -> Dict[str, Any]:
        return {"type": "montecarlo"}
