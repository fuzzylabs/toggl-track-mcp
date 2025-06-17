# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This is a Model Context Protocol (MCP) server that exposes Toggl Track time tracking data as AI tools. The server runs in two modes:

1. **stdio mode**: For direct integration with AI assistants like Claude Desktop and Cursor
2. **HTTP mode**: For remote access via web APIs (deployed on Render)

### API Coverage

- **Time Entries API**: Individual user time tracking data
- **Reports API**: Team-wide time entries and summaries (admin access required)
- **Workspace API**: Projects, clients, tags, and user management

### Core Components

- **`toggl_track_mcp/server.py`**: Main MCP server with FastMCP framework and FastAPI backend
- **`toggl_track_mcp/toggl_client.py`**: Centralized Toggl API client with rate limiting and typed models
- **`toggl_track_mcp/rate_limiter.py`**: Token bucket rate limiter for API requests
- **`tests/`**: Test suite for server functionality and rate limiting

### Tool Structure

All MCP tools follow a consistent pattern:
- Decorated with `@mcp.tool()` 
- Return structured data with standardized error handling: `{"error": str(e)}`
- Include filtering, pagination, and formatting capabilities
- Use the centralized `_get_toggl_client()` helper for API access

### Key Patterns

- **Environment Configuration**: Uses `python-dotenv` with fallbacks for missing tokens (testing compatibility)
- **Dual Mode Operation**: Server works as both stdio MCP server and HTTP API server
- **Type Safety**: Full Pydantic models for all Toggl API responses
- **Rate Limiting**: Built-in token bucket limiting for API requests
- **Authentication**: Optional API key authentication for HTTP mode

## Development Commands

### Installation and Setup
```bash
uv sync --dev               # Install dependencies including dev tools
uv run pre-commit install  # Install pre-commit hooks (recommended)
```

### Testing
```bash
uv run pytest              # Run all tests
uv run pytest --cov=toggl_track_mcp --cov-report=term-missing  # Run with coverage
uv run pytest tests/test_rate_limiter.py -v  # Run specific test file
uv run pytest -k "test_name" # Run specific test
```

### Code Quality
```bash
uv run ruff check toggl_track_mcp/     # Lint code
uv run black toggl_track_mcp/          # Format code  
uv run isort toggl_track_mcp/          # Sort imports
uv run mypy toggl_track_mcp/           # Type checking
uv run pre-commit run --all-files      # Run all pre-commit hooks
```

### Development Server
```bash
# HTTP server mode (for web access)
uv run uvicorn toggl_track_mcp.server:app --reload  # HTTP server at localhost:8000

# stdio mode (for Claude Code integration)
uv run python -m toggl_track_mcp  # MCP stdio server
```

### Test MCP Protocol
```bash
# Test tools list
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'

# Test specific tool
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_current_user", "arguments": {}}, "id": 1}'
```

## Claude Code Integration

To use this MCP server with Claude Code, add this configuration to your Claude Code settings:

```json
{
  "toggl-track": {
    "command": "/Users/your-username/.local/bin/uv",
    "args": [
      "run",
      "--directory",
      "/path/to/toggl-track-mcp",
      "python",
      "-m",
      "toggl_track_mcp"
    ],
    "env": {
      "TOGGL_API_TOKEN": "your_toggl_api_token_here"
    }
  }
}
```

**Setup steps:**
1. Get your Toggl API token from https://track.toggl.com/profile
2. Replace `/path/to/toggl-track-mcp` with the actual path to this repository
3. Replace `your_toggl_api_token_here` with your actual API token
4. Restart Claude Code

## Configuration Synchronization

⚠️ **Critical**: Multiple configuration files must be kept in sync:

1. **README.md**: Claude Desktop and Cursor configuration examples
2. **render.yaml**: Render deployment configuration 
3. **scripts/test_connection.py**: Connection testing script
4. **pyproject.toml**: Dependencies and tool configuration

When making changes to:
- **Dependencies**: Update both `pyproject.toml` and any README examples
- **Environment variables**: Update README configuration examples and `.env.example`
- **MCP tools**: Ensure examples in README reflect actual available tools
- **Deployment settings**: Sync between README and `render.yaml`

### Recommended Workflow for Configuration Changes

1. Make changes to the primary source (usually code)
2. Update README examples to match
3. Update deployment configs (`render.yaml`)
4. Test with `scripts/test_connection.py`
5. Verify all examples work end-to-end

## Environment Variables

Required:
- `TOGGL_API_TOKEN`: Toggl Track API token

Optional:
- `TOGGL_BASE_URL`: API base URL (defaults to v9 API)
- `TOGGL_WORKSPACE_ID`: Default workspace ID
- `MCP_API_KEY`: Authentication for HTTP mode
- `LOG_LEVEL`: Logging level (default: INFO)

## Testing Requirements

### Mandatory Test Coverage
- **All MCP tools**: Each `@mcp.tool()` function must have unit tests
- **API client methods**: Mock HTTP responses and test success/error cases  
- **New Pydantic models**: Test validation with real API response samples
- **Integration tests**: Test FastAPI endpoints for new features

### Testing Workflow (Required)
1. **Write tests BEFORE implementing features** (Test-Driven Development)
2. Run `uv run pytest --cov=toggl_track_mcp --cov-report=term-missing` - must pass 100%
3. Maintain >90% test coverage - CI will fail below this threshold
4. Add integration tests for user-facing features
5. All existing tests must continue to pass
6. **Pre-commit hooks automatically enforce** test coverage and missing test detection

### Test Templates

**MCP Tool Test Pattern:**
```python
@pytest.mark.asyncio
async def test_new_mcp_tool_success():
    """Test successful MCP tool execution."""
    # Mock the toggl client
    with patch('toggl_track_mcp.server._get_toggl_client') as mock_client:
        mock_client.return_value.some_method.return_value = expected_data
        
        # Call the MCP tool
        result = await new_mcp_tool(param1="value")
        
        # Assert expected output format
        assert "error" not in result
        assert result["expected_key"] == expected_value

@pytest.mark.asyncio  
async def test_new_mcp_tool_error_handling():
    """Test MCP tool error handling."""
    # Mock API error
    with patch('toggl_track_mcp.server._get_toggl_client') as mock_client:
        mock_client.side_effect = TogglAPIError("API Error")
        
        # Call the MCP tool
        result = await new_mcp_tool(param1="value")
        
        # Assert error response format
        assert "error" in result
        assert result["error"] == "API Error"
```

**API Client Test Pattern:**
```python
@pytest.mark.asyncio
async def test_api_client_method_success():
    """Test successful API client method."""
    # Mock HTTP response
    mock_response = {"id": 123, "name": "Test"}
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.request.return_value.json.return_value = mock_response
        mock_client.return_value.__aenter__.return_value.request.return_value.status_code = 200
        
        client = TogglAPIClient("fake_token")
        result = await client.new_method()
        
        assert isinstance(result, ExpectedModel)
        assert result.id == 123
```

### No Exceptions Policy
- **PRs without tests for new features will be rejected**
- **GitHub Actions must pass including test coverage checks**
- **Existing functionality cannot be broken by new changes**
- **Test coverage cannot decrease below 90%**

### Definition of Done for New Features

A feature is only complete when:
- ✅ Implementation works as specified
- ✅ Unit tests written and passing (TDD approach)
- ✅ Integration tests added if user-facing
- ✅ Test coverage maintained above 90%
- ✅ All existing tests still pass
- ✅ **Documentation updated** (see Documentation Requirements below)
- ✅ GitHub Actions pass completely

### Documentation Requirements

**All new features MUST include documentation updates:**

#### User-Facing Features (New MCP Tools)
- ✅ **README.md**: Add example queries in "What This Does" section
- ✅ **README.md**: Update "What You Can Access" table with new capabilities
- ✅ **README.md**: Add troubleshooting entries for common issues
- ✅ **README.md**: Update API testing examples if applicable

#### Admin-Only Features
- ✅ **README.md**: Add **(Admin only)** markers to examples
- ✅ **README.md**: Update "Team Features" section
- ✅ **README.md**: Add admin permission troubleshooting

#### Internal/Developer Features
- ✅ **CLAUDE.md**: Update architecture notes for new components
- ✅ **CLAUDE.md**: Update common patterns if new patterns introduced

#### API Changes
- ✅ **README.md**: Update API testing examples
- ✅ **README.md**: Update deployment configuration if needed

**🚨 No Exceptions Policy**: Features without proper documentation updates will be rejected in code review.

## Common Issues

- **Import Errors**: Use `uv run` commands or ensure proper virtual environment activation
- **API Token**: Server gracefully handles missing tokens for testing, but tools will fail at runtime
- **Rate Limiting**: Built-in token bucket prevents API rate limit errors
- **Type Checking**: All API responses use Pydantic models for type safety
- **Test Coverage**: Use `pytest-cov` to track coverage and identify untested code paths