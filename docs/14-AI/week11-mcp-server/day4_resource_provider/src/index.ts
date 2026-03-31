/**
 * Day 4: MCP Server — Resource Provider
 *
 * Add MCP Resources to let AI browse and read documentation.
 * Resources are like GET endpoints: they expose data for AI to read.
 *
 * Key concepts:
 * - resource(): register a static resource with a fixed URI
 * - resource() with template: register dynamic resources using URI templates
 * - Resources are read-only, no side effects
 * - URI schemes: we use "docs://" for our documentation
 */

import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as fs from "node:fs";
import * as path from "node:path";
import { glob } from "glob";

// ============================================================
// 1. Configuration
// ============================================================

/**
 * Resolve the docs root directory from an environment variable or fall back to cwd.
 * Users can set DOCS_ROOT when starting the server to point at their docs directory.
 */
const DOCS_ROOT = process.env.DOCS_ROOT || process.cwd();

// ============================================================
// 2. Helper functions
// ============================================================

/** Get all markdown files under the docs root directory */
async function getDocFiles(): Promise<string[]> {
  const pattern = path.join(DOCS_ROOT, "**/*.md");
  const files = await glob(pattern, { nodir: true });
  return files.map((f) => path.relative(DOCS_ROOT, f)).sort();
}

/** Read a document file by its relative path and return its content */
function readDocFile(relativePath: string): string | null {
  const fullPath = path.join(DOCS_ROOT, relativePath);

  // Prevent path traversal attacks
  const resolved = path.resolve(fullPath);
  if (!resolved.startsWith(path.resolve(DOCS_ROOT))) {
    return null;
  }

  if (!fs.existsSync(resolved)) {
    return null;
  }

  return fs.readFileSync(resolved, "utf-8");
}

/** Extract the first heading and first paragraph from a markdown file as a summary */
function extractSummary(content: string): string {
  const lines = content.split("\n");
  const heading = lines.find((l) => l.startsWith("# "));
  const firstParagraph = lines.find(
    (l) => l.trim() !== "" && !l.startsWith("#")
  );

  const parts: string[] = [];
  if (heading) parts.push(heading.replace(/^#\s+/, ""));
  if (firstParagraph) parts.push(firstParagraph.trim());
  return parts.join(" — ") || "No summary available";
}

// ============================================================
// 3. Create MCP Server
// ============================================================

const server = new McpServer({
  name: "docs-resource-server",
  version: "0.1.0",
});

// ============================================================
// 4. Register Static Resource: docs table of contents
//
// Static resources have a fixed URI, similar to a hardcoded API endpoint.
// This one returns a list of all available documents.
// ============================================================

server.resource(
  "docs-toc",
  "docs://toc",
  {
    description: "Table of contents — lists all available documentation files",
    mimeType: "text/plain",
  },
  async () => {
    const files = await getDocFiles();

    const content = [
      `Documentation Table of Contents`,
      `Root: ${DOCS_ROOT}`,
      `Total files: ${files.length}`,
      "",
      ...files.map((f) => {
        const fullContent = readDocFile(f);
        const summary = fullContent ? extractSummary(fullContent) : "";
        return `  ${f}${summary ? ` — ${summary}` : ""}`;
      }),
    ].join("\n");

    return {
      contents: [
        {
          uri: "docs://toc",
          mimeType: "text/plain",
          text: content,
        },
      ],
    };
  }
);

// ============================================================
// 5. Register Dynamic Resource: read a specific document
//
// Dynamic resources use URI templates with placeholders.
// The {+path} syntax means "match the rest of the URI" (including slashes).
// This lets AI read any specific document by its path.
// ============================================================

server.resource(
  "doc-file",
  new ResourceTemplate("docs://files/{+path}", {
    list: async () => {
      // List all available documents so AI knows what's available
      const files = await getDocFiles();
      return files.map((f) => ({
        uri: `docs://files/${f}`,
        name: f,
        description: extractSummary(readDocFile(f) || ""),
        mimeType: "text/markdown",
      }));
    },
  }),
  {
    description: "Read the content of a specific documentation file by path",
    mimeType: "text/markdown",
  },
  async (uri, { path: docPath }) => {
    const filePath = Array.isArray(docPath) ? docPath.join("/") : docPath;
    const content = readDocFile(filePath);

    if (content === null) {
      return {
        contents: [
          {
            uri: uri.href,
            mimeType: "text/plain",
            text: `Error: Document not found: ${filePath}`,
          },
        ],
      };
    }

    return {
      contents: [
        {
          uri: uri.href,
          mimeType: "text/markdown",
          text: content,
        },
      ],
    };
  }
);

// ============================================================
// 6. Register search_docs tool (from Day 3, for completeness)
// A server can have both Tools and Resources
// ============================================================

server.tool(
  "search_docs",
  "Search documentation files for a keyword. Returns matching lines with file paths and line numbers.",
  {
    keyword: z
      .string()
      .min(1)
      .describe("The keyword to search for (case-insensitive)"),
    max_results: z
      .number()
      .min(1)
      .max(50)
      .optional()
      .describe("Maximum number of results (default: 20)"),
  },
  async ({ keyword, max_results }) => {
    const limit = max_results || 20;
    const files = await getDocFiles();
    const lowerKeyword = keyword.toLowerCase();

    const results: Array<{ file: string; line: number; content: string }> = [];
    let matchingFiles = 0;

    for (const relativePath of files) {
      if (results.length >= limit) break;

      const content = readDocFile(relativePath);
      if (!content) continue;

      const lines = content.split("\n");
      let fileHasMatch = false;

      for (let i = 0; i < lines.length; i++) {
        if (results.length >= limit) break;
        if (lines[i].toLowerCase().includes(lowerKeyword)) {
          if (!fileHasMatch) {
            matchingFiles++;
            fileHasMatch = true;
          }
          results.push({
            file: relativePath,
            line: i + 1,
            content: lines[i].trim(),
          });
        }
      }
    }

    const output = [
      `Search: "${keyword}" — ${results.length} matches in ${matchingFiles}/${files.length} files`,
      "",
      ...results.map((r) => `  ${r.file}:${r.line}  ${r.content}`),
    ];

    if (results.length === 0) {
      output.push("No matches found.");
    }

    return {
      content: [{ type: "text" as const, text: output.join("\n") }],
    };
  }
);

// ============================================================
// 7. Start server
// ============================================================

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`Docs Resource Server running on stdio (root: ${DOCS_ROOT})`);
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});

// ============================================================
// How to test:
//
// 1. Build:
//    npm run build
//
// 2. Add to Claude Code with DOCS_ROOT:
//    claude mcp add docs-server -e DOCS_ROOT=/path/to/your/docs -- node /path/to/dist/index.js
//
// 3. Ask Claude:
//    "Read the table of contents from docs"
//    "Show me the content of README.md"
//    "Search for 'MCP' in the docs"
//
// TODO: Add a resource for "docs://stats" that returns word count, file count, etc.
// TODO: Add a resource template "docs://headings/{+path}" that returns only headings from a file
// ============================================================
