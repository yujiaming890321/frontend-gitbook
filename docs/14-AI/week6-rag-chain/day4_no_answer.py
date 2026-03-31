"""
Day 4: 处理"检索不到"的情况 — 让 AI 说"我不知道"而不是编造
AI 开发中最重要的安全措施：防止 LLM 幻觉 (Hallucination)

什么是 LLM 幻觉？
  - LLM 会"自信地"编造不存在的信息
  - 在 RAG 场景中，如果检索不到相关文档，LLM 可能用自己的"记忆"胡编
  - 这在企业应用中是绝对不能接受的（法律、医疗、金融...）

JS/TS 对比：
  - 类似前端的"空状态"处理：数据为空时显示友好提示，而不是崩溃
  - if (!data) return <EmptyState /> 的后端版本
"""

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


# ============================================================
# 1. 准备知识库（范围有限的文档）
# 故意只放前端相关的文档，这样问后端/其他问题时就检索不到
# ============================================================

# Knowledge base documents with a limited scope (frontend only)
knowledge_base = [
    Document(
        page_content="""
React 18 引入了并发特性 (Concurrent Features)。

核心概念：
- Automatic Batching：自动合并多个 setState 更新
- Transitions：区分紧急更新和非紧急更新
- Suspense 改进：支持服务端组件的 Suspense
- Streaming SSR：流式服务端渲染

使用 startTransition 标记非紧急更新：
```javascript
import { startTransition } from 'react';

// 紧急更新（用户输入）
setInputValue(input);

// 非紧急更新（搜索结果）
startTransition(() => {
  setSearchResults(results);
});
```
""",
        metadata={"source": "react-18-features.md"},
    ),
    Document(
        page_content="""
Vite 是新一代前端构建工具，由 Vue 的作者尤雨溪创建。

核心特性：
- 极速的开发服务器启动（利用浏览器原生 ESM）
- 热模块替换 (HMR) 极快
- 使用 Rollup 进行生产打包
- 丰富的插件生态

与 Webpack 对比：
- 开发启动：Vite 秒级 vs Webpack 分钟级
- HMR 速度：Vite 毫秒级 vs Webpack 秒级
- 配置复杂度：Vite 简单 vs Webpack 复杂
- 生态成熟度：Webpack 更成熟，Vite 快速追赶

迁移建议：
- 新项目推荐 Vite
- 旧项目可以渐进迁移
- 注意插件兼容性
""",
        metadata={"source": "vite-guide.md"},
    ),
    Document(
        page_content="""
CSS Container Queries 使用指南。

Container Queries 允许组件根据其容器的大小来调整样式，而不是根据视口大小。

基本语法：
```css
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
```

与 Media Queries 对比：
- Media Queries：基于视口大小
- Container Queries：基于容器大小
- Container Queries 让组件更独立、可复用
""",
        metadata={"source": "container-queries.md"},
    ),
]


# ============================================================
# 2. 方法一：通过 Prompt 模板控制（最简单）
# 在 prompt 中明确告诉 LLM "不知道就说不知道"
# ============================================================

# Prompt template that instructs the LLM to admit when it lacks information
no_hallucination_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""你是一个严谨的技术文档助手。请严格根据提供的参考文档回答问题。

重要规则：
1. 只使用参考文档中的信息来回答
2. 如果参考文档中没有与问题相关的信息，你必须回答：
   "根据现有知识库，我无法回答这个问题。建议您查阅相关专业文档。"
3. 不要使用你自己的知识来补充或编造信息
4. 不要猜测或推断文档中没有的内容
5. 如果参考文档只能部分回答问题，请说明哪些部分能回答，哪些部分无法回答

参考文档：
{context}

用户问题：{question}

回答：""",
)


def demo_prompt_approach():
    """Demo: use prompt template to prevent hallucination"""

    print("=" * 60)
    print("方法一：通过 Prompt 模板防止幻觉")
    print("=" * 60)

    # 构建向量库
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(knowledge_base)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="no_answer_v1"
    )

    llm = Ollama(model="qwen2.5:7b", temperature=0.1)  # 低温度减少随机性
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": no_hallucination_prompt},
    )

    # 测试：知识库内的问题（应该能回答）
    in_scope_questions = [
        "React 18 有什么新特性？",
        "Vite 和 Webpack 有什么区别？",
    ]

    # 测试：知识库外的问题（应该说"不知道"）
    out_of_scope_questions = [
        "如何用 Python 连接 MySQL 数据库？",
        "Kubernetes 的 Pod 调度策略有哪些？",
        "怎么做微服务架构？",
    ]

    print("\n--- 知识库内的问题（应该能回答）---")
    for q in in_scope_questions:
        result = qa_chain.invoke({"query": q})
        answer = result["result"][:150]
        print(f"\n问: {q}")
        print(f"答: {answer}...")

    print("\n--- 知识库外的问题（应该说"不知道"）---")
    for q in out_of_scope_questions:
        result = qa_chain.invoke({"query": q})
        answer = result["result"][:150]
        print(f"\n问: {q}")
        print(f"答: {answer}...")

    vectorstore.delete_collection()


# ============================================================
# 3. 方法二：检索相关性评分过滤
# 在检索阶段就过滤掉不相关的文档
# ============================================================

def demo_score_filtering():
    """
    Demo: filter retrieved documents by relevance score.
    If all documents score below threshold, return "I don't know".
    """

    print("\n" + "=" * 60)
    print("方法二：基于相关性评分过滤")
    print("=" * 60)

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(knowledge_base)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="no_answer_v2"
    )

    # Use similarity_search_with_relevance_scores to get scores
    # score range: 0.0 (irrelevant) to 1.0 (perfect match)
    questions = [
        "React 18 的并发特性是什么？",          # 知识库内
        "如何搭建 Kubernetes 集群？",            # 知识库外
        "Vite 的 HMR 有多快？",                 # 知识库内
        "Python 的 asyncio 怎么用？",            # 知识库外
    ]

    # Relevance score threshold — documents below this score are considered irrelevant
    RELEVANCE_THRESHOLD = 0.3

    for question in questions:
        print(f"\n问题: {question}")

        # Retrieve documents with relevance scores
        results_with_scores = vectorstore.similarity_search_with_relevance_scores(
            question, k=3
        )

        if not results_with_scores:
            print("  结果: 没有检索到任何文档")
            print("  回答: 根据现有知识库，我无法回答这个问题。")
            continue

        # Check if any document is relevant enough
        relevant_docs = [
            (doc, score) for doc, score in results_with_scores
            if score >= RELEVANCE_THRESHOLD
        ]

        print(f"  检索到 {len(results_with_scores)} 个文档：")
        for doc, score in results_with_scores:
            status = "✅ 相关" if score >= RELEVANCE_THRESHOLD else "❌ 不相关"
            preview = doc.page_content[:50].replace("\n", " ").strip()
            print(f"    {status} (score={score:.3f}) {preview}...")

        if not relevant_docs:
            print("  回答: 根据现有知识库，我无法回答这个问题。所有检索到的文档相关性都低于阈值。")
        else:
            print(f"  → 有 {len(relevant_docs)} 个相关文档，可以回答")

    vectorstore.delete_collection()


# ============================================================
# 4. 方法三：两阶段检查 — 先判断能否回答，再回答
# 先用 LLM 判断检索到的文档是否能回答问题
# ============================================================

def demo_two_stage_check():
    """
    Demo: two-stage approach.
    Stage 1: Ask LLM if the retrieved documents can answer the question.
    Stage 2: If yes, generate the answer; if no, return "I don't know".
    """

    print("\n" + "=" * 60)
    print("方法三：两阶段检查（先判断能否回答）")
    print("=" * 60)

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(knowledge_base)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="no_answer_v3"
    )

    llm = Ollama(model="qwen2.5:7b", temperature=0.1)

    # Stage 1 prompt: determine if documents can answer the question
    judge_prompt = PromptTemplate.from_template(
        """判断以下参考文档是否包含足够的信息来回答用户问题。

参考文档：
{context}

用户问题：{question}

请只回答"YES"或"NO"：
- YES：参考文档中有相关信息，可以回答
- NO：参考文档中没有相关信息，无法回答

你的判断（只回答YES或NO）："""
    )

    # Stage 2 prompt: answer the question if documents are relevant
    answer_prompt = PromptTemplate.from_template(
        """根据参考文档回答问题。回答要简洁准确，引用来源。

参考文档：
{context}

问题：{question}

回答："""
    )

    questions = [
        "Vite 和 Webpack 对比有什么优劣？",    # 知识库内
        "如何优化 Docker 镜像体积？",             # 知识库外
        "Container Queries 是什么？",             # 知识库内
    ]

    for question in questions:
        print(f"\n问题: {question}")

        # Step 1: 检索文档
        docs = vectorstore.similarity_search(question, k=3)
        context = "\n\n".join([d.page_content for d in docs])

        # Step 2: 判断能否回答
        judge_input = judge_prompt.format(context=context, question=question)
        judgment = llm.invoke(judge_input).strip().upper()
        print(f"  LLM 判断: {judgment}")

        # Step 3: 根据判断决定是否回答
        if "YES" in judgment:
            answer_input = answer_prompt.format(context=context, question=question)
            answer = llm.invoke(answer_input)
            print(f"  回答: {answer[:200]}...")
        else:
            print("  回答: 根据现有知识库，我无法回答这个问题。建议您查阅相关专业文档。")

    vectorstore.delete_collection()


# ============================================================
# 5. 方法四：后置校验 — 回答后检查是否有幻觉
# 生成回答后，用另一个 LLM 调用来验证回答是否基于文档
# ============================================================

def demo_post_validation():
    """
    Demo: post-generation validation.
    After generating an answer, use another LLM call to verify
    that the answer is grounded in the source documents.
    """

    print("\n" + "=" * 60)
    print("方法四：后置校验（回答后检查幻觉）")
    print("=" * 60)

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(knowledge_base)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="no_answer_v4"
    )

    llm = Ollama(model="qwen2.5:7b", temperature=0.1)

    # Validation prompt: check if answer is grounded in source documents
    validation_prompt = PromptTemplate.from_template(
        """你是一个事实核查员。请判断以下回答是否完全基于参考文档中的信息。

参考文档：
{context}

用户问题：{question}

AI 的回答：{answer}

请分析：
1. 回答中的每个事实是否都能在参考文档中找到依据？
2. 有没有编造的信息？

判断结果（回答 GROUNDED 或 HALLUCINATION）：
- GROUNDED：回答完全基于参考文档
- HALLUCINATION：回答包含参考文档中没有的信息

你的判断："""
    )

    question = "Vite 的核心特性有哪些？它是谁创建的？"

    # Step 1: 检索 + 生成回答
    docs = vectorstore.similarity_search(question, k=3)
    context = "\n\n".join([d.page_content for d in docs])

    answer_prompt = PromptTemplate.from_template(
        """根据参考文档回答问题。

参考文档：
{context}

问题：{question}

回答："""
    )
    answer = llm.invoke(answer_prompt.format(context=context, question=question))

    print(f"\n问题: {question}")
    print(f"回答: {answer[:300]}...")

    # Step 2: 后置校验
    validation_input = validation_prompt.format(
        context=context,
        question=question,
        answer=answer,
    )
    validation_result = llm.invoke(validation_input)
    print(f"\n校验结果: {validation_result[:200]}...")

    if "HALLUCINATION" in validation_result.upper():
        print("\n⚠️ 检测到幻觉！回答包含文档中没有的信息。")
        print("建议：重新生成回答，或标记为低可信度。")
    else:
        print("\n✅ 回答已验证，内容基于参考文档。")

    vectorstore.delete_collection()


# ============================================================
# 6. 完整的防幻觉 RAG Pipeline
# 综合以上方法，构建生产级的防幻觉流程
# ============================================================

def create_safe_rag_pipeline():
    """
    Build a production-grade RAG pipeline that combines multiple
    anti-hallucination strategies for reliable answers.
    """

    print("\n" + "=" * 60)
    print("完整的防幻觉 RAG Pipeline")
    print("=" * 60)

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(knowledge_base)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="safe_rag"
    )
    llm = Ollama(model="qwen2.5:7b", temperature=0.1)

    RELEVANCE_THRESHOLD = 0.3

    def safe_answer(question: str) -> dict:
        """
        Generate a safe answer with anti-hallucination checks.
        Returns a dict with answer, confidence, and metadata.
        """

        # Stage 1: 检索 + 相关性过滤
        results_with_scores = vectorstore.similarity_search_with_relevance_scores(
            question, k=3
        )

        relevant_docs = [
            (doc, score) for doc, score in results_with_scores
            if score >= RELEVANCE_THRESHOLD
        ]

        if not relevant_docs:
            return {
                "answer": "根据现有知识库，我无法回答这个问题。建议您查阅相关专业文档。",
                "confidence": "none",
                "source_count": 0,
                "sources": [],
                "reason": "no_relevant_documents",
            }

        # Stage 2: 使用防幻觉 prompt 生成回答
        context = "\n\n".join([doc.page_content for doc, _ in relevant_docs])
        sources = [doc.metadata.get("source", "unknown") for doc, _ in relevant_docs]
        avg_score = sum(s for _, s in relevant_docs) / len(relevant_docs)

        # Determine confidence level based on average relevance score
        if avg_score >= 0.7:
            confidence = "high"
        elif avg_score >= 0.5:
            confidence = "medium"
        else:
            confidence = "low"

        prompt = no_hallucination_prompt.format(
            context=context, question=question
        )
        answer = llm.invoke(prompt)

        return {
            "answer": answer,
            "confidence": confidence,
            "avg_relevance": round(avg_score, 3),
            "source_count": len(relevant_docs),
            "sources": sources,
            "reason": "answered",
        }

    # 测试各种问题
    test_questions = [
        "React 18 的 Automatic Batching 是什么？",   # 知识库内
        "如何部署 Spring Boot 应用到 AWS？",           # 知识库外
        "Vite 的 HMR 速度如何？",                     # 知识库内
        "GraphQL 和 REST 的区别是什么？",              # 知识库外
        "CSS Container Queries 怎么用？",              # 知识库内
    ]

    for question in test_questions:
        print(f"\n{'─' * 50}")
        print(f"问题: {question}")
        result = safe_answer(question)
        print(f"置信度: {result['confidence']}")
        if result.get('avg_relevance'):
            print(f"平均相关性: {result['avg_relevance']}")
        print(f"来源数: {result['source_count']}")
        if result['sources']:
            print(f"来源: {', '.join(result['sources'])}")
        print(f"回答: {result['answer'][:200]}...")

    vectorstore.delete_collection()


# ============================================================
# 7. 防幻觉策略对比总结
# ============================================================

def print_strategy_comparison():
    """Print a comparison of anti-hallucination strategies"""

    print("""
╔════════════════════════════════════════════════════════════════════╗
║                    防幻觉策略对比                                  ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  策略              │ 优点              │ 缺点              │ 推荐  ║
║  ─────────────────┼──────────────────┼──────────────────┼──────  ║
║  Prompt 约束       │ 简单，零成本      │ LLM 不一定遵守    │ ★★★★  ║
║  相关性评分过滤     │ 快速，精确        │ 需要调阈值        │ ★★★★★ ║
║  两阶段检查        │ 判断准确          │ 多一次 LLM 调用   │ ★★★   ║
║  后置校验          │ 最严格            │ 多一次 LLM 调用   │ ★★★   ║
║  综合方案          │ 最可靠            │ 复杂度高          │ ★★★★★ ║
║                                                                    ║
║  生产环境建议：                                                     ║
║  1. 基础：Prompt 约束 + 相关性评分过滤（必须有）                      ║
║  2. 进阶：加上两阶段检查（重要场景）                                  ║
║  3. 严格：加上后置校验（金融/医疗/法律场景）                           ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")


# ============================================================
# 8. 主入口
# ============================================================

if __name__ == "__main__":
    # 策略对比总结
    print_strategy_comparison()

    # 方法一：Prompt 模板
    demo_prompt_approach()

    # 方法二：相关性评分过滤
    demo_score_filtering()

    # 方法三：两阶段检查
    demo_two_stage_check()

    # 方法四：后置校验
    demo_post_validation()

    # 完整 Pipeline
    create_safe_rag_pipeline()


# ============================================================
# 练习题
# ============================================================

# TODO 1: 调整 RELEVANCE_THRESHOLD 值（0.1, 0.3, 0.5, 0.7），观察：
#         - 阈值太低：可能放过不相关的文档
#         - 阈值太高：可能误杀相关的文档
#         找到适合你知识库的最佳阈值

# TODO 2: 改进 safe_answer 函数，在 confidence="low" 时：
#         - 在回答前加上"以下回答仅供参考，可信度较低："
#         - 或者直接拒绝回答

# TODO 3: 实现一个 "fallback" 机制：
#         当 RAG 检索不到时，用通用的 LLM 回答，但加上免责声明：
#         "以下回答不基于知识库，仅为 AI 的一般性知识，请自行验证。"

# TODO 4: 给 safe_answer 函数添加日志功能：
#         记录每次问答的 question、confidence、sources、timestamp
#         方便后续分析哪些问题经常无法回答（提示需要补充知识库）
