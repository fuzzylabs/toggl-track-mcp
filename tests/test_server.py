"""Tests for Toggl Track MCP server."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from toggl_track_mcp.server import app, mcp
from toggl_track_mcp.toggl_client import TogglUser, TogglTimeEntry, TogglProject, TogglClient, TogglWorkspace, TogglTag


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock Toggl user data."""
    return TogglUser(
        id=12345,
        email="test@example.com",
        fullname="Test User",
        timezone="UTC",
        default_workspace_id=67890,
        beginning_of_week=1,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z"
    )


@pytest.fixture
def mock_time_entry():
    """Mock Toggl time entry data."""
    return TogglTimeEntry(
        id=98765,
        workspace_id=67890,
        project_id=11111,
        billable=True,
        start="2023-12-01T09:00:00Z",
        stop="2023-12-01T17:00:00Z",
        duration=28800,  # 8 hours
        description="Working on important project",
        tags=["work", "client"],
        at="2023-12-01T17:00:00Z",
        user_id=12345
    )


@pytest.fixture
def mock_project():
    """Mock Toggl project data."""
    return TogglProject(
        id=11111,
        workspace_id=67890,
        client_id=22222,
        name="Important Project",
        is_private=False,
        active=True,
        at="2023-01-01T00:00:00Z",
        created_at="2023-01-01T00:00:00Z",
        color="#ff0000",
        billable=True
    )


@pytest.fixture
def mock_client():
    """Mock Toggl client data."""
    return TogglClient(
        id=22222,
        workspace_id=67890,
        name="Important Client",
        at="2023-01-01T00:00:00Z"
    )


@pytest.fixture
def mock_workspace():
    """Mock Toggl workspace data."""
    return TogglWorkspace(
        id=67890,
        name="Test Workspace",
        premium=False,
        admin=True,
        default_currency="USD",
        only_admins_may_create_projects=False,
        only_admins_see_billable_rates=False,
        projects_billable_by_default=True,
        api_token="test_token",
        ical_enabled=False
    )


@pytest.fixture
def mock_tag():
    """Mock Toggl tag data."""
    return TogglTag(
        id=33333,
        workspace_id=67890,
        name="work",
        at="2023-01-01T00:00:00Z"
    )


@pytest.fixture
def mock_toggl_client(mock_user, mock_time_entry, mock_project, mock_client, mock_workspace, mock_tag):
    """Mock the Toggl API client."""
    client_mock = AsyncMock()
    client_mock.get_current_user.return_value = mock_user
    client_mock.get_current_time_entry.return_value = mock_time_entry
    client_mock.get_time_entries.return_value = [mock_time_entry]
    client_mock.get_time_entry.return_value = mock_time_entry
    client_mock.get_projects.return_value = [mock_project]
    client_mock.get_clients.return_value = [mock_client]
    client_mock.get_workspaces.return_value = [mock_workspace]
    client_mock.get_tags.return_value = [mock_tag]
    client_mock.calculate_duration.return_value = 28800
    client_mock.format_duration.return_value = "8h 0m"
    return client_mock


class TestMCPSchema:
    """Test MCP schema and tool listing."""

    @patch.dict(os.environ, {"TOGGL_API_TOKEN": "test_token"})
    @pytest.mark.asyncio
    async def test_tools_list(self):
        """Test that tools list returns expected tools."""
        tools = await mcp.get_tools()
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            "get_current_user",
            "get_current_time_entry", 
            "list_time_entries",
            "get_time_entry_details",
            "list_projects",
            "list_clients",
            "list_workspaces",
            "list_tags",
            "search_time_entries",
            "get_time_summary"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names


class TestTogglTools:
    """Test individual Toggl MCP tools."""

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_get_current_user(self, mock_get_client, mock_toggl_client):
        """Test get_current_user tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("get_current_user", {})
        
        assert "user" in result
        assert "message" in result
        assert result["user"]["email"] == "test@example.com"
        assert "Test User" in result["message"]

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_get_current_time_entry(self, mock_get_client, mock_toggl_client):
        """Test get_current_time_entry tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("get_current_time_entry", {})
        
        assert "time_entry" in result
        assert "message" in result
        assert result["time_entry"]["description"] == "Working on important project"
        assert result["time_entry"]["duration_formatted"] == "8h 0m"

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_get_current_time_entry_none(self, mock_get_client, mock_toggl_client):
        """Test get_current_time_entry when no entry is running."""
        mock_toggl_client.get_current_time_entry.return_value = None
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("get_current_time_entry", {})
        
        assert result["message"] == "No time entry is currently running"

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_list_time_entries(self, mock_get_client, mock_toggl_client):
        """Test list_time_entries tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("list_time_entries", {"start_date": "2023-12-01", "end_date": "2023-12-02"})
        
        assert "time_entries" in result
        assert "total_count" in result
        assert "total_duration_formatted" in result
        assert result["total_count"] == 1
        assert len(result["time_entries"]) == 1

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_list_time_entries_with_filters(self, mock_get_client, mock_toggl_client):
        """Test list_time_entries with filtering."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("list_time_entries", {
            "start_date": "2023-12-01",
            "project_id": 11111,
            "billable": True,
            "description_contains": "important"
        })
        
        assert result["total_count"] == 1
        assert "filters_applied" in result
        assert result["filters_applied"]["project_id"] == 11111

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_get_time_entry_details(self, mock_get_client, mock_toggl_client):
        """Test get_time_entry_details tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("get_time_entry_details", {"entry_id": 98765})
        
        assert "time_entry" in result
        assert result["time_entry"]["id"] == 98765

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_list_projects(self, mock_get_client, mock_toggl_client):
        """Test list_projects tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("list_projects", {})
        
        assert "projects" in result
        assert "total_count" in result
        assert "active_count" in result
        assert "inactive_count" in result
        assert result["total_count"] == 1
        assert result["active_count"] == 1

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_list_clients(self, mock_get_client, mock_toggl_client):
        """Test list_clients tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("list_clients", {})
        
        assert "clients" in result
        assert "total_count" in result
        assert result["total_count"] == 1

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_list_workspaces(self, mock_get_client, mock_toggl_client):
        """Test list_workspaces tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("list_workspaces", {})
        
        assert "workspaces" in result
        assert "total_count" in result
        assert result["total_count"] == 1

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_list_tags(self, mock_get_client, mock_toggl_client):
        """Test list_tags tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("list_tags", {})
        
        assert "tags" in result
        assert "total_count" in result
        assert result["total_count"] == 1

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_search_time_entries(self, mock_get_client, mock_toggl_client):
        """Test search_time_entries tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("search_time_entries", {"query": "important"})
        
        assert "query" in result
        assert "time_entries" in result
        assert "total_count" in result
        assert result["query"] == "important"
        assert result["total_count"] == 1
        assert result["time_entries"][0]["match_reason"] == "description"

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_search_time_entries_by_tag(self, mock_get_client, mock_toggl_client):
        """Test search_time_entries by tag."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("search_time_entries", {"query": "work"})
        
        assert result["total_count"] == 1
        assert result["time_entries"][0]["match_reason"] == "tags"

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_get_time_summary(self, mock_get_client, mock_toggl_client):
        """Test get_time_summary tool."""
        mock_get_client.return_value = mock_toggl_client
        
        result = await mcp._call_tool("get_time_summary", {"start_date": "2023-12-01", "end_date": "2023-12-02"})
        
        assert "summary" in result
        assert "project_breakdown" in result
        assert "client_breakdown" in result
        assert "tag_breakdown" in result
        assert "filters_applied" in result
        assert result["summary"]["total_duration"] == 28800


class TestErrorHandling:
    """Test error handling in tools."""

    @patch("toggl_track_mcp.server._get_toggl_client")
    @pytest.mark.asyncio
    async def test_tool_error_handling(self, mock_get_client):
        """Test that tools handle API errors gracefully."""
        from toggl_track_mcp.toggl_client import TogglAPIError
        
        mock_client = AsyncMock()
        mock_client.get_current_user.side_effect = TogglAPIError("API Error")
        mock_get_client.return_value = mock_client
        
        result = await mcp._call_tool("get_current_user", {})
        
        assert "error" in result
        assert result["error"] == "API Error"

    def test_missing_toggl_token(self):
        """Test that missing TOGGL_API_TOKEN is handled gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            from toggl_track_mcp.server import _get_toggl_client
            from toggl_track_mcp.toggl_client import TogglAPIError
            
            with pytest.raises(TogglAPIError, match="TOGGL_API_TOKEN environment variable is required"):
                _get_toggl_client()


class TestHTTPEndpoints:
    """Test HTTP endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_user = TogglUser(
                id=12345,
                email="test@example.com", 
                fullname="Test User",
                timezone="UTC",
                default_workspace_id=67890,
                beginning_of_week=1,
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z"
            )
            mock_client.get_current_user.return_value = mock_user
            mock_get_client.return_value = mock_client
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["user"] == "Test User"

    def test_root_endpoint(self, client):
        """Test root endpoint redirects to MCP."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/mcp"


class TestAuthentication:
    """Test authentication middleware."""

    def test_authentication_with_api_key(self, client):
        """Test API key authentication when MCP_API_KEY is set."""
        with patch.dict(os.environ, {"MCP_API_KEY": "test_key"}):
            # Request without auth header should fail
            response = client.post("/mcp/", json={"test": "data"})
            assert response.status_code == 401
            
            # Request with wrong auth header should fail  
            response = client.post(
                "/mcp/", 
                json={"test": "data"},
                headers={"Authorization": "Bearer wrong_key"}
            )
            assert response.status_code == 401
            
            # Request with correct auth header should pass to MCP
            response = client.post(
                "/mcp/",
                json={"test": "data"}, 
                headers={"Authorization": "Bearer test_key"}
            )
            # Will fail at MCP level, but auth passes
            assert response.status_code != 401

    def test_no_authentication_when_no_api_key(self, client):
        """Test that requests pass through when no MCP_API_KEY is set."""
        with patch.dict(os.environ, {}, clear=True):
            response = client.post("/mcp/", json={"test": "data"})
            # Will fail at MCP level, but auth passes
            assert response.status_code != 401