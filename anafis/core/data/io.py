"""
Pure functions for data input/output.
"""

import pandas as pd
from anafis.core.data_structures import ImportSettings


def load_dataframe(file_path: str, settings: ImportSettings) -> pd.DataFrame:
    """
    Load a DataFrame from a file using the specified settings.

    Args:
        file_path: Path to the file.
        settings: Dictionary of import settings.

    Returns:
        A pandas DataFrame.
    """
    file_type = settings.get("file_type", "autodetect")

    if file_type == "autodetect":
        if file_path.endswith(".csv"):
            file_type = "csv"
        elif file_path.endswith(".txt"):
            file_type = "txt"
        elif file_path.endswith((".xlsx", ".xls")):
            file_type = "excel"

    if file_type in ["csv", "txt"]:
        return pd.read_csv(
            file_path,
            sep=settings.get("delimiter", ","),
            header=0 if settings.get("header", True) else None,
            skiprows=settings.get("skiprows", 0),
            nrows=settings.get("nrows"),
        )
    elif file_type == "excel":
        return pd.read_excel(
            file_path,
            sheet_name=settings.get("sheet_name", "Sheet1"),
            header=0 if settings.get("header", True) else None,
            skiprows=settings.get("skiprows", 0),
            nrows=settings.get("nrows"),
        )
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
