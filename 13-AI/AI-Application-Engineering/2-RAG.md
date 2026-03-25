# RAG（检索增强生成）

RAG（Retrieval-Augmented Generation）是一种将外部知识检索与大语言模型生成能力结合的技术架构，解决 LLM 知识截止、幻觉等问题。

## 核心流程

```
用户提问 → Embedding 向量化 → 向量数据库检索 → 相关文档片段 → 拼接 Prompt → LLM 生成回答
```

## 关键组件

### 1. 文档处理（Indexing）

将原始文档转化为可检索的格式：

- **文档加载**：支持 PDF、Markdown、HTML、数据库等多种数据源
- **文本分块（Chunking）**：将长文档切分为合适大小的片段
  - 固定大小分块（Fixed Size）
  - 语义分块（Semantic Chunking）
  - 递归字符分块（Recursive Character Splitting）
- **向量化（Embedding）**：将文本转换为高维向量
  - OpenAI `text-embedding-3-small/large`
  - 开源模型：`bge-large`、`e5-large`

### 2. 向量数据库（Vector Store）

存储和检索向量的专用数据库：

| 数据库 | 特点 |
|--------|------|
| **Chroma** | 轻量级，适合原型开发 |
| **Pinecone** | 全托管云服务 |
| **Milvus** | 高性能，支持十亿级向量 |
| **Weaviate** | 支持混合搜索 |
| **pgvector** | PostgreSQL 扩展，适合已有 PG 的团队 |

### 3. 检索策略（Retrieval）

- **相似度搜索**：余弦相似度、欧氏距离
- **混合搜索**：向量搜索 + 关键词搜索（BM25）
- **重排序（Reranking）**：使用 Cross-Encoder 对检索结果重新排序
- **元数据过滤**：按时间、来源、类别等条件筛选

### 4. 生成（Generation）

将检索到的上下文与用户问题组合，交给 LLM 生成回答：

```
System: 你是一个问答助手，基于以下上下文回答问题。如果上下文中没有相关信息，请说"我不知道"。

Context: {retrieved_documents}

User: {question}
```

## 进阶模式

### Naive RAG vs Advanced RAG

```
Naive RAG:   Query → Retrieve → Generate

Advanced RAG: Query → Query改写 → 多路检索 → 重排序 → 压缩 → Generate → 自我验证
```

### 常见优化手段

- **Query 改写**：用 LLM 重写用户问题，提升检索质量
- **HyDE**：先让 LLM 生成假设性回答，用回答去检索
- **多跳检索（Multi-hop）**：多次检索，逐步收集信息
- **Self-RAG**：模型自己判断是否需要检索、检索结果是否相关
- **父文档检索**：检索小块，但返回所属的大块上下文

## 评估指标

| 指标 | 说明 |
|------|------|
| **Faithfulness** | 回答是否忠于检索到的上下文 |
| **Relevance** | 检索到的文档是否与问题相关 |
| **Answer Correctness** | 回答是否正确 |
| **Context Precision** | 相关文档排名是否靠前 |
| **Context Recall** | 是否召回了所有相关文档 |

评估工具：[Ragas](https://github.com/explodinggradients/ragas)、[TruLens](https://github.com/truera/trulens)

## 适用场景

- 企业知识库问答
- 文档搜索与摘要
- 客服机器人
- 代码库问答
- 法律/医疗等领域的专业问答

## 大规模数据下的 Agent 使用策略

Agent 的 context window 有限，无法一次性加载所有 RAG 数据。以下是处理大规模数据的主要策略。

### 1. 分层检索（Hierarchical Retrieval）

先用轻量级模型/向量检索缩小范围，再用 LLM 精读：

```
100万文档 → Embedding 检索 Top 100 → Rerank 到 Top 10 → 送入 Agent
```

### 2. 迭代检索（Iterative Retrieval）

Agent 不一次查完，而是**多轮查询**，根据上一轮结果调整查询策略。类似人类"先搜一下，看看结果，再换个关键词搜"。

### 3. 摘要 + 索引

- 预先对文档生成摘要，Agent 先读摘要决定是否需要原文
- 建立多级索引：目录级 → 章节级 → 段落级

### 4. Chunk 策略优化

- **语义分块**而非固定长度切分
- 保留 metadata（来源、时间、类别）供 Agent 过滤
- 适当的 chunk overlap 防止信息断裂

### 5. Tool-based 按需加载

把 RAG 封装成 **工具（Tool）**，Agent 按需调用，而非一股脑塞进 context：

```
Agent 决定查什么、查多少
  ↓
调用 search_docs(query, filters, top_k)
  ↓
获取结果，决定是否需要进一步检索
```

### 规模与方案对照

| 数据规模 | 推荐方案 |
|---------|---------|
| < 10万条 | 向量检索 + Rerank，直接塞 context |
| 10万 - 千万 | 分层检索 + Tool 按需加载 |
| > 千万 | 多级索引 + 迭代检索 + 摘要预处理 |

### 核心原则

> Agent 不应该"看完所有数据再回答"，而是"知道去哪找、找多少"。把 RAG 看作 Agent 的一个 Tool，让 Agent 自主决定检索策略，比硬塞 context 更高效也更准确。
