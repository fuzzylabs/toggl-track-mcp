import {
  User,
  Workspace,
  Project,
  Client,
  TimeEntry,
  Tag,
  TogglConfig,
  TimeEntryFilters,
  TimeSummary,
  TogglApiError,
  UserSchema,
  WorkspaceSchema,
  ProjectSchema,
  ClientSchema,
  TimeEntrySchema,
  TagSchema,
} from './types/toggl.js';
import { RateLimiter } from './utils/rate-limiter.js';

export class TogglClient {
  private readonly config: TogglConfig;
  private readonly rateLimiter: RateLimiter;

  constructor(config: TogglConfig) {
    this.config = config;
    this.rateLimiter = new RateLimiter(
      config.rateLimit.requestsPerSecond,
      config.rateLimit.burstSize
    );
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    await this.rateLimiter.waitForToken();

    const url = `${this.config.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${Buffer.from(`${this.config.apiToken}:api_token`).toString('base64')}`,
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        if (response.status === 429) {
          const retryAfter = response.headers.get('retry-after');
          const delay = retryAfter ? parseInt(retryAfter, 10) * 1000 : 2000;
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.makeRequest<T>(endpoint, options);
        }

        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorBody = await response.json() as TogglApiError;
          errorMessage = errorBody.message || errorBody.error || errorMessage;
        } catch {
          // Ignore JSON parsing errors for error responses
        }

        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error(`Request failed: ${String(error)}`);
    }
  }

  async getCurrentUser(): Promise<User> {
    const data = await this.makeRequest<User>('/me');
    return UserSchema.parse(data);
  }

  async getCurrentTimeEntry(): Promise<TimeEntry | null> {
    try {
      const data = await this.makeRequest<TimeEntry>('/me/time_entries/current');
      return data ? TimeEntrySchema.parse(data) : null;
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async getTimeEntries(filters: TimeEntryFilters = {}): Promise<TimeEntry[]> {
    let endpoint = '/me/time_entries';
    const params = new URLSearchParams();

    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);

    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }

    const data = await this.makeRequest<TimeEntry[]>(endpoint);
    const timeEntries = data.map(entry => TimeEntrySchema.parse(entry));

    return this.filterTimeEntries(timeEntries, filters);
  }

  async getTimeEntry(id: number): Promise<TimeEntry> {
    const data = await this.makeRequest<TimeEntry>(`/me/time_entries/${id}`);
    return TimeEntrySchema.parse(data);
  }

  async getProjects(): Promise<Project[]> {
    const user = await this.getCurrentUser();
    const workspaceId = this.config.workspaceId || user.default_workspace_id;
    
    const data = await this.makeRequest<Project[]>(`/workspaces/${workspaceId}/projects`);
    return data.map(project => ProjectSchema.parse(project));
  }

  async getClients(): Promise<Client[]> {
    const user = await this.getCurrentUser();
    const workspaceId = this.config.workspaceId || user.default_workspace_id;
    
    const data = await this.makeRequest<Client[]>(`/workspaces/${workspaceId}/clients`);
    return data.map(client => ClientSchema.parse(client));
  }

  async getWorkspaces(): Promise<Workspace[]> {
    const data = await this.makeRequest<Workspace[]>('/me/workspaces');
    return data.map(workspace => WorkspaceSchema.parse(workspace));
  }

  async getTags(): Promise<Tag[]> {
    const user = await this.getCurrentUser();
    const workspaceId = this.config.workspaceId || user.default_workspace_id;
    
    const data = await this.makeRequest<Tag[]>(`/workspaces/${workspaceId}/tags`);
    return data.map(tag => TagSchema.parse(tag));
  }

  async searchTimeEntries(query: string, filters: TimeEntryFilters = {}): Promise<TimeEntry[]> {
    const timeEntries = await this.getTimeEntries(filters);
    
    return timeEntries.filter(entry => {
      const searchText = query.toLowerCase();
      return (
        entry.description.toLowerCase().includes(searchText) ||
        (entry.tags && entry.tags.some(tag => tag.toLowerCase().includes(searchText)))
      );
    });
  }

  async getTimeSummary(filters: TimeEntryFilters = {}): Promise<TimeSummary> {
    const [timeEntries, projects, clients] = await Promise.all([
      this.getTimeEntries(filters),
      this.getProjects(),
      this.getClients(),
    ]);

    const projectMap = new Map(projects.map(p => [p.id, p]));
    const clientMap = new Map(clients.map(c => [c.id, c]));

    let totalDuration = 0;
    let billableDuration = 0;
    const projectBreakdown = new Map<number | null, { duration: number; count: number }>();
    const clientBreakdown = new Map<number | null, { duration: number; count: number }>();
    const tagBreakdown = new Map<string, { duration: number; count: number }>();

    for (const entry of timeEntries) {
      const duration = this.calculateDuration(entry);
      totalDuration += duration;
      
      if (entry.billable) {
        billableDuration += duration;
      }

      const projectId = entry.project_id;
      if (!projectBreakdown.has(projectId)) {
        projectBreakdown.set(projectId, { duration: 0, count: 0 });
      }
      const projectData = projectBreakdown.get(projectId)!;
      projectData.duration += duration;
      projectData.count++;

      const project = projectId ? projectMap.get(projectId) : null;
      const clientId = project?.client_id ?? null;
      if (!clientBreakdown.has(clientId)) {
        clientBreakdown.set(clientId, { duration: 0, count: 0 });
      }
      const clientData = clientBreakdown.get(clientId)!;
      clientData.duration += duration;
      clientData.count++;

      if (entry.tags) {
        for (const tag of entry.tags) {
          if (!tagBreakdown.has(tag)) {
            tagBreakdown.set(tag, { duration: 0, count: 0 });
          }
          const tagData = tagBreakdown.get(tag)!;
          tagData.duration += duration;
          tagData.count++;
        }
      }
    }

    return {
      totalDuration,
      totalHours: totalDuration / 3600,
      billableDuration,
      billableHours: billableDuration / 3600,
      entriesCount: timeEntries.length,
      projectBreakdown: Array.from(projectBreakdown.entries()).map(([projectId, data]) => {
        const project = projectId ? projectMap.get(projectId) : null;
        return {
          projectId,
          projectName: project?.name ?? 'No Project',
          duration: data.duration,
          hours: data.duration / 3600,
          entriesCount: data.count,
        };
      }),
      clientBreakdown: Array.from(clientBreakdown.entries()).map(([clientId, data]) => {
        const client = clientId ? clientMap.get(clientId) : null;
        return {
          clientId,
          clientName: client?.name ?? 'No Client',
          duration: data.duration,
          hours: data.duration / 3600,
          entriesCount: data.count,
        };
      }),
      tagBreakdown: Array.from(tagBreakdown.entries()).map(([tag, data]) => ({
        tag,
        duration: data.duration,
        hours: data.duration / 3600,
        entriesCount: data.count,
      })),
    };
  }

  private filterTimeEntries(timeEntries: TimeEntry[], filters: TimeEntryFilters): TimeEntry[] {
    return timeEntries.filter(entry => {
      if (filters.projectId !== undefined && entry.project_id !== filters.projectId) {
        return false;
      }
      if (filters.billable !== undefined && entry.billable !== filters.billable) {
        return false;
      }
      if (filters.description && !entry.description.toLowerCase().includes(filters.description.toLowerCase())) {
        return false;
      }
      if (filters.tags && filters.tags.length > 0) {
        if (!entry.tags || !filters.tags.some(tag => entry.tags!.includes(tag))) {
          return false;
        }
      }
      return true;
    });
  }

  private calculateDuration(entry: TimeEntry): number {
    if (entry.duration < 0) {
      return Math.abs(Date.now() / 1000 + entry.duration);
    }
    return entry.duration;
  }
}