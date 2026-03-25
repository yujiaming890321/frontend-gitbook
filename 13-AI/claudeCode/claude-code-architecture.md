# Claude Code 底层架构设计

## 概述

Claude Code 是 Anthropic 开发的终端 AI 编程助手，其架构设计遵循 **Unix 哲学与极简主义**——提供一个轻量级封装层，让 Claude 模型的原生能力直接发挥作用，而非构建过于复杂的脚手架。

核心控制逻辑位于一个高度混淆的 `cli.mjs` 文件中。

---

## 一、整体架构分层

```
┌─────────────────────────────────────────────────────────┐
│                   用户交互层 (UI Layer)                    │
│         CLI  │  VS Code 插件  │  JetBrains 插件  │  Web UI │
├─────────────────────────────────────────────────────────┤
│               Agent 核心调度层 (Agent Core)                │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│    │  Master Loop  │  │  Real-time   │  │   Context    │ │
│    │    (nO)       │  │  Steering    │  │  Compressor  │ │
│    │              │  │   (h2A)      │  │   (wU2)      │ │
│    └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────┤
│                工具引擎层 (Tool Engine)                    │
│  ToolEngine & Scheduler │ Permission System │ Hook System │
├─────────────────────────────────────────────────────────┤
│              外部集成层 (Integration Layer)                │
│   MCP Servers  │  Anthropic API  │  File System  │  Git   │
└─────────────────────────────────────────────────────────┘
```

### 1.1 用户交互层

本质上是一个 **多前端适配器模式**。Claude Code 的核心逻辑与 UI 解耦，底层是同一套 Agent 引擎，上面套不同的"壳"：

```
CLI（核心入口）
  │  通过 stdin/stdout 直接与用户交互
  │  所有其他前端本质上都在调用这个 CLI 进程
  │
VS Code / JetBrains 插件
  │  通过 Language Server Protocol 或类似 IPC 机制
  │  与本地 CLI 进程通信，插件本身只是 UI 渲染层
  │
Web UI
  │  云端运行 CLI 实例（隔离的虚拟机内）
  │  通过 WebSocket 或 HTTP 传输会话数据
```

关键设计决策：**CLI 是唯一的真实入口**。VS Code 插件不会直接调 Anthropic API，而是启动一个本地 Claude Code CLI 子进程，然后把用户操作转发给它。这保证了所有前端行为一致。

### 1.2 Agent 核心调度层

这是整个系统的"大脑"，包含三个独立组件（`nO`、`h2A`、`wU2`），它们协同工作：

- **Master Loop（主循环 `nO`）**：核心 Agent 循环引擎，决定"下一步做什么"
- **Real-time Steering（实时转向 `h2A`）**：异步双缓冲队列，允许"改变正在做的事"
- **Context Compressor（上下文压缩器 `wU2`）**：管理上下文窗口，确保"不会忘记重要的事"

### 1.3 工具引擎层

负责**工具的注册、调度、权限检查和沙箱执行**。工具调用不是直接执行的，而是经过一条完整的管道：

```
模型请求调用工具
    → Hook 拦截（PreToolUse，可以改写参数或拒绝）
    → 权限规则匹配（allow/ask/deny）
    → 用户审批（如果规则是 ask）
    → 沙箱环境内执行
    → Hook 后处理（PostToolUse，如自动格式化）
    → 结果序列化为 content item 返回给模型
```

核心组件：
- **ToolEngine & Scheduler**：编排工具调用和模型查询队列
- **Permission System**：分层权限控制
- **Hook System**：生命周期钩子

### 1.4 外部集成层

与外界交互的边界。MCP Server 是关键扩展点——它把"Claude Code 能做什么"从固定的内置工具集，扩展到了理论上**无限的外部能力**：

- **MCP Servers**：Model Context Protocol 服务器，开放标准协议
- **Anthropic API**：Claude 模型 API
- **File System / Git**：本地文件系统和版本控制

---

## 二、Agentic Loop（Agent 循环）

Claude Code 的核心是一个 **单线程主循环**（内部代号 `nO`），采用经典的 `while-loop` 模式。

### 2.1 循环流程

```
                    ┌──────────┐
                    │  开始任务  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
              ┌────►│  感知     │ ← 收集上下文，理解任务，识别可用能力
              │     │ Perceive │
              │     └────┬─────┘
              │          │
              │     ┌────▼─────┐
              │     │  思考     │ ← 推理问题，制定计划（常使用 TODO 列表）
              │     │  Think   │
              │     └────┬─────┘
              │          │
              │     ┌────▼─────┐
              │     │  行动     │ ← 调用工具，修改状态，执行计划
              │     │   Act    │
              │     └────┬─────┘
              │          │
              │     ┌────▼─────┐
              │     │  验证     │ ← 检查操作是否成功，评估进度
              │     │ Verify   │
              │     └────┬─────┘
              │          │
              │     ┌────▼──────────┐
              │     │ 是否完成目标？  │
              │     └───┬───────┬───┘
              │         │       │
              │        否      是
              │         │       │
              └─────────┘  ┌────▼─────┐
                           │ 输出结果   │
                           │  停止循环  │
                           └──────────┘
```

### 2.2 核心伪代码

```typescript
async function agentLoop(userMessage: string) {
  // 初始化对话历史
  messages.push({ role: "user", content: userMessage });

  while (true) {
    // 1. 调用 Claude API，传入完整对话历史 + 可用工具列表
    const response = await anthropicAPI.call({
      messages,
      tools: availableTools,
      system: systemPrompt  // 包含 CLAUDE.md 内容
    });

    // 2. 检查响应类型
    if (response.hasToolCalls()) {
      // 模型想调用工具 → 执行工具 → 继续循环
      for (const toolCall of response.toolCalls) {
        const result = await executeToolWithPermissions(toolCall);
        // 工具结果作为 assistant + tool_result 消息加入历史
        messages.push({ role: "assistant", content: toolCall });
        messages.push({ role: "user", content: result }); // tool_result
      }
      // 回到 while(true) 继续下一轮
    } else {
      // 模型返回纯文本 → 输出给用户 → 循环结束
      display(response.text);
      break;
    }

    // 3. 安全检查
    if (turnCount >= maxTurns || costSoFar >= maxBudgetUsd) {
      break; // 超限退出
    }
  }
}
```

### 2.3 终止条件

循环在以下情况下终止：
- 模型返回 **纯文本响应**（不包含工具调用）→ 循环结束
- 达到 **最大迭代次数**（`maxTurns`）
- 达到 **预算上限**（`maxBudgetUsd`）

### 2.4 为什么选择单线程？

刻意的设计选择。单线程意味着执行路径完全可预测、可调试。出了问题可以精确追踪到哪一步出错。虽然牺牲了并发性，但换来了可靠性。

### 2.5 工具调用的消息模型

工具调用和结果不是特殊的数据结构，而是作为普通的对话消息加入历史：

```
messages = [
  { role: "user",      content: "帮我找到所有 TODO" },
  { role: "assistant",  content: [tool_use: Grep("TODO")] },     ← 模型决定调工具
  { role: "user",      content: [tool_result: "找到3处..."] },   ← 工具结果伪装成 user 消息
  { role: "assistant",  content: [tool_use: Read("file.ts")] },  ← 模型继续调工具
  { role: "user",      content: [tool_result: "文件内容..."] },
  { role: "assistant",  content: "我找到了3处 TODO，分别是..." } ← 纯文本 → 循环结束
]
```

这样做的好处是：整个对话历史就是一个线性的消息数组，模型可以"回忆"之前所有的工具操作和结果，不需要额外的状态管理。

### 2.6 并行工具调用

虽然主循环是单线程，但模型可以在一次响应中返回**多个工具调用**。这些工具调用如果相互独立，会被并行执行，然后所有结果一起返回给模型。这就是为什么你会看到 Claude Code 同时读多个文件。

### 2.7 工具调用流程

```
用户输入
    │
    ▼
Claude 模型推理
    │
    ├── 返回纯文本 ──────► 循环结束，输出给用户
    │
    └── 返回工具调用 ──────► 权限检查
                              │
                        ┌─────▼──────┐
                        │ 用户审批？   │
                        │ (取决于模式) │
                        └─────┬──────┘
                              │
                         执行工具
                              │
                         工具返回结果
                              │
                     将结果作为 content item
                     加入对话历史
                              │
                         回到模型推理
```

工具调用的结果被视为统一消息模型中的 **content items**，文本和工具使用无缝集成到自然对话流中。

---

## 三、上下文管理系统

### 3.1 Context Compressor（上下文压缩器 `wU2`）

#### 核心问题

Claude 模型的上下文窗口有限（如 200K tokens）。一个长编码会话可能产生大量工具调用和结果，很快就会耗尽上下文。

#### 工作机制

```
对话进行中... tokens 持续增长
    │
    │  context_usage = current_tokens / max_tokens
    │
    ▼
┌──────────────────────────────────┐
│  context_usage >= 92% ?          │
│                                  │
│  否 → 继续正常对话                │
│  是 → 触发压缩 ↓                 │
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│        压缩过程                   │
│                                  │
│  1. 遍历历史消息                  │
│  2. 对每段对话/工具结果评分        │
│     - 架构决策 → 高分保留         │
│     - 未解决的 bug → 高分保留     │
│     - 用户显式指令 → 高分保留     │
│     - 冗余工具输出 → 低分丢弃     │
│     - 重复的文件读取 → 低分       │
│  3. 生成压缩摘要替换原始消息       │
└──────────────────────────────────┘
    │
    ▼
压缩后 context_usage ≈ 50-60%
继续正常对话...
```

#### 压缩策略的取舍

| 保留 | 丢弃 |
|------|------|
| 架构决策（"我们决定用 Redux"） | 大量 `grep` 搜索的原始结果 |
| 未解决的 bug 信息 | 已读过但不再需要的文件内容 |
| 用户的显式指令和偏好 | 中间步骤的调试输出 |
| 最终修改方案的关键代码 | 被否决的方案的探索过程 |
| 当前任务的核心上下文 | 已完成子任务的详细过程 |

#### 用户可感知的表现

当你在 Claude Code 中看到类似这样的消息时，就是压缩器在工作：

```
ℹ Auto-compacting conversation (92% of context used)
```

压缩后，Claude 仍然"记得"做过什么（通过摘要），但不再持有原始的详细数据。这就是为什么有时候长会话中 Claude 会说"让我重新读一下那个文件"——因为压缩后原始文件内容已被丢弃。

### 3.2 存储方式

Claude Code 使用 **简单 Markdown 文件**（如 `CLAUDE.md`、`MEMORY.md`）作为项目记忆，**刻意避免使用向量数据库**，追求务实的解决方案。

### 3.3 Real-time Steering（实时转向 `h2A`）

#### 解决的问题

假设 Claude Code 正在执行一个耗时任务（比如逐个读取 20 个文件），执行到第 10 个时你发现方向错了，想让它改做别的事。**没有 `h2A` 的话**，你只能等它全部执行完，或者强制终止丢失所有上下文。

#### 异步双缓冲队列机制

```
┌────────────────────────────────────────────────┐
│                  主循环 (nO)                     │
│                                                │
│  正在执行: Read("file1.ts")                     │
│          → Read("file2.ts")                    │
│          → Read("file3.ts") ← 当前执行          │
│          → Read("file4.ts") ← 待执行            │
│          → ...                                 │
│                                                │
│  ┌──────────────────────────────┐              │
│  │     缓冲区 (h2A)             │              │
│  │                              │              │
│  │  [用户新输入]:                │ ← 用户此时    │
│  │  "停下来，改去看 config 文件"  │   按下 Esc   │
│  │                              │   或输入新指令 │
│  └──────────────────────────────┘              │
│                                                │
│  下一轮循环开始时:                               │
│  1. 检查缓冲区 → 发现有用户新指令               │
│  2. 将新指令注入到下一次 API 调用               │
│  3. 模型看到新指令后自行调整行为                 │
└────────────────────────────────────────────────┘
```

#### 工作流程时间线

```
t0  用户: "帮我重构 auth 模块"
t1  Claude: [开始读取 auth 相关文件...]
t2  Claude: [读取 auth/login.ts]
t3  Claude: [读取 auth/register.ts]
t4  用户: (按 Esc 或输入) "等等，先只处理 login 部分"   ← 注入到 h2A 缓冲区
t5  Claude: [读取 auth/middleware.ts]  ← 当前工具调用继续完成
t6  [本轮工具调用结束，准备下次 API 调用]
t7  [检查 h2A 缓冲区 → 发现用户新指令]
t8  [将新指令作为附加 user message 加入对话]
t9  Claude: "好的，我只关注 login 部分..."  ← 模型自动调整方向
```

#### 关键设计点

- **非中断式**：不会强制终止正在执行的工具调用，而是等当前工具完成后再处理
- **缓冲而非丢弃**：用户输入被缓冲，不会丢失
- **双缓冲**：一个缓冲区接收用户输入，另一个在下次循环时被消费，避免竞态条件
- **模型自主判断**：新指令被注入后，由模型自行判断如何调整，不需要硬编码的打断逻辑

这个设计使得 Claude Code 的交互体验更接近"与真人协作"——你可以随时插话修正方向，而不是只能等对方说完。

---

## 四、工具系统（Tool System）

### 4.1 内置工具列表

| 工具名 | 功能 | 说明 |
|--------|------|------|
| `Read` / `View` | 读取文件 | 支持文本、图片、Jupyter Notebook |
| `Write` | 创建文件 | 完整写入新文件 |
| `Edit` | 编辑文件 | 精确字符串替换 |
| `Glob` | 文件搜索 | 支持 glob 模式匹配 |
| `Grep` | 内容搜索 | 基于 ripgrep 的正则搜索 |
| `Bash` | 执行命令 | 沙箱化的 shell 命令执行 |
| `Task` | 子 Agent | 启动专用子 Agent 处理复杂任务 |
| `WebFetch` | 网页获取 | 获取并分析网页内容 |
| `WebSearch` | 网页搜索 | 搜索互联网获取信息 |
| `NotebookEdit` | Notebook 编辑 | 编辑 Jupyter Notebook 单元格 |

### 4.2 工具执行模型

```
工具调用请求
    │
    ▼
┌──────────────────┐
│  PreToolUse Hook │ ← 执行前钩子（可拦截/修改/拒绝）
└────────┬─────────┘
         │
    ┌────▼──────────┐
    │  Permission   │ ← 权限规则检查（allow / ask / deny）
    │   Check       │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │  Sandbox      │ ← 沙箱执行（macOS seatbelt / Linux bubblewrap）
    │  Execution    │
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │ PostToolUse   │ ← 执行后钩子
    │    Hook       │
    └────┬──────────┘
         │
    返回结果给模型
```

### 4.3 MCP Server 集成

通过 **Model Context Protocol (MCP)** 扩展工具能力：

- MCP 是开放标准协议
- 以本地进程、HTTP 连接或 SDK 内直接执行方式运行
- 可连接数据库、第三方 API（如 Slack、GitHub）等外部服务
- 支持动态工具发现和加载

---

## 五、权限系统（Permission System）

### 5.1 权限模式

| 模式 | 说明 |
|------|------|
| `manual`（默认） | 敏感操作需要用户显式批准 |
| `acceptEdits` | 自动批准文件编辑，其他操作仍需确认 |
| `acceptAll` / `bypassPermissions` | 完全自主模式，自动批准所有操作 |

### 5.2 权限规则

通过 `.claude/settings.json` 或 `/permissions` 命令配置：

```json
{
  "permissions": {
    "allow": ["Read", "Glob", "Grep"],
    "ask": ["Write", "Edit", "Bash"],
    "deny": ["dangerous_tool"]
  }
}
```

### 5.3 安全沙箱

- **macOS**：使用 `sandbox-exec`（seatbelt）强制限制
- **Linux**：使用 `bubblewrap` 容器化执行
- 默认 **严格只读权限**，写操作需要显式授权

---

## 六、Hook 系统（Lifecycle Hooks）

### 6.1 Hook 事件类型

| 事件 | 触发时机 |
|------|---------|
| `SessionStart` | 会话启动时 |
| `SessionEnd` | 会话结束时 |
| `PreToolUse` | 工具调用执行前 |
| `PostToolUse` | 工具调用执行后 |
| `WorktreeCreate` | 创建 Git worktree 时 |
| `WorktreeRemove` | 移除 Git worktree 时 |
| `SubagentStart` | 子 Agent 启动时 |
| `SubagentStop` | 子 Agent 停止时 |
| `PermissionRequest` | 权限请求时 |

### 6.2 Hook 执行类型

- **Shell 命令**：执行自定义脚本
- **HTTP 端点**：调用外部 API
- **LLM Prompt**：使用 AI 模型判断

### 6.3 Hook 配置示例

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "command": "prettier --write $CLAUDE_FILE_PATH"
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "echo 'Bash command intercepted: $CLAUDE_TOOL_INPUT'"
      }
    ]
  }
}
```

---

## 七、子 Agent 系统（Subagent System）

### 7.1 子 Agent 类型

| 类型 | 能力 | 用途 |
|------|------|------|
| `general-purpose` | 所有工具 | 通用复杂任务 |
| `Explore` | 只读（无编辑） | 快速代码库探索和搜索 |
| `Plan` | 只读（无编辑） | 设计实现计划 |
| `claude-code-guide` | 只读 + Web | Claude Code 使用指南问答 |
| `code-reviewer` | 所有工具 | 代码审查 |

### 7.2 子 Agent 架构

```
主 Agent (Main Agent)
    │
    ├── 子 Agent 1 (Explore)     ← 独立上下文窗口
    │     └── 只读工具集
    │
    ├── 子 Agent 2 (general)     ← 独立上下文窗口
    │     └── 完整工具集
    │
    └── 子 Agent 3 (Plan)        ← 独立上下文窗口
          └── 只读工具集
```

每个子 Agent 拥有：
- **独立上下文窗口**：不占用主 Agent 上下文
- **自定义系统提示词**：根据角色定制
- **可配置的工具权限**：按需分配工具访问
- **可并行执行**：多个子 Agent 可同时运行

### 7.3 Worktree 隔离

子 Agent 可以使用 Git worktree 实现代码隔离：

```
项目根目录/
├── .claude/
│   └── worktrees/
│       ├── agent-1-branch/     ← 子 Agent 1 的独立工作副本
│       └── agent-2-branch/     ← 子 Agent 2 的独立工作副本
├── src/
└── ...
```

- 每个 worktree 是项目的独立 Git 副本
- 变更互不干扰，直到显式提交/合并
- 会话结束后可自动清理

---

## 八、Proxy 架构

Claude Agent SDK 通过本地 Claude Code CLI 进程通信：

```
应用代码 (SDK)
    │
    ▼
Claude Code CLI (本地代理)
    │
    ├── 认证管理 (Authentication)
    ├── 会话状态 (Session State)
    ├── 权限管理 (Permissions)
    │
    ▼
Anthropic API (云端)
```

CLI 充当代理角色，负责：
- **认证管理**：处理 API 密钥和 OAuth 流程
- **会话状态**：维护对话历史和上下文
- **权限控制**：在本地执行权限规则
- **API 调用**：向 Anthropic API 发送实际请求

---

## 九、记忆系统（Memory System）

### 9.1 分层记忆

```
┌─────────────────────────────────────┐
│       CLAUDE.md 指令系统             │ ← 显式规则（详见上一篇文档）
│  企业 > 用户 > 项目 > 规则 > 子目录   │
├─────────────────────────────────────┤
│       MEMORY.md 自动记忆             │ ← 自动学习和记忆
│  ~/.claude/projects/<project>/      │
│         memory/MEMORY.md            │
├─────────────────────────────────────┤
│       对话上下文                     │ ← 当前会话对话历史
│   （由 Compressor wU2 管理）          │
└─────────────────────────────────────┘
```

### 9.2 MEMORY.md 特性

- 位置：`~/.claude/projects/<project-path>/memory/MEMORY.md`
- 自动加载到对话上下文
- 超过 **200 行**会被截断
- 详细笔记应拆分到独立的主题文件中
- 语义组织（按主题），非时间线组织

---

## 十、设计哲学总结

| 原则 | 实践 |
|------|------|
| **极简主义** | 薄封装层，让 Claude 原生能力直接发挥 |
| **可调试性** | 单线程循环，清晰的执行路径 |
| **务实方案** | Markdown 文件替代向量数据库，ripgrep 替代语义搜索 |
| **安全优先** | 默认只读，沙箱执行，分层权限 |
| **可扩展性** | MCP 协议，Hook 系统，自定义子 Agent |
| **可控自主** | 用户始终保持控制权，可中途干预 |

---

## 十一、技术栈

| 组件 | 技术 |
|------|------|
| 运行时 | Node.js |
| 主要语言 | TypeScript（编译为混淆的 `cli.mjs`） |
| 搜索引擎 | ripgrep（`rg`） |
| 沙箱 | macOS seatbelt / Linux bubblewrap |
| 扩展协议 | Model Context Protocol (MCP) |
| SDK | Claude Agent SDK（TypeScript & Python） |
| 版本控制集成 | Git / Git worktree |
| CI/CD | GitHub Actions 集成 |
