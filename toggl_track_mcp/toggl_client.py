"""Toggl Track API client with rate limiting and error handling."""

import asyncio
import base64
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from pydantic import BaseModel, ConfigDict

from .analytics import (
    ANALYTICS_BASE_URL,
    TogglAnalyticsChart,
    TogglAnalyticsDashboard,
    build_query,
    period_for_dashboard,
    resolve_rows,
    sort_rows,
    summarise_rows,
)
from .rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)


class TogglUser(BaseModel):
    """Toggl user model."""

    id: int
    email: str
    fullname: str
    timezone: str
    default_workspace_id: int
    beginning_of_week: int
    image_url: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(extra="ignore")


class TogglWorkspace(BaseModel):
    """Toggl workspace model."""

    id: Optional[int] = None
    name: Optional[str] = None
    premium: Optional[bool] = None
    admin: Optional[bool] = None
    default_hourly_rate: Optional[float] = None
    default_currency: Optional[str] = None
    only_admins_may_create_projects: Optional[bool] = None
    only_admins_see_billable_rates: Optional[bool] = None
    projects_billable_by_default: Optional[bool] = None
    api_token: Optional[str] = None
    ical_enabled: Optional[bool] = None
    # Additional fields that might be present
    organization_id: Optional[int] = None
    active_project_count: Optional[int] = None

    model_config = ConfigDict(
        extra="ignore"
    )  # Ignore extra fields not defined in model


class TogglProject(BaseModel):
    """Toggl project model."""

    id: Optional[int] = None
    wid: Optional[int] = None  # workspace_id in API response
    workspace_id: Optional[int] = None  # Alternative field name
    client_id: Optional[int] = None
    name: Optional[str] = None
    is_private: Optional[bool] = None
    active: Optional[bool] = None
    at: Optional[str] = None
    created_at: Optional[str] = None
    color: Optional[str] = None
    billable: Optional[bool] = None
    estimated_hours: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    rate: Optional[float] = None
    currency: Optional[str] = None
    recurring: bool = False
    actual_hours: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class TogglClient(BaseModel):
    """Toggl client model."""

    id: Optional[int] = None
    wid: Optional[int] = None  # workspace_id in API response
    workspace_id: Optional[int] = None  # Alternative field name
    name: Optional[str] = None
    notes: Optional[str] = None
    at: Optional[str] = None
    # Additional fields that might be present
    total_count: Optional[int] = None

    model_config = ConfigDict(
        extra="ignore"
    )  # Ignore extra fields not defined in model


class TogglTimeEntry(BaseModel):
    """Toggl time entry model."""

    id: Optional[int] = None
    wid: Optional[int] = None  # workspace_id in API response
    workspace_id: Optional[int] = None  # Alternative field name
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    billable: bool = False
    start: Optional[str] = None
    stop: Optional[str] = None
    duration: Optional[int] = None
    description: str = ""
    tags: Optional[List[str]] = None
    tag_ids: Optional[List[int]] = None
    duronly: bool = False
    at: Optional[str] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class TogglTag(BaseModel):
    """Toggl tag model."""

    id: Optional[int] = None
    wid: Optional[int] = None  # workspace_id in API response
    workspace_id: Optional[int] = None  # Alternative field name
    name: Optional[str] = None
    at: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class TogglReportTimeEntry(BaseModel):
    """Toggl Reports API time entry model."""

    id: Optional[int] = None
    start: Optional[str] = None
    end: Optional[str] = None
    seconds: Optional[int] = None
    description: Optional[str] = None
    project: Optional[str] = None
    project_id: Optional[int] = None
    project_color: Optional[str] = None
    project_hex_color: Optional[str] = None
    client: Optional[str] = None
    client_id: Optional[int] = None
    user: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    tags: Optional[List[str]] = None
    billable: Optional[bool] = None
    billable_amount_in_cents: Optional[int] = None
    hourly_rate_in_cents: Optional[int] = None
    currency: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class TogglReportSummary(BaseModel):
    """Toggl Reports API summary model."""

    seconds: Optional[int] = None
    billable_seconds: Optional[int] = None
    resolution: Optional[str] = None
    billable_amount_in_cents: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class TogglReportsResponse(BaseModel):
    """Toggl Reports API response model."""

    time_entries: Optional[List[TogglReportTimeEntry]] = None
    total_seconds: Optional[int] = None
    total_billable_seconds: Optional[int] = None
    total_count: Optional[int] = None
    per_page: Optional[int] = None
    next_id: Optional[int] = None
    summary: Optional[TogglReportSummary] = None

    model_config = ConfigDict(extra="ignore")


class TogglAPIError(Exception):
    """Custom exception for Toggl API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class TogglAPIClient:
    """Toggl Track API client with rate limiting."""

    def __init__(
        self,
        api_token: str,
        base_url: str = "https://api.track.toggl.com/api/v9",
        workspace_id: Optional[int] = None,
        requests_per_second: float = 1.0,
        burst_size: int = 3,
    ):
        """Initialize Toggl API client.

        Args:
            api_token: Toggl Track API token
            base_url: Base URL for Toggl API
            workspace_id: Default workspace ID (optional)
            requests_per_second: Rate limit for requests
            burst_size: Burst capacity for rate limiting
        """
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self.workspace_id = workspace_id
        self.rate_limiter = TokenBucketRateLimiter(requests_per_second, burst_size)
        self._organization_id: Optional[int] = None

        # Create auth header
        auth_string = f"{api_token}:api_token"
        auth_bytes = auth_string.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
        self.auth_header = f"Basic {auth_b64}"

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retries: int = 3,
        base_url: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Make an authenticated request to the Toggl API.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON body data
            retries: Number of retries for rate limiting
            base_url: Override the client's base URL (used for the Analytics API,
                which is served from a different path than the v9 API)

        Returns:
            Response data as dict or list

        Raises:
            TogglAPIError: For API errors
        """
        await self.rate_limiter.acquire()

        url = f"{(base_url or self.base_url).rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "User-Agent": "toggl-track-mcp/0.1.0",
        }

        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data,
                    )

                    if response.status_code == 429:
                        # Rate limited - wait and retry
                        retry_after = int(response.headers.get("Retry-After", "2"))
                        logger.warning(
                            f"Rate limited, waiting {retry_after} seconds..."
                        )
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status_code == 402:
                        raise TogglAPIError(
                            "Payment required - check your Toggl subscription",
                            status_code=402,
                        )

                    if response.status_code == 410:
                        raise TogglAPIError(
                            "Resource no longer available", status_code=410
                        )

                    response.raise_for_status()

                    # Handle empty responses
                    if response.status_code == 204 or not response.content:
                        return {}

                    result = response.json()
                    return result  # type: ignore[no-any-return]

            except httpx.HTTPStatusError as e:
                # A 4xx is the server rejecting the request itself (bad payload,
                # no permission, no such resource) and will fail identically on
                # retry, so surface it rather than backing off three times.
                is_client_error = 400 <= e.response.status_code < 500
                if attempt == retries or is_client_error:
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                    raise TogglAPIError(error_msg, status_code=e.response.status_code)
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except httpx.RequestError as e:
                if attempt == retries:
                    raise TogglAPIError(f"Request failed: {str(e)}")
                await asyncio.sleep(2**attempt)

        raise TogglAPIError("Max retries exceeded")

    async def get_current_user(self) -> TogglUser:
        """Get current user information."""
        data = await self._make_request("GET", "/me")
        if isinstance(data, dict):
            return TogglUser(**data)
        raise TogglAPIError("Invalid response format for user data")

    async def get_current_time_entry(self) -> Optional[TogglTimeEntry]:
        """Get currently running time entry."""
        try:
            data = await self._make_request("GET", "/me/time_entries/current")
            if data and isinstance(data, dict):
                return TogglTimeEntry(**data)
            return None
        except TogglAPIError as e:
            if e.status_code == 404:
                return None
            raise

    async def get_time_entries(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> List[TogglTimeEntry]:
        """Get time entries with optional filtering."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        data = await self._make_request("GET", "/me/time_entries", params=params)
        if isinstance(data, list):
            return [TogglTimeEntry(**entry) for entry in data]
        raise TogglAPIError("Invalid response format for time entries")

    async def get_time_entry(self, entry_id: int) -> TogglTimeEntry:
        """Get specific time entry by ID."""
        data = await self._make_request("GET", f"/me/time_entries/{entry_id}")
        if isinstance(data, dict):
            return TogglTimeEntry(**data)
        raise TogglAPIError("Invalid response format for time entry")

    async def create_time_entry(
        self,
        description: str,
        start_time: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        billable: bool = False,
        tags: Optional[List[str]] = None,
        workspace_id: Optional[int] = None,
    ) -> TogglTimeEntry:
        """Create a new time entry.

        Args:
            description: Time entry description
            start_time: Start time in ISO format (defaults to now)
            duration_seconds: Duration in seconds. If None, creates running entry
            project_id: Project ID to assign
            task_id: Task ID to assign
            billable: Whether entry is billable
            tags: List of tags to assign
            workspace_id: Workspace ID (uses default if not provided)

        Returns:
            Created time entry

        Raises:
            TogglAPIError: If creation fails
        """
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        # Build payload
        import datetime

        if not start_time:
            start_time = (
                datetime.datetime.now(datetime.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )

        payload: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "description": description,
            "start": start_time,
            "billable": billable,
            "created_with": "toggl-track-mcp",
        }

        # Add optional fields
        if project_id:
            payload["project_id"] = project_id
        if task_id:
            payload["task_id"] = task_id
        if tags:
            payload["tags"] = tags

        # Handle duration
        if duration_seconds is not None:
            # Completed entry
            payload["duration"] = duration_seconds
            if duration_seconds > 0:
                # Calculate stop time
                start_dt = datetime.datetime.fromisoformat(start_time.rstrip("Z"))
                stop_dt = start_dt + datetime.timedelta(seconds=duration_seconds)
                payload["stop"] = stop_dt.isoformat() + "Z"
        else:
            # Running entry - use negative timestamp
            import time

            payload["duration"] = -int(time.time())

        data = await self._make_request(
            "POST", f"/workspaces/{workspace_id}/time_entries", json_data=payload
        )
        if isinstance(data, dict):
            return TogglTimeEntry(**data)
        raise TogglAPIError("Invalid response format for created time entry")

    async def get_workspaces(self) -> List[TogglWorkspace]:
        """Get available workspaces."""
        data = await self._make_request("GET", "/me/workspaces")
        if isinstance(data, list):
            return [TogglWorkspace(**workspace) for workspace in data]
        raise TogglAPIError("Invalid response format for workspaces")

    async def get_projects(
        self, workspace_id: Optional[int] = None
    ) -> List[TogglProject]:
        """Get projects for workspace."""
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        data = await self._make_request("GET", f"/workspaces/{workspace_id}/projects")
        if isinstance(data, list):
            return [TogglProject(**project) for project in data]
        raise TogglAPIError("Invalid response format for projects")

    async def get_clients(
        self, workspace_id: Optional[int] = None
    ) -> List[TogglClient]:
        """Get clients for workspace."""
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        data = await self._make_request("GET", f"/workspaces/{workspace_id}/clients")
        if isinstance(data, list):
            return [TogglClient(**client) for client in data]
        raise TogglAPIError("Invalid response format for clients")

    async def create_project(
        self,
        name: str,
        client_id: Optional[int] = None,
        color: Optional[str] = None,
        billable: bool = False,
        is_private: bool = True,
        active: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        estimated_hours: Optional[int] = None,
        workspace_id: Optional[int] = None,
    ) -> TogglProject:
        """Create a new project in the workspace.

        ``start_date``, ``end_date`` and ``estimated_hours`` are accepted by the
        Toggl v9 API but only take effect on plans that support them
        (Premium / Starter+ for dates, Team+ for estimates). On lower plans
        Toggl silently ignores the unsupported fields.

        ``active`` defaults to True. Toggl's API defaults to False when the
        field is omitted, which produces an archived project that rejects
        member adds and time entries — almost never what callers want.
        """
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        payload: Dict[str, Any] = {
            "name": name,
            "billable": billable,
            "is_private": is_private,
            "active": active,
        }
        if client_id:
            payload["client_id"] = client_id
        if color:
            payload["color"] = color
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        if estimated_hours is not None:
            payload["estimated_hours"] = estimated_hours

        data = await self._make_request(
            "POST", f"/workspaces/{workspace_id}/projects", json_data=payload
        )
        if isinstance(data, dict):
            return TogglProject(**data)
        raise TogglAPIError("Invalid response format for created project")

    async def add_project_user(
        self,
        project_id: int,
        user_id: int,
        manager: bool = False,
        workspace_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a workspace user to a project.

        Maps to ``POST /workspaces/{workspace_id}/project_users``. Toggl accepts
        only one user per call, so to add several members the caller invokes
        this method once per user.
        """
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        payload: Dict[str, Any] = {
            "project_id": project_id,
            "user_id": user_id,
            "manager": manager,
        }

        data = await self._make_request(
            "POST", f"/workspaces/{workspace_id}/project_users", json_data=payload
        )
        if isinstance(data, dict):
            return data
        raise TogglAPIError("Invalid response format for created project user")

    async def create_client(
        self,
        name: str,
        notes: Optional[str] = None,
        workspace_id: Optional[int] = None,
    ) -> TogglClient:
        """Create a new client in the workspace."""
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        payload: Dict[str, Any] = {"name": name, "wid": workspace_id}
        if notes:
            payload["notes"] = notes

        data = await self._make_request(
            "POST", f"/workspaces/{workspace_id}/clients", json_data=payload
        )
        if isinstance(data, dict):
            return TogglClient(**data)
        raise TogglAPIError("Invalid response format for created client")

    async def get_tags(self, workspace_id: Optional[int] = None) -> List[TogglTag]:
        """Get tags for workspace."""
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        data = await self._make_request("GET", f"/workspaces/{workspace_id}/tags")
        if isinstance(data, list):
            return [TogglTag(**tag) for tag in data]
        raise TogglAPIError("Invalid response format for tags")

    def calculate_duration(self, time_entry: TogglTimeEntry) -> int:
        """Calculate actual duration for time entry (handles running entries)."""
        duration = time_entry.duration or 0
        if duration < 0:
            # Running time entry - duration is negative offset from current time
            import time

            return int(time.time()) + duration
        return duration

    def format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    # Reports API Methods (Read-Only Team Access)

    async def get_team_time_entries(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        workspace_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None,
        project_ids: Optional[List[int]] = None,
        client_ids: Optional[List[int]] = None,
        billable: Optional[bool] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page_size: int = 50,
    ) -> TogglReportsResponse:
        """Get team time entries using Reports API.

        Requires admin access. Returns time entries for all team members.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            workspace_id: Workspace ID (uses default if not provided)
            user_ids: Filter by specific user IDs
            project_ids: Filter by specific project IDs
            client_ids: Filter by specific client IDs
            billable: Filter by billable status
            description: Filter by description containing text
            tags: Filter by tags
            page_size: Number of entries per page (max 1000)
        """
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        # Build request payload
        payload: Dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
            "page_size": min(page_size, 1000),  # API max is 1000
        }

        # Add optional filters
        if user_ids:
            payload["user_ids"] = user_ids
        if project_ids:
            payload["project_ids"] = project_ids
        if client_ids:
            payload["client_ids"] = client_ids
        if billable is not None:
            payload["billable"] = billable
        if description:
            payload["description"] = description
        if tags:
            payload["tag_ids"] = tags

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        # Use Reports API endpoint
        reports_url = "https://api.track.toggl.com/reports/api/v3"
        url = f"{reports_url}/workspace/{workspace_id}/search/time_entries"

        await self.rate_limiter.acquire()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                return TogglReportsResponse(**data)
            else:
                error_msg = f"Reports API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise TogglAPIError(error_msg, response.status_code)

    async def get_team_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        workspace_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None,
        project_ids: Optional[List[int]] = None,
        client_ids: Optional[List[int]] = None,
        billable: Optional[bool] = None,
        grouping: str = "users",
    ) -> Dict[str, Any]:
        """Get team time summary using Reports API.

        Args:
            grouping: How to group results ("users", "projects", "clients", "entries")
            Other args: Same as get_team_time_entries
        """
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        # Build request payload
        payload: Dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
            "grouping": grouping,
        }

        # Add optional filters
        if user_ids:
            payload["user_ids"] = user_ids
        if project_ids:
            payload["project_ids"] = project_ids
        if client_ids:
            payload["client_ids"] = client_ids
        if billable is not None:
            payload["billable"] = billable

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        # Use Reports API summary endpoint
        reports_url = "https://api.track.toggl.com/reports/api/v3"
        url = f"{reports_url}/workspace/{workspace_id}/summary/time_entries"

        await self.rate_limiter.acquire()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data: Dict[str, Any] = response.json()
                return data
            else:
                error_msg = (
                    f"Reports API summary request failed: {response.status_code}"
                )
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except Exception:
                    error_msg += f" - {response.text}"
                raise TogglAPIError(error_msg, response.status_code)

    # Analytics API Methods (Custom Reports)
    #
    # Custom reports are organization-scoped dashboards. See analytics.py for
    # what this API is and why it needs handling of its own.

    async def get_organization_id(self, workspace_id: Optional[int] = None) -> int:
        """Get the organization ID that owns a workspace.

        Custom reports are scoped to an organization, not a workspace, but the
        workspace is what callers usually have to hand. Resolving it costs two
        requests, so the default workspace's organization is cached.
        """
        if not workspace_id and self._organization_id is not None:
            return self._organization_id

        requested_id = workspace_id
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id

        for workspace in await self.get_workspaces():
            if workspace.id == workspace_id and workspace.organization_id:
                if requested_id is None:
                    self._organization_id = workspace.organization_id
                return workspace.organization_id

        raise TogglAPIError(f"No organization found for workspace {workspace_id}")

    async def list_dashboards(
        self,
        organization_id: Optional[int] = None,
        only_pinned: bool = False,
    ) -> List[TogglAnalyticsDashboard]:
        """List the custom reports in an organization.

        Args:
            organization_id: Organization ID (resolved from the workspace if omitted)
            only_pinned: Return only reports pinned to the sidebar
        """
        if not organization_id:
            organization_id = await self.get_organization_id()

        params: Dict[str, Any] = {"organization_id": organization_id}
        if only_pinned:
            params["pinned"] = "true"

        data = await self._make_request(
            "GET", "/dashboards", params=params, base_url=ANALYTICS_BASE_URL
        )
        if isinstance(data, list):
            return [TogglAnalyticsDashboard(**dashboard) for dashboard in data]
        raise TogglAPIError("Invalid response format for custom reports")

    async def get_dashboard(self, dashboard_id: int) -> TogglAnalyticsDashboard:
        """Get a custom report's full definition, including its charts."""
        data = await self._make_request(
            "GET", f"/dashboards/{dashboard_id}", base_url=ANALYTICS_BASE_URL
        )
        if isinstance(data, dict):
            return TogglAnalyticsDashboard(**data)
        raise TogglAPIError("Invalid response format for custom report")

    async def run_analytics_query(
        self,
        organization_id: int,
        query: Dict[str, Any],
        include_dicts: bool = True,
    ) -> Dict[str, Any]:
        """Run a query against the analytics engine.

        Args:
            organization_id: Organization the query runs against
            query: Query payload (period, groupings, aggregations, filters)
            include_dicts: Ask for the id-to-name dictionaries alongside the rows
        """
        data = await self._make_request(
            "POST",
            f"/organizations/{organization_id}/query",
            params={
                "response_format": "json_row",
                "include_dicts": "true" if include_dicts else "false",
            },
            json_data=query,
            base_url=ANALYTICS_BASE_URL,
        )
        if isinstance(data, dict):
            return data
        raise TogglAPIError("Invalid response format for analytics query")

    async def run_dashboard_chart(
        self,
        dashboard_id: int,
        chart_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dashboard: Optional[TogglAnalyticsDashboard] = None,
    ) -> Dict[str, Any]:
        """Run one chart of a custom report and return its rows.

        Reproduces what the report shows: the chart's saved query, the
        report-level filters, and either the report's saved period or the dates
        given here.

        Args:
            dashboard_id: Custom report ID
            chart_id: Chart to run (defaults to the report's first chart)
            start_date: Override start date (YYYY-MM-DD)
            end_date: Override end date (YYYY-MM-DD)
            dashboard: Already-fetched report, to save a round trip
        """
        if dashboard is None:
            dashboard = await self.get_dashboard(dashboard_id)

        charts: List[TogglAnalyticsChart] = dashboard.charts or []
        if not charts:
            raise TogglAPIError(f"Custom report {dashboard_id} has no charts")

        if chart_id is None:
            chart = charts[0]
        else:
            matches = [chart for chart in charts if chart.id == chart_id]
            if not matches:
                available = ", ".join(str(chart.id) for chart in charts)
                raise TogglAPIError(
                    f"Chart {chart_id} is not part of custom report "
                    f"{dashboard_id} (charts: {available})"
                )
            chart = matches[0]

        # Only a relative preset needs a week start, and the report's own
        # setting wins over the caller's, so skip the /me call when both dates
        # are given.
        fallback_beginning_of_week = None
        today: Optional[date] = None
        if not (start_date and end_date):
            user = await self.get_current_user()
            fallback_beginning_of_week = user.beginning_of_week
            try:
                today = datetime.now(ZoneInfo(user.timezone)).date()
            except ZoneInfoNotFoundError:
                logger.warning(
                    "Unknown Toggl timezone %r; using the server's local date",
                    user.timezone,
                )
                today = date.today()

        period = period_for_dashboard(
            dashboard,
            start_date=start_date,
            end_date=end_date,
            today=today,
            fallback_beginning_of_week=fallback_beginning_of_week,
        )

        query, local_ordinations = build_query(dashboard, chart, period)

        organization_id = dashboard.organization_id
        if not organization_id:
            organization_id = await self.get_organization_id()

        response = await self.run_analytics_query(organization_id, query)
        rows = resolve_rows(
            response.get("data_json_row") or [], response.get("dictionaries")
        )
        rows = sort_rows(rows, local_ordinations)

        return {
            "report_id": dashboard_id,
            "report_name": dashboard.name,
            "chart_id": chart.id,
            "chart_type": chart.type,
            "period": period,
            "rows": rows,
            "totals": summarise_rows(rows),
            "query": query,
        }
