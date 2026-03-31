"""
Day 6-7: 综合练习 — 测试和调优 RAG 系统

这个项目综合运用本周所有知识点：
- Day 1: RetrievalQA Chain（问答链构建）
- Day 2: Prompt Template（模板优化和来源引用）
- Day 3: 参数调优（chunk_size、k、temperature）
- Day 4: 防幻觉（检索不到时说"不知道"）
- Day 5: Conversational RAG（对话历史和追问）

用法:
  python day67_testing.py build              # 构建知识库
  python day67_testing.py ask "你的问题"      # 单次提问
  python day67_testing.py chat               # 交互式对话
  python day67_testing.py evaluate           # 运行评估测试集
  python day67_testing.py benchmark          # 参数基准测试
"""

import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


# ============================================================
# 1. 配置管理
# JS 对比：类似 next.config.js / vite.config.ts 的作用
# ============================================================

@dataclass
class RAGConfig:
    """Configuration for the RAG system, with sensible defaults"""
    # 模型配置
    llm_model: str = "qwen2.5:7b"
    embedding_model: str = "nomic-embed-text"
    temperature: float = 0.3

    # 切分配置
    chunk_size: int = 400
    chunk_overlap: int = 50
    separators: list[str] = field(
        default_factory=lambda: ["\n\n", "\n", "。", "，", " ", ""]
    )

    # 检索配置
    search_type: str = "similarity"  # "similarity" or "mmr"
    k: int = 3
    relevance_threshold: float = 0.3

    # 对话配置
    max_history: int = 5

    # 存储配置
    persist_directory: str = "./chroma_week6_test"
    collection_name: str = "week6_test"


# Default configuration instance
DEFAULT_CONFIG = RAGConfig()


# ============================================================
# 2. 知识库构建器
# 支持从多种来源加载文档
# ============================================================

class KnowledgeBaseBuilder:
    """
    Build a knowledge base from various document sources.
    Supports plain text strings, file paths, and Document objects.
    """

    def __init__(self, config: RAGConfig = DEFAULT_CONFIG):
        self.config = config
        self.documents: list[Document] = []

    def add_text(self, text: str, source: str = "inline") -> "KnowledgeBaseBuilder":
        """Add a plain text string as a document"""
        self.documents.append(
            Document(page_content=text, metadata={"source": source})
        )
        return self  # Return self for method chaining

    def add_file(self, file_path: str) -> "KnowledgeBaseBuilder":
        """Load a text file and add it as a document"""
        path = Path(file_path)
        if not path.exists():
            print(f"警告: 文件不存在: {file_path}")
            return self
        content = path.read_text(encoding="utf-8")
        self.documents.append(
            Document(page_content=content, metadata={"source": path.name})
        )
        return self

    def add_directory(self, dir_path: str, glob: str = "**/*.md") -> "KnowledgeBaseBuilder":
        """Load all matching files from a directory"""
        path = Path(dir_path)
        if not path.exists():
            print(f"警告: 目录不存在: {dir_path}")
            return self

        files = list(path.glob(glob))
        for file in files:
            content = file.read_text(encoding="utf-8")
            self.documents.append(
                Document(
                    page_content=content,
                    metadata={"source": str(file.relative_to(path))},
                )
            )
        print(f"从 {dir_path} 加载了 {len(files)} 个文件")
        return self

    def build(self) -> Chroma:
        """Split documents and build the vector store"""
        if not self.documents:
            raise ValueError("没有文档可构建，请先添加文档")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.separators,
        )
        chunks = splitter.split_documents(self.documents)
        print(f"文档切分: {len(self.documents)} 篇 → {len(chunks)} 块")

        embeddings = OllamaEmbeddings(model=self.config.embedding_model)
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=self.config.collection_name,
            persist_directory=self.config.persist_directory,
        )
        print(f"向量库构建完成: {vectorstore._collection.count()} 条向量")
        return vectorstore


# ============================================================
# 3. RAG 引擎 — 综合 Day 1-5 所有功能
# ============================================================

# Production-grade prompt template combining all best practices
PRODUCTION_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""你是一个专业的技术文档助手。请严格根据提供的参考文档回答用户问题。

规则：
1. 只使用参考文档中的信息来回答，不要使用你自己的知识
2. 在回答中引用来源，格式为 [来源: 文件名]
3. 如果参考文档中没有相关信息，回答："根据现有知识库，我无法回答这个问题。"
4. 回答要简洁、准确、分点列出
5. 使用 Markdown 格式

参考文档：
{context}

用户问题：{question}

回答：""",
)

# Question rewriting prompt for conversational mode
REWRITE_PROMPT = PromptTemplate.from_template(
    """给定对话历史和最新问题，把最新问题改写成独立的完整问题。
只返回改写后的问题，不要其他内容。如果已经是独立问题，直接返回。

对话历史：
{chat_history}

最新问题：{question}

独立问题："""
)


class RAGEngine:
    """
    Production-grade RAG engine that combines:
    - RetrievalQA chain with custom prompt
    - Relevance score filtering (anti-hallucination)
    - Conversational mode with question rewriting
    - Performance tracking
    """

    def __init__(self, config: RAGConfig = DEFAULT_CONFIG):
        self.config = config
        self.llm = Ollama(
            model=config.llm_model,
            temperature=config.temperature,
        )
        self.embeddings = OllamaEmbeddings(model=config.embedding_model)
        self.vectorstore: Optional[Chroma] = None
        self.chat_history: list[tuple[str, str]] = []

        # Performance tracking
        self.query_log: list[dict] = []

    def load_vectorstore(self) -> None:
        """Load existing vector store from disk"""
        self.vectorstore = Chroma(
            collection_name=self.config.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.config.persist_directory,
        )
        count = self.vectorstore._collection.count()
        print(f"向量库已加载: {count} 条向量")

    def set_vectorstore(self, vectorstore: Chroma) -> None:
        """Set the vector store directly (for testing)"""
        self.vectorstore = vectorstore

    def _format_docs_with_sources(self, docs: list[Document]) -> str:
        """Format retrieved documents with source metadata for citation"""
        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            content = doc.page_content.strip()
            parts.append(f"[文档 {i}] (来源: {source})\n{content}")
        return "\n\n---\n\n".join(parts)

    def _format_chat_history(self) -> str:
        """Format conversation history for the rewriting prompt"""
        if not self.chat_history:
            return "（无历史对话）"
        lines = []
        for user_msg, ai_msg in self.chat_history:
            lines.append(f"用户: {user_msg}")
            lines.append(f"AI: {ai_msg[:100]}...")
        return "\n".join(lines)

    def _rewrite_question(self, question: str) -> str:
        """Rewrite a follow-up question into a standalone question using history"""
        if not self.chat_history:
            return question
        history_text = self._format_chat_history()
        prompt = REWRITE_PROMPT.format(
            chat_history=history_text,
            question=question,
        )
        return self.llm.invoke(prompt).strip()

    def ask(
        self,
        question: str,
        conversational: bool = False,
    ) -> dict:
        """
        Ask a question and get a RAG-powered answer.

        Args:
            question: The user's question
            conversational: Whether to use conversation history

        Returns:
            Dict with answer, sources, confidence, timing, etc.
        """
        if not self.vectorstore:
            raise ValueError("向量库未加载，请先调用 load_vectorstore() 或 set_vectorstore()")

        start_time = time.time()
        result = {
            "question": question,
            "rewritten_question": question,
            "answer": "",
            "sources": [],
            "confidence": "none",
            "retrieval_scores": [],
            "elapsed_seconds": 0,
        }

        # Step 1: 改写问题（对话模式）
        if conversational and self.chat_history:
            result["rewritten_question"] = self._rewrite_question(question)

        search_question = result["rewritten_question"]

        # Step 2: 检索 + 相关性过滤
        results_with_scores = self.vectorstore.similarity_search_with_relevance_scores(
            search_question, k=self.config.k
        )

        # Filter by relevance threshold
        relevant_docs = []
        all_scores = []
        for doc, score in results_with_scores:
            all_scores.append({"source": doc.metadata.get("source", "unknown"), "score": round(score, 3)})
            if score >= self.config.relevance_threshold:
                relevant_docs.append(doc)

        result["retrieval_scores"] = all_scores

        # Step 3: 判断能否回答
        if not relevant_docs:
            result["answer"] = "根据现有知识库，我无法回答这个问题。建议您查阅相关文档或调整问题。"
            result["confidence"] = "none"
        else:
            # Build context with source metadata
            context = self._format_docs_with_sources(relevant_docs)
            sources = list(set(
                doc.metadata.get("source", "unknown") for doc in relevant_docs
            ))
            result["sources"] = sources

            # Determine confidence from average relevance score
            avg_score = sum(
                s["score"] for s in all_scores
                if s["score"] >= self.config.relevance_threshold
            ) / len(relevant_docs)

            if avg_score >= 0.7:
                result["confidence"] = "high"
            elif avg_score >= 0.5:
                result["confidence"] = "medium"
            else:
                result["confidence"] = "low"

            # Step 4: 生成回答
            prompt = PRODUCTION_PROMPT.format(
                context=context,
                question=question,
            )
            result["answer"] = self.llm.invoke(prompt)

        # Step 5: 更新对话历史
        if conversational:
            self.chat_history.append((question, result["answer"][:200]))
            if len(self.chat_history) > self.config.max_history:
                self.chat_history = self.chat_history[-self.config.max_history:]

        result["elapsed_seconds"] = round(time.time() - start_time, 2)

        # Log the query for later analysis
        self.query_log.append(result)

        return result

    def reset_history(self):
        """Clear conversation history"""
        self.chat_history = []

    def get_stats(self) -> dict:
        """Get statistics about queries processed so far"""
        if not self.query_log:
            return {"total_queries": 0}

        total = len(self.query_log)
        answered = sum(1 for q in self.query_log if q["confidence"] != "none")
        avg_time = sum(q["elapsed_seconds"] for q in self.query_log) / total

        confidence_dist = {}
        for q in self.query_log:
            c = q["confidence"]
            confidence_dist[c] = confidence_dist.get(c, 0) + 1

        return {
            "total_queries": total,
            "answered": answered,
            "unanswered": total - answered,
            "answer_rate": round(answered / total * 100, 1),
            "avg_time_seconds": round(avg_time, 2),
            "confidence_distribution": confidence_dist,
        }


# ============================================================
# 4. 评估测试集
# 用预定义的问题和期望答案来评估 RAG 系统
# ============================================================

# Evaluation test cases with expected behavior
EVAL_TEST_SET = [
    {
        "question": "React useState 是什么？有什么用？",
        "expected_behavior": "should_answer",
        "keywords": ["useState", "状态", "函数组件"],
        "category": "in_scope",
    },
    {
        "question": "Next.js 的文件系统路由是怎么工作的？",
        "expected_behavior": "should_answer",
        "keywords": ["文件", "路由", "page.tsx", "app"],
        "category": "in_scope",
    },
    {
        "question": "如何优化 React 应用的性能？",
        "expected_behavior": "should_answer",
        "keywords": ["性能", "memo", "优化"],
        "category": "in_scope",
    },
    {
        "question": "TypeScript 的泛型组件怎么写？",
        "expected_behavior": "should_answer",
        "keywords": ["泛型", "generic", "TypeScript"],
        "category": "in_scope",
    },
    {
        "question": "如何用 Go 语言写微服务？",
        "expected_behavior": "should_not_answer",
        "keywords": ["不知道", "无法回答"],
        "category": "out_of_scope",
    },
    {
        "question": "MySQL 和 PostgreSQL 哪个好？",
        "expected_behavior": "should_not_answer",
        "keywords": ["不知道", "无法回答"],
        "category": "out_of_scope",
    },
    {
        "question": "Docker 容器网络怎么配置？",
        "expected_behavior": "should_not_answer",
        "keywords": ["不知道", "无法回答"],
        "category": "out_of_scope",
    },
]


@dataclass
class EvalResult:
    """Result of evaluating a single test case"""
    question: str
    category: str
    expected_behavior: str
    actual_answer: str
    confidence: str
    passed: bool
    elapsed_seconds: float
    reason: str = ""


def evaluate_rag(engine: RAGEngine) -> list[EvalResult]:
    """
    Run the evaluation test set against the RAG engine
    and return results for each test case.
    """
    results = []

    for test in EVAL_TEST_SET:
        answer_result = engine.ask(test["question"])
        answer = answer_result["answer"]

        # Determine if the test passed
        if test["expected_behavior"] == "should_answer":
            # Check if answer contains expected keywords
            has_keywords = any(kw in answer for kw in test["keywords"])
            not_refused = "无法回答" not in answer and "不知道" not in answer
            passed = has_keywords and not_refused
            reason = ""
            if not passed:
                if not has_keywords:
                    reason = f"缺少关键词: {test['keywords']}"
                if not not_refused:
                    reason = "错误地拒绝回答"
        else:
            # Should not answer — check if it correctly refused
            refused = "无法回答" in answer or "不知道" in answer
            passed = refused
            reason = "" if passed else "未能拒绝回答，可能存在幻觉"

        results.append(EvalResult(
            question=test["question"],
            category=test["category"],
            expected_behavior=test["expected_behavior"],
            actual_answer=answer[:150],
            confidence=answer_result["confidence"],
            passed=passed,
            elapsed_seconds=answer_result["elapsed_seconds"],
            reason=reason,
        ))

    return results


def print_eval_report(results: list[EvalResult]):
    """Print a formatted evaluation report"""

    print("\n" + "=" * 60)
    print("RAG 评估报告")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    in_scope = [r for r in results if r.category == "in_scope"]
    out_scope = [r for r in results if r.category == "out_of_scope"]

    print(f"\n总体: {passed}/{total} 通过 ({passed/total*100:.0f}%)")

    in_passed = sum(1 for r in in_scope if r.passed)
    out_passed = sum(1 for r in out_scope if r.passed)
    print(f"  知识库内: {in_passed}/{len(in_scope)} 通过")
    print(f"  知识库外: {out_passed}/{len(out_scope)} 通过")

    avg_time = sum(r.elapsed_seconds for r in results) / total
    print(f"  平均耗时: {avg_time:.2f}s")

    # Detailed results
    print(f"\n{'─' * 60}")
    print(f"{'问题':<30} {'期望':<15} {'结果':<6} {'置信度':<8} {'耗时'}")
    print(f"{'─' * 60}")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        q = r.question[:28] + ".." if len(r.question) > 30 else r.question
        expected = "能回答" if r.expected_behavior == "should_answer" else "拒绝回答"
        print(f"{q:<30} {expected:<15} {status:<6} {r.confidence:<8} {r.elapsed_seconds:.1f}s")
        if not r.passed and r.reason:
            print(f"  └─ 原因: {r.reason}")

    print(f"{'─' * 60}")


# ============================================================
# 5. 参数基准测试
# 自动测试不同参数组合，找到最佳配置
# ============================================================

@dataclass
class BenchmarkResult:
    """Result of a parameter benchmark run"""
    config_label: str
    chunk_size: int
    k: int
    temperature: float
    pass_rate: float
    avg_time: float
    in_scope_pass: float
    out_scope_pass: float


def run_benchmark(
    documents: list[Document],
    configs: list[dict],
) -> list[BenchmarkResult]:
    """
    Run benchmark tests with different parameter configurations
    and return performance metrics for each.
    """
    results = []

    for cfg in configs:
        print(f"\n--- 测试配置: {cfg['label']} ---")

        rag_config = RAGConfig(
            chunk_size=cfg.get("chunk_size", 400),
            chunk_overlap=cfg.get("chunk_overlap", 50),
            k=cfg.get("k", 3),
            temperature=cfg.get("temperature", 0.3),
            collection_name=f"benchmark_{cfg['label'].replace(' ', '_')}",
            persist_directory="./chroma_benchmark",
        )

        # Build knowledge base
        builder = KnowledgeBaseBuilder(rag_config)
        for doc in documents:
            builder.documents.append(doc)
        vectorstore = builder.build()

        # Create engine and run evaluation
        engine = RAGEngine(rag_config)
        engine.set_vectorstore(vectorstore)
        eval_results = evaluate_rag(engine)

        # Calculate metrics
        total = len(eval_results)
        passed = sum(1 for r in eval_results if r.passed)
        in_scope = [r for r in eval_results if r.category == "in_scope"]
        out_scope = [r for r in eval_results if r.category == "out_of_scope"]
        in_passed = sum(1 for r in in_scope if r.passed) / max(len(in_scope), 1)
        out_passed = sum(1 for r in out_scope if r.passed) / max(len(out_scope), 1)
        avg_time = sum(r.elapsed_seconds for r in eval_results) / total

        results.append(BenchmarkResult(
            config_label=cfg["label"],
            chunk_size=cfg.get("chunk_size", 400),
            k=cfg.get("k", 3),
            temperature=cfg.get("temperature", 0.3),
            pass_rate=passed / total,
            avg_time=avg_time,
            in_scope_pass=in_passed,
            out_scope_pass=out_passed,
        ))

        # Cleanup
        vectorstore.delete_collection()

    return results


def print_benchmark_report(results: list[BenchmarkResult]):
    """Print a formatted benchmark comparison report"""

    print("\n" + "=" * 70)
    print("参数基准测试报告")
    print("=" * 70)

    print(f"\n{'配置':<18} {'chunk':<8} {'k':<4} {'temp':<6} {'通过率':<8} {'库内':<8} {'库外':<8} {'耗时'}")
    print(f"{'─' * 70}")

    for r in results:
        print(
            f"{r.config_label:<18} "
            f"{r.chunk_size:<8} "
            f"{r.k:<4} "
            f"{r.temperature:<6} "
            f"{r.pass_rate*100:>5.0f}%  "
            f"{r.in_scope_pass*100:>5.0f}%  "
            f"{r.out_scope_pass*100:>5.0f}%  "
            f"{r.avg_time:>5.1f}s"
        )

    # Find best configuration
    best = max(results, key=lambda r: r.pass_rate)
    print(f"\n最佳配置: {best.config_label} (通过率 {best.pass_rate*100:.0f}%)")


# ============================================================
# 6. 示例知识库文档
# 用于没有外部文档时的演示
# ============================================================

SAMPLE_DOCS = [
    Document(
        page_content="""
React Hooks 是 React 16.8 引入的特性。

常用 Hooks：
- useState：管理组件状态，返回 [state, setState]
- useEffect：处理副作用，第二参数是依赖数组
- useMemo：缓存计算结果，避免重复计算
- useCallback：缓存回调函数，优化子组件渲染
- useRef：持有可变引用，不触发重渲染
- useContext：访问 React Context 的值
- useReducer：复杂状态管理，类似 Redux 的 dispatch + reducer

自定义 Hook：
- 以 use 开头的函数
- 可以组合其他 Hooks
- 用于抽取可复用的状态逻辑
""",
        metadata={"source": "react-hooks.md"},
    ),
    Document(
        page_content="""
React 性能优化最佳实践。

渲染优化：
- React.memo：包裹纯展示组件，避免不必要的重渲染
- useCallback：缓存传给子组件的函数引用
- useMemo：缓存计算密集的结果
- 状态下沉：把状态放在最近的需要它的组件

代码分割：
- React.lazy + Suspense：路由级别懒加载
- dynamic import：按需加载模块

列表优化：
- 使用 react-window 或 react-virtuoso 实现虚拟列表
- 为列表项设置稳定的 key

数据获取：
- 使用 React Query 或 SWR 管理服务端状态
- 实现请求去重和缓存
""",
        metadata={"source": "react-performance.md"},
    ),
    Document(
        page_content="""
Next.js App Router 是 Next.js 13+ 的路由系统。

文件约定：
- page.tsx：页面组件
- layout.tsx：共享布局
- loading.tsx：加载状态
- error.tsx：错误边界
- not-found.tsx：404 页面

路由规则：
- app/page.tsx → /
- app/about/page.tsx → /about
- app/blog/[slug]/page.tsx → /blog/:slug（动态路由）
- app/(marketing)/page.tsx → /（路由组，不影响 URL）

数据获取：
- Server Components 中直接 async/await
- 使用 fetch 自动去重和缓存
- revalidate 参数控制缓存策略
""",
        metadata={"source": "nextjs-app-router.md"},
    ),
    Document(
        page_content="""
TypeScript 与 React 结合使用。

组件类型：
- React.FC<Props>：函数组件类型（有争议，部分团队不推荐）
- 直接标注函数参数和返回值更灵活

Props 类型定义：
```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}
```

常用类型：
- React.ReactNode：可渲染内容
- React.ChangeEvent<HTMLInputElement>：输入事件
- React.MouseEvent<HTMLButtonElement>：点击事件

泛型组件：
```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
}
function List<T>({ items, renderItem }: ListProps<T>) { ... }
```
""",
        metadata={"source": "typescript-react.md"},
    ),
]


# ============================================================
# 7. CLI 命令实现
# ============================================================

def cmd_build(doc_dir: Optional[str] = None):
    """Build the knowledge base from sample docs or a directory"""

    print("=" * 60)
    print("构建知识库")
    print("=" * 60)

    builder = KnowledgeBaseBuilder(DEFAULT_CONFIG)

    if doc_dir:
        builder.add_directory(doc_dir)
    else:
        print("使用内置示例文档（如需使用自己的文档，请传入目录路径）")
        for doc in SAMPLE_DOCS:
            builder.documents.append(doc)

    vectorstore = builder.build()
    print(f"\n知识库构建完成！存储在 {DEFAULT_CONFIG.persist_directory}")
    print(f"向量数: {vectorstore._collection.count()}")


def cmd_ask(question: str):
    """Ask a single question"""

    engine = RAGEngine(DEFAULT_CONFIG)
    engine.load_vectorstore()

    print(f"\n问题: {question}")
    result = engine.ask(question)

    print(f"\n回答: {result['answer']}")
    print(f"\n置信度: {result['confidence']}")
    if result['sources']:
        print(f"来源: {', '.join(result['sources'])}")
    print(f"耗时: {result['elapsed_seconds']}s")


def cmd_chat():
    """Run interactive conversational RAG chat"""

    print("=" * 60)
    print("交互式 RAG 聊天")
    print("=" * 60)
    print("命令: 'quit' 退出, 'reset' 清除历史, 'stats' 查看统计")
    print("=" * 60)

    engine = RAGEngine(DEFAULT_CONFIG)

    # Try to load existing vectorstore, or build from sample docs
    try:
        engine.load_vectorstore()
    except Exception:
        print("未找到已有向量库，使用示例文档构建...")
        builder = KnowledgeBaseBuilder(DEFAULT_CONFIG)
        for doc in SAMPLE_DOCS:
            builder.documents.append(doc)
        vectorstore = builder.build()
        engine.set_vectorstore(vectorstore)

    while True:
        try:
            question = input("\n你: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not question:
            continue

        if question.lower() == "quit":
            break
        elif question.lower() == "reset":
            engine.reset_history()
            print("对话历史已清除")
            continue
        elif question.lower() == "stats":
            stats = engine.get_stats()
            print(f"\n查询统计:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            continue

        result = engine.ask(question, conversational=True)

        if result["question"] != result["rewritten_question"]:
            print(f"[改写] {result['rewritten_question']}")

        print(f"\nAI: {result['answer']}")

        confidence_icon = {
            "high": "+++", "medium": "++", "low": "+", "none": "---"
        }
        icon = confidence_icon.get(result['confidence'], '?')
        print(f"\n[置信度: {icon} {result['confidence']}]", end="")
        if result['sources']:
            print(f" [来源: {', '.join(result['sources'])}]", end="")
        print(f" [耗时: {result['elapsed_seconds']}s]")

    # Print final stats
    stats = engine.get_stats()
    if stats["total_queries"] > 0:
        print(f"\n会话统计: {stats['total_queries']} 次查询, "
              f"回答率 {stats['answer_rate']}%, "
              f"平均耗时 {stats['avg_time_seconds']}s")

    print("\n再见！")


def cmd_evaluate():
    """Run evaluation test set"""

    print("=" * 60)
    print("运行 RAG 评估测试集")
    print("=" * 60)

    engine = RAGEngine(DEFAULT_CONFIG)

    # Build from sample docs for evaluation
    builder = KnowledgeBaseBuilder(DEFAULT_CONFIG)
    for doc in SAMPLE_DOCS:
        builder.documents.append(doc)
    vectorstore = builder.build()
    engine.set_vectorstore(vectorstore)

    # Run evaluation
    results = evaluate_rag(engine)
    print_eval_report(results)

    # Cleanup
    vectorstore.delete_collection()


def cmd_benchmark():
    """Run parameter benchmark tests"""

    print("=" * 60)
    print("运行参数基准测试")
    print("=" * 60)

    benchmark_configs = [
        {"label": "small-chunk-low-k", "chunk_size": 150, "k": 2, "temperature": 0.3},
        {"label": "small-chunk-high-k", "chunk_size": 150, "k": 5, "temperature": 0.3},
        {"label": "medium-chunk-low-k", "chunk_size": 400, "k": 2, "temperature": 0.3},
        {"label": "medium-chunk-mid-k", "chunk_size": 400, "k": 3, "temperature": 0.3},
        {"label": "large-chunk-mid-k", "chunk_size": 800, "k": 3, "temperature": 0.3},
        {"label": "large-chunk-high-k", "chunk_size": 800, "k": 5, "temperature": 0.3},
    ]

    results = run_benchmark(SAMPLE_DOCS, benchmark_configs)
    print_benchmark_report(results)


# ============================================================
# 8. CLI 入口
# ============================================================

def print_usage():
    """Print CLI usage instructions"""
    print("""
RAG 测试工具 — Week 6 综合练习

用法:
  python day67_testing.py build [目录路径]     构建知识库（默认用内置文档）
  python day67_testing.py ask "问题"           单次提问
  python day67_testing.py chat                 交互式对话
  python day67_testing.py evaluate             运行评估测试集
  python day67_testing.py benchmark            参数基准测试

示例:
  python day67_testing.py build
  python day67_testing.py ask "React Hooks 有哪些？"
  python day67_testing.py chat
  python day67_testing.py evaluate
  python day67_testing.py benchmark
""")


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1]

    if command == "build":
        doc_dir = sys.argv[2] if len(sys.argv) >= 3 else None
        cmd_build(doc_dir)
    elif command == "ask" and len(sys.argv) >= 3:
        cmd_ask(sys.argv[2])
    elif command == "chat":
        cmd_chat()
    elif command == "evaluate":
        cmd_evaluate()
    elif command == "benchmark":
        cmd_benchmark()
    else:
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()


# ============================================================
# 练习题
# ============================================================

# TODO 1: 用你自己的文档构建知识库
#         python day67_testing.py build /path/to/your/docs
#         然后用 chat 模式测试各种问题
#         记录哪些问题效果好，哪些需要改进

# TODO 2: 在 EVAL_TEST_SET 中添加更多测试用例
#         覆盖你知识库中的主要话题
#         确保每个话题至少有 2-3 个测试问题

# TODO 3: 改进 evaluate_rag 函数，添加 LLM 自动评分：
#         用 LLM 给回答打分（1-5 分），而不只是关键词匹配
#         提示：写一个评分 prompt，让 LLM 判断回答质量

# TODO 4: 给 RAGEngine 添加 export_log 方法：
#         把 query_log 导出为 JSON 文件
#         包含每次查询的 question、answer、confidence、sources、timing
#         方便后续分析和改进

# TODO 5: 在 benchmark 中添加更多配置组合：
#         - 不同的 search_type（similarity vs mmr）
#         - 不同的 relevance_threshold
#         - 不同的 prompt 模板
#         找到你文档的最佳参数组合
