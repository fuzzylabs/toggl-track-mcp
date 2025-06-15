import { z } from 'zod';

export const ToolInputSchema = z.object({
  name: z.string(),
  arguments: z.record(z.any()).optional(),
});

export const ToolResultSchema = z.object({
  content: z.array(z.object({
    type: z.literal('text'),
    text: z.string(),
  })),
  isError: z.boolean().optional(),
});

export type ToolInput = z.infer<typeof ToolInputSchema>;
export type ToolResult = z.infer<typeof ToolResultSchema>;

export interface MCPToolDefinition {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required?: string[];
  };
}

export const createToolResult = (data: any, isError = false): ToolResult => ({
  content: [{
    type: 'text',
    text: typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  }],
  isError
});

export const createErrorResult = (error: string | Error): ToolResult => {
  const message = error instanceof Error ? error.message : error;
  return createToolResult(`Error: ${message}`, true);
};