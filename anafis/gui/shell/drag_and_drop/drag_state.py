from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QWidget

# Avoid circular imports for type hinting
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anafis.gui.shell.detachable_tab import DetachableTabWidget
    from anafis.gui.shell.drag_and_drop.drag_preview_widget import DragPreviewWidget


class DragState(Enum):
    """Enhanced drag states for sophisticated tab handling"""

    NONE = 0
    PREPARING = 1  # Mouse down, checking distance threshold
    REORDERING = 2  # Dragging within same tab bar (reorder)
    DETACHING = 3  # Dragging outside bounds (will detach)
    EXTERNAL_DRAG = 4  # Dragging over other windows
    COMPLETING = 5  # Finalizing drag operation


@dataclass
class DragOperation:
    """Complete drag operation state"""

    source_tab_index: int
    source_widget: "DetachableTabWidget"
    source_window: QMainWindow
    dragged_widget: QWidget
    tab_title: str
    tab_icon: Optional[QIcon]
    drag_start_pos: QPoint
    drag_preview: Optional["DragPreviewWidget"]
    current_state: DragState

    def cleanup(self) -> None:
        """Clean up drag operation resources"""
        if self.drag_preview:
            self.drag_preview.close()
            self.drag_preview = None
