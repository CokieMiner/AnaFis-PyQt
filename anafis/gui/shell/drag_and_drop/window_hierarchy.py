import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING, Callable, cast
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget
)

from anafis.core.protocols import HasGetState

# Avoid circular imports for type hinting
if TYPE_CHECKING:
    from anafis.gui.shell.detachable_tab import DetachedWindow

logger = logging.getLogger(__name__)


class WindowHierarchy(QObject):
    """Manages the hierarchy of windows with Home tab authority"""

    # Signals for window management events
    shutdown_initiated = pyqtSignal()
    all_windows_closing = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.main_window: Optional[QMainWindow] = None  # Window with Home tab
        self.detached_windows: List["DetachedWindow"] = []
        self._shutdown_in_progress = False

        logger.debug("WindowHierarchy initialized")

    def register_main_window(self, window: QMainWindow) -> None:
        """Register the main window (contains Home tab)"""
        self.main_window = window
        
        # Store original close event
        if hasattr(window, 'closeEvent'):
            original_close = window.closeEvent
            
            def enhanced_close_event(event: QCloseEvent) -> None:
                if not self._shutdown_in_progress:
                    logger.info("Main window closing - initiating application shutdown")
                    self.initiate_application_shutdown()
                    # Let the original close event handle the rest
                original_close(event)
            
            # Replace the close event
            window.closeEvent = cast(Callable[[QCloseEvent | None], None], enhanced_close_event) # type: ignore
        
        logger.info("Main window registered with WindowHierarchy")
    
    def register_detached_window(self, window: 'DetachedWindow') -> None:
        """Register a detached window"""
        if window not in self.detached_windows:
            self.detached_windows.append(window)
            window.hierarchy_manager = self
            
            # Connect close event for cleanup
            window.window_closed.connect(self.on_detached_window_closed)
            
            logger.debug(f"Detached window registered: {window.windowTitle()}")

    def unregister_detached_window(self, window: "DetachedWindow") -> None:
        """Unregister a detached window"""
        if window in self.detached_windows:
            self.detached_windows.remove(window)
            logger.debug(f"Detached window unregistered: {window.windowTitle()}")

    def initiate_application_shutdown(self) -> None:
        """Initiate complete application shutdown"""
        if self._shutdown_in_progress:
            return

        self._shutdown_in_progress = True
        logger.info("Starting application shutdown sequence")

        # Emit shutdown signal
        self.shutdown_initiated.emit()

        try:
            # Save complete application state
            self.save_complete_application_state()

            # Close all detached windows
            self.all_windows_closing.emit()
            for window in self.detached_windows[:]:  # Copy to avoid modification during iteration
                try:
                    window.close()
                except Exception as e:
                    logger.error(f"Error closing detached window: {e}")

            # Shutdown data bus
            try:
                from anafis.gui.shared.data_bus import shutdown_global_data_bus

                shutdown_global_data_bus()
            except ImportError:
                logger.warning("Could not import data bus shutdown function")
            except Exception as e:
                logger.error(f"Error shutting down data bus: {e}")

        except Exception as e:
            logger.error(f"Error during shutdown sequence: {e}")

        # Exit application
        app = QApplication.instance()
        if app:
            app.quit()

    def save_complete_application_state(self) -> None:
        """Save state of all windows and tabs"""
        try:
            state_data = {
                "version": "2.0",
                "timestamp": datetime.now().isoformat(),
                "main_window": self._get_main_window_state(),
                "detached_windows": self._get_detached_windows_state(),
                "window_count": len(self.detached_windows) + 1,
                "shutdown_reason": "main_window_closed",
            }

            # Ensure logs directory exists
            session_file = Path(".logs") / "complete_session.json"
            session_file.parent.mkdir(exist_ok=True)

            with open(session_file, "w") as f:
                json.dump(state_data, f, indent=4, default=str)

            logger.info(f"Application state saved: {len(self.detached_windows) + 1} windows")

        except Exception as e:
            logger.error(f"Error saving application state: {e}")

    def _get_main_window_state(self) -> Dict:
        """Get main window state"""
        if not self.main_window:
            return {"tabs": []}

        state: Dict = {
            "window_type": "main",
            "geometry": {
                "width": self.main_window.width(),
                "height": self.main_window.height(),
                "x": self.main_window.x(),
                "y": self.main_window.y(),
            },
            "tabs": [],
        }

        # Try to get tab states if the window has the method
        if hasattr(self.main_window, "get_all_tab_states"):
            try:
                state["tabs"] = self.main_window.get_all_tab_states()
            except Exception as e:
                logger.error(f"Error getting main window tab states: {e}")
        elif hasattr(self.main_window, "tabs"):
            # Fallback: try to get states directly from tabs
            try:
                for i in range(self.main_window.tabs.count()):
                    widget = self.main_window.tabs.widget(i)
                    if widget is not None and hasattr(widget, "get_state"):
                        tab_state = widget.get_state()
                        cast(List[Dict], state["tabs"]).append(tab_state)
            except Exception as e:
                logger.error(f"Error getting tab states: {e}")

        return state

    def _get_detached_windows_state(self) -> List[Dict]:
        """Get state of all detached windows"""
        states: List[Dict] = []

        for window in self.detached_windows:
            try:
                window_state: Dict = {
                    "window_type": "detached",
                    "title": window.windowTitle(),
                    "geometry": {"width": window.width(), "height": window.height(), "x": window.x(), "y": window.y()},
                    "tabs": [],
                }

                # Get tabs from internal tab widget
                if hasattr(window, "internal_tab_widget"):
                    for i in range(window.internal_tab_widget.count()):
                        widget = window.internal_tab_widget.widget(i)
                        if widget is not None and hasattr(widget, "get_state"):
                            tab_state = widget.get_state()
                            tab_state["detached"] = True
                            cast(List[Dict], window_state["tabs"]).append(tab_state)

                states.append(window_state)

            except Exception as e:
                logger.error(f"Error getting detached window state: {e}")

        return states

    def on_detached_window_closed(self, window: "DetachedWindow", widget: QWidget) -> None:
        """Handle detached window closure"""
        self.unregister_detached_window(window)

        # If not during shutdown and we have a main window, try to reattach orphaned widgets
        if not self._shutdown_in_progress and self.main_window:
            try:
                if hasattr(self.main_window, "tabs") and widget is not None and isinstance(widget, HasGetState):
                    has_get_state_widget = cast(HasGetState, widget)
                    tab_state = has_get_state_widget.get_state()
                    tab_title = tab_state.get("tab_name", "Untitled Tab")

                    if hasattr(self.main_window.tabs, "reattach_tab"):
                        self.main_window.tabs.reattach_tab(has_get_state_widget, tab_title)
                        logger.info(f"Reattached orphaned tab: {tab_title}")

            except Exception as e:
                logger.error(f"Error reattaching orphaned tab: {e}")


# Global instance
window_hierarchy = WindowHierarchy()