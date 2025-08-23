from typing import Optional, List
from PyQt6.QtWidgets import (
    QTabWidget,
    QTabBar,
    QMainWindow,
    QApplication,
    QStyle,
    QWidget,
    QInputDialog,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QMimeData
from PyQt6.QtGui import QMouseEvent, QCloseEvent, QDrag


class TabBar(QTabBar):
    def __init__(self, parent: Optional[QTabWidget] = None) -> None:
        super().__init__(parent)
        self.drag_start_pos = QPoint()
        self.dragging = False # Add a flag to track if a drag is in progress

    def mousePressEvent(self, event: Optional[QMouseEvent]) -> None:
        if event and event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
            self.dragging = False # Reset dragging flag on mouse press
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Optional[QMouseEvent]) -> None:
        if event and event.buttons() == Qt.MouseButton.LeftButton and not self.dragging: # Only initiate if not already dragging
            distance = (event.pos() - self.drag_start_pos).manhattanLength()
            style = QApplication.style()
            if style:
                overlap = style.pixelMetric(QStyle.PixelMetric.PM_TabBarTabHSpace)

                if distance >= QApplication.startDragDistance() + overlap:
                    index = self.tabAt(self.drag_start_pos)
                    if index >= 0:
                        parent = self.parent()
                        if parent and hasattr(parent, "detach_tab"):
                            parent.detach_tab(index)
                            self.dragging = True # Set dragging flag to true after initiating detach
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Optional[QMouseEvent]) -> None: # Add mouseReleaseEvent to reset flag
        if event and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: Optional[QMouseEvent]) -> None:
        if event and event.button() == Qt.MouseButton.LeftButton:
            index = self.tabAt(event.pos())
            if index >= 0:
                # Exclude the Home tab (index 0) from renaming
                if index == 0:
                    super().mouseDoubleClickEvent(event)
                    return

                old_name = self.tabText(index)
                new_name, ok = QInputDialog.getText(
                    self, "Rename Tab", "New tab name:", QLineEdit.EchoMode.Normal, old_name
                )
                if ok and new_name and new_name != old_name:
                    self.setTabText(index, new_name)
                    # Notify the tab widget (DetachableTabWidget) about the rename
                    parent = self.parent()
                    if parent and hasattr(parent, "_emit_tab_renamed_signal"):
                        parent._emit_tab_renamed_signal(index, new_name)
        super().mouseDoubleClickEvent(event)


class DetachedTabBar(QTabBar):
    def __init__(self, parent: Optional[QTabWidget] = None) -> None:
        super().__init__(parent)
        self.drag_start_pos = QPoint()

    def mousePressEvent(self, event: Optional[QMouseEvent]) -> None:
        if event and event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Optional[QMouseEvent]) -> None:
        if event and event.buttons() == Qt.MouseButton.LeftButton:
            distance = (event.pos() - self.drag_start_pos).manhattanLength()
            style = QApplication.style()
            if style:
                overlap = style.pixelMetric(QStyle.PixelMetric.PM_TabBarTabHSpace)

                if distance >= QApplication.startDragDistance() + overlap:
                    index = self.tabAt(self.drag_start_pos)
                    if index >= 0:
                        # Get widget and tab_title before initiating drag
                        widget = self.parent().widget(index)
                        tab_title = self.tabText(index)

                        # Initiate drag operation
                        mime_data = QMimeData()
                        mime_data.setData('application/x-anafis-tab-data', b'dummy_data') # Placeholder data

                        drag = QDrag(self)
                        drag.setMimeData(mime_data)
                        # Store the actual widget and title in the drag object's properties
                        drag.setProperty('widget', widget)
                        drag.setProperty('tab_title', tab_title)
                        drag.setProperty('detached_window_id', id(self.parent().parent())) # Pass ID of DetachedWindow

                        # Execute the drag
                        print(f"DetachedTabBar: Initiating drag for tab: {tab_title}, widget: {widget}, detached_window_id: {id(self.parent().parent())}")
                        drag.exec(Qt.DropAction.MoveAction)
        super().mouseMoveEvent(event)


class DetachedWindow(QMainWindow):
    """A detached window that can be reattached."""

    window_closed = pyqtSignal(object, object)  # window, widget

    def __init__(
        self,
        widget: QWidget,
        tab_title: str,
        parent_widget: Optional[QTabWidget] = None,
    ) -> None:
        super().__init__()
        self.original_widget = widget # Store original widget
        self.tab_title = tab_title
        self.parent_widget = parent_widget

        # Create an internal QTabWidget
        self.internal_tab_widget = QTabWidget()
        self.internal_tab_widget.setTabBar(DetachedTabBar(self.internal_tab_widget))
        self.internal_tab_widget.addTab(widget, tab_title)
        self.setCentralWidget(self.internal_tab_widget)

        self.setWindowTitle(f"ANAFIS - {tab_title}")
        self.resize(800, 600)

        # Add a reattach action in the menu
        menu_bar = self.menuBar()
        if menu_bar:
            window_menu = menu_bar.addMenu("Window")
            if window_menu:
                reattach_action = window_menu.addAction("Reattach to Main Window")
                if reattach_action:
                    reattach_action.triggered.connect(self.reattach)

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:
        """Handle window close event."""
        self.window_closed.emit(self, self.original_widget)
        super().closeEvent(event)

    def reattach(self) -> None:
        """Reattach this window to the main tab widget."""
        if self.parent_widget and hasattr(self.parent_widget, "reattach_tab"):
            # Get the widget from the internal tab widget
            reattach_widget = self.internal_tab_widget.widget(0)
            self.parent_widget.reattach_tab(reattach_widget, self.tab_title)
            self.close()


class DetachableTabWidget(QTabWidget):
    tab_renamed = pyqtSignal(int, str)  # index, new_name

    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)
        self.setTabBar(TabBar(self))
        self.detached_windows: List[DetachedWindow] = []
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: 'QDragEnterEvent') -> None:
        # Placeholder: Accept the event if it contains our custom tab data
        # We'll define the custom MIME type later when initiating the drag
        if event.mimeData().hasFormat('application/x-anafis-tab-data'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: 'QDragMoveEvent') -> None:
        # Placeholder: Provide visual feedback during drag
        if event.mimeData().hasFormat('application/x-anafis-tab-data'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: 'QDropEvent') -> None:
        if event.mimeData().hasFormat('application/x-anafis-tab-data'):
            # Extract widget and title from the QDrag object's properties
            drag = event.source() # The QDrag object is the source of the event
            widget = drag.property('widget')
            tab_title = drag.property('tab_title')
            detached_window_id = drag.property('detached_window_id')

            if widget and tab_title:
                print(f"DetachableTabWidget: Drop received. Widget: {widget}, Title: {tab_title}, Detached Window ID: {detached_window_id}")
                self.reattach_tab(widget, tab_title)
                event.acceptProposedAction()

                # Close the detached window that initiated the drag
                for window in self.detached_windows:
                    if id(window) == detached_window_id:
                        window.close()
                        break # Found and closed, exit loop
            else:
                event.ignore()
        else:
            event.ignore()

    def _emit_tab_renamed_signal(self, index: int, new_name: str) -> None:
        self.tab_renamed.emit(index, new_name)

    def detach_tab(self, index: int) -> None:
        """Detach a tab to a separate window."""
        if self.count() <= 1 or index == 0:  # Don't detach home tab or if it's the only tab
            return

        widget = self.widget(index)
        tab_title = self.tabText(index)

        if widget:
            self.removeTab(index)
            detached_window = DetachedWindow(widget, tab_title, self)
            detached_window.window_closed.connect(self.on_detached_window_closed)

            self.detached_windows.append(detached_window)
            detached_window.show()

    def reattach_tab(self, widget: QWidget, tab_title: str) -> None:
        """Reattach a widget as a new tab."""
        index = self.addTab(widget, tab_title)
        self.setCurrentIndex(index)

    def on_detached_window_closed(self, window: DetachedWindow, widget: QWidget) -> None:
        """Handle when a detached window is closed."""
        if window in self.detached_windows:
            self.detached_windows.remove(window)

    def close_all_detached_windows(self) -> None:
        """Close all detached windows."""
        for window in self.detached_windows[:]:
            window.close()
