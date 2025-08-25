import json
import logging
from pathlib import Path
from typing import Union, List, Dict, cast, TypedDict, Optional
from datetime import datetime

from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QTabBar, QMessageBox, QApplication
from PyQt6.QtGui import QCloseEvent, QAction
from PyQt6.QtCore import QPoint

from anafis import __version__
from anafis.gui.shell.detachable_tab import DetachableTabWidget
from anafis.gui.shell.home_menu import HomeMenuWidget
from anafis.gui.tabs.spreadsheet_tab import SpreadsheetTab
from anafis.gui.tabs.fitting_tab import FittingTab
from anafis.gui.tabs.solver_tab import SolverTab
from anafis.gui.tabs.montecarlo_tab import MonteCarloTab
from anafis.gui.dialogs.config_dialog import ConfigDialog
from anafis.gui.dialogs.uncertainty_calculator_dialog import UncertaintyCalculatorDialog
from anafis.gui.shared.data_bus import get_global_data_bus

from anafis.core.data_structures import TabState, ApplicationConfig
from anafis.core.protocols import HasGetState

# Import new window hierarchy and session management
from anafis.gui.shell.drag_and_drop.window_hierarchy import window_hierarchy


class WindowState(TypedDict):
    window_type: str
    geometry: Dict[str, int]
    tabs: List[TabState]


class DetachedWindowState(WindowState):
    title: str


logger = logging.getLogger(__name__)


class SessionManager:
    """Enhanced session management with multi-window support"""

    @staticmethod
    def save_session(notebook: "Notebook") -> None:
        """Save complete session including all windows"""
        session_data = {
            "version": __version__,
            "timestamp": datetime.now().isoformat(),
            "main_window": SessionManager._get_main_window_state(notebook),
            "detached_windows": SessionManager._get_detached_windows_state(notebook),
            "application_config": SessionManager._get_app_config_state(notebook),
        }

        session_file = Path(".logs") / "complete_session.json"
        try:
            session_file.parent.mkdir(exist_ok=True)
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=4, default=str)

            logger.info(f"Complete session saved: {len(session_data['detached_windows']) + 1} windows")

        except Exception as e:
            logger.error(f"Error saving session: {e}")

    @staticmethod
    def load_session(notebook: "Notebook") -> bool:
        """Load complete session including all windows"""
        session_file = Path(".logs") / "complete_session.json"

        if not session_file.exists():
            logger.info("No complete session file found")
            return False

        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)

            # Validate session version
            version = session_data.get("version", "1.0")
            if version != __version__:
                logger.warning(f"Session version mismatch: {version}. Attempting legacy load.")
                return SessionManager._load_legacy_session(notebook, session_data)

            # Clear existing state
            SessionManager._clear_current_session(notebook)

            # Restore main window
            main_window_data = session_data.get("main_window", {})
            SessionManager._restore_main_window(notebook, main_window_data)

            # Restore detached windows
            detached_windows_data = session_data.get("detached_windows", [])
            SessionManager._restore_detached_windows(notebook, detached_windows_data)

            # Apply application config if available
            app_config_data = session_data.get("application_config")
            if app_config_data:
                SessionManager._apply_app_config(notebook, app_config_data)

            logger.info(f"Session restored: {len(detached_windows_data) + 1} windows")
            return True

        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False

    @staticmethod
    def _get_main_window_state(notebook: "Notebook") -> WindowState:
        """Get main window state"""
        tabs: List[TabState] = []
        for i in range(notebook.tabs.count()):
            widget = notebook.tabs.widget(i)
            if isinstance(widget, HasGetState):
                tab_state = widget.get_state()
                tabs.append(tab_state)

        return {
            "window_type": "main",
            "geometry": {"width": notebook.width(), "height": notebook.height(), "x": notebook.x(), "y": notebook.y()},
            "tabs": tabs,
        }

    @staticmethod
    def _get_detached_windows_state(notebook: "Notebook") -> List[DetachedWindowState]:
        """Get state of all detached windows"""
        states: List[DetachedWindowState] = []

        for window in notebook.tabs.detached_windows:
            tabs: List[TabState] = []
            for i in range(window.internal_tab_widget.count()):
                widget = window.internal_tab_widget.widget(i)
                if isinstance(widget, HasGetState):
                    tab_state = widget.get_state()
                    tab_state["detached"] = True
                    tabs.append(tab_state)

            states.append(
                {
                    "window_type": "detached",
                    "title": window.windowTitle(),
                    "geometry": {"width": window.width(), "height": window.height(), "x": window.x(), "y": window.y()},
                    "tabs": tabs,
                }
            )

        return states

    @staticmethod
    def _get_app_config_state(notebook: "Notebook") -> Dict:
        """Get application configuration state"""
        # This is a placeholder. Actual config should be retrieved from notebook._config
        return {
            "theme": getattr(notebook._config.interface, "theme", "system"),
            "window_behavior": {"cascade_offset": [30, 30], "default_detached_size": [800, 600]},
        }

    @staticmethod
    def _clear_current_session(notebook: "Notebook") -> None:
        """Clear current session state"""
        # Close all detached windows
        notebook.tabs.close_all_detached_windows()

        # Clear main window tabs (except Home)
        while notebook.tabs.count() > 1:
            notebook.tabs.removeTab(1)

    @staticmethod
    def _restore_main_window(notebook: "Notebook", main_window_data: Dict) -> None:
        """Restore main window state"""
        # Apply geometry if available
        geometry = main_window_data.get("geometry", {})
        if geometry:
            # Only apply size, not position (let OS decide position)
            width = geometry.get("width", 1200)
            height = geometry.get("height", 800)
            notebook.resize(width, height)

        # Restore tabs
        tabs_data = main_window_data.get("tabs", [])
        for tab_state in tabs_data:
            if tab_state.get("type") != "home":  # Skip home tab
                try:
                    tab_widget = notebook.create_tab_from_state(cast(TabState, tab_state))  # Cast to TabState
                    if tab_widget:
                        tab_type = tab_state.get("type")
                        tab_title = tab_state.get("tab_name", tab_type.capitalize() if tab_type is not None else "")
                        notebook.tabs.addTab(tab_widget, tab_title)
                except Exception as e:
                    logger.error(f"Error restoring tab: {e}")

    @staticmethod
    def _restore_detached_windows(notebook: "Notebook", detached_windows_data: List[Dict]) -> None:
        """Restore detached windows"""
        screen = QApplication.primaryScreen()
        if screen is None:  # Added check for None
            return  # Cannot restore if screen is None

        screen_geometry = screen.geometry()

        for i, window_data in enumerate(detached_windows_data):
            tabs_data = window_data.get("tabs", [])

            if not tabs_data:
                continue

            try:
                # Create widgets for tabs
                widgets_and_titles = []
                for tab_state in tabs_data:
                    tab_widget = notebook.create_tab_from_state(cast(TabState, tab_state))  # Cast to TabState
                    if tab_widget:
                        tab_type = tab_state.get("type")
                        tab_title = tab_state.get("tab_name", tab_type.capitalize() if tab_type is not None else "")
                        widgets_and_titles.append((tab_widget, tab_title))

                if widgets_and_titles:
                    # Create detached window with first tab
                    first_widget, first_title = widgets_and_titles[0]
                    detached_window = notebook.tabs.window_manager.create_detached_window_at_position(
                        first_widget, first_title, QPoint(0, 0)  # Position will be set by geometry
                    )

                    # Add remaining tabs
                    for widget, title in widgets_and_titles[1:]:
                        detached_window.internal_tab_widget.addTab(widget, title)

                    # Apply geometry with screen bounds checking
                    geometry = window_data.get("geometry", {})
                    if geometry:
                        width = max(400, min(geometry.get("width", 800), screen_geometry.width() - 100))
                        height = max(300, min(geometry.get("height", 600), screen_geometry.height() - 100))
                        detached_window.resize(width, height)

                        # Position with cascade fallback
                        x = geometry.get("x", 100 + (i * 30))
                        y = geometry.get("y", 100 + (i * 30))

                        # Ensure on screen
                        x = max(0, min(x, screen_geometry.width() - width))
                        y = max(0, min(y, screen_geometry.height() - height))

                        detached_window.move(x, y)

                    # Register and show
                    notebook.tabs.detached_windows.append(detached_window)
                    window_hierarchy.register_detached_window(detached_window)
                    detached_window.show()

            except Exception as e:
                logger.error(f"Error restoring detached window: {e}")

    @staticmethod
    def _load_legacy_session(notebook: "Notebook", session_data: List[Dict]) -> bool:
        """Loads a legacy session from a file (version 1.0)."""
        logger.info("Loading legacy session...")
        try:
            # Clear existing tabs (except Home)
            while notebook.tabs.count() > 1:
                notebook.tabs.removeTab(1)

            for tab_state in session_data:
                if tab_state.get("type") != "home":
                    tab_widget = notebook.create_tab_from_state(cast(TabState, tab_state))  # Cast to TabState
                    if tab_widget:
                        tab_type = tab_state.get("type")
                        tab_title = tab_state.get("tab_name", tab_type.capitalize() if tab_type is not None else "")
                        notebook.tabs.addTab(
                            tab_widget,
                            tab_title,
                        )
            logger.info("Legacy session loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Error loading legacy session: {e}")
            return False

    @staticmethod
    def _apply_app_config(notebook: "Notebook", app_config_data: Dict) -> None:
        """Applies application configuration from session data."""
        # This is a placeholder for applying config. Implement actual logic here.
        logger.info(f"Applying application config from session: {app_config_data}")
        # Example: update theme if it's in config
        # if "theme" in app_config_data:
        #     notebook._config.interface.theme = app_config_data["theme"]


class Notebook(QMainWindow):

    def __init__(self, config: ApplicationConfig) -> None:
        super().__init__()
        self.setWindowTitle("ANAFIS - Workbook")
        self._config = config
        self.tabs = DetachableTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.tab_renamed.connect(self._handle_tab_renamed)
        self.setCentralWidget(self.tabs)
        self.insert_home_tab()

        # Register with window hierarchy
        window_hierarchy.register_main_window(self)

        # Enhanced session management
        self.session_manager = SessionManager()

        # Create menu bar
        menu_bar = self.menuBar()
        if menu_bar:
            # Project Menu
            project_menu = menu_bar.addMenu("&Project")
            if project_menu:
                new_project_action = QAction("&New Project", self)
                new_project_action.triggered.connect(self._new_project_placeholder)
                project_menu.addAction(new_project_action)

                project_menu.addSeparator()

                open_project_action = QAction("&Open Project", self)
                open_project_action.triggered.connect(self._open_project_placeholder)
                project_menu.addAction(open_project_action)

                save_project_action = QAction("&Save Project", self)
                save_project_action.triggered.connect(self._save_project_placeholder)
                project_menu.addAction(save_project_action)

                save_as_project_action = QAction("Save &As Project...", self)
                save_as_project_action.triggered.connect(self._save_as_project_placeholder)
                project_menu.addAction(save_as_project_action)

                project_menu.addSeparator()

            # New Tab Menu
            new_spreadsheet_action = QAction("New &Spreadsheet Tab", self)
            new_spreadsheet_action.triggered.connect(lambda: self.new_tab("spreadsheet"))
            menu_bar.addAction(new_spreadsheet_action)

            new_fitting_action = QAction("New &Fitting Tab", self)
            new_fitting_action.triggered.connect(lambda: self.new_tab("fitting"))
            menu_bar.addAction(new_fitting_action)

            new_solver_action = QAction("New S&olver Tab", self)
            new_solver_action.triggered.connect(lambda: self.new_tab("solver"))
            menu_bar.addAction(new_solver_action)

            new_montecarlo_action = QAction("New &Monte Carlo Tab", self)
            new_montecarlo_action.triggered.connect(lambda: self.new_tab("montecarlo"))
            menu_bar.addAction(new_montecarlo_action)

            new_uncertainty_action = QAction("&Uncertainty Calculator", self)
            new_uncertainty_action.triggered.connect(self._open_uncertainty_calculator)
            menu_bar.addAction(new_uncertainty_action)

            # Settings Action
            open_config_action = QAction("&Settings", self)
            open_config_action.triggered.connect(self._open_config_editor_placeholder)
            menu_bar.addAction(open_config_action)

        # Tab ID counter for unique identification
        self._tab_id_counter = 1

        # Set minimum window size
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

    def _handle_tab_renamed(self, index: int, new_name: str) -> None:
        widget = self.tabs.widget(index)
        if widget is not None and hasattr(widget, "set_tab_name"):
            widget.set_tab_name(new_name)

        # Update the tab's state in the session data if it's a persistent tab
        if widget is not None and isinstance(widget, HasGetState):
            state = widget.get_state()
            state["tab_name"] = new_name

    def insert_home_tab(self) -> None:
        self.tabs.insertTab(0, HomeMenuWidget(self), "🏠 Home")
        self.tabs.setTabToolTip(0, "Welcome / Launcher")
        tab_bar = self.tabs.tabBar()
        if tab_bar:
            tab_bar.setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

    def new_tab(self, tab_type: str) -> None:
        # Generate unique tab ID
        tab_id = f"{tab_type}_{self._tab_id_counter}"
        self._tab_id_counter += 1

        # Create widget with tab_id for data bus enabled tabs
        tab_title = f"{tab_type.capitalize()} {self._tab_id_counter}"
        widget: Optional[Union[SpreadsheetTab, FittingTab, SolverTab, MonteCarloTab]] = None
        if tab_type == "spreadsheet":
            widget = SpreadsheetTab(tab_id=tab_id, parent=self, tab_name=tab_title)
        elif tab_type == "fitting":
            widget = FittingTab(tab_id=tab_id, parent=self, tab_name=tab_title)
        elif tab_type == "solver":
            widget = SolverTab(parent=self)
        elif tab_type == "montecarlo":
            widget = MonteCarloTab(parent=self)
        else:
            logger.error(f"Unknown tab type: {tab_type}")
            return

        if widget:
            idx = self.tabs.addTab(widget, tab_title)
            self.tabs.setCurrentIndex(idx)

    def create_tab_from_state(self, state: TabState) -> Union[QWidget, QLabel]:
        tab_type = state.get("type")
        tab_name = state.get("tab_name")

        # Use existing tab_id from state or generate new one
        tab_id = state.get("tab_id", f"{tab_type}_{self._tab_id_counter}")
        if "tab_id" not in state:
            self._tab_id_counter += 1

        if tab_type == "spreadsheet":
            return SpreadsheetTab(tab_id=tab_id, parent=self, tab_name=tab_name)
        elif tab_type == "fitting":
            return FittingTab(tab_id=tab_id, parent=self, tab_name=tab_name)
        elif tab_type == "solver":
            return SolverTab(parent=self)
        elif tab_type == "montecarlo":
            return MonteCarloTab(parent=self)
        else:
            return QLabel(f"Unknown Tab Type: {tab_type}")  # Fallback

    def close_tab(self, index: int) -> None:
        if index != 0:  # protect Home
            self.tabs.removeTab(index)

    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Enhanced close event with complete state saving"""
        # Save complete session before closing
        self.session_manager.save_session(self)

        # Let window hierarchy handle the shutdown
        window_hierarchy.initiate_application_shutdown()

        super().closeEvent(event)

    def get_all_tab_states(self) -> list[TabState]:
        """Get state of all tabs including detached ones."""
        states: List[TabState] = []

        # Get states from main tab widget
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if widget is not None and isinstance(widget, HasGetState):
                state = widget.get_state()
                if state.get("type") != "home":  # Skip home tab
                    states.append(state)

        # The detached windows are now managed by window_hierarchy and their states are retrieved via SessionManager
        return states

    def save_session(self) -> None:
        """Saves the current session to a file."""
        self.session_manager.save_session(self)

    def load_session(self) -> None:
        """Loads a session from a file."""
        self.session_manager.load_session(self)

    def _open_project_placeholder(self) -> None:
        QMessageBox.information(self, "Open Project", "Open Project functionality will be implemented here.")

    def _new_project_placeholder(self) -> None:
        QMessageBox.information(self, "New Project", "New Project functionality will be implemented here.")

    def _save_project_placeholder(self) -> None:
        QMessageBox.information(self, "Save Project", "Save Project functionality will be implemented here.")

    def _save_as_project_placeholder(self) -> None:
        QMessageBox.information(self, "Save As Project", "Save As Project functionality will be implemented here.")

    def _open_app_stats_placeholder(self) -> None:
        QMessageBox.information(self, "App Stats", "Application statistics will be displayed here.")

    def _open_config_editor_placeholder(self) -> None:
        dialog = ConfigDialog(self._config, self)
        if dialog.exec():
            new_config = dialog.get_new_config()
            self._config = new_config  # Update the Notebook's config reference
            # Publish config update via DataBus
            data_bus = get_global_data_bus()
            data_bus.publish_data(
                source_tab_id="notebook",  # A unique ID for the Notebook
                data_type="config_updated",
                data=new_config,  # Pass the new config object
                metadata={"description": "Application configuration updated"},
            )
            QMessageBox.information(
                self,
                "Configuration Editor",
                "Configuration saved. Some changes might require a restart.",
            )

    def _open_uncertainty_calculator(self) -> None:
        dialog = UncertaintyCalculatorDialog(self)
        dialog.show()
