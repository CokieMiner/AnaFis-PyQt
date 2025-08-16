"""
Tests for core immutable data structures.
"""

import pytest
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime

from anafis.core.data_structures import (
    SpreadsheetState, FittingState, SolverState, ApplicationState,
    Parameter, FittingMethod, SolverOperation, DistributionType,
    create_spreadsheet_state, create_fitting_state, create_solver_state, create_application_state,
    update_spreadsheet_state, update_fitting_state, update_solver_state, update_application_state
)


class TestParameter:
    """Test Parameter dataclass."""

    def test_parameter_creation(self):
        """Test basic parameter creation."""
        param = Parameter(name="a", value=1.0)
        assert param.name == "a"
        assert param.value == 1.0
        assert param.vary is True
        assert param.min_value is None
        assert param.max_value is None

    def test_parameter_with_constraints(self):
        """Test parameter with min/max constraints."""
        param = Parameter(name="b", value=2.0, min_value=0.0, max_value=10.0)
        assert param.min_value == 0.0
        assert param.max_value == 10.0

    def test_parameter_validation_error(self):
        """Test parameter validation errors."""
        with pytest.raises(ValueError):
            Parameter(name="bad", value=5.0, min_value=10.0, max_value=1.0)

        with pytest.raises(ValueError):
            Parameter(name="bad", value=-1.0, min_value=0.0)

        with pytest.raises(ValueError):
            Parameter(name="bad", value=11.0, max_value=10.0)


class TestSpreadsheetState:
    """Test SpreadsheetState NamedTuple."""

    def test_default_creation(self):
        """Test creation with default values."""
        state = create_spreadsheet_state()
        assert isinstance(state.data, pd.DataFrame)
        assert len(state.data) == 0
        assert state.formulas == {}
        assert state.units == {}
        assert isinstance(state.dependencies, nx.DiGraph)
        assert isinstance(state.last_modified, datetime)

    def test_creation_with_data(self):
        """Test creation with actual data."""
        data = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        formulas = {"C1": "=A1+B1"}
        units = {"A": "m", "B": "s"}

        state = create_spreadsheet_state(
            data=data,
            formulas=formulas,
            units=units
        )

        assert len(state.data) == 3
        assert "A" in state.data.columns
        assert state.formulas["C1"] == "=A1+B1"
        assert state.units["A"] == "m"

    def test_immutability(self):
        """Test that the state is immutable."""
        state = create_spreadsheet_state()

        # Should not be able to modify the state directly
        with pytest.raises(AttributeError):
            state.formulas = {"new": "formula"}

    def test_update_function(self):
        """Test the update helper function."""
        original_state = create_spreadsheet_state()
        new_formulas = {"A1": "=1+1"}

        updated_state = update_spreadsheet_state(
            original_state,
            formulas=new_formulas
        )

        assert updated_state.formulas == new_formulas
        assert updated_state.last_modified > original_state.last_modified
        assert original_state.formulas == {}  # Original unchanged


class TestFittingState:
    """Test FittingState NamedTuple."""

    def test_default_creation(self):
        """Test creation with default values."""
        state = create_fitting_state()
        assert isinstance(state.source_data, pd.DataFrame)
        assert state.model_formula == ""
        assert state.method == FittingMethod.LEVENBERG_MARQUARDT
        assert state.results is None

    def test_creation_with_data(self):
        """Test creation with fitting data."""
        data = pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6]})
        parameters = {"a": Parameter("a", 1.0), "b": Parameter("b", 0.0)}

        state = create_fitting_state(
            source_data=data,
            model_formula="a*x + b",
            parameters=parameters,
            method=FittingMethod.ODR
        )

        assert len(state.source_data) == 3
        assert state.model_formula == "a*x + b"
        assert state.method == FittingMethod.ODR
        assert "a" in state.parameters


class TestSolverState:
    """Test SolverState NamedTuple."""

    def test_default_creation(self):
        """Test creation with default values."""
        state = create_solver_state()
        assert state.expression == ""
        assert state.variables == ()
        assert state.operation == SolverOperation.SOLVE
        assert state.steps == ()

    def test_creation_with_expression(self):
        """Test creation with mathematical expression."""
        state = create_solver_state(
            expression="x^2 + 2*x + 1 = 0",
            variables=("x",),
            operation=SolverOperation.SOLVE
        )

        assert state.expression == "x^2 + 2*x + 1 = 0"
        assert state.variables == ("x",)
        assert state.operation == SolverOperation.SOLVE


class TestApplicationState:
    """Test ApplicationState NamedTuple."""

    def test_default_creation(self):
        """Test creation with default values."""
        state = create_application_state()
        assert state.spreadsheet_tabs == {}
        assert state.fitting_tabs == {}
        assert state.solver_tabs == {}
        assert state.active_tab_id is None
        assert state.tab_order == ()
        assert state.detached_windows == frozenset()

    def test_creation_with_tabs(self):
        """Test creation with tab states."""
        spreadsheet_tab = create_spreadsheet_state()
        fitting_tab = create_fitting_state()

        state = create_application_state(
            spreadsheet_tabs={"sheet1": spreadsheet_tab},
            fitting_tabs={"fit1": fitting_tab},
            active_tab_id="sheet1",
            tab_order=("sheet1", "fit1")
        )

        assert "sheet1" in state.spreadsheet_tabs
        assert "fit1" in state.fitting_tabs
        assert state.active_tab_id == "sheet1"
        assert state.tab_order == ("sheet1", "fit1")


class TestEnums:
    """Test enumeration classes."""

    def test_fitting_method_enum(self):
        """Test FittingMethod enumeration."""
        assert FittingMethod.LEVENBERG_MARQUARDT.value == "lm"
        assert FittingMethod.ODR.value == "odr"
        assert FittingMethod.MCMC.value == "mcmc"

    def test_solver_operation_enum(self):
        """Test SolverOperation enumeration."""
        assert SolverOperation.SOLVE.value == "solve"
        assert SolverOperation.INTEGRATE.value == "integrate"
        assert SolverOperation.DIFFERENTIATE.value == "differentiate"

    def test_distribution_type_enum(self):
        """Test DistributionType enumeration."""
        assert DistributionType.NORMAL.value == "normal"
        assert DistributionType.UNIFORM.value == "uniform"
        assert DistributionType.LOGNORMAL.value == "lognormal"


class TestUpdateFunctions:
    """Test state update functions."""

    def test_update_spreadsheet_state(self):
        """Test spreadsheet state update."""
        original = create_spreadsheet_state()
        updated = update_spreadsheet_state(original, formulas={"A1": "=1+1"})

        assert updated.formulas == {"A1": "=1+1"}
        assert updated.last_modified > original.last_modified
        assert original.formulas == {}  # Original unchanged

    def test_update_fitting_state(self):
        """Test fitting state update."""
        original = create_fitting_state()
        updated = update_fitting_state(original, model_formula="y = mx + b")

        assert updated.model_formula == "y = mx + b"
        assert updated.last_modified > original.last_modified
        assert original.model_formula == ""  # Original unchanged

    def test_update_solver_state(self):
        """Test solver state update."""
        original = create_solver_state()
        updated = update_solver_state(original, expression="x^2 = 4")

        assert updated.expression == "x^2 = 4"
        assert updated.last_modified > original.last_modified
        assert original.expression == ""  # Original unchanged

    def test_update_application_state(self):
        """Test application state update."""
        original = create_application_state()
        updated = update_application_state(original, active_tab_id="tab1")

        assert updated.active_tab_id == "tab1"
        assert updated.last_modified > original.last_modified
        assert original.active_tab_id is None  # Original unchanged