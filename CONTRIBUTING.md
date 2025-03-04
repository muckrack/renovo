# Contributing to Renovo

Thank you for considering contributing to Renovo! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md) that all contributors are expected to follow. Please read the full text to understand what actions will and will not be tolerated.

## Development Setup

### Prerequisites

- Python 3.7 or higher
- [pipx](https://github.com/pypa/pipx) for installing Python application tools
- [uv](https://github.com/astral-sh/uv) for dependency management
- [flit](https://flit.pypa.io/) for building the package

Install the required tools:
```bash
# Install pipx
python -m pip install --user pipx
python -m pipx ensurepath

# Install tools with pipx
pipx install uv
pipx install flit
```

### Setting up your development environment

1. Fork the repository on GitHub

2. Clone your fork:
   ```bash
   git clone git@github.com:<YOUR GITHUB USERNAME>/renovo.git
   cd renovo
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   uv pip install -e ".[dev,test]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git commit -m "Description of your changes"
   ```

3. Run tests to ensure everything works as expected:
   ```bash
   make test
   ```

4. Format and lint your code:
   ```bash
   make lint
   ```

5. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a pull request from your fork to the main repository

## Code Style

Renovo uses [ruff](https://github.com/astral-sh/ruff) for code formatting and linting. The configuration is defined in `pyproject.toml`.

Key style points:
- Line length is 119 characters
- Follow PEP 8 conventions
- Use docstrings for all public functions, classes, and methods
- Sort imports using isort (via ruff)

You can format your code with:
```bash
make lint
```

## Testing

Renovo uses pytest for testing. Tests are located in the `tests/` directory.

To run tests:
```bash
make test
```

When adding new features, please include appropriate tests.

## Pull Request Process

1. Update the README.md and/or documentation with details of any interface changes if applicable.
2. Update the CHANGELOG.md with notes on your changes under the "Unreleased" section.
3. Submit your pull request against the `main` branch.
4. Ensure that all CI checks pass on your pull request.

## Versioning

Renovo uses [tbump](https://github.com/TankerHQ/tbump) for version management. Version numbers follow the [SemVer](https://semver.org/) convention.

## Building and Distribution

To build the package:
```bash
make dist
```

## Getting Help

If you have questions or need help with the contribution process, please open an issue on the GitHub repository.

Thank you for contributing to Renovo!
