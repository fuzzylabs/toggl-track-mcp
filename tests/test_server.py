"""Tests for Toggl Track MCP server."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from toggl_track_mcp.server import app
from toggl_track_mcp.toggl_client import TogglUser


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestErrorHandling:
    """Test error handling in tools."""

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


