# Contributing to Spotify MCP

First off, thank you for considering contributing to Spotify MCP! It's people like you that make Spotify MCP such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include error messages and stack traces**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior and explain which behavior you expected to see instead**
* **Explain why this enhancement would be useful**

### Pull Requests

* Fill in the required template
* Follow the Python style guide (PEP 8)
* Include type hints for all functions
* Write comprehensive docstrings
* Add tests for new functionality
* Update documentation as needed
* Ensure all tests pass

## Development Process

### Setting Up Your Development Environment

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/your-username/spotify-mcp.git
   cd spotify-mcp
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks** (optional but recommended)

   ```bash
   pre-commit install
   ```

### Development Workflow

1. **Create a new branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   * Write clean, readable code
   * Follow existing patterns
   * Add type hints
   * Write docstrings

3. **Run tests**

   ```bash
   make test
   # or
   pytest
   ```

4. **Run linters**

   ```bash
   make lint
   # or
   black src/
   mypy src/
   pylint src/
   ```

5. **Update documentation**
   * Update docstrings
   * Update README if needed
   * Add examples if applicable

6. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: Add new feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   * `feat:` for new features
   * `fix:` for bug fixes
   * `docs:` for documentation changes
   * `test:` for test changes
   * `refactor:` for code refactoring
   * `chore:` for maintenance tasks

7. **Push and create a pull request**

   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style

* **PEP 8**: Follow Python PEP 8 style guide
* **Line length**: 79 characters maximum
* **Type hints**: Use type hints for all function signatures
* **Docstrings**: Google-style docstrings for all public functions/classes
* **Imports**: Organized in three groups (standard lib, third-party, local)
* **Naming**:
  * `snake_case` for functions and variables
  * `PascalCase` for classes
  * `UPPER_CASE` for constants

Example:

```python
from typing import List, Optional

def search_spotify(
    query: str,
    search_type: str = "track",
    limit: int = 5
) -> str:
    """Search Spotify for tracks, albums, artists, or playlists.

    Args:
        query: The search query string.
        search_type: The type ('track'|'album'|'artist'|'playlist').
        limit: Maximum number of results. Defaults to 5.

    Returns:
        A formatted string of results or error message.

    Raises:
        SpotifyException: If the API request fails.
    """
    # Implementation
    pass
```

### Testing

* Write tests for all new functionality
* Maintain test coverage above 80%
* Use pytest for testing
* Use meaningful test names: `test_<function>_<scenario>_<expected_result>`

```python
def test_search_spotify_with_valid_query_returns_results():
    """Test that search returns results for valid query."""
    result = search_spotify("Beatles", "artist", limit=5)
    assert "Beatles" in result
```

### Documentation

* Update README.md for user-facing changes
* Update docstrings for code changes
* Add examples in docs/ for new features
* Keep CHANGELOG.md updated

## Project Structure

```
spotify-mcp/
├── src/spotify_mcp/      # Source code
│   ├── __init__.py
│   ├── server.py          # MCP server
│   ├── tools.py           # Spotify API tools
│   ├── config.py          # Configuration
│   ├── cli/               # CLI commands
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── docs/                  # Documentation
├── .github/               # GitHub workflows
├── pyproject.toml         # Project metadata
└── README.md
```

## Release Process

Releases are handled by maintainers:

1. Update version in `src/spotify_mcp/__version__.py`
2. Update CHANGELOG.md
3. Create a new tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions will automatically publish to PyPI

## Getting Help

* **Questions?** Open a [Discussion](https://github.com/yourusername/spotify-mcp/discussions)
* **Found a bug?** Open an [Issue](https://github.com/yourusername/spotify-mcp/issues)
* **Want to contribute but don't know where to start?** Look for issues labeled `good first issue`

## Recognition

Contributors will be recognized in:

* AUTHORS.md file
* Release notes
* Project README

Thank you for contributing to Spotify MCP! 🎵

