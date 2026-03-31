"""
Day 5-7: 综合练习 — 用 FastAPI 写一个完整的 REST API

这个项目综合运用本周所有知识点：
- Day 1: httpx（调用外部 API）
- Day 2: pydantic（数据校验）
- Day 3: dotenv + JSON（配置管理）
- Day 4: FastAPI（路由、中间件、SSE）

项目：AI 文档管理 API
功能：文档 CRUD + 关键词搜索 + 模拟 LLM 问答

启动方式:
  uvicorn day57_fastapi_rest_api:app --reload --port 8000
  访问 http://localhost:8000/docs 查看 API 文档
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pathlib import Path
import asyncio
import json
import uuid


# ============================================================
# Day 3: 配置管理
# ============================================================

class AppSettings(BaseModel):
    """Application settings loaded from environment"""
    app_name: str = "AI Doc Manager"
    llm_model: str = "qwen2.5:7b"
    llm_temperature: float = 0.7
    max_results: int = 10

settings = AppSettings()


# ============================================================
# Day 2: Pydantic 模型定义
# ============================================================

class Document(BaseModel):
    """Document stored in the system"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class CreateDocRequest(BaseModel):
    """Request body for creating a document"""
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)

class UpdateDocRequest(BaseModel):
    """Request body for updating a document — all fields optional"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    tags: Optional[list[str]] = None

class ChatRequest(BaseModel):
    """Request for AI chat about documents"""
    question: str = Field(min_length=1)
    doc_ids: Optional[list[str]] = None  # Limit search to specific docs

class ChatResponse(BaseModel):
    """Response from AI chat"""
    answer: str
    sources: list[str]  # Document IDs used for the answer
    tokens_used: int


# ============================================================
# In-memory database (replaced by real DB in production)
# ============================================================

db: dict[str, Document] = {}

# Seed with sample data
for title, content, tags in [
    ("RAG 入门", "RAG（检索增强生成）是一种将检索和生成结合的技术。它先从知识库中检索相关文档，再将文档作为上下文传给 LLM 生成回答。", ["ai", "rag"]),
    ("Agent 基础", "AI Agent 是能自主决策和使用工具的系统。它通过 ReAct 循环（思考→行动→观察）来完成复杂任务。", ["ai", "agent"]),
    ("Prompt Engineering", "Prompt Engineering 是设计和优化 LLM 输入提示的技术。包括 system prompt、few-shot、CoT 等策略。", ["ai", "prompt"]),
]:
    doc = Document(title=title, content=content, tags=tags)
    db[doc.id] = doc


# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(
    title=settings.app_name,
    description="AI 文档管理 API — Week 2 综合练习",
    version="1.0.0",
)

# Day 4: CORS middleware — allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CRUD 路由
# ============================================================

@app.get("/docs", response_model=list[Document])
async def list_documents(
    tag: Optional[str] = Query(default=None, description="Filter by tag"),
    q: Optional[str] = Query(default=None, description="Search in title and content"),
    limit: int = Query(default=10, ge=1, le=100),
):
    """List all documents with optional filtering"""
    results = list(db.values())

    # Filter by tag
    if tag:
        results = [d for d in results if tag in d.tags]

    # Search by keyword in title and content
    if q:
        q_lower = q.lower()
        results = [d for d in results if q_lower in d.title.lower() or q_lower in d.content.lower()]

    # Sort by updated_at descending and apply limit
    results.sort(key=lambda d: d.updated_at, reverse=True)
    return results[:limit]


@app.get("/docs/{doc_id}", response_model=Document)
async def get_document(doc_id: str):
    """Get a single document by ID"""
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return doc


@app.post("/docs", response_model=Document, status_code=201)
async def create_document(request: CreateDocRequest):
    """Create a new document"""
    doc = Document(
        title=request.title,
        content=request.content,
        tags=request.tags,
    )
    db[doc.id] = doc
    return doc


@app.put("/docs/{doc_id}", response_model=Document)
async def update_document(doc_id: str, request: UpdateDocRequest):
    """Update an existing document — only provided fields are changed"""
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # Only update fields that were provided (partial update)
    if request.title is not None:
        doc.title = request.title
    if request.content is not None:
        doc.content = request.content
    if request.tags is not None:
        doc.tags = request.tags

    doc.updated_at = datetime.now()
    return doc


@app.delete("/docs/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    if doc_id not in db:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    del db[doc_id]
    return {"message": f"Document {doc_id} deleted"}


# ============================================================
# AI 问答路由 — 模拟 RAG
# ============================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Answer questions based on stored documents.
    Simulates a simple RAG pipeline: search → context → answer.
    """
    # Step 1: Search relevant documents
    q_lower = request.question.lower()
    candidates = list(db.values())
    if request.doc_ids:
        candidates = [d for d in candidates if d.id in request.doc_ids]

    # Simple keyword matching (real RAG uses vector similarity)
    relevant = [d for d in candidates if any(
        word in d.content.lower() or word in d.title.lower()
        for word in q_lower.split() if len(word) > 1
    )]

    if not relevant:
        return ChatResponse(
            answer="根据现有文档无法回答这个问题。",
            sources=[],
            tokens_used=0,
        )

    # Step 2: Build context from relevant docs
    context = "\n\n".join(f"[{d.title}]: {d.content}" for d in relevant[:3])

    # Step 3: Generate answer (simulated)
    answer = f"根据文档内容：{relevant[0].content[:100]}..."

    return ChatResponse(
        answer=answer,
        sources=[d.id for d in relevant[:3]],
        tokens_used=len(context) + len(request.question),
    )


@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat response using SSE — for typing effect in frontend"""

    async def generate():
        # Search relevant docs (same as above)
        relevant = [d for d in db.values() if any(
            word in d.content.lower()
            for word in request.question.lower().split() if len(word) > 1
        )]
        answer = relevant[0].content if relevant else "根据现有文档无法回答。"

        # Stream character by character
        for char in answer:
            data = json.dumps({"content": char, "done": False}, ensure_ascii=False)
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.03)

        # Final message with metadata
        final = json.dumps({
            "content": "",
            "done": True,
            "sources": [d.id for d in relevant[:3]],
        }, ensure_ascii=False)
        yield f"data: {final}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================================
# 统计路由
# ============================================================

@app.get("/stats")
async def get_stats():
    """Get statistics about stored documents"""
    docs = list(db.values())
    all_tags = [tag for d in docs for tag in d.tags]
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {
        "total_documents": len(docs),
        "total_characters": sum(len(d.content) for d in docs),
        "tags": tag_counts,
        "avg_content_length": sum(len(d.content) for d in docs) / max(len(docs), 1),
    }


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    print("""
启动方式:
  uvicorn day57_fastapi_rest_api:app --reload --port 8000

然后:
  1. 访问 http://localhost:8000/docs 查看 Swagger API 文档
  2. 测试 CRUD:
     curl http://localhost:8000/docs
     curl -X POST http://localhost:8000/docs -H "Content-Type: application/json" \\
       -d '{"title": "测试", "content": "测试内容", "tags": ["test"]}'
  3. 测试问答:
     curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \\
       -d '{"question": "什么是 RAG"}'
  4. 测试流式:
     curl -X POST http://localhost:8000/chat/stream -H "Content-Type: application/json" \\
       -d '{"question": "什么是 Agent"}'
""")


# ============================================================
# 扩展练习
# ============================================================

# TODO 1: 添加分页支持
# GET /docs?page=1&page_size=10
# 返回 { "items": [...], "total": 100, "page": 1, "pages": 10 }

# TODO 2: 用 httpx.AsyncClient 替换模拟的 LLM 调用
# 实际调用 Ollama API 来生成回答

# TODO 3: 添加文档导入功能
# POST /docs/import — 接收一个 Markdown 文件路径
# 读取文件内容，自动切分成多个文档存入 db

# TODO 4: 添加认证中间件
# 用 API Key 认证：请求头中必须包含 X-API-Key
# 提示：from fastapi.security import APIKeyHeader
