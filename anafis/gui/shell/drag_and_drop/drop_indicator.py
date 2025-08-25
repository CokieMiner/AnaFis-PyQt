from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QPoint
from enum import Enum


class DropIndicator(QWidget):
    """Visual indicator showing where a tab will be dropped"""

    class IndicatorType(Enum):
        INSERT_BEFORE = 0  # Insert before specific tab
        INSERT_AFTER = 1  # Insert after specific tab
        NEW_WINDOW = 2  # Create new window
        ATTACH_WINDOW = 3  # Attach to existing window

    def __init__(self, parent: QWidget, indicator_type: IndicatorType) -> None:
        super().__init__(parent)
        self.indicator_type = indicator_type
        self.setFixedSize(4, 30)  # Thin vertical line

        # Visual styling
        if indicator_type in [
            DropIndicator.IndicatorType.INSERT_BEFORE,
            DropIndicator.IndicatorType.INSERT_AFTER,
        ]:
            self.setStyleSheet("background-color: #0078d4; border-radius: 2px;")
        else:
            self.setStyleSheet("background-color: #00ff00; border-radius: 2px;")

    def show_at_position(self, pos: QPoint) -> None:
        """Show indicator at specific position"""
        self.move(pos)
        self.show()
        self.raise_()