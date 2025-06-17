# Toggl Track MCP Server

> **Connect your Toggl Track time tracking data to AI assistants** — Access time entries, projects, clients, and analytics through natural language queries, with secure-by-default read-only access and optional write capabilities.

[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io) [![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org) [![Toggl Track API v9](https://img.shields.io/badge/Toggl%20Track-API%20v9-red)](https://developers.track.toggl.com)

**🚨 Disclaimer**: This project is created by [Fuzzy Labs](https://fuzzylabs.ai) with good vibes and is not officially supported by Toggl Track. Use at your own discretion.

## What This Does

Transform how you work with your Toggl Track time tracking data by asking AI assistants natural language questions like:

- *"How much time did I spend on client work last week?"*
- *"What's my most productive day this month?"* 
- *"Show me all time entries tagged with 'meeting'"*
- *"Which project am I spending the most time on?"*
- *"Generate a time summary for the Marketing project"*
- *"Show me team time entries for the past month"* **(Admin only)**
- *"Generate a team summary grouped by users"* **(Admin only)**
- *"List all workspace users and their IDs"* **(Admin only)**
- *"Start a timer for my current project"* **(Write mode only)**
- *"Stop my running timer and add a description"* **(Write mode only)**
- *"Create a new time entry for yesterday's meeting"* **(Write mode only)**
- *"Update the description of my last time entry"* **(Write mode only)**

**🔒 Secure by Default** — Read-only access with optional write mode for trusted environments  
**🚀 Instant Setup** — Works with any MCP-compatible AI assistant  
**📊 Complete Coverage** — Access time entries, projects, clients, analytics & more  
**👥 Team Reports** — Admin users can access team-wide time tracking data

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
        "TOGGL_API_TOKEN": "your_toggl_api_token_here",
        "TOGGL_WRITE_ENABLED": "false"
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
      "TOGGL_API_TOKEN": "your_toggl_api_token_here",
      "TOGGL_WRITE_ENABLED": "false"
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
> *"Show me team time entries for this month"* **(Admin only)**  
> *"List all workspace users"* **(Admin only)**

## Write Mode (Optional)

By default, the MCP server operates in **read-only mode** for maximum security. You can optionally enable write mode to create, update, and manage time entries directly through your AI assistant.

### 🔒 Security First Approach

- **Default:** Read-only mode - no write access to your time tracking data
- **Optional:** Write mode must be explicitly enabled via environment variable
- **Recommended:** Only enable write mode in trusted, secure environments
- **Best Practice:** Use separate configurations for read-only vs write-enabled setups

### Enabling Write Mode

To enable write operations, set the environment variable:

```bash
TOGGL_WRITE_ENABLED=true
```

**Configuration Examples:**

**Claude Desktop (Write Mode Enabled):**
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
        "TOGGL_API_TOKEN": "your_toggl_api_token_here",
        "TOGGL_WRITE_ENABLED": "true"
      }
    }
  }
}
```

**Local Development (.env file):**
```bash
TOGGL_API_TOKEN=your_toggl_api_token_here
TOGGL_WRITE_ENABLED=true
```

### Write Mode Capabilities

When write mode is enabled, you can:

- **Timer Management:** Start, stop, and control running timers
- **Time Entry Creation:** Create new time entries with custom dates and times
- **Time Entry Updates:** Modify descriptions, projects, tags, and other properties
- **Time Entry Deletion:** Remove time entries (use with caution)
- **Project Assignment:** Change which project a time entry belongs to
- **Billing Control:** Mark time entries as billable or non-billable

### Write Mode Examples

Try these queries when write mode is enabled:

- *"Start a timer for the Marketing project"*
- *"Stop my current timer and set the description to 'Client meeting'"*
- *"Create a 2-hour time entry for yesterday's design work"*
- *"Update my last time entry to be billable"*
- *"Add the tag 'urgent' to my current timer"*
- *"Delete the time entry I created 5 minutes ago"*
- *"Change my running timer to the Development project"*

### Write Mode Safety

- **Confirmation Required:** Destructive operations (like deleting time entries) will ask for confirmation
- **Detailed Responses:** All write operations provide detailed feedback about what was changed
- **Error Handling:** Clear error messages if operations fail or are not permitted
- **Validation:** Input validation ensures data integrity before making changes

⚠️ **Important Security Notes:**
- Only enable write mode in environments you fully trust
- Consider using separate API tokens for read-only vs write-enabled configurations
- Write operations cannot be undone through the MCP server - use Toggl Track's web interface to revert changes if needed
- Monitor your time tracking data when using write mode in automated workflows

## What You Can Access

This MCP server provides **comprehensive access** to your Toggl Track data:

| **Data Type** | **Read Access** | **Write Access** *(Write Mode Only)* |
|---------------|-----------------|--------------------------------------|
| **👤 User Info** | View profile, workspace, timezone settings | *(Read-only)* |
| **⏱️ Current Timer** | Check running time entry, duration, description | Start, stop, modify running timers |
| **📊 Time Entries** | List, search, filter by date, project, tags | Create, update, delete time entries |
| **📂 Projects** | View project details, status, client assignments | *(Read-only)* |
| **👥 Clients** | Access client information and relationships | *(Read-only)* |
| **🏢 Workspaces** | View available workspaces and permissions | *(Read-only)* |
| **🏷️ Tags** | Browse all tags for categorization | *(Read-only)* |
| **📈 Analytics** | Generate time summaries, breakdowns, reports | *(Read-only)* |
| **👥 Team Reports** | **(Admin only)** Access team-wide time entries, summaries, and user data | *(Read-only)* |
| **🔍 Workspace Users** | **(Admin only)** List all workspace members with IDs for filtering | *(Read-only)* |

## Team Features (Admin Required)

The MCP server includes powerful team reporting capabilities that require **workspace admin permissions**:

### Team Time Entries
- Access all team members' time entries within date ranges
- Filter by specific users, projects, clients, or billable status
- Get rich data including user names, emails, project details, and billing information
- Support for large datasets (up to 1,000 entries per request)

### Team Summaries
- Generate aggregated team summaries grouped by users, projects, or clients
- View total time, billable time, and productivity metrics
- Formatted duration displays for easy reading
- Flexible date range filtering

### Workspace User Management
- List all workspace members with their IDs and details
- Essential for filtering team reports by specific users
- View user roles and active status

### Example Team Queries
Try these with admin permissions:
- *"Show me all team time entries for last week"*
- *"Generate a team summary grouped by projects for this month"*
- *"Which team members logged the most billable hours yesterday?"*
- *"List all workspace users so I can filter reports"*

**⚠️ Important**: Team features only work if your Toggl Track account has workspace admin permissions. Regular users will receive appropriate error messages when attempting to access team data.

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

**"Admin access required" or team features not working**
- Team features require workspace admin permissions in Toggl Track
- Check your role: Profile Settings → Workspaces → your workspace → check if you're an admin
- Contact your workspace owner to grant admin access if needed

**Write operations not working**
- Check that `TOGGL_WRITE_ENABLED=true` is set in your environment variables
- Verify your API token has write permissions (some restricted tokens are read-only)
- Ensure you're not trying to write to read-only data (like projects or clients)
- Check error messages for specific permission or validation issues

**"Write mode disabled" errors**
- Write operations require `TOGGL_WRITE_ENABLED=true` in environment variables
- Restart your AI assistant after changing environment variables
- Verify the environment variable is correctly set in your MCP configuration

**Time entry operations failing**
- Ensure required fields are provided (project, description, duration)
- Check that project IDs exist and are accessible to your account
- Verify date formats are correct (YYYY-MM-DD or ISO 8601)
- Some operations may require workspace admin permissions

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
   - `TOGGL_WRITE_ENABLED`: Set to `false` for read-only mode (recommended) or `true` for write access
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
# Edit .env and set:
# TOGGL_API_TOKEN=your_token_here
# TOGGL_WRITE_ENABLED=false  # Set to true only for write mode testing
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

Test team time entries (requires admin):
```bash
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_team_time_entries",
      "arguments": {
        "start_date": "2025-06-01",
        "end_date": "2025-06-17"
      }
    },
    "id": 1
  }'
```

### Architecture

- **Server:** FastMCP framework with FastAPI backend
- **Protocol:** Model Context Protocol (MCP) via stdio
- **API:** Toggl Track API v9 with read-only access
- **Authentication:** API token (Basic Auth)