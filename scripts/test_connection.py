#!/usr/bin/env python3
"""Test script to verify Toggl Track API connection."""

import asyncio
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from toggl_track_mcp.toggl_client import TogglAPIClient, TogglAPIError


async def test_connection():
    """Test Toggl Track API connection and functionality."""
    load_dotenv()
    
    api_token = os.getenv("TOGGL_API_TOKEN")
    if not api_token:
        print("❌ Error: TOGGL_API_TOKEN environment variable not set")
        print("Please set your Toggl Track API token in the .env file")
        return False
    
    print("🔍 Testing Toggl Track API connection...\n")
    
    try:
        # Initialize client
        client = TogglAPIClient(api_token=api_token)
        
        # Test 1: Get current user
        print("👤 Testing user authentication...")
        user = await client.get_current_user()
        print(f"✅ Authenticated as: {user.fullname} ({user.email})")
        print(f"   Default workspace: {user.default_workspace_id}")
        print(f"   Timezone: {user.timezone}\n")
        
        # Test 2: Get workspaces
        print("🏢 Testing workspace access...")
        workspaces = await client.get_workspaces()
        print(f"✅ Found {len(workspaces)} workspace(s):")
        for ws in workspaces:
            print(f"   - {ws.name} (ID: {ws.id}, Admin: {ws.admin})")
        print()
        
        # Test 3: Get projects
        print("📂 Testing project access...")
        projects = await client.get_projects()
        print(f"✅ Found {len(projects)} project(s):")
        active_projects = [p for p in projects if p.active]
        for project in active_projects[:5]:  # Show first 5 active projects
            billable_status = "billable" if project.billable else "non-billable"
            print(f"   - {project.name} ({billable_status})")
        if len(active_projects) > 5:
            print(f"   ... and {len(active_projects) - 5} more active projects")
        print()
        
        # Test 4: Get clients
        print("👥 Testing client access...")
        clients = await client.get_clients()
        print(f"✅ Found {len(clients)} client(s):")
        for client_obj in clients[:5]:  # Show first 5 clients
            print(f"   - {client_obj.name}")
        if len(clients) > 5:
            print(f"   ... and {len(clients) - 5} more clients")
        print()
        
        # Test 5: Get current time entry
        print("⏱️  Testing current time entry...")
        current_entry = await client.get_current_time_entry()
        if current_entry:
            duration = client.calculate_duration(current_entry)
            duration_formatted = client.format_duration(duration)
            print(f"✅ Timer is running: '{current_entry.description}'")
            print(f"   Duration: {duration_formatted}")
            print(f"   Project ID: {current_entry.project_id or 'No project'}")
            print(f"   Billable: {current_entry.billable}")
        else:
            print("⏸️  No timer currently running")
        print()
        
        # Test 6: Get recent time entries
        print("📝 Testing time entries access...")
        # Get entries from last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        entries = await client.get_time_entries(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        print(f"✅ Found {len(entries)} time entries in the last 7 days:")
        
        total_duration = 0
        billable_duration = 0
        for entry in entries[:3]:  # Show first 3 entries
            duration = client.calculate_duration(entry)
            duration_formatted = client.format_duration(duration)
            total_duration += duration
            if entry.billable:
                billable_duration += duration
            
            status = "running" if entry.duration < 0 else "completed"
            billable_status = "billable" if entry.billable else "non-billable"
            print(f"   - '{entry.description}' ({duration_formatted}, {billable_status}, {status})")
        
        if len(entries) > 3:
            print(f"   ... and {len(entries) - 3} more entries")
        
        if entries:
            total_formatted = client.format_duration(total_duration)
            billable_formatted = client.format_duration(billable_duration)
            print(f"   Total time: {total_formatted} ({billable_formatted} billable)")
        print()
        
        # Test 7: Get tags
        print("🏷️  Testing tags access...")
        tags = await client.get_tags()
        print(f"✅ Found {len(tags)} tag(s):")
        for tag in tags[:10]:  # Show first 10 tags
            print(f"   - {tag.name}")
        if len(tags) > 10:
            print(f"   ... and {len(tags) - 10} more tags")
        print()
        
        # Test 8: Rate limiting
        print("🚦 Testing rate limiting...")
        start_time = datetime.now()
        for i in range(3):
            await client.get_current_user()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ Made 3 requests in {duration:.2f} seconds (rate limiting working)")
        print()
        
        print("🎉 All tests passed! Toggl Track MCP server should work correctly.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e .")
        print("2. Run the server: python -m uvicorn toggl_track_mcp.server:app --reload")
        print("3. Test MCP endpoints at http://localhost:8000/mcp")
        
        return True
        
    except TogglAPIError as e:
        print(f"❌ Toggl API Error: {e}")
        if e.status_code == 401:
            print("\n💡 Authentication failed. Please check:")
            print("   - Your TOGGL_API_TOKEN in the .env file")
            print("   - That the token is copied correctly from your Toggl profile")
            print("   - Go to https://track.toggl.com/profile to get your API token")
        elif e.status_code == 403:
            print("\n💡 Permission denied. Please check:")
            print("   - Your Toggl account has the necessary permissions")
            print("   - You have access to the workspace")
        elif e.status_code == 402:
            print("\n💡 Payment required. Please check:")
            print("   - Your Toggl subscription status")
            print("   - API access may require a paid plan")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("\n💡 This might be a network issue or configuration problem.")
        print("Please check:")
        print("   - Your internet connection")
        print("   - That you can access https://api.track.toggl.com")
        print("   - Your .env file configuration")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)