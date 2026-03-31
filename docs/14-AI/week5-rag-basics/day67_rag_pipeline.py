"""
Day 6-7: 综合练习 — 完整的 RAG Pipeline

串联本周所有组件：加载 → 切分 → 向量化 → 存储 → 检索 → 回答
用你自己的 gitbook 文档作为知识库

用法:
  python day67_rag_pipeline.py build     # 构建知识库
  python day67_rag_pipeline.py ask "问题"  # 提问
  python day67_rag_pipeline.py interactive  # 交互模式
"""

import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_chroma import Chroma
from langchain_core.documents import Document

# ============================================================
# Configuration
# ============================================================

@dataclass
class RAGConfig:
    """RAG pipeline configuration"""
    docs_dir: str = "../../"  # Relative to this file, points to gitbook root
    chroma_dir: str = "/tmp/chroma_gitbook"
    collection_name: str = "gitbook_docs"
    embedding_model: str = "nomic-embed-text"
    llm_model: str = "qwen2.5:7b"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3

config = RAGConfig()


# ============================================================
# Step 1: Document Loading
# ============================================================

def load_documents(docs_dir: str) -> list[Document]:
    """Load all markdown files from the docs directory"""
    docs_path = Path(docs_dir).resolve()
    if not docs_path.exists():
        print(f"目录不存在: {docs_path}")
        return []

    loader = DirectoryLoader(
        str(docs_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )

    docs = loader.load()
    print(f"加载了 {len(docs)} 个文档")
    return docs


# ============================================================
# Step 2: Document Splitting
# ============================================================

def split_documents(docs: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
    """Split documents into chunks"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", " ", ""],
    )

    chunks = splitter.split_documents(docs)
    print(f"切分成 {len(chunks)} 个 chunks (chunk_size={chunk_size}, overlap={chunk_overlap})")

    # Add chunk index to metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    return chunks


# ============================================================
# Step 3: Build Vector Store
# ============================================================

def build_vectorstore(chunks: list[Document], config: RAGConfig) -> Chroma:
    """Build Chroma vector store from document chunks"""
    embeddings = OllamaEmbeddings(model=config.embedding_model)

    start = time.time()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=config.chroma_dir,
        collection_name=config.collection_name,
    )
    elapsed = time.time() - start

    print(f"向量数据库构建完成 ({elapsed:.1f}s)")
    print(f"持久化到: {config.chroma_dir}")
    return vectorstore


def load_vectorstore(config: RAGConfig) -> Chroma:
    """Load existing vector store from disk"""
    embeddings = OllamaEmbeddings(model=config.embedding_model)
    return Chroma(
        persist_directory=config.chroma_dir,
        embedding_function=embeddings,
        collection_name=config.collection_name,
    )


# ============================================================
# Step 4: RAG Query
# ============================================================

def rag_query(question: str, vectorstore: Chroma, config: RAGConfig) -> dict:
    """
    Complete RAG query:
    1. Search relevant chunks
    2. Build context from chunks
    3. Ask LLM to answer based on context
    """
    # Step 1: Retrieve relevant chunks
    results = vectorstore.similarity_search_with_score(question, k=config.top_k)

    if not results:
        return {"answer": "没有找到相关文档。", "sources": [], "chunks_used": 0}

    # Step 2: Build context
    context_parts = []
    sources = []
    for doc, score in results:
        source = Path(doc.metadata.get("source", "unknown")).name
        context_parts.append(f"[来源: {source}]\n{doc.page_content}")
        sources.append({"source": source, "score": float(score), "preview": doc.page_content[:80]})

    context = "\n\n---\n\n".join(context_parts)

    # Step 3: Ask LLM
    prompt = f"""基于以下参考资料回答问题。如果资料中没有相关信息，请说"根据现有资料无法回答"。
请在回答中引用来源。

参考资料：
{context}

问题：{question}

回答："""

    llm = Ollama(model=config.llm_model)
    try:
        answer = llm.invoke(prompt)
    except Exception as e:
        answer = f"[LLM 调用失败: {e}]"

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(results),
        "context_length": len(context),
    }


# ============================================================
# CLI Interface
# ============================================================

def cmd_build():
    """Build the knowledge base"""
    print("=== 构建知识库 ===\n")
    docs = load_documents(config.docs_dir)
    if not docs:
        print("没有找到文档，请检查路径")
        return

    chunks = split_documents(docs, config.chunk_size, config.chunk_overlap)
    build_vectorstore(chunks, config)
    print("\n知识库构建完成！")


def cmd_ask(question: str):
    """Ask a question"""
    try:
        vectorstore = load_vectorstore(config)
    except Exception as e:
        print(f"请先运行 build 命令构建知识库: {e}")
        return

    print(f"\n问题: {question}\n")
    result = rag_query(question, vectorstore, config)

    print(f"回答: {result['answer']}\n")
    print(f"使用了 {result['chunks_used']} 个文档块 ({result['context_length']} 字符)")
    print(f"\n来源:")
    for src in result["sources"]:
        print(f"  - {src['source']} (距离: {src['score']:.4f})")


def cmd_interactive():
    """Interactive Q&A mode"""
    try:
        vectorstore = load_vectorstore(config)
    except Exception:
        print("请先运行: python day67_rag_pipeline.py build")
        return

    print("RAG 交互模式 (输入 /quit 退出)\n")
    while True:
        try:
            question = input("你: ").strip()
            if not question:
                continue
            if question == "/quit":
                break

            result = rag_query(question, vectorstore, config)
            print(f"\nAI: {result['answer']}")
            print(f"[来源: {', '.join(s['source'] for s in result['sources'])}]\n")
        except (KeyboardInterrupt, EOFError):
            break

    print("再见！")


def main():
    if len(sys.argv) < 2:
        print("""
RAG Pipeline — 知识库问答系统

用法:
  python day67_rag_pipeline.py build          构建知识库
  python day67_rag_pipeline.py ask "问题"      提问
  python day67_rag_pipeline.py interactive    交互模式
""")
        return

    command = sys.argv[1]
    if command == "build":
        cmd_build()
    elif command == "ask" and len(sys.argv) >= 3:
        cmd_ask(sys.argv[2])
    elif command == "interactive":
        cmd_interactive()
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()


# ============================================================
# 扩展练习
# ============================================================

# TODO 1: 添加文档更新功能
# 当文档修改后，只重新索引变化的文件
# 提示：对比文件的修改时间和数据库的时间戳

# TODO 2: 添加检索评估
# 准备 10 个问题和期望的答案
# 运行 RAG 并评估：答案是否包含关键信息？来源是否正确？

# TODO 3: 实现混合检索
# 同时用向量搜索（语义）和关键词搜索（BM25）
# 合并两种结果，提升检索准确率
