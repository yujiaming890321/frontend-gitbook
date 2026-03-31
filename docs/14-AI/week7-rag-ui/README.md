# Week 7: RAG UI -- 给 RAG 系统加上 Web 界面

> 目标：用 FastAPI 封装 RAG 后端，用 React 搭建聊天 UI，实现流式输出和来源引用

## 学习安排

| 天 | 文件 | 内容 | 时间 |
|---|------|------|------|
| Day 1 | `day1_fastapi_wrap.py` | 用 FastAPI 封装 RAG pipeline (POST /ask, GET /docs, POST /index) | 40min |
| Day 2 | `day2_sse_streaming.py` | SSE 流式输出 (StreamingResponse, async generator) | 40min |
| Day 3 | `day3_react_chat_ui/index.html` | React 聊天界面，调用 FastAPI 后端 | 45min |
| Day 4 | `day4_stream_frontend/index.html` | 前端接入流式输出 (EventSource / ReadableStream) | 45min |
| Day 5 | `day5_source_citation/index.html` | 展示来源引用（哪些文档被用到了） | 40min |
| Day 6-7 | `day67_polish.py` | 完整集成：CORS、健康检查、错误处理、部署笔记 | 60min |

## 环境准备

```bash
cd docs/14-AI/week7-rag-ui
python -m venv .venv && source .venv/bin/activate

# 后端依赖
pip install fastapi uvicorn langchain langchain-community langchain-chroma chromadb
pip install openai python-dotenv sse-starlette

# Ollama 模型（如已有可跳过）
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

## 如何使用

```bash
# 1. 先确保 Week 5-6 的知识库已构建（或用 Day 1 的 /index 接口重新构建）

# 2. 启动后端
python day1_fastapi_wrap.py
# 或
uvicorn day1_fastapi_wrap:app --reload --port 8000

# 3. 打开前端
# 直接在浏览器打开 day3_react_chat_ui/index.html
# 或用 Python 起一个简单 HTTP 服务：
python -m http.server 3000

# 4. 每个文件中有 TODO 标记的地方是练习题
```

## 架构说明

```
前端 (React CDN)          后端 (FastAPI)           AI (Ollama + Chroma)
+-----------------+       +------------------+      +------------------+
| Chat UI         | ----> | POST /ask        | ---> | RAG Pipeline     |
| Stream Display  | <---- | GET  /ask/stream | <--- | Streaming LLM    |
| Source Citation  |       | GET  /docs       |      | Vector Search    |
| (index.html)    |       | POST /index      |      | (Chroma DB)      |
+-----------------+       +------------------+      +------------------+
```

## 为什么用 CDN React 而不是 create-react-app？

作为前端开发者，你已经熟悉 React 的构建工具链了。这里用 CDN 方式是为了：
1. 零配置，打开 HTML 就能跑
2. 聚焦在 AI 后端对接上，不用折腾前端工具
3. 实际项目中可以很容易迁移到 Next.js / Vite 等框架
