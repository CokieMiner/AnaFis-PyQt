import logging
from typing import Optional

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QIcon, QPainter, QColor, QPaintEvent # Added QPaintEvent
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class DragPreviewWidget(QWidget):
    """Semi-transparent preview of the tab being dragged"""

    def __init__(self, tab_text: str, tab_icon: Optional[QIcon] = None,
                 tab_rect: QRect = QRect()):
        super().__init__()
        self.tab_text = tab_text
        self.tab_icon = tab_icon
        self.tab_rect = tab_rect if not tab_rect.isEmpty() else QRect(0, 0, 120, 30)

        # Window setup for floating preview
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Visual properties
        self.opacity = 0.7
        self.setFixedSize(self.tab_rect.width() + 10, self.tab_rect.height() + 10)

        logger.debug("DragPreviewWidget initialized")

    def paintEvent(self, event: QPaintEvent | None) -> None: # Added event type and return type
        """Paint the drag preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set opacity
        painter.setOpacity(self.opacity)

        # Draw tab background with rounded corners
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.fillRect(rect, QColor(100, 150, 200, 180))

        # Draw border
        painter.setPen(QColor(50, 100, 150, 200))
        painter.drawRect(rect)

        # Draw icon if available
        if self.tab_icon and not self.tab_icon.isNull():
            icon_rect = QRect(rect.left() + 5, rect.center().y() - 8, 16, 16)
            painter.drawPixmap(icon_rect, self.tab_icon.pixmap(16, 16))
            text_rect = QRect(icon_rect.right() + 5, rect.top(),
                             rect.width() - icon_rect.width() - 10, rect.height())
        else:
            text_rect = rect.adjusted(5, 0, -5, 0)

        # Draw tab text
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.tab_text)

    def update_position(self, global_pos: QPoint) -> None: # Added return type
        """Update preview position following cursor"""
        # Offset slightly from cursor to avoid interfering with drag detection
        self.move(global_pos + QPoint(10, 10))