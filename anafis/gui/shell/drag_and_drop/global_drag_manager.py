import logging
from typing import Optional, List, cast, TYPE_CHECKING
from PyQt6.QtCore import QObject, QEvent, pyqtSignal, QPoint

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QMouseEvent

from anafis.gui.shell.drag_and_drop.drag_state import DragOperation

# Avoid circular imports for type hinting
if TYPE_CHECKING:
    from anafis.gui.shell.detachable_tab import DetachableTabWidget  # Moved inside TYPE_CHECKING

logger = logging.getLogger(__name__)


class GlobalDragManager(QObject):
    """Manages drag operations across all application windows"""

    _instance: Optional["GlobalDragManager"] = None

    # Signals
    drag_started = pyqtSignal(object)  # DragOperation
    drag_ended = pyqtSignal(object)  # DragOperation
    external_drop_available = pyqtSignal(QPoint, object)  # position, target_widget

    def __init__(self) -> None:
        super().__init__()
        self.active_drag: Optional[DragOperation] = None
        self.all_tab_widgets: List["DetachableTabWidget"] = []  # Changed type hint
        self.all_windows: List[QMainWindow] = []

        # Install global event filter for cross-window drag detection
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    @classmethod
    def instance(cls) -> "GlobalDragManager":
        """Singleton access"""
        if cls._instance is None:
            cls._instance = GlobalDragManager()
        return cls._instance

    def register_tab_widget(self, widget: "DetachableTabWidget") -> None:  # Changed type hint
        """Register a tab widget for drag operations"""
        if widget not in self.all_tab_widgets:
            self.all_tab_widgets.append(widget)

        # Register parent window
        window = widget.window()
        if isinstance(window, QMainWindow) and window not in self.all_windows:  # Check if it's QMainWindow
            self.all_windows.append(window)

    def register_drag(self, drag_op: DragOperation) -> None:
        """Register an active drag operation"""
        self.active_drag = drag_op
        self.drag_started.emit(drag_op)

        # Notify all tab widgets about active drag
        for widget in self.all_tab_widgets:
            if widget != drag_op.source_widget:
                widget.set_external_drag_mode(True, drag_op)

    def complete_drag(self) -> None:
        """Complete active drag operation"""
        if self.active_drag:
            self.drag_ended.emit(self.active_drag)

            # Notify all tab widgets
            for widget in self.all_tab_widgets:
                widget.set_external_drag_mode(False, None)

            self.active_drag = None

    def eventFilter(self, obj: Optional[QObject], event: Optional[QEvent]) -> bool:  # Matched supertype signature
        """Global event filter for cross-window drag detection"""
        if self.active_drag and event is not None and event.type() == QEvent.Type.MouseMove:
            mouse_event = cast(QMouseEvent, event)
            global_pos = mouse_event.globalPosition().toPoint()

            # Check if dragging over any of our windows
            self._check_drop_targets(global_pos)

        return False  # Don't consume events

    def _check_drop_targets(self, global_pos: QPoint) -> None:
        """Check for valid drop targets at global position"""
        if not self.active_drag:
            return

        for widget in self.all_tab_widgets:
            if widget == self.active_drag.source_widget:
                continue

            # Check if position is over this widget
            local_pos = widget.mapFromGlobal(global_pos)
            if widget.rect().contains(local_pos):
                self.external_drop_available.emit(global_pos, widget)
                break
