"""Toggl Track API client with rate limiting and error handling."""

import base64
import os
from typing import Any, Dict, List, Optional, Union
import asyncio
import logging

import httpx
from pydantic import BaseModel, Field

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


class TogglWorkspace(BaseModel):
    """Toggl workspace model."""
    id: int
    name: str
    premium: bool
    admin: bool
    default_hourly_rate: Optional[float] = None
    default_currency: str
    only_admins_may_create_projects: bool
    only_admins_see_billable_rates: bool
    projects_billable_by_default: bool
    api_token: str
    ical_enabled: bool


class TogglProject(BaseModel):
    """Toggl project model."""
    id: int
    workspace_id: int
    client_id: Optional[int] = None
    name: str
    is_private: bool
    active: bool
    at: str
    created_at: str
    color: str
    billable: Optional[bool] = None
    estimated_hours: Optional[int] = None
    rate: Optional[float] = None
    currency: Optional[str] = None
    recurring: bool = False
    actual_hours: Optional[int] = None


class TogglClient(BaseModel):
    """Toggl client model."""
    id: int
    workspace_id: int
    name: str
    notes: Optional[str] = None
    at: str


class TogglTimeEntry(BaseModel):
    """Toggl time entry model."""
    id: int
    workspace_id: int
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    billable: bool
    start: str
    stop: Optional[str] = None
    duration: int
    description: str
    tags: Optional[List[str]] = None
    tag_ids: Optional[List[int]] = None
    duronly: bool = False
    at: str
    user_id: int


class TogglTag(BaseModel):
    """Toggl tag model."""
    id: int
    workspace_id: int
    name: str
    at: str


class TogglAPIError(Exception):
    """Custom exception for Toggl API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
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
        burst_size: int = 3
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
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        self.auth_header = f"Basic {auth_b64}"
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retries: int = 3
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
            "User-Agent": "toggl-track-mcp/0.1.0"
        }
        
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data
                    )
                    
                    if response.status_code == 429:
                        # Rate limited - wait and retry
                        retry_after = int(response.headers.get("Retry-After", "2"))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if response.status_code == 402:
                        raise TogglAPIError(
                            "Payment required - check your Toggl subscription",
                            status_code=402
                        )
                    
                    if response.status_code == 410:
                        raise TogglAPIError(
                            "Resource no longer available",
                            status_code=410
                        )
                    
                    response.raise_for_status()
                    
                    # Handle empty responses
                    if response.status_code == 204 or not response.content:
                        return {}
                    
                    return response.json()
                    
            except httpx.HTTPStatusError as e:
                if attempt == retries:
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                    raise TogglAPIError(error_msg, status_code=e.response.status_code)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.RequestError as e:
                if attempt == retries:
                    raise TogglAPIError(f"Request failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)
        
        raise TogglAPIError("Max retries exceeded")
    
    async def get_current_user(self) -> TogglUser:
        """Get current user information."""
        data = await self._make_request("GET", "/me")
        return TogglUser(**data)
    
    async def get_current_time_entry(self) -> Optional[TogglTimeEntry]:
        """Get currently running time entry."""
        try:
            data = await self._make_request("GET", "/me/time_entries/current")
            return TogglTimeEntry(**data) if data else None
        except TogglAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_time_entries(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> List[TogglTimeEntry]:
        """Get time entries with optional filtering."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        data = await self._make_request("GET", "/me/time_entries", params=params)
        return [TogglTimeEntry(**entry) for entry in data]
    
    async def get_time_entry(self, entry_id: int) -> TogglTimeEntry:
        """Get specific time entry by ID."""
        data = await self._make_request("GET", f"/me/time_entries/{entry_id}")
        return TogglTimeEntry(**data)
    
    async def get_workspaces(self) -> List[TogglWorkspace]:
        """Get available workspaces."""
        data = await self._make_request("GET", "/me/workspaces")
        return [TogglWorkspace(**workspace) for workspace in data]
    
    async def get_projects(self, workspace_id: Optional[int] = None) -> List[TogglProject]:
        """Get projects for workspace."""
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id
        
        data = await self._make_request("GET", f"/workspaces/{workspace_id}/projects")
        return [TogglProject(**project) for project in data]
    
    async def get_clients(self, workspace_id: Optional[int] = None) -> List[TogglClient]:
        """Get clients for workspace."""
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id
        
        data = await self._make_request("GET", f"/workspaces/{workspace_id}/clients")
        return [TogglClient(**client) for client in data]
    
    async def get_tags(self, workspace_id: Optional[int] = None) -> List[TogglTag]:
        """Get tags for workspace."""
        if not workspace_id:
            user = await self.get_current_user()
            workspace_id = self.workspace_id or user.default_workspace_id
        
        data = await self._make_request("GET", f"/workspaces/{workspace_id}/tags")
        return [TogglTag(**tag) for tag in data]
    
    def calculate_duration(self, time_entry: TogglTimeEntry) -> int:
        """Calculate actual duration for time entry (handles running entries)."""
        if time_entry.duration < 0:
            # Running time entry - duration is negative offset from current time
            import time
            return int(time.time()) + time_entry.duration
        return time_entry.duration
    
    def format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"