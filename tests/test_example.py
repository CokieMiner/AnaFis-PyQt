"""
Example test file to verify pytest configuration.
"""

import pytest
import numpy as np
from PyQt6.QtWidgets import QWidget


def test_basic_functionality():
    """Test basic Python functionality."""
    assert 1 + 1 == 2


def test_numpy_integration():
    """Test NumPy integration."""
    arr = np.array([1, 2, 3, 4, 5])
    assert np.sum(arr) == 15
    assert arr.dtype == np.int64 or arr.dtype == np.int32  # Platform dependent


@pytest.mark.gui
def test_qt_widget_creation(qtbot):
    """Test PyQt6 widget creation."""
    widget = QWidget()
    qtbot.addWidget(widget)

    assert widget is not None
    assert not widget.isVisible()  # Widget not shown by default


def test_sample_data_fixture(sample_data):
    """Test the sample data fixture."""
    assert "x" in sample_data.columns
    assert "y" in sample_data.columns
    assert "error" in sample_data.columns
    assert len(sample_data) == 100


@pytest.mark.slow
def test_slow_operation():
    """Example of a slow test that can be skipped."""
    import time

    time.sleep(0.1)  # Simulate slow operation
    assert True
