"""Tests for MCP server tools."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from toggl_track_mcp.server import (
    app,
    _get_toggl_client,
)
import toggl_track_mcp.server as server
from toggl_track_mcp.toggl_client import (
    TogglAPIError,
    TogglUser,
    TogglTimeEntry,
    TogglProject,
    TogglClient,
    TogglWorkspace,
    TogglTag,
    TogglReportsResponse,
    TogglReportTimeEntry,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# Test helper functions
def create_mock_user():
    """Create a mock TogglUser for testing."""
    return TogglUser(
        id=123,
        email="test@example.com",
        fullname="Test User",
        timezone="UTC",
        default_workspace_id=456,
        beginning_of_week=1,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
    )


def create_mock_time_entry(running=False):
    """Create a mock TogglTimeEntry for testing."""
    return TogglTimeEntry(
        id=789,
        workspace_id=456,
        project_id=111,
        description="Test task",
        start="2023-01-01T10:00:00Z",
        stop="2023-01-01T11:00:00Z" if not running else None,
        duration=3600 if not running else -1673456400,  # Negative for running
        billable=True,
        user_id=123,
    )


def create_mock_project():
    """Create a mock TogglProject for testing."""
    return TogglProject(
        id=111,
        workspace_id=456,
        name="Test Project",
        active=True,
        billable=True,
        color="#ff0000",
        created_at="2023-01-01T00:00:00Z",
        at="2023-01-01T00:00:00Z",
    )


# Tests for _get_toggl_client helper
def test_get_toggl_client_success():
    """Test _get_toggl_client returns client when available."""
    with patch("toggl_track_mcp.server.toggl_client", MagicMock()):
        client = _get_toggl_client()
        assert client is not None


def test_get_toggl_client_none():
    """Test _get_toggl_client raises error when client is None."""
    with patch("toggl_track_mcp.server.toggl_client", None):
        with pytest.raises(TogglAPIError) as exc_info:
            _get_toggl_client()
        assert "TOGGL_API_TOKEN" in str(exc_info.value)


# Tests for get_current_user
@pytest.mark.asyncio
async def test_get_current_user_success():
    """Test successful get_current_user execution."""
    mock_user = create_mock_user()
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_current_user.return_value = mock_user
        mock_get_client.return_value = mock_client
        
        result = await server.get_current_user.fn()
        
        assert "error" not in result
        assert "user" in result
        assert "message" in result
        assert result["user"]["id"] == 123
        assert result["user"]["email"] == "test@example.com"
        assert "Test User" in result["message"]


@pytest.mark.asyncio
async def test_get_current_user_error_handling():
    """Test get_current_user error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.get_current_user.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for get_current_time_entry
@pytest.mark.asyncio
async def test_get_current_time_entry_success_running():
    """Test get_current_time_entry with running timer."""
    mock_entry = create_mock_time_entry(running=True)
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_current_time_entry.return_value = mock_entry
        mock_client.calculate_duration = MagicMock(return_value=1800)
        mock_client.format_duration = MagicMock(return_value="30m")
        mock_get_client.return_value = mock_client
        
        result = await server.get_current_time_entry.fn()
        
        assert "error" not in result
        assert "time_entry" in result
        assert "message" in result
        assert result["time_entry"]["is_running"] is True
        assert result["time_entry"]["calculated_duration"] == 1800
        assert "Timer running" in result["message"]


@pytest.mark.asyncio
async def test_get_current_time_entry_no_timer():
    """Test get_current_time_entry with no running timer."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_current_time_entry.return_value = None
        mock_get_client.return_value = mock_client
        
        result = await server.get_current_time_entry.fn()
        
        assert "error" not in result
        assert "message" in result
        assert "No time entry is currently running" in result["message"]


@pytest.mark.asyncio
async def test_get_current_time_entry_error_handling():
    """Test get_current_time_entry error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.get_current_time_entry.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for list_time_entries
@pytest.mark.asyncio
async def test_list_time_entries_success():
    """Test successful list_time_entries execution."""
    mock_entries = [create_mock_time_entry(), create_mock_time_entry()]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entries.return_value = mock_entries
        mock_client.calculate_duration = MagicMock(return_value=3600)
        mock_client.format_duration = MagicMock(return_value="1h 0m")
        mock_get_client.return_value = mock_client
        
        result = await server.list_time_entries.fn(
            start_date="2023-01-01",
            end_date="2023-01-02",
            project_id=111,
            billable=True,
        )
        
        assert "error" not in result
        assert "time_entries" in result
        assert "total_count" in result
        assert "total_duration" in result
        assert len(result["time_entries"]) == 2
        assert result["total_duration"] == 7200  # 2 entries * 3600 seconds


@pytest.mark.asyncio
async def test_list_time_entries_filtering():
    """Test list_time_entries with filtering."""
    # Create entries with different properties for filtering
    entry1 = create_mock_time_entry()
    entry1.project_id = 111
    entry1.billable = True
    entry1.description = "Meeting with client"
    
    entry2 = create_mock_time_entry()
    entry2.project_id = 222
    entry2.billable = False
    entry2.description = "Development work"
    
    mock_entries = [entry1, entry2]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entries.return_value = mock_entries
        mock_client.calculate_duration = MagicMock(return_value=3600)
        mock_client.format_duration = MagicMock(return_value="1h 0m")
        mock_get_client.return_value = mock_client
        
        # Test filtering by project_id
        result = await server.list_time_entries.fn(project_id=111)
        assert len(result["time_entries"]) == 1
        
        # Test filtering by billable
        result = await server.list_time_entries.fn(billable=False)
        assert len(result["time_entries"]) == 1
        
        # Test filtering by description
        result = await server.list_time_entries.fn(description_contains="meeting")
        assert len(result["time_entries"]) == 1


@pytest.mark.asyncio
async def test_list_time_entries_error_handling():
    """Test list_time_entries error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.list_time_entries.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for get_time_entry_details
@pytest.mark.asyncio
async def test_get_time_entry_details_success():
    """Test successful get_time_entry_details execution."""
    mock_entry = create_mock_time_entry()
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entry.return_value = mock_entry
        mock_client.calculate_duration = MagicMock(return_value=3600)
        mock_client.format_duration = MagicMock(return_value="1h 0m")
        mock_get_client.return_value = mock_client
        
        result = await server.get_time_entry_details.fn(789)
        
        assert "error" not in result
        assert "time_entry" in result
        assert result["time_entry"]["id"] == 789
        assert result["time_entry"]["calculated_duration"] == 3600


@pytest.mark.asyncio
async def test_get_time_entry_details_error_handling():
    """Test get_time_entry_details error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.get_time_entry_details.fn(789)
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for list_projects
@pytest.mark.asyncio
async def test_list_projects_success():
    """Test successful list_projects execution."""
    active_project = create_mock_project()
    inactive_project = create_mock_project()
    inactive_project.active = False
    mock_projects = [active_project, inactive_project]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_projects.return_value = mock_projects
        mock_get_client.return_value = mock_client
        
        result = await server.list_projects.fn()
        
        assert "error" not in result
        assert "projects" in result
        assert "total_count" in result
        assert "active_count" in result
        assert "inactive_count" in result
        assert result["total_count"] == 2
        assert result["active_count"] == 1
        assert result["inactive_count"] == 1


@pytest.mark.asyncio
async def test_list_projects_error_handling():
    """Test list_projects error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.list_projects.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for list_clients
@pytest.mark.asyncio
async def test_list_clients_success():
    """Test successful list_clients execution."""
    mock_clients = [
        TogglClient(id=1, workspace_id=456, name="Client A", at="2023-01-01T00:00:00Z"),
        TogglClient(id=2, workspace_id=456, name="Client B", at="2023-01-01T00:00:00Z"),
    ]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_clients.return_value = mock_clients
        mock_get_client.return_value = mock_client
        
        result = await server.list_clients.fn()
        
        assert "error" not in result
        assert "clients" in result
        assert "total_count" in result
        assert result["total_count"] == 2


@pytest.mark.asyncio
async def test_list_clients_error_handling():
    """Test list_clients error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.list_clients.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for list_workspaces
@pytest.mark.asyncio
async def test_list_workspaces_success():
    """Test successful list_workspaces execution."""
    mock_workspaces = [
        TogglWorkspace(id=456, name="My Workspace", admin=True, premium=False, default_currency="USD"),
    ]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_workspaces.return_value = mock_workspaces
        mock_get_client.return_value = mock_client
        
        result = await server.list_workspaces.fn()
        
        assert "error" not in result
        assert "workspaces" in result
        assert "total_count" in result
        assert result["total_count"] == 1


@pytest.mark.asyncio
async def test_list_workspaces_error_handling():
    """Test list_workspaces error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.list_workspaces.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for list_tags
@pytest.mark.asyncio
async def test_list_tags_success():
    """Test successful list_tags execution."""
    mock_tags = [
        TogglTag(id=1, workspace_id=456, name="meeting", at="2023-01-01T00:00:00Z"),
        TogglTag(id=2, workspace_id=456, name="development", at="2023-01-01T00:00:00Z"),
    ]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_tags.return_value = mock_tags
        mock_get_client.return_value = mock_client
        
        result = await server.list_tags.fn()
        
        assert "error" not in result
        assert "tags" in result
        assert "total_count" in result
        assert result["total_count"] == 2


@pytest.mark.asyncio
async def test_list_tags_error_handling():
    """Test list_tags error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.list_tags.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for search_time_entries
@pytest.mark.asyncio
async def test_search_time_entries_success():
    """Test successful search_time_entries execution."""
    entry1 = create_mock_time_entry()
    entry1.description = "Meeting with client"
    entry1.tags = ["meeting", "client"]
    
    entry2 = create_mock_time_entry()
    entry2.description = "Development work"
    entry2.tags = ["development", "urgent"]
    
    mock_entries = [entry1, entry2]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entries.return_value = mock_entries
        mock_client.calculate_duration = MagicMock(return_value=3600)
        mock_client.format_duration = MagicMock(return_value="1h 0m")
        mock_get_client.return_value = mock_client
        
        # Test search by description
        result = await server.search_time_entries.fn("meeting")
        
        assert "error" not in result
        assert "time_entries" in result
        assert "query" in result
        assert len(result["time_entries"]) == 1
        assert result["time_entries"][0]["match_reason"] == "description"
        
        # Test search by tag - search for a word that only appears in tags
        mock_client.get_time_entries.return_value = mock_entries
        result = await server.search_time_entries.fn("urgent")  # This should match tags only (not in description)
        assert len(result["time_entries"]) == 1
        assert result["time_entries"][0]["match_reason"] == "tags"


@pytest.mark.asyncio
async def test_search_time_entries_error_handling():
    """Test search_time_entries error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.search_time_entries.fn("test")
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for get_time_summary
@pytest.mark.asyncio
async def test_get_time_summary_success():
    """Test successful get_time_summary execution."""
    # Create mock data
    entry1 = create_mock_time_entry()
    entry1.project_id = 111
    entry1.billable = True
    entry1.tags = ["meeting"]
    
    entry2 = create_mock_time_entry()
    entry2.project_id = 222
    entry2.billable = False
    entry2.tags = ["development"]
    
    mock_entries = [entry1, entry2]
    
    project1 = create_mock_project()
    project1.id = 111
    project1.name = "Project A"
    project1.client_id = 333
    
    project2 = create_mock_project()
    project2.id = 222
    project2.name = "Project B"
    project2.client_id = None
    
    mock_projects = [project1, project2]
    
    client1 = TogglClient(id=333, workspace_id=456, name="Client A", at="2023-01-01T00:00:00Z")
    mock_clients = [client1]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_time_entries.return_value = mock_entries
        mock_client.get_projects.return_value = mock_projects
        mock_client.get_clients.return_value = mock_clients
        mock_client.calculate_duration = MagicMock(return_value=3600)
        mock_client.format_duration = MagicMock(return_value="1h 0m")
        mock_get_client.return_value = mock_client
        
        result = await server.get_time_summary.fn()
        
        assert "error" not in result
        assert "summary" in result
        assert "project_breakdown" in result
        assert "client_breakdown" in result
        assert "tag_breakdown" in result
        assert result["summary"]["total_duration"] == 7200  # 2 entries * 3600
        assert result["summary"]["billable_duration"] == 3600  # 1 billable entry


@pytest.mark.asyncio
async def test_get_time_summary_error_handling():
    """Test get_time_summary error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.get_time_summary.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for get_team_time_entries
@pytest.mark.asyncio
async def test_get_team_time_entries_success():
    """Test successful get_team_time_entries execution."""
    mock_report_entry = TogglReportTimeEntry(
        id=789,
        description="Team task",
        start="2023-01-01T10:00:00Z",
        end="2023-01-01T11:00:00Z",
        seconds=3600,
        user="Team Member",
        user_id=124,
        email="team@example.com",
        project="Team Project",
        project_id=111,
        billable=True,
    )
    
    mock_response = TogglReportsResponse(
        time_entries=[mock_report_entry],
        total_seconds=3600,
        total_billable_seconds=3600,
        total_count=1,
    )
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_team_time_entries.return_value = mock_response
        mock_client.format_duration = MagicMock(return_value="1h 0m")
        mock_get_client.return_value = mock_client
        
        result = await server.get_team_time_entries.fn(
            start_date="2023-01-01",
            end_date="2023-01-02",
            user_ids="123,124",
        )
        
        assert "error" not in result
        assert "time_entries" in result
        assert "summary" in result
        assert len(result["time_entries"]) == 1
        assert result["summary"]["total_entries"] == 1


@pytest.mark.asyncio
async def test_get_team_time_entries_error_handling():
    """Test get_team_time_entries error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.get_team_time_entries.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for get_team_summary
@pytest.mark.asyncio
async def test_get_team_summary_success():
    """Test successful get_team_summary execution."""
    mock_summary_data = {
        "groups": [
            {"name": "User A", "seconds": 3600, "billable_seconds": 1800},
            {"name": "User B", "seconds": 7200, "billable_seconds": 7200},
        ],
        "total_seconds": 10800,
        "total_billable_seconds": 9000,
    }
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_team_summary.return_value = mock_summary_data
        mock_client.format_duration = MagicMock(return_value="1h 0m")
        mock_get_client.return_value = mock_client
        
        result = await server.get_team_summary.fn(grouping="users")
        
        assert "error" not in result
        assert "summary" in result
        assert "grouping" in result
        assert result["grouping"] == "users"
        assert "duration_formatted" in result["summary"]["groups"][0]


@pytest.mark.asyncio
async def test_get_team_summary_error_handling():
    """Test get_team_summary error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.get_team_summary.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# Tests for list_workspace_users
@pytest.mark.asyncio
async def test_list_workspace_users_success():
    """Test successful list_workspace_users execution."""
    mock_user = create_mock_user()
    mock_users_data = [
        {
            "id": 123,
            "fullname": "User A",
            "email": "usera@example.com",
            "active": True,
            "admin": False,
        },
        {
            "id": 124,
            "name": "User B",
            "email": "userb@example.com",
            "active": True,
            "admin": True,
        },
    ]
    
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_current_user.return_value = mock_user
        mock_client._make_request.return_value = mock_users_data
        mock_client.workspace_id = None
        mock_get_client.return_value = mock_client
        
        result = await server.list_workspace_users.fn()
        
        assert "error" not in result
        assert "users" in result
        assert "total_count" in result
        assert "workspace_id" in result
        assert len(result["users"]) == 2
        assert result["workspace_id"] == 456


@pytest.mark.asyncio
async def test_list_workspace_users_error_handling():
    """Test list_workspace_users error handling."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_get_client.side_effect = TogglAPIError("API Error")
        
        result = await server.list_workspace_users.fn()
        
        assert "error" in result
        assert result["error"] == "API Error"


# HTTP endpoint tests
def test_health_endpoint(client):
    """Test health check endpoint."""
    with patch("toggl_track_mcp.server._get_toggl_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_user = create_mock_user()
        mock_client.get_current_user.return_value = mock_user
        mock_get_client.return_value = mock_client
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["user"] == "Test User"


def test_root_endpoint(client):
    """Test root endpoint redirects to MCP."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/mcp"


