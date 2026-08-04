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
- *"List our saved custom reports"*
- *"Run the 'Client time by team' custom report for June"*
- *"What does the client time custom report measure?"*
- *"Create a new time entry for 'Meeting with client'"* **(Write mode only)**
- *"Start a timer for 'Working on feature X'"* **(Write mode only)**
- *"Create a new client called 'Acme Corp' with the note 'Q3 SOW pending'"*
- *"Create a new project ACME-200-3001 for client 101, billable, starting 2026-05-01, ending 2026-08-31, 120 estimated hours"*
- *"Add Alex (user 202) and Jordan (user 203) to project 3001"*

**🔒 Secure by Default** — Read-only access with optional write mode via environment variable
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

By default, the MCP server operates in **read-only mode** for security. To enable time entry creation, set the `TOGGL_WRITE_ENABLED` environment variable:

### Enabling Write Mode

Update your MCP configuration to include:

```json
"env": {
  "TOGGL_API_TOKEN": "your_toggl_api_token_here",
  "TOGGL_WRITE_ENABLED": "true"
}
```

### Write Operations Available

When write mode is enabled, you can:

- **Create running time entries** - Start new timers with just a description
- **Create completed time entries** - Add past work with specific durations
- **Assign to projects** - Link time entries to existing projects
- **Set billable status** - Mark entries as billable or non-billable  
- **Add tags** - Categorize entries with comma-separated tags
- **Custom start times** - Backdate entries to specific times

### Example Write Mode Queries

```
"Create a new time entry for 'Client meeting'"
"Start a timer for 'Working on feature X' and assign it to project 123"
"Add a 2-hour billable entry for 'Code review' from 2pm today"
"Create entry 'Documentation work' with tags 'writing, urgent'"
```

### Security Notes

- **Environment-gated**: Write operations are completely disabled unless explicitly enabled
- **No data modification**: Only supports creating new time entries, no editing/deleting
- **Audit trail**: All created entries include 'toggl-track-mcp' identifier for tracking
- **API rate limits**: Respects Toggl's rate limiting to prevent abuse

## What You Can Access

This MCP server provides **complete access** to your Toggl Track data:

| **Data Type** | **What You Can Do** |
|---------------|-------------------|
| **👤 User Info** | View profile, workspace, timezone settings |
| **⏱️ Current Timer** | Check running time entry, duration, description |
| **📊 Time Entries** | List, search, filter by date, project, tags |
| **✏️ Create Entries** | **(Write mode only)** Create new time entries, start/stop timers |
| **📂 Projects** | View project details, status, client assignments |
| **🆕 Create Projects** | Create new projects with client, color, billable, dates, and estimated hours |
| **👥 Clients** | Access client information and relationships |
| **➕ Create Clients** | Create new clients with optional notes |
| **👤 Project Members** | Add users to projects (one per call); set as manager |
| **🏢 Workspaces** | View available workspaces and permissions |
| **🏷️ Tags** | Browse all tags for categorization |
| **📈 Analytics** | Generate time summaries, breakdowns, reports |
| **📋 Custom Reports** | List saved "My Reports" dashboards, read their definitions, and run them for any date range |
| **👥 Team Reports** | **(Admin only)** Access team-wide time entries, summaries, and user data |
| **🔍 Workspace Users** | **(Admin only)** List all workspace members with IDs for filtering |

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

## Custom Reports

Custom reports are the multi-chart dashboards built in Toggl's **My Reports** section — the ones at
`track.toggl.com/reports/{organization_id}/custom/{report_id}`. Three tools cover them:

| **Tool** | **What it does** |
|---|---|
| `list_custom_reports` | Lists the organization's saved reports with their IDs, chart types and saved date period |
| `get_custom_report` | Shows a report's definition: each chart's groupings, aggregations and filters |
| `run_custom_report` | Runs one chart and returns its rows, with IDs resolved to names and durations in seconds |

`run_custom_report` uses the report's own saved date period (`Last month`, `This quarter` and so on)
unless you pass `start_date` and `end_date`. A report with several charts runs one at a time — pass
the `chart_id` from `get_custom_report` to pick a specific one, or omit it for the first chart.

### Example Custom Report Queries
- *"List our custom reports"*
- *"Run custom report 12345 for July 2026"*
- *"Which clients did the engineering team log time against last month?"*

**⚠️ Unofficial API**: Toggl serves custom reports from an `analytics` API that is not part of its
published API documentation. It authenticates with the same API token, and the endpoints were
verified against the live API, but Toggl can change them without notice. Everything here is
read-only — these tools never modify a report.

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

**Custom reports return "No organization found for workspace"**
- Custom reports are scoped to an organization, resolved from your default workspace
- Set `TOGGL_WORKSPACE_ID` to the workspace whose organization owns the reports

**A custom report returns no rows, or fewer than the Toggl UI shows**
- Check the period in the response: a report saved with a relative period (`Last month`) resolves
  against today's date, so it moves as the month does. Pass `start_date` and `end_date` to pin it
- Reports you can only view (rather than edit) still run, but a chart belonging to someone else's
  report cannot be fetched on its own

**"Report uses a custom date range but has no dates saved"**
- The report was saved with a custom period Toggl did not store dates for
- Pass `start_date` and `end_date` to `run_custom_report`

**MCP tools not showing in your AI assistant**
- Restart your AI assistant after config changes
- Check the config file syntax is valid JSON
- Verify file paths are absolute, not relative

**Write operations not working**
- Check that `TOGGL_WRITE_ENABLED=true` is set in your environment variables
- Restart your AI assistant after adding the environment variable
- Verify you have permissions to create time entries in your Toggl workspace

**"Write operations are disabled" error**
- The `create_time_entry` tool requires `TOGGL_WRITE_ENABLED=true`
- This is a security feature to prevent accidental time entry creation
- Update your MCP configuration to include the environment variable

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
   - `TOGGL_WRITE_ENABLED`: Set to `"true"` to enable time entry creation (optional, defaults to `"false"`)

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
# TOGGL_WRITE_ENABLED=true  # Optional: enable write operations
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
- **API:** Toggl Track API v9 with configurable read/write access
- **Authentication:** API token (Basic Auth)
- **Security:** Environment-gated write operations