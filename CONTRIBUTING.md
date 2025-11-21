# Contributing to Soseki

Thank you for your interest in contributing to Soseki! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/soseki.git`
3. Create a virtual environment: `python -m venv .venv`
4. Activate it: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Development Workflow

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest`
4. Run tests with coverage: `pytest --cov=ssk`
5. Commit your changes: `git commit -S -m "Description of changes"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Open a Pull Request

## Code Standards

- Follow PEP 8 style guidelines
- Write docstrings for functions and classes
- Add tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ssk

# Run specific test file
pytest tests/unittests/test_example.py
```

## Project Structure

```
soseki/
├── ssk/              # Core framework package
├── app/              # Example application
├── tests/            # Test suite
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## Reporting Issues

- Use the GitHub issue tracker
- Provide a clear description
- Include steps to reproduce
- Mention your Python version and OS

## Pull Request Guidelines

- Keep PRs focused on a single feature/fix
- Update CHANGELOG.md
- Ensure all tests pass
- Add tests for new functionality
- Update documentation if needed

## Questions?

Feel free to open an issue for questions or discussion.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
