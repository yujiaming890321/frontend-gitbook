# Agent（AI 智能体）

Agent 是能够自主规划、使用工具、执行多步骤任务的 AI 系统。与简单的 LLM 调用不同，Agent 具备感知环境、做出决策、采取行动的能力。

## 核心概念

```
感知（Perception）→ 规划（Planning）→ 行动（Action）→ 观察（Observation）→ 循环
```

Agent 的本质是一个**决策循环**：LLM 作为"大脑"，根据当前状态决定下一步做什么。

## Agent 的核心组件

### 1. LLM（推理引擎）

Agent 的核心，负责理解任务、制定计划、决定使用哪个工具。

### 2. Tools（工具）

Agent 可以调用的外部能力：

- **搜索工具**：网络搜索、数据库查询
- **代码执行**：运行 Python/JS 代码
- **API 调用**：与外部服务交互
- **文件操作**：读写文件
- **浏览器操作**：网页浏览和交互

### 3. Memory（记忆）

- **短期记忆**：当前对话的上下文（Context Window）
- **长期记忆**：持久化存储的信息（向量数据库、文件）
- **工作记忆**：当前任务的中间状态和推理过程

### 4. Planning（规划）

Agent 如何分解和执行复杂任务：

- **任务分解**：将大任务拆解为子任务
- **反思与修正**：根据执行结果调整计划
- **回溯**：发现错误时回到之前的步骤

## 常见 Agent 架构

### ReAct（Reasoning + Acting）

最经典的 Agent 模式，交替进行推理和行动：

```
Thought: 我需要查找今天的天气
Action: search("今天北京天气")
Observation: 北京今天晴，25°C
Thought: 我已经获得了天气信息，可以回答了
Answer: 北京今天天气晴朗，气温25°C。
```

### Plan-and-Execute

先制定完整计划，再逐步执行：

```
Plan:
1. 搜索相关论文
2. 阅读并总结关键信息
3. 对比分析
4. 撰写报告

Execute: 按步骤逐一执行，每步可能调用不同工具
```

### Multi-Agent（多智能体协作）

多个专业化 Agent 协同工作：

```
Orchestrator（编排者）
  ├── Researcher Agent（研究）
  ├── Writer Agent（写作）
  ├── Reviewer Agent（审查）
  └── Coder Agent（编码）
```

## Tool Calling（工具调用）

现代 LLM 原生支持工具调用，通过 Function Calling 实现：

```json
{
  "name": "get_weather",
  "description": "获取指定城市的天气信息",
  "parameters": {
    "type": "object",
    "properties": {
      "city": { "type": "string", "description": "城市名" }
    },
    "required": ["city"]
  }
}
```

LLM 会根据用户意图决定是否调用工具、传入什么参数。

## Agent 框架

| 框架 | 特点 |
|------|------|
| **LangGraph** | 基于图的状态机，灵活控制流程 |
| **CrewAI** | 多 Agent 协作框架 |
| **AutoGen** | 微软出品，多 Agent 对话 |
| **Claude Code** | Anthropic 的编码 Agent |
| **OpenAI Agents SDK** | OpenAI 官方 Agent 框架 |

## Agent vs Workflow

| | Agent | Workflow |
|---|---|---|
| **控制流** | LLM 动态决定 | 预定义路径 |
| **灵活性** | 高，可应对意外情况 | 低，固定步骤 |
| **可预测性** | 低 | 高 |
| **调试难度** | 难 | 易 |
| **适用场景** | 开放式探索任务 | 结构化重复任务 |

## 设计原则

1. **最小权限**：只给 Agent 必要的工具和权限
2. **人在回路（Human-in-the-loop）**：关键决策让人确认
3. **失败安全**：设置最大迭代次数、超时机制
4. **可观测性**：记录每一步的推理和行动，便于调试
5. **渐进式复杂度**：从简单 Workflow 开始，只在需要时引入 Agent
