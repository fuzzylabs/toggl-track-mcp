# Toggl Track MCP Server

> **Connect your Toggl Track time tracking data to AI assistants** — Access time entries, projects, clients, and analytics through natural language queries, with complete read-only security.

[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io) [![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org) [![Toggl Track API v9](https://img.shields.io/badge/Toggl%20Track-API%20v9-red)](https://developers.track.toggl.com)

**🚨 Disclaimer**: This project is created by [Fuzzy Labs](https://fuzzylabs.ai) with good vibes and is not officially supported by Toggl Track. Use at your own discretion.

## What This Does

Transform how you work with your Toggl Track time tracking data by asking AI assistants natural language questions like:

- *"How much time did I spend on client work last week?"*
- *"What's my most productive day this month?"* 
- *"Show me all time entries tagged with 'meeting'"*
- *"Which project am I spending the most time on?"*
- *"Generate a time summary for the Marketing project"*

**🔒 Read-Only & Secure** — No write access to your time tracking data  
**🚀 Instant Setup** — Works with any MCP-compatible AI assistant  
**📊 Complete Coverage** — Access time entries, projects, clients, analytics & more

## Quick Start

### 1. Get Your Toggl Track API Token
1. Log into your Toggl Track account
2. Go to **Profile Settings → API Token**
3. Copy your API token (keep it safe!)

### 2. Install & Configure

#### macOS Setup

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/fuzzylabs/toggl-track-mcp.git
cd toggl-track-mcp
uv sync
```

#### Linux/Windows Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# OR for Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone and install
git clone https://github.com/fuzzylabs/toggl-track-mcp.git
cd toggl-track-mcp
uv sync
```

### 3. Connect to Your AI Assistant

#### Claude Desktop

Add this to your Claude Desktop config file:

**Config Location:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "toggl-track": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/toggl-track-mcp",
        "python",
        "-m",
        "toggl_track_mcp"
      ],
      "env": {
        "TOGGL_API_TOKEN": "your_toggl_api_token_here"
      }
    }
  }
}
```

#### Cursor

**📋 Quick Setup:** 

**Copy this Cursor deeplink and paste it in your browser address bar:**

```
cursor://anysphere.cursor-deeplink/mcp/install?name=toggl-track&config=eyJ0b2dnbC10cmFjayI6eyJjb21tYW5kIjoidXYiLCJhcmdzIjpbInJ1biIsIi0tZGlyZWN0b3J5IiwiL3BhdGgvdG8veW91ci90b2dnbC10cmFjay1tY3AiLCJweXRob24iLCItbSIsInRvZ2dsX3RyYWNrX21jcCJdLCJlbnYiOnsiVE9HR0xfQVBJX1RPS0VOIjoieW91cl90b2dnbF9hcGlfdG9rZW5faGVyZSJ9fX0K
```

**💡 How to use:**
1. Copy the entire `cursor://` URL above
2. Paste it into your browser's address bar 
3. Press Enter - this will open Cursor and prompt to install the MCP server

**Note:** After clicking the button, you'll need to:
1. Update the path `/path/to/your/toggl-track-mcp` to your actual installation directory
2. Replace `your_toggl_api_token_here` with your actual Toggl Track API token

Or manually add this to your Cursor MCP settings:

```json
{
  "toggl-track": {
    "command": "uv",
    "args": [
      "run",
      "--directory",
      "/path/to/your/toggl-track-mcp",
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

#### Other MCP Clients

This server is compatible with any MCP client. Refer to your client's documentation for MCP server configuration.

**💡 Setup Help:**
- **Using uv (recommended):** Use `uv run` command as shown above - no Python path needed!
- **uv path for Claude Desktop:** Use full path `~/.local/bin/uv` (find yours with `which uv`)
- **Manual Python paths (if not using uv):**
  - **macOS (Homebrew):** `/opt/homebrew/bin/python3` (Apple Silicon) or `/usr/local/bin/python3` (Intel)
  - **macOS (System):** `/usr/bin/python3` (if available)
  - **Find your Python:** Run `which python3` in terminal
  - **Windows:** Try `C:\Python311\python.exe`

### 4. Start Using

1. **Restart your AI assistant**
2. **Start asking questions!**

Try these example queries:
> *"Show me my current time entry"*  
> *"How much time did I log yesterday?"*  
> *"What projects am I working on?"*  
> *"Generate a weekly time report"*

## What You Can Access

This MCP server provides **complete read-only access** to your Toggl Track data:

| **Data Type** | **What You Can Do** |
|---------------|-------------------|
| **👤 User Info** | View profile, workspace, timezone settings |
| **⏱️ Current Timer** | Check running time entry, duration, description |
| **📊 Time Entries** | List, search, filter by date, project, tags |
| **📂 Projects** | View project details, status, client assignments |
| **👥 Clients** | Access client information and relationships |
| **🏢 Workspaces** | View available workspaces and permissions |
| **🏷️ Tags** | Browse all tags for categorization |
| **📈 Analytics** | Generate time summaries, breakdowns, reports |

## Troubleshooting

### Common Issues

**"No module named 'toggl_track_mcp'"**
- **Using uv:** Make sure you're using the absolute directory path with `uv run --directory`
- **Manual setup:** Verify Python can find the installed packages: `pip list | grep fastmcp`

**"spawn uv ENOENT" or "command not found: uv"**
- Install uv first: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Restart your terminal after installation
- Verify installation: `uv --version`

**"spawn python ENOENT" (if not using uv)**
- Switch to uv setup (recommended) or use full Python path in config
- Check your Python path: `which python3`
- Try different common paths: `/usr/bin/python3`, `/usr/local/bin/python3`, `/opt/homebrew/bin/python3`

**"Authentication failed"**
- Verify your Toggl Track API token is correct
- Check that your Toggl account has API access (may require paid plan)

**MCP tools not showing in your AI assistant**
- Restart your AI assistant after config changes
- Check the config file syntax is valid JSON
- Verify file paths are absolute, not relative

### Getting Help

- **Issues & Bugs:** [GitHub Issues](https://github.com/fuzzylabs/toggl-track-mcp/issues)
- **Toggl API Docs:** [developers.track.toggl.com](https://developers.track.toggl.com)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## Render Deployment (Secure Remote HTTP Access)

Want to deploy the MCP server remotely so multiple users can access it via HTTP? Deploy to Render for easy cloud hosting with API key authentication.

### Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/fuzzylabs/toggl-track-mcp)

### Manual Deployment

1. **Fork this repository** to your GitHub account

2. **Create a Render account** at [render.com](https://render.com)

3. **Create a new Web Service** and connect your GitHub fork

4. **Configure the service:**
   - **Build Command:** `uv sync`
   - **Start Command:** `uv run uvicorn toggl_track_mcp.server:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (or choose a paid plan for better performance)

5. **Set environment variables** in Render dashboard:
   - `TOGGL_API_TOKEN`: Your Toggl Track API token
   - `MCP_API_KEY`: A secure random API key for authentication (see generation instructions below)

6. **Deploy** - Render will automatically build and deploy your service

### Generating a Secure API Key

Generate a secure random API key for the `MCP_API_KEY` environment variable:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL  
openssl rand -base64 32

# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

⚠️ **Important**: Store this API key securely - you'll need it to configure your MCP clients.

### Using Your Deployed Server

Once deployed, you'll get a URL like `https://your-service.onrender.com`. Configure your MCP clients to use:

**Claude Desktop:**
```json
{
  "mcpServers": {
    "toggl-track": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://your-service.onrender.com/mcp/",
        "-H", "Content-Type: application/json",
        "-H", "Authorization: Bearer YOUR_MCP_API_KEY_HERE",
        "-d", "@-"
      ]
    }
  }
}
```

Replace `YOUR_MCP_API_KEY_HERE` with the API key you generated and set in Render.

🔒 **Security Note**: The API key authentication is only enforced when the `MCP_API_KEY` environment variable is set. If no API key is configured, the server will accept unauthenticated requests (useful for local development).

**Direct HTTP Access:**
```bash
# List available tools
curl -X POST https://your-service.onrender.com/mcp/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_MCP_API_KEY_HERE" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'

# Get current time entry
curl -X POST https://your-service.onrender.com/mcp/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_MCP_API_KEY_HERE" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_current_time_entry",
      "arguments": {}
    },
    "id": 1
  }'
```

**⚠️ Note on Free Tier:** Render's free tier spins down services after inactivity. First requests may take 30-60 seconds to wake up the service.

---

## For Developers

### Development Setup

**Environment Variables (for development):**
```bash
cp .env.example .env
# Edit .env and set TOGGL_API_TOKEN=your_token_here
```

**Run Tests:**
```bash
uv run pytest
```

**HTTP Server (for testing):**
```bash
uv run uvicorn toggl_track_mcp.server:app --reload
# Server available at http://localhost:8000/mcp/
```

### API Testing

Test the schema endpoint:
```bash
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

Test getting current time entry:
```bash
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_current_time_entry",
      "arguments": {}
    },
    "id": 1
  }'
```

### Architecture

- **Server:** FastMCP framework with FastAPI backend
- **Protocol:** Model Context Protocol (MCP) via stdio
- **API:** Toggl Track API v9 with read-only access
- **Authentication:** API token (Basic Auth)