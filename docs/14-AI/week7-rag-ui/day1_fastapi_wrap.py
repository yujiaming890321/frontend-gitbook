"""
Day 1: 用 FastAPI 封装 RAG Pipeline
把 Week 5 的 RAG pipeline 包装成 HTTP API，前端可以直接调用

接口设计:
  POST /ask          提问并返回 RAG 回答
  GET  /docs         查看已索引的文档列表
  POST /index        触发重新索引文档
  GET  /health       健康检查

用法:
  python day1_fastapi_wrap.py
  # 或
  uvicorn day1_fastapi_wrap:app --reload --port 8000

测试:
  curl http://localhost:8000/health
  curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "什么是 React hooks?"}'
  curl http://localhost:8000/docs
"""

import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_chroma import Chroma
from langchain_core.documents import Document


# ============================================================
# 1. Configuration
# ============================================================

@dataclass
class RAGConfig:
    """RAG pipeline configuration, reuse from Week 5"""
    docs_dir: str = "../../"
    chroma_dir: str = "/tmp/chroma_gitbook"
    collection_name: str = "gitbook_docs"
    embedding_model: str = "nomic-embed-text"
    llm_model: str = "qwen2.5:7b"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3


config = RAGConfig()


# ============================================================
# 2. Pydantic Models — API request/response schemas
# JS/TS 对应: interface AskRequest { question: string }
# FastAPI uses Pydantic for auto-validation + Swagger docs
# ============================================================

class AskRequest(BaseModel):
    """Request body for /ask endpoint"""
    question: str = Field(..., min_length=1, max_length=1000, description="The question to ask")
    top_k: Optional[int] = Field(None, ge=1, le=10, description="Number of source chunks to retrieve")


class SourceInfo(BaseModel):
    """A single source document that contributed to the answer"""
    source: str
    score: float
    preview: str


class AskResponse(BaseModel):
    """Response body for /ask endpoint"""
    answer: str
    sources: list[SourceInfo]
    chunks_used: int
    context_length: int
    elapsed_ms: int


class DocsResponse(BaseModel):
    """Response body for /docs endpoint"""
    total_chunks: int
    collection_name: str
    sample_sources: list[str]


class IndexRequest(BaseModel):
    """Request body for /index endpoint"""
    docs_dir: Optional[str] = Field(None, description="Override docs directory path")


class IndexResponse(BaseModel):
    """Response body for /index endpoint"""
    docs_loaded: int
    chunks_created: int
    elapsed_ms: int


# ============================================================
# 3. RAG Core Functions — same logic as Week 5 day67
# ============================================================

def get_embeddings() -> OllamaEmbeddings:
    """Create embeddings instance"""
    return OllamaEmbeddings(model=config.embedding_model)


def get_vectorstore() -> Chroma:
    """Load existing vector store from disk"""
    return Chroma(
        persist_directory=config.chroma_dir,
        embedding_function=get_embeddings(),
        collection_name=config.collection_name,
    )


def build_index(docs_dir: str) -> dict:
    """
    Build the vector index from markdown files.
    Returns stats about the indexing process.
    """
    docs_path = Path(docs_dir).resolve()
    if not docs_path.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_path}")

    # Load documents
    loader = DirectoryLoader(
        str(docs_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()

    if not docs:
        raise ValueError("No markdown files found in directory")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    # Add chunk index to metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    # Build vector store
    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=config.chroma_dir,
        collection_name=config.collection_name,
    )

    return {"docs_loaded": len(docs), "chunks_created": len(chunks)}


def rag_query(question: str, top_k: int = 3) -> dict:
    """
    Full RAG query: retrieve relevant chunks, build context, ask LLM.
    Same logic as Week 5 but returns a structured dict.
    """
    vectorstore = get_vectorstore()

    # Retrieve relevant chunks by similarity search
    results = vectorstore.similarity_search_with_score(question, k=top_k)

    if not results:
        return {"answer": "No relevant documents found.", "sources": [], "chunks_used": 0, "context_length": 0}

    # Build context from retrieved chunks
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

    # Build prompt and call LLM
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
        answer = f"[LLM call failed: {e}]"

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(results),
        "context_length": len(context),
    }


# ============================================================
# 4. FastAPI Application
# JS 对应: Express app
# app = FastAPI()  ≈  const app = express()
# @app.get("/")    ≈  app.get("/", handler)
# ============================================================

app = FastAPI(
    title="RAG API",
    description="RAG pipeline wrapped as HTTP API for frontend consumption",
    version="1.0.0",
)

# CORS middleware — allow frontend to call backend from different origin
# JS equivalent: app.use(cors({ origin: "*" }))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint, returns 200 if server is running"""
    return {"status": "ok", "model": config.llm_model}


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question and get a RAG-powered answer.
    The backend retrieves relevant document chunks and passes them to the LLM.
    """
    top_k = request.top_k or config.top_k

    start = time.time()
    try:
        result = rag_query(request.question, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")
    elapsed_ms = int((time.time() - start) * 1000)

    return AskResponse(
        answer=result["answer"],
        sources=[SourceInfo(**s) for s in result["sources"]],
        chunks_used=result["chunks_used"],
        context_length=result["context_length"],
        elapsed_ms=elapsed_ms,
    )


@app.get("/docs", response_model=DocsResponse)
async def list_docs():
    """
    List indexed documents in the vector store.
    Useful for the frontend to show what knowledge is available.
    """
    try:
        vectorstore = get_vectorstore()
        collection = vectorstore._collection
        count = collection.count()

        # Get a sample of unique source filenames
        sample = collection.peek(limit=20)
        source_set = set()
        if sample and "metadatas" in sample:
            for meta in sample["metadatas"]:
                if meta and "source" in meta:
                    source_set.add(Path(meta["source"]).name)

        return DocsResponse(
            total_chunks=count,
            collection_name=config.collection_name,
            sample_sources=sorted(source_set),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list docs: {str(e)}")


@app.post("/index", response_model=IndexResponse)
async def reindex_docs(request: IndexRequest):
    """
    Trigger re-indexing of documents.
    This rebuilds the vector store from scratch.
    """
    docs_dir = request.docs_dir or config.docs_dir

    start = time.time()
    try:
        result = build_index(docs_dir)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")
    elapsed_ms = int((time.time() - start) * 1000)

    return IndexResponse(
        docs_loaded=result["docs_loaded"],
        chunks_created=result["chunks_created"],
        elapsed_ms=elapsed_ms,
    )


# ============================================================
# 5. Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting RAG API server...")
    print("Swagger docs: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================
# 练习题
# ============================================================

# TODO 1: 添加 DELETE /docs 接口 — 清空向量数据库
# 提示: Chroma 有 delete_collection 方法

# TODO 2: 添加 GET /docs/search?q=keyword 接口 — 关键词搜索文档
# 提示: 用 vectorstore.similarity_search(query, k=5)

# TODO 3: 添加请求限流
# 提示: 使用 slowapi 库，限制每分钟最多 10 次 /ask 请求

# TODO 4: 把 RAGConfig 改成从环境变量 / .env 文件读取
# 提示: 使用 pydantic-settings 库的 BaseSettings
