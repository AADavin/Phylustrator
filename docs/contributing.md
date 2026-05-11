# Contributing to Phylustrator

Thank you for your interest in contributing to Phylustrator! We welcome contributions from the community, whether they are bug reports, feature requests, documentation improvements, or code changes.

Phylustrator is a Python library for rendering customizable phylogenetic trees. This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:

- Be kind and respectful to all community members
- Maintain a professional tone in all interactions
- Be inclusive and consider diverse perspectives
- Report any code of conduct violations to the project maintainers

## Getting Started with Development

### Prerequisites

- Python 3.8 or higher
- Git
- A fork of the repository (for submitting pull requests)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/AADavin/Phylustrator.git
   cd Phylustrator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

This ensures code quality checks run automatically before each commit.

## Code Style and Quality

### Linting and Formatting

We use `ruff` to maintain consistent code style. Your code must pass ruff checks before being merged.

Run linting locally:
```bash
ruff check .
ruff format .
```

### Type Hints

Type hints are required for all new code. They improve code clarity and enable better static analysis.

```python
def calculate_tree_layout(tree: Tree, width: float) -> dict[str, Any]:
    """Calculate layout coordinates for phylogenetic tree."""
    ...
```

### Docstrings

All public functions, classes, and modules must include docstrings in Google style format.

```python
def render_tree(tree: Tree, output_file: str = None) -> str:
    """Render a phylogenetic tree to SVG format.

    Args:
        tree: The phylogenetic tree to render.
        output_file: Optional path to write SVG output. If not provided,
            returns the SVG string.

    Returns:
        SVG representation of the tree as a string.

    Raises:
        ValueError: If the tree is empty or invalid.
    """
    ...
```

## Testing

### Running Tests

We use `pytest` for testing. All new features and bug fixes should include appropriate tests.

Run the test suite:
```bash
pytest tests/
```

Run tests with coverage report:
```bash
pytest tests/ --cov=phylustrator --cov-report=html
```

### Test Coverage

Aim for high test coverage for new code. While we don't enforce a strict minimum, new features should have meaningful test cases covering:

- Normal use cases
- Edge cases
- Error conditions

## Submitting Changes

### Pull Request Process

1. **Fork the repository** on GitHub

2. **Create a feature branch** from the `main` branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

   Use descriptive branch names like `feature/svg-exports`, `fix/rendering-bug`, or `docs/api-guide`.

3. **Make your changes** and commit with clear, descriptive messages:
   ```bash
   git commit -m "Add tree rotation feature"
   ```

4. **Run tests locally** to ensure everything passes:
   ```bash
   pytest tests/
   ruff check .
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a pull request** on GitHub with:
   - A clear title describing the changes
   - A description explaining what the changes do and why
   - Reference to any related issues (use "Fixes #123" to auto-close issues)
   - Confirmation that tests pass and new tests are included

### Pull Request Guidelines

- Keep pull requests focused on a single feature or fix
- Include tests for new functionality
- Update documentation if needed
- Ensure all CI checks pass
- Be responsive to feedback and review comments

## Issue Guidelines

### Reporting Bugs

When reporting a bug, please include:

- **Version**: The version of Phylustrator you're using (e.g., 0.0.1)
- **Operating System**: Your OS and Python version
- **Minimal Reproduction**: A minimal, complete code example that reproduces the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Error Messages**: Full error tracebacks if applicable

Example bug report:
```
Version: 0.0.1
OS: Ubuntu 22.04, Python 3.10

When rendering a tree with Unicode characters in node names, I get the following error:

UnicodeEncodeError: 'ascii' codec can't encode character...

Minimal reproduction:
```python
from phylustrator import Tree
tree = Tree("(A:1,B:1)C;")
tree["A"].name = "α"
tree.render()
```
```

### Requesting Features

Feature requests are welcome! Please:

- Describe the feature and what problem it solves
- Provide use cases or examples
- Consider implementation complexity
- Be open to discussion about feasibility

## Questions and Support

If you have questions about contributing or need help getting started:

- Check existing issues and discussions
- Open a new discussion in the repository
- Reach out to the maintainers

## Documentation

### Updating Documentation

Documentation lives in the `docs/` directory and is built with MkDocs.

To view documentation locally:
```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Visit http://localhost:8000 to see the documentation.

### Writing Documentation

When documenting features:

- Include code examples
- Explain parameters clearly
- Document return values and exceptions
- Provide use cases and best practices
- Keep examples runnable and self-contained

## Release Process

Releases are managed by project maintainers. If you want to contribute, focus on:

- Code quality and testing
- Documentation
- Bug fixes

## Thank You!

Thank you for contributing to Phylustrator! Your efforts help make phylogenetic visualization accessible and powerful for the community.
