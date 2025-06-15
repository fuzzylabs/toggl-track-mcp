# Contributing to Toggl Track MCP Server

Thank you for your interest in contributing to the Toggl Track MCP Server! This document provides guidelines and information for contributors.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Issues

- Use the [GitHub Issues](https://github.com/fuzzylabs/toggl-track-mcp/issues) page
- Check if the issue already exists before creating a new one
- Provide detailed information including:
  - Python version
  - Operating system
  - Steps to reproduce the issue
  - Expected vs actual behavior
  - Relevant logs or error messages

### Suggesting Features

- Open a [GitHub Discussion](https://github.com/fuzzylabs/toggl-track-mcp/discussions) for feature requests
- Explain the use case and expected behavior
- Consider if the feature aligns with the project's goals

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/toggl-track-mcp.git
   cd toggl-track-mcp
   ```

2. **Set up development environment**
   ```bash
   # Install in development mode
   pip install -e ".[dev]"
   
   # Set up pre-commit hooks (optional)
   pre-commit install
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Workflow

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use Black for code formatting: `black toggl_track_mcp/`
   - Sort imports with isort: `isort toggl_track_mcp/`
   - Lint with ruff: `ruff check toggl_track_mcp/`

2. **Type Hints**
   - Add type hints to all functions and methods
   - Run mypy for type checking: `mypy toggl_track_mcp/`

3. **Testing**
   - Write tests for new functionality
   - Maintain or improve test coverage
   - Run tests: `pytest`
   - Run with coverage: `pytest --cov=toggl_track_mcp`

4. **Documentation**
   - Update docstrings for new functions/classes
   - Update README.md if needed
   - Add comments for complex logic

### Making Changes

1. **API Client Changes**
   - Test against real Toggl API when possible
   - Handle rate limiting appropriately
   - Add proper error handling for new endpoints

2. **MCP Tools**
   - Follow existing tool patterns
   - Add comprehensive input validation
   - Include helpful error messages
   - Document tool parameters clearly

3. **Breaking Changes**
   - Avoid breaking changes when possible
   - If necessary, increment version appropriately
   - Document breaking changes in commit messages

### Testing

#### Unit Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rate_limiter.py

# Run with verbose output
pytest -v
```

#### Integration Tests
```bash
# Test with real API (requires TOGGL_API_TOKEN)
python scripts/test_connection.py
```

#### Test Environment Variables
For testing, you can use these environment variables:
```bash
export TOGGL_API_TOKEN=your_test_token
export PYTEST_CURRENT_TEST=1  # Skips authentication in tests
```

### Submitting Pull Requests

1. **Before submitting**
   - Ensure all tests pass
   - Run the full linting suite
   - Update documentation if needed
   - Add entry to CHANGELOG.md (if applicable)

2. **Pull Request Guidelines**
   - Use a clear, descriptive title
   - Reference related issues: "Fixes #123"
   - Describe what the PR does and why
   - Include testing instructions
   - Keep PRs focused and atomic

3. **PR Checklist**
   - [ ] Tests pass locally
   - [ ] Code follows style guidelines
   - [ ] New functionality includes tests
   - [ ] Documentation updated
   - [ ] No breaking changes (or clearly documented)

### Review Process

1. **Automated Checks**
   - GitHub Actions will run tests and linting
   - All checks must pass before review

2. **Code Review**
   - Maintainers will review code for quality, style, and functionality
   - Be responsive to feedback and suggestions
   - Make requested changes promptly

3. **Merge Requirements**
   - At least one approval from a maintainer
   - All GitHub Action checks passing
   - Up-to-date with main branch

## Development Guidelines

### Error Handling
- Use specific exception types when possible
- Provide helpful error messages
- Log errors appropriately (but never log API tokens)
- Handle Toggl API edge cases gracefully

### Rate Limiting
- Respect Toggl's API rate limits
- Use the existing rate limiter for all API calls
- Handle 429 responses with proper backoff

### Security
- Never log or expose API tokens
- Validate all inputs
- Use read-only API operations only
- Follow secure coding practices

### Performance
- Minimize API calls when possible
- Cache responses when appropriate
- Use efficient data structures
- Consider memory usage for large datasets

## Release Process

1. **Version Bumping**
   - Follow semantic versioning (semver)
   - Update version in `pyproject.toml`
   - Update CHANGELOG.md

2. **Release Checklist**
   - All tests pass
   - Documentation is up-to-date
   - CHANGELOG.md includes all changes
   - Version bump is appropriate

3. **Creating Releases**
   - Maintainers will create GitHub releases
   - Releases trigger automatic PyPI deployment
   - Include release notes with notable changes

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/fuzzylabs/toggl-track-mcp/discussions)
- **Issues**: Use [GitHub Issues](https://github.com/fuzzylabs/toggl-track-mcp/issues)
- **Email**: Contact [tom@fuzzylabs.ai](mailto:tom@fuzzylabs.ai)

## Recognition

Contributors will be:
- Listed in the project's README
- Mentioned in release notes for significant contributions
- Added to the AUTHORS file

Thank you for contributing to make Toggl Track data more accessible to AI assistants! 🎉