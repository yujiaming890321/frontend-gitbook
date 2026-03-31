# Week 10: 完整 Agent 项目

> 目标：构建一个功能完整的 Agent 项目，包含多工具、错误处理、记忆、API 和 UI

## 学习安排

| 天 | 文件 | 内容 | 时间 |
|---|------|------|------|
| Day 1 | `day1_multi_tools.py` | 添加多种工具：文件读写、网页摘要、代码执行 | 45min |
| Day 2 | `day2_error_handling.py` | 错误处理：工具失败时的重试和回退 | 30min |
| Day 3 | `day3_conversation_memory.py` | Agent 的对话记忆管理 | 30min |
| Day 4 | `day4_fastapi_agent.py` | 把 Agent 包装成 FastAPI API | 45min |
| Day 5 | `day5_react_agent_ui/index.html` | React UI 展示 Agent 思考过程（CDN React，单 HTML） | 60min |
| Day 6-7 | `day67_full_project.py` | 完整项目整合 + README 模板 | 60min |

## 环境准备

```bash
cd docs/14-AI/week10-agent-project
python -m venv .venv && source .venv/bin/activate
pip install langchain langchain-community langchain-chroma chromadb langgraph
pip install fastapi uvicorn openai python-dotenv httpx
pip install beautifulsoup4

# Ollama 模型
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

## 项目架构

```
完整 Agent 项目架构：

┌─────────────────────────────────────────────┐
│                  React UI                    │
│        (展示思考过程 + 对话界面)               │
├─────────────────────────────────────────────┤
│               FastAPI Server                 │
│        (HTTP API + SSE streaming)            │
├─────────────────────────────────────────────┤
│              Agent Core (LangGraph)          │
│   ┌─────────┐  ┌──────────┐  ┌──────────┐  │
│   │ 多工具   │  │ 错误处理  │  │ 对话记忆  │  │
│   │ 管理器   │  │ 重试回退  │  │ 管理器    │  │
│   └─────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│     Ollama (LLM)    │    Chroma (RAG)       │
└─────────────────────────────────────────────┘
```
