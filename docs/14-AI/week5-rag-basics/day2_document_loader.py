"""
Day 2: 文档加载器 — 加载各种格式的文件
RAG 的第一步：把文档读进来
"""

from pathlib import Path
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_core.documents import Document

# ============================================================
# 1. 手动创建 Document 对象
# ============================================================

"""
LangChain 中所有文档都用 Document 对象表示：

Document(
    page_content="文档内容",     # 正文
    metadata={"source": "file.md", "title": "..."}  # 元数据
)
"""

# Create documents manually
docs = [
    Document(
        page_content="RAG 是检索增强生成，它通过检索知识库来增强 LLM 的回答。",
        metadata={"source": "rag.md", "topic": "rag"},
    ),
    Document(
        page_content="Agent 是能自主决策和使用工具的 AI 系统。",
        metadata={"source": "agent.md", "topic": "agent"},
    ),
]

for doc in docs:
    print(f"[{doc.metadata['source']}] {doc.page_content[:50]}...")


# ============================================================
# 2. TextLoader — 加载单个文本文件
# ============================================================

# Create a sample file for loading
sample_dir = Path("/tmp/rag_demo_docs")
sample_dir.mkdir(exist_ok=True)

(sample_dir / "rag_intro.md").write_text("""# RAG 入门

RAG（Retrieval-Augmented Generation，检索增强生成）是一种将检索和生成结合的 AI 技术。

## 工作流程

1. 用户提问
2. 从知识库中检索相关文档
3. 将检索结果作为上下文传给 LLM
4. LLM 基于上下文生成回答

## 优势

- 不需要重新训练模型
- 知识可以实时更新
- 回答有据可查
""", encoding="utf-8")

(sample_dir / "agent_intro.md").write_text("""# Agent 基础

AI Agent 是能自主决策和执行任务的系统。

## 核心组件

1. **LLM**: 大脑，负责推理和决策
2. **Tools**: 工具集，Agent 可以调用的外部功能
3. **Memory**: 记忆，维护对话和任务上下文
4. **Planning**: 计划，将复杂任务分解为步骤

## ReAct 模式

Agent 通过 Thought → Action → Observation 循环来完成任务。
""", encoding="utf-8")

(sample_dir / "prompt_tips.md").write_text("""# Prompt Engineering 技巧

## 常用策略

1. **System Prompt**: 设定 AI 的角色和行为规则
2. **Few-Shot**: 给出示例引导输出格式
3. **CoT**: 让 AI 分步推理
4. **Structured Output**: 指定输出为 JSON 等格式

## 最佳实践

- 越具体越好
- 用"你必须"表达强约束
- 给出输出格式的示例
""", encoding="utf-8")

# Load a single file
loader = TextLoader(str(sample_dir / "rag_intro.md"), encoding="utf-8")
docs = loader.load()
print(f"\n--- TextLoader ---")
print(f"加载了 {len(docs)} 个文档")
print(f"内容预览: {docs[0].page_content[:100]}...")
print(f"元数据: {docs[0].metadata}")


# ============================================================
# 3. DirectoryLoader — 加载整个目录
# ============================================================

dir_loader = DirectoryLoader(
    str(sample_dir),
    glob="**/*.md",           # Only load .md files
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
    show_progress=True,
)

all_docs = dir_loader.load()
print(f"\n--- DirectoryLoader ---")
print(f"加载了 {len(all_docs)} 个文档")
for doc in all_docs:
    source = Path(doc.metadata["source"]).name
    print(f"  {source}: {len(doc.page_content)} 字符")


# ============================================================
# 4. 自定义 Loader — 加载特殊格式
# ============================================================

class MarkdownSectionLoader:
    """
    Custom loader that splits a Markdown file by headings.
    Each section becomes a separate Document.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list[Document]:
        """Split markdown by ## headings into separate documents"""
        content = Path(self.file_path).read_text(encoding="utf-8")
        sections = []
        current_title = ""
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                # Save previous section
                if current_content:
                    sections.append(Document(
                        page_content="\n".join(current_content).strip(),
                        metadata={
                            "source": self.file_path,
                            "section": current_title,
                        },
                    ))
                current_title = line[3:].strip()
                current_content = [line]
            elif line.startswith("# ") and not current_title:
                current_title = line[2:].strip()
                current_content = [line]
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_content:
            sections.append(Document(
                page_content="\n".join(current_content).strip(),
                metadata={"source": self.file_path, "section": current_title},
            ))

        return sections


print(f"\n--- 自定义 Loader ---")
section_loader = MarkdownSectionLoader(str(sample_dir / "rag_intro.md"))
sections = section_loader.load()
for sec in sections:
    print(f"  [{sec.metadata['section']}] {sec.page_content[:60]}...")


# ============================================================
# 5. 元数据增强 — 给文档添加有用的元数据
# ============================================================

def enrich_metadata(docs: list[Document]) -> list[Document]:
    """Add useful metadata to documents for better retrieval"""
    for doc in docs:
        source = Path(doc.metadata.get("source", ""))
        doc.metadata["file_name"] = source.name
        doc.metadata["file_type"] = source.suffix
        doc.metadata["char_count"] = len(doc.page_content)
        doc.metadata["word_count"] = len(doc.page_content.split())
        # Rough token estimate
        doc.metadata["estimated_tokens"] = int(len(doc.page_content) * 1.5)
    return docs

enriched = enrich_metadata(all_docs)
print(f"\n--- 元数据增强 ---")
for doc in enriched:
    print(f"  {doc.metadata['file_name']}: {doc.metadata['char_count']} 字符, "
          f"~{doc.metadata['estimated_tokens']} tokens")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 写一个 loader 加载你自己的 gitbook 文档目录
# 路径: docs/14-AI/ 下的所有 .md 文件
# 加载后打印每个文件的路径和字符数

# TODO 2: 改进 MarkdownSectionLoader
# - 支持 #, ##, ### 三级标题
# - 在 metadata 中记录标题层级
# - 支持提取文档中的代码块作为单独的 Document

# TODO 3: 实现一个 GitHistoryLoader
# 读取 git log 的输出，每个 commit 变成一个 Document
# metadata 包含: hash, author, date, message
# 提示: subprocess.run(["git", "log", "--oneline", "-20"])
