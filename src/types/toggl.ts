import { z } from 'zod';

export const UserSchema = z.object({
  id: z.number(),
  email: z.string(),
  fullname: z.string(),
  timezone: z.string(),
  default_workspace_id: z.number(),
  beginning_of_week: z.number(),
  image_url: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const WorkspaceSchema = z.object({
  id: z.number(),
  name: z.string(),
  profile: z.number(),
  premium: z.boolean(),
  business_ws: z.boolean(),
  admin: z.boolean(),
  suspended_at: z.string().nullable(),
  server_deleted_at: z.string().nullable(),
  default_hourly_rate: z.number().nullable(),
  rate_last_updated: z.string().nullable(),
  default_currency: z.string(),
  only_admins_may_create_projects: z.boolean(),
  only_admins_see_billable_rates: z.boolean(),
  only_admins_see_team_dashboard: z.boolean(),
  projects_billable_by_default: z.boolean(),
  reports_collapse: z.boolean(),
  rounding: z.number(),
  rounding_minutes: z.number(),
  api_token: z.string(),
  at: z.string(),
  logo_url: z.string().nullable(),
  ical_enabled: z.boolean(),
  ical_url: z.string().nullable(),
});

export const ProjectSchema = z.object({
  id: z.number(),
  workspace_id: z.number(),
  client_id: z.number().nullable(),
  name: z.string(),
  is_private: z.boolean(),
  active: z.boolean(),
  at: z.string(),
  created_at: z.string(),
  server_deleted_at: z.string().nullable(),
  color: z.string(),
  billable: z.boolean().nullable(),
  template: z.boolean().nullable(),
  auto_estimates: z.boolean().nullable(),
  estimated_hours: z.number().nullable(),
  rate: z.number().nullable(),
  rate_last_updated: z.string().nullable(),
  currency: z.string().nullable(),
  recurring: z.boolean(),
  recurring_parameters: z.array(z.any()).nullable(),
  current_period: z.any().nullable(),
  fixed_fee: z.number().nullable(),
  actual_hours: z.number().nullable(),
  wid: z.number(),
  cid: z.number().nullable(),
});

export const ClientSchema = z.object({
  id: z.number(),
  workspace_id: z.number(),
  name: z.string(),
  notes: z.string().nullable(),
  at: z.string(),
  server_deleted_at: z.string().nullable(),
  wid: z.number(),
});

export const TimeEntrySchema = z.object({
  id: z.number(),
  workspace_id: z.number(),
  project_id: z.number().nullable(),
  task_id: z.number().nullable(),
  billable: z.boolean(),
  start: z.string(),
  stop: z.string().nullable(),
  duration: z.number(),
  description: z.string(),
  tags: z.array(z.string()).nullable(),
  tag_ids: z.array(z.number()).nullable(),
  duronly: z.boolean(),
  at: z.string(),
  server_deleted_at: z.string().nullable(),
  user_id: z.number(),
  uid: z.number(),
  wid: z.number(),
  pid: z.number().nullable(),
  tid: z.number().nullable(),
});

export const TagSchema = z.object({
  id: z.number(),
  workspace_id: z.number(),
  name: z.string(),
  at: z.string(),
  deleted_at: z.string().nullable(),
  wid: z.number(),
});

export type User = z.infer<typeof UserSchema>;
export type Workspace = z.infer<typeof WorkspaceSchema>;
export type Project = z.infer<typeof ProjectSchema>;
export type Client = z.infer<typeof ClientSchema>;
export type TimeEntry = z.infer<typeof TimeEntrySchema>;
export type Tag = z.infer<typeof TagSchema>;

export interface TogglConfig {
  apiToken: string;
  workspaceId?: number;
  baseUrl: string;
  rateLimit: {
    requestsPerSecond: number;
    burstSize: number;
  };
}

export interface TimeEntryFilters {
  startDate?: string;
  endDate?: string;
  projectId?: number;
  clientId?: number;
  tags?: string[];
  description?: string;
  billable?: boolean;
}

export interface TimeSummary {
  totalDuration: number;
  totalHours: number;
  billableDuration: number;
  billableHours: number;
  entriesCount: number;
  projectBreakdown: Array<{
    projectId: number | null;
    projectName: string | null;
    duration: number;
    hours: number;
    entriesCount: number;
  }>;
  clientBreakdown: Array<{
    clientId: number | null;
    clientName: string | null;
    duration: number;
    hours: number;
    entriesCount: number;
  }>;
  tagBreakdown: Array<{
    tag: string;
    duration: number;
    hours: number;
    entriesCount: number;
  }>;
}

export interface TogglApiError {
  error: string;
  message?: string;
  code?: number;
}