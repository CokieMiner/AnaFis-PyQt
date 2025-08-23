import math
from typing import Dict, Tuple

import sympy as sp
from sympy import Expr

from anafis.core.uncertanty.formula_generator import _get_math_functions, _preprocess_formula


class UncertaintyCalculator:
    """Calculator for uncertainty propagation in mathematical formulas."""

    @staticmethod
    def _calculate_formula_value(expr: Expr, variables_values: Dict[str, float]) -> float:
        """Calculate the final value of the formula."""
        expr_substituted = expr.subs(variables_values)
        return float(sp.N(expr_substituted))

    @staticmethod
    def _calculate_uncertainty(
        expr: Expr, variaveis: Dict[str, Tuple[float, float]], variables_values: Dict[str, float]
    ) -> float:
        """Calculate the total uncertainty using error propagation."""
        incerteza_total = 0.0
        for var, (_, sigma) in variaveis.items():
            symbol_var = sp.Symbol(var)
            derivada = sp.diff(expr, symbol_var)
            derivada_substituted = derivada.subs(variables_values)
            derivada_num = float(sp.N(derivada_substituted))
            incerteza_total += (derivada_num * sigma) ** 2
        return math.sqrt(incerteza_total)

    @staticmethod
    def calcular_incerteza(
        formula: str,
        variaveis: Dict[str, Tuple[float, float]],
    ) -> Tuple[float, float]:
        """
        Calculate uncertainty propagation for a given formula.

        Args:
            formula: Mathematical formula as string
            variaveis: Dictionary mapping variable names to (value, uncertainty) tuples
            language: Language for error messages ('pt' or 'en')

        Returns:
            Tuple containing (final_value, total_uncertainty)
        """
        math_functions = _get_math_functions()
        variable_names = list(variaveis.keys())
        formula = _preprocess_formula(formula, variable_names, math_functions)

        try:
            expr = sp.sympify(formula, locals=math_functions)
            variables_values = {k: v[0] for k, v in variaveis.items()}

            valor_final = UncertaintyCalculator._calculate_formula_value(expr, variables_values)
            incerteza_total = UncertaintyCalculator._calculate_uncertainty(expr, variaveis, variables_values)
            return valor_final, incerteza_total
        except Exception as e:
            raise ValueError(f"Error processing formula: {str(e)}") from e
