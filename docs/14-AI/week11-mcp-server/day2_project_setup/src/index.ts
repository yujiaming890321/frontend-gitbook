/**
 * Day 2: Minimal MCP Server — Hello Tool
 *
 * This is the simplest possible MCP server.
 * It registers one tool: "hello" that greets the user.
 *
 * Key concepts:
 * - McpServer: the main class that handles MCP protocol
 * - StdioServerTransport: communicates via stdin/stdout
 * - z (zod): validates tool parameters
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// ============================================================
// 1. Create MCP Server instance
// Think of this like: const app = express()
// ============================================================

const server = new McpServer({
  name: "hello-server",
  version: "0.1.0",
});

// ============================================================
// 2. Register a Tool
// Think of this like: app.post('/hello', handler)
// ============================================================

server.tool(
  // Tool name — AI will use this name to call the tool
  "hello",
  // Tool description — AI reads this to decide when to use the tool
  "Greet a user by name. Returns a friendly greeting message.",
  // Parameter schema using zod — validates input automatically
  {
    name: z.string().describe("The name of the person to greet"),
  },
  // Handler function — runs when AI calls this tool
  async ({ name }) => {
    return {
      content: [
        {
          type: "text" as const,
          text: `Hello, ${name}! Welcome to MCP Server development.`,
        },
      ],
    };
  }
);

// ============================================================
// 3. Register another tool with multiple parameters
// ============================================================

server.tool(
  "add_numbers",
  "Add two numbers together and return the result.",
  {
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  },
  async ({ a, b }) => {
    const result = a + b;
    return {
      content: [
        {
          type: "text" as const,
          text: `${a} + ${b} = ${result}`,
        },
      ],
    };
  }
);

// ============================================================
// 4. Start the server with stdio transport
// This connects stdin/stdout to the MCP protocol
// ============================================================

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log to stderr because stdout is used for MCP protocol
  console.error("Hello MCP Server is running on stdio");
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});

// ============================================================
// How to test:
//
// 1. Build and run:
//    npm run build
//    npm start
//
// 2. Add to Claude Code:
//    claude mcp add hello-server node /path/to/dist/index.js
//
// 3. Ask Claude: "Use the hello tool to greet me"
//
// TODO: Add a "current_time" tool that returns the current date and time
// TODO: Add a "reverse_string" tool that reverses any given string
// ============================================================
