# Requirements Document

## Introduction

ANAFIS is a detachable-notebook desktop application designed for scientific computing and data analysis. The application provides a multi-tab interface where each major capability (Spreadsheet, Curve-Fitting, Wolfram-like Solver, Monte-Carlo Simulator) operates as its own closable and detachable tab spawned from a central Home Menu. The application includes GPU acceleration where beneficial, uncertainty calculation capabilities, and inter-tab communication through a shared data bus.

## Requirements

### Requirement 1

**User Story:** As a scientist, I want a multi-tab desktop application with a persistent home menu, so that I can organize different analysis tools in separate workspaces while maintaining easy access to create new tools.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL display a Home Menu as the first tab that cannot be closed
2. WHEN a user clicks on tool creation buttons in the Home Menu THEN the system SHALL create new tabs for Spreadsheet, Fitting, Solver, or Monte-Carlo tools
3. WHEN a user attempts to close the Home Menu tab THEN the system SHALL prevent the closure and maintain the tab as index 0
4. WHEN a user closes any non-Home tab THEN the system SHALL remove the tab and preserve any unsaved work through auto-save functionality
5. WHEN the application is restarted THEN the system SHALL restore previously open tabs and their states

### Requirement 2

**User Story:** As a researcher, I want detachable tabs that can become independent windows, so that I can work with multiple tools simultaneously across different monitors.

#### Acceptance Criteria

1. WHEN a user drags a tab out of the main window THEN the system SHALL create an independent detached window containing that tab's content
2. WHEN a detached window is closed THEN the system SHALL optionally reattach the content to the main window or close it permanently based on user choice
3. WHEN tabs are detached THEN the system SHALL maintain data bus communication between detached windows and the main application
4. WHEN a user drags a detached window back to the main window THEN the system SHALL reattach it as a tab

### Requirement 3

**User Story:** As a data analyst, I want a spreadsheet tool with formula evaluation and unit support, so that I can perform calculations with proper unit handling and dependency tracking.

#### Acceptance Criteria

1. WHEN a user creates a new spreadsheet tab THEN the system SHALL provide a grid interface for data entry and formula input
2. WHEN a user enters a formula in a cell THEN the system SHALL evaluate the formula using topological sorting for dependency resolution
3. WHEN a formula references other cells THEN the system SHALL automatically update dependent cells when source cells change
4. WHEN a user specifies units in formulas THEN the system SHALL handle unit conversions and validate unit compatibility using the pint library
5. WHEN formulas are evaluated THEN the system SHALL use GPU acceleration where beneficial and fall back to CPU computation when necessary

### Requirement 4

**User Story:** As a scientist, I want a curve fitting tool with multiple algorithms and visualization, so that I can fit mathematical models to experimental data with uncertainty quantification.

#### Acceptance Criteria

1. WHEN a user creates a fitting tab THEN the system SHALL provide interfaces for data source selection, model definition, and parameter estimation
2. WHEN a user selects data sources THEN the system SHALL support input from spreadsheet tabs, CSV files, or other tabs via the data bus
3. WHEN a user defines a fitting model THEN the system SHALL support custom formula input with parameter specification and constraints
4. WHEN a user initiates fitting THEN the system SHALL provide ODR (Orthogonal Distance Regression), Bayesian MCMC, and Levenberg-Marquardt methods with extensibility for additional multidimensional fitting algorithms
5. WHEN fitting is in progress THEN the system SHALL display real-time progress updates and intermediate results in the plot
6. WHEN fitting completes THEN the system SHALL display best-fit parameters with uncertainties, covariance matrices, and goodness-of-fit statistics
7. WHEN fitting results are available THEN the system SHALL provide visualization for 2-5 dimensional fittings (x,y,z,color, and time slider with configurable parameter mapping) and alternative visualization for 5+ dimensions using VisPy with interactive controls

### Requirement 5

**User Story:** As a student, I want a Wolfram-like equation solver with step-by-step solutions, so that I can understand mathematical problem-solving processes and verify my work.

#### Acceptance Criteria

1. WHEN a user creates a solver tab THEN the system SHALL provide a LaTeX input editor with live preview
2. WHEN a user enters a mathematical expression THEN the system SHALL display the formatted equation in real-time
3. WHEN a user requests solution THEN the system SHALL provide step-by-step solution process using SymPy
4. WHEN solutions are generated THEN the system SHALL display each step with LaTeX formatting and explanatory text
5. WHEN solutions include graphable functions THEN the system SHALL provide optional visualization plots
6. WHEN solutions are complete THEN the system SHALL offer export options for LaTeX, PNG, and PDF formats
7. WHEN mathematical operations are requested THEN the system SHALL support variable solving, integration, differentiation, differential equations, and additional symbolic mathematics operations

### Requirement 6

**User Story:** As a researcher, I want Monte-Carlo simulation capabilities, so that I can generate synthetic datasets with specified parameter distributions and propagate uncertainties.

#### Acceptance Criteria

1. WHEN a user creates a Monte-Carlo tab THEN the system SHALL provide interfaces for model definition and parameter specification
2. WHEN a user defines simulation parameters THEN the system SHALL support multiple probability distributions (Normal, Uniform, etc.) with configurable parameters
3. WHEN a user initiates simulation THEN the system SHALL generate synthetic data using the specified model and parameter distributions
4. WHEN simulation is running THEN the system SHALL display progress updates and intermediate statistics with optional real-time visualization
5. WHEN simulation completes THEN the system SHALL provide histogram visualization and statistical summaries
6. WHEN simulation results are available THEN the system SHALL offer options to send generated data to fitting tabs via the data bus

### Requirement 7

**User Story:** As a scientist, I want floating utility tools for quick calculations, so that I can perform uncertainty calculations and solve simple equations without creating full tabs.

#### Acceptance Criteria

1. WHEN a user presses F9 THEN the system SHALL display a floating uncertainty calculator dialog
2. WHEN a user presses Alt+S THEN the system SHALL display a floating quick solver dialog
3. WHEN floating tools are open THEN the system SHALL allow non-modal interaction with the main application
4. WHEN calculations are performed in floating tools THEN the system SHALL provide copy/paste functionality to transfer results
5. WHEN floating tools are closed THEN the system SHALL preserve their last-used settings for the next session
6. WHEN uncertainty propagation is requested THEN the system SHALL provide symbolic uncertainty propagation formulas for user-defined expressions and calculate final results with uncertainties when given variable values and errors
7. WHEN uncertainty formulas are generated THEN the system SHALL render the resulting propagation formula in LaTeX format

### Requirement 8

**User Story:** As a data analyst, I want inter-tab communication capabilities, so that I can share data between different analysis tools seamlessly.

#### Acceptance Criteria

1. WHEN tabs generate or modify data THEN the system SHALL broadcast data availability through a shared data bus
2. WHEN tabs need external data THEN the system SHALL provide interfaces to subscribe to data bus updates
3. WHEN data is transferred between tabs THEN the system SHALL maintain data integrity and unit information
4. WHEN data bus communication occurs THEN the system SHALL work across detached windows and the main application
5. WHEN data formats differ between tools THEN the system SHALL provide automatic conversion where possible

### Requirement 9

**User Story:** As a user, I want persistent application state and internationalization support, so that my work is preserved between sessions and I can use the application in my preferred language.

#### Acceptance Criteria

1. WHEN the application closes THEN the system SHALL save all open tabs, their states, and user preferences to HDF5 format
2. WHEN the application starts THEN the system SHALL restore the previous session state including open tabs and their content
3. WHEN the user changes language settings THEN the system SHALL update all interface elements using the babel internationalization framework
4. WHEN translation files are updated THEN the system SHALL support hot-reloading of language changes without restart
5. WHEN user preferences are modified THEN the system SHALL persist settings across application sessions

### Requirement 10

**User Story:** As a power user, I want GPU acceleration and performance optimization, so that I can handle large datasets and complex calculations efficiently.

#### Acceptance Criteria

1. WHEN GPU hardware is available THEN the system SHALL automatically detect and utilize CUDA or OpenCL capabilities for fitting algorithms and Monte Carlo simulations
2. WHEN GPU acceleration is unavailable THEN the system SHALL gracefully fall back to optimized CPU computation using NumPy and Numba
3. WHEN large datasets are processed THEN the system SHALL use memory-mapped files and chunked processing to manage memory efficiently
4. WHEN computationally intensive operations run THEN the system SHALL provide progress indicators and cancellation options
5. WHEN performance bottlenecks occur THEN the system SHALL log performance metrics for optimization analysis
6. WHEN users have multiple GPUs THEN the system SHALL allow GPU selection in application settings