import { z } from 'zod';
import { TogglConfig } from './types/toggl.js';

const ConfigSchema = z.object({
  TOGGL_API_TOKEN: z.string().min(1, 'Toggl API token is required'),
  TOGGL_WORKSPACE_ID: z.string().optional().transform((val) => val ? parseInt(val, 10) : undefined),
  TOGGL_BASE_URL: z.string().url().default('https://api.track.toggl.com/api/v9'),
  MCP_SERVER_NAME: z.string().default('toggl-track-mcp'),
  MCP_SERVER_VERSION: z.string().default('0.1.0'),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

export function loadConfig(): TogglConfig & { 
  serverName: string; 
  serverVersion: string; 
  logLevel: string; 
} {
  try {
    const env = ConfigSchema.parse(process.env);
    
    return {
      apiToken: env.TOGGL_API_TOKEN,
      workspaceId: env.TOGGL_WORKSPACE_ID,
      baseUrl: env.TOGGL_BASE_URL,
      rateLimit: {
        requestsPerSecond: 1,
        burstSize: 3,
      },
      serverName: env.MCP_SERVER_NAME,
      serverVersion: env.MCP_SERVER_VERSION,
      logLevel: env.LOG_LEVEL,
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const messages = error.errors.map(err => `${err.path.join('.')}: ${err.message}`);
      throw new Error(`Configuration error:\n${messages.join('\n')}`);
    }
    throw error;
  }
}

export function validateConfig(): void {
  loadConfig();
}