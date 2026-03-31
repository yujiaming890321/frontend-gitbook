"""
Day 1: LangChain + Chroma 安装和 Quickstart
LangChain 是 AI 应用开发的主流框架，Chroma 是轻量级向量数据库
"""

# ============================================================
# 1. LangChain 核心概念
# ============================================================

"""
LangChain 的核心抽象（类比前端概念）：

┌──────────────────┬──────────────────────────────┐
│ LangChain 概念    │ 前端类比                      │
├──────────────────┼──────────────────────────────┤
│ LLM / ChatModel  │ API 客户端 (axios instance)    │
│ Prompt Template  │ 模板引擎 (handlebars/ejs)      │
│ Chain            │ 中间件管道 (express middleware) │
│ Document Loader  │ 文件读取器 (fs.readFile)        │
│ Text Splitter    │ 分页组件 (pagination)           │
│ Embedding        │ 数据转换器 (transformer)        │
│ Vector Store     │ 搜索引擎 (Elasticsearch)       │
│ Retriever        │ 数据查询层 (data fetcher)       │
└──────────────────┴──────────────────────────────┘
"""

# ============================================================
# 2. 基本使用 — ChatModel
# ============================================================

from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, SystemMessage

# Create LLM instance (connects to local Ollama)
llm = Ollama(model="qwen2.5:7b")

# Simple invocation
try:
    result = llm.invoke("用一句话解释什么是 RAG")
    print(f"LLM 回复: {result[:150]}...")
except Exception as e:
    print(f"[Ollama 未启动: {e}]")


# ============================================================
# 3. Prompt Template
# ============================================================

from langchain_core.prompts import ChatPromptTemplate

# Create a reusable prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，用{style}的方式回答问题。"),
    ("human", "{question}"),
])

# Fill in the template
messages = prompt.format_messages(
    role="Python 老师",
    style="简洁易懂",
    question="什么是列表推导式？",
)
print(f"\n格式化后的消息: {messages}")

# Chain: prompt | llm
try:
    chain = prompt | llm
    result = chain.invoke({
        "role": "Python 老师",
        "style": "简洁易懂",
        "question": "什么是装饰器？",
    })
    print(f"\nChain 结果: {result[:200]}...")
except Exception as e:
    print(f"[Chain 执行失败: {e}]")


# ============================================================
# 4. Output Parser
# ============================================================

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# String parser (most basic)
str_parser = StrOutputParser()

# JSON parser
json_parser = JsonOutputParser()

# Chain with parser: prompt → LLM → parse output
try:
    json_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是数据分析师。用 JSON 格式回答。"),
        ("human", "分析这个词的情感：{word}"),
    ])

    chain = json_prompt | llm | str_parser
    result = chain.invoke({"word": "开心"})
    print(f"\n带 parser 的 Chain: {result[:200]}...")
except Exception as e:
    print(f"[执行失败: {e}]")


# ============================================================
# 5. Chroma 向量数据库 — 快速验证
# ============================================================

import chromadb

# Create in-memory Chroma client
chroma_client = chromadb.Client()

# Create a collection (like a database table)
collection = chroma_client.create_collection(name="test_collection")

# Add documents with auto-generated embeddings
collection.add(
    documents=[
        "RAG 是检索增强生成，结合检索和 LLM",
        "Agent 是能自主决策的 AI 系统",
        "Prompt Engineering 是设计 LLM 输入的技巧",
        "Fine-tuning 是对模型进行微调训练",
        "LangChain 是构建 AI 应用的框架",
    ],
    ids=["doc1", "doc2", "doc3", "doc4", "doc5"],
    metadatas=[
        {"topic": "rag"}, {"topic": "agent"}, {"topic": "prompt"},
        {"topic": "training"}, {"topic": "framework"},
    ],
)

# Query — find similar documents
results = collection.query(
    query_texts=["如何让 AI 记住知识？"],
    n_results=3,
)

print("\n--- Chroma 检索结果 ---")
for i, (doc, distance) in enumerate(zip(results["documents"][0], results["distances"][0])):
    print(f"  {i+1}. (距离={distance:.4f}) {doc}")


# ============================================================
# 6. LangChain 架构速查
# ============================================================

"""
LangChain 模块结构：

langchain-core          核心抽象（Prompt, Chain, Parser）
langchain-community     社区集成（Ollama, Chroma, ...）
langchain               高层 Chain 和 Agent
langgraph               图状态机（Week 8-10 学）

安装建议：
pip install langchain langchain-community langchain-chroma
# 不要装 langchain[all]，太多依赖
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 用 ChatPromptTemplate 创建一个"翻译链"
# 接收 source_lang, target_lang, text
# 输出翻译结果

# TODO 2: 用 Chroma 存储 10 条技术笔记
# 然后实现一个搜索函数，支持按关键词搜索 + 按 topic 过滤

# TODO 3: 组合 Prompt + LLM + Chroma
# 先在 Chroma 中搜索相关文档
# 把搜索结果作为上下文传给 LLM
# 让 LLM 基于上下文回答问题
# 这就是 RAG 的核心流程！
