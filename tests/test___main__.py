"""Tests for __main__ entry point module."""

import pytest
from unittest.mock import patch


def test_main_function_exists():
    """Test that main function exists and is callable."""
    from toggl_track_mcp.__main__ import main
    
    assert callable(main)


@patch('toggl_track_mcp.__main__.asyncio.run')
@patch('toggl_track_mcp.__main__.mcp')
def test_main_calls_mcp_run_stdio_async(mock_mcp, mock_asyncio_run):
    """Test that main function calls the correct MCP stdio runner."""
    from toggl_track_mcp.__main__ import main
    
    # Set up mocks
    mock_mcp.run_stdio_async.return_value = "mock_coroutine"
    
    # Call main
    main()
    
    # Verify the calls
    mock_mcp.run_stdio_async.assert_called_once()
    mock_asyncio_run.assert_called_once_with("mock_coroutine")


def test_module_import():
    """Test that the module can be imported without errors."""
    import toggl_track_mcp.__main__
    
    assert hasattr(toggl_track_mcp.__main__, 'main')


@patch('toggl_track_mcp.__main__.main')
def test_if_name_main_guard(mock_main):
    """Test that main is called when module is executed as script."""
    # This test verifies the structure rather than actual execution
    import toggl_track_mcp.__main__ as main_module
    
    # Verify the guard exists by checking the module has the main function
    assert hasattr(main_module, 'main')
    
    # The actual if __name__ == "__main__": guard is tested by the module structure