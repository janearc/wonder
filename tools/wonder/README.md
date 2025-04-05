# Wonder CLI Tool

The Wonder CLI tool provides command-line utilities for managing Wonder framework projects.

## Installation

```bash
cd tools/wonder
poetry install
```

## Available Commands

- `wonder list-picokernels` - List all available picokernel applications
- `wonder refine KERNEL_NAME` - Generate a refined-kernel from a picokernel
- `wonder clean` - Clean build artifacts and temporary files
- `wonder format` - Format code using black and isort
- `wonder lint` - Run linting and type checking
- `wonder test` - Run tests with pytest
- `wonder docs` - Generate documentation
- `wonder build` - Build the project
- `wonder install` - Install the project in development mode
- `wonder example` - Run an example refinement of Cinder's kernel
- `wonder clean-venv` - Clean and reinstall the virtual environment

## Development

The Wonder CLI tool is built using:
- [Invoke](https://www.pyinvoke.org/) for task management
- [Poetry](https://python-poetry.org/) for dependency management
- [Rich](https://rich.readthedocs.io/) for terminal formatting

To contribute:
1. Install development dependencies: `poetry install --with dev`
2. Run tests: `poetry run pytest`
3. Format code: `poetry run black . && poetry run isort .`
4. Run type checking: `poetry run mypy src` 