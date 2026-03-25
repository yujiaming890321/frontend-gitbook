# Claude Code 实践

## 各层的职责

| level | responsibility |
| --- | --- |
| ClAUDE.md / rules / memory | 长期上下文，告诉Claude “是什么” |
| Tools/MCP | 动作能力，告诉Claude “能做什么” |
| Skills | 按需加载的方法论，告诉Claude “怎么能” |
| Hooks | 强制执行某些行为，不依赖Claude 自己判断 |
| Subagent | 隔离上下文的工作者，负责受控自治 |
| Verifiers | 验证闭环，让输出可验、可回滚、可审计 |

## How Claude Code works

https://code.claude.com/docs/en/how-claude-code-works

### 代理循环 agentic loop

给 Claude 一个任务时，它会经历三个阶段：收集上下文、采取行动和验证结果。
这些阶段相互融合。Claude 始终使用工具，无论是搜索文件以了解您的代码、编辑以进行更改，还是运行测试以检查其工作。

```
收集上下文 → 采取行动 → 验证结果 → [完成 or 回到收集]
     ↑                    ↓
  CLAUDE.md          Hooks / 权限 / 沙箱
  Skills             Tools / MCP
  Memory
```

代理循环由两个组件驱动：推理的模型和采取行动的工具。

#### 模型

Claude Code 使用 Claude 模型来理解您的代码并推理任务。

- Sonnet 可以很好地处理大多数编码任务。
- Opus 为复杂的架构决策提供更强的推理能力。

#### 工具

工具是使 Claude Code 成为代理的原因。
没有工具，Claude 只能用文本回应。
有了工具，Claude 可以采取行动：读取您的代码、编辑文件、运行命令、搜索网络并与外部服务交互。
每个工具使用都会返回信息，反馈到循环中，告知 Claude 的下一个决定。

LLM 不直接操作文件系统或执行命令。它通过返回结构化的 tool_use 块告诉 Claude Code 要做什么：

// LLM 返回
{"type": "tool_use", "name": "Read", "input": {"file_path": "/path/to/file.ts"}}

// Claude Code 本地执行后返回
{"type": "tool_result", "tool_use_id": "...", "content": "文件内容..."}

内置工具通常分为五类

| 类别 | Claude 可以做什么 |
| --- | --- |
| 文件操作 | 读取文件、编辑代码、创建新文件、重命名和重新组织 |
| 搜索 | 按模式查找文件、使用正则表达式搜索内容、探索代码库 |
| 执行 | 运行 shell 命令、启动服务器、运行测试、使用 git |
| 网络 | 搜索网络、获取文档、查找错误消息 |
| 代码智能 | 编辑后查看类型错误和警告、跳转到定义、查找引用（需要代码智能插件） |

这些是主要功能。Claude 还有用于生成 subagents、询问您问题和其他编排任务的工具。
https://code.claude.com/docs/en/settings#tools-available-to-claude

Claude 根据您的提示和沿途学到的内容选择使用哪些工具。
每个工具使用都给 Claude 新信息，告知下一步。这就是代理循环的实际应用。

扩展基本功能： 内置工具是基础。您可以使用 skills 扩展 Claude 知道的内容、使用 MCP 连接到外部服务、使用 hooks 自动化工作流，以及使用 subagents 卸载任务。这些扩展形成了核心代理循环之上的一层。
