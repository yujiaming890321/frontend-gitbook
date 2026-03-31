"""
Day 4: Embedding — 用 Ollama 做向量化
Embedding 把文本变成向量（一组数字），让计算机能"理解"语义
类比前端：就像把用户行为数据转成特征向量做推荐
"""

import numpy as np
from langchain_community.embeddings import OllamaEmbeddings

# ============================================================
# 1. 什么是 Embedding？
# ============================================================

"""
Embedding 把文本变成固定长度的浮点数向量：

"RAG 是检索增强生成" → [0.12, -0.34, 0.56, ..., 0.78]  (768 维)
"检索增强生成技术"    → [0.11, -0.33, 0.55, ..., 0.77]  (相似！)
"今天天气不错"        → [0.89, 0.12, -0.67, ..., 0.23]  (不同！)

语义相似的文本 → 向量也相似（距离近）
语义不同的文本 → 向量也不同（距离远）

类比：
- 把"文字"映射到"坐标空间"
- 相似的文字在空间中距离近
- 搜索 = 在空间中找最近的点
"""


# ============================================================
# 2. 使用 Ollama Embedding 模型
# ============================================================

# nomic-embed-text: 768 dimensions, good for general text
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Embed a single text
try:
    single_vector = embeddings.embed_query("什么是 RAG？")
    print(f"--- 单个文本的 Embedding ---")
    print(f"维度: {len(single_vector)}")
    print(f"前 10 个值: {single_vector[:10]}")
    print(f"向量范数: {np.linalg.norm(single_vector):.4f}")
except Exception as e:
    print(f"[Embedding 失败: {e}]")
    # Fallback: use fake embeddings for demonstration
    single_vector = list(np.random.randn(768))
    print("使用模拟 embedding 继续演示")


# Embed multiple texts at once (batch)
texts = [
    "RAG 是检索增强生成",
    "检索增强生成技术很有用",
    "今天天气真好",
    "Agent 能自主决策",
    "Python 是编程语言",
]

try:
    vectors = embeddings.embed_documents(texts)
    print(f"\n--- 批量 Embedding ---")
    print(f"文本数: {len(texts)}")
    print(f"向量数: {len(vectors)}")
    print(f"每个向量维度: {len(vectors[0])}")
except Exception as e:
    print(f"[批量 Embedding 失败: {e}]")
    vectors = [list(np.random.randn(768)) for _ in texts]


# ============================================================
# 3. 计算相似度
# ============================================================

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

print(f"\n--- 相似度计算 ---")
for i, text_i in enumerate(texts):
    for j, text_j in enumerate(texts):
        if i < j:
            sim = cosine_similarity(vectors[i], vectors[j])
            print(f"  '{text_i}' vs '{text_j}': {sim:.4f}")


# ============================================================
# 4. 搜索 — 找最相似的文本
# ============================================================

def find_most_similar(query: str, documents: list[str], doc_vectors: list, top_k: int = 3) -> list[tuple[str, float]]:
    """Find the most similar documents to a query"""
    try:
        query_vector = embeddings.embed_query(query)
    except Exception:
        query_vector = list(np.random.randn(768))

    similarities = []
    for i, doc in enumerate(documents):
        sim = cosine_similarity(query_vector, doc_vectors[i])
        similarities.append((doc, sim))

    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


print(f"\n--- 语义搜索 ---")
query = "如何让 AI 使用外部知识？"
results = find_most_similar(query, texts, vectors, top_k=3)
print(f"查询: {query}")
for doc, score in results:
    print(f"  {score:.4f} — {doc}")


# ============================================================
# 5. Embedding 模型对比
# ============================================================

"""
模型                   维度    大小     特点
──────                ────    ────    ────
nomic-embed-text      768     274MB   通用，Ollama 默认
bge-m3                1024    ~1.2GB  多语言，中文好
mxbai-embed-large     1024    670MB   大模型，效果好
text-embedding-3-small 1536    -      OpenAI 付费，效果好
text-embedding-3-large 3072    -      OpenAI 付费，效果最好

选择建议：
- 学习/本地开发 → nomic-embed-text（小、快、免费）
- 中文场景 → bge-m3（中文效果最好）
- 生产环境 → text-embedding-3-small（性价比高）
"""


# ============================================================
# 6. Embedding 缓存 — 避免重复计算
# ============================================================

import hashlib
import json
from pathlib import Path


class EmbeddingCache:
    """Cache embeddings to avoid recomputing for same text"""

    def __init__(self, cache_dir: str = "/tmp/embedding_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.embeddings = embeddings

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def embed(self, text: str) -> list[float]:
        """Get embedding from cache or compute and cache it"""
        cache_file = self.cache_dir / f"{self._hash(text)}.json"

        if cache_file.exists():
            return json.loads(cache_file.read_text())

        vector = self.embeddings.embed_query(text)
        cache_file.write_text(json.dumps(vector))
        return vector

cache = EmbeddingCache()
# First call: compute and cache
# Second call: read from cache (instant)


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 用你的 gitbook 文档做 embedding
# 加载所有 .md 文件 → 切分 → embedding
# 统计总共多少个 chunk，embedding 耗时多少

# TODO 2: 实现一个简单的语义搜索引擎
# 输入查询 → 返回最相似的 3 个文档块
# 显示相似度分数和来源文件

# TODO 3: 对比不同查询的搜索结果
# 用以下 3 个查询测试你的搜索引擎：
# - "什么是 RAG？"（应该匹配 RAG 相关文档）
# - "如何构建 Agent？"（应该匹配 Agent 相关文档）
# - "JavaScript 和 Python 的区别"（可能匹配多个文档）
