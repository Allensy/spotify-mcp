# Testing Guide for Spotify MCP

This document describes the comprehensive test suite for the Spotify MCP server, including all improvements made for robustness and better UX.

## Test Overview

The test suite covers **5 major categories** with **50+ test cases**:

1. **Structure Tests** - Module organization and imports
2. **Server Integration Tests** - MCP server and tool registration  
3. **Error Handling Tests** - Timeouts, error messages, robustness
4. **Authentication Flow Tests** - OAuth flows and token handling
5. **Spotify Tools Tests** - API integration (requires credentials)

## Quick Start

```bash
# Run all tests
./scripts/run-tests.sh

# Run a specific category
pytest tests/test_error_handling.py -v

# Run with coverage report
pytest --cov=spotify_mcp --cov-report=html
```

## Test Categories

### 1. Error Handling Tests (`test_error_handling.py`)

Tests all the improvements we made to prevent hanging and provide better error messages.

**Test Classes:**

- `TestAuthenticationErrorHandling` - Missing tokens, auth failures
- `TestTimeoutHandling` - Operation timeouts
- `TestSignalHandling` - Container shutdown signals
- `TestConfigValidation` - Environment variable validation
- `TestMCPServerRobustness` - Exception handling

**Key Tests:**

```python
# Missing token produces helpful error
test_missing_token_error_message()

# open_browser=False prevents hanging
test_open_browser_false_in_client()

# Timeout decorator works correctly
test_timeout_decorator_exists()
test_timeout_error_message()

# Signal handler uses os._exit for forceful shutdown
test_signal_handler_uses_os_exit()

# Stdin monitor detects disconnects
test_stdin_monitor_exists()
test_stdin_monitor_logic()
```

**What We Test:**

- ✅ Error messages include actionable instructions
- ✅ `open_browser=False` prevents browser opening in Docker
- ✅ Timeouts prevent infinite hangs (15s default)
- ✅ Signal handler uses `os._exit()` not `sys.exit()`
- ✅ Stdin monitor detects when Cursor disconnects
- ✅ Config validation provides clear error messages

### 2. Authentication Flow Tests (`test_auth_flow.py`)

Tests the improved OAuth flows with automatic browser opening.

**Test Classes:**

- `TestAuthInitModule` - Module imports and structure
- `TestAutoAuthFlow` - Browser-based OAuth (`--auto`)
- `TestManualAuthFlow` - Copy-paste OAuth (fallback)
- `TestAuthInitMain` - Main function behavior
- `TestCallbackHTMLResponses` - Success/failure pages

**Key Tests:**

```python
# Auto auth starts HTTP server on correct port
test_auto_auth_starts_server()

# Attempts to open browser automatically
test_auto_auth_attempts_browser_open()

# Falls back to manual when browser fails
test_auto_auth_falls_back_to_manual()

# Manual auth prompts for redirect URL
test_manual_auth_prompts_for_url()

# Handles empty/invalid input gracefully
test_manual_auth_handles_empty_input()
test_manual_auth_handles_invalid_url()

# Main uses correct flow based on flags
test_main_uses_auto_when_flag_present()
test_main_uses_manual_without_flag()
```

**What We Test:**

- ✅ HTTP server starts on port 8888 for callbacks
- ✅ Browser opens automatically with auth URL
- ✅ Fallback to manual input when browser fails
- ✅ Empty/invalid input handled gracefully
- ✅ `--auto` flag enables automatic flow
- ✅ Success/failure HTML pages render correctly

### 3. Server Integration Tests (`test_server.py`)

Tests MCP server creation and tool registration.

**What We Test:**

- ✅ MCP server object created correctly
- ✅ All 25+ tools registered
- ✅ All Spotify functions exported
- ✅ Config validation works

### 4. Spotify Tools Tests (`test_tools.py`)

Integration tests with real Spotify API (requires credentials).

**What We Test:**

- ✅ Search (tracks, albums, artists, playlists)
- ✅ Playback info (currently playing, queue)
- ✅ Library management (liked songs, playlists)
- ✅ Device management (list, transfer)
- ✅ User analytics (top tracks, artists, recently played)

**Note:** These tests are skipped in CI when credentials aren't available.

### 5. Structure Tests (`test_structure.py`)

Basic structure and import tests to ensure everything is wired correctly.

## Running Tests Locally

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Or install all dev dependencies
pip install -r requirements.txt
```

### Run All Tests

```bash
# Using the test runner script (recommended)
./run-tests.sh

# Or using pytest directly
pytest -v

# With coverage report
pytest --cov=spotify_mcp --cov-report=html
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Single test file
pytest tests/test_error_handling.py -v

# Single test class
pytest tests/test_error_handling.py::TestAuthenticationErrorHandling -v

# Single test function
pytest tests/test_error_handling.py::TestAuthenticationErrorHandling::test_missing_token_error_message -v

# Tests matching a pattern
pytest -k "timeout" -v
pytest -k "auth" -v
```

### Run Without Spotify Credentials

```bash
# Skip integration tests that require Spotify API
pytest -m "not integration" -v

# Or just run unit tests
pytest tests/test_error_handling.py tests/test_auth_flow.py tests/test_server.py -v
```

## Test Configuration

### Fixtures (conftest.py)

```python
# Mock Spotify client
mock_spotify_client

# Test configuration
test_config

# Test environment variables
test_env

# Mock OAuth
mock_spotify_oauth

# Clean imports between tests
clean_imports
```

### Markers

```python
# Skip if credentials not available
@pytest.mark.skipif(not _has_spotify_credentials(), ...)

# Mark as integration test
@pytest.mark.integration
```

## CI/CD Integration

Tests run automatically on GitHub Actions:

```yaml
# .github/workflows/ci.yml
- name: Run tests
  run: pytest -v --cov=spotify_mcp

- name: Run linters
  run: |
    black --check .
    ruff check .
```

**Test Matrix:**

- Python 3.10, 3.11, 3.12
- Ubuntu, macOS, Windows (optional)
- With/without Spotify credentials

## Writing New Tests

### Error Handling Test Example

```python
def test_new_error_message(self):
    """Test that new feature produces helpful error."""
    with pytest.raises(RuntimeError) as exc_info:
        # Call function that should fail
        some_function()
    
    error_msg = str(exc_info.value)
    assert "helpful message" in error_msg
    assert "what to do" in error_msg
```

### Auth Flow Test Example

```python
@patch('spotify_mcp.cli.auth_init.webbrowser')
def test_new_auth_feature(self, mock_browser):
    """Test new authentication feature."""
    mock_browser.open.return_value = True
    
    result = auth_function()
    
    assert result is True
    mock_browser.open.assert_called_once()
```

### Async Test Example

```python
@pytest.mark.asyncio
async def test_async_feature(self):
    """Test async Spotify function."""
    result = await async_spotify_function()
    
    assert result is not None
    assert "expected" in result
```

## Test Coverage Goals

Current coverage: **~85%** of new error handling code

Target coverage:

- Error handling: **95%+**
- Auth flows: **90%+**
- Server integration: **100%**
- Spotify tools: **80%+** (integration dependent)

## Debugging Tests

### Run with verbose output

```bash
pytest -vv tests/test_error_handling.py
```

### Show print statements

```bash
pytest -s tests/test_error_handling.py
```

### Drop into debugger on failure

```bash
pytest --pdb tests/test_error_handling.py
```

### Run last failed tests only

```bash
pytest --lf
```

## Common Issues

### Import Errors

```bash
# Make sure PYTHONPATH includes src
export PYTHONPATH=/Users/allenjacobson/Dev/spotify-mcp/src
pytest
```

### Mock Issues

```bash
# Clean imports between tests
pytest --cache-clear
```

### Async Test Issues

```bash
# Make sure pytest-asyncio is installed
pip install pytest-asyncio
```

## Test Maintenance

### When Adding New Features

1. **Add error handling tests** if feature can fail
2. **Add auth tests** if feature touches authentication
3. **Add integration tests** if feature calls Spotify API
4. **Update test count** in this document

### When Fixing Bugs

1. **Add regression test** that reproduces the bug
2. **Verify test fails** before fix
3. **Verify test passes** after fix
4. **Keep test** to prevent regression

### Before Releasing

```bash
# Run full test suite
./run-tests.sh

# Check coverage
pytest --cov=spotify_mcp --cov-report=term-missing

# Run linters
black .
ruff check .
```

## Summary

Our comprehensive test suite ensures:

- ✅ **No more hanging** - Timeouts and error messages tested
- ✅ **Better UX** - Auth flows thoroughly tested
- ✅ **Clean shutdown** - Signal handling verified
- ✅ **Clear errors** - All error messages validated
- ✅ **Robust code** - Edge cases covered

Run `./run-tests.sh` before each commit to maintain quality! 🧪✨
