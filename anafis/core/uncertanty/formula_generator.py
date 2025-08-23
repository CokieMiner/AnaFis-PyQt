from typing import Dict, List, Tuple, Union, Callable

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from sympy.printing.latex import latex


def _get_math_functions() -> Dict[str, Union[sp.Expr, Callable]]:
    """Get mathematical functions dictionary for sympy evaluation."""
    return {
        # Trigonometric functions
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "cot": sp.cot,
        "sec": sp.sec,
        "csc": sp.csc,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
        "acot": sp.acot,
        "asec": sp.asec,
        "acsc": sp.acsc,
        "sinh": sp.sinh,
        "cosh": sp.cosh,
        "tanh": sp.tanh,
        "coth": sp.coth,
        "sech": sp.sech,
        "csch": sp.csch,
        "asinh": sp.asinh,
        "acosh": sp.acosh,
        "atanh": sp.atanh,
        "acoth": sp.acoth,
        "asech": sp.asech,
        "acsch": sp.acsch,
        # Logarithmic functions
        "log": sp.log,
        "ln": sp.ln,
        # Exponential functions
        "exp": sp.exp,
        "exp_polar": sp.exp_polar,
        # Powers and roots
        "sqrt": sp.sqrt,
        "cbrt": lambda x: x ** sp.Rational(1, 3),
        "root": lambda x, n: x ** sp.Rational(1, n),
        # Special functions
        "erf": sp.erf,
        "erfc": sp.erfc,
        "erfi": sp.erfi,
        "gamma": sp.gamma,
        "beta": sp.beta,
        "Ei": sp.Ei,
        "Si": sp.Si,
        "Ci": sp.Ci,
        "zeta": sp.zeta,
        # Piecewise and conditional functions
        "Abs": sp.Abs,
        "abs": sp.Abs,
        "sign": sp.sign,
        "floor": sp.floor,
        "ceiling": sp.ceiling,
        "ceil": sp.ceiling,
        "Min": sp.Min,
        "min": sp.Min,
        "Max": sp.Max,
        "max": sp.Max,
        # Continuous combinatorial functions
        "binomial": sp.binomial,
        "factorial": sp.factorial,
        "factorial2": sp.factorial2,
        # Constants
        "pi": sp.pi,
        "e": sp.E,
        "E": sp.E,
        "I": sp.I,
        "j": sp.I,  # Imaginary unit
    }


def _preprocess_formula(formula: str, variaveis: List[str], math_functions: Dict[str, Union[sp.Expr, Callable]]) -> str:
    """Preprocess formula to handle implicit multiplication while preserving function names."""
    simbolos = {var: sp.Symbol(var) for var in variaveis}
    combined_locals = {**simbolos, **math_functions}
    transformations = standard_transformations + (implicit_multiplication_application,)
    expr = parse_expr(formula, local_dict=combined_locals, transformations=transformations)
    return str(expr)


def generate_uncertainty_formula(formula: str, variaveis: List[str]) -> Tuple[str, str]:
    """Generate LaTeX formula for uncertainty propagation."""
    math_functions = _get_math_functions()
    formula = _preprocess_formula(formula, variaveis, math_functions)

    try:
        simbolos = {var: sp.Symbol(var) for var in variaveis}
        combined_locals = {**simbolos, **math_functions}
        expr = sp.sympify(formula, locals=combined_locals)

        termos_str = []
        termos_latex = []
        for var in variaveis:
            derivada = sp.diff(expr, sp.Symbol(var))

            derivada_str = str(derivada)
            if isinstance(derivada, (sp.Add)):
                derivada_str = f"({derivada_str})"

            latex_derivada = latex(derivada, mul_symbol="dot", full_prec=True)
            if isinstance(derivada, (sp.Add)):
                latex_derivada = f"({latex_derivada})"

            termos_str.append(f"(sigma_{var} * {derivada_str})^2")
            termos_latex.append(f"(\\sigma_{{{var}}} \\cdot {latex_derivada})^2")

        string_representation = f"sqrt({' + '.join(termos_str)})"
        latex_representation = "\\sigma_{\\text{total}} = \\sqrt{" + " + ".join(termos_latex) + "}"
        return string_representation, latex_representation
    except Exception as e:
        raise ValueError(f"Error generating formula: {str(e)}") from e
