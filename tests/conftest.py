"""
Pytest configuration and fixtures for ANAFIS testing.
"""

import pytest
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def qapp():
    """
    Create a QApplication instance for GUI testing.

    This fixture ensures that only one QApplication instance exists
    during the entire test session.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Set up a timer to process events during tests
    timer = QTimer()
    timer.timeout.connect(app.processEvents)
    timer.start(10)  # Process events every 10ms

    yield app

    timer.stop()
    # Don't quit the app here as it might be needed by other tests


@pytest.fixture
def qtbot(qapp, qtbot):
    """
    Enhanced qtbot fixture with additional setup.
    """
    # Ensure the application processes events
    qapp.processEvents()
    return qtbot


@pytest.fixture
def sample_data():
    """
    Provide sample data for testing scientific computations.
    """
    import numpy as np
    import pandas as pd

    # Generate sample dataset
    x = np.linspace(0, 10, 100)
    y = 2.5 * x + 1.0 + np.random.normal(0, 0.5, len(x))

    return pd.DataFrame({"x": x, "y": y, "error": np.full_like(x, 0.5)})


@pytest.fixture
def temp_config_dir(tmp_path):
    """
    Provide a temporary directory for configuration files during testing.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


# Pytest markers for test categorization
# pytest_plugins = ["pytestqt.plugin"]  # Already loaded automatically
