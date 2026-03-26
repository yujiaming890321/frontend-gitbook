# MCP、Skill、Plugin：AI 工具生态的三大扩展机制

## 前言：Agent 之后还缺什么？

读完 Agent 和 RAG 的文章后，你已经知道：

- **Agent** = LLM + Tools + Memory，能自主决策、循环完成任务
- Agent 通过 **Function Calling** 可靠地调用工具
- **LangChain / LangGraph** 提供了构建 Agent 应用的框架

但当你真正开始用 AI 编程工具（Claude Code、Cursor、GitHub Copilot 等）时，会遇到三个新问题：

```
问题一：工具连接碎片化
  Claude Code 想连 GitHub → 自己写集成代码
  Cursor 也想连 GitHub   → 再写一遍
  每个 AI 工具都重复造轮子

问题二：工作流无法复用
  你教会了 AI "提交代码时要先检查 lint、再写 commit message、再 push"
  换个项目、换个同事，又要重新教一遍

问题三：扩展能力难分发
  有人写了一个很好用的 GitHub 集成
  怎么让其他人一键安装、开箱即用？
```

MCP、Skill、Plugin 分别解决这三个问题。

---

## 一、MCP（Model Context Protocol）

### 1. 问题：M × N 的集成噩梦

假设市面上有 5 个 AI 工具，10 个外部服务需要集成：

```
没有标准协议时：

Claude Code ──→ 自己写 GitHub 集成、Slack 集成、Jira 集成...（10个）
Cursor      ──→ 自己写 GitHub 集成、Slack 集成、Jira 集成...（10个）
Copilot     ──→ 自己写 GitHub 集成、Slack 集成、Jira 集成...（10个）
Windsurf    ──→ 自己写 GitHub 集成、Slack 集成、Jira 集成...（10个）
自定义 Agent ──→ 自己写 GitHub 集成、Slack 集成、Jira 集成...（10个）

总共需要：5 × 10 = 50 个集成代码
```

这就是经典的 **M × N 问题**——和 Web 时代之前每个应用自己实现网络协议一样。

### 2. MCP 是什么

MCP（Model Context Protocol，模型上下文协议）是 Anthropic 在 2024 年底推出的**开放标准协议**，定义了 AI 应用与外部工具/数据源之间的通信方式。

一句话：**MCP 是 AI 时代的 USB 接口**——让任何 AI 应用可以即插即用地连接任何外部工具。

```
有了 MCP 之后：

AI 应用侧（实现 MCP Client）          工具侧（实现 MCP Server）
┌─────────────┐                      ┌─────────────────┐
│ Claude Code  │                      │ GitHub Server    │
│ Cursor       │ ←── MCP 协议 ──→    │ Slack Server     │
│ Copilot      │                      │ Jira Server      │
│ Windsurf     │                      │ Database Server  │
│ 自定义 Agent  │                      │ ...              │
└─────────────┘                      └─────────────────┘

总共需要：5 + 10 = 15 个实现（而不是 50 个）
```

每个 AI 应用只需实现一次 MCP Client，每个工具只需实现一次 MCP Server。

### 3. 架构

```
┌──────────────┐                    ┌──────────────────┐
│   AI 应用     │     MCP 协议       │   MCP Server      │
│ (MCP Client)  │ ←──────────────→  │  (工具提供方)       │
│               │                   │                    │
│  发送请求：    │   JSON-RPC 通信    │  响应请求：         │
│  tools/list   │ ────────────────→ │  返回可用工具列表    │
│  tools/call   │ ────────────────→ │  执行工具并返回结果  │
│  resources/   │ ────────────────→ │  返回数据资源       │
│  read         │                   │                    │
└──────────────┘                    └──────────────────┘
```

### 4. 三大核心概念

MCP Server 可以提供三种能力：

```
┌────────────────────────────────────────────────────┐
│                    MCP Server                       │
├────────────┬─────────────────┬──────────────────────┤
│   Tools    │   Resources     │   Prompts            │
│  (工具)    │  (资源)          │  (提示词模板)         │
│            │                 │                      │
│ 可执行的    │ 可读取的数据     │ 预定义的交互模板      │
│ 函数/动作   │ 文件/API/数据库  │                      │
│            │                 │                      │
│ 例：创建    │ 例：读取文件     │ 例：代码审查的        │
│ GitHub PR  │ 内容、查询数据库  │ 标准 prompt          │
└────────────┴─────────────────┴──────────────────────┘
```

| 概念 | 类比 | 说明 |
|------|------|------|
| **Tools** | Function Calling 里的函数 | AI 可以调用的动作（创建 PR、发消息、写文件） |
| **Resources** | REST API 的 GET 端点 | AI 可以读取的数据（文件内容、数据库记录） |
| **Prompts** | Prompt 模板库 | 预定义的交互模板（代码审查模板、分析模板） |

### 5. 通信方式

MCP 使用 **JSON-RPC 2.0** 协议通信，支持两种传输方式：

```
1. stdio（标准输入/输出）
   AI 应用 ──spawn──→ MCP Server 进程
   通过 stdin/stdout 通信
   适合本地工具

2. HTTP + SSE（服务器发送事件）/ Streamable HTTP
   AI 应用 ──HTTP──→ 远程 MCP Server
   适合云端服务
```

### 6. 配置示例

以 Claude Code 为例，在项目的 `.mcp.json` 中配置：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxx"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

配置后，AI 就自动获得了这些 Server 提供的工具能力，无需写任何代码。

### 7. MCP 与 Function Calling 的关系

| | Function Calling | MCP |
|---|---|---|
| **层级** | 协议层（LLM 怎么调工具） | 生态层（工具怎么标准化提供） |
| **定义方** | AI 应用开发者在代码里定义 | 工具提供方独立实现为 MCP Server |
| **作用域** | 单个 AI 应用内部 | 跨应用、跨平台 |
| **工具发现** | 硬编码在应用里 | 动态发现（tools/list） |
| **类比** | "这个应用能调用这些函数" | "这些函数作为服务发布，任何应用都能用" |

**MCP 不是替代 Function Calling，而是建立在它之上**——MCP Server 暴露的 Tools，最终还是通过 Function Calling 机制被 LLM 调用。

### 8. 各 AI 工具对 MCP 的支持

| AI 工具 | MCP 支持 | 说明 |
|---------|---------|------|
| **Claude Code** | 原生支持 | Anthropic 自家产品，MCP 一等公民 |
| **Claude Desktop** | 原生支持 | 通过 `claude_desktop_config.json` 配置 |
| **Cursor** | 支持 | 可在设置中添加 MCP Server |
| **Windsurf** | 支持 | Codeium 推出的 AI IDE |
| **VS Code Copilot** | 支持 | GitHub Copilot Chat 可连接 MCP Server |
| **Zed** | 支持 | 开源编辑器，内置 MCP 支持 |
| **自定义 Agent** | 可集成 | 使用 MCP SDK 实现 Client |

### 9. MCP 的本质

```
类比：
  HTTP 协议     → 标准化了浏览器和服务器之间的通信
  MCP 协议      → 标准化了 AI 应用和外部工具之间的通信

  REST API 规范 → 让任何客户端都能调用任何服务端
  MCP 规范      → 让任何 AI 应用都能使用任何工具
```

---

## 二、Skill（技能 / 工作流模板）

### 1. 问题：AI 有能力，但不知道"该怎么做"

MCP 解决了"AI 能连什么工具"的问题，但有了工具不代表会用。

```
场景：你让 AI 帮你提交代码

没有 Skill 时：
  你：帮我提交代码
  AI：好的，git add . && git commit -m "update" && git push
  你：不对！commit message 要用英文，格式是 "JIRA-123: description"，
      要先跑 lint，PR title 也有格式要求...
  AI：好的，下次我注意
  （下次又忘了）

有 Skill 时：
  你：帮我提交代码
  AI：（自动加载 commit skill）
      1. 检查 diff 内容
      2. 从分支名提取 Jira ticket
      3. 生成符合规范的 commit message
      4. 执行 git commit && git push
  ← 每次都按规范来，不会忘
```

### 2. Skill 是什么

一句话：**Skill 是写给 AI 的 SOP（标准操作流程）**——告诉 AI 遇到某种任务时，应该按什么步骤、什么规范来完成。

```
Skill 的本质：
┌──────────────────────────────────────┐
│              Skill                    │
│                                      │
│  触发条件：什么时候该用这个 Skill      │
│  工作步骤：按什么顺序做什么           │
│  规范约束：什么该做、什么不该做        │
│  工具编排：用哪些工具、怎么组合        │
│                                      │
│  本质上就是一段结构化的 Prompt        │
│  + 预定义的工作流                     │
└──────────────────────────────────────┘
```

### 3. Skill 的结构（以 Claude Code 为例）

Claude Code 的 Skill 是一个 Markdown 文件（`SKILL.md`），包含 frontmatter 元数据和工作流步骤：

```markdown
---
name: fix-pr-comments
description: "Use when fixing code based on GitHub PR review comments."
---

# Fix PR Review Comments

## Keywords
fix pr comments, fix review, resolve review, address feedback

## When to Use
- User says "fix pr comments" or provides a PR URL
- User wants to resolve review feedback

## Workflow

### Step 1: Identify PR
Extract PR number from user input, detect repo from git remote.

### Step 2: Fetch Comments
Use `gh api` to fetch review comments...

### Step 3: Fix Code
For each comment, read the file, understand feedback, apply fix.

### Step 4: Commit and Push
Stage changes, commit with project format, push.

## Rules
- Commit message must be English
- Format: `JIRA_TICKET: description`
- Always show comments summary before fixing
```

当用户说"帮我修复 PR 评论"时，AI 会自动匹配并加载这个 Skill，然后严格按照定义的步骤执行。

### 4. 各 AI 工具中的"Skill"概念

不同 AI 工具对这个概念有不同的叫法和实现，但**本质都一样——告诉 AI 该怎么做事**：

| AI 工具 | 对应概念 | 文件/配置 | 说明 |
|---------|---------|----------|------|
| **Claude Code** | Skill（`.claude/skills/`） | `SKILL.md` 文件 | 结构化的 Markdown，支持触发条件、工作流步骤 |
| **Claude Code** | CLAUDE.md | 项目根目录 `CLAUDE.md` | 项目级指令，类似轻量版 Skill |
| **Cursor** | Rules（`.cursor/rules/`） | `.mdc` 文件 | 告诉 Cursor 项目的编码规范和工作方式 |
| **GitHub Copilot** | Instructions | `.github/copilot-instructions.md` | 项目级指令文件 |
| **ChatGPT** | Custom Instructions | 设置页面 | 全局指令，告诉 ChatGPT 你的偏好 |
| **ChatGPT** | GPTs | GPT Builder | 自定义的专用 ChatGPT，内含指令+工具 |
| **Windsurf** | Rules（`.windsurfrules`） | 项目根目录 | 类似 Cursor Rules |

#### 对比：Claude Code Skill vs Cursor Rules

```
Claude Code Skill（SKILL.md）：
┌─────────────────────────────────────────┐
│ name: fix-security                      │  ← 名称
│ description: Fix Dependabot alerts      │  ← 触发描述
│                                         │
│ ## Workflow                             │  ← 详细的多步骤工作流
│ ### Step 1: Fetch alerts                │
│ ### Step 2: Classify dependencies       │
│ ### Step 3: Present fix plan            │
│ ### Step 4: Apply fixes                 │
│ ### Step 5: Verify build                │
│                                         │
│ ## Rules                                │  ← 约束条件
│ - NEVER apply fixes without confirmation│
└─────────────────────────────────────────┘

Cursor Rules（.mdc）：
┌─────────────────────────────────────────┐
│ ---                                     │
│ description: TypeScript coding standards│  ← 触发描述
│ globs: **/*.ts, **/*.tsx                │  ← 文件匹配规则
│ ---                                     │
│                                         │
│ # TypeScript Rules                      │
│ - Use `unknown` instead of `any`        │  ← 编码规范指令
│ - Prefer `interface` over `type`        │
│ - Always use strict null checks         │
└─────────────────────────────────────────┘
```

**关键区别**：Claude Code Skill 侧重**工作流编排**（多步骤任务），Cursor Rules 侧重**编码规范**（写代码时的约束）。但本质上都是"给 AI 的指令"。

#### ChatGPT GPTs

GPTs 是 Skill 概念在 ChatGPT 生态中的极致体现——一个 GPT 就是：

```
GPT = Custom Instructions（指令/Skill）
    + Knowledge（上传的文档/RAG）
    + Actions（API 调用/Tools）

例如：一个"代码审查 GPT"
  指令：你是一个资深代码审查员，关注安全、性能、可读性...
  知识：上传公司编码规范文档
  Actions：连接 GitHub API 获取 PR diff
```

### 5. Skill 与 Prompt Engineering 的关系

```
Prompt Engineering → 单次交互的 prompt 技巧（CoT、Few-Shot 等）
Skill             → 多步骤任务的完整 prompt + 工作流
```

Skill 本质上就是**高级 Prompt Engineering**——不是一条 prompt，而是一组 prompt + 步骤编排 + 约束规则，打包成可复用的模板。

### 6. Skill 的价值

```
没有 Skill：每次交互都要重新教 AI 怎么做
  "帮我提交代码，注意 commit message 用英文，格式是..."
  "帮我修 PR 评论，先用 gh api 获取评论，注意 hostname..."
  "帮我修安全漏洞，先看 Dependabot alerts，注意区分直接和间接依赖..."

有了 Skill：AI 自动按规范执行
  "帮我提交代码"      → 自动加载 commit skill
  "修复 PR 评论"       → 自动加载 fix-pr-comments skill
  "修安全漏洞"         → 自动加载 fix-security skill
```

**Skill 把团队的工程经验和最佳实践编码化了**——新人（无论是新同事还是新 AI 对话）不需要重新学习，加载 Skill 就能按规范执行。

---

## 三、Plugin（插件 / 扩展）

### 1. 问题：好工具怎么分发给别人用？

假设有人写了一个很好用的 MCP Server（比如连接 Context7 文档查询服务），你怎么用上它？

```
没有 Plugin 机制时：
  1. 找到这个 MCP Server 的 GitHub 仓库
  2. 阅读 README，了解怎么配置
  3. 手动写配置文件，填入正确的 command、args、env
  4. 调试连接问题
  5. 同事也想用？把以上步骤再走一遍

有 Plugin 机制时：
  1. 搜索 Plugin 市场
  2. 一键安装
  3. 完成
```

### 2. Plugin 是什么

一句话：**Plugin 是打包好的扩展能力包**——把 MCP Server（或其他扩展）包装成用户友好的安装形式，实现一键安装、开箱即用。

```
Plugin 的本质：
┌───────────────────────────────────────┐
│              Plugin                    │
│                                       │
│  ┌─ MCP Server（核心能力）              │
│  │   - 提供 Tools（可调用的工具）       │
│  │   - 提供 Resources（可读取的数据）   │
│  │                                     │
│  ├─ 配置模板（预填好的参数）            │
│  │                                     │
│  ├─ 安装脚本（依赖管理）               │
│  │                                     │
│  └─ 使用说明（触发关键词、示例）        │
└───────────────────────────────────────┘
```

**类比**：

```
MCP Server  ≈ 一个 npm 包的源代码
Plugin      ≈ 发布到 npm registry 的包 + 使用说明 + 配置模板

或者：
MCP Server  ≈ VS Code 扩展的源代码
Plugin      ≈ 发布到 VS Code Marketplace 的扩展（一键安装）
```

### 3. 各 AI 工具中的 Plugin 概念

| AI 工具 | Plugin 形式 | 分发方式 | 说明 |
|---------|-----------|---------|------|
| **Claude Code** | MCP Plugin | npm 包 / 配置文件 | 通过 `.mcp.json` 或 `claude mcp add` 安装 |
| **ChatGPT** | ChatGPT Plugins（已演变为 GPTs + Actions） | GPT Store | 早期独立 Plugin 机制，现整合进 GPTs |
| **Cursor** | Extensions | 内置配置 | MCP Server + Cursor Rules 的组合 |
| **VS Code Copilot** | Copilot Extensions | VS Code Marketplace | GitHub 出品，扩展 Copilot 能力 |
| **Chrome** | AI Extensions | Chrome Web Store | 浏览器插件形式接入 AI 能力 |

#### ChatGPT Plugin 的演变（历史参考）

ChatGPT Plugin 是最早的 AI Plugin 尝试之一，它的演变过程很有参考价值：

```
2023 年初：ChatGPT Plugins（第一代）
  ├─ 开发者提供一个 API + openapi.yaml 描述文件
  ├─ ChatGPT 通过 API 调用外部服务
  ├─ 用户在 Plugin Store 安装
  └─ 问题：生态碎片化、用户使用率低

2023 年底：GPTs 取代了独立 Plugin
  ├─ GPTs = Custom Instructions + Knowledge + Actions
  ├─ Actions 就是原来 Plugin 的 API 调用能力
  ├─ 但更易创建（无需开发者，普通用户就能做）
  └─ 通过 GPT Store 分发

本质变化：
  Plugin（纯工具能力）→ GPTs（工具 + 指令 + 知识 的组合体）
                            ≈ Plugin + Skill + RAG 的融合
```

#### Claude Code 的 Plugin

Claude Code 的 Plugin 就是 MCP Server，通过以下方式安装：

```bash
# 方式一：命令行添加
claude mcp add context7 -- npx -y @anthropic-ai/context7-mcp

# 方式二：配置文件（.mcp.json）
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/context7-mcp"]
    }
  }
}
```

安装后，AI 就能使用这个 Plugin 提供的工具——比如 `query-docs` 查询第三方库文档。

#### VS Code Copilot Extensions

GitHub Copilot 的扩展机制，让第三方开发者扩展 Copilot 的能力：

```
Copilot Extension 的类型：
  ├─ Skill Extension：给 Copilot 添加新技能（类似 Skill）
  ├─ Agent Extension：在 Copilot Chat 中添加 @agent（如 @docker）
  └─ MCP Extension：通过 MCP 协议连接外部工具

使用方式：
  用户在 Copilot Chat 中输入 @docker build this project
  → Copilot 调用 Docker Extension
  → Extension 通过 Docker API 执行构建
```

### 4. Plugin 与 MCP 的关系

```
层级关系：

Plugin（分发和安装形式）
  └── 内含 MCP Server（标准化的工具提供方）
        └── 通过 MCP 协议暴露 Tools / Resources / Prompts
              └── AI 通过 Function Calling 调用这些 Tools

打个比方：
  MCP 协议    ≈ USB 标准规范
  MCP Server  ≈ 一个 USB 设备的硬件
  Plugin      ≈ 这个 USB 设备的零售包装（说明书 + 驱动光盘 + 设备本体）
```

不是所有 Plugin 都基于 MCP。但 MCP 正在成为 AI Plugin 的主流底层协议——因为一个 MCP Server 写一次，就能被所有支持 MCP 的 AI 工具使用。

---

## 四、三者对比

### 1. 核心区别

| | MCP | Skill | Plugin |
|---|---|---|---|
| **是什么** | 通信协议 | 工作流模板 | 扩展安装包 |
| **解决什么** | AI 怎么连接外部工具 | AI 怎么按流程做事 | 怎么分发和安装扩展能力 |
| **类比** | HTTP 协议 / USB 标准 | SOP 操作手册 | npm 包 / VS Code 插件 |
| **谁写** | 工具/服务提供方 | 团队/个人/社区 | 工具提供方 |
| **内容** | Client-Server 通信规范 | Prompt + 步骤 + 约束 | MCP Server + 配置 + 说明 |
| **存储位置** | 协议规范文档 | `.claude/skills/`、`.cursor/rules/` 等 | npm registry、配置文件 |

### 2. 一句话记忆

```
MCP    → "怎么连"  → 标准化 AI 与外部工具的通信方式
Skill  → "怎么用"  → 告诉 AI 按什么步骤完成任务
Plugin → "装什么"  → 把工具能力打包成可安装的扩展
```

### 3. 类比

```
开发者世界的类比：

MCP    ≈ REST API 规范      → 定义了客户端和服务端怎么通信
Skill  ≈ Makefile / 脚本     → 定义了一系列步骤该怎么执行
Plugin ≈ npm 包 / brew formula → 把能力打包成可安装的形式

现实世界的类比：

MCP    ≈ 电源插座标准（国标、美标）  → 定义了设备怎么接入电网
Skill  ≈ 菜谱 / 操作手册            → 告诉你怎么一步步完成任务
Plugin ≈ 家电产品（带插头 + 说明书） → 即插即用的成品
```

### 4. 关系图

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   Plugin（安装包）                                       │
│   ┌───────────────────────────────────┐                 │
│   │                                   │                 │
│   │  MCP Server（工具能力）            │                 │
│   │  ┌─────────────────────────────┐  │                 │
│   │  │ Tools    Resources  Prompts │  │                 │
│   │  └─────────────────────────────┘  │                 │
│   │  + 安装配置 + 使用说明             │                 │
│   │                                   │                 │
│   └───────────────────────────────────┘                 │
│                                                         │
│   Skill（工作流模板）                                    │
│   ┌───────────────────────────────────┐                 │
│   │ 触发条件 + 步骤编排 + 约束规则     │                 │
│   │                                   │                 │
│   │ 编排如何使用 Tools 来完成任务       │←── 调用 MCP     │
│   │ （包括 MCP 提供的 Tools）          │    提供的工具    │
│   └───────────────────────────────────┘                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 五、协作示例：修复 GitHub PR 评论

一个真实场景，看三者如何协作：

```
用户："帮我修复 PR #42 的评论"

┌─ Skill 层：加载 fix-pr-comments skill
│   定义了完整工作流：
│   Step 1: 获取 PR 信息
│   Step 2: 拉取评论
│   Step 3: 逐条修复
│   Step 4: 提交推送
│
├─ MCP 层：通过 MCP 协议调用 GitHub MCP Server
│   tools/call: get_pull_request_comments(pr: 42)
│   tools/call: get_pull_request_reviews(pr: 42)
│   → 返回结构化的评论数据
│
├─ Plugin 层：GitHub MCP Server 作为 Plugin 被安装
│   之前通过 `claude mcp add github ...` 一键安装
│   无需手动写 GitHub API 集成代码
│
└─ 执行结果：
    1. 展示评论摘要
    2. 逐条修复代码
    3. 按规范 commit（"JIRA-123: address pr review comments"）
    4. git push
```

三者各司其职：

```
Plugin  → 提供了 GitHub 工具能力（安装层）
MCP     → 标准化了与 GitHub 的通信（协议层）
Skill   → 编排了修复 PR 评论的完整流程（工作流层）
```

---

## 六、总结

### 技术栈全景

```
┌────────────────────────────────────────────────────────┐
│                    AI 工具扩展生态                       │
├──────────────┬──────────────────┬──────────────────────┤
│   Plugin     │     Skill        │       MCP            │
│  (分发安装)   │   (工作流编排)    │   (通信协议)          │
│              │                  │                      │
│  解决：      │  解决：           │  解决：               │
│  怎么装？    │  怎么用？         │  怎么连？             │
│              │                  │                      │
│  npm 包      │  SKILL.md        │  JSON-RPC            │
│  GPT Store   │  Cursor Rules    │  stdio / HTTP        │
│  Marketplace │  Custom Instr.   │  tools/resources     │
├──────────────┴──────────────────┴──────────────────────┤
│              底层：Function Calling                     │
│              LLM 调用工具的标准化接口                    │
├───────────────────────────────────────────────────────┤
│              基座：LLM（大语言模型）                     │
│              理解意图、推理决策、生成内容                 │
└───────────────────────────────────────────────────────┘
```

### 与之前知识的衔接

```
你已经知道的：
  Prompt Engineering  → LLM 怎么理解意图
  Function Calling    → LLM 怎么调用工具
  Agent               → LLM 怎么自主完成任务
  RAG                 → LLM 怎么利用外部知识

这篇文章新增的：
  MCP                 → 工具怎么标准化连接（跨应用复用）
  Skill               → 工作流怎么模板化（跨项目复用）
  Plugin              → 扩展能力怎么分发（跨团队复用）
```

每一层都在解决**复用**的问题——从单次调用的复用（Function Calling），到跨应用的复用（MCP），到工作流的复用（Skill），到安装分发的复用（Plugin）。它们共同构成了 AI 工具的完整扩展生态。
