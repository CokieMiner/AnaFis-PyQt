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
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QCloseEvent


class TabBar(QTabBar):
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
                        parent = self.parent()
                        if parent and hasattr(parent, "detach_tab"):
                            parent.detach_tab(index)
        super().mouseMoveEvent(event)

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
        self.widget = widget
        self.tab_title = tab_title
        self.parent_widget = parent_widget

        self.setCentralWidget(widget)
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
        self.window_closed.emit(self, self.widget)
        super().closeEvent(event)

    def reattach(self) -> None:
        """Reattach this window to the main tab widget."""
        if self.parent_widget and hasattr(self.parent_widget, "reattach_tab"):
            self.parent_widget.reattach_tab(self.widget, self.tab_title)
            self.close()


class DetachableTabWidget(QTabWidget):
    tab_renamed = pyqtSignal(int, str)  # index, new_name

    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)
        self.setTabBar(TabBar(self))
        self.detached_windows: List[DetachedWindow] = []

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
