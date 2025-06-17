"""Tests for Toggl API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from toggl_track_mcp.toggl_client import (
    TogglAPIClient,
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
    """Create a TogglAPIClient for testing."""
    return TogglAPIClient(api_token="test_token", workspace_id=123)


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    response.content = b'{"test": "data"}'
    response.json.return_value = {"test": "data"}
    return response


class TestTogglAPIClient:
    """Test TogglAPIClient initialization and basic functionality."""
    
    def test_init(self):
        """Test client initialization."""
        client = TogglAPIClient("test_token", workspace_id=456)
        assert client.api_token == "test_token"
        assert client.workspace_id == 456
        assert client.base_url == "https://api.track.toggl.com/api/v9"
        assert "Basic" in client.auth_header
    
    def test_init_custom_base_url(self):
        """Test client initialization with custom base URL."""
        client = TogglAPIClient("test_token", base_url="https://custom.api.com/v1")
        assert client.base_url == "https://custom.api.com/v1"


class TestMakeRequest:
    """Test _make_request method."""
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, client, mock_response):
        """Test successful API request."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            result = await client._make_request("GET", "/test")
            
            assert result == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_make_request_empty_response(self, client):
        """Test API request with empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            result = await client._make_request("GET", "/test")
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limited(self, client):
        """Test API request with rate limiting."""
        # First response: rate limited
        rate_limited_response = MagicMock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {"Retry-After": "1"}
        
        # Second response: success
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.content = b'{"success": true}'
        success_response.json.return_value = {"success": True}
        
        with patch("httpx.AsyncClient") as mock_httpx:
            with patch("asyncio.sleep") as mock_sleep:
                mock_httpx.return_value.__aenter__.return_value.request = AsyncMock(
                    side_effect=[rate_limited_response, success_response]
                )
                
                result = await client._make_request("GET", "/test")
                
                assert result == {"success": True}
                mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_make_request_payment_required(self, client):
        """Test API request with payment required error."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            with pytest.raises(TogglAPIError) as exc_info:
                await client._make_request("GET", "/test")
            
            assert "Payment required" in str(exc_info.value)
            assert exc_info.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_make_request_gone(self, client):
        """Test API request with 410 Gone error."""
        mock_response = MagicMock()
        mock_response.status_code = 410
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            with pytest.raises(TogglAPIError) as exc_info:
                await client._make_request("GET", "/test")
            
            assert "Resource no longer available" in str(exc_info.value)
            assert exc_info.value.status_code == 410
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self, client):
        """Test API request with HTTP error."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock(status_code=500, text="Server Error"))
            )
            
            with pytest.raises(TogglAPIError) as exc_info:
                await client._make_request("GET", "/test")
            
            assert "HTTP 500" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_make_request_network_error(self, client):
        """Test API request with network error."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )
            
            with pytest.raises(TogglAPIError) as exc_info:
                await client._make_request("GET", "/test")
            
            assert "Request failed" in str(exc_info.value)


class TestGetCurrentUser:
    """Test get_current_user method."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, client):
        """Test successful get_current_user."""
        mock_data = {
            "id": 123,
            "email": "test@example.com",
            "fullname": "Test User",
            "timezone": "UTC",
            "default_workspace_id": 456,
            "beginning_of_week": 1,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        with patch.object(client, "_make_request", return_value=mock_data):
            result = await client.get_current_user()
            
            assert isinstance(result, TogglUser)
            assert result.id == 123
            assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_response(self, client):
        """Test get_current_user with invalid response format."""
        with patch.object(client, "_make_request", return_value=[]):  # List instead of dict
            with pytest.raises(TogglAPIError) as exc_info:
                await client.get_current_user()
            
            assert "Invalid response format" in str(exc_info.value)


class TestGetCurrentTimeEntry:
    """Test get_current_time_entry method."""
    
    @pytest.mark.asyncio
    async def test_get_current_time_entry_success(self, client):
        """Test successful get_current_time_entry."""
        mock_data = {
            "id": 789,
            "workspace_id": 456,
            "description": "Test task",
            "start": "2023-01-01T10:00:00Z",
            "duration": -1673456400,  # Running entry
            "billable": True,
            "user_id": 123,
        }
        
        with patch.object(client, "_make_request", return_value=mock_data):
            result = await client.get_current_time_entry()
            
            assert isinstance(result, TogglTimeEntry)
            assert result.id == 789
            assert result.description == "Test task"
    
    @pytest.mark.asyncio
    async def test_get_current_time_entry_none(self, client):
        """Test get_current_time_entry with no running entry."""
        with patch.object(client, "_make_request", return_value=None):
            result = await client.get_current_time_entry()
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_current_time_entry_404(self, client):
        """Test get_current_time_entry with 404 error."""
        with patch.object(client, "_make_request", side_effect=TogglAPIError("Not found", status_code=404)):
            result = await client.get_current_time_entry()
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_current_time_entry_other_error(self, client):
        """Test get_current_time_entry with other error."""
        with patch.object(client, "_make_request", side_effect=TogglAPIError("Server error", status_code=500)):
            with pytest.raises(TogglAPIError):
                await client.get_current_time_entry()


class TestGetTimeEntries:
    """Test get_time_entries method."""
    
    @pytest.mark.asyncio
    async def test_get_time_entries_success(self, client):
        """Test successful get_time_entries."""
        mock_data = [
            {
                "id": 1,
                "workspace_id": 456,
                "description": "Task 1",
                "duration": 3600,
                "billable": True,
            },
            {
                "id": 2,
                "workspace_id": 456,
                "description": "Task 2",
                "duration": 1800,
                "billable": False,
            },
        ]
        
        with patch.object(client, "_make_request", return_value=mock_data):
            result = await client.get_time_entries()
            
            assert len(result) == 2
            assert all(isinstance(entry, TogglTimeEntry) for entry in result)
            assert result[0].id == 1
            assert result[1].id == 2
    
    @pytest.mark.asyncio
    async def test_get_time_entries_with_dates(self, client):
        """Test get_time_entries with date parameters."""
        with patch.object(client, "_make_request", return_value=[]) as mock_request:
            await client.get_time_entries(start_date="2023-01-01", end_date="2023-01-02")
            
            mock_request.assert_called_once_with(
                "GET", 
                "/me/time_entries", 
                params={"start_date": "2023-01-01", "end_date": "2023-01-02"}
            )
    
    @pytest.mark.asyncio
    async def test_get_time_entries_invalid_response(self, client):
        """Test get_time_entries with invalid response format."""
        with patch.object(client, "_make_request", return_value={}):  # Dict instead of list
            with pytest.raises(TogglAPIError) as exc_info:
                await client.get_time_entries()
            
            assert "Invalid response format" in str(exc_info.value)


class TestGetTimeEntry:
    """Test get_time_entry method."""
    
    @pytest.mark.asyncio
    async def test_get_time_entry_success(self, client):
        """Test successful get_time_entry."""
        mock_data = {
            "id": 789,
            "workspace_id": 456,
            "description": "Specific task",
            "duration": 3600,
            "billable": True,
        }
        
        with patch.object(client, "_make_request", return_value=mock_data):
            result = await client.get_time_entry(789)
            
            assert isinstance(result, TogglTimeEntry)
            assert result.id == 789
            assert result.description == "Specific task"
    
    @pytest.mark.asyncio
    async def test_get_time_entry_invalid_response(self, client):
        """Test get_time_entry with invalid response format."""
        with patch.object(client, "_make_request", return_value=[]):  # List instead of dict
            with pytest.raises(TogglAPIError) as exc_info:
                await client.get_time_entry(789)
            
            assert "Invalid response format" in str(exc_info.value)


class TestGetWorkspaces:
    """Test get_workspaces method."""
    
    @pytest.mark.asyncio
    async def test_get_workspaces_success(self, client):
        """Test successful get_workspaces."""
        mock_data = [
            {
                "id": 456,
                "name": "My Workspace",
                "admin": True,
                "premium": False,
                "default_currency": "USD",
            }
        ]
        
        with patch.object(client, "_make_request", return_value=mock_data):
            result = await client.get_workspaces()
            
            assert len(result) == 1
            assert isinstance(result[0], TogglWorkspace)
            assert result[0].id == 456
            assert result[0].name == "My Workspace"
    
    @pytest.mark.asyncio
    async def test_get_workspaces_invalid_response(self, client):
        """Test get_workspaces with invalid response format."""
        with patch.object(client, "_make_request", return_value={}):  # Dict instead of list
            with pytest.raises(TogglAPIError) as exc_info:
                await client.get_workspaces()
            
            assert "Invalid response format" in str(exc_info.value)


class TestGetProjects:
    """Test get_projects method."""
    
    @pytest.mark.asyncio
    async def test_get_projects_success(self, client):
        """Test successful get_projects."""
        mock_data = [
            {
                "id": 111,
                "workspace_id": 456,
                "name": "Project 1",
                "active": True,
                "billable": True,
                "color": "#ff0000",
            }
        ]
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_data):
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.get_projects()
                
                assert len(result) == 1
                assert isinstance(result[0], TogglProject)
                assert result[0].id == 111
                assert result[0].name == "Project 1"
    
    @pytest.mark.asyncio
    async def test_get_projects_with_workspace_id(self, client):
        """Test get_projects with specific workspace ID."""
        with patch.object(client, "_make_request", return_value=[]) as mock_request:
            await client.get_projects(workspace_id=789)
            
            mock_request.assert_called_once_with("GET", "/workspaces/789/projects")
    
    @pytest.mark.asyncio
    async def test_get_projects_default_workspace(self, client):
        """Test get_projects using default workspace."""
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=999, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=[]) as mock_request:
            with patch.object(client, "get_current_user", return_value=mock_user):
                client.workspace_id = None  # No default workspace
                await client.get_projects()
                
                mock_request.assert_called_with("GET", "/workspaces/999/projects")


class TestGetClients:
    """Test get_clients method."""
    
    @pytest.mark.asyncio
    async def test_get_clients_success(self, client):
        """Test successful get_clients."""
        mock_data = [
            {
                "id": 333,
                "workspace_id": 456,
                "name": "Client A",
                "at": "2023-01-01T00:00:00Z",
            }
        ]
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_data):
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.get_clients()
                
                assert len(result) == 1
                assert isinstance(result[0], TogglClient)
                assert result[0].id == 333
                assert result[0].name == "Client A"


class TestGetTags:
    """Test get_tags method."""
    
    @pytest.mark.asyncio
    async def test_get_tags_success(self, client):
        """Test successful get_tags."""
        mock_data = [
            {
                "id": 1,
                "workspace_id": 456,
                "name": "meeting",
                "at": "2023-01-01T00:00:00Z",
            }
        ]
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_data):
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.get_tags()
                
                assert len(result) == 1
                assert isinstance(result[0], TogglTag)
                assert result[0].id == 1
                assert result[0].name == "meeting"


class TestCalculateDuration:
    """Test calculate_duration method."""
    
    def test_calculate_duration_completed_entry(self, client):
        """Test calculate_duration for completed time entry."""
        entry = TogglTimeEntry(duration=3600)  # 1 hour
        
        result = client.calculate_duration(entry)
        
        assert result == 3600
    
    def test_calculate_duration_running_entry(self, client):
        """Test calculate_duration for running time entry."""
        import time
        current_time = int(time.time())
        entry = TogglTimeEntry(duration=-current_time + 1800)  # Started 30 minutes ago
        
        result = client.calculate_duration(entry)
        
        # Should be close to 1800 seconds (30 minutes)
        assert 1790 <= result <= 1810
    
    def test_calculate_duration_none_duration(self, client):
        """Test calculate_duration with None duration."""
        entry = TogglTimeEntry(duration=None)
        
        result = client.calculate_duration(entry)
        
        assert result == 0


class TestFormatDuration:
    """Test format_duration method."""
    
    def test_format_duration_hours_minutes(self, client):
        """Test format_duration with hours and minutes."""
        result = client.format_duration(3661)  # 1 hour, 1 minute, 1 second
        
        assert result == "1h 1m"
    
    def test_format_duration_minutes_only(self, client):
        """Test format_duration with minutes only."""
        result = client.format_duration(300)  # 5 minutes
        
        assert result == "0h 5m"
    
    def test_format_duration_zero(self, client):
        """Test format_duration with zero duration."""
        result = client.format_duration(0)
        
        assert result == "0h 0m"


class TestTeamReports:
    """Test team reports API methods."""
    
    @pytest.mark.asyncio
    async def test_get_team_time_entries_success(self, client):
        """Test successful get_team_time_entries."""
        mock_response_data = {
            "time_entries": [
                {
                    "id": 789,
                    "description": "Team task",
                    "start": "2023-01-01T10:00:00Z",
                    "end": "2023-01-01T11:00:00Z",
                    "seconds": 3600,
                    "user": "Team Member",
                    "user_id": 124,
                    "project": "Team Project",
                    "billable": True,
                }
            ],
            "total_seconds": 3600,
            "total_billable_seconds": 3600,
            "total_count": 1,
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch("httpx.AsyncClient") as mock_httpx:
            with patch.object(client, "get_current_user", return_value=mock_user):
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_response_data
                mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                result = await client.get_team_time_entries(
                    start_date="2023-01-01",
                    end_date="2023-01-02"
                )
                
                assert isinstance(result, TogglReportsResponse)
                assert result.total_count == 1
                assert len(result.time_entries or []) == 1
    
    @pytest.mark.asyncio
    async def test_get_team_time_entries_error(self, client):
        """Test get_team_time_entries with API error."""
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch("httpx.AsyncClient") as mock_httpx:
            with patch.object(client, "get_current_user", return_value=mock_user):
                mock_response = MagicMock()
                mock_response.status_code = 400
                mock_response.text = "Bad Request"
                mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                with pytest.raises(TogglAPIError) as exc_info:
                    await client.get_team_time_entries()
                
                assert "Reports API request failed: 400" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_team_summary_success(self, client):
        """Test successful get_team_summary."""
        mock_summary_data = {
            "groups": [
                {"name": "User A", "seconds": 3600, "billable_seconds": 1800},
            ],
            "total_seconds": 3600,
            "total_billable_seconds": 1800,
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch("httpx.AsyncClient") as mock_httpx:
            with patch.object(client, "get_current_user", return_value=mock_user):
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_summary_data
                mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                result = await client.get_team_summary(grouping="users")
                
                assert result == mock_summary_data
                assert "groups" in result
                assert result["total_seconds"] == 3600


class TestCreateTimeEntry:
    """Test create_time_entry method."""
    
    @pytest.mark.asyncio
    async def test_create_running_time_entry(self, client):
        """Test creating a running time entry."""
        mock_data = {
            "id": 999,
            "workspace_id": 123,  # Match client's workspace_id
            "description": "Test running task",
            "start": "2023-01-01T10:00:00Z",
            "duration": -1673456400,  # Negative for running
            "billable": False,
            "user_id": 123,
            "created_with": "toggl-track-mcp",
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_data):
            with patch.object(client, "get_current_user", return_value=mock_user):
                with patch("time.time", return_value=1673456400):
                    result = await client.create_time_entry("Test running task")
                    
                    assert isinstance(result, TogglTimeEntry)
                    assert result.id == 999
                    assert result.description == "Test running task"
                    assert result.duration == -1673456400
                    assert result.billable is False
    
    @pytest.mark.asyncio
    async def test_create_completed_time_entry(self, client):
        """Test creating a completed time entry."""
        mock_data = {
            "id": 998,
            "workspace_id": 123,  # Match client's workspace_id
            "description": "Test completed task",
            "start": "2023-01-01T10:00:00Z",
            "stop": "2023-01-01T11:00:00Z",
            "duration": 3600,
            "billable": True,
            "user_id": 123,
            "created_with": "toggl-track-mcp",
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_data):
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.create_time_entry(
                    "Test completed task",
                    duration_seconds=3600,
                    billable=True
                )
                
                assert isinstance(result, TogglTimeEntry)
                assert result.id == 998
                assert result.description == "Test completed task"
                assert result.duration == 3600
                assert result.billable is True
    
    @pytest.mark.asyncio
    async def test_create_time_entry_custom_start_time(self, client):
        """Test creating a time entry with custom start time."""
        mock_data = {
            "id": 997,
            "workspace_id": 123,  # Match client's workspace_id
            "description": "Test custom time",
            "start": "2023-01-01T08:00:00Z",
            "duration": 7200,
            "billable": False,
            "user_id": 123,
            "created_with": "toggl-track-mcp",
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_data) as mock_request:
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.create_time_entry(
                    "Test custom time",
                    start_time="2023-01-01T08:00:00Z",
                    duration_seconds=7200
                )
                
                # Verify the request was made with custom start time
                call_args = mock_request.call_args
                assert call_args[0][1] == "/workspaces/123/time_entries"  # Client has workspace_id=123
                payload = call_args[1]["json_data"]
                assert payload["start"] == "2023-01-01T08:00:00Z"
                assert payload["duration"] == 7200
                
                assert isinstance(result, TogglTimeEntry)
                assert result.id == 997
    
    @pytest.mark.asyncio
    async def test_create_time_entry_with_project_and_tags(self, client):
        """Test creating a time entry with project and tags."""
        mock_data = {
            "id": 996,
            "workspace_id": 123,  # Match client's workspace_id
            "project_id": 111,
            "description": "Test with project",
            "start": "2023-01-01T10:00:00Z",
            "duration": 1800,
            "billable": True,
            "tags": ["meeting", "client"],
            "user_id": 123,
            "created_with": "toggl-track-mcp",
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_data) as mock_request:
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.create_time_entry(
                    "Test with project",
                    project_id=111,
                    duration_seconds=1800,
                    billable=True,
                    tags=["meeting", "client"]
                )
                
                # Verify the request payload
                call_args = mock_request.call_args
                payload = call_args[1]["json_data"]
                assert payload["project_id"] == 111
                assert payload["tags"] == ["meeting", "client"]
                assert payload["billable"] is True
                
                assert isinstance(result, TogglTimeEntry)
                assert result.project_id == 111
                assert result.tags == ["meeting", "client"]
    
    @pytest.mark.asyncio
    async def test_create_time_entry_with_workspace_id(self, client):
        """Test creating a time entry with explicit workspace ID."""
        mock_data = {
            "id": 995,
            "workspace_id": 789,
            "description": "Test explicit workspace",
            "start": "2023-01-01T10:00:00Z",
            "duration": -1673456400,
            "billable": False,
            "user_id": 123,
            "created_with": "toggl-track-mcp",
        }
        
        with patch.object(client, "_make_request", return_value=mock_data) as mock_request:
            with patch("time.time", return_value=1673456400):
                result = await client.create_time_entry(
                    "Test explicit workspace",
                    workspace_id=789
                )
                
                # Verify the correct workspace was used
                call_args = mock_request.call_args
                assert call_args[0][1] == "/workspaces/789/time_entries"
                payload = call_args[1]["json_data"]
                assert payload["workspace_id"] == 789
                
                assert isinstance(result, TogglTimeEntry)
                assert result.workspace_id == 789
    
    @pytest.mark.asyncio
    async def test_create_time_entry_api_error(self, client):
        """Test create_time_entry with API error."""
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", side_effect=TogglAPIError("Create failed", status_code=400)):
            with patch.object(client, "get_current_user", return_value=mock_user):
                with pytest.raises(TogglAPIError) as exc_info:
                    await client.create_time_entry("Test error")
                
                assert "Create failed" in str(exc_info.value)
                assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_create_time_entry_invalid_response(self, client):
        """Test create_time_entry with invalid response format."""
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=[]):  # List instead of dict
            with patch.object(client, "get_current_user", return_value=mock_user):
                with pytest.raises(TogglAPIError) as exc_info:
                    await client.create_time_entry("Test invalid response")
                
                assert "Invalid response format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_time_entry_default_start_time(self, client):
        """Test create_time_entry uses current time when start_time not provided."""
        mock_data = {
            "id": 994,
            "workspace_id": 123,  # Match client's workspace_id
            "description": "Test default time",
            "start": "2023-01-01T12:00:00Z",
            "duration": -1673456400,
            "billable": False,
            "user_id": 123,
            "created_with": "toggl-track-mcp",
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        # Mock datetime to return a fixed time
        mock_datetime = MagicMock()
        mock_now = MagicMock()
        mock_now.isoformat.return_value = "2023-01-01T12:00:00.000000+00:00"
        mock_datetime.now.return_value = mock_now
        
        with patch.object(client, "_make_request", return_value=mock_data) as mock_request:
            with patch.object(client, "get_current_user", return_value=mock_user):
                with patch("datetime.datetime", mock_datetime):
                    with patch("time.time", return_value=1673456400):
                        result = await client.create_time_entry("Test default time")
                        
                        # Verify the start time was auto-generated
                        call_args = mock_request.call_args
                        payload = call_args[1]["json_data"]
                        assert payload["start"] == "2023-01-01T12:00:00.000000Z"
                        
                        assert isinstance(result, TogglTimeEntry)


class TestPydanticModels:
    """Test Pydantic model validation and extra field handling."""
    
    def test_toggl_user_extra_fields(self):
        """Test TogglUser handles extra fields."""
        data = {
            "id": 123,
            "email": "test@example.com",
            "fullname": "Test User",
            "timezone": "UTC",
            "default_workspace_id": 456,
            "beginning_of_week": 1,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "extra_field": "should_be_ignored"  # Extra field
        }
        
        user = TogglUser(**data)
        assert user.id == 123
        assert user.email == "test@example.com"
        # Extra field should be ignored due to model_config
    
    def test_toggl_workspace_optional_fields(self):
        """Test TogglWorkspace with optional fields."""
        data = {
            "id": 456,
            "name": "Test Workspace",
            "extra_field": "ignored"
        }
        
        workspace = TogglWorkspace(**data)
        assert workspace.id == 456
        assert workspace.name == "Test Workspace"
        assert workspace.premium is None  # Optional field
    
    def test_toggl_time_entry_default_values(self):
        """Test TogglTimeEntry with default values."""
        data = {"id": 789}
        
        entry = TogglTimeEntry(**data)
        assert entry.id == 789
        assert entry.billable is False  # Default value
        assert entry.description == ""  # Default value
        assert entry.duronly is False  # Default value
    
    def test_toggl_project_field_mapping(self):
        """Test TogglProject with API field mapping."""
        data = {
            "id": 111,
            "wid": 456,  # API uses 'wid' for workspace_id
            "name": "Test Project",
            "active": True,
        }
        
        project = TogglProject(**data)
        assert project.id == 111
        assert project.wid == 456
        assert project.name == "Test Project"


class TestCreateTimeEntry:
    """Test create_time_entry method."""
    
    @pytest.mark.asyncio
    async def test_create_time_entry_running(self, client):
        """Test creating a running time entry."""
        mock_response_data = {
            "id": 789,
            "workspace_id": 456,
            "description": "Working on feature",
            "start": "2023-01-01T10:00:00Z",
            "duration": -1673456400,  # Running entry
            "billable": False,
            "tags": ["development"]
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_response_data) as mock_request:
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.create_time_entry(
                    description="Working on feature",
                    tags=["development"]
                )
                
                assert isinstance(result, TogglTimeEntry)
                assert result.id == 789
                assert result.description == "Working on feature"
                assert result.duration == -1673456400
                
                # Verify the request was made correctly
                mock_request.assert_called_once()
                call_args = mock_request.call_args
                assert call_args[0][0] == "POST"  # method
                assert "workspaces/123/time_entries" in call_args[0][1]  # endpoint
                
                # Check payload
                payload = call_args[1]["json_data"]
                assert payload["description"] == "Working on feature"
                assert payload["tags"] == ["development"]
                assert payload["billable"] is False
                assert payload["created_with"] == "toggl-track-mcp"
                assert "start" in payload
                assert payload["duration"] < 0  # Running entry
    
    @pytest.mark.asyncio
    async def test_create_time_entry_completed(self, client):
        """Test creating a completed time entry."""
        mock_response_data = {
            "id": 790,
            "workspace_id": 456,
            "description": "Meeting with client",
            "start": "2023-01-01T10:00:00Z",
            "stop": "2023-01-01T11:00:00Z",
            "duration": 3600,
            "billable": True,
            "project_id": 111
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_response_data) as mock_request:
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.create_time_entry(
                    description="Meeting with client",
                    duration_seconds=3600,
                    project_id=111,
                    billable=True
                )
                
                assert isinstance(result, TogglTimeEntry)
                assert result.id == 790
                assert result.description == "Meeting with client"
                assert result.duration == 3600
                assert result.billable is True
                assert result.project_id == 111
                
                # Verify the request payload
                payload = mock_request.call_args[1]["json_data"]
                assert payload["description"] == "Meeting with client"
                assert payload["duration"] == 3600
                assert payload["project_id"] == 111
                assert payload["billable"] is True
                assert "stop" in payload  # Should have stop time for completed entry
    
    @pytest.mark.asyncio
    async def test_create_time_entry_with_custom_start_time(self, client):
        """Test creating time entry with custom start time."""
        custom_start = "2023-01-01T09:00:00Z"
        mock_response_data = {
            "id": 791,
            "workspace_id": 456,
            "description": "Custom start time entry",
            "start": custom_start,
            "duration": 1800,
        }
        
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "_make_request", return_value=mock_response_data) as mock_request:
            with patch.object(client, "get_current_user", return_value=mock_user):
                result = await client.create_time_entry(
                    description="Custom start time entry",
                    start_time=custom_start,
                    duration_seconds=1800
                )
                
                assert result.start == custom_start
                
                # Verify custom start time was used
                payload = mock_request.call_args[1]["json_data"]
                assert payload["start"] == custom_start
    
    @pytest.mark.asyncio
    async def test_create_time_entry_api_error(self, client):
        """Test create_time_entry with API error."""
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "get_current_user", return_value=mock_user):
            with patch.object(client, "_make_request", side_effect=TogglAPIError("Creation failed")):
                with pytest.raises(TogglAPIError) as exc_info:
                    await client.create_time_entry("Test entry")
                
                assert "Creation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_time_entry_invalid_response(self, client):
        """Test create_time_entry with invalid response format."""
        mock_user = TogglUser(
            id=123, email="test@example.com", fullname="Test", timezone="UTC",
            default_workspace_id=456, beginning_of_week=1,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch.object(client, "get_current_user", return_value=mock_user):
            with patch.object(client, "_make_request", return_value=[]):  # List instead of dict
                with pytest.raises(TogglAPIError) as exc_info:
                    await client.create_time_entry("Test entry")
                
                assert "Invalid response format for created time entry" in str(exc_info.value)