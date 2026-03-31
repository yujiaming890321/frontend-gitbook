/**
 * Day 3: MCP Server — Search Docs Tool
 *
 * A practical MCP server that searches markdown files by keyword.
 * This is a real-world use case: let AI search your documentation.
 *
 * Key concepts:
 * - File system operations in MCP tools
 * - Returning structured search results
 * - Error handling in tools
 * - Using glob to find files
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as fs from "node:fs";
import * as path from "node:path";
import { glob } from "glob";

// ============================================================
// 1. Types
// ============================================================

interface SearchResult {
  file: string;
  line: number;
  content: string;
}

interface SearchSummary {
  keyword: string;
  docsRoot: string;
  totalFiles: number;
  matchingFiles: number;
  totalMatches: number;
  results: SearchResult[];
}

// ============================================================
// 2. Helper: search markdown files for a keyword
// ============================================================

/**
 * Search all markdown files under a root directory for lines containing the keyword.
 * Returns a structured summary with file paths, line numbers, and matching lines.
 */
async function searchMarkdownFiles(
  docsRoot: string,
  keyword: string,
  maxResults: number = 20
): Promise<SearchSummary> {
  // Find all .md files recursively
  const pattern = path.join(docsRoot, "**/*.md");
  const files = await glob(pattern, { nodir: true });

  const results: SearchResult[] = [];
  let matchingFiles = 0;
  const lowerKeyword = keyword.toLowerCase();

  for (const filePath of files) {
    // Stop early if we have enough results
    if (results.length >= maxResults) break;

    try {
      const content = fs.readFileSync(filePath, "utf-8");
      const lines = content.split("\n");
      let fileHasMatch = false;

      for (let i = 0; i < lines.length; i++) {
        if (results.length >= maxResults) break;

        if (lines[i].toLowerCase().includes(lowerKeyword)) {
          if (!fileHasMatch) {
            matchingFiles++;
            fileHasMatch = true;
          }

          results.push({
            // Show relative path for readability
            file: path.relative(docsRoot, filePath),
            line: i + 1,
            content: lines[i].trim(),
          });
        }
      }
    } catch {
      // Skip files that can't be read
      continue;
    }
  }

  return {
    keyword,
    docsRoot,
    totalFiles: files.length,
    matchingFiles,
    totalMatches: results.length,
    results,
  };
}

// ============================================================
// 3. Create MCP Server
// ============================================================

const server = new McpServer({
  name: "search-docs-server",
  version: "0.1.0",
});

// ============================================================
// 4. Register search_docs tool
// ============================================================

server.tool(
  "search_docs",
  "Search markdown documentation files for a keyword. Returns matching lines with file paths and line numbers.",
  {
    keyword: z
      .string()
      .min(1)
      .describe("The keyword or phrase to search for (case-insensitive)"),
    docs_root: z
      .string()
      .optional()
      .describe(
        "Root directory to search in. Defaults to current working directory."
      ),
    max_results: z
      .number()
      .min(1)
      .max(50)
      .optional()
      .describe("Maximum number of results to return (default: 20, max: 50)"),
  },
  async ({ keyword, docs_root, max_results }) => {
    const root = docs_root || process.cwd();
    const limit = max_results || 20;

    // Validate directory exists
    if (!fs.existsSync(root)) {
      return {
        content: [
          {
            type: "text" as const,
            text: `Error: Directory not found: ${root}`,
          },
        ],
        isError: true,
      };
    }

    try {
      const summary = await searchMarkdownFiles(root, keyword, limit);

      // Format results as readable text
      const lines: string[] = [
        `Search results for "${keyword}" in ${root}`,
        `Found ${summary.totalMatches} matches in ${summary.matchingFiles}/${summary.totalFiles} files`,
        "",
      ];

      for (const result of summary.results) {
        lines.push(`  ${result.file}:${result.line}`);
        lines.push(`    ${result.content}`);
        lines.push("");
      }

      if (summary.totalMatches === 0) {
        lines.push("No matches found. Try a different keyword.");
      }

      return {
        content: [
          {
            type: "text" as const,
            text: lines.join("\n"),
          },
        ],
      };
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown error occurred";
      return {
        content: [
          {
            type: "text" as const,
            text: `Error searching docs: ${message}`,
          },
        ],
        isError: true,
      };
    }
  }
);

// ============================================================
// 5. Register list_docs tool — complementary to search
// ============================================================

server.tool(
  "list_docs",
  "List all markdown documentation files in a directory. Useful to see what docs are available before searching.",
  {
    docs_root: z
      .string()
      .optional()
      .describe(
        "Root directory to list. Defaults to current working directory."
      ),
  },
  async ({ docs_root }) => {
    const root = docs_root || process.cwd();

    if (!fs.existsSync(root)) {
      return {
        content: [
          {
            type: "text" as const,
            text: `Error: Directory not found: ${root}`,
          },
        ],
        isError: true,
      };
    }

    try {
      const pattern = path.join(root, "**/*.md");
      const files = await glob(pattern, { nodir: true });
      const relativePaths = files
        .map((f) => path.relative(root, f))
        .sort();

      const text = [
        `Documentation files in ${root}`,
        `Total: ${files.length} files`,
        "",
        ...relativePaths.map((f) => `  ${f}`),
      ].join("\n");

      return {
        content: [{ type: "text" as const, text }],
      };
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown error occurred";
      return {
        content: [
          {
            type: "text" as const,
            text: `Error listing docs: ${message}`,
          },
        ],
        isError: true,
      };
    }
  }
);

// ============================================================
// 6. Start server
// ============================================================

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Search Docs MCP Server is running on stdio");
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
// 2. Add to Claude Code:
//    claude mcp add search-docs node /path/to/dist/index.js
//
// 3. Ask Claude:
//    "Search for 'MCP' in my docs"
//    "List all documentation files"
//
// TODO: Add a "search_by_heading" tool that only searches # headings
// TODO: Add a "count_words" tool that counts words in a specific doc
// ============================================================
