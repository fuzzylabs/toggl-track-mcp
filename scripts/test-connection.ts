#!/usr/bin/env tsx

import 'dotenv/config';
import { TogglClient } from '../src/toggl-client.js';
import { loadConfig } from '../src/config.js';

async function testConnection(): Promise<void> {
  try {
    console.log('Testing Toggl Track API connection...\n');
    
    const config = loadConfig();
    const client = new TogglClient(config);
    
    console.log('🔍 Fetching current user...');
    const user = await client.getCurrentUser();
    console.log(`✅ User: ${user.fullname} (${user.email})`);
    console.log(`   Default Workspace: ${user.default_workspace_id}`);
    console.log(`   Timezone: ${user.timezone}\n`);
    
    console.log('🏢 Fetching workspaces...');
    const workspaces = await client.getWorkspaces();
    console.log(`✅ Found ${workspaces.length} workspace(s):`);
    workspaces.forEach(ws => {
      console.log(`   - ${ws.name} (ID: ${ws.id})`);
    });
    console.log();
    
    console.log('📂 Fetching projects...');
    const projects = await client.getProjects();
    console.log(`✅ Found ${projects.length} project(s):`);
    projects.slice(0, 5).forEach(project => {
      console.log(`   - ${project.name} (ID: ${project.id}, Active: ${project.active})`);
    });
    if (projects.length > 5) {
      console.log(`   ... and ${projects.length - 5} more`);
    }
    console.log();
    
    console.log('👥 Fetching clients...');
    const clients = await client.getClients();
    console.log(`✅ Found ${clients.length} client(s):`);
    clients.slice(0, 5).forEach(client => {
      console.log(`   - ${client.name} (ID: ${client.id})`);
    });
    if (clients.length > 5) {
      console.log(`   ... and ${clients.length - 5} more`);
    }
    console.log();
    
    console.log('🏃 Checking for current time entry...');
    const currentEntry = await client.getCurrentTimeEntry();
    if (currentEntry) {
      const duration = currentEntry.duration < 0 
        ? Math.abs(Date.now() / 1000 + currentEntry.duration)
        : currentEntry.duration;
      console.log(`✅ Timer is running: "${currentEntry.description}"`);
      console.log(`   Duration: ${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`);
      console.log(`   Project: ${currentEntry.project_id || 'No project'}`);
    } else {
      console.log('⏸️  No timer currently running');
    }
    console.log();
    
    console.log('📝 Fetching recent time entries...');
    const entries = await client.getTimeEntries({
      startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    });
    console.log(`✅ Found ${entries.length} time entries in the last 7 days`);
    entries.slice(0, 3).forEach(entry => {
      const duration = entry.duration < 0 
        ? Math.abs(Date.now() / 1000 + entry.duration)
        : entry.duration;
      const hours = Math.floor(duration / 3600);
      const minutes = Math.floor((duration % 3600) / 60);
      console.log(`   - "${entry.description}" (${hours}h ${minutes}m, ${entry.billable ? 'billable' : 'non-billable'})`);
    });
    console.log();
    
    console.log('🎯 Fetching tags...');
    const tags = await client.getTags();
    console.log(`✅ Found ${tags.length} tag(s):`);
    tags.slice(0, 10).forEach(tag => {
      console.log(`   - ${tag.name}`);
    });
    if (tags.length > 10) {
      console.log(`   ... and ${tags.length - 10} more`);
    }
    console.log();
    
    console.log('🎉 Connection test completed successfully!');
    console.log('\nThe Toggl Track MCP server should work correctly with your API token.');
    
  } catch (error) {
    console.error('❌ Connection test failed:');
    console.error(error instanceof Error ? error.message : String(error));
    
    if (error instanceof Error) {
      if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        console.error('\n💡 This looks like an authentication error. Please check:');
        console.error('   - Your TOGGL_API_TOKEN in the .env file');
        console.error('   - That the token is copied correctly from your Toggl profile');
      } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
        console.error('\n💡 This looks like a permissions error. Please check:');
        console.error('   - That your Toggl account has API access');
        console.error('   - Your workspace permissions');
      } else if (error.message.includes('network') || error.message.includes('ENOTFOUND')) {
        console.error('\n💡 This looks like a network error. Please check:');
        console.error('   - Your internet connection');
        console.error('   - That you can access https://api.track.toggl.com');
      }
    }
    
    process.exit(1);
  }
}

testConnection();