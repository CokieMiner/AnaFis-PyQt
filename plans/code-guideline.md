The project uses several tools for code quality:

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- Try as much to not use the `Any` type for type hints nor type ignores

ANAFIS follows a functional programming approach with immutable data structures:

- **Pure Functions**: Business logic implemented as side-effect-free functions
- **Immutable State**: Application state managed through NamedTuples and dataclasses
- **PyQt6 Integration**: Minimal classes for GUI, maximum functional core
- **Library Reuse**: Leverages existing Python scientific libraries