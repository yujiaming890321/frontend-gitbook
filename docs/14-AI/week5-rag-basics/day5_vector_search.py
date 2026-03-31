"""
Day 5: 向量检索 — 用 Chroma 存储和检索向量
把文档向量存入数据库，实现语义搜索
"""

from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path

# ============================================================
# 1. 创建向量数据库
# ============================================================

embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Sample documents for the vector store
sample_docs = [
    Document(page_content="RAG 是检索增强生成，通过从知识库检索信息来增强 LLM 的回答。它不需要重新训练模型，知识可以实时更新。", metadata={"source": "rag.md", "topic": "rag"}),
    Document(page_content="RAG 的工作流程分为三步：索引（文档向量化）、检索（语义搜索）、生成（LLM 基于上下文回答）。", metadata={"source": "rag.md", "topic": "rag"}),
    Document(page_content="Agent 是能自主决策的 AI 系统。核心组件包括：LLM（推理）、Tools（工具）、Memory（记忆）、Planning（规划）。", metadata={"source": "agent.md", "topic": "agent"}),
    Document(page_content="ReAct 模式是 Agent 的核心工作模式：Thought（思考）→ Action（行动）→ Observation（观察），循环直到完成任务。", metadata={"source": "agent.md", "topic": "agent"}),
    Document(page_content="Prompt Engineering 包括：System Prompt 设计、Few-Shot 示例、Chain-of-Thought 推理、结构化输出等技巧。", metadata={"source": "prompt.md", "topic": "prompt"}),
    Document(page_content="Function Calling 让 LLM 可以调用外部函数。LLM 根据用户输入决定调用哪个函数、传什么参数。", metadata={"source": "prompt.md", "topic": "prompt"}),
    Document(page_content="LangChain 是构建 AI 应用的框架，提供文档加载、切分、向量化、检索、链式调用等组件。", metadata={"source": "langchain.md", "topic": "framework"}),
    Document(page_content="Chroma 是轻量级向量数据库，支持本地运行。适合开发和小规模生产环境使用。", metadata={"source": "chroma.md", "topic": "framework"}),
]

# Create Chroma vector store
persist_dir = "/tmp/chroma_week5"

try:
    vectorstore = Chroma.from_documents(
        documents=sample_docs,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="ai_knowledge",
    )
    print(f"向量数据库创建成功，存储 {len(sample_docs)} 个文档")
    print(f"持久化目录: {persist_dir}")
except Exception as e:
    print(f"[创建失败: {e}]")
    vectorstore = None


# ============================================================
# 2. 基本检索
# ============================================================

if vectorstore:
    # similarity_search — returns Documents sorted by relevance
    print("\n--- 基本检索 ---")
    query = "如何让 AI 使用外部知识？"
    results = vectorstore.similarity_search(query, k=3)
    print(f"查询: {query}")
    for i, doc in enumerate(results):
        print(f"  {i+1}. [{doc.metadata['source']}] {doc.page_content[:60]}...")


# ============================================================
# 3. 带分数的检索
# ============================================================

if vectorstore:
    print("\n--- 带分数的检索 ---")
    query = "Agent 怎么工作？"
    results_with_scores = vectorstore.similarity_search_with_score(query, k=3)
    print(f"查询: {query}")
    for doc, score in results_with_scores:
        # Lower score = more similar (L2 distance)
        print(f"  距离={score:.4f} [{doc.metadata['source']}] {doc.page_content[:60]}...")


# ============================================================
# 4. 过滤检索 — 按 metadata 筛选
# ============================================================

if vectorstore:
    print("\n--- 过滤检索 ---")
    # Only search within "rag" topic documents
    results = vectorstore.similarity_search(
        "工作流程是什么？",
        k=3,
        filter={"topic": "rag"},
    )
    print(f"查询: '工作流程是什么？' (filter: topic=rag)")
    for doc in results:
        print(f"  [{doc.metadata['topic']}] {doc.page_content[:60]}...")


# ============================================================
# 5. Retriever 接口 — LangChain 标准检索器
# ============================================================

if vectorstore:
    print("\n--- Retriever 接口 ---")
    # Convert to retriever (standard LangChain interface)
    retriever = vectorstore.as_retriever(
        search_type="similarity",    # or "mmr" for diversity
        search_kwargs={"k": 3},
    )

    # Use retriever
    docs = retriever.invoke("什么是 Prompt Engineering？")
    print(f"Retriever 返回 {len(docs)} 个文档:")
    for doc in docs:
        print(f"  {doc.page_content[:60]}...")

    # MMR (Maximal Marginal Relevance) — balances relevance and diversity
    mmr_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 6},  # Fetch 6, pick best 3 with diversity
    )

    docs = mmr_retriever.invoke("AI 应用开发")
    print(f"\nMMR Retriever 返回 {len(docs)} 个文档:")
    for doc in docs:
        print(f"  [{doc.metadata['topic']}] {doc.page_content[:60]}...")


# ============================================================
# 6. 加载已有的向量数据库
# ============================================================

if vectorstore:
    # Load existing vector store from disk
    loaded_store = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name="ai_knowledge",
    )

    results = loaded_store.similarity_search("检索", k=2)
    print(f"\n--- 从磁盘加载 ---")
    print(f"加载成功，检索结果: {len(results)} 个")


# ============================================================
# 7. 检索策略对比
# ============================================================

"""
搜索类型              说明                      适用场景
──────────           ────                      ────────
similarity           纯相似度排序                一般问答
mmr                  相似度 + 多样性              避免重复内容
similarity_threshold 只返回超过阈值的结果          需要高精度
hybrid               向量 + 关键词（BM25）混合     综合场景

k 值选择：
- k=3：一般问答（推荐起点）
- k=5-10：需要更多上下文的场景
- k=1：非常精确的匹配场景

注意：
- k 越大，传给 LLM 的上下文越多，成本越高
- 但 k 太小可能漏掉关键信息
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 加载你的 gitbook 文档
# 切分 → 向量化 → 存入 Chroma
# 用 5 个不同的问题测试检索效果

# TODO 2: 对比 similarity vs mmr 的检索结果
# 用同一个问题，分别用两种方式检索
# 观察结果的差异（mmr 应该更多样化）

# TODO 3: 实现一个 similarity_threshold 搜索
# 只返回相似度高于 0.7 的结果
# 如果没有结果，返回"未找到相关文档"
# 提示：用 similarity_search_with_score + 手动过滤
