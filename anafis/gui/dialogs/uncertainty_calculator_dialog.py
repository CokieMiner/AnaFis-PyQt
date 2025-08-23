from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QWidget,
    QScrollArea,
)
from typing import Dict, List, Optional, Tuple, cast
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg

from anafis.core.uncertanty.uncertainties import UncertaintyCalculator
from anafis.core.uncertanty.formula_generator import generate_uncertainty_formula


class UncertaintyCalculatorDialog(QDialog):
    """
    A dialog for performing uncertainty calculations and generating LaTeX formulas.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Uncertainty Calculator")
        self.setMinimumWidth(600)
        # Dictionary to store references to variable input fields
        self.variable_inputs: Dict[str, Tuple[QLineEdit, QLineEdit]] = {}
        self._current_variables: List[str] = []
        self._init_ui()
        self._connect_signals()
        self._update_ui_mode()  # Initialize UI based on default mode

    def _init_ui(self) -> None:
        """
        Initialize the UI components of the dialog.
        """
        main_layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Uncertainty Calculation")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Formula input
        formula_group = QGroupBox("Formula (e.g., x*sin(y) + z)")
        formula_layout = QVBoxLayout()
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("Enter your mathematical formula here")
        formula_layout.addWidget(self.formula_input)
        formula_group.setLayout(formula_layout)
        main_layout.addWidget(formula_group)

        # Variables input
        variables_group = QGroupBox("Variables (comma-separated, e.g., x, y, z)")
        variables_layout = QVBoxLayout()
        self.variables_input = QLineEdit()
        self.variables_input.setPlaceholderText("Enter variable names")
        variables_layout.addWidget(self.variables_input)
        variables_group.setLayout(variables_layout)
        main_layout.addWidget(variables_group)

        # Mode selection
        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout()
        self.calculate_radio = QRadioButton("Calculate Value")
        self.propagate_radio = QRadioButton("Propagate Formula")
        self.calculate_radio.setChecked(True)
        mode_layout.addWidget(self.calculate_radio)
        mode_layout.addWidget(self.propagate_radio)
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # Dynamic input/output area (stacked widget or conditional visibility)
        # For simplicity, we'll use conditional visibility for now
        self.calculate_mode_widget = QWidget()
        self.calculate_mode_layout = QVBoxLayout(self.calculate_mode_widget)

        self.dynamic_variables_group = QGroupBox("Variable Values and Uncertainties")
        self.dynamic_variables_layout = QFormLayout()
        self.dynamic_variables_group.setLayout(self.dynamic_variables_layout)
        self.calculate_mode_layout.addWidget(self.dynamic_variables_group)

        self.calculate_button = QPushButton("Calculate Result")
        self.calculate_mode_layout.addWidget(self.calculate_button)

        self.result_group = QGroupBox("Calculation Result")
        self.result_layout = QVBoxLayout()
        self.result_label = QLabel("Value: N/A\nUncertainty: N/A")
        self.result_layout.addWidget(self.result_label)
        self.result_group.setLayout(self.result_layout)
        self.calculate_mode_layout.addWidget(self.result_group)
        main_layout.addWidget(self.calculate_mode_widget)

        self.propagate_mode_widget = QWidget()
        self.propagate_mode_layout = QVBoxLayout(self.propagate_mode_widget)

        self.propagate_button = QPushButton("Generate LaTeX Formula")
        self.propagate_mode_layout.addWidget(self.propagate_button)

        self.string_representation_group = QGroupBox("String Representation")
        self.string_representation_layout = QVBoxLayout()
        self.string_representation_output = QLineEdit()
        self.string_representation_output.setReadOnly(True)
        self.string_representation_output.setPlaceholderText("String representation will appear here")
        self.string_representation_layout.addWidget(self.string_representation_output)
        self.string_representation_group.setLayout(self.string_representation_layout)
        self.propagate_mode_layout.addWidget(self.string_representation_group)

        self.latex_output_group = QGroupBox("Generated LaTeX Formula")
        self.latex_output_layout = QVBoxLayout()
        self.latex_output = QLineEdit()
        self.latex_output.setReadOnly(True)
        self.latex_output.setPlaceholderText("LaTeX formula will appear here")
        self.latex_output_layout.addWidget(self.latex_output)
        self.latex_output_group.setLayout(self.latex_output_layout)
        self.propagate_mode_layout.addWidget(self.latex_output_group)

        self.rendered_latex_group = QGroupBox("Rendered Formula (Requires LaTeX Renderer)")
        self.rendered_latex_layout = QVBoxLayout()
        self.rendered_latex_label = QLabel("<i>Rendered formula will appear here.</i>")
        self.rendered_latex_label.setWordWrap(True)
        self.rendered_latex_label.setOpenExternalLinks(True)
        self.rendered_latex_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.rendered_latex_label)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.rendered_latex_layout.addWidget(self.scroll_area)
        self.rendered_latex_group.setLayout(self.rendered_latex_layout)
        self.propagate_mode_layout.addWidget(self.rendered_latex_group)
        main_layout.addWidget(self.propagate_mode_widget)

        # Add stretch to push content to top
        main_layout.addStretch(1)

    def _connect_signals(self) -> None:
        """
        Connect signals to slots.
        """
        self.variables_input.textChanged.connect(self._update_variable_inputs)
        self.calculate_radio.toggled.connect(self._update_ui_mode)
        self.calculate_button.clicked.connect(self._calculate_uncertainty_result)
        self.propagate_button.clicked.connect(self._generate_latex_formula)

    def _update_ui_mode(self) -> None:
        """
        Update the UI based on the selected mode (Calculate Value or Propagate Formula).
        """
        is_calculate_mode = self.calculate_radio.isChecked()
        self.calculate_mode_widget.setVisible(is_calculate_mode)
        self.propagate_mode_widget.setVisible(not is_calculate_mode)
        if is_calculate_mode:
            # Force update of variable inputs when switching to calculate mode
            self._current_variables = []
            self._update_variable_inputs()
        self.adjustSize()

    def _update_variable_inputs(self) -> None:
        """
        Dynamically create/update input fields for variables based on the variables_input.
        """
        variables_text = self.variables_input.text()
        variables = [v.strip() for v in variables_text.split(",") if v.strip()]

        if variables == self._current_variables:
            return

        self._current_variables = variables

        # Clear existing inputs and reset stored references
        while self.dynamic_variables_layout.count():
            item = self.dynamic_variables_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    layout = item.layout()
                    if layout is not None:
                        while layout.count():
                            child_item = layout.takeAt(0)
                            if child_item is not None:
                                child_widget = child_item.widget()
                                if child_widget is not None:
                                    child_widget.deleteLater()
        self.variable_inputs = {}

        if self.calculate_radio.isChecked():
            self.dynamic_variables_group.setTitle("Variable Values and Uncertainties")
            for var in variables:
                value_input = QLineEdit()
                value_input.setPlaceholderText(f"Value of {var}")

                uncertainty_input = QLineEdit()
                uncertainty_input.setPlaceholderText(f"Uncertainty of {var}")

                # Store references to the input fields
                self.variable_inputs[var] = (value_input, uncertainty_input)

                h_layout = QHBoxLayout()
                h_layout.addWidget(QLabel(f"{var}:"))
                h_layout.addWidget(QLabel("Value:"))
                h_layout.addWidget(value_input)
                h_layout.addWidget(QLabel("Uncertainty:"))
                h_layout.addWidget(uncertainty_input)
                self.dynamic_variables_layout.addRow(h_layout)
        else:
            self.dynamic_variables_group.setTitle("Variables for Propagation")
            # No dynamic inputs needed for propagate mode, just clear them
        self.adjustSize()

    def _get_variable_data(self) -> Dict[str, Tuple[float, float]]:
        """
        Retrieves variable values and uncertainties from dynamic input fields.
        """
        variables_data: Dict[str, Tuple[float, float]] = {}
        variables_text = self.variables_input.text()
        variables = [v.strip() for v in variables_text.split(",") if v.strip()]

        for var in variables:
            if var not in self.variable_inputs:
                raise ValueError(f"Input fields for variable '{var}' not found. This should not happen.")

            value_input, uncertainty_input = self.variable_inputs[var]

            try:
                value = float(value_input.text())
                uncertainty = float(uncertainty_input.text())
                variables_data[var] = (value, uncertainty)
            except ValueError:
                raise ValueError(f"Invalid number for variable '{var}'. Please enter numerical values.")
        return variables_data

    def _calculate_uncertainty_result(self) -> None:
        """
        Performs the uncertainty calculation and displays the result.
        """
        formula = self.formula_input.text().strip()
        if not formula:
            QMessageBox.warning(self, "Input Error", "Please enter a formula.")
            return

        try:
            variables_data = self._get_variable_data()
            if not variables_data:
                QMessageBox.warning(self, "Input Error", "Please enter variables and their values/uncertainties.")
                return

            final_value, total_uncertainty = UncertaintyCalculator.calcular_incerteza(
                formula=formula,
                variaveis=variables_data,
            )
            self.result_label.setText(f"Value: {final_value:.6g}\nUncertainty: {total_uncertainty:.6g}")
        except ValueError as e:
            QMessageBox.critical(self, "Calculation Error", f"ValueError: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "An Error Occurred", f"Unexpected error: {e}\n\nType: {type(e).__name__}")

    def _generate_latex_formula(self) -> None:
        """
        Generates the LaTeX uncertainty propagation formula.
        """
        formula = self.formula_input.text().strip()
        if not formula:
            QMessageBox.warning(self, "Input Error", "Please enter a formula.")
            return

        variables_text = self.variables_input.text()
        variables = [v.strip() for v in variables_text.split(",") if v.strip()]
        if not variables:
            QMessageBox.warning(self, "Input Error", "Please enter variable names.")
            return

        try:
            string_representation, latex_formula = generate_uncertainty_formula(
                formula=formula,
                variaveis=variables,
            )
            self.string_representation_output.setText(string_representation)
            self.latex_output.setText(latex_formula)

            palette = self.palette()
            bg_color = palette.color(palette.ColorRole.Window).name()
            fg_color = palette.color(palette.ColorRole.WindowText).name()

            pixmap, error = self._render_latex(latex_formula, fg_color, bg_color)
            if pixmap:
                self.rendered_latex_label.setPixmap(pixmap)
                horizontal_scroll_bar = self.scroll_area.horizontalScrollBar()
                scroll_bar_height = horizontal_scroll_bar.height() if horizontal_scroll_bar is not None else 0
                self.scroll_area.setMinimumHeight(pixmap.height() + scroll_bar_height)
            else:
                if error == "renderer_not_found":
                    error_message = "<i>Error rendering LaTeX: LaTeX renderer not found.</i><br>"
                    error_message += "Please install a LaTeX distribution like "
                    error_message += (
                        '<a href="https://miktex.org/download">MiKTeX</a> and ensure it is in your system\'s PATH.'
                    )
                else:
                    error_message = f"<i>Error rendering LaTeX:</i><br><pre>{error}</pre>"
                self.rendered_latex_label.setText(error_message)
            self.adjustSize()
        except ValueError as e:
            QMessageBox.critical(self, "Formula Generation Error", f"ValueError: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "An Error Occurred", f"Unexpected error: {e}\n\nType: {type(e).__name__}")

    def _render_latex(self, latex: str, fg_color: str, bg_color: str) -> Tuple[Optional[QPixmap], Optional[str]]:
        """
        Renders a LaTeX string into a QPixmap.
        """
        try:
            buffer = BytesIO()
            plt.rc("text", usetex=True)
            plt.rc("font", family="serif")
            plt.rc("text.latex", preamble=r"\usepackage{amsmath}")

            font_size = 30 * self.logicalDpiX() / 96.0
            fig = plt.figure(facecolor=bg_color)
            text = fig.text(0, 0, f"${latex}$", ha="center", va="center", color=fg_color, fontsize=font_size)

            # Dynamically adjust font size
            canvas_agg = cast(FigureCanvasAgg, fig.canvas)
            renderer = canvas_agg.get_renderer()
            bbox = text.get_window_extent(renderer=renderer)

            fig.set_size_inches(bbox.width / fig.dpi, bbox.height / fig.dpi)

            plt.axis("off")
            fig.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0, facecolor=bg_color)
            plt.close(fig)

            buffer.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.read())
            return pixmap, None
        except FileNotFoundError:
            return None, "renderer_not_found"
        except RuntimeError as e:
            return None, str(e)


# Example of how to use it (for testing purposes)
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = UncertaintyCalculatorDialog()
    dialog.show()
    sys.exit(app.exec())
