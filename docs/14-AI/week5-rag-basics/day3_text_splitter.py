"""
Day 3: 文档切分 — chunk_size 和 overlap
RAG 的关键步骤：把长文档切成适合检索的小块
切分质量直接影响 RAG 的效果
"""

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from langchain_core.documents import Document

# ============================================================
# 1. 为什么要切分文档？
# ============================================================

"""
为什么不能把整个文档直接扔给 LLM？

1. 上下文窗口限制：LLM 有 token 上限（4K-128K）
2. 检索精度：小块更容易精确匹配用户问题
3. Embedding 质量：短文本的向量表示更精准
4. 成本控制：减少不必要的 token 消耗

类比前端：
- 长列表要虚拟化 (virtualization) → 长文档要切分
- 分页 (pagination) → chunk_size
- 预加载 (prefetch overlap) → chunk_overlap
"""


# ============================================================
# 2. CharacterTextSplitter — 按字符切分
# ============================================================

long_text = """
RAG（Retrieval-Augmented Generation）是一种结合检索和生成的 AI 技术。它的核心思想是：与其让 LLM 记住所有知识，不如在需要时从外部知识库中检索相关信息。

RAG 的工作流程分为三个阶段：

第一阶段是索引（Indexing）。将文档切分成小块，然后用 Embedding 模型把每个小块转换成向量，存入向量数据库。这个过程通常只需要做一次。

第二阶段是检索（Retrieval）。当用户提问时，先把问题也转换成向量，然后在向量数据库中搜索最相似的文档块。通常返回 top-k 个最相关的结果。

第三阶段是生成（Generation）。将检索到的文档块作为上下文，和用户问题一起传给 LLM，让 LLM 基于这些上下文生成回答。

RAG 相比 Fine-tuning 的优势在于：不需要重新训练模型，知识可以实时更新，回答有据可查，成本更低。
""".strip()

# Basic character splitter
char_splitter = CharacterTextSplitter(
    separator="\n\n",     # Split on paragraph breaks
    chunk_size=200,       # Max characters per chunk
    chunk_overlap=30,     # Overlap between chunks
)

chunks = char_splitter.split_text(long_text)
print("--- CharacterTextSplitter ---")
print(f"原文长度: {len(long_text)} 字符")
print(f"切分成: {len(chunks)} 块\n")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i} ({len(chunk)} chars): {chunk[:60]}...")


# ============================================================
# 3. RecursiveCharacterTextSplitter — 推荐使用
# 递归按多个分隔符切分，保持语义完整性
# ============================================================

recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=30,
    separators=["\n\n", "\n", "。", "，", " ", ""],  # Try each separator in order
    # First try paragraph breaks, then sentences, then characters
)

recursive_chunks = recursive_splitter.split_text(long_text)
print(f"\n--- RecursiveCharacterTextSplitter ---")
print(f"切分成: {len(recursive_chunks)} 块\n")
for i, chunk in enumerate(recursive_chunks):
    print(f"Chunk {i} ({len(chunk)} chars): {chunk[:60]}...")


# ============================================================
# 4. chunk_size 和 chunk_overlap 的选择
# ============================================================

"""
chunk_size 选择指南：

chunk_size    适用场景                        特点
────────     ────────                        ────
100-200      精确问答、FAQ                     检索精度高，但可能丢失上下文
300-500      一般知识库问答（推荐起点）          平衡精度和上下文
500-1000     需要较多上下文的场景                上下文丰富，但检索精度可能降低
1000+        长文档分析                         很少使用

chunk_overlap 选择：
- 通常是 chunk_size 的 10-20%
- 太小：关键信息可能被切断
- 太大：重复内容多，浪费存储和计算

经验公式：
- chunk_overlap = chunk_size * 0.1  （最少）
- chunk_overlap = chunk_size * 0.2  （推荐）
"""

def compare_chunk_sizes(text: str, sizes: list[int]):
    """Compare different chunk sizes on the same text"""
    print(f"\n--- Chunk Size 对比 ---")
    print(f"原文: {len(text)} 字符\n")
    for size in sizes:
        overlap = int(size * 0.15)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=size, chunk_overlap=overlap,
        )
        chunks = splitter.split_text(text)
        avg_len = sum(len(c) for c in chunks) / len(chunks) if chunks else 0
        print(f"  chunk_size={size:4d}, overlap={overlap:3d} → "
              f"{len(chunks):2d} 块, 平均 {avg_len:.0f} 字符/块")

compare_chunk_sizes(long_text, [100, 200, 300, 500])


# ============================================================
# 5. MarkdownHeaderTextSplitter — 按标题切分
# 专门为 Markdown 设计，保持文档结构
# ============================================================

markdown_text = """# RAG 系统设计

## 1. 索引阶段

索引阶段将文档处理成可检索的格式。
包括文档加载、切分、向量化三个步骤。

### 1.1 文档加载

支持 PDF、Markdown、HTML 等格式。

### 1.2 文档切分

使用 RecursiveCharacterTextSplitter。

## 2. 检索阶段

检索阶段从向量数据库中找到相关文档。

### 2.1 相似度搜索

使用余弦相似度或 L2 距离。

## 3. 生成阶段

将检索结果传给 LLM 生成回答。
"""

headers_to_split_on = [
    ("#", "title"),
    ("##", "section"),
    ("###", "subsection"),
]

md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
md_chunks = md_splitter.split_text(markdown_text)

print(f"\n--- MarkdownHeaderTextSplitter ---")
for chunk in md_chunks:
    print(f"  [{chunk.metadata}] {chunk.page_content[:50]}...")


# ============================================================
# 6. 切分 Document 对象（带 metadata）
# ============================================================

documents = [
    Document(
        page_content=long_text,
        metadata={"source": "rag_guide.md", "topic": "rag"},
    ),
]

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
split_docs = splitter.split_documents(documents)

print(f"\n--- 切分 Document ---")
print(f"切分前: {len(documents)} 个文档")
print(f"切分后: {len(split_docs)} 个文档块")
for doc in split_docs[:3]:
    print(f"  [{doc.metadata['source']}] {doc.page_content[:50]}...")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 加载你的 gitbook 文档（Week 5 Day 2 的 loader）
# 用 RecursiveCharacterTextSplitter 切分
# 统计：总文档数、总 chunk 数、平均 chunk 大小

# TODO 2: 实现一个"智能切分器"
# 优先在段落边界切分
# 如果段落太长，在句号处切分
# 如果句子太长，在逗号处切分
# 保证每个 chunk 都以完整句子结尾

# TODO 3: 对比不同 chunk_size 的检索效果
# 用同一组问题，在不同 chunk_size 下检索
# 记录每个问题的 top-1 结果的相关性
# 找出最佳 chunk_size（Week 5 Day 5 之后做）
