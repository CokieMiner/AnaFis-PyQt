from PyQt6.QtWidgets import (
    QTabWidget,
    QTabBar,
    QMainWindow,
    QApplication,
    QStyle,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QCloseEvent
from typing import Optional, List


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


class DetachedWindow(QMainWindow):
    """A detached window that can be reattached."""

    window_closed = pyqtSignal(object, object)  # window, widget

    def __init__(
        self, widget, tab_title: str, parent_widget: Optional[QTabWidget] = None
    ) -> None:
        super().__init__()
        self.widget = widget
        self.tab_title = tab_title
        self.parent_widget = parent_widget

        self.setCentralWidget(widget)
        self.setWindowTitle(f"ANAFIS - {tab_title}")
        self.resize(800, 600)

        # Add a reattach action in the menu
        if hasattr(self, "menuBar"):
            window_menu = self.menuBar().addMenu("Window")
            reattach_action = window_menu.addAction("Reattach to Main Window")
            reattach_action.triggered.connect(self.reattach)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        self.window_closed.emit(self, self.widget)
        super().closeEvent(event)

    def reattach(self) -> None:
        """Reattach this window to the main tab widget."""
        if self.parent_widget:
            self.parent_widget.reattach_tab(self.widget, self.tab_title)
            self.close()


class DetachableTabWidget(QTabWidget):
    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)
        self.setTabBar(TabBar(self))
        self.detached_windows: List[DetachedWindow] = []

    def detach_tab(self, index: int) -> None:
        """Detach a tab to a separate window."""
        if (
            self.count() <= 1 or index == 0
        ):  # Don't detach home tab or if it's the only tab
            return

        widget = self.widget(index)
        tab_title = self.tabText(index)

        if widget:
            self.removeTab(index)
            detached_window = DetachedWindow(widget, tab_title, self)
            detached_window.window_closed.connect(self.on_detached_window_closed)

            self.detached_windows.append(detached_window)
            detached_window.show()

    def reattach_tab(self, widget, tab_title: str) -> None:
        """Reattach a widget as a new tab."""
        index = self.addTab(widget, tab_title)
        self.setCurrentIndex(index)

    def on_detached_window_closed(self, window: DetachedWindow, widget) -> None:
        """Handle when a detached window is closed."""
        if window in self.detached_windows:
            self.detached_windows.remove(window)

    def close_all_detached_windows(self) -> None:
        """Close all detached windows."""
        for window in self.detached_windows[:]:
            window.close()
