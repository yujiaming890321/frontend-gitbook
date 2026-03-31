# Day 5: MCP Server 测试与调试

> 写完 MCP Server 之后，怎么确认它能正常工作？本节介绍三种测试方式。

## 1. 用 Claude Code 测试 (最直接)

### 添加 MCP Server

```bash
# 语法: claude mcp add <name> <command> [args...]
# 添加 Day 2 的 hello server
claude mcp add hello-server node /absolute/path/to/day2_project_setup/dist/index.js

# 添加 Day 4 的 docs server，带环境变量
claude mcp add docs-server \
  -e DOCS_ROOT=/path/to/your/docs \
  -- node /absolute/path/to/day4_resource_provider/dist/index.js
```

### 管理 MCP Server

```bash
# 查看已添加的 MCP servers
claude mcp list

# 删除一个 server
claude mcp remove hello-server
```

### 测试对话

添加后启动 Claude Code，直接对话测试：

```
你: "Use the hello tool to greet 'MCP Developer'"
AI: 调用 hello tool → "Hello, MCP Developer! Welcome to MCP Server development."

你: "Search my docs for 'TypeScript'"
AI: 调用 search_docs tool → 返回搜索结果

你: "Show me the table of contents of my docs"
AI: 读取 docs://toc resource → 返回文档列表
```

## 2. 用 MCP Inspector 调试 (推荐)

MCP Inspector 是官方提供的可视化调试工具，可以直接在浏览器中测试你的 MCP Server。

### 安装和使用

```bash
# 直接用 npx 运行，不需要安装
npx @modelcontextprotocol/inspector node /path/to/dist/index.js

# 带环境变量
npx @modelcontextprotocol/inspector \
  -e DOCS_ROOT=/path/to/docs \
  node /path/to/dist/index.js
```

### Inspector 功能

```
┌──────────────────────────────────────────────────┐
│  MCP Inspector                          localhost │
│                                                   │
│  ┌─────────┐ ┌───────────┐ ┌──────────┐         │
│  │  Tools  │ │ Resources │ │ Prompts  │         │
│  └────┬────┘ └─────┬─────┘ └────┬─────┘         │
│       │             │            │                │
│  ┌────▼─────────────▼────────────▼──────────┐    │
│  │                                           │    │
│  │  Tool: search_docs                        │    │
│  │  ┌──────────────────────────┐             │    │
│  │  │ keyword: [MCP        ]   │             │    │
│  │  │ max_results: [20     ]   │             │    │
│  │  └──────────────────────────┘             │    │
│  │  [Call Tool]                              │    │
│  │                                           │    │
│  │  Response:                                │    │
│  │  Search: "MCP" — 5 matches in 2/10 files  │    │
│  │    README.md:1  # MCP Server Development  │    │
│  │    ...                                    │    │
│  └───────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

Inspector 的优势：
- 可以看到所有注册的 Tools、Resources、Prompts
- 可以手动填参数并调用
- 实时查看请求/响应的 JSON
- 不需要启动 Claude Code

## 3. 直接用 stdin/stdout 测试 (底层调试)

如果需要看原始 JSON-RPC 通信，可以直接和 MCP Server 交互：

```bash
# 启动 server 并手动发送 JSON-RPC 请求
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | node dist/index.js
```

这种方式一般只在调试协议问题时使用。

## 4. 常见问题与排查

### 问题 1: Server 启动失败

```
症状: claude mcp list 显示 server 状态为 error

排查步骤:
1. 确认 dist/index.js 存在 → 是否忘了 npm run build？
2. 手动运行 node dist/index.js → 看有没有报错
3. 确认路径是绝对路径 → claude mcp add 需要绝对路径
```

### 问题 2: Tool 不出现

```
症状: Claude 说找不到工具

排查步骤:
1. claude mcp list → 确认 server 已添加且状态正常
2. 用 Inspector 检查 → Tools 标签页是否列出了你的工具
3. 检查 tool 的 name 和 description 是否合理
```

### 问题 3: Tool 调用报错

```
症状: Claude 调用工具后返回错误

排查步骤:
1. 检查 console.error 输出（stderr 不影响 MCP 协议）
2. 用 Inspector 手动调用，看返回的 JSON
3. 检查参数校验（zod schema 是否和 AI 传的参数匹配）
```

### 问题 4: 日志在哪看？

```
关键原则: stdout 是给 MCP 协议用的，不能 console.log！

正确做法:
- console.error("debug info")  ← 输出到 stderr，不影响协议
- 写文件日志: fs.appendFileSync('/tmp/mcp-debug.log', message)

常见错误:
- console.log("hello")  ← 会破坏 JSON-RPC 通信！
```

## 5. 调试清单

在测试你的 MCP Server 之前，过一遍这个清单：

```
[ ] npm run build 成功，没有 TypeScript 错误
[ ] dist/index.js 文件存在
[ ] 手动 node dist/index.js 不报错（会挂起等待 stdin，Ctrl+C 退出）
[ ] console.log 全部换成了 console.error
[ ] tool 的 description 清晰描述了用途
[ ] zod schema 的 .describe() 清晰描述了每个参数
[ ] 错误情况有 try/catch 处理
[ ] 路径使用绝对路径
```

## 练习

1. 用 Inspector 测试 Day 2 的 hello server
2. 用 Claude Code 添加 Day 3 的 search server，搜索本项目的文档
3. 故意在 tool handler 里加一个 `console.log("test")`，观察会发生什么
4. 故意让 zod schema 和实际参数不匹配，观察错误提示
