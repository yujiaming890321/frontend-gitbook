"""
Day 6-7: 综合练习 — 完整集成 RAG Web 应用

把本周所有内容整合成一个生产就绪的 FastAPI 应用:
- Day 1: FastAPI 封装 RAG pipeline
- Day 2: SSE 流式输出
- Day 3-5: 前端对接 (直接用浏览器打开 HTML 文件)

新增内容:
- CORS 精细配置
- 健康检查 + 就绪检查
- 统一错误处理
- 请求日志中间件
- 静态文件服务（可选）
- 部署笔记

用法:
  python day67_polish.py
  # 或
  uvicorn day67_polish:app --reload --port 8000

  # 然后打开浏览器访问:
  # http://localhost:8000           → 前端页面 (如果启用静态文件)
  # http://localhost:8000/docs      → Swagger API 文档
  # http://localhost:8000/health    → 健康检查
  # http://localhost:8000/ready     → 就绪检查
"""

import json
import time
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_chroma import Chroma
from langchain_core.documents import Document


# ============================================================
# 1. Logging Setup
# JS equivalent: winston / pino logger
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rag-api")


# ============================================================
# 2. Configuration
# In production, use pydantic-settings to read from env vars
# ============================================================

@dataclass
class AppConfig:
    """Application configuration"""
    # RAG settings
    docs_dir: str = "../../"
    chroma_dir: str = "/tmp/chroma_gitbook"
    collection_name: str = "gitbook_docs"
    embedding_model: str = "nomic-embed-text"
    llm_model: str = "qwen2.5:7b"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: list[str] = None  # None = allow all

    # Feature flags
    serve_static: bool = True  # Serve frontend HTML files
    enable_demo: bool = True   # Enable demo endpoint (no Ollama needed)

    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ["*"]


config = AppConfig()


# ============================================================
# 3. Pydantic Models
# ============================================================

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(None, ge=1, le=10)


class SourceInfo(BaseModel):
    source: str
    score: float
    preview: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]
    chunks_used: int
    context_length: int
    elapsed_ms: int


class IndexRequest(BaseModel):
    docs_dir: Optional[str] = None


class IndexResponse(BaseModel):
    docs_loaded: int
    chunks_created: int
    elapsed_ms: int


class HealthResponse(BaseModel):
    status: str
    model: str
    uptime_seconds: int
    version: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int


# ============================================================
# 4. RAG Core — same logic, better error handling
# ============================================================

def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=config.embedding_model)


def get_vectorstore() -> Chroma:
    """Load vector store, raise clear error if not initialized"""
    chroma_path = Path(config.chroma_dir)
    if not chroma_path.exists():
        raise RuntimeError(
            "Vector store not initialized. "
            "Run POST /index first to build the knowledge base."
        )
    return Chroma(
        persist_directory=config.chroma_dir,
        embedding_function=get_embeddings(),
        collection_name=config.collection_name,
    )


def build_index(docs_dir: str) -> dict:
    """Build vector index from markdown files"""
    docs_path = Path(docs_dir).resolve()
    if not docs_path.exists():
        raise FileNotFoundError(f"Directory not found: {docs_path}")

    loader = DirectoryLoader(
        str(docs_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    if not docs:
        raise ValueError("No markdown files found")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=config.chroma_dir,
        collection_name=config.collection_name,
    )

    logger.info(f"Indexed {len(docs)} docs into {len(chunks)} chunks")
    return {"docs_loaded": len(docs), "chunks_created": len(chunks)}


def rag_query(question: str, top_k: int = 3) -> dict:
    """Full RAG query with source tracking"""
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_score(question, k=top_k)

    if not results:
        return {"answer": "No relevant documents found.", "sources": [], "chunks_used": 0, "context_length": 0}

    context_parts = []
    sources = []
    for doc, score in results:
        source_name = Path(doc.metadata.get("source", "unknown")).name
        context_parts.append(f"[source: {source_name}]\n{doc.page_content}")
        sources.append({
            "source": source_name,
            "score": float(score),
            "preview": doc.page_content[:100],
        })

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""Based on the following reference materials, answer the question.
If the information is not available, say so. Cite your sources.

Reference materials:
{context}

Question: {question}

Answer:"""

    llm = Ollama(model=config.llm_model)
    try:
        answer = llm.invoke(prompt)
    except Exception as e:
        answer = f"[LLM error: {e}]"

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(results),
        "context_length": len(context),
    }


# ============================================================
# 5. SSE Streaming
# ============================================================

def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


async def stream_rag_response(question: str, top_k: int = 3) -> AsyncGenerator[str, None]:
    """Stream RAG response as SSE events"""
    try:
        embeddings = get_embeddings()
        vectorstore = Chroma(
            persist_directory=config.chroma_dir,
            embedding_function=embeddings,
            collection_name=config.collection_name,
        )

        # Notify frontend that we're searching
        yield _sse_event("status", {"message": "Searching relevant documents..."})

        results = vectorstore.similarity_search_with_score(question, k=top_k)
        if not results:
            yield _sse_event("error", {"message": "No relevant documents found"})
            return

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

        yield _sse_event("sources", {"sources": sources})
        yield _sse_event("status", {"message": "Generating answer..."})

        context = "\n\n---\n\n".join(context_parts)
        prompt = f"""Based on the following reference materials, answer the question.
If the information is not available, say so. Cite your sources.

Reference materials:
{context}

Question: {question}

Answer:"""

        llm = Ollama(model=config.llm_model)
        token_count = 0
        start_time = time.time()

        async for chunk in llm.astream(prompt):
            token_count += 1
            yield _sse_event("token", {"content": chunk})

        elapsed = time.time() - start_time
        tokens_per_sec = token_count / elapsed if elapsed > 0 else 0
        yield _sse_event("done", {
            "token_count": token_count,
            "elapsed_seconds": round(elapsed, 2),
            "tokens_per_second": round(tokens_per_sec, 1),
        })

    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield _sse_event("error", {"message": str(e)})


async def demo_sse_generator() -> AsyncGenerator[str, None]:
    """Demo streaming without Ollama — for testing frontend"""
    yield _sse_event("sources", {
        "sources": [
            {"source": "react-hooks.md", "score": 0.85, "preview": "React Hooks let you use state and lifecycle features..."},
            {"source": "react-basics.md", "score": 0.72, "preview": "React is a JavaScript library for building UIs..."},
            {"source": "javascript-es6.md", "score": 0.91, "preview": "ES6 introduced arrow functions, destructuring..."},
        ]
    })

    demo_text = (
        "React Hooks are functions that let you use state and other React features "
        "in functional components without writing a class. The most commonly used hooks are:\n\n"
        "1. **useState** - for managing component state\n"
        "2. **useEffect** - for side effects (data fetching, subscriptions)\n"
        "3. **useContext** - for consuming context values\n"
        "4. **useRef** - for mutable references that persist across renders\n\n"
        "Hooks were introduced in React 16.8 and have largely replaced class components "
        "as the preferred way to write React code [source: react-hooks.md]."
    )

    words = demo_text.split(" ")
    for word in words:
        yield _sse_event("token", {"content": word + " "})
        await asyncio.sleep(0.03)

    yield _sse_event("done", {
        "token_count": len(words),
        "elapsed_seconds": round(len(words) * 0.03, 2),
        "tokens_per_second": round(1 / 0.03, 1),
    })


# ============================================================
# 6. Application Lifespan — startup/shutdown events
# JS equivalent: app.listen() callback + process.on('SIGTERM')
# ============================================================

# Track server start time for uptime reporting
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Code before yield runs on startup, after yield runs on shutdown.
    """
    # Startup
    logger.info("RAG API starting up...")
    logger.info(f"LLM model: {config.llm_model}")
    logger.info(f"Embedding model: {config.embedding_model}")
    logger.info(f"Chroma dir: {config.chroma_dir}")

    # Check if vector store exists
    if Path(config.chroma_dir).exists():
        logger.info("Vector store found, ready to serve queries")
    else:
        logger.warning("Vector store not found. Run POST /index to build it.")

    yield

    # Shutdown
    logger.info("RAG API shutting down...")


# ============================================================
# 7. FastAPI App with all middleware and error handlers
# ============================================================

app = FastAPI(
    title="RAG Web Application",
    description="Complete RAG system with streaming support and source citations",
    version="1.0.0",
    lifespan=lifespan,
)


# --- CORS Middleware ---
# In production, replace "*" with your actual frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# --- Request Logging Middleware ---
# Logs every request with method, path, status, and duration
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing information"""
    start = time.time()
    response = await call_next(request)
    elapsed_ms = int((time.time() - start) * 1000)

    logger.info(
        f"{request.method} {request.url.path} "
        f"-> {response.status_code} ({elapsed_ms}ms)"
    )
    return response


# --- Global Exception Handler ---
# Catch unhandled exceptions and return a clean JSON error
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return structured error response instead of raw 500 page"""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "status_code": 500,
        },
    )


# ============================================================
# 8. API Endpoints
# ============================================================

# --- Health Check ---
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check — always returns 200 if the server is running.
    Used by load balancers and monitoring tools.
    """
    return HealthResponse(
        status="ok",
        model=config.llm_model,
        uptime_seconds=int(time.time() - _start_time),
        version="1.0.0",
    )


# --- Readiness Check ---
@app.get("/ready")
async def readiness_check():
    """
    Readiness check — returns 200 only if the system is ready to serve.
    Unlike /health, this checks that dependencies (vector store, Ollama) are available.
    """
    errors = []

    # Check vector store
    if not Path(config.chroma_dir).exists():
        errors.append("Vector store not initialized (run POST /index)")

    # Check Ollama connectivity
    try:
        embeddings = get_embeddings()
        # Quick test embedding to verify Ollama is running
        embeddings.embed_query("test")
    except Exception as e:
        errors.append(f"Ollama not available: {e}")

    if errors:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "errors": errors},
        )

    return {"status": "ready"}


# --- Ask (non-streaming) ---
@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Ask a question and get a complete RAG answer"""
    top_k = request.top_k or config.top_k
    start = time.time()

    try:
        result = rag_query(request.question, top_k=top_k)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    elapsed_ms = int((time.time() - start) * 1000)
    logger.info(f"RAG query completed in {elapsed_ms}ms, {result['chunks_used']} chunks used")

    return AskResponse(
        answer=result["answer"],
        sources=[SourceInfo(**s) for s in result["sources"]],
        chunks_used=result["chunks_used"],
        context_length=result["context_length"],
        elapsed_ms=elapsed_ms,
    )


# --- Ask (streaming) ---
@app.post("/ask/stream")
async def ask_stream(request: AskRequest):
    """Stream a RAG answer as SSE events"""
    top_k = request.top_k or config.top_k
    return StreamingResponse(
        stream_rag_response(request.question, top_k),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Prevent nginx buffering
        },
    )


# --- Demo stream (no Ollama needed) ---
if config.enable_demo:
    @app.get("/ask/demo")
    async def ask_demo():
        """Demo streaming endpoint for testing frontend without Ollama"""
        return StreamingResponse(
            demo_sse_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )


# --- List indexed documents ---
@app.get("/docs")
async def list_docs():
    """List all indexed documents in the vector store"""
    try:
        vectorstore = get_vectorstore()
        collection = vectorstore._collection
        count = collection.count()

        sample = collection.peek(limit=50)
        source_set = set()
        if sample and "metadatas" in sample:
            for meta in sample["metadatas"]:
                if meta and "source" in meta:
                    source_set.add(Path(meta["source"]).name)

        return {
            "total_chunks": count,
            "collection_name": config.collection_name,
            "unique_sources": sorted(source_set),
            "source_count": len(source_set),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# --- Rebuild index ---
@app.post("/index", response_model=IndexResponse)
async def reindex_docs(request: IndexRequest):
    """Rebuild the vector index from markdown files"""
    docs_dir = request.docs_dir or config.docs_dir
    start = time.time()

    try:
        result = build_index(docs_dir)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    elapsed_ms = int((time.time() - start) * 1000)
    return IndexResponse(
        docs_loaded=result["docs_loaded"],
        chunks_created=result["chunks_created"],
        elapsed_ms=elapsed_ms,
    )


# --- Delete index ---
@app.delete("/docs")
async def delete_index():
    """Delete the entire vector store"""
    import shutil
    chroma_path = Path(config.chroma_dir)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)
        logger.info("Vector store deleted")
        return {"status": "deleted"}
    else:
        return {"status": "not_found", "message": "No vector store to delete"}


# ============================================================
# 9. Static File Serving (Optional)
# Serve the frontend HTML files from FastAPI
# ============================================================

if config.serve_static:
    # Mount the week7 directory so frontend files are accessible
    static_dir = Path(__file__).parent
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files served from {static_dir}")

    @app.get("/")
    async def serve_index():
        """Redirect to the Day 5 (most complete) UI"""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/static/day5_source_citation/index.html")


# ============================================================
# 10. Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print(f"""
============================================================
  RAG Web Application
============================================================

  Server:     http://localhost:{config.port}
  Swagger:    http://localhost:{config.port}/docs
  Health:     http://localhost:{config.port}/health
  Ready:      http://localhost:{config.port}/ready

  Frontend:   http://localhost:{config.port}/static/day5_source_citation/index.html
  Demo SSE:   curl -N http://localhost:{config.port}/ask/demo

  Note: If you see "Vector store not initialized", run:
    curl -X POST http://localhost:{config.port}/index

============================================================
""")

    uvicorn.run(
        "day67_polish:app",
        host=config.host,
        port=config.port,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info",
    )


# ============================================================
# 练习题
# ============================================================

# TODO 1: 添加认证
# 实现简单的 API Key 认证:
#   - 在 header 中传递 X-API-Key
#   - 用 FastAPI 的 Depends + Security 实现
#   - 没有 API Key 的请求返回 401
# 提示:
#   from fastapi.security import APIKeyHeader
#   api_key_header = APIKeyHeader(name="X-API-Key")

# TODO 2: 添加请求限流
# 限制每个 IP 每分钟最多 10 次 /ask 请求
# 推荐库: slowapi
# pip install slowapi
# from slowapi import Limiter
# limiter = Limiter(key_func=get_remote_address)

# TODO 3: Docker 部署
# 写一个 Dockerfile:
#   FROM python:3.11-slim
#   WORKDIR /app
#   COPY requirements.txt .
#   RUN pip install -r requirements.txt
#   COPY . .
#   CMD ["uvicorn", "day67_polish:app", "--host", "0.0.0.0", "--port", "8000"]
#
# 写一个 docker-compose.yml:
#   services:
#     rag-api:
#       build: .
#       ports: ["8000:8000"]
#       volumes: ["./chroma_data:/tmp/chroma_gitbook"]
#     ollama:
#       image: ollama/ollama
#       ports: ["11434:11434"]

# TODO 4: 添加对话历史
# 目前每次 /ask 都是独立的，没有上下文
# 实现方案:
#   - 前端传 conversation_id
#   - 后端用 dict 保存每个 conversation 的历史消息
#   - 在 prompt 中加入历史对话作为上下文
# 注意: 内存存储不适合生产，应该用 Redis 或数据库

# TODO 5: 前端部署到 Vercel / Netlify
# 把 day5_source_citation/index.html 中的 API_BASE
# 改成你后端的公网地址
# 然后把 HTML 文件部署到任意静态托管服务
