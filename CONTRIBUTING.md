# Contributing to typedkafka

Thank you for your interest in contributing to typedkafka! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check the issue tracker to avoid duplicates
2. Collect relevant information (OS, Python version, error messages)

When creating a bug report, include:
- A clear title and description
- Steps to reproduce the issue
- Expected vs actual behavior
- Code samples if applicable
- Your environment details

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:
- Use a clear and descriptive title
- Provide a detailed description of the proposed feature
- Explain why this enhancement would be useful
- Include code examples if applicable

### Pull Requests

1. **Fork the repository** and create your branch from `main`

2. **Set up your development environment:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/typedkafka.git
   cd typedkafka
   pip install -e ".[dev]"
   ```

3. **Make your changes:**
   - Write clear, documented code
   - Add type hints to all functions
   - Include comprehensive docstrings
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes:**
   ```bash
   # Run tests
   pytest

   # Run linter
   ruff check .

   # Run type checker
   mypy src
   ```

5. **Commit your changes:**
   - Use clear, descriptive commit messages
   - Follow conventional commits format (optional but recommended)
   - Reference related issues

6. **Submit a pull request:**
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure all CI checks pass

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use ruff for linting
- Maximum line length: 100 characters
- Use type hints for all function signatures

### Documentation

- Add docstrings to all public classes and methods
- Follow Google docstring format
- Include examples in docstrings where helpful
- Keep README.md up to date

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Test edge cases and error conditions

### Type Hints

- Add type hints to all function signatures
- Use `from typing import` for generic types
- Avoid using `Any` when possible
- Use `Optional` for nullable types

## Project Structure

```
typedkafka/
├── src/typedkafka/      # Main package code
│   ├── producer.py      # Producer with transactions and batch send
│   ├── consumer.py      # Consumer with rebalance callbacks
│   ├── admin.py         # Admin client for topic management
│   ├── config.py        # Configuration builders with validation
│   ├── testing.py       # Mock implementations for unit tests
│   ├── exceptions.py    # Custom exception hierarchy
│   ├── aio.py           # Async producer and consumer
│   ├── retry.py         # Retry decorator and policy
│   └── serializers.py   # Pluggable serializer framework
├── tests/               # Test files
├── .github/             # GitHub Actions workflows
└── docs/                # Documentation (if applicable)
```

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
