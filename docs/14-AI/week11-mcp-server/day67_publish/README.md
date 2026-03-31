# mcp-gitbook-server

A MCP (Model Context Protocol) server for browsing and searching documentation. Lets AI assistants like Claude search, read, and analyze your markdown documentation.

## Features

- **Tools**: Search docs by keyword, list files, get document stats
- **Resources**: Browse table of contents, read individual documents
- **Prompts**: Review documentation quality, generate summaries

## Installation

```bash
npm install -g mcp-gitbook-server
```

Or use directly with npx:

```bash
npx mcp-gitbook-server
```

## Configuration

### Claude Code

```bash
# Add with default docs root (current directory)
claude mcp add gitbook-server -- npx mcp-gitbook-server

# Add with custom docs root
claude mcp add gitbook-server \
  -e DOCS_ROOT=/path/to/your/docs \
  -- npx mcp-gitbook-server
```

### Claude Desktop (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "gitbook-server": {
      "command": "npx",
      "args": ["mcp-gitbook-server"],
      "env": {
        "DOCS_ROOT": "/path/to/your/docs"
      }
    }
  }
}
```

### Cursor (.cursor/mcp.json)

```json
{
  "mcpServers": {
    "gitbook-server": {
      "command": "npx",
      "args": ["mcp-gitbook-server"],
      "env": {
        "DOCS_ROOT": "/path/to/your/docs"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCS_ROOT` | Root directory for documentation | Current working directory |

## Available Tools

### search_docs

Search documentation files for a keyword (case-insensitive).

```
Parameters:
  keyword (string, required) - The search keyword
  max_results (number, optional) - Max results to return (default: 20)
```

### list_docs

List all markdown files with their titles.

```
Parameters:
  directory (string, optional) - Subdirectory to filter
```

### get_doc_stats

Get statistics about a document (word count, headings, links, etc.).

```
Parameters:
  file_path (string, required) - Relative path to the document
```

## Available Resources

| URI | Description |
|-----|-------------|
| `docs://toc` | Table of contents with all files and summaries |
| `docs://files/{path}` | Read a specific document by path |

## Available Prompts

| Name | Description |
|------|-------------|
| `review_doc` | Review a document for quality and completeness |
| `summarize_doc` | Summarize a document for a target audience |

## Development

```bash
# Clone and install
git clone <repo-url>
cd mcp-gitbook-server
npm install

# Build
npm run build

# Run locally
DOCS_ROOT=/path/to/docs npm start

# Watch mode for development
npm run dev
```

## Publishing to npm

```bash
# 1. Update version in package.json
# 2. Build
npm run build

# 3. Test locally
npx @modelcontextprotocol/inspector node dist/index.js

# 4. Publish
npm publish
```

## License

MIT
