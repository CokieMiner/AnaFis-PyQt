from typing import Optional

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

from anafis.core.data_structures import TabState


class MonteCarloTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Monte-Carlo Tab Content"))
        self.setLayout(layout)

    def get_state(self) -> TabState:
        return {"type": "montecarlo"}
