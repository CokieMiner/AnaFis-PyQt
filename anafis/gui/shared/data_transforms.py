"""
Functional data transformation utilities for ANAFIS data bus.

This module provides pure functions for transforming data between different
tab formats while maintaining data integrity and type safety.
"""

import json
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path


# Data format definitions
DataPayload = Dict[str, Any]
TabData = Union[pd.DataFrame, Dict[str, Any], List[Any], str, float, int]


def create_data_message(
    source_tab_id: str,
    source_tab_type: str,
    data_type: str,
    data: TabData,
    metadata: Optional[Dict[str, Any]] = None,
) -> DataPayload:
    """
    Create a standardized data message for the data bus.

    Args:
        source_tab_id: Unique identifier of the source tab
        source_tab_type: Type of source tab (spreadsheet, fitting, etc.)
        data_type: Type of data being sent (dataframe, parameters, results, etc.)
        data: The actual data payload
        metadata: Optional metadata about the data

    Returns:
        Standardized data message dictionary
    """
    return {
        "source_tab_id": source_tab_id,
        "source_tab_type": source_tab_type,
        "data_type": data_type,
        "data": data,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat(),
        "version": "1.0",
    }


def serialize_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Serialize a pandas DataFrame for data bus transmission.

    Args:
        df: DataFrame to serialize

    Returns:
        Serialized DataFrame data
    """
    return {
        "type": "dataframe",
        "data": df.to_dict("records"),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "index": df.index.tolist(),
        "shape": df.shape,
    }


def deserialize_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Deserialize DataFrame data from data bus message.

    Args:
        data: Serialized DataFrame data

    Returns:
        Reconstructed pandas DataFrame
    """
    if data.get("type") != "dataframe":
        raise ValueError("Data is not a serialized DataFrame")

    df = pd.DataFrame(data["data"])
    
    # Restore column order
    if "columns" in data:
        df = df.reindex(columns=data["columns"])
    
    # Restore data types where possible
    if "dtypes" in data:
        for col, dtype_str in data["dtypes"].items():
            if col in df.columns:
                try:
                    if dtype_str.startswith("int"):
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    elif dtype_str.startswith("float"):
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    elif dtype_str == "bool":
                        df[col] = df[col].astype(bool, errors="ignore")
                    elif dtype_str.startswith("datetime"):
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                except (ValueError, TypeError):
                    # Keep original data if conversion fails
                    pass
    
    return df


def serialize_numpy_array(arr: np.ndarray) -> Dict[str, Any]:
    """
    Serialize a numpy array for data bus transmission.

    Args:
        arr: NumPy array to serialize

    Returns:
        Serialized array data
    """
    return {
        "type": "numpy_array",
        "data": arr.tolist(),
        "dtype": str(arr.dtype),
        "shape": arr.shape,
    }


def deserialize_numpy_array(data: Dict[str, Any]) -> np.ndarray:
    """
    Deserialize numpy array from data bus message.

    Args:
        data: Serialized array data

    Returns:
        Reconstructed numpy array
    """
    if data.get("type") != "numpy_array":
        raise ValueError("Data is not a serialized numpy array")

    arr = np.array(data["data"])
    
    # Restore dtype if possible
    if "dtype" in data:
        try:
            arr = arr.astype(data["dtype"])
        except (ValueError, TypeError):
            pass
    
    # Restore shape if needed
    if "shape" in data and arr.shape != tuple(data["shape"]):
        try:
            arr = arr.reshape(data["shape"])
        except ValueError:
            pass
    
    return arr


def transform_spreadsheet_to_fitting(
    spreadsheet_data: pd.DataFrame, 
    x_column: str, 
    y_column: str,
    weights_column: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transform spreadsheet data for fitting tab consumption.

    Args:
        spreadsheet_data: Source DataFrame from spreadsheet
        x_column: Column name for x values
        y_column: Column name for y values  
        weights_column: Optional column name for weights

    Returns:
        Transformed data suitable for fitting tab
    """
    if x_column not in spreadsheet_data.columns:
        raise ValueError(f"X column '{x_column}' not found in data")
    if y_column not in spreadsheet_data.columns:
        raise ValueError(f"Y column '{y_column}' not found in data")

    # Create clean data for fitting
    fitting_data = pd.DataFrame({
        "x": spreadsheet_data[x_column],
        "y": spreadsheet_data[y_column],
    })

    # Add weights if specified
    if weights_column and weights_column in spreadsheet_data.columns:
        fitting_data["weights"] = spreadsheet_data[weights_column]

    # Remove any rows with NaN values
    fitting_data = fitting_data.dropna()

    return {
        "type": "fitting_data",
        "data": serialize_dataframe(fitting_data),
        "source_columns": {
            "x": x_column,
            "y": y_column,
            "weights": weights_column,
        },
        "original_shape": spreadsheet_data.shape,
        "cleaned_shape": fitting_data.shape,
    }


def transform_montecarlo_to_fitting(
    montecarlo_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Transform Monte Carlo simulation results for fitting tab.

    Args:
        montecarlo_results: Results from Monte Carlo simulation

    Returns:
        Transformed data suitable for fitting tab
    """
    if "simulation_data" not in montecarlo_results:
        raise ValueError("Monte Carlo results missing simulation_data")

    # Extract simulated data points
    sim_data = montecarlo_results["simulation_data"]
    
    if isinstance(sim_data, dict) and "data" in sim_data:
        df = deserialize_dataframe(sim_data)
    elif isinstance(sim_data, pd.DataFrame):
        df = sim_data
    else:
        raise ValueError("Invalid Monte Carlo data format")

    return {
        "type": "fitting_data",
        "data": serialize_dataframe(df),
        "source_type": "montecarlo",
        "simulation_parameters": montecarlo_results.get("parameters", {}),
        "original_shape": df.shape,
    }


def validate_data_message(message: DataPayload) -> tuple[bool, List[str]]:
    """
    Validate a data bus message format and content.

    Args:
        message: Data message to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check required fields
    required_fields = [
        "source_tab_id", "source_tab_type", "data_type", 
        "data", "timestamp", "version"
    ]
    
    for field in required_fields:
        if field not in message:
            errors.append(f"Missing required field: {field}")

    # Validate field types
    if "source_tab_id" in message and not isinstance(message["source_tab_id"], str):
        errors.append("source_tab_id must be a string")
    
    if "source_tab_type" in message and not isinstance(message["source_tab_type"], str):
        errors.append("source_tab_type must be a string")
    
    if "data_type" in message and not isinstance(message["data_type"], str):
        errors.append("data_type must be a string")

    # Validate timestamp format
    if "timestamp" in message:
        try:
            datetime.fromisoformat(message["timestamp"])
        except (ValueError, TypeError):
            errors.append("Invalid timestamp format")

    # Validate data based on type
    if "data" in message and "data_type" in message:
        data_type = message["data_type"]
        data = message["data"]
        
        if data_type == "dataframe" and not isinstance(data, dict):
            errors.append("DataFrame data must be a dictionary")
        elif data_type == "numpy_array" and not isinstance(data, dict):
            errors.append("NumPy array data must be a dictionary")
        elif data_type == "parameters" and not isinstance(data, dict):
            errors.append("Parameters data must be a dictionary")

    return len(errors) == 0, errors


def extract_numerical_columns(df: pd.DataFrame) -> List[str]:
    """
    Extract column names that contain numerical data.

    Args:
        df: DataFrame to analyze

    Returns:
        List of column names with numerical data
    """
    numerical_columns = []
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numerical_columns.append(col)
        else:
            # Check if column can be converted to numeric
            try:
                pd.to_numeric(df[col], errors="raise")
                numerical_columns.append(col)
            except (ValueError, TypeError):
                pass
    
    return numerical_columns


def get_data_summary(data: TabData) -> Dict[str, Any]:
    """
    Get a summary of data for display purposes.

    Args:
        data: Data to summarize

    Returns:
        Dictionary containing data summary
    """
    summary = {"type": type(data).__name__}
    
    if isinstance(data, pd.DataFrame):
        summary.update({
            "shape": data.shape,
            "columns": list(data.columns),
            "dtypes": {col: str(dtype) for col, dtype in data.dtypes.items()},
            "memory_usage": data.memory_usage(deep=True).sum(),
        })
    elif isinstance(data, np.ndarray):
        summary.update({
            "shape": data.shape,
            "dtype": str(data.dtype),
            "size": data.size,
        })
    elif isinstance(data, dict):
        summary.update({
            "keys": list(data.keys()),
            "num_items": len(data),
        })
    elif isinstance(data, list):
        summary.update({
            "length": len(data),
            "first_item_type": type(data[0]).__name__ if data else "empty",
        })
    
    return summary
