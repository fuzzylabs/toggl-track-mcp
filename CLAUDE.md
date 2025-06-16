# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This is a Model Context Protocol (MCP) server that exposes Toggl Track time tracking data as AI tools. The server runs in two modes:

1. **stdio mode**: For direct integration with AI assistants like Claude Desktop and Cursor
2. **HTTP mode**: For remote access via web APIs (deployed on Render)

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
```

### Testing
```bash
uv run pytest              # Run all tests
uv run pytest tests/test_rate_limiter.py -v  # Run specific test file
uv run pytest -k "test_name" # Run specific test
```

### Code Quality
```bash
uv run ruff check toggl_track_mcp/     # Lint code
uv run black toggl_track_mcp/          # Format code  
uv run isort toggl_track_mcp/          # Sort imports
uv run mypy toggl_track_mcp/           # Type checking
```

### Development Server
```bash
uv run uvicorn toggl_track_mcp.server:app --reload  # HTTP server at localhost:8000
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

## Common Issues

- **Import Errors**: Use `uv run` commands or ensure proper virtual environment activation
- **API Token**: Server gracefully handles missing tokens for testing, but tools will fail at runtime
- **Rate Limiting**: Built-in token bucket prevents API rate limit errors
- **Type Checking**: All API responses use Pydantic models for type safety