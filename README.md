# Toggl Track MCP Server

Connect your Toggl Track time tracking data to AI assistants via the Model Context Protocol (MCP).

[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-blue.svg)](https://modelcontextprotocol.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-red.svg)](https://fastapi.tiangolo.com)
[![Test](https://github.com/fuzzylabs/toggl-track-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/fuzzylabs/toggl-track-mcp/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **⚠️ Read-Only Access**: This server only reads your Toggl Track data. It cannot create, modify, or delete any time entries, projects, or other data.

## What This Does

This server exposes your Toggl Track time tracking data through the [Model Context Protocol](https://modelcontextprotocol.org), allowing AI assistants like Claude to help you analyze your time tracking patterns, generate reports, and answer questions about your work habits.

**Example queries you can ask:**
- *"How much time did I spend on client work last week?"*
- *"Show me my most productive day this month"*
- *"What projects am I spending the most time on?"*
- *"Generate a time summary for the Marketing project"*
- *"Find all time entries tagged with 'meeting'"*

## Quick Start

### 1. Get Your Toggl Track API Token

1. Visit your [Toggl Track Profile Settings](https://track.toggl.com/profile)
2. Scroll down to find your **API Token**
3. Copy the token (you'll need it for configuration)

### 2. Installation

```bash
git clone https://github.com/fuzzylabs/toggl-track-mcp.git
cd toggl-track-mcp
uv sync
```

### 3. Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Add your API token to `.env`:

```env
TOGGL_API_TOKEN=your_api_token_here
```

### 4. Test Your Setup

Verify everything works:

```bash
uv run python scripts/test_connection.py
```

### 5. Connect to Claude Desktop

Add this to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

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
        "TOGGL_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

That's it! 🎉 Restart Claude Desktop and start asking questions about your time tracking data.

## What You Can Access

| **Data Type** | **Description** | **Example Use Cases** |
|---------------|-----------------|----------------------|
| **Current User** | Your profile and account information | Check timezone, workspace details |
| **Time Entries** | All your time tracking records | Analyze work patterns, find specific entries |
| **Running Timer** | Currently active time tracking | Check what you're working on now |
| **Projects** | All your projects with details | Project time analysis, budget tracking |
| **Clients** | Client information and relationships | Client-specific time reports |
| **Workspaces** | Your available workspaces | Multi-workspace time analysis |
| **Tags** | All tags used in time entries | Tag-based filtering and categorization |
| **Time Summaries** | Aggregated time data with breakdowns | Detailed reporting and analytics |

## Advanced Features

### 🔍 Smart Search & Filtering
- Search time entries by description or tags
- Filter by date ranges, projects, clients, or billable status
- Find patterns in your work habits

### 📊 Time Analytics
- Automatic duration calculations for running timers
- Billable vs non-billable time breakdowns
- Project and client time summaries
- Tag-based time categorization

### 🛡️ Rate Limiting & Error Handling
- Respects Toggl's API limits (1 request/second)
- Graceful handling of API errors and edge cases
- Automatic retries for rate limit scenarios

### 🔧 Developer-Friendly
- FastAPI backend with automatic API documentation
- Health checks and monitoring endpoints
- Comprehensive test coverage
- Full type safety with Pydantic models

## Deployment Options

### Local Development
```bash
uv run uvicorn toggl_track_mcp.server:app --reload
```
Server available at: http://localhost:8000

### Using uv (Recommended)
If you have [uv](https://docs.astral.sh/uv/) installed:

```json
{
  "mcpServers": {
    "toggl-track": {
      "command": "uv",
      "args": ["run", "uvicorn", "toggl_track_mcp.server:app"],
      "env": {
        "TOGGL_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

### Production Deployment
```bash
# With Gunicorn
gunicorn toggl_track_mcp.server:app -w 4 -k uvicorn.workers.UvicornWorker

# With Docker
docker build -t toggl-track-mcp .
docker run -p 8000:8000 -e TOGGL_API_TOKEN=your_token toggl-track-mcp
```

### Cloud Deployment

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/fuzzylabs/toggl-track-mcp)

Click the button above for one-click deployment to Render, or deploy to your preferred cloud platform.

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format and lint
uv run black toggl_track_mcp/
uv run isort toggl_track_mcp/
uv run ruff check toggl_track_mcp/

# Type checking
uv run mypy toggl_track_mcp/
```

### Project Structure

```
toggl_track_mcp/
├── __init__.py           # Package exports
├── server.py            # FastAPI/MCP server
├── toggl_client.py      # Toggl API client
└── rate_limiter.py      # Rate limiting utilities

tests/                   # Test suite
scripts/                 # Utility scripts
.github/workflows/       # CI/CD automation
```

### Running the Test Suite

```bash
# Run all tests with coverage
uv run pytest --cov=toggl_track_mcp

# Run specific tests
uv run pytest tests/test_rate_limiter.py -v

# Test with multiple Python versions (use GitHub Actions)
# or install and use tox: uv tool install tox && uv tool run tox
```

## Troubleshooting

### 🔑 Authentication Issues
**Problem**: Getting 401 Unauthorized errors

**Solutions**:
- Double-check your `TOGGL_API_TOKEN` in the `.env` file
- Verify the token is copied correctly from your Toggl profile
- Ensure your Toggl account has API access (may require paid plan)

### 🌐 Connection Problems
**Problem**: Cannot connect to Toggl API

**Solutions**:
- Run the connection test: `uv run python scripts/test_connection.py`
- Check your internet connection
- Verify you can access https://api.track.toggl.com in your browser

### 🚦 Rate Limiting
**Problem**: Getting rate limit errors

**Solutions**:
- The server handles this automatically with retries
- If persistent, check if other applications are using your API token
- Consider upgrading your Toggl plan for higher rate limits

### 💳 Payment Required (402)
**Problem**: API returns payment required error

**Solutions**:
- Check your Toggl subscription status
- Some API features require a paid Toggl plan
- Verify your account is in good standing

### 🐛 Other Issues
- Enable debug logging: `export LOG_LEVEL=debug`
- Check the health endpoint: `curl http://localhost:8000/health`
- Review the [Toggl Track API documentation](https://developers.track.toggl.com/)

## Getting Help

- 📖 [Toggl Track API Documentation](https://developers.track.toggl.com/)
- 🐛 [Report Issues](https://github.com/fuzzylabs/toggl-track-mcp/issues)
- 💬 [Discussions](https://github.com/fuzzylabs/toggl-track-mcp/discussions)
- 📧 [Email Support](mailto:tom@fuzzylabs.ai)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Submit a pull request

## Security & Privacy

- **🔒 Read-Only**: This server only reads data from Toggl Track
- **🛡️ Token Security**: API tokens are never logged or exposed
- **🚦 Rate Limiting**: Respects Toggl's API usage policies  
- **🔍 Data Validation**: All responses validated with Pydantic schemas
- **🏠 Local Processing**: Your data stays on your machine

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/modelcontextprotocol/fastmcp) for robust MCP integration
- Inspired by the [Capsule CRM MCP Server](https://github.com/fuzzylabs/capsule-mcp)
- Thanks to the [Toggl Track](https://toggl.com) team for their excellent API

---

<div align="center">
  <strong>Made with ❤️ by <a href="https://fuzzylabs.ai">Fuzzy Labs</a></strong>
</div>