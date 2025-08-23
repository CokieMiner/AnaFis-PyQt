import json
from pathlib import Path
from typing import Union, List

from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QTabBar, QMessageBox
from PyQt6.QtGui import QCloseEvent, QAction

from anafis.gui.shell.detachable_tab import DetachableTabWidget
from anafis.gui.shell.home_menu import HomeMenuWidget
from anafis.gui.tabs.spreadsheet_tab import SpreadsheetTab
from anafis.gui.tabs.fitting_tab import FittingTab
from anafis.gui.tabs.solver_tab import SolverTab
from anafis.gui.tabs.montecarlo_tab import MonteCarloTab
from anafis.gui.dialogs.config_dialog import ConfigDialog
from anafis.gui.dialogs.uncertainty_calculator_dialog import UncertaintyCalculatorDialog
from anafis.gui.shared.data_bus import get_global_data_bus

from anafis.core.data_structures import TabState
from anafis.core.config import ApplicationConfig


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
        if widget is not None and hasattr(widget, "get_state"):
            state = widget.get_state()
            state["tab_name"] = new_name

    def insert_home_tab(self) -> None:
        self.tabs.insertTab(0, HomeMenuWidget(self), "🏠 Home")
        self.tabs.setTabToolTip(0, "Welcome / Launcher")
        tab_bar = self.tabs.tabBar()
        if tab_bar:
            tab_bar.setTabButton(0, QTabBar.ButtonPosition.RightSide, None)

    def new_tab(self, tab_type: str) -> None:
        mapping = {
            "spreadsheet": SpreadsheetTab,
            "fitting": FittingTab,
            "solver": SolverTab,
            "montecarlo": MonteCarloTab,
        }
        if tab_type not in mapping:
            raise ValueError(f"Unknown tab type: {tab_type}")

        # Generate unique tab ID
        tab_id = f"{tab_type}_{self._tab_id_counter}"
        self._tab_id_counter += 1

        # Create widget with tab_id for data bus enabled tabs
        tab_title = f"{tab_type.capitalize()} {self._tab_id_counter}"
        if tab_type in ["spreadsheet", "fitting"]:
            widget = mapping[tab_type](tab_id=tab_id, parent=self, tab_name=tab_title)
        else:
            # For tabs not yet updated with data bus integration
            widget = mapping[tab_type](parent=self)

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
        """Handle application close event."""
        # Close all detached windows before closing main window
        self.tabs.close_all_detached_windows()
        super().closeEvent(event)

    def get_all_tab_states(self) -> list[TabState]:
        """Get state of all tabs including detached ones."""
        states: List[TabState] = []

        # Get states from main tab widget
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, "get_state"):
                state = widget.get_state()  # type: ignore
                if state.get("type") != "home":  # Skip home tab
                    states.append(state)

        # Get states from detached windows
        for detached_window in self.tabs.detached_windows:
            if hasattr(detached_window.widget, "get_state"):
                state = detached_window.widget.get_state()
                state["detached"] = True
                states.append(state)

        return states

    def save_session(self) -> None:
        """Saves the current session to a file."""
        session_file = Path(".logs") / "session.json"
        session_data = self.get_all_tab_states()
        try:
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=4)
        except Exception as e:
            print(f"Error saving session: {e}")

    def load_session(self) -> None:
        """Loads a session from a file."""
        session_file = Path(".logs") / "session.json"
        if not session_file.exists():
            return

        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)

            # Clear existing tabs (except Home)
            while self.tabs.count() > 1:
                self.tabs.removeTab(1)

            for tab_state in session_data:
                if tab_state.get("type") != "home":
                    tab_widget = self.create_tab_from_state(tab_state)
                    if tab_widget:
                        # Use tab_name from state, or default to type.capitalize() if not present
                        tab_title = tab_state.get("tab_name", tab_state.get("type").capitalize())
                        self.tabs.addTab(
                            tab_widget,
                            tab_title,
                        )
        except Exception as e:
            print(f"Error loading session: {e}")

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
                self, "Configuration Editor", "Configuration saved. Some changes might require a restart."
            )

    def _open_uncertainty_calculator(self) -> None:
        dialog = UncertaintyCalculatorDialog(self)
        dialog.show()
