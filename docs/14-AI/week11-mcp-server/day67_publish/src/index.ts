#!/usr/bin/env node

/**
 * Day 6-7: Complete MCP Server — Gitbook Documentation Server
 *
 * A production-ready MCP server that combines everything from the week:
 * - Tools: search_docs, list_docs, get_doc_stats
 * - Resources: docs://toc, docs://files/{path}
 * - Prompts: review_doc, summarize_doc
 *
 * This server is ready to be published to npm.
 */

import {
  McpServer,
  ResourceTemplate,
} from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as fs from "node:fs";
import * as path from "node:path";
import { glob } from "glob";

// ============================================================
// 1. Configuration
// ============================================================

const DOCS_ROOT = process.env.DOCS_ROOT || process.cwd();
const SERVER_NAME = "mcp-gitbook-server";
const SERVER_VERSION = "1.0.0";

// ============================================================
// 2. Shared helper functions
// ============================================================

/** Get all markdown files under the docs root directory */
async function getDocFiles(): Promise<string[]> {
  const pattern = path.join(DOCS_ROOT, "**/*.md");
  const files = await glob(pattern, { nodir: true });
  return files.map((f) => path.relative(DOCS_ROOT, f)).sort();
}

/**
 * Read a document file by its relative path.
 * Returns null if the file doesn't exist or the path is invalid.
 * Validates against path traversal attacks.
 */
function readDocFile(relativePath: string): string | null {
  const fullPath = path.join(DOCS_ROOT, relativePath);
  const resolved = path.resolve(fullPath);

  // Prevent path traversal
  if (!resolved.startsWith(path.resolve(DOCS_ROOT))) {
    return null;
  }

  if (!fs.existsSync(resolved)) {
    return null;
  }

  return fs.readFileSync(resolved, "utf-8");
}

/** Extract the first heading from markdown content */
function extractTitle(content: string): string {
  const heading = content.split("\n").find((l) => l.startsWith("# "));
  return heading ? heading.replace(/^#\s+/, "") : "Untitled";
}

/** Extract a brief summary from markdown content (first heading + first paragraph) */
function extractSummary(content: string): string {
  const lines = content.split("\n");
  const heading = lines.find((l) => l.startsWith("# "));
  const paragraph = lines.find((l) => l.trim() !== "" && !l.startsWith("#"));

  const parts: string[] = [];
  if (heading) parts.push(heading.replace(/^#\s+/, ""));
  if (paragraph) parts.push(paragraph.trim());
  return parts.join(" — ") || "No summary available";
}

/** Count words in a text (handles both CJK and Latin characters) */
function countWords(text: string): number {
  // Count CJK characters individually
  const cjkChars = (text.match(/[\u4e00-\u9fff\u3400-\u4dbf]/g) || []).length;
  // Count Latin words
  const latinWords = text
    .replace(/[\u4e00-\u9fff\u3400-\u4dbf]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 0).length;
  return cjkChars + latinWords;
}

// ============================================================
// 3. Create MCP Server
// ============================================================

const server = new McpServer({
  name: SERVER_NAME,
  version: SERVER_VERSION,
});

// ============================================================
// 4. Tools
// ============================================================

// --- Tool: search_docs ---
server.tool(
  "search_docs",
  "Search documentation files for a keyword. Returns matching lines with file paths and line numbers. Supports case-insensitive search.",
  {
    keyword: z
      .string()
      .min(1)
      .describe("The keyword or phrase to search for (case-insensitive)"),
    max_results: z
      .number()
      .min(1)
      .max(100)
      .optional()
      .describe("Maximum number of matching lines to return (default: 20)"),
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
      output.push("No matches found. Try a different keyword.");
    }

    return {
      content: [{ type: "text" as const, text: output.join("\n") }],
    };
  }
);

// --- Tool: list_docs ---
server.tool(
  "list_docs",
  "List all markdown documentation files with their titles. Useful to discover available documentation before searching or reading.",
  {
    directory: z
      .string()
      .optional()
      .describe(
        "Subdirectory to list (relative to docs root). Lists all docs if omitted."
      ),
  },
  async ({ directory }) => {
    let files = await getDocFiles();

    if (directory) {
      files = files.filter((f) => f.startsWith(directory));
    }

    const entries = files.map((f) => {
      const content = readDocFile(f);
      const title = content ? extractTitle(content) : "?";
      return `  ${f}  (${title})`;
    });

    const text = [
      `Documentation files${directory ? ` in ${directory}` : ""}`,
      `Total: ${files.length} files`,
      "",
      ...entries,
    ].join("\n");

    return {
      content: [{ type: "text" as const, text }],
    };
  }
);

// --- Tool: get_doc_stats ---
server.tool(
  "get_doc_stats",
  "Get statistics about a specific document: word count, line count, heading count, link count.",
  {
    file_path: z
      .string()
      .describe("Relative path to the document file (e.g., 'README.md')"),
  },
  async ({ file_path }) => {
    const content = readDocFile(file_path);

    if (content === null) {
      return {
        content: [
          {
            type: "text" as const,
            text: `Error: Document not found: ${file_path}`,
          },
        ],
        isError: true,
      };
    }

    const lines = content.split("\n");
    const headings = lines.filter((l) => l.startsWith("#"));
    const links = content.match(/\[.*?\]\(.*?\)/g) || [];
    const codeBlocks = content.match(/```/g) || [];

    const stats = [
      `Stats for: ${file_path}`,
      "",
      `  Lines:        ${lines.length}`,
      `  Words:        ${countWords(content)}`,
      `  Characters:   ${content.length}`,
      `  Headings:     ${headings.length}`,
      `  Links:        ${links.length}`,
      `  Code blocks:  ${Math.floor(codeBlocks.length / 2)}`,
      "",
      "Headings:",
      ...headings.map((h) => `  ${h}`),
    ];

    return {
      content: [{ type: "text" as const, text: stats.join("\n") }],
    };
  }
);

// ============================================================
// 5. Resources
// ============================================================

// --- Resource: Table of Contents ---
server.resource(
  "docs-toc",
  "docs://toc",
  {
    description:
      "Table of contents listing all available documentation files with summaries",
    mimeType: "text/plain",
  },
  async () => {
    const files = await getDocFiles();

    const content = [
      `Documentation Table of Contents`,
      `Root: ${DOCS_ROOT}`,
      `Total: ${files.length} files`,
      "",
      ...files.map((f) => {
        const fileContent = readDocFile(f);
        const summary = fileContent ? extractSummary(fileContent) : "";
        return `  ${f}${summary ? `  —  ${summary}` : ""}`;
      }),
    ].join("\n");

    return {
      contents: [{ uri: "docs://toc", mimeType: "text/plain", text: content }],
    };
  }
);

// --- Resource: Individual Document ---
server.resource(
  "doc-file",
  new ResourceTemplate("docs://files/{+path}", {
    list: async () => {
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
    description: "Read the full content of a specific documentation file",
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
        { uri: uri.href, mimeType: "text/markdown", text: content },
      ],
    };
  }
);

// ============================================================
// 6. Prompt Templates
// ============================================================

// --- Prompt: Review Documentation ---
server.prompt(
  "review_doc",
  "Generate a prompt to review a documentation file for quality, accuracy, and completeness.",
  {
    file_path: z
      .string()
      .describe("Relative path to the document to review"),
  },
  async ({ file_path }) => {
    const content = readDocFile(file_path);

    if (content === null) {
      return {
        messages: [
          {
            role: "user" as const,
            content: {
              type: "text" as const,
              text: `Error: Document not found: ${file_path}`,
            },
          },
        ],
      };
    }

    return {
      messages: [
        {
          role: "user" as const,
          content: {
            type: "text" as const,
            text: [
              `Please review the following documentation file: ${file_path}`,
              "",
              "Check for:",
              "1. Clarity: Is the content easy to understand?",
              "2. Completeness: Are there missing sections or explanations?",
              "3. Accuracy: Are code examples correct and up-to-date?",
              "4. Formatting: Is markdown used consistently?",
              "5. Links: Are there broken or missing links?",
              "",
              "Document content:",
              "```markdown",
              content,
              "```",
              "",
              "Provide specific suggestions for improvement.",
            ].join("\n"),
          },
        },
      ],
    };
  }
);

// --- Prompt: Summarize Documentation ---
server.prompt(
  "summarize_doc",
  "Generate a prompt to create a concise summary of a documentation file.",
  {
    file_path: z
      .string()
      .describe("Relative path to the document to summarize"),
    audience: z
      .string()
      .optional()
      .describe(
        "Target audience (e.g., 'beginners', 'senior developers'). Default: general."
      ),
  },
  async ({ file_path, audience }) => {
    const content = readDocFile(file_path);

    if (content === null) {
      return {
        messages: [
          {
            role: "user" as const,
            content: {
              type: "text" as const,
              text: `Error: Document not found: ${file_path}`,
            },
          },
        ],
      };
    }

    const targetAudience = audience || "general developers";

    return {
      messages: [
        {
          role: "user" as const,
          content: {
            type: "text" as const,
            text: [
              `Summarize the following documentation for ${targetAudience}.`,
              "",
              "Requirements:",
              "- Keep it under 200 words",
              "- Highlight the key takeaways",
              "- List any prerequisites mentioned",
              "- Note any action items or next steps",
              "",
              `File: ${file_path}`,
              "",
              "```markdown",
              content,
              "```",
            ].join("\n"),
          },
        },
      ],
    };
  }
);

// ============================================================
// 7. Start server
// ============================================================

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(
    `${SERVER_NAME} v${SERVER_VERSION} running on stdio (root: ${DOCS_ROOT})`
  );
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
