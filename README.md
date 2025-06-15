# Toggl Track MCP Server

A Model Context Protocol (MCP) server that provides read-only access to Toggl Track time tracking data. This server exposes Toggl Track's time entries, projects, clients, and other data through standardized MCP tools that can be used with AI assistants like Claude.

## Features

- **Read-only access** to Toggl Track data for safe AI interaction
- **Rate limiting** with proper backoff (1 request/second, burst of 3)
- **Comprehensive time tracking tools** for data analysis and reporting
- **Timezone-aware** duration calculations for running time entries
- **Rich filtering and search** capabilities across time entries
- **Data aggregation** for time summaries and reporting
- **Error handling** for API rate limits and common Toggl API issues

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

- Node.js 18.0.0 or later
- A Toggl Track account with API access
- Your Toggl Track API token

### 1. Get Your Toggl API Token

1. Log in to your Toggl Track account
2. Go to [Profile Settings](https://track.toggl.com/profile)
3. Scroll down to find your API Token
4. Copy the token (you'll need it for configuration)

### 2. Install Dependencies

```bash
npm install
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

# Optional: Server configuration
MCP_SERVER_NAME=toggl-track-mcp
MCP_SERVER_VERSION=0.1.0
LOG_LEVEL=info
```

### 4. Build the Server

```bash
npm run build
```

### 5. Configure with Claude Desktop

Add the server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "toggl-track": {
      "command": "node",
      "args": ["/path/to/toggl-track-mcp/dist/index.js"],
      "env": {
        "TOGGL_API_TOKEN": "your_toggl_api_token_here"
      }
    }
  }
}
```

Replace `/path/to/toggl-track-mcp` with the actual path to this project.

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

### Rate Limiting
- Implements 1 request per second limit as per Toggl API guidelines
- Uses token bucket algorithm with burst capacity of 3 requests
- Automatic retry with exponential backoff for rate limit errors (429)

### Error Handling
- Graceful handling of common Toggl API errors:
  - 402 Payment Required (subscription issues)
  - 410 Gone (deleted resources)
  - 429 Too Many Requests (rate limiting)
- Validates all API responses against TypeScript schemas
- Provides meaningful error messages for troubleshooting

### Data Processing
- Handles negative duration values for running time entries
- Calculates actual durations for active timers
- Provides both raw duration (seconds) and formatted hours
- Supports timezone-aware date filtering
- Includes additional computed fields like `is_running` and `calculated_hours`

## Development

### Scripts

```bash
# Development with hot reload
npm run dev

# Build TypeScript
npm run build

# Run built server
npm start

# Lint code
npm run lint

# Run tests
npm test

# Type checking
npm run typecheck
```

### Project Structure

```
src/
├── types/          # TypeScript type definitions
│   ├── toggl.ts    # Toggl API types and schemas
│   └── mcp.ts      # MCP protocol types
├── utils/          # Utility modules
│   └── rate-limiter.ts  # Rate limiting implementation
├── tools/          # MCP tool implementations
│   └── index.ts    # Tool definitions and handlers
├── config.ts       # Configuration management
├── toggl-client.ts # Toggl API client
├── server.ts       # MCP server implementation
└── index.ts        # Main entry point
```

## Security & Privacy

- **Read-only access**: This server only reads data from Toggl Track, never writes or modifies
- **Token security**: API tokens are loaded from environment variables, never hardcoded
- **Rate limiting**: Respects Toggl's API limits to prevent abuse
- **Error isolation**: API errors are handled gracefully without exposing sensitive details

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run linting and type checking: `npm run lint && npm run typecheck`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the [Toggl Track API documentation](https://developers.track.toggl.com/)
2. Review this README for configuration help
3. Open an issue on GitHub for bugs or feature requests

## Changelog

### v0.1.0
- Initial release with read-only Toggl Track integration
- Support for all major Toggl entities (users, time entries, projects, clients, workspaces, tags)
- Advanced filtering and search capabilities
- Time summary and reporting tools
- Rate limiting and error handling
- Full MCP protocol compliance