import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { TogglClient } from './toggl-client.js';
import { TogglTools } from './tools/index.js';
import { loadConfig } from './config.js';

export class TogglMCPServer {
  private server: Server;
  private client: TogglClient;
  private tools: TogglTools;

  constructor() {
    const config = loadConfig();
    
    this.server = new Server(
      {
        name: config.serverName,
        version: config.serverVersion,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.client = new TogglClient(config);
    this.tools = new TogglTools(this.client);
    
    this.setupHandlers();
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const toolDefinitions = this.tools.getToolDefinitions();
      return {
        tools: toolDefinitions.map(tool => ({
          name: tool.name,
          description: tool.description,
          inputSchema: tool.inputSchema,
        })),
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        const result = await this.tools.executeTool(name, args || {});
        return result;
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return {
          content: [{
            type: 'text',
            text: `Error executing tool ${name}: ${message}`,
          }],
          isError: true,
        };
      }
    });
  }

  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    console.error(`Toggl Track MCP server running on stdio`);
    console.error(`Available tools: ${this.tools.getToolDefinitions().map(t => t.name).join(', ')}`);
  }

  async stop(): Promise<void> {
    await this.server.close();
  }
}