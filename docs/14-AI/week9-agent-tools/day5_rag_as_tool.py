"""
Day 5: 把 RAG 集成为 Agent 工具
让 Agent 可以通过工具调用来检索知识库，结合 Chroma 向量数据库
类比前端：RAG 工具就像一个内部搜索 API，Agent 通过它查询企业知识库
"""

import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import chromadb
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import from previous days
from day1_tool_functions import ToolResult, TOOL_REGISTRY, execute_tool, get_tools_description
from day3_react_loop import (
    ReActStep, ReActTrace, StepType, parse_react_output,
    REACT_SYSTEM_PROMPT, REACT_STEP_PROMPT,
)
from day4_max_iterations import GuardConfig, GuardState, GuardChecker


# ============================================================
# 1. RAG 作为工具的设计思路
# ============================================================

"""
RAG 作为 Agent 工具的架构：

┌──────────────────────────────────────────────────────┐
│                    Agent (ReAct Loop)                  │
│                                                        │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ read_file │  │ search_text  │  │ rag_search   │    │
│  │ (精确读取) │  │ (关键词搜索) │  │ (语义搜索)   │    │
│  └──────────┘  └──────────────┘  └──────┬───────┘    │
│                                          │             │
│                                    ┌─────▼─────┐      │
│                                    │ Chroma DB │      │
│                                    │ (向量库)   │      │
│                                    └───────────┘      │
└──────────────────────────────────────────────────────┘

类比前端：
- read_file  → 直接请求特定 API  (GET /api/docs/:id)
- search_text → 全文搜索         (GET /api/search?q=keyword)
- rag_search  → 语义搜索         (POST /api/semantic-search)

语义搜索的优势：
- "如何部署应用" 可以匹配到 "项目发布到生产环境的步骤"
- 关键词搜索做不到这种语义理解
"""


# ============================================================
# 2. 知识库管理器
# ============================================================

class KnowledgeBase:
    """
    Manages a Chroma vector store as a knowledge base.
    Can ingest documents and perform semantic search.
    """

    def __init__(
        self,
        collection_name: str = "agent_knowledge",
        embedding_model: str = "nomic-embed-text",
        persist_directory: Optional[str] = None,
    ):
        self.collection_name = collection_name

        # Initialize embedding model
        try:
            self.embeddings = OllamaEmbeddings(model=embedding_model)
            self._embedding_available = True
        except Exception:
            self._embedding_available = False
            print("[Warning] Ollama embeddings not available, using Chroma's default")

        # Initialize Chroma client
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()  # In-memory

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Agent knowledge base"},
        )

        # Text splitter for chunking documents
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )

    def ingest_text(self, text: str, source: str = "unknown", metadata: Optional[dict] = None) -> int:
        """
        Ingest a text document into the knowledge base.
        Splits into chunks and stores with embeddings.
        Returns number of chunks created.
        """
        chunks = self.splitter.split_text(text)

        if not chunks:
            return 0

        # Prepare data for Chroma
        ids = [f"{source}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {**(metadata or {}), "source": source, "chunk_index": i}
            for i in range(len(chunks))
        ]

        # Generate embeddings if available, otherwise let Chroma handle it
        if self._embedding_available:
            try:
                embeddings = self.embeddings.embed_documents(chunks)
                self.collection.add(
                    ids=ids,
                    documents=chunks,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
            except Exception:
                # Fall back to Chroma's built-in embedding
                self.collection.add(
                    ids=ids,
                    documents=chunks,
                    metadatas=metadatas,
                )
        else:
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
            )

        return len(chunks)

    def ingest_file(self, file_path: str) -> int:
        """Ingest a file into the knowledge base"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        return self.ingest_text(
            text=content,
            source=path.name,
            metadata={"file_path": str(path), "extension": path.suffix},
        )

    def ingest_directory(self, directory: str, extensions: list[str] = None) -> dict:
        """Ingest all matching files from a directory"""
        if extensions is None:
            extensions = [".md", ".txt", ".py"]

        dir_path = Path(directory)
        results = {"total_files": 0, "total_chunks": 0, "files": []}

        for ext in extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                # Skip hidden and build directories
                if any(p.startswith(".") or p in ("node_modules", "__pycache__") for p in file_path.parts):
                    continue
                try:
                    chunk_count = self.ingest_file(str(file_path))
                    results["total_files"] += 1
                    results["total_chunks"] += chunk_count
                    results["files"].append({
                        "path": str(file_path),
                        "chunks": chunk_count,
                    })
                except Exception as e:
                    print(f"  [Skip] {file_path}: {e}")

        return results

    def search(self, query: str, n_results: int = 5, source_filter: Optional[str] = None) -> list[dict]:
        """
        Perform semantic search in the knowledge base.
        Returns list of matching chunks with metadata.
        """
        # Build where filter if source is specified
        where_filter = None
        if source_filter:
            where_filter = {"source": source_filter}

        # Generate query embedding if available
        if self._embedding_available:
            try:
                query_embedding = self.embeddings.embed_query(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_filter,
                )
            except Exception:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter,
                )
        else:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )

        # Format results
        formatted = []
        if results and results["documents"]:
            for i, (doc, meta, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )):
                formatted.append({
                    "rank": i + 1,
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "distance": round(distance, 4),
                    "metadata": meta,
                })

        return formatted

    def get_stats(self) -> dict:
        """Get knowledge base statistics"""
        return {
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
            "embedding_available": self._embedding_available,
        }


# ============================================================
# 3. RAG 工具函数
# ============================================================

# Global knowledge base instance (initialized in main)
_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """Get or create the global knowledge base instance"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base


def rag_search(query: str, n_results: int = 5) -> ToolResult:
    """
    Search the knowledge base using semantic search.
    Returns the most relevant document chunks for the given query.
    Use this when you need to find information from ingested documents.
    """
    try:
        kb = get_knowledge_base()
        results = kb.search(query, n_results=n_results)

        if not results:
            return ToolResult(
                success=True,
                data=f"No results found for query: '{query}'",
                metadata={"match_count": 0, "query": query},
            )

        # Format results for the agent
        lines = [f"Found {len(results)} relevant documents for '{query}':\n"]
        for r in results:
            lines.append(f"--- Result #{r['rank']} (distance: {r['distance']}) ---")
            lines.append(f"Source: {r['source']}")
            lines.append(f"Content: {r['content']}")
            lines.append("")

        return ToolResult(
            success=True,
            data="\n".join(lines),
            metadata={
                "match_count": len(results),
                "query": query,
                "sources": list(set(r["source"] for r in results)),
            },
        )

    except Exception as e:
        return ToolResult(
            success=False,
            data="",
            error=f"RAG search error: {str(e)}",
        )


def rag_ingest(file_path: str) -> ToolResult:
    """
    Add a file to the knowledge base for future searches.
    Splits the file into chunks and stores embeddings.
    """
    try:
        kb = get_knowledge_base()
        chunk_count = kb.ingest_file(file_path)

        return ToolResult(
            success=True,
            data=f"Successfully ingested '{file_path}': {chunk_count} chunks created",
            metadata={
                "file_path": file_path,
                "chunk_count": chunk_count,
                "total_documents": kb.collection.count(),
            },
        )

    except FileNotFoundError:
        return ToolResult(success=False, data="", error=f"File not found: {file_path}")
    except Exception as e:
        return ToolResult(success=False, data="", error=f"Ingest error: {str(e)}")


def rag_stats() -> ToolResult:
    """Get statistics about the knowledge base"""
    try:
        kb = get_knowledge_base()
        stats = kb.get_stats()
        return ToolResult(
            success=True,
            data=json.dumps(stats, indent=2, ensure_ascii=False),
            metadata=stats,
        )
    except Exception as e:
        return ToolResult(success=False, data="", error=f"Stats error: {str(e)}")


# ============================================================
# 4. 注册 RAG 工具
# ============================================================

# Add RAG tools to the global registry
RAG_TOOLS = {
    "rag_search": {
        "name": "rag_search",
        "description": "Search the knowledge base using semantic search. Returns the most relevant document chunks. Use this when you need to find information from previously ingested documents.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query in natural language",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        "function": rag_search,
    },
    "rag_ingest": {
        "name": "rag_ingest",
        "description": "Add a file to the knowledge base. The file will be split into chunks and stored for future semantic search.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to ingest",
                },
            },
            "required": ["file_path"],
        },
        "function": rag_ingest,
    },
    "rag_stats": {
        "name": "rag_stats",
        "description": "Get statistics about the knowledge base, including document count.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "function": rag_stats,
    },
}


def register_rag_tools():
    """Register RAG tools in the global tool registry"""
    TOOL_REGISTRY.update(RAG_TOOLS)


# ============================================================
# 5. RAG Agent（结合 ReAct + RAG 工具）
# ============================================================

class RAGAgent:
    """
    An agent that can use RAG alongside other tools.
    First ingests documents, then answers questions using semantic search.
    """

    def __init__(self, model_name: str = "qwen2.5:7b"):
        # Register RAG tools
        register_rag_tools()

        self.llm = Ollama(model=model_name)
        self.kb = get_knowledge_base()
        self.guard_config = GuardConfig(
            max_iterations=5,
            max_same_tool_calls=3,
        )
        self.guard_checker = GuardChecker(self.guard_config)

    def ingest_documents(self, directory: str) -> dict:
        """Ingest all documents from a directory into the knowledge base"""
        return self.kb.ingest_directory(directory)

    def ask(self, question: str) -> ReActTrace:
        """Answer a question using ReAct loop with RAG tools"""
        trace = ReActTrace(question=question)
        guard_state = GuardState()
        guard_state.start_time = __import__("time").time()
        history_lines = []

        print(f"\n{'='*60}")
        print(f"RAG Agent: {question}")
        print(f"Knowledge base: {self.kb.collection.count()} documents")
        print(f"{'='*60}")

        while True:
            guard_state.iteration_count += 1
            trace.total_iterations = guard_state.iteration_count

            # Guard check
            stop_reason = self.guard_checker.check(guard_state)
            if stop_reason:
                trace.final_answer = f"Stopped: {stop_reason}"
                break

            # Build prompt
            history_text = "\n".join(history_lines) if history_lines else "(No previous steps)"
            prompt = REACT_STEP_PROMPT.format(question=question, history=history_text)
            if guard_state.iteration_count == 1:
                prompt = REACT_SYSTEM_PROMPT.format(
                    tools_description=get_tools_description(),
                ) + "\n\n" + prompt

            # LLM call
            print(f"\n  [Iteration {guard_state.iteration_count}]...")
            try:
                llm_output = self.llm.invoke(prompt)
            except Exception as e:
                trace.final_answer = f"[LLM Error: {e}]"
                break

            parsed = parse_react_output(llm_output)

            if parsed["thought"]:
                step = ReActStep(step_type=StepType.THINK, content=parsed["thought"], iteration=guard_state.iteration_count)
                trace.steps.append(step)
                history_lines.append(f"Thought: {parsed['thought']}")
                print(f"  [Thought] {parsed['thought'][:100]}...")

            if parsed["answer"]:
                step = ReActStep(step_type=StepType.ANSWER, content=parsed["answer"], iteration=guard_state.iteration_count)
                trace.steps.append(step)
                trace.final_answer = parsed["answer"]
                print(f"  [Answer] {parsed['answer'][:100]}...")
                break

            if parsed["action"]:
                tool_name = parsed["action"]["tool"]
                tool_args = parsed["action"]["arguments"]
                guard_state.record_tool_call(tool_name)

                act_step = ReActStep(
                    step_type=StepType.ACT, content=f"Calling {tool_name}",
                    tool_name=tool_name, tool_args=tool_args,
                    iteration=guard_state.iteration_count,
                )
                trace.steps.append(act_step)
                history_lines.append(f"Action: {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")
                print(f"  [Action] {tool_name}")

                tool_result = execute_tool(tool_name, **tool_args)
                result_text = str(tool_result)[:1500]

                obs_step = ReActStep(
                    step_type=StepType.OBSERVE, content=result_text,
                    tool_result=result_text, iteration=guard_state.iteration_count,
                )
                trace.steps.append(obs_step)
                history_lines.append(f"Observation: {result_text}")
                print(f"  [Observe] {result_text[:100]}...")

        return trace


# ============================================================
# 6. 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 5: RAG as Agent Tool 演示")
    print("=" * 60)

    # ---- Part A: Knowledge Base basics ----
    print("\n--- Part A: Knowledge Base 基本操作 ---")

    kb = KnowledgeBase()

    # Ingest some sample documents
    sample_docs = [
        {
            "text": """
LangChain 是一个用于构建 AI 应用的 Python 框架。它提供了以下核心组件：
1. LLM 封装：统一的接口调用各种大语言模型
2. Prompt Template：模板化的提示词管理
3. Chain：将多个组件串联成处理流水线
4. Agent：能自主决策和使用工具的 AI 系统
5. Memory：对话历史和上下文管理
""",
            "source": "langchain_intro.md",
        },
        {
            "text": """
RAG（检索增强生成）的工作流程：
1. 文档加载：读取各种格式的文档（PDF、Markdown、HTML）
2. 文本切分：将长文档切分成小块（chunk）
3. 向量化：用 Embedding 模型将文本转为向量
4. 存储：将向量存入向量数据库（如 Chroma）
5. 检索：用户提问时，找到最相关的文档块
6. 生成：将检索结果作为上下文，让 LLM 生成回答
""",
            "source": "rag_guide.md",
        },
        {
            "text": """
Agent 的核心概念：
- Tool：Agent 可以调用的函数，如文件读取、搜索、计算
- ReAct：Think → Act → Observe 的循环模式
- Planning：将复杂任务分解为子任务
- Memory：记住之前的对话和操作结果
Agent 与普通 Chatbot 的区别：Agent 能主动行动，Chatbot 只能被动回答。
""",
            "source": "agent_concepts.md",
        },
        {
            "text": """
Ollama 是一个本地运行大语言模型的工具：
- 安装简单：brew install ollama 或从官网下载
- 模型管理：ollama pull qwen2.5:7b 下载模型
- API 兼容：提供 OpenAI 兼容的 REST API
- 隐私安全：所有数据都在本地处理
- 常用模型：qwen2.5、llama3、mistral、nomic-embed-text
""",
            "source": "ollama_guide.md",
        },
        {
            "text": """
Chroma 向量数据库特点：
- 轻量级：可以内存运行，也可以持久化到磁盘
- Python 原生：API 设计简洁，学习成本低
- 内置 Embedding：默认使用 all-MiniLM-L6-v2 模型
- 支持过滤：可以按 metadata 字段过滤搜索结果
- 集成方便：与 LangChain 深度集成
""",
            "source": "chroma_guide.md",
        },
    ]

    for doc in sample_docs:
        chunk_count = kb.ingest_text(doc["text"], source=doc["source"])
        print(f"  Ingested {doc['source']}: {chunk_count} chunks")

    print(f"\n  Knowledge base stats: {kb.get_stats()}")

    # ---- Part B: Semantic search ----
    print("\n--- Part B: 语义搜索 ---")

    queries = [
        "什么是 RAG？",
        "如何在本地运行大模型？",
        "Agent 和普通聊天机器人有什么区别？",
        "向量数据库怎么选？",
    ]

    for query in queries:
        results = kb.search(query, n_results=2)
        print(f"\n  Query: {query}")
        for r in results:
            print(f"    #{r['rank']} ({r['source']}, dist={r['distance']}): {r['content'][:60]}...")

    # ---- Part C: RAG tool function ----
    print("\n--- Part C: RAG 工具函数 ---")

    # Set global knowledge base
    _knowledge_base = kb

    result = rag_search("Agent 怎么使用工具")
    print(f"  Search result: success={result.success}")
    print(f"  {result.data[:200]}...")

    result = rag_stats()
    print(f"\n  Stats: {result.data}")

    # ---- Part D: RAG Agent (requires Ollama) ----
    print("\n--- Part D: RAG Agent (requires Ollama) ---")
    try:
        register_rag_tools()
        agent = RAGAgent()
        trace = agent.ask("请解释什么是 RAG，以及它和 Agent 的关系")
        print(trace.display())
    except Exception as e:
        print(f"[Ollama not available: {e}]")
        print("Knowledge base is working. Start Ollama to use the full RAG Agent.")


    # ============================================================
    # 练习题
    # ============================================================

    print("\n" + "=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 给 rag_search 添加 source_filter 参数
    # 让 Agent 可以指定只搜索某个来源的文档
    # 例如: rag_search("什么是 RAG", source_filter="rag_guide.md")

    # TODO 2: 实现一个 rag_summary 工具
    # 接收一个 source 名称，返回该文档的摘要
    # 提示：先检索该 source 的所有 chunks，再拼接返回

    # TODO 3: 把当前目录的所有 .py 文件导入知识库
    # 然后问 Agent："这些代码文件之间的依赖关系是什么？"
