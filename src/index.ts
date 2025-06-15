#!/usr/bin/env node

import 'dotenv/config';
import { TogglMCPServer } from './server.js';
import { validateConfig } from './config.js';

async function main(): Promise<void> {
  try {
    validateConfig();
    
    const server = new TogglMCPServer();
    
    const handleShutdown = async (signal: string): Promise<void> => {
      console.error(`\nReceived ${signal}, shutting down gracefully...`);
      await server.stop();
      process.exit(0);
    };

    process.on('SIGINT', () => handleShutdown('SIGINT'));
    process.on('SIGTERM', () => handleShutdown('SIGTERM'));

    await server.start();
  } catch (error) {
    console.error('Failed to start Toggl MCP server:', error);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('Unhandled error:', error);
  process.exit(1);
});