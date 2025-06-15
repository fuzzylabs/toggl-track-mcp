# Toggl Track MCP Server

A Model Context Protocol (MCP) server that provides read-only access to Toggl Track time tracking data. This server exposes Toggl Track's time entries, projects, clients, and other data through standardized MCP tools that can be used with AI assistants like Claude.

Built using Python and FastMCP, following the same architecture patterns as the [Capsule CRM MCP server](https://github.com/fuzzylabs/capsule-mcp).

## Features

- **Read-only access** to Toggl Track data for safe AI interaction
- **Rate limiting** with proper backoff (1 request/second, burst of 3)
- **Comprehensive time tracking tools** for data analysis and reporting
- **Timezone-aware** duration calculations for running time entries
- **Rich filtering and search** capabilities across time entries
- **Data aggregation** for time summaries and reporting
- **Error handling** for API rate limits and common Toggl API issues
- **FastAPI backend** with health checks and authentication
- **Pydantic models** for robust data validation

## Available Tools

### User & Session
- `get_current_user` - Get current user profile and session information
- `get_current_time_entry` - Get currently running time entry (if any)

### Time Entries
- `list_time_entries` - Get time entries with optional date range and filtering
- `get_time_entry_details` - Get detailed information about a specific time entry
- `search_time_entries` - Search time entries by description, project, client, or tags

### Projects & Organization
- `list_projects` - Get all projects for current workspace
- `list_clients` - Get all clients
- `list_workspaces` - Get available workspaces
- `list_tags` - Get all available tags

### Analytics & Reporting
- `get_time_summary` - Calculate total time with breakdowns by project, client, and tags

## Installation & Setup

### Prerequisites

- Python 3.10 or later
- A Toggl Track account with API access
- Your Toggl Track API token

### 1. Get Your Toggl API Token

1. Log in to your Toggl Track account
2. Go to [Profile Settings](https://track.toggl.com/profile)
3. Scroll down to find your API Token
4. Copy the token (you'll need it for configuration)

### 2. Clone and Install

```bash
git clone https://github.com/fuzzylabs/toggl-track-mcp.git
cd toggl-track-mcp
pip install -e .
```

### 3. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Required: Your Toggl Track API token
TOGGL_API_TOKEN=your_toggl_api_token_here

# Optional: Specific workspace ID (uses default if not specified)
TOGGL_WORKSPACE_ID=your_workspace_id_here

# Optional: MCP API key for authentication (leave blank to disable auth)
MCP_API_KEY=optional_api_key_for_authentication

# Optional: Server configuration
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=info
```

### 4. Test Your Connection

Before using the MCP server, test your Toggl API connection:

```bash
python scripts/test_connection.py
```

This will verify your API token and show you available data.

### 5. Run the Server

Start the MCP server:

```bash
uvicorn toggl_track_mcp.server:app --reload
```

The server will be available at:
- **MCP endpoint**: http://localhost:8000/mcp
- **Health check**: http://localhost:8000/health
- **API docs**: http://localhost:8000/docs

## Claude Desktop Integration

### Configuration

Add the server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

#### Option 1: Direct execution (recommended)

```json
{
  "mcpServers": {
    "toggl-track": {
      "command": "uvicorn",
      "args": [
        "toggl_track_mcp.server:app",
        "--host", "127.0.0.1",
        "--port", "8000"
      ],
      "env": {
        "TOGGL_API_TOKEN": "your_toggl_api_token_here"
      }
    }
  }
}
```

#### Option 2: Using uv (if you have uv installed)

```json
{
  "mcpServers": {
    "toggl-track": {
      "command": "uv",
      "args": [
        "run",
        "uvicorn",
        "toggl_track_mcp.server:app",
        "--host", "127.0.0.1", 
        "--port", "8000"
      ],
      "env": {
        "TOGGL_API_TOKEN": "your_toggl_api_token_here"
      }
    }
  }
}
```

#### Option 3: With API key authentication

If you want to add an extra layer of security:

```json
{
  "mcpServers": {
    "toggl-track": {
      "command": "uvicorn",
      "args": [
        "toggl_track_mcp.server:app",
        "--host", "127.0.0.1",
        "--port", "8000"
      ],
      "env": {
        "TOGGL_API_TOKEN": "your_toggl_api_token_here",
        "MCP_API_KEY": "your_secret_api_key_here"
      }
    }
  }
}
```

## Usage Examples

Once configured with Claude Desktop, you can use natural language to interact with your Toggl data:

### Basic Queries

- "Show me my current time entry"
- "List all my projects"
- "What time entries did I log today?"
- "Show me all my clients"

### Time Analysis

- "How much time did I spend on work last week?"
- "What's my total billable hours this month?"
- "Show me a breakdown of time by project for the last 30 days"
- "Which client did I work the most hours for this quarter?"

### Searching & Filtering

- "Find all time entries with 'meeting' in the description"
- "Show me all billable time entries from last month"
- "What time entries are tagged with 'development'?"
- "List time entries for the 'Website Redesign' project"

### Advanced Reporting

- "Generate a time summary for client 'Acme Corp' in Q4 2023"
- "Show me my productivity breakdown by project and tags"
- "What's my average daily work time this month?"

## API Integration Details

### Authentication
- Uses API token-based authentication with HTTP Basic Auth
- API token is sent as username with 'api_token' as password
- All requests include proper Content-Type headers
- Optional MCP API key for additional security layer

### Rate Limiting
- Implements 1 request per second limit as per Toggl API guidelines
- Uses token bucket algorithm with burst capacity of 3 requests
- Automatic retry with exponential backoff for rate limit errors (429)

### Error Handling
- Graceful handling of common Toggl API errors:
  - 402 Payment Required (subscription issues)
  - 410 Gone (deleted resources)
  - 429 Too Many Requests (rate limiting)
- Validates all API responses against Pydantic models
- Provides meaningful error messages for troubleshooting

### Data Processing
- Handles negative duration values for running time entries
- Calculates actual durations for active timers
- Provides both raw duration (seconds) and formatted hours
- Supports timezone-aware date filtering
- Includes additional computed fields like `is_running` and `duration_formatted`

## Development

### Development Setup

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black toggl_track_mcp/
isort toggl_track_mcp/

# Lint code
ruff check toggl_track_mcp/

# Type checking
mypy toggl_track_mcp/
```

### Project Structure

```
toggl_track_mcp/
├── __init__.py           # Package initialization
├── server.py             # FastAPI/MCP server implementation
├── toggl_client.py       # Toggl API client with rate limiting
└── rate_limiter.py       # Token bucket rate limiting

tests/
├── __init__.py
└── test_rate_limiter.py  # Rate limiter tests

scripts/
└── test_connection.py    # Connection testing script
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=toggl_track_mcp

# Run specific test
pytest tests/test_rate_limiter.py -v
```

### Deployment

#### Local Development
```bash
uvicorn toggl_track_mcp.server:app --reload --host 127.0.0.1 --port 8000
```

#### Production (example with Gunicorn)
```bash
gunicorn toggl_track_mcp.server:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### Docker (example Dockerfile)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .

COPY toggl_track_mcp/ ./toggl_track_mcp/
EXPOSE 8000

CMD ["uvicorn", "toggl_track_mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security & Privacy

- **Read-only access**: This server only reads data from Toggl Track, never writes or modifies
- **Token security**: API tokens are loaded from environment variables, never hardcoded
- **Rate limiting**: Respects Toggl's API limits to prevent abuse
- **Error isolation**: API errors are handled gracefully without exposing sensitive details
- **Optional authentication**: MCP API key can be configured for additional security
- **Pydantic validation**: All data is validated against strict schemas

## Troubleshooting

### Common Issues

1. **Authentication errors (401)**
   - Check your `TOGGL_API_TOKEN` in the `.env` file
   - Verify the token is copied correctly from your Toggl profile
   - Ensure you have API access (may require paid plan)

2. **Permission errors (403)**
   - Check your workspace permissions
   - Verify you're a member of the workspace
   - Some operations may require admin access

3. **Rate limiting (429)**
   - The server handles this automatically with retries
   - If persistent, check if other applications are using the API

4. **Payment required (402)**
   - Check your Toggl subscription status
   - API access may require a paid plan

5. **Connection issues**
   - Run `python scripts/test_connection.py` to diagnose
   - Check your internet connection
   - Verify you can access https://api.track.toggl.com

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=debug
uvicorn toggl_track_mcp.server:app --reload
```

Check the health endpoint:
```bash
curl http://localhost:8000/health
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Run linting and formatting: `black . && isort . && ruff check .`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the [Toggl Track API documentation](https://developers.track.toggl.com/)
2. Review this README for configuration help
3. Run the connection test script: `python scripts/test_connection.py`
4. Open an issue on GitHub for bugs or feature requests

## Changelog

### v0.1.0
- Initial release with Python implementation following Capsule MCP patterns
- Support for all major Toggl entities (users, time entries, projects, clients, workspaces, tags)
- Advanced filtering and search capabilities
- Time summary and reporting tools
- Rate limiting and comprehensive error handling
- FastAPI backend with health checks and optional authentication
- Full MCP protocol compliance with Pydantic validation