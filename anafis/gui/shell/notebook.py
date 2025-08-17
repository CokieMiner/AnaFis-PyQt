from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget
from PyQt6.QtGui import QCloseEvent
from typing import Optional, Dict, Any, Union
from anafis.gui.shell.detachable_tab import DetachableTabWidget
from anafis.gui.shell.home_menu import HomeMenuWidget
from anafis.gui.tabs.spreadsheet_tab import SpreadsheetTab
from anafis.gui.tabs.fitting_tab import FittingTab
from anafis.gui.tabs.solver_tab import SolverTab
from anafis.gui.tabs.montecarlo_tab import MonteCarloTab


class Notebook(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ANAFIS – Workbook")
        self.tabs = DetachableTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)
        self.insert_home_tab()

        # Tab ID counter for unique identification
        self._tab_id_counter = 1

        # Set minimum window size
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

    def insert_home_tab(self) -> None:
        self.tabs.insertTab(0, HomeMenuWidget(self), "🏠 Home")
        self.tabs.setTabToolTip(0, "Welcome / Launcher")

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
        if tab_type in ["spreadsheet", "fitting"]:
            widget = mapping[tab_type](tab_id=tab_id, parent=self)
        else:
            # For tabs not yet updated with data bus integration
            widget = mapping[tab_type](parent=self)

        tab_title = f"{tab_type.capitalize()} {self._tab_id_counter - 1}"
        idx = self.tabs.addTab(widget, tab_title)
        self.tabs.setCurrentIndex(idx)

    def create_tab_from_state(self, state: Dict[str, Any]) -> Union[QWidget, QLabel]:
        tab_type = state.get("type")
        
        # Use existing tab_id from state or generate new one
        tab_id = state.get("tab_id", f"{tab_type}_{self._tab_id_counter}")
        if "tab_id" not in state:
            self._tab_id_counter += 1
        
        if tab_type == "spreadsheet":
            return SpreadsheetTab(tab_id=tab_id, parent=self)
        elif tab_type == "fitting":
            return FittingTab(tab_id=tab_id, parent=self)
        elif tab_type == "solver":
            return SolverTab(parent=self)
        elif tab_type == "montecarlo":
            return MonteCarloTab(parent=self)
        else:
            return QLabel(f"Unknown Tab Type: {tab_type}")  # Fallback

    def close_tab(self, index: int) -> None:
        if index != 0:  # protect Home
            self.tabs.removeTab(index)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle application close event."""
        # Close all detached windows before closing main window
        self.tabs.close_all_detached_windows()
        super().closeEvent(event)

    def get_all_tab_states(self) -> list[Dict[str, Any]]:
        """Get state of all tabs including detached ones."""
        states = []

        # Get states from main tab widget
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, "get_state"):
                state = widget.get_state()
                if state.get("type") != "home":  # Skip home tab
                    states.append(state)

        # Get states from detached windows
        for detached_window in self.tabs.detached_windows:
            if hasattr(detached_window.widget, "get_state"):
                state = detached_window.widget.get_state()
                state["detached"] = True
                states.append(state)

        return states
