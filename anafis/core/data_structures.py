"""
Simplified core immutable data structures for ANAFIS application state management.

This module defines the primary data structures used throughout the application
using NamedTuples without custom __new__ methods to avoid Python compatibility issues.
"""

from typing import NamedTuple, Dict, Optional, Tuple, Any, FrozenSet
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime


class FittingMethod(Enum):
    """Enumeration of available fitting methods."""
    LEVENBERG_MARQUARDT = "lm"
    ODR = "odr"
    MCMC = "mcmc"
    LEAST_SQUARES = "least_squares"


class SolverOperation(Enum):
    """Enumeration of solver operations."""
    SOLVE = "solve"
    INTEGRATE = "integrate"
    DIFFERENTIATE = "differentiate"
    SIMPLIFY = "simplify"
    EXPAND = "expand"
    FACTOR = "factor"


class DistributionType(Enum):
    """Enumeration of probability distributions for Monte Carlo."""
    NORMAL = "normal"
    UNIFORM = "uniform"
    LOGNORMAL = "lognormal"
    EXPONENTIAL = "exponential"
    GAMMA = "gamma"
    BETA = "beta"


@dataclass(frozen=True)
class Parameter:
    """Immutable parameter definition for fitting and Monte Carlo."""
    name: str
    value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    vary: bool = True
    error: Optional[float] = None

    def __post_init__(self):
        """Validate parameter constraints."""
        if self.min_value is not None and self.max_value is not None:
            if self.min_value >= self.max_value:
                raise ValueError(f"min_value ({self.min_value}) must be less than max_value ({self.max_value})")

        if self.min_value is not None and self.value < self.min_value:
            raise ValueError(f"value ({self.value}) must be >= min_value ({self.min_value})")

        if self.max_value is not None and self.value > self.max_value:
            raise ValueError(f"value ({self.value}) must be <= max_value ({self.max_value})")


class SpreadsheetState(NamedTuple):
    """Immutable state container for spreadsheet data and formulas."""
    data: pd.DataFrame
    formulas: Dict[str, str]
    units: Dict[str, str]
    dependencies: nx.DiGraph
    metadata: Dict[str, Any]
    last_modified: datetime


class FittingState(NamedTuple):
    """Immutable state container for curve fitting operations."""
    source_data: pd.DataFrame
    model_formula: str
    parameters: Dict[str, Parameter]
    method: FittingMethod
    results: Optional[Any]  # Will be FitResult when implemented
    data_columns: Dict[str, str]
    weights_column: Optional[str]
    metadata: Dict[str, Any]
    last_modified: datetime


class SolverState(NamedTuple):
    """Immutable state container for symbolic mathematics operations."""
    expression: str
    variables: Tuple[str, ...]
    target_variable: Optional[str]
    operation: SolverOperation
    steps: Tuple[Any, ...]  # Will be SolutionStep when implemented
    final_result: Optional[str]
    latex_result: Optional[str]
    assumptions: Dict[str, Any]
    metadata: Dict[str, Any]
    last_modified: datetime


class ApplicationState(NamedTuple):
    """Immutable state container for the entire application."""
    spreadsheet_tabs: Dict[str, SpreadsheetState]
    fitting_tabs: Dict[str, FittingState]
    solver_tabs: Dict[str, SolverState]
    active_tab_id: Optional[str]
    tab_order: Tuple[str, ...]
    detached_windows: FrozenSet[str]
    user_preferences: Dict[str, Any]
    data_bus_state: Dict[str, Any]
    last_saved: Optional[datetime]
    last_modified: datetime


# Factory functions for creating states with defaults

def create_spreadsheet_state(
    data: Optional[pd.DataFrame] = None,
    formulas: Optional[Dict[str, str]] = None,
    units: Optional[Dict[str, str]] = None,
    dependencies: Optional[nx.DiGraph] = None,
    metadata: Optional[Dict[str, Any]] = None,
    last_modified: Optional[datetime] = None
) -> SpreadsheetState:
    """Create a new SpreadsheetState with defaults."""
    return SpreadsheetState(
        data=data if data is not None else pd.DataFrame(),
        formulas=formulas if formulas is not None else {},
        units=units if units is not None else {},
        dependencies=dependencies if dependencies is not None else nx.DiGraph(),
        metadata=metadata if metadata is not None else {},
        last_modified=last_modified if last_modified is not None else datetime.now()
    )


def create_fitting_state(
    source_data: Optional[pd.DataFrame] = None,
    model_formula: str = "",
    parameters: Optional[Dict[str, Parameter]] = None,
    method: FittingMethod = FittingMethod.LEVENBERG_MARQUARDT,
    results: Optional[Any] = None,
    data_columns: Optional[Dict[str, str]] = None,
    weights_column: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    last_modified: Optional[datetime] = None
) -> FittingState:
    """Create a new FittingState with defaults."""
    return FittingState(
        source_data=source_data if source_data is not None else pd.DataFrame(),
        model_formula=model_formula,
        parameters=parameters if parameters is not None else {},
        method=method,
        results=results,
        data_columns=data_columns if data_columns is not None else {},
        weights_column=weights_column,
        metadata=metadata if metadata is not None else {},
        last_modified=last_modified if last_modified is not None else datetime.now()
    )


def create_solver_state(
    expression: str = "",
    variables: Optional[Tuple[str, ...]] = None,
    target_variable: Optional[str] = None,
    operation: SolverOperation = SolverOperation.SOLVE,
    steps: Optional[Tuple[Any, ...]] = None,
    final_result: Optional[str] = None,
    latex_result: Optional[str] = None,
    assumptions: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    last_modified: Optional[datetime] = None
) -> SolverState:
    """Create a new SolverState with defaults."""
    return SolverState(
        expression=expression,
        variables=variables if variables is not None else (),
        target_variable=target_variable,
        operation=operation,
        steps=steps if steps is not None else (),
        final_result=final_result,
        latex_result=latex_result,
        assumptions=assumptions if assumptions is not None else {},
        metadata=metadata if metadata is not None else {},
        last_modified=last_modified if last_modified is not None else datetime.now()
    )


def create_application_state(
    spreadsheet_tabs: Optional[Dict[str, SpreadsheetState]] = None,
    fitting_tabs: Optional[Dict[str, FittingState]] = None,
    solver_tabs: Optional[Dict[str, SolverState]] = None,
    active_tab_id: Optional[str] = None,
    tab_order: Optional[Tuple[str, ...]] = None,
    detached_windows: Optional[FrozenSet[str]] = None,
    user_preferences: Optional[Dict[str, Any]] = None,
    data_bus_state: Optional[Dict[str, Any]] = None,
    last_saved: Optional[datetime] = None,
    last_modified: Optional[datetime] = None
) -> ApplicationState:
    """Create a new ApplicationState with defaults."""
    return ApplicationState(
        spreadsheet_tabs=spreadsheet_tabs if spreadsheet_tabs is not None else {},
        fitting_tabs=fitting_tabs if fitting_tabs is not None else {},
        solver_tabs=solver_tabs if solver_tabs is not None else {},
        active_tab_id=active_tab_id,
        tab_order=tab_order if tab_order is not None else (),
        detached_windows=detached_windows if detached_windows is not None else frozenset(),
        user_preferences=user_preferences if user_preferences is not None else {},
        data_bus_state=data_bus_state if data_bus_state is not None else {},
        last_saved=last_saved,
        last_modified=last_modified if last_modified is not None else datetime.now()
    )


# Utility functions for working with immutable states

def update_spreadsheet_state(state: SpreadsheetState, **kwargs) -> SpreadsheetState:
    """Create a new SpreadsheetState with updated fields."""
    return state._replace(last_modified=datetime.now(), **kwargs)


def update_fitting_state(state: FittingState, **kwargs) -> FittingState:
    """Create a new FittingState with updated fields."""
    return state._replace(last_modified=datetime.now(), **kwargs)


def update_solver_state(state: SolverState, **kwargs) -> SolverState:
    """Create a new SolverState with updated fields."""
    return state._replace(last_modified=datetime.now(), **kwargs)


def update_application_state(state: ApplicationState, **kwargs) -> ApplicationState:
    """Create a new ApplicationState with updated fields."""
    return state._replace(last_modified=datetime.now(), **kwargs)