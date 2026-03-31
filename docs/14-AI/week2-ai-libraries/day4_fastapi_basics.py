"""
Day 4: FastAPI 基础 — 写一个简单 API 服务
AI 开发中常用：把 LLM/RAG/Agent 包装成 HTTP API 供前端调用
你已经熟悉 Express，FastAPI 是 Python 版的 Express（但更强大）

启动方式:
  uvicorn day4_fastapi_basics:app --reload
  然后访问 http://localhost:8000/docs 查看自动生成的 API 文档
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
import json

# ============================================================
# 1. 创建应用
# JS/Express: const app = express()
# Python/FastAPI: app = FastAPI()
# ============================================================

app = FastAPI(
    title="AI Learning API",
    description="Week 2 练习 — FastAPI 基础",
    version="1.0.0",
)


# ============================================================
# 2. 基本路由
# JS: app.get("/", (req, res) => res.json({...}))
# Python: @app.get("/") async def root(): return {...}
# ============================================================

# GET — simplest route
@app.get("/")
async def root():
    """Root endpoint — health check"""
    return {"message": "Hello from FastAPI!", "status": "ok"}

# GET with path parameter
# JS: app.get("/users/:id", (req, res) => { const id = req.params.id })
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID — path parameter auto-validated as int"""
    return {"user_id": user_id, "name": f"User {user_id}"}

# GET with query parameters
# JS: app.get("/search", (req, res) => { const q = req.query.q })
@app.get("/search")
async def search(
    q: str = Query(description="Search keyword"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Search with query parameters — auto-validated"""
    return {
        "query": q,
        "limit": limit,
        "offset": offset,
        "results": [f"Result {i}" for i in range(offset, offset + limit)],
    }


# ============================================================
# 3. POST 请求和 Request Body
# JS: app.post("/chat", (req, res) => { const body = req.body })
# FastAPI 用 pydantic 自动校验 request body
# ============================================================

class ChatRequest(BaseModel):
    """Request body — auto-validated by pydantic"""
    message: str = Field(min_length=1, description="User message")
    model: str = Field(default="qwen2.5:7b")
    temperature: float = Field(default=0.7, ge=0, le=2)

class ChatResponse(BaseModel):
    """Response model — also generates API docs"""
    reply: str
    model: str
    tokens_used: int

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint — simulate LLM response.
    FastAPI auto-validates request body using pydantic model.
    """
    # Simulate LLM processing
    reply = f"[{request.model}] 收到消息: {request.message}"
    return ChatResponse(
        reply=reply,
        model=request.model,
        tokens_used=len(request.message) * 2,
    )


# ============================================================
# 4. 错误处理
# JS: res.status(404).json({error: "Not found"})
# Python: raise HTTPException(status_code=404)
# ============================================================

FAKE_DB = {
    1: {"id": 1, "name": "RAG 入门", "content": "RAG 是检索增强生成..."},
    2: {"id": 2, "name": "Agent 实战", "content": "Agent 是自主决策..."},
}

@app.get("/docs/{doc_id}")
async def get_document(doc_id: int):
    """Get document by ID — returns 404 if not found"""
    doc = FAKE_DB.get(doc_id)
    if not doc:
        # Like Express: res.status(404).json({...})
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return doc


# ============================================================
# 5. 流式响应 (SSE) — AI 应用的核心
# 让前端实现打字机效果
# ============================================================

class StreamRequest(BaseModel):
    prompt: str

@app.post("/stream")
async def stream_chat(request: StreamRequest):
    """Stream response using Server-Sent Events (SSE)"""

    async def generate():
        """Async generator that yields SSE-formatted chunks"""
        words = f"这是对「{request.prompt}」的回复，正在流式输出中。"
        for char in words:
            # SSE format: data: {...}\n\n
            chunk = json.dumps({"content": char, "done": False}, ensure_ascii=False)
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.05)
        # Send final chunk
        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============================================================
# 6. 中间件 (Middleware)
# JS: app.use((req, res, next) => {...})
# Python: @app.middleware("http")
# ============================================================

import time

@app.middleware("http")
async def add_timing_header(request, call_next):
    """Add X-Process-Time header to every response"""
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response


# ============================================================
# 7. Express vs FastAPI 对比速查表
# ============================================================

"""
Express                              FastAPI                         说明
───────                              ───────                         ────
const app = express()                app = FastAPI()                  创建应用
app.get("/", handler)                @app.get("/")                    GET 路由
app.post("/", handler)               @app.post("/")                   POST 路由
req.params.id                        path parameter (auto)            路径参数
req.query.q                          Query(...)                       查询参数
req.body                             Pydantic BaseModel               请求体
res.json({...})                      return {...}                     返回 JSON
res.status(404).json(...)            raise HTTPException(404)         错误响应
app.use(middleware)                  @app.middleware("http")           中间件
Swagger (手动配)                     /docs (自动生成!)                  API 文档
express.static("public")            StaticFiles                      静态文件
nodemon                              uvicorn --reload                 热重载

FastAPI 的独特优势：
- 自动生成 OpenAPI 文档（/docs）
- 请求/响应自动校验（pydantic）
- 原生 async 支持
- 性能极高（Starlette + Uvicorn）
"""


# ============================================================
# 练习题
# ============================================================

# TODO 1: 添加一个 PUT /docs/{doc_id} 端点
# 用 pydantic 定义 UpdateDocRequest(name, content)
# 如果文档不存在返回 404，否则更新 FAKE_DB 并返回更新后的文档

# TODO 2: 添加一个 POST /batch-chat 端点
# 接收 messages: list[str]，并发处理所有消息
# 返回 [{"message": "原始消息", "reply": "回复"}, ...]
# 提示：用 asyncio.gather

# TODO 3: 添加 CORS 中间件
# 让前端 React 项目能跨域调用这个 API
# 提示：from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# 启动说明（不直接运行，需要用 uvicorn）
# ============================================================

if __name__ == "__main__":
    print("""
FastAPI 启动方式:
  uvicorn day4_fastapi_basics:app --reload --port 8000

然后:
  1. 访问 http://localhost:8000/docs 查看 API 文档（自动生成！）
  2. 在文档页面直接测试各个接口
  3. 或用 curl/httpx 调用:
     curl http://localhost:8000/
     curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "你好"}'
""")
