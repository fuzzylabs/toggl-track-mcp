import { TogglClient } from '../toggl-client.js';
import { createToolResult, createErrorResult, MCPToolDefinition } from '../types/mcp.js';

export class TogglTools {
  constructor(private client: TogglClient) {}

  getToolDefinitions(): MCPToolDefinition[] {
    return [
      {
        name: 'get_current_user',
        description: 'Get current user profile and session information',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'get_current_time_entry',
        description: 'Get currently running time entry (if any)',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'list_time_entries',
        description: 'Get time entries with optional date range filtering',
        inputSchema: {
          type: 'object',
          properties: {
            start_date: {
              type: 'string',
              description: 'Start date in YYYY-MM-DD format',
            },
            end_date: {
              type: 'string',
              description: 'End date in YYYY-MM-DD format',
            },
            project_id: {
              type: 'number',
              description: 'Filter by project ID',
            },
            billable: {
              type: 'boolean',
              description: 'Filter by billable status',
            },
            description: {
              type: 'string',
              description: 'Filter by description containing text',
            },
            tags: {
              type: 'array',
              items: { type: 'string' },
              description: 'Filter by tags',
            },
          },
        },
      },
      {
        name: 'get_time_entry_details',
        description: 'Get detailed information about a specific time entry',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'number',
              description: 'Time entry ID',
            },
          },
          required: ['id'],
        },
      },
      {
        name: 'list_projects',
        description: 'Get all projects for current workspace',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'list_clients',
        description: 'Get all clients',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'list_workspaces',
        description: 'Get available workspaces',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'list_tags',
        description: 'Get all available tags',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'search_time_entries',
        description: 'Search time entries by description, project, client, or tags',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query for description or tags',
            },
            start_date: {
              type: 'string',
              description: 'Start date in YYYY-MM-DD format',
            },
            end_date: {
              type: 'string',
              description: 'End date in YYYY-MM-DD format',
            },
            project_id: {
              type: 'number',
              description: 'Filter by project ID',
            },
            billable: {
              type: 'boolean',
              description: 'Filter by billable status',
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'get_time_summary',
        description: 'Calculate total time for a given period, project, or client',
        inputSchema: {
          type: 'object',
          properties: {
            start_date: {
              type: 'string',
              description: 'Start date in YYYY-MM-DD format',
            },
            end_date: {
              type: 'string',
              description: 'End date in YYYY-MM-DD format',
            },
            project_id: {
              type: 'number',
              description: 'Filter by project ID',
            },
            client_id: {
              type: 'number',
              description: 'Filter by client ID',
            },
            billable: {
              type: 'boolean',
              description: 'Filter by billable status',
            },
            tags: {
              type: 'array',
              items: { type: 'string' },
              description: 'Filter by tags',
            },
          },
        },
      },
    ];
  }

  async executeTool(name: string, args: Record<string, any> = {}) {
    try {
      switch (name) {
        case 'get_current_user':
          return await this.getCurrentUser();
        case 'get_current_time_entry':
          return await this.getCurrentTimeEntry();
        case 'list_time_entries':
          return await this.listTimeEntries(args);
        case 'get_time_entry_details':
          return await this.getTimeEntryDetails(args);
        case 'list_projects':
          return await this.listProjects();
        case 'list_clients':
          return await this.listClients();
        case 'list_workspaces':
          return await this.listWorkspaces();
        case 'list_tags':
          return await this.listTags();
        case 'search_time_entries':
          return await this.searchTimeEntries(args);
        case 'get_time_summary':
          return await this.getTimeSummary(args);
        default:
          return createErrorResult(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return createErrorResult(error);
    }
  }

  private async getCurrentUser() {
    const user = await this.client.getCurrentUser();
    return createToolResult(user);
  }

  private async getCurrentTimeEntry() {
    const timeEntry = await this.client.getCurrentTimeEntry();
    if (!timeEntry) {
      return createToolResult({ message: 'No time entry is currently running' });
    }
    
    const duration = timeEntry.duration < 0 
      ? Math.abs(Date.now() / 1000 + timeEntry.duration)
      : timeEntry.duration;
    
    return createToolResult({
      ...timeEntry,
      calculated_duration: duration,
      calculated_hours: duration / 3600,
      is_running: timeEntry.duration < 0,
    });
  }

  private async listTimeEntries(args: Record<string, any>) {
    const filters = {
      startDate: args.start_date,
      endDate: args.end_date,
      projectId: args.project_id,
      billable: args.billable,
      description: args.description,
      tags: args.tags,
    };
    
    const timeEntries = await this.client.getTimeEntries(filters);
    const enrichedEntries = timeEntries.map(entry => ({
      ...entry,
      calculated_duration: entry.duration < 0 
        ? Math.abs(Date.now() / 1000 + entry.duration)
        : entry.duration,
      calculated_hours: (entry.duration < 0 
        ? Math.abs(Date.now() / 1000 + entry.duration)
        : entry.duration) / 3600,
      is_running: entry.duration < 0,
    }));
    
    return createToolResult({
      time_entries: enrichedEntries,
      total_count: enrichedEntries.length,
    });
  }

  private async getTimeEntryDetails(args: Record<string, any>) {
    if (!args.id) {
      return createErrorResult('Time entry ID is required');
    }
    
    const timeEntry = await this.client.getTimeEntry(args.id);
    const duration = timeEntry.duration < 0 
      ? Math.abs(Date.now() / 1000 + timeEntry.duration)
      : timeEntry.duration;
    
    return createToolResult({
      ...timeEntry,
      calculated_duration: duration,
      calculated_hours: duration / 3600,
      is_running: timeEntry.duration < 0,
    });
  }

  private async listProjects() {
    const projects = await this.client.getProjects();
    return createToolResult({
      projects,
      total_count: projects.length,
    });
  }

  private async listClients() {
    const clients = await this.client.getClients();
    return createToolResult({
      clients,
      total_count: clients.length,
    });
  }

  private async listWorkspaces() {
    const workspaces = await this.client.getWorkspaces();
    return createToolResult({
      workspaces,
      total_count: workspaces.length,
    });
  }

  private async listTags() {
    const tags = await this.client.getTags();
    return createToolResult({
      tags,
      total_count: tags.length,
    });
  }

  private async searchTimeEntries(args: Record<string, any>) {
    if (!args.query) {
      return createErrorResult('Search query is required');
    }
    
    const filters = {
      startDate: args.start_date,
      endDate: args.end_date,
      projectId: args.project_id,
      billable: args.billable,
    };
    
    const timeEntries = await this.client.searchTimeEntries(args.query, filters);
    const enrichedEntries = timeEntries.map(entry => ({
      ...entry,
      calculated_duration: entry.duration < 0 
        ? Math.abs(Date.now() / 1000 + entry.duration)
        : entry.duration,
      calculated_hours: (entry.duration < 0 
        ? Math.abs(Date.now() / 1000 + entry.duration)
        : entry.duration) / 3600,
      is_running: entry.duration < 0,
    }));
    
    return createToolResult({
      query: args.query,
      time_entries: enrichedEntries,
      total_count: enrichedEntries.length,
    });
  }

  private async getTimeSummary(args: Record<string, any>) {
    const filters = {
      startDate: args.start_date,
      endDate: args.end_date,
      projectId: args.project_id,
      clientId: args.client_id,
      billable: args.billable,
      tags: args.tags,
    };
    
    const summary = await this.client.getTimeSummary(filters);
    return createToolResult(summary);
  }
}