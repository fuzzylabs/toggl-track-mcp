"""Toggl Track API client with rate limiting and error handling."""

import asyncio
import base64
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, ConfigDict

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
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Make an authenticated request to the Toggl API.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON body data
            retries: Number of retries for rate limiting

        Returns:
            Response data as dict or list

        Raises:
            TogglAPIError: For API errors
        """
        await self.rate_limiter.acquire()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
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
                if attempt == retries:
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
