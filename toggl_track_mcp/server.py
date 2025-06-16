"""Toggl Track MCP Server implementation."""

import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastmcp import FastMCP

from .toggl_client import TogglAPIClient, TogglAPIError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# Configuration
TOGGL_API_TOKEN = os.getenv("TOGGL_API_TOKEN")
TOGGL_BASE_URL = os.getenv("TOGGL_BASE_URL", "https://api.track.toggl.com/api/v9")
TOGGL_WORKSPACE_ID = os.getenv("TOGGL_WORKSPACE_ID")
MCP_API_KEY = os.getenv("MCP_API_KEY")

# Initialize Toggl client (only if token is available)
toggl_client = None
if TOGGL_API_TOKEN:
    workspace_id = int(TOGGL_WORKSPACE_ID) if TOGGL_WORKSPACE_ID else None
    toggl_client = TogglAPIClient(
        api_token=TOGGL_API_TOKEN, base_url=TOGGL_BASE_URL, workspace_id=workspace_id
    )

# Initialize FastMCP
mcp: FastMCP[None] = FastMCP("Toggl Track MCP")


def _get_toggl_client() -> TogglAPIClient:
    """Get the Toggl client, raising an error if not configured."""
    if toggl_client is None:
        raise TogglAPIError("TOGGL_API_TOKEN environment variable is required")
    return toggl_client


async def authenticate_request(request: Request) -> None:
    """Authenticate MCP requests if API key is configured."""
    # Skip auth for tests
    if os.getenv("PYTEST_CURRENT_TEST"):
        return

    # Skip auth if no API key configured
    if not MCP_API_KEY:
        return

    # Only authenticate MCP endpoints
    if not request.url.path.startswith("/mcp"):
        return

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    provided_key = auth_header[7:]  # Remove "Bearer " prefix
    if provided_key != MCP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# MCP Tools


@mcp.tool()
async def get_current_user() -> Dict[str, Any]:
    """Get current user profile and session information."""
    try:
        client = _get_toggl_client()
        user = await client.get_current_user()
        return {
            "user": user.model_dump(),
            "message": f"Current user: {user.fullname} ({user.email})",
        }
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def get_current_time_entry() -> Dict[str, Any]:
    """Get currently running time entry (if any)."""
    try:
        client = _get_toggl_client()
        entry = await client.get_current_time_entry()
        if not entry:
            return {"message": "No time entry is currently running"}

        duration = client.calculate_duration(entry)
        duration_formatted = client.format_duration(duration)

        result = entry.model_dump()
        result.update(
            {
                "calculated_duration": duration,
                "duration_formatted": duration_formatted,
                "is_running": entry.duration < 0,
            }
        )

        return {
            "time_entry": result,
            "message": f"Timer running: '{entry.description}' ({duration_formatted})",
        }
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def list_time_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    project_id: Optional[int] = None,
    billable: Optional[bool] = None,
    description_contains: Optional[str] = None,
) -> Dict[str, Any]:
    """Get time entries with optional filtering.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        project_id: Filter by project ID
        billable: Filter by billable status
        description_contains: Filter by description containing text
    """
    try:
        client = _get_toggl_client()
        entries = await client.get_time_entries(start_date, end_date)

        # Apply additional filters
        filtered_entries = []
        for entry in entries:
            if project_id is not None and entry.project_id != project_id:
                continue
            if billable is not None and entry.billable != billable:
                continue
            if (
                description_contains
                and description_contains.lower() not in entry.description.lower()
            ):
                continue

            # Calculate actual duration
            duration = client.calculate_duration(entry)
            entry_data = entry.model_dump()
            entry_data.update(
                {
                    "calculated_duration": duration,
                    "duration_formatted": client.format_duration(duration),
                    "is_running": entry.duration < 0,
                }
            )
            filtered_entries.append(entry_data)

        total_duration = sum(e["calculated_duration"] for e in filtered_entries)
        total_formatted = client.format_duration(total_duration)

        return {
            "time_entries": filtered_entries,
            "total_count": len(filtered_entries),
            "total_duration": total_duration,
            "total_duration_formatted": total_formatted,
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "project_id": project_id,
                "billable": billable,
                "description_contains": description_contains,
            },
        }
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def get_time_entry_details(entry_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific time entry.

    Args:
        entry_id: Time entry ID
    """
    try:
        client = _get_toggl_client()
        entry = await client.get_time_entry(entry_id)
        duration = client.calculate_duration(entry)

        result = entry.model_dump()
        result.update(
            {
                "calculated_duration": duration,
                "duration_formatted": client.format_duration(duration),
                "is_running": entry.duration < 0,
            }
        )

        return {"time_entry": result}
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def list_projects() -> Dict[str, Any]:
    """Get all projects for current workspace."""
    try:
        client = _get_toggl_client()
        projects = await client.get_projects()

        active_projects = [p for p in projects if p.active]
        inactive_projects = [p for p in projects if not p.active]

        return {
            "projects": [p.model_dump() for p in projects],
            "total_count": len(projects),
            "active_count": len(active_projects),
            "inactive_count": len(inactive_projects),
            "summary": f"Found {len(projects)} projects ({len(active_projects)} active, {len(inactive_projects)} inactive)",
        }
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def list_clients() -> Dict[str, Any]:
    """Get all clients."""
    try:
        client = _get_toggl_client()
        clients = await client.get_clients()

        return {
            "clients": [c.model_dump() for c in clients],
            "total_count": len(clients),
            "summary": f"Found {len(clients)} clients",
        }
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def list_workspaces() -> Dict[str, Any]:
    """Get available workspaces."""
    try:
        client = _get_toggl_client()
        workspaces = await client.get_workspaces()

        return {
            "workspaces": [w.model_dump() for w in workspaces],
            "total_count": len(workspaces),
            "summary": f"Found {len(workspaces)} workspaces",
        }
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def list_tags() -> Dict[str, Any]:
    """Get all available tags."""
    try:
        client = _get_toggl_client()
        tags = await client.get_tags()

        return {
            "tags": [t.model_dump() for t in tags],
            "total_count": len(tags),
            "summary": f"Found {len(tags)} tags",
        }
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def search_time_entries(
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    project_id: Optional[int] = None,
    billable: Optional[bool] = None,
) -> Dict[str, Any]:
    """Search time entries by description or tags.

    Args:
        query: Search query for description or tags
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        project_id: Filter by project ID
        billable: Filter by billable status
    """
    try:
        client = _get_toggl_client()
        entries = await client.get_time_entries(start_date, end_date)

        # Search and filter
        matching_entries = []
        query_lower = query.lower()

        for entry in entries:
            # Check if query matches description
            description_match = query_lower in entry.description.lower()

            # Check if query matches tags
            tag_match = False
            if entry.tags:
                tag_match = any(query_lower in tag.lower() for tag in entry.tags)

            if not (description_match or tag_match):
                continue

            # Apply additional filters
            if project_id is not None and entry.project_id != project_id:
                continue
            if billable is not None and entry.billable != billable:
                continue

            # Calculate duration
            duration = client.calculate_duration(entry)
            entry_data = entry.model_dump()
            entry_data.update(
                {
                    "calculated_duration": duration,
                    "duration_formatted": client.format_duration(duration),
                    "is_running": entry.duration < 0,
                    "match_reason": "description" if description_match else "tags",
                }
            )
            matching_entries.append(entry_data)

        total_duration = sum(e["calculated_duration"] for e in matching_entries)
        total_formatted = client.format_duration(total_duration)

        return {
            "query": query,
            "time_entries": matching_entries,
            "total_count": len(matching_entries),
            "total_duration": total_duration,
            "total_duration_formatted": total_formatted,
            "summary": f"Found {len(matching_entries)} entries matching '{query}' ({total_formatted})",
        }
    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def get_time_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    project_id: Optional[int] = None,
    client_id: Optional[int] = None,
    billable: Optional[bool] = None,
) -> Dict[str, Any]:
    """Calculate total time with breakdowns by project, client, and tags.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        project_id: Filter by project ID
        client_id: Filter by client ID (via project)
        billable: Filter by billable status
    """
    try:
        # Get data
        client = _get_toggl_client()
        entries = await client.get_time_entries(start_date, end_date)
        projects = await client.get_projects()
        clients = await client.get_clients()

        # Create lookup maps
        project_map = {p.id: p for p in projects}
        client_map = {c.id: c for c in clients}

        # Filter entries
        filtered_entries = []
        for entry in entries:
            # Apply client filter (via project)
            if client_id is not None:
                if entry.project_id is not None:
                    project = project_map.get(entry.project_id)
                else:
                    project = None
                if not project or project.client_id != client_id:
                    continue

            if project_id is not None and entry.project_id != project_id:
                continue
            if billable is not None and entry.billable != billable:
                continue

            filtered_entries.append(entry)

        # Calculate totals and breakdowns
        total_duration = 0
        billable_duration = 0
        project_breakdown = {}
        client_breakdown = {}
        tag_breakdown = {}

        for entry in filtered_entries:
            duration = client.calculate_duration(entry)
            total_duration += duration

            if entry.billable:
                billable_duration += duration

            # Project breakdown
            project_name = "No Project"
            if entry.project_id and entry.project_id in project_map:
                project_name = project_map[entry.project_id].name

            if project_name not in project_breakdown:
                project_breakdown[project_name] = {"duration": 0, "count": 0}
            project_breakdown[project_name]["duration"] += duration
            project_breakdown[project_name]["count"] += 1

            # Client breakdown
            client_name = "No Client"
            if entry.project_id and entry.project_id in project_map:
                project = project_map[entry.project_id]
                if project.client_id and project.client_id in client_map:
                    client_name = client_map[project.client_id].name

            if client_name not in client_breakdown:
                client_breakdown[client_name] = {"duration": 0, "count": 0}
            client_breakdown[client_name]["duration"] += duration
            client_breakdown[client_name]["count"] += 1

            # Tag breakdown
            if entry.tags:
                for tag in entry.tags:
                    if tag not in tag_breakdown:
                        tag_breakdown[tag] = {"duration": 0, "count": 0}
                    tag_breakdown[tag]["duration"] += duration
                    tag_breakdown[tag]["count"] += 1

        # Format breakdowns
        def format_breakdown(
            breakdown_dict: Dict[str, Dict[str, Any]],
        ) -> List[Dict[str, Any]]:
            return [
                {
                    "name": name,
                    "duration": data["duration"],
                    "duration_formatted": client.format_duration(data["duration"]),
                    "entries_count": data["count"],
                }
                for name, data in sorted(
                    breakdown_dict.items(), key=lambda x: x[1]["duration"], reverse=True
                )
            ]

        return {
            "summary": {
                "total_duration": total_duration,
                "total_duration_formatted": client.format_duration(total_duration),
                "billable_duration": billable_duration,
                "billable_duration_formatted": client.format_duration(
                    billable_duration
                ),
                "non_billable_duration": total_duration - billable_duration,
                "non_billable_duration_formatted": client.format_duration(
                    total_duration - billable_duration
                ),
                "total_entries": len(filtered_entries),
            },
            "project_breakdown": format_breakdown(project_breakdown),
            "client_breakdown": format_breakdown(client_breakdown),
            "tag_breakdown": format_breakdown(tag_breakdown),
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "project_id": project_id,
                "client_id": client_id,
                "billable": billable,
            },
            "period_summary": f"Total time: {client.format_duration(total_duration)} ({len(filtered_entries)} entries)",
        }
    except TogglAPIError as e:
        return {"error": str(e)}


# FastAPI application setup
def create_app() -> FastAPI:
    """Create FastAPI application with MCP integration."""
    app = FastAPI(
        title="Toggl Track MCP Server",
        description="Toggl Track time tracking data exposed as AI tools",
        version="0.1.0",
    )

    # Add authentication middleware
    app.middleware("http")(authenticate_request)

    # Mount MCP - use type ignore for mypy compatibility
    mcp_app = mcp.http_app()
    app.mount("/mcp", mcp_app)

    @app.get("/")
    async def root() -> RedirectResponse:
        """Redirect to MCP endpoint."""
        return RedirectResponse(url="/mcp")

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        """Health check endpoint."""
        try:
            client = _get_toggl_client()
            user = await client.get_current_user()
            return {
                "status": "healthy",
                "user": user.fullname,
                "workspace_id": user.default_workspace_id,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    return app


# Create app instance
app = create_app()
