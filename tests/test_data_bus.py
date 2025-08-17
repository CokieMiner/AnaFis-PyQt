"""
Test cases for data bus and inter-tab communication.

Tests cover data transformation, bus functionality, and end-to-end
data flow between different tab types.
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from anafis.gui.shared.data_transforms import (
    create_data_message, serialize_dataframe, deserialize_dataframe,
    serialize_numpy_array, deserialize_numpy_array,
    transform_spreadsheet_to_fitting, transform_montecarlo_to_fitting,
    validate_data_message, extract_numerical_columns, get_data_summary,
    DataPayload, TabData
)

from anafis.gui.shared.data_bus import (
    DataBus, TabRegistration, get_global_data_bus
)


class TestDataTransforms(unittest.TestCase):
    """Test data transformation utilities."""

    def setUp(self):
        """Set up test data."""
        self.sample_df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10],
            'weights': [1.0, 1.2, 0.8, 1.1, 0.9],
            'category': ['A', 'B', 'A', 'B', 'A']
        })
        
        self.sample_array = np.array([[1, 2, 3], [4, 5, 6]])

    def test_create_data_message(self):
        """Test data message creation."""
        message = create_data_message(
            source_tab_id="tab1",
            source_tab_type="spreadsheet",
            data_type="dataframe",
            data=self.sample_df,
            metadata={"description": "test data"}
        )
        
        self.assertEqual(message["source_tab_id"], "tab1")
        self.assertEqual(message["source_tab_type"], "spreadsheet")
        self.assertEqual(message["data_type"], "dataframe")
        self.assertEqual(message["version"], "1.0")
        self.assertIn("timestamp", message)
        self.assertEqual(message["metadata"]["description"], "test data")

    def test_dataframe_serialization_roundtrip(self):
        """Test DataFrame serialization and deserialization."""
        serialized = serialize_dataframe(self.sample_df)
        
        # Check serialized structure
        self.assertEqual(serialized["type"], "dataframe")
        self.assertIn("data", serialized)
        self.assertIn("columns", serialized)
        self.assertIn("dtypes", serialized)
        self.assertIn("shape", serialized)
        
        # Test roundtrip
        deserialized = deserialize_dataframe(serialized)
        
        # Check basic properties
        self.assertEqual(deserialized.shape, self.sample_df.shape)
        self.assertListEqual(list(deserialized.columns), list(self.sample_df.columns))
        
        # Check data equality (allowing for type changes)
        pd.testing.assert_frame_equal(
            deserialized.reset_index(drop=True), 
            self.sample_df.reset_index(drop=True),
            check_dtype=False  # Allow type changes during serialization
        )

    def test_numpy_array_serialization_roundtrip(self):
        """Test NumPy array serialization and deserialization."""
        serialized = serialize_numpy_array(self.sample_array)
        
        # Check serialized structure
        self.assertEqual(serialized["type"], "numpy_array")
        self.assertIn("data", serialized)
        self.assertIn("dtype", serialized)
        self.assertIn("shape", serialized)
        
        # Test roundtrip
        deserialized = deserialize_numpy_array(serialized)
        
        # Check properties
        self.assertEqual(deserialized.shape, self.sample_array.shape)
        np.testing.assert_array_equal(deserialized, self.sample_array)

    def test_transform_spreadsheet_to_fitting(self):
        """Test spreadsheet to fitting data transformation."""
        result = transform_spreadsheet_to_fitting(
            self.sample_df,
            x_column='x',
            y_column='y',
            weights_column='weights'
        )
        
        self.assertEqual(result["type"], "fitting_data")
        self.assertIn("data", result)
        self.assertIn("source_columns", result)
        self.assertIn("original_shape", result)
        self.assertIn("cleaned_shape", result)
        
        # Check source column mapping
        self.assertEqual(result["source_columns"]["x"], "x")
        self.assertEqual(result["source_columns"]["y"], "y")
        self.assertEqual(result["source_columns"]["weights"], "weights")
        
        # Check data structure
        fitting_df = deserialize_dataframe(result["data"])
        self.assertIn("x", fitting_df.columns)
        self.assertIn("y", fitting_df.columns)
        self.assertIn("weights", fitting_df.columns)

    def test_transform_spreadsheet_to_fitting_missing_columns(self):
        """Test error handling for missing columns in transformation."""
        with self.assertRaises(ValueError):
            transform_spreadsheet_to_fitting(
                self.sample_df,
                x_column='missing',
                y_column='y'
            )

    def test_transform_montecarlo_to_fitting(self):
        """Test Monte Carlo to fitting data transformation."""
        montecarlo_results = {
            "simulation_data": serialize_dataframe(self.sample_df),
            "parameters": {"iterations": 1000, "seed": 42}
        }
        
        result = transform_montecarlo_to_fitting(montecarlo_results)
        
        self.assertEqual(result["type"], "fitting_data")
        self.assertEqual(result["source_type"], "montecarlo")
        self.assertIn("data", result)
        self.assertIn("simulation_parameters", result)
        self.assertEqual(result["simulation_parameters"]["iterations"], 1000)

    def test_validate_data_message_valid(self):
        """Test validation of valid data messages."""
        message = create_data_message(
            source_tab_id="tab1",
            source_tab_type="spreadsheet",
            data_type="dataframe",
            data={"test": "data"}
        )
        
        is_valid, errors = validate_data_message(message)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_data_message_invalid(self):
        """Test validation of invalid data messages."""
        invalid_message = {
            "source_tab_id": "tab1",
            # Missing required fields
            "data": "some data"
        }
        
        is_valid, errors = validate_data_message(invalid_message)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_extract_numerical_columns(self):
        """Test extraction of numerical columns from DataFrame."""
        numerical_cols = extract_numerical_columns(self.sample_df)
        
        # Should include x, y, weights (numerical)
        # Should exclude category (string)
        expected_cols = ['x', 'y', 'weights']
        for col in expected_cols:
            self.assertIn(col, numerical_cols)
        self.assertNotIn('category', numerical_cols)

    def test_get_data_summary(self):
        """Test data summary generation."""
        # Test DataFrame summary
        df_summary = get_data_summary(self.sample_df)
        self.assertEqual(df_summary["type"], "DataFrame")
        self.assertEqual(df_summary["shape"], (5, 4))
        self.assertIn("columns", df_summary)
        self.assertIn("dtypes", df_summary)
        
        # Test NumPy array summary
        array_summary = get_data_summary(self.sample_array)
        self.assertEqual(array_summary["type"], "ndarray")
        self.assertEqual(array_summary["shape"], (2, 3))
        self.assertIn("dtype", array_summary)
        
        # Test dict summary
        test_dict = {"key1": "value1", "key2": "value2"}
        dict_summary = get_data_summary(test_dict)
        self.assertEqual(dict_summary["type"], "dict")
        self.assertEqual(dict_summary["num_items"], 2)
        self.assertIn("keys", dict_summary)


class TestDataBus(unittest.TestCase):
    """Test data bus functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
            
        self.data_bus = DataBus()
        self.sample_data = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })

    def tearDown(self):
        """Clean up after tests."""
        self.data_bus.shutdown()

    def test_data_bus_initialization(self):
        """Test data bus initialization."""
        self.assertTrue(self.data_bus.is_active)
        self.assertEqual(len(self.data_bus.registered_tabs), 0)
        self.assertEqual(len(self.data_bus.message_history), 0)

    def test_tab_registration(self):
        """Test tab registration and unregistration."""
        # Test successful registration
        success = self.data_bus.register_tab("tab1", "spreadsheet")
        self.assertTrue(success)
        self.assertIn("tab1", self.data_bus.registered_tabs)
        
        # Test registration info
        tab_info = self.data_bus.get_registered_tabs()
        self.assertIn("tab1", tab_info)
        self.assertEqual(tab_info["tab1"]["tab_type"], "spreadsheet")
        self.assertTrue(tab_info["tab1"]["is_active"])
        
        # Test unregistration
        success = self.data_bus.unregister_tab("tab1")
        self.assertTrue(success)
        self.assertNotIn("tab1", self.data_bus.registered_tabs)

    def test_tab_registration_with_callback(self):
        """Test tab registration with callback function."""
        callback_called = False
        received_message = None
        
        def test_callback(message):
            nonlocal callback_called, received_message
            callback_called = True
            received_message = message
        
        # Register tab with callback
        self.data_bus.register_tab("tab1", "spreadsheet", callback=test_callback)
        self.data_bus.register_tab("tab2", "fitting")
        
        # Subscribe tab2 to dataframe data
        self.data_bus.subscribe_to_data_type("tab1", "dataframe")
        
        # Publish data from tab2
        success = self.data_bus.publish_data(
            source_tab_id="tab2",
            data_type="dataframe",
            data=serialize_dataframe(self.sample_data)
        )
        
        self.assertTrue(success)
        # Note: callback should be called for tab1 if subscribed

    def test_data_subscription(self):
        """Test data type subscriptions."""
        # Register tabs
        self.data_bus.register_tab("tab1", "spreadsheet")
        self.data_bus.register_tab("tab2", "fitting")
        
        # Test subscription
        success = self.data_bus.subscribe_to_data_type("tab1", "dataframe")
        self.assertTrue(success)
        
        # Test duplicate subscription
        success = self.data_bus.subscribe_to_data_type("tab1", "dataframe")
        self.assertFalse(success)
        
        # Test unsubscription
        success = self.data_bus.unsubscribe_from_data_type("tab1", "dataframe")
        self.assertTrue(success)
        
        # Test unsubscription of non-existent subscription
        success = self.data_bus.unsubscribe_from_data_type("tab1", "dataframe")
        self.assertFalse(success)

    def test_data_publishing(self):
        """Test data publishing functionality."""
        # Register a tab
        self.data_bus.register_tab("tab1", "spreadsheet")
        
        # Test successful publishing
        success = self.data_bus.publish_data(
            source_tab_id="tab1",
            data_type="dataframe",
            data=serialize_dataframe(self.sample_data),
            metadata={"test": "metadata"}
        )
        
        self.assertTrue(success)
        
        # Check message history
        history = self.data_bus.get_message_history()
        self.assertEqual(len(history), 1)
        
        message = history[0]
        self.assertEqual(message["source_tab_id"], "tab1")
        self.assertEqual(message["data_type"], "dataframe")
        self.assertEqual(message["metadata"]["test"], "metadata")

    def test_data_publishing_unregistered_tab(self):
        """Test data publishing from unregistered tab fails."""
        success = self.data_bus.publish_data(
            source_tab_id="nonexistent",
            data_type="dataframe",
            data=serialize_dataframe(self.sample_data)
        )
        
        self.assertFalse(success)

    def test_data_filtering(self):
        """Test data filtering functionality."""
        # Register tab
        self.data_bus.register_tab("tab1", "spreadsheet")
        
        # Add a filter that blocks all data
        def block_all_filter(message):
            return False
        
        self.data_bus.add_data_filter("block_all", block_all_filter)
        
        # Try to publish data
        success = self.data_bus.publish_data(
            source_tab_id="tab1",
            data_type="dataframe",
            data=serialize_dataframe(self.sample_data)
        )
        
        # Publishing should succeed but data should be filtered
        self.assertFalse(success)
        
        # Remove filter
        removed = self.data_bus.remove_data_filter("block_all")
        self.assertTrue(removed)
        
        # Now publishing should work
        success = self.data_bus.publish_data(
            source_tab_id="tab1",
            data_type="dataframe",
            data=serialize_dataframe(self.sample_data)
        )
        self.assertTrue(success)

    def test_message_history_management(self):
        """Test message history management."""
        # Register tab
        self.data_bus.register_tab("tab1", "spreadsheet")
        
        # Set small history limit for testing
        self.data_bus.max_message_history = 2
        
        # Publish multiple messages
        for i in range(3):
            self.data_bus.publish_data(
                source_tab_id="tab1",
                data_type="test",
                data=f"message_{i}"
            )
        
        # Check history is limited
        history = self.data_bus.get_message_history()
        self.assertEqual(len(history), 2)
        
        # Check it kept the most recent messages
        self.assertIn("message_1", str(history[0]["data"]))
        self.assertIn("message_2", str(history[1]["data"]))

    def test_bus_statistics(self):
        """Test bus statistics functionality."""
        # Register tabs
        self.data_bus.register_tab("tab1", "spreadsheet")
        self.data_bus.register_tab("tab2", "fitting")
        
        # Subscribe to data
        self.data_bus.subscribe_to_data_type("tab1", "dataframe")
        self.data_bus.subscribe_to_data_type("tab2", "parameters")
        
        # Publish some data
        self.data_bus.publish_data("tab1", "dataframe", serialize_dataframe(self.sample_data))
        
        # Get statistics
        stats = self.data_bus.get_bus_statistics()
        
        self.assertTrue(stats["is_active"])
        self.assertEqual(stats["total_registered_tabs"], 2)
        self.assertEqual(stats["active_tabs"], 2)
        self.assertEqual(stats["total_messages_processed"], 1)
        self.assertEqual(stats["total_subscriptions"], 2)

    def test_bus_shutdown(self):
        """Test proper bus shutdown."""
        # Register tabs and add data
        self.data_bus.register_tab("tab1", "spreadsheet")
        self.data_bus.publish_data("tab1", "test", "data")
        
        # Shutdown
        self.data_bus.shutdown()
        
        # Verify cleanup
        self.assertFalse(self.data_bus.is_active)
        self.assertEqual(len(self.data_bus.registered_tabs), 0)
        self.assertEqual(len(self.data_bus.message_history), 0)


class TestEndToEndDataFlow(unittest.TestCase):
    """Test end-to-end data flow between different tab types."""

    def setUp(self):
        """Set up test environment."""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
            
        self.data_bus = DataBus()
        
        # Create sample data
        self.spreadsheet_data = pd.DataFrame({
            'time': [0, 1, 2, 3, 4, 5],
            'temperature': [20.0, 25.3, 30.1, 28.7, 26.2, 23.8],
            'pressure': [1.01, 1.05, 1.08, 1.06, 1.03, 1.02],
            'quality': ['good', 'good', 'fair', 'good', 'good', 'fair']
        })

    def tearDown(self):
        """Clean up after tests."""
        self.data_bus.shutdown()

    def test_spreadsheet_to_fitting_flow(self):
        """Test data flow from spreadsheet to fitting tab."""
        received_messages = []
        
        def fitting_callback(message):
            received_messages.append(message)
        
        # Register tabs
        self.data_bus.register_tab("spreadsheet_1", "spreadsheet")
        self.data_bus.register_tab("fitting_1", "fitting", callback=fitting_callback)
        
        # Subscribe fitting tab to fitting data
        self.data_bus.subscribe_to_data_type("fitting_1", "fitting_data")
        
        # Transform and publish data from spreadsheet
        fitting_data = transform_spreadsheet_to_fitting(
            self.spreadsheet_data,
            x_column='time',
            y_column='temperature'
        )
        
        success = self.data_bus.publish_data(
            source_tab_id="spreadsheet_1",
            data_type="fitting_data",
            data=fitting_data,
            metadata={"transformation": "spreadsheet_to_fitting"}
        )
        
        self.assertTrue(success)
        
        # Verify fitting tab received the data
        self.assertEqual(len(received_messages), 1)
        message = received_messages[0]
        
        self.assertEqual(message["source_tab_type"], "spreadsheet")
        self.assertEqual(message["data_type"], "fitting_data")
        self.assertIn("transformation", message["metadata"])

    def test_multiple_tab_data_flow(self):
        """Test data flow between multiple tabs."""
        # Track received messages per tab
        received_by_tab = {
            "fitting_1": [],
            "solver_1": [],
            "montecarlo_1": []
        }
        
        def create_callback(tab_id):
            def callback(message):
                received_by_tab[tab_id].append(message)
            return callback
        
        # Register multiple tabs
        self.data_bus.register_tab("spreadsheet_1", "spreadsheet")
        self.data_bus.register_tab("fitting_1", "fitting", 
                                 callback=create_callback("fitting_1"))
        self.data_bus.register_tab("solver_1", "solver", 
                                 callback=create_callback("solver_1"))
        self.data_bus.register_tab("montecarlo_1", "montecarlo", 
                                 callback=create_callback("montecarlo_1"))
        
        # Set up subscriptions
        self.data_bus.subscribe_to_data_type("fitting_1", "fitting_data")
        self.data_bus.subscribe_to_data_type("solver_1", "fitting_data")
        self.data_bus.subscribe_to_data_type("montecarlo_1", "dataframe")
        
        # Publish fitting data from spreadsheet
        fitting_data = transform_spreadsheet_to_fitting(
            self.spreadsheet_data,
            x_column='time',
            y_column='temperature'
        )
        
        self.data_bus.publish_data(
            source_tab_id="spreadsheet_1",
            data_type="fitting_data",
            data=fitting_data
        )
        
        # Publish raw dataframe data
        self.data_bus.publish_data(
            source_tab_id="spreadsheet_1",
            data_type="dataframe",
            data=serialize_dataframe(self.spreadsheet_data)
        )
        
        # Verify correct routing
        self.assertEqual(len(received_by_tab["fitting_1"]), 1)  # Got fitting_data
        self.assertEqual(len(received_by_tab["solver_1"]), 1)   # Got fitting_data
        self.assertEqual(len(received_by_tab["montecarlo_1"]), 1)  # Got dataframe

    def test_data_transformation_chain(self):
        """Test a chain of data transformations between tabs."""
        transformation_chain = []
        
        def track_transformations(tab_id):
            def callback(message):
                transformation_chain.append({
                    "receiver": tab_id,
                    "source": message["source_tab_id"],
                    "data_type": message["data_type"]
                })
            return callback
        
        # Register tabs
        self.data_bus.register_tab("spreadsheet_1", "spreadsheet")
        self.data_bus.register_tab("fitting_1", "fitting", 
                                 callback=track_transformations("fitting_1"))
        self.data_bus.register_tab("montecarlo_1", "montecarlo", 
                                 callback=track_transformations("montecarlo_1"))
        
        # Set up subscription chain
        self.data_bus.subscribe_to_data_type("fitting_1", "fitting_data")
        self.data_bus.subscribe_to_data_type("montecarlo_1", "fitting_data")
        
        # Start the chain: Spreadsheet -> Fitting
        fitting_data = transform_spreadsheet_to_fitting(
            self.spreadsheet_data,
            x_column='time',
            y_column='temperature'
        )
        
        self.data_bus.publish_data(
            source_tab_id="spreadsheet_1",
            data_type="fitting_data",
            data=fitting_data
        )
        
        # Simulate fitting tab processing and sending results
        fitting_results = {
            "model_type": "linear",
            "coefficients": [1.2, 0.8],
            "r_squared": 0.95,
            "residuals": [0.1, -0.2, 0.15, -0.1, 0.05, 0.0]
        }
        
        self.data_bus.publish_data(
            source_tab_id="fitting_1",
            data_type="fitting_results",
            data=fitting_results
        )
        
        # Verify the transformation chain
        self.assertEqual(len(transformation_chain), 2)
        
        # Check first transformation: spreadsheet -> fitting
        first_step = transformation_chain[0]
        self.assertEqual(first_step["receiver"], "fitting_1")
        self.assertEqual(first_step["source"], "spreadsheet_1")
        self.assertEqual(first_step["data_type"], "fitting_data")
        
        # Check second transformation: fitting -> montecarlo
        second_step = transformation_chain[1]
        self.assertEqual(second_step["receiver"], "montecarlo_1")
        self.assertEqual(second_step["source"], "spreadsheet_1")


if __name__ == '__main__':
    unittest.main()
