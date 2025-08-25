# Design Document

## Overview

ANAFIS is a desktop application for scientific data analysis built with PyQt6. The application follows a tabbed notebook interface where each major capability (Spreadsheet, Curve-Fitting, Wolfram-like Solver, Monte-Carlo Simulator) exists as closable, detachable tabs. The design prioritizes leveraging existing, well-tested Python libraries over custom implementations.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PyQt6 GUI Layer                          │
├─────────────────────────────────────────────────────────────┤
│                   Services Layer                            │
├─────────────────────────────────────────────────────────────┤
│                    Core Layer                               │
├─────────────────────────────────────────────────────────────┤
│              External Libraries Integration                  │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Library Reuse**: Leverage existing Python scientific libraries (NumPy, SciPy, SymPy, Pandas, etc.)
2. **PyQt6 Native**: Use PyQt6 widgets and patterns throughout the GUI
3. **Functional Programming**: Prefer pure functions and immutable data structures over classes
4. **Modular Tabs**: Each analysis tool is an independent, closable tab
5. **Data Bus Communication**: Inter-tab data sharing via PyQt signals/slots
6. **Detachable Interface**: Tabs can be torn off into separate windows

## Components and Interfaces

### GUI Components (PyQt6)

#### Main Application Shell
- **AnafisNotebook** (QMainWindow): Root window with QTabWidget
- **DetachableTabWidget** (QTabWidget): Custom tab widget supporting drag-to-detach
- **HomeMenuWidget** (QWidget): Welcome screen with "New Tab" buttons

#### Tab Components
- **SpreadsheetTab** (QWidget): Embeds QTableWidget with formula support
- **FittingTab** (QWidget): Data fitting interface with matplotlib canvas
- **SolverTab** (QWidget): Equation solver with LaTeX input/output
- **MonteCarloTab** (QWidget): Monte Carlo simulation interface

#### Floating Tools
- **UncertaintyDialog** (QDialog): Non-modal uncertainty calculator (F9)
- **QuickSolverDialog** (QDialog): Mini equation solver (Alt+S)

### Services Layer (Functional Modules)

#### Data Processing Functions
- **spreadsheet_engine.py**: Pure functions for formula evaluation using `pandas` and `numexpr`
- **fitting_service.py**: Functional curve fitting using `lmfit`, `scipy.optimize`, `emcee`
- **solver_service.py**: Functional symbolic math using `sympy` and `latex2sympy2`
- **monte_carlo_service.py**: Functional statistical simulation using `numpy` and `scipy.stats`

#### Core Service Functions
- **data_bus.py**: Functional data transformation and routing (minimal QObject wrapper)
- **state_manager.py**: Pure functions for state serialization/deserialization using `h5py`
- **unit_manager.py**: Pure functions for unit handling using `pint`
- **translation_manager.py**: Functional internationalization utilities

### External Library Integration

#### Scientific Computing Stack
- **NumPy**: Array operations and numerical computing
- **Pandas**: Data manipulation and analysis
- **SciPy**: Scientific algorithms (optimization, statistics, integration)
- **SymPy**: Symbolic mathematics and equation solving
- **Matplotlib**: 2D plotting and visualization
- **VisPy**: High-performance 3D/multi-dimensional visualization

#### Specialized Libraries
- **lmfit**: Non-linear least-squares fitting
- **emcee**: MCMC sampling for Bayesian analysis
- **pint**: Physical units and unit conversion
- **numexpr**: Fast numerical expression evaluation
- **h5py**: HDF5 file format for data persistence
- **latex2sympy2**: LaTeX to SymPy expression conversion
- **babel**: Internationalization and localization support

## Data Models (Functional Approach)

### Core Data Structures (Immutable)

#### Spreadsheet State (NamedTuple)
```python
from typing import NamedTuple, Dict, Optional
import pandas as pd
import networkx as nx

class SpreadsheetState(NamedTuple):
    data: pd.DataFrame          # Cell values (immutable)
    formulas: Dict[str, str]    # Cell formulas (frozen dict)
    units: Dict[str, str]       # Column units (frozen dict)
    dependencies: nx.DiGraph    # Formula dependency graph (immutable)
```

#### Fitting State (NamedTuple)
```python
class FittingState(NamedTuple):
    source_data: pd.DataFrame   # Input data (immutable)
    model_formula: str          # Mathematical model
    parameters: Dict[str, 'Parameter']  # Fit parameters (frozen dict)
    results: Optional['FitResult']      # Fitting results (immutable)
    method: str                # Fitting algorithm
```

#### Solver State (NamedTuple)
```python
class SolverState(NamedTuple):
    expression: str            # Input expression (LaTeX)
    variables: Tuple[str, ...]  # Variables to solve for (immutable)
    steps: Tuple['SolutionStep', ...]  # Step-by-step solution (immutable)
    result: Optional[sympy.Expr]       # Final result
```

### Data Flow Architecture

#### Inter-Tab Communication
```
Tab A ──signal──> DataBus ──signal──> Tab B
      <──slot────         <──slot────
```

#### Data Persistence
```
Application State ──> HDF5 File
    ├── Tab States
    ├── User Preferences
    ├── Recent Files
    └── Window Layout
```

## Error Handling

### Error Categories

1. **User Input Errors**: Invalid formulas, malformed expressions
2. **Computation Errors**: Numerical instability, convergence failures
3. **Data Errors**: Missing data, unit mismatches
4. **System Errors**: File I/O, memory limitations

### Error Handling Strategy

#### Input Validation
- Real-time formula syntax checking using `sympy.parsing`
- Unit compatibility validation using `pint`
- Data type validation using `pandas` dtypes

#### Graceful Degradation
- Fallback algorithms when primary methods fail
- Partial results display when computation is interrupted
- Error recovery with user guidance

#### User Feedback
- Status bar messages for ongoing operations
- Progress bars for long-running computations
- Detailed error dialogs with suggested solutions

## Testing Strategy

### Unit Testing Framework
- **pytest**: Primary testing framework
- **pytest-qt**: PyQt6 widget testing
- **numpy.testing**: Numerical accuracy testing

### Test Categories

#### Core Logic Tests
- Formula evaluation accuracy
- Fitting algorithm convergence
- Symbolic math correctness
- Unit conversion precision

#### GUI Integration Tests
- Tab creation/destruction
- Data bus communication
- User interaction workflows
- Window management

#### Performance Tests
- Large dataset handling
- Memory usage monitoring
- Computation speed benchmarks

### Test Data Management
- Synthetic datasets for reproducible testing
- Real-world data samples for validation
- Edge cases and boundary conditions

## Implementation Details

### PyQt6 Functional Patterns

#### Model-View Architecture (Functional)
```python
# Pure functions for data transformation
def create_qt_model_data(spreadsheet_state: SpreadsheetState) -> List[List[str]]:
    """Convert immutable state to Qt model data."""
    return spreadsheet_state.data.values.tolist()

def update_spreadsheet_state(current_state: SpreadsheetState,
                           cell: str, value: str) -> SpreadsheetState:
    """Pure function returning new state."""
    new_data = current_state.data.copy()
    # Update logic here
    return current_state._replace(data=new_data)

class SpreadsheetModel(QAbstractTableModel):
    def __init__(self, initial_state: SpreadsheetState):
        super().__init__()
        self._state = initial_state

    def update_state(self, new_state: SpreadsheetState):
        """Update model with new immutable state."""
        self._state = new_state
        self.dataChanged.emit(QModelIndex(), QModelIndex())
```

#### Signal-Slot Communication (Functional)
```python
# Pure functions for data transformation
def transform_data_for_broadcast(data: pd.DataFrame, source: str) -> Dict:
    """Pure function to prepare data for transmission."""
    return {"data": data.to_dict(), "source": source, "timestamp": time.time()}

def process_received_data(message: Dict) -> pd.DataFrame:
    """Pure function to process received data."""
    return pd.DataFrame.from_dict(message["data"])

class DataBus(QObject):
    data_updated = pyqtSignal(dict)  # Use dict for serializable data

    def broadcast_data(self, data: pd.DataFrame, source: str):
        """Minimal wrapper around pure function."""
        message = transform_data_for_broadcast(data, source)
        self.data_updated.emit(message)
```

#### Widget Creation (Functional)
```python
# Pure functions for widget configuration
def create_formula_validator() -> QValidator:
    """Pure function returning configured validator."""
    # Validation logic here
    pass

def setup_formula_line_edit(parent=None) -> QLineEdit:
    """Pure function creating configured widget."""
    line_edit = QLineEdit(parent)
    line_edit.setValidator(create_formula_validator())
    return line_edit

# Usage in widget classes (minimal classes, maximum functions)
class FormulaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_edit = setup_formula_line_edit(self)
        # Connect to functional handlers
        self.line_edit.textChanged.connect(
            lambda text: self.handle_formula_change(text)
        )

    def handle_formula_change(self, text: str):
        """Delegate to pure function."""
        result = validate_and_parse_formula(text)
        self.update_ui_from_result(result)
```

### Functional Programming Principles

#### Pure Functions
- All business logic implemented as pure functions (no side effects)
- Functions take immutable inputs and return new immutable outputs
- Easy to test, reason about, and parallelize

#### Immutable Data Structures
- Use NamedTuple and frozen dataclasses for state representation
- pandas DataFrames treated as immutable (always copy, never modify in-place)
- State transitions create new state objects rather than mutating existing ones

#### Function Composition
```python
# Compose functions for complex operations
def process_spreadsheet_formula(state: SpreadsheetState, cell: str, formula: str) -> SpreadsheetState:
    """Compose multiple pure functions for formula processing."""
    parsed_formula = parse_formula(formula)
    validated_formula = validate_formula_syntax(parsed_formula)
    updated_dependencies = update_dependency_graph(state.dependencies, cell, validated_formula)
    new_state = update_cell_formula(state, cell, validated_formula)
    return new_state._replace(dependencies=updated_dependencies)

# Pipeline-style data processing
def fit_curve_pipeline(data: pd.DataFrame, model: str, method: str) -> FittingState:
    """Functional pipeline for curve fitting."""
    return (data
            |> validate_fitting_data
            |> lambda df: prepare_fitting_input(df, model)
            |> lambda input_data: execute_fitting(input_data, method)
            |> create_fitting_state)
```

#### Minimal Classes
- Classes only for PyQt6 integration (widgets, models, signals)
- Business logic extracted to pure functions
- Classes act as thin wrappers around functional core

### Library Integration Patterns

#### NumPy/Pandas Integration (Functional)
- Use pandas DataFrames as immutable data containers
- Leverage NumPy for numerical computations via pure functions
- Integrate with PyQt models through functional transformations

#### Matplotlib Integration
```python
class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = plt.figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
```

#### SymPy Integration
- Use SymPy for symbolic mathematics
- Convert LaTeX input to SymPy expressions
- Generate step-by-step solutions

### Performance Considerations

#### Lazy Evaluation
- Defer expensive computations until needed
- Cache results for repeated calculations
- Use generators for large datasets

#### Memory Management
- Stream large datasets rather than loading entirely
- Use memory-mapped files for huge arrays
- Implement garbage collection for temporary objects

#### Parallel Processing
- Use `concurrent.futures` for CPU-bound tasks
- Leverage NumPy's built-in parallelization
- Implement progress reporting for long operations

### Internationalization Support

#### Translation Architecture
The application uses PyQt6's built-in internationalization system combined with `babel` for translation management.

#### Translation Implementation
```python
class TranslationManager:
    def __init__(self):
        self.translator = QTranslator()
        self.current_locale = QLocale.system().name()

    def load_translation(self, locale: str):
        translation_file = f"anafis_{locale}.qm"
        self.translator.load(translation_file, ":/translations/")
        QApplication.instance().installTranslator(self.translator)
```

#### Translation Workflow
1. **String Marking**: Use `self.tr()` in PyQt6 widgets and `QCoreApplication.translate()` for non-widget classes
2. **Extraction**: Use `pylupdate6` to extract translatable strings to `.ts` files
3. **Translation**: Use Qt Linguist for translation management
4. **Compilation**: Use `lrelease` to compile `.ts` files to `.qm` files
5. **Runtime Loading**: Load appropriate translation based on system locale or user preference

#### Supported Elements
- All GUI text (menus, buttons, labels, tooltips)
- Error messages and status updates
- Mathematical operation descriptions
- Help documentation

### Application Configuration

#### Settings Management
The application uses PyQt6's `QSettings` for persistent configuration management with a dedicated settings dialog.

#### Configuration Architecture
```python
class SettingsManager:
    def __init__(self):
        self.settings = QSettings("ANAFIS", "AnafisApp")
        self.load_defaults()

    def get_setting(self, key: str, default=None):
        return self.settings.value(key, default)

    def set_setting(self, key: str, value):
        self.settings.setValue(key, value)
        self.settings.sync()
```

#### Settings Categories
- **General**: Language, theme, startup behavior
- **Computation**: Default algorithms, precision settings, GPU usage
- **Interface**: Tab behavior, floating tool shortcuts, plot defaults
- **Updates**: Auto-check frequency, update channel (stable/beta)
- **Advanced**: Debug logging, memory limits, cache settings

#### Settings Dialog
```python
class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("ANAFIS Settings"))
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        # Tabbed interface for different setting categories
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(GeneralSettingsWidget(), self.tr("General"))
        self.tab_widget.addTab(ComputationSettingsWidget(), self.tr("Computation"))
        # ... additional tabs
```

### Update Management

#### GitHub-Based Update System
The application includes an integrated update checker that queries GitHub releases for new versions.

#### Update Architecture
```python
class UpdateChecker(QObject):
    update_available = pyqtSignal(str, str)  # version, download_url

    def __init__(self):
        super().__init__()
        self.github_repo = "your-org/anafis"
        self.current_version = __version__

    async def check_for_updates(self):
        # Query GitHub API for latest release
        api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        # Compare versions and emit signal if update available
```

#### Update Features
- **Automatic Checking**: Configurable auto-check on startup or periodic intervals
- **Manual Checking**: "Check for Updates" menu option
- **Version Comparison**: Semantic version comparison for update detection
- **Release Notes**: Display changelog from GitHub release notes
- **Download Integration**: Direct download links to platform-specific installers

### Distribution Strategy

#### Windows Distribution (.exe)
- **PyInstaller**: Primary packaging tool for Windows executable creation
- **NSIS Installer**: Professional installer with uninstall support
- **Code Signing**: Digital signature for Windows SmartScreen compatibility

```python
# PyInstaller spec file configuration
a = Analysis(['anafis/app.py'],
             pathex=[],
             binaries=[],
             datas=[('anafis/i18n', 'i18n'),
                    ('anafis/resources', 'resources')],
             hiddenimports=['scipy', 'numpy', 'matplotlib'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
```

#### Linux Distribution
- **AppImage**: Self-contained portable application format
- **Flatpak**: Sandboxed application for Flathub distribution
- **Snap Package**: Alternative universal package format

#### AppImage Configuration
```yaml
# AppImageBuilder.yml
version: 1
script:
  - rm -rf AppDir || true
  - python -m pip install --system --target AppDir/usr/lib/python3.9/site-packages .
  - cp -r anafis/resources AppDir/usr/share/anafis/
```

#### Flatpak Manifest
```json
{
    "app-id": "org.anafis.ANAFIS",
    "runtime": "org.kde.Platform",
    "runtime-version": "6.6",
    "sdk": "org.kde.Sdk",
    "command": "anafis",
    "finish-args": [
        "--share=ipc",
        "--socket=x11",
        "--device=dri",
        "--filesystem=home"
    ]
}
```

#### Distribution Pipeline
1. **Continuous Integration**: GitHub Actions for automated building
2. **Multi-Platform Builds**: Windows, Linux builds on each release
3. **Automated Testing**: Integration tests on target platforms
4. **Release Automation**: Automatic upload to GitHub releases
5. **Store Submission**: Automated Flathub submission process

### Extensibility Design

#### Plugin Architecture
```python
class AnalysisPlugin:
    def get_tab_widget(self) -> QWidget:
        pass

    def get_menu_actions(self) -> List[QAction]:
        pass

    def get_translations(self) -> Dict[str, str]:
        pass  # Plugin-specific translations
```

#### Custom Function Registration
- Allow users to define custom fitting functions
- Support user-defined uncertainty propagation formulas
- Enable custom data import/export formats
- Plugin translations integrated with main translation system

This design leverages the strengths of PyQt6 for the GUI while building on the robust foundation of established Python scientific libraries, ensuring reliability and maintainability while avoiding unnecessary reimplementation of well-tested functionality. The internationalization support ensures the application can be used by scientists worldwide in their preferred language.