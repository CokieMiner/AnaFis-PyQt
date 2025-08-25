import logging
from typing import Optional, List, Dict, Union, cast
from enum import IntEnum

from PyQt6.QtWidgets import (
    QTabWidget,
    QTabBar,
    QMainWindow,
    QApplication,
    QWidget,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QSize
from PyQt6.QtGui import (
    QMouseEvent,
    QCloseEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QDragLeaveEvent,  # Added QDragLeaveEvent
)

# Import new drag and drop components
from anafis.gui.shell.drag_and_drop.drag_preview_widget import DragPreviewWidget
from anafis.gui.shell.drag_and_drop.drop_indicator import DropIndicator
from anafis.gui.shell.drag_and_drop.drag_state import DragState, DragOperation
from anafis.gui.shell.drag_and_drop.global_drag_manager import GlobalDragManager
from anafis.gui.shell.drag_and_drop.window_hierarchy import window_hierarchy, WindowHierarchy

# For new tab creation in detached windows
from anafis.gui.tabs.spreadsheet_tab import SpreadsheetTab
from anafis.gui.tabs.fitting_tab import FittingTab

import math
import time

logger = logging.getLogger(__name__)


class EnhancedTabBar(QTabBar):
    """Enhanced TabBar with improved drag handling for Phase 1"""

    # Signals for drag operations
    tab_detach_requested = pyqtSignal(int, QPoint)  # index, global_pos
    tab_reorder_requested = pyqtSignal(int, int)  # from_index, to_index
    drag_operation_started = pyqtSignal(object)  # DragOperation
    drag_operation_ended = pyqtSignal()

    def __init__(self, parent: Optional[QTabWidget] = None):
        super().__init__(parent)

        # Drag configuration - can be made configurable later
        self.drag_threshold = 15  # Pixels before drag starts
        self.detach_threshold = 50  # Pixels outside tab bar to detach

        # Drag state
        self.current_drag: Optional[DragOperation] = None
        self.drag_start_pos = QPoint()

        # Enable mouse tracking for better hover effects
        self.setMouseTracking(True)

        logger.debug("EnhancedTabBar initialized")

    def mousePressEvent(self, event: Optional[QMouseEvent]) -> None:
        """Handle mouse press with drag preparation"""
        if event and event.button() == Qt.MouseButton.LeftButton:
            tab_index = self.tabAt(event.pos())

            if tab_index >= 0:
                # Don't allow dragging Home tab (index 0)
                if tab_index == 0:
                    super().mousePressEvent(event)
                    return

                # Store drag start position
                self.drag_start_pos = event.globalPosition().toPoint()

                # Prepare drag operation
                parent_widget = self.parent()
                if isinstance(parent_widget, QTabWidget):
                    # Cast parent_widget to DetachableTabWidget
                    detachable_tab_widget = cast(DetachableTabWidget, parent_widget)

                    # Ensure source_window is QMainWindow
                    source_window = detachable_tab_widget.window()
                    if not isinstance(source_window, QMainWindow):
                        logger.warning("Source window is not QMainWindow, cannot start drag operation.")
                        return

                    # Ensure dragged_widget is not None
                    dragged_widget = detachable_tab_widget.widget(tab_index)
                    if dragged_widget is None:
                        logger.warning(f"Dragged widget at index {tab_index} is None, cannot start drag operation.")
                        return

                    self.current_drag = DragOperation(
                        source_tab_index=tab_index,
                        source_widget=detachable_tab_widget,
                        source_window=source_window,
                        dragged_widget=dragged_widget,
                        tab_title=self.tabText(tab_index),
                        tab_icon=self.tabIcon(tab_index),
                        drag_start_pos=self.drag_start_pos,
                        drag_preview=None,
                        current_state=DragState.PREPARING,
                    )

                    logger.debug(f"Drag prepared for tab {tab_index}: {self.current_drag.tab_title}")

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Optional[QMouseEvent]) -> None:
        """Handle mouse move with drag state management"""
        if event and self.current_drag and event.buttons() == Qt.MouseButton.LeftButton:
            current_pos = event.globalPosition().toPoint()
            drag_distance = (current_pos - self.drag_start_pos).manhattanLength()

            if self.current_drag.current_state == DragState.PREPARING:
                # Check if we've moved enough to start dragging
                if drag_distance >= self.drag_threshold:
                    self._start_active_drag(current_pos)

            elif self.current_drag.current_state in [DragState.REORDERING, DragState.DETACHING]:
                # Handle active drag
                self._handle_active_drag(event.pos(), current_pos)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Optional[QMouseEvent]) -> None:
        """Handle mouse release and complete drag operation"""
        if event and self.current_drag:
            try:
                final_pos = event.globalPosition().toPoint()
                self._complete_drag_operation(final_pos)
            except Exception as e:
                logger.error(f"Error completing drag operation: {e}")
            finally:
                # Always clean up
                self._cleanup_drag_operation()

        super().mouseReleaseEvent(event)

    def _start_active_drag(self, global_pos: QPoint) -> None:
        """Start active drag with visual feedback"""
        if not self.current_drag:
            return

        logger.debug(f"Starting active drag for: {self.current_drag.tab_title}")

        try:
            # Create drag preview
            tab_rect = self.tabRect(self.current_drag.source_tab_index)
            self.current_drag.drag_preview = DragPreviewWidget(
                self.current_drag.tab_title, self.current_drag.tab_icon, tab_rect
            )
            self.current_drag.drag_preview.show()
            self.current_drag.drag_preview.update_position(global_pos)

            # Determine initial drag state
            if self._is_dragging_within_tab_bar(global_pos):
                self.current_drag.current_state = DragState.REORDERING
                logger.debug("Drag state: REORDERING")
            else:
                self.current_drag.current_state = DragState.DETACHING
                logger.debug("Drag state: DETACHING")

            # Emit signal
            self.drag_operation_started.emit(self.current_drag)

        except Exception as e:
            logger.error(f"Error starting active drag: {e}")

    def _handle_active_drag(self, local_pos: QPoint, global_pos: QPoint) -> None:
        """Handle active drag movement"""
        if not self.current_drag or not self.current_drag.drag_preview:
            return

        try:
            # Update preview position
            self.current_drag.drag_preview.update_position(global_pos)

            # Determine current drag context
            within_tab_bar = self._is_dragging_within_tab_bar(global_pos)

            if within_tab_bar and self.current_drag.current_state != DragState.REORDERING:
                self.current_drag.current_state = DragState.REORDERING
                logger.debug("Drag state changed to: REORDERING")

            elif not within_tab_bar and self.current_drag.current_state != DragState.DETACHING:
                self.current_drag.current_state = DragState.DETACHING
                logger.debug("Drag state changed to: DETACHING")

        except Exception as e:
            logger.error(f"Error handling active drag: {e}")

    def _complete_drag_operation(self, global_pos: QPoint) -> None:
        """Complete the drag operation"""
        if not self.current_drag:
            return

        try:
            self.current_drag.current_state = DragState.COMPLETING

            if self._is_dragging_within_tab_bar(global_pos):
                # Handle reorder
                logger.debug("Completing reorder operation")
                self._complete_reorder()
            else:
                # Handle detach
                logger.debug("Completing detach operation")
                self._complete_detach(global_pos)

        except Exception as e:
            logger.error(f"Error completing drag operation: {e}")

    def _complete_reorder(self) -> None:
        """Complete tab reorder operation"""
        if not self.current_drag:
            return

        # For Phase 1, we'll emit a signal for the parent to handle
        # In later phases, this will be more sophisticated
        current_index = self.current_drag.source_tab_index

        # Simple reorder logic - this will be enhanced in later phases
        self.tab_reorder_requested.emit(current_index, current_index)
        logger.debug(f"Reorder requested for tab {current_index}")

    def _complete_detach(self, global_pos: QPoint) -> None:
        """Complete tab detach operation"""
        if not self.current_drag:
            return

        # Emit detach signal for parent to handle
        self.tab_detach_requested.emit(self.current_drag.source_tab_index, global_pos)

        logger.info(f"Detach requested for tab {self.current_drag.source_tab_index}: {self.current_drag.tab_title}")

    def _is_dragging_within_tab_bar(self, global_pos: QPoint) -> bool:
        """Check if drag is within tab bar bounds (with some tolerance)"""
        local_pos = self.mapFromGlobal(global_pos)
        # Add some margin for easier reordering
        expanded_rect = self.rect().adjusted(-20, -20, 20, self.detach_threshold)
        return expanded_rect.contains(local_pos)

    def _cleanup_drag_operation(self) -> None:
        """Clean up drag operation resources"""
        if self.current_drag:
            try:
                self.current_drag.cleanup()
                self.drag_operation_ended.emit()
                logger.debug("Drag operation cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up drag operation: {e}")
            finally:
                self.current_drag = None


class DetachedWindow(QMainWindow):
    """Enhanced detached window with multi-tab support"""

    window_closed = pyqtSignal(object, object)  # window, widget
    tab_moved_to_main = pyqtSignal(object, str)  # widget, title

    def __init__(self, widget: QWidget, tab_title: str, parent_tab_widget: Optional[QTabWidget] = None):
        super().__init__()

        self.original_widgets: List[QWidget] = [widget]  # Keep track of original widgets
        self.parent_tab_widget = parent_tab_widget
        self.hierarchy_manager: Optional[WindowHierarchy] = None  # Will be set by WindowHierarchy

        # Create internal tab widget with enhanced tab bar
        self.internal_tab_widget = DetachableTabWidget(self)  # Pass self as parent
        self.internal_tab_widget.addTab(widget, tab_title)
        self.setCentralWidget(self.internal_tab_widget)

        # Window properties
        self.setWindowTitle(f"ANAFIS - {tab_title}")
        self.resize(800, 600)
        self.setMinimumSize(400, 300)

        # Connect signals
        self.internal_tab_widget.tab_detach_requested.connect(self._handle_internal_detach)

        # Menu setup
        self._setup_menu()

        # Register with global systems
        GlobalDragManager.instance().register_tab_widget(self.internal_tab_widget)

    def _setup_menu(self) -> None:
        """Setup window menu with reattach options"""
        menu_bar = self.menuBar()
        if menu_bar:  # Added check for None
            window_menu = menu_bar.addMenu("Window")
            if window_menu:  # Added check for None
                # Reattach current tab
                reattach_current_action = window_menu.addAction("Reattach Current Tab")
                if reattach_current_action:  # Added check for None
                    reattach_current_action.triggered.connect(self._reattach_current_tab)

                # Reattach all tabs
                reattach_all_action = window_menu.addAction("Reattach All Tabs")
                if reattach_all_action:  # Added check for None
                    reattach_all_action.triggered.connect(self._reattach_all_tabs)

                window_menu.addSeparator()

                # New tab in this window
                new_tab_menu = window_menu.addMenu("New Tab")
                if new_tab_menu:  # Added check for None
                    spreadsheet_action = new_tab_menu.addAction("Spreadsheet")
                    if spreadsheet_action:
                        spreadsheet_action.triggered.connect(lambda: self._create_new_tab("spreadsheet"))
                    fitting_action = new_tab_menu.addAction("Fitting")
                    if fitting_action:
                        fitting_action.triggered.connect(lambda: self._create_new_tab("fitting"))

    def _handle_internal_detach(self, index: int, global_pos: QPoint) -> None:
        """Handle tab detachment from this window"""
        if self.internal_tab_widget.count() <= 1:
            return  # Don't detach last tab

        widget = self.internal_tab_widget.widget(index)
        tab_title = self.internal_tab_widget.tabText(index)

        if widget is not None:  # Added check for None
            self.internal_tab_widget.removeTab(index)

            # Create new detached window
            new_window = WindowManager(self.internal_tab_widget).create_detached_window_at_position(
                widget, tab_title, global_pos
            )
            new_window.show()

            # Register new window
            if self.parent_tab_widget and hasattr(self.parent_tab_widget, "detached_windows"):
                self.parent_tab_widget.detached_windows.append(new_window)

            if self.hierarchy_manager:
                self.hierarchy_manager.register_detached_window(new_window)

    def _reattach_current_tab(self) -> None:
        """Reattach current tab to main window"""
        current_index = self.internal_tab_widget.currentIndex()
        if current_index >= 0:
            widget = self.internal_tab_widget.widget(current_index)
            tab_title = self.internal_tab_widget.tabText(current_index)

            if self.parent_tab_widget and hasattr(self.parent_tab_widget, "reattach_tab"):
                self.internal_tab_widget.removeTab(current_index)
                self.parent_tab_widget.reattach_tab(widget, tab_title)

                # Close window if no tabs left
                if self.internal_tab_widget.count() == 0:
                    self.close()

    def _reattach_all_tabs(self) -> None:
        """Reattach all tabs to main window"""
        if not self.parent_tab_widget or not hasattr(self.parent_tab_widget, "reattach_tab"):
            return

        # Collect all tabs
        tabs_to_reattach = []
        for i in range(self.internal_tab_widget.count()):
            widget = self.internal_tab_widget.widget(i)
            title = self.internal_tab_widget.tabText(i)
            tabs_to_reattach.append((widget, title))

        # Reattach all
        for widget, title in tabs_to_reattach:
            self.parent_tab_widget.reattach_tab(widget, title)

        # Close this window
        self.close()

    def _create_new_tab(self, tab_type: str) -> None:
        """Create new tab in this detached window"""
        # Generate unique tab ID
        tab_id = f"{tab_type}_{int(time.time())}"
        tab_title = f"{tab_type.capitalize()} Tab"

        # Create appropriate widget
        if tab_type == "spreadsheet":
            widget: Union[SpreadsheetTab, FittingTab] = SpreadsheetTab(tab_id=tab_id, parent=self, tab_name=tab_title)
        elif tab_type == "fitting":
            widget = FittingTab(tab_id=tab_id, parent=self, tab_name=tab_title)
        else:
            return

        # Add to internal tab widget
        index = self.internal_tab_widget.addTab(widget, tab_title)
        self.internal_tab_widget.setCurrentIndex(index)

    def accept_external_tab(self, widget: QWidget, tab_title: str) -> bool:
        """Accept a tab from external drag operation"""
        try:
            index = self.internal_tab_widget.addTab(widget, tab_title)
            self.internal_tab_widget.setCurrentIndex(index)
            self.original_widgets.append(widget)  # Keep track of all widgets

            # Update window title if this is the only tab
            if self.internal_tab_widget.count() == 1:
                self.setWindowTitle(f"ANAFIS - {tab_title}")

            return True
        except Exception as e:
            logger.error(f"Error accepting external tab: {e}")
            return False

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:
        """Handle window close event"""
        # Collect all widgets before closing
        widgets_to_emit = []
        for i in range(self.internal_tab_widget.count()):
            widget = self.internal_tab_widget.widget(i)
            if widget:
                widgets_to_emit.append(widget)

        # Emit signals for each widget
        for widget in widgets_to_emit:
            self.window_closed.emit(self, widget)

        super().closeEvent(event)


class DetachableTabWidget(QTabWidget):
    tab_renamed = pyqtSignal(int, str)  # index, new_name
    tab_detach_requested = pyqtSignal(int, QPoint)  # index, global_pos
    external_tab_received = pyqtSignal(QWidget, str)  # widget, title

    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)

        # Set enhanced tab bar
        self.setTabBar(EnhancedTabBar(self))

        # Window management
        self.detached_windows: List[DetachedWindow] = []
        self.window_manager = WindowManager(self)

        # Drag and drop setup
        self.setAcceptDrops(True)
        self.external_drag_mode = False
        self.current_external_drag: Optional[DragOperation] = None

        # Visual feedback
        self.drop_indicator: Optional[DropIndicator] = None
        self.drop_preview_line: Optional[QWidget] = None  # Not used in plan, but kept for consistency

        # Connect signals
        self._setup_connections()

        # Register with global drag manager
        GlobalDragManager.instance().register_tab_widget(self)

    def _setup_connections(self) -> None:
        """Setup internal signal connections"""
        # Tab bar signals
        tab_bar = self.tabBar()
        if isinstance(tab_bar, EnhancedTabBar):
            tab_bar.tab_detach_requested.connect(self.detach_tab_at_position)
            tab_bar.tab_reorder_requested.connect(self.reorder_tabs)
            tab_bar.drag_operation_started.connect(self._handle_external_drag_start)
            tab_bar.drag_operation_ended.connect(self._handle_drag_ended)

        # Global drag manager signals
        drag_manager = GlobalDragManager.instance()
        drag_manager.external_drop_available.connect(self._handle_external_drop_available)
        drag_manager.drag_ended.connect(self._handle_drag_ended)

    def set_external_drag_mode(self, enabled: bool, drag_op: Optional[DragOperation]) -> None:
        """Set external drag mode for cross-window operations"""
        self.external_drag_mode = enabled
        self.current_external_drag = drag_op

        if enabled and drag_op:
            # Show visual feedback that this widget can accept drops
            self.setStyleSheet(
                """
                DetachableTabWidget {
                    border: 2px dashed #0078d4;
                    background-color: rgba(0, 120, 212, 0.1);
                }
            """
            )
        else:
            # Remove visual feedback
            self.setStyleSheet("")
            self._hide_drop_indicators()

    def dragEnterEvent(self, event: Optional[QDragEnterEvent]) -> None:  # Changed to Optional
        """Handle drag enter events"""
        if event and self._should_accept_drag(event):
            event.acceptProposedAction()
            self._show_drop_preview(event.position().toPoint())
        else:
            if event:
                event.ignore()

    def dragMoveEvent(self, event: Optional[QDragMoveEvent]) -> None:  # Changed to Optional
        """Handle drag move events"""
        if event and self._should_accept_drag(event):
            event.acceptProposedAction()
            self._update_drop_preview(event.position().toPoint())
        else:
            if event:
                event.ignore()

    def dragLeaveEvent(self, event: Optional[QDragLeaveEvent]) -> None:  # Changed to Optional
        """Handle drag leave events"""
        if event:  # Added check for None
            self._hide_drop_indicators()
            super().dragLeaveEvent(event)

    def dropEvent(self, event: Optional[QDropEvent]) -> None:  # Changed to Optional
        """Handle drop events"""
        if event and self._handle_external_drop(event.position().toPoint()):
            event.acceptProposedAction()
        else:
            if event:  # Added check for None
                event.ignore()

        self._hide_drop_indicators()
        GlobalDragManager.instance().complete_drag()  # Ensure drag manager is notified

    def _should_accept_drag(
        self, event: Union[QDragEnterEvent, QDragMoveEvent, QDropEvent]
    ) -> bool:  # Added QDropEvent
        """Determine if drag should be accepted"""
        mime_data = event.mimeData()
        if mime_data is not None and mime_data.hasFormat("application/x-anafis-tab-data"):
            return True

        # Accept if we're in external drag mode and there's an active drag from our system
        if self.external_drag_mode and self.current_external_drag:
            return True

        return False

    def _show_drop_preview(self, pos: QPoint) -> None:
        """Show drop preview indicators"""
        drop_zone = self._detect_drop_zone(pos)

        if drop_zone == DropZone.TAB_BAR:
            # Show insertion indicator
            insert_index = self._calculate_insertion_index(pos)
            self._show_insertion_indicator(insert_index)
        elif drop_zone in [DropZone.WINDOW_TITLE, DropZone.EMPTY_SPACE]:
            # Show general drop indicator
            self._show_general_drop_indicator()

    def _update_drop_preview(self, pos: QPoint) -> None:
        """Update drop preview based on current position"""
        self._show_drop_preview(pos)

    def _detect_drop_zone(self, pos: QPoint) -> "DropZone":
        """Detect which drop zone the position is in"""
        tab_bar = self.tabBar()
        if tab_bar is not None:  # Added check for None
            tab_bar_rect = tab_bar.geometry()

            if tab_bar_rect.contains(pos):
                return DropZone.TAB_BAR
            elif pos.y() < tab_bar_rect.bottom() + 10:  # Near tab bar, but not on it
                return DropZone.WINDOW_TITLE
            else:
                return DropZone.EMPTY_SPACE
        return DropZone.NONE  # Return NONE if tabBar is None

    def _calculate_insertion_index(self, pos: QPoint) -> int:
        """Calculate where to insert tab based on drop position"""
        tab_bar = self.tabBar()
        if tab_bar is None:  # Added check for None
            return self.count()

        # Find insertion point between tabs
        for i in range(self.count()):
            tab_rect = tab_bar.tabRect(i)
            if tab_rect is not None and pos.x() < tab_rect.center().x():  # Added check for None
                return i

        return self.count()  # Insert at end

    def _show_insertion_indicator(self, index: int) -> None:
        """Show indicator for tab insertion"""
        self._hide_drop_indicators()

        tab_bar = self.tabBar()
        if tab_bar is not None:  # Added check for None
            if index < self.count():
                # Show indicator before tab
                tab_rect = tab_bar.tabRect(index)
                indicator_pos = QPoint(tab_rect.left() - 2, tab_rect.top())
            else:
                # Show indicator at end
                if self.count() > 0:
                    last_rect = tab_bar.tabRect(self.count() - 1)
                    indicator_pos = QPoint(last_rect.right() + 2, last_rect.top())
                else:
                    indicator_pos = QPoint(10, 5)  # Fallback for empty tab bar

            self.drop_indicator = DropIndicator(self, DropIndicator.IndicatorType.INSERT_BEFORE)
            self.drop_indicator.show_at_position(indicator_pos)

    def _show_general_drop_indicator(self) -> None:
        """Show general drop indicator for window attachment"""
        self._hide_drop_indicators()

        # Show indicator in center of widget
        center_pos = QPoint(self.width() // 2 - 2, self.height() // 2 - 15)
        self.drop_indicator = DropIndicator(self, DropIndicator.IndicatorType.ATTACH_WINDOW)
        self.drop_indicator.show_at_position(center_pos)

    def _hide_drop_indicators(self) -> None:
        """Hide all drop indicators"""
        if self.drop_indicator:
            self.drop_indicator.close()
            self.drop_indicator = None

        if self.drop_preview_line:  # This was in the plan, but not used in the code
            self.drop_preview_line.close()
            self.drop_preview_line = None

    def _handle_external_drag_start(self, drag_op: DragOperation) -> None:
        """Handle signal from TabBar when an external drag starts"""
        # This widget is the source, so it doesn't need to do anything here
        pass

    def _handle_external_drop_available(self, global_pos: QPoint, target_widget: "DetachableTabWidget") -> None:
        """Handle signal from GlobalDragManager when an external drag is over this widget"""
        if target_widget == self:
            # This widget is the target, show appropriate drop preview
            self._show_drop_preview(self.mapFromGlobal(global_pos))
        else:
            # Not the target, hide any indicators
            self._hide_drop_indicators()

    def _handle_drag_ended(self, drag_op: Optional[DragOperation] = None) -> None:
        """Handle signal from GlobalDragManager when a drag operation ends"""
        self._hide_drop_indicators()
        self.set_external_drag_mode(False, None)

    def _handle_external_drop(self, pos: QPoint) -> bool:
        """Handle external drop operation"""
        if self.current_external_drag:
            return self._complete_external_drag_drop(pos)

        return False

    def _complete_external_drag_drop(self, pos: QPoint) -> bool:
        """Complete external drag drop from global drag manager"""
        if not self.current_external_drag:
            return False

        try:
            # Remove tab from source
            source_widget = self.current_external_drag.source_widget
            source_index = self.current_external_drag.source_tab_index

            widget = source_widget.widget(source_index)
            tab_title = source_widget.tabText(source_index)

            if widget is not None:  # Added check for None
                source_widget.removeTab(source_index)

                # Add to this widget
                drop_zone = self._detect_drop_zone(pos)
                if drop_zone == DropZone.TAB_BAR:
                    insert_index = self._calculate_insertion_index(pos)
                    final_index = self.insertTab(insert_index, widget, tab_title)
                else:
                    # If dropping on window title or empty space, create a new detached window
                    # and add the tab there.
                    new_window = self.window_manager.create_detached_window_at_position(
                        widget, tab_title, self.mapToGlobal(pos)
                    )
                    new_window.show()
                    self.detached_windows.append(new_window)
                    window_hierarchy.register_detached_window(new_window)

                    # If the source was a detached window and it's now empty, close it
                    if source_widget.count() == 0 and isinstance(source_widget.parent(), DetachedWindow):
                        cast(DetachedWindow, source_widget.parent()).close()  # Cast to DetachedWindow

                    logger.info(f"External tab dropped to new window: {tab_title}")
                    return True  # Handled by creating new window, no need to add to current tab widget

                self.setCurrentIndex(final_index)

                # Emit signal
                self.external_tab_received.emit(widget, tab_title)

                logger.info(f"External tab drop completed: {tab_title}")
                return True
            return False  # Return False if widget is None

        except Exception as e:
            logger.error(f"Error completing external drag drop: {e}")
            return False

    def _emit_tab_renamed_signal(self, index: int, new_name: str) -> None:
        self.tab_renamed.emit(index, new_name)

    def detach_tab_at_position(self, index: int, global_pos: QPoint) -> None:
        """Detach tab and create window at specific position"""
        if self.count() <= 1 or index == 0:  # Don't detach home tab or if it's the only tab
            return

        widget = self.widget(index)
        tab_title = self.tabText(index)

        if widget is not None:  # Added check for None
            self.removeTab(index)

            # Create detached window at position
            detached_window = self.window_manager.create_detached_window_at_position(widget, tab_title, global_pos)

            # Register window
            self.detached_windows.append(detached_window)
            window_hierarchy.register_detached_window(detached_window)

            detached_window.window_closed.connect(self.on_detached_window_closed)
            detached_window.show()

            logger.info(f"Tab detached: {tab_title}")

    def reorder_tabs(self, from_index: int, to_index: int) -> None:
        """Reorder tabs within this widget"""
        if from_index == to_index or from_index == 0 or to_index == 0:  # Don't move home tab
            return

        # Get tab information
        widget = self.widget(from_index)
        tab_title = self.tabText(from_index)
        tab_icon = self.tabIcon(from_index)

        if widget is not None:  # Added check for None
            # Remove and reinsert
            self.removeTab(from_index)

            # Adjust target index if necessary
            if to_index > from_index:
                to_index -= 1

            final_index = self.insertTab(to_index, widget, tab_icon, tab_title)
            self.setCurrentIndex(final_index)

            logger.debug(f"Tab reordered: {tab_title} from {from_index} to {final_index}")

    def reattach_tab(self, widget: QWidget, tab_title: str) -> None:
        """Reattach a widget as a new tab"""
        index = self.addTab(widget, tab_title)
        self.setCurrentIndex(index)

        logger.info(f"Tab reattached: {tab_title}")

    def on_detached_window_closed(self, window: "DetachedWindow", widget: QWidget) -> None:
        """Handle when a detached window is closed"""
        if window in self.detached_windows:
            self.detached_windows.remove(window)

        logger.debug("Detached window closed and removed from tracking")

    def close_all_detached_windows(self) -> None:
        """Close all detached windows"""
        for window in self.detached_windows[:]:  # Copy list to avoid modification during iteration
            try:
                window.close()
            except Exception as e:
                logger.error(f"Error closing detached window: {e}")

        self.detached_windows.clear()
        logger.info("All detached windows closed")

    def get_all_windows_state(self) -> List[Dict]:
        """Get state of all windows (main + detached)"""
        states = []

        # Main window state (this widget's tabs)
        main_state = {"window_type": "main", "tabs": []}

        for i in range(self.count()):
            widget = self.widget(i)
            if widget is not None and hasattr(widget, "get_state"):
                tab_state = widget.get_state()
                cast(List[Dict], main_state["tabs"]).append(tab_state)  # Cast to List[Dict]

        states.append(main_state)

        # Detached windows states
        for window in self.detached_windows:
            # Assuming DetachedWindow has a method to get its state
            # This needs to be implemented in DetachedWindow if not already
            if hasattr(window, "get_state"):  # Placeholder, needs actual implementation
                states.append(cast(Dict, window.get_state()))  # Cast to Dict

        return states


class DropZone(IntEnum):  # Inherit from QStyle.StandardPixmap for convenience
    """Drop zone types for enhanced drag feedback"""

    NONE = 0
    TAB_BAR = 1  # Drop between existing tabs
    WINDOW_TITLE = 2  # Drop on title bar (new window)
    EMPTY_SPACE = 3  # Drop on empty area (attach to window)


class WindowManager:
    """Manages smart window positioning and creation"""

    def __init__(self, parent_tab_widget: DetachableTabWidget):
        self.parent_tab_widget = parent_tab_widget
        self.cascade_offset = QPoint(30, 30)
        self.created_windows_count = 0

    def create_detached_window_at_position(self, widget: QWidget, tab_title: str, global_pos: QPoint) -> DetachedWindow:
        """Create detached window at smart position"""
        window = DetachedWindow(widget, tab_title, self.parent_tab_widget)

        # Calculate smart position
        smart_pos = self._calculate_smart_position(global_pos)
        window.move(smart_pos)

        # Set appropriate size
        window.resize(800, 600)

        self.created_windows_count += 1
        return window

    def _calculate_smart_position(self, requested_pos: QPoint) -> QPoint:
        """Calculate smart window position avoiding overlaps"""
        # Get screen geometry
        screen = QApplication.primaryScreen()
        if screen is None:  # Added check for None
            return requested_pos  # Return original position if screen is None

        screen_geometry = screen.geometry()

        # Start with requested position
        target_pos = QPoint(requested_pos)

        # Apply cascade offset based on number of created windows
        cascade = self.cascade_offset * self.created_windows_count
        target_pos += cascade

        # Ensure window stays on screen
        window_size = QSize(800, 600)

        # Adjust if would go off right edge
        if target_pos.x() + window_size.width() > screen_geometry.right():
            target_pos.setX(screen_geometry.right() - window_size.width() - 20)

        # Adjust if would go off bottom edge
        if target_pos.y() + window_size.height() > screen_geometry.bottom():
            target_pos.setY(screen_geometry.bottom() - window_size.height() - 40)

        # Ensure not too far left or up
        target_pos.setX(max(target_pos.x(), screen_geometry.left() + 20))
        target_pos.setY(max(target_pos.y(), screen_geometry.top() + 40))

        return target_pos

    def arrange_windows_cascade(self) -> None:
        """Arrange all detached windows in cascade pattern"""
        base_pos = QPoint(100, 100)

        for i, window in enumerate(self.parent_tab_widget.detached_windows):
            cascade_pos = base_pos + (self.cascade_offset * i)
            window.move(cascade_pos)

    def arrange_windows_tile(self) -> None:
        """Arrange all detached windows in tile pattern"""
        screen = QApplication.primaryScreen()
        if screen is None:  # Added check for None
            return  # Cannot arrange if screen is None

        screen_geometry = screen.geometry()
        windows = self.parent_tab_widget.detached_windows

        if not windows:
            return

        # Calculate grid dimensions
        count = len(windows)
        cols = int(math.ceil(math.sqrt(count)))
        rows = int(math.ceil(count / cols))

        # Calculate window sizes
        window_width = (screen_geometry.width() - 40) // cols
        window_height = (screen_geometry.height() - 80) // rows

        # Position windows
        for i, window in enumerate(windows):
            row = i // cols
            col = i % cols

            x = screen_geometry.left() + 20 + (col * window_width)
            y = screen_geometry.top() + 40 + (row * window_height)

            window.move(x, y)
            window.resize(window_width - 10, window_height - 10)
