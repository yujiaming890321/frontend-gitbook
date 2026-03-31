"""
Day 2: SSE 流式输出 — 让 RAG 回答一个字一个字地返回

为什么需要流式输出？
- LLM 生成回答可能需要 5-30 秒，用户看到空白页会焦虑
- 流式输出让用户立即看到第一个字，体验像 ChatGPT 一样
- 技术方案: Server-Sent Events (SSE)，比 WebSocket 简单，单向就够用

JS 对比:
  前端 EventSource   ≈  Python SSE client
  Express res.write() ≈  FastAPI StreamingResponse
  ReadableStream     ≈  Python async generator

用法:
  python day2_sse_streaming.py
  # 测试流式输出:
  curl -N http://localhost:8000/ask/stream -H "Content-Type: application/json" -d '{"question": "什么是 React?"}'
"""

import json
import time
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_chroma import Chroma


# ============================================================
# 1. Configuration (same as Day 1)
# ============================================================

CHROMA_DIR = "/tmp/chroma_gitbook"
COLLECTION_NAME = "gitbook_docs"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5:7b"
TOP_K = 3


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(None, ge=1, le=10)


# ============================================================
# 2. Async Generator — the core of SSE streaming
# Python async generator ≈ JS async function* / ReadableStream
# yield produces values one at a time instead of returning all at once
# ============================================================

async def stream_rag_response(question: str, top_k: int = 3) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE events as the LLM generates tokens.

    SSE format (each event):
      data: {"type": "token", "content": "some text"}\n\n

    Event types:
      - sources:  retrieved document sources (sent first)
      - token:    a chunk of the LLM response
      - done:     signal that generation is complete
      - error:    something went wrong
    """
    try:
        # Step 1: Retrieve relevant chunks
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )

        results = vectorstore.similarity_search_with_score(question, k=top_k)

        if not results:
            yield _sse_event("error", {"message": "No relevant documents found"})
            return

        # Step 2: Send source information first so frontend can display it
        sources = []
        context_parts = []
        for doc, score in results:
            source_name = Path(doc.metadata.get("source", "unknown")).name
            sources.append({
                "source": source_name,
                "score": round(float(score), 4),
                "preview": doc.page_content[:100],
            })
            context_parts.append(f"[source: {source_name}]\n{doc.page_content}")

        # Send sources event before streaming tokens
        yield _sse_event("sources", {"sources": sources})

        context = "\n\n---\n\n".join(context_parts)

        # Step 3: Stream LLM response token by token
        prompt = f"""Based on the following reference materials, answer the question.
If the information is not available, say so. Cite your sources.

Reference materials:
{context}

Question: {question}

Answer:"""

        llm = Ollama(model=LLM_MODEL)

        # Use .stream() instead of .invoke() to get token-by-token output
        # This is like switching from fetch().then(res => res.json())
        # to fetch().then(res => res.body.getReader())
        token_count = 0
        async for chunk in llm.astream(prompt):
            token_count += 1
            yield _sse_event("token", {"content": chunk})

        # Step 4: Send completion signal
        yield _sse_event("done", {"token_count": token_count})

    except Exception as e:
        yield _sse_event("error", {"message": str(e)})


def _sse_event(event_type: str, data: dict) -> str:
    """
    Format a Server-Sent Event string.

    SSE protocol format:
      event: <type>\n
      data: <json>\n
      \n

    In JS you'd receive this via EventSource:
      const es = new EventSource('/ask/stream');
      es.addEventListener('token', (e) => { console.log(JSON.parse(e.data)); });
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


# ============================================================
# 3. Alternative: Simple line-by-line streaming without SSE events
# Simpler but less structured — just streams raw text
# ============================================================

async def stream_simple(question: str) -> AsyncGenerator[str, None]:
    """
    Simpler streaming approach: just yield text chunks.
    Frontend uses fetch + ReadableStream to read them.

    This is the approach ChatGPT's API uses (without event types).
    """
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )

    results = vectorstore.similarity_search_with_score(question, k=TOP_K)
    if not results:
        yield "No relevant documents found."
        return

    context_parts = [doc.page_content for doc, _ in results]
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""Based on the following reference materials, answer the question.

Reference materials:
{context}

Question: {question}

Answer:"""

    llm = Ollama(model=LLM_MODEL)
    async for chunk in llm.astream(prompt):
        yield chunk


# ============================================================
# 4. FastAPI with SSE endpoints
# ============================================================

app = FastAPI(title="RAG Streaming API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "streaming": True}


@app.post("/ask/stream")
async def ask_stream(request: AskRequest):
    """
    SSE streaming endpoint with structured events.

    Returns a stream of SSE events:
    1. event: sources  — which documents were found
    2. event: token    — each text chunk from the LLM (repeated)
    3. event: done     — generation complete

    Frontend usage:
      const response = await fetch('/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: '...' })
      });
      const reader = response.body.getReader();
    """
    top_k = request.top_k or TOP_K
    return StreamingResponse(
        stream_rag_response(request.question, top_k),
        media_type="text/event-stream",
        headers={
            # Prevent proxy/nginx from buffering the stream
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/ask/stream/simple")
async def ask_stream_simple(request: AskRequest):
    """
    Simple streaming endpoint — just raw text chunks.
    Easier to consume but no structured events.
    """
    return StreamingResponse(
        stream_simple(request.question),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"},
    )


# ============================================================
# 5. Demo: How SSE works (standalone test)
# ============================================================

async def demo_sse_generator() -> AsyncGenerator[str, None]:
    """
    Demo generator that simulates streaming without needing Ollama.
    Useful for testing the frontend connection.
    """
    # Send sources
    yield _sse_event("sources", {
        "sources": [
            {"source": "react-hooks.md", "score": 0.85, "preview": "React Hooks let you use state..."},
            {"source": "react-basics.md", "score": 0.72, "preview": "React is a JavaScript library..."},
        ]
    })

    # Simulate token-by-token generation
    demo_answer = "React Hooks are functions that let you use state and other React features in functional components. The most common hooks are useState and useEffect."
    words = demo_answer.split(" ")
    for word in words:
        yield _sse_event("token", {"content": word + " "})
        await asyncio.sleep(0.05)  # Simulate generation delay

    yield _sse_event("done", {"token_count": len(words)})


@app.get("/ask/demo")
async def ask_demo():
    """
    Demo endpoint that streams a fake response.
    No Ollama needed — useful for testing the frontend.

    Test: curl -N http://localhost:8000/ask/demo
    """
    return StreamingResponse(
        demo_sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting RAG Streaming API server...")
    print("Demo:    curl -N http://localhost:8000/ask/demo")
    print("Swagger: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================
# 练习题
# ============================================================

# TODO 1: 添加 "thinking" 事件
# 在检索和生成之间，发送一个 thinking 事件告诉前端 "正在检索..."
# yield _sse_event("thinking", {"message": "正在检索相关文档..."})

# TODO 2: 实现超时机制
# 如果 LLM 生成超过 60 秒，发送 error 事件并停止
# 提示: 用 asyncio.wait_for() 或 asyncio.timeout()

# TODO 3: 实现流式输出的速率统计
# 在 done 事件中加入 tokens_per_second 字段
# 提示: 记录开始时间，计算 token_count / elapsed_seconds

# TODO 4: 用 sse-starlette 库重写 SSE
# 对比 StreamingResponse 和 sse-starlette 的 EventSourceResponse
# sse-starlette 提供更标准的 SSE 实现
