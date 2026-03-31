# Day 1: MCP 核心概念

> MCP (Model Context Protocol) 是 Anthropic 推出的开放协议，让 AI 模型能以标准化方式访问外部工具和数据

## 1. 为什么需要 MCP？

```
传统方式：每个 AI 应用自己实现工具调用，格式各不相同

  App A  ──(自定义格式)──> Tool X
  App B  ──(另一种格式)──> Tool X   ← 同一个工具要适配多次
  App C  ──(又一种格式)──> Tool X

MCP 方式：统一协议，一次实现到处用

  Claude Code ─┐
  Cursor      ─┼──(MCP 协议)──> MCP Server ──> Tool X
  其他 AI 工具 ─┘
```

类比前端：MCP 就像 REST API 之于前后端通信 —— 定义了统一的"接口规范"。

## 2. MCP 架构

```
┌─────────────────────────────────────────────────┐
│                   AI 应用 (Host)                 │
│  ┌───────────────────────────────────────────┐  │
│  │             MCP Client                     │  │
│  │  (内置在 Claude Code / Cursor 等工具中)     │  │
│  └──────────────┬────────────────────────────┘  │
│                 │                                │
│          MCP 协议 (JSON-RPC)                     │
│                 │                                │
│  ┌──────────────▼────────────────────────────┐  │
│  │            MCP Server (你写的)              │  │
│  │                                            │  │
│  │  ┌────────┐ ┌───────────┐ ┌────────────┐  │  │
│  │  │ Tools  │ │ Resources │ │  Prompts   │  │  │
│  │  │ 工具   │ │  资源     │ │  提示模板   │  │  │
│  │  └────────┘ └───────────┘ └────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 角色说明

| 角色 | 说明 | 类比前端 |
|------|------|----------|
| **Host** | 运行 AI 的应用 | 浏览器 |
| **Client** | MCP 协议的客户端 | fetch / axios |
| **Server** | 你开发的，提供能力 | Express / Koa 后端 |

## 3. 三种核心能力

### Tools (工具)

AI 可以调用的函数。最像前端的 API 端点。

```
特点：
- AI 主动调用（需要时才调）
- 有输入参数和返回值
- 适合"做事情"：搜索、计算、调用外部 API

示例：
- search_docs(keyword) → 搜索文档
- create_issue(title, body) → 创建 GitHub Issue
- run_query(sql) → 执行数据库查询
```

### Resources (资源)

AI 可以读取的数据源。类似 REST API 的 GET 端点。

```
特点：
- AI 或用户主动请求读取
- 只读，不会产生副作用
- 适合"提供数据"：文件内容、数据库记录、配置信息
- 用 URI 标识：file:///path/to/doc.md

示例：
- docs://guide/getting-started → 返回入门文档内容
- config://app/settings → 返回应用配置
```

### Prompts (提示模板)

预定义的提示词模板。类似前端的组件模板。

```
特点：
- 用户选择使用（不是 AI 自动调用）
- 可以有参数
- 适合"标准化交互"：代码审查模板、文档生成模板

示例：
- review_code(code) → 生成代码审查提示词
- explain_error(error_message) → 生成错误分析提示词
```

### 三者对比

```
              谁触发？      副作用？     类比
  Tools       AI 主动调用    可能有       POST /api/action
  Resources   请求读取       无           GET /api/data
  Prompts     用户选择       无           UI 模板/组件
```

## 4. 传输方式 (Transport)

MCP 支持两种通信方式：

### stdio (标准输入输出)

```
AI Host ←──stdin/stdout──→ MCP Server (子进程)

特点：
- 最常用，本地运行
- MCP Server 作为子进程启动
- 通过 stdin 接收请求，stdout 返回响应
- Claude Code / Cursor 默认使用这种方式
```

### SSE (Server-Sent Events) / Streamable HTTP

```
AI Host ←──HTTP──→ MCP Server (独立服务)

特点：
- 适合远程 MCP Server
- 支持多客户端连接
- 通过 HTTP 通信
- 适合部署为云服务
```

**本周我们用 stdio**，因为：
1. 开发简单，不需要启动 HTTP 服务
2. 本地调试方便
3. Claude Code 原生支持

## 5. 协议细节 (了解即可)

MCP 基于 JSON-RPC 2.0：

```json
// Client → Server: 请求调用工具
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": { "keyword": "MCP" }
  }
}

// Server → Client: 返回结果
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      { "type": "text", "text": "Found 3 documents matching 'MCP'..." }
    ]
  }
}
```

你不需要手动处理 JSON-RPC —— SDK 会帮你封装好。

## 练习

1. 画出你想开发的 MCP Server 的架构图（纸上或文本）
2. 列出 3 个你想给 AI 提供的 Tools
3. 列出 2 个你想暴露的 Resources
4. 思考：为什么 MCP 选择 JSON-RPC 而不是 REST？

## 参考链接

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP 规范](https://spec.modelcontextprotocol.io/)
