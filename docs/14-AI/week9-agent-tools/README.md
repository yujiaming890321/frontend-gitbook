# Week 9: Agent 工具与循环

> 目标：让 LLM 学会使用工具，实现 ReAct 循环，构建能自主完成任务的 Agent

## 学习安排

| 天 | 文件 | 内容 | 时间 |
|---|------|------|------|
| Day 1 | `day1_tool_functions.py` | 定义工具函数：文件读取、文本搜索 | 30min |
| Day 2 | `day2_tool_calling.py` | Tool Calling：让 LLM 决定调用哪个工具 | 30min |
| Day 3 | `day3_react_loop.py` | ReAct 循环：Think → Call Tool → Observe → Think again | 45min |
| Day 4 | `day4_max_iterations.py` | 添加最大迭代次数限制，防止死循环 | 30min |
| Day 5 | `day5_rag_as_tool.py` | 把 RAG 集成为 Agent 工具 | 45min |
| Day 6-7 | `day67_research_agent.py` | 综合：能搜文档 + 生成摘要的 Research Agent | 60min |

## 环境准备

```bash
cd docs/14-AI/week9-agent-tools
python -m venv .venv && source .venv/bin/activate
pip install langchain langchain-community langchain-chroma chromadb langgraph
pip install openai python-dotenv

# Ollama 模型
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

## 核心概念

```
Agent 的核心循环（类比前端概念）：

┌──────────────────┬──────────────────────────────┐
│ Agent 概念        │ 前端类比                      │
├──────────────────┼──────────────────────────────┤
│ Tool             │ API 端点 (REST endpoint)       │
│ Tool Calling     │ 动态 import / 路由分发          │
│ ReAct Loop       │ Redux Saga / 事件循环          │
│ Max Iterations   │ 请求超时 / 重试上限             │
│ Agent State      │ Redux Store / 状态管理          │
│ Observation      │ API Response                   │
└──────────────────┴──────────────────────────────┘
```
