"""Toggl Track MCP Server implementation."""

import logging
import os
from typing import Any, Awaitable, Callable, Dict, List, Optional

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
TOGGL_WRITE_ENABLED = os.getenv("TOGGL_WRITE_ENABLED", "false").lower() == "true"

# Initialize Toggl client (optional for testing)
toggl_client: Optional[TogglAPIClient] = None
if TOGGL_API_TOKEN:
    workspace_id = int(TOGGL_WORKSPACE_ID) if TOGGL_WORKSPACE_ID else None
    toggl_client = TogglAPIClient(
        api_token=TOGGL_API_TOKEN, base_url=TOGGL_BASE_URL, workspace_id=workspace_id
    )


def _get_toggl_client() -> TogglAPIClient:
    """Get the Toggl client, raising an error if not configured."""
    if toggl_client is None:
        raise TogglAPIError("TOGGL_API_TOKEN environment variable is required")
    return toggl_client


# Initialize FastMCP
mcp: FastMCP[None] = FastMCP("Toggl Track MCP")


async def authenticate_request(
    request: Request, call_next: Callable[[Request], Awaitable[Any]]
) -> Any:
    """Authenticate MCP requests if API key is configured."""
    # Skip auth for tests
    if os.getenv("PYTEST_CURRENT_TEST"):
        return await call_next(request)

    # Skip auth if no API key configured
    if not MCP_API_KEY:
        return await call_next(request)

    # Only authenticate MCP endpoints
    if not request.url.path.startswith("/mcp"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    provided_key = auth_header[7:]  # Remove "Bearer " prefix
    if provided_key != MCP_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return await call_next(request)


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
                "is_running": (entry.duration or 0) < 0,
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
                    "is_running": (entry.duration or 0) < 0,
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
                "is_running": (entry.duration or 0) < 0,
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
                    "is_running": (entry.duration or 0) < 0,
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
                project_name = project_map[entry.project_id].name or "No Project"

            if project_name not in project_breakdown:
                project_breakdown[project_name] = {"duration": 0, "count": 0}
            project_breakdown[project_name]["duration"] += duration
            project_breakdown[project_name]["count"] += 1

            # Client breakdown
            client_name = "No Client"
            if entry.project_id and entry.project_id in project_map:
                project = project_map[entry.project_id]
                if project.client_id and project.client_id in client_map:
                    client_name = client_map[project.client_id].name or "No Client"

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


# Team Reports API Tools (Admin Access Required)


@mcp.tool()
async def get_team_time_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_ids: Optional[str] = None,
    project_ids: Optional[str] = None,
    client_ids: Optional[str] = None,
    billable: Optional[bool] = None,
    description: Optional[str] = None,
    page_size: int = 50,
) -> Dict[str, Any]:
    """Get time entries for all team members (requires admin access).

    Uses Toggl Reports API to retrieve time entries across your entire team.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        user_ids: Comma-separated user IDs to filter by (e.g., "123,456")
        project_ids: Comma-separated project IDs to filter by
        client_ids: Comma-separated client IDs to filter by
        billable: Filter by billable status (true/false)
        description: Filter by description containing text
        page_size: Number of entries per page (max 1000)
    """
    try:
        client = _get_toggl_client()

        # Parse comma-separated IDs
        user_id_list = None
        if user_ids:
            user_id_list = [
                int(x.strip()) for x in user_ids.split(",") if x.strip().isdigit()
            ]

        project_id_list = None
        if project_ids:
            project_id_list = [
                int(x.strip()) for x in project_ids.split(",") if x.strip().isdigit()
            ]

        client_id_list = None
        if client_ids:
            client_id_list = [
                int(x.strip()) for x in client_ids.split(",") if x.strip().isdigit()
            ]

        response = await client.get_team_time_entries(
            start_date=start_date,
            end_date=end_date,
            user_ids=user_id_list,
            project_ids=project_id_list,
            client_ids=client_id_list,
            billable=billable,
            description=description,
            page_size=page_size,
        )

        # Format the response
        result: Dict[str, Any] = {
            "time_entries": [],
            "summary": {
                "total_entries": response.total_count or 0,
                "total_seconds": response.total_seconds or 0,
                "total_billable_seconds": response.total_billable_seconds or 0,
                "total_duration_formatted": client.format_duration(
                    response.total_seconds or 0
                ),
                "billable_duration_formatted": client.format_duration(
                    response.total_billable_seconds or 0
                ),
            },
            "pagination": {
                "per_page": response.per_page or page_size,
                "next_id": response.next_id,
            },
        }

        # Format time entries
        if response.time_entries:
            for entry in response.time_entries:
                formatted_entry = {
                    "id": entry.id,
                    "description": entry.description or "No description",
                    "start": entry.start,
                    "end": entry.end,
                    "duration_seconds": entry.seconds or 0,
                    "duration_formatted": client.format_duration(entry.seconds or 0),
                    "user": entry.user or "Unknown",
                    "user_id": entry.user_id,
                    "email": entry.email,
                    "project": entry.project or "No project",
                    "project_id": entry.project_id,
                    "client": entry.client or "No client",
                    "client_id": entry.client_id,
                    "billable": entry.billable or False,
                    "billable_amount_cents": entry.billable_amount_in_cents,
                    "hourly_rate_cents": entry.hourly_rate_in_cents,
                    "currency": entry.currency,
                    "tags": entry.tags or [],
                }
                result["time_entries"].append(formatted_entry)

        # Add summary message
        total_hours = (response.total_seconds or 0) // 3600
        billable_hours = (response.total_billable_seconds or 0) // 3600
        result["message"] = (
            f"Found {response.total_count or 0} team time entries. Total: {total_hours}h, Billable: {billable_hours}h"
        )

        return result

    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def get_team_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_ids: Optional[str] = None,
    project_ids: Optional[str] = None,
    client_ids: Optional[str] = None,
    billable: Optional[bool] = None,
    grouping: str = "users",
) -> Dict[str, Any]:
    """Get team time summary grouped by users, projects, or clients (requires admin access).

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        user_ids: Comma-separated user IDs to filter by
        project_ids: Comma-separated project IDs to filter by
        client_ids: Comma-separated client IDs to filter by
        billable: Filter by billable status (true/false)
        grouping: How to group results ("users", "projects", "clients", "entries")
    """
    try:
        client = _get_toggl_client()

        # Parse comma-separated IDs
        user_id_list = None
        if user_ids:
            user_id_list = [
                int(x.strip()) for x in user_ids.split(",") if x.strip().isdigit()
            ]

        project_id_list = None
        if project_ids:
            project_id_list = [
                int(x.strip()) for x in project_ids.split(",") if x.strip().isdigit()
            ]

        client_id_list = None
        if client_ids:
            client_id_list = [
                int(x.strip()) for x in client_ids.split(",") if x.strip().isdigit()
            ]

        summary_data = await client.get_team_summary(
            start_date=start_date,
            end_date=end_date,
            user_ids=user_id_list,
            project_ids=project_id_list,
            client_ids=client_id_list,
            billable=billable,
            grouping=grouping,
        )

        # Add formatted durations to the response
        if "groups" in summary_data:
            for group in summary_data.get("groups", []):
                if "seconds" in group:
                    group["duration_formatted"] = client.format_duration(
                        group["seconds"]
                    )
                if "billable_seconds" in group:
                    group["billable_duration_formatted"] = client.format_duration(
                        group["billable_seconds"]
                    )

        # Add overall summary
        if "total_seconds" in summary_data:
            summary_data["total_duration_formatted"] = client.format_duration(
                summary_data["total_seconds"]
            )
        if "total_billable_seconds" in summary_data:
            summary_data["total_billable_duration_formatted"] = client.format_duration(
                summary_data["total_billable_seconds"]
            )

        return {
            "summary": summary_data,
            "grouping": grouping,
            "message": f"Team summary grouped by {grouping} for {start_date or 'all time'} to {end_date or 'now'}",
        }

    except TogglAPIError as e:
        return {"error": str(e)}


@mcp.tool()
async def list_workspace_users() -> Dict[str, Any]:
    """List all users in the current workspace (requires admin access).

    Useful for getting user IDs to filter team reports.
    """
    try:
        client = _get_toggl_client()

        # Get current user to determine workspace
        user = await client.get_current_user()
        workspace_id = client.workspace_id or user.default_workspace_id

        # Get workspace users
        data = await client._make_request("GET", f"/workspaces/{workspace_id}/users")

        users = []
        if isinstance(data, list):
            for user_data in data:
                if isinstance(user_data, dict):
                    users.append(
                        {
                            "id": user_data.get("id"),
                            "name": user_data.get("fullname") or user_data.get("name"),
                            "email": user_data.get("email"),
                            "active": user_data.get("active", True),
                            "admin": user_data.get("admin", False),
                        }
                    )

        return {
            "users": users,
            "total_count": len(users),
            "workspace_id": workspace_id,
            "message": f"Found {len(users)} users in workspace {workspace_id}",
        }

    except TogglAPIError as e:
        return {"error": str(e)}


# Write Operations (Optional - Gated by Environment Variable)


@mcp.tool()
async def create_time_entry(
    description: str,
    project_id: Optional[int] = None,
    start_time: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    billable: bool = False,
    tags: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new time entry (requires TOGGL_WRITE_ENABLED=true).

    Args:
        description: Time entry description (required)
        project_id: Project ID to assign (optional)
        start_time: Start time in ISO format (defaults to now)
        duration_minutes: Duration in minutes. If not provided, creates running entry
        billable: Whether entry is billable (default: false)
        tags: Comma-separated list of tags (optional)

    Returns:
        Created time entry data or error message

    Example:
        create_time_entry("Meeting with client", project_id=123, duration_minutes=60, billable=True)
    """
    # Check if write operations are enabled
    if not TOGGL_WRITE_ENABLED:
        return {
            "error": "Write operations are disabled. Set TOGGL_WRITE_ENABLED=true to enable time entry creation.",
            "help": "This is a security feature to prevent accidental time entry creation.",
        }

    try:
        client = _get_toggl_client()

        # Parse tags if provided
        parsed_tags = []
        if tags:
            parsed_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Convert duration from minutes to seconds
        duration_seconds = None
        if duration_minutes is not None:
            duration_seconds = duration_minutes * 60

        # Create time entry
        entry = await client.create_time_entry(
            description=description,
            project_id=project_id,
            start_time=start_time,
            duration_seconds=duration_seconds,
            billable=billable,
            tags=parsed_tags if parsed_tags else None,
        )

        # Calculate display duration
        display_duration = client.calculate_duration(entry)
        formatted_duration = client.format_duration(display_duration)

        # Determine entry type
        is_running = (entry.duration or 0) < 0
        entry_type = "running" if is_running else "completed"

        result = {
            "time_entry": entry.model_dump(),
            "calculated_duration": display_duration,
            "duration_formatted": formatted_duration,
            "is_running": is_running,
            "entry_type": entry_type,
            "message": f"Created {entry_type} time entry: '{description}' ({formatted_duration})",
        }

        # Add project info if available
        if entry.project_id:
            message: str = result["message"]  # type: ignore
            result["message"] = message + f" for project ID {entry.project_id}"

        return result

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

    # Mount MCP
    app.mount("/mcp", mcp.http_app)  # type: ignore

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
