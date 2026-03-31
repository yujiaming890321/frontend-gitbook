"""
Day 2: 优化 Prompt 模板 — 让 RAG 回答引用来源文档
AI 开发关键技能：好的 prompt 模板决定了 RAG 系统的回答质量

JS/TS 对比：
  - JS 中你用 template literal: `Based on ${context}, answer ${question}`
  - LangChain 的 PromptTemplate 提供了更强大的模板引擎，支持变量验证和组合
"""

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


# ============================================================
# 1. LangChain PromptTemplate 基础
# JS 对比：类似 Handlebars/EJS 模板引擎，但专门为 LLM 设计
# ============================================================

# 最基本的 PromptTemplate
# input_variables 声明了模板中的变量名，LangChain 会在运行时校验
basic_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""请根据以下内容回答问题。

内容：{context}

问题：{question}

回答：""",
)

# 使用 format 方法填充变量（类似 JS 的 template literal）
filled = basic_template.format(
    context="React 是一个构建用户界面的 JavaScript 库。",
    question="React 是什么？",
)
print("基本模板填充结果:")
print(filled)
print()


# ============================================================
# 2. 从字符串快速创建模板
# 更简洁的写法，适合快速原型
# ============================================================

# from_template 自动从字符串中提取 {variable_name}
quick_template = PromptTemplate.from_template(
    "用一句话解释 {concept}，面向 {audience}。"
)
print("快速模板:")
print(quick_template.format(concept="RAG", audience="前端程序员"))
print()


# ============================================================
# 3. RAG 专用 Prompt 模板 — 这是今天的重点
# 不同的模板设计会显著影响回答质量
# ============================================================

# Template v1: 基础版 — 只给上下文和问题
rag_template_v1 = PromptTemplate(
    input_variables=["context", "question"],
    template="""根据以下参考文档回答问题。

参考文档：
{context}

问题：{question}

回答：""",
)

# Template v2: 加上角色设定和约束 — 更好的回答质量
rag_template_v2 = PromptTemplate(
    input_variables=["context", "question"],
    template="""你是一个专业的技术文档助手。请严格根据提供的参考文档回答用户问题。

规则：
1. 只使用参考文档中的信息来回答
2. 如果参考文档中没有相关信息，请明确说"根据已有文档，我无法回答这个问题"
3. 回答要简洁、准确

参考文档：
{context}

用户问题：{question}

回答：""",
)

# Template v3: 引用来源 — 让回答标注出处（企业级 RAG 的必备功能）
rag_template_v3 = PromptTemplate(
    input_variables=["context", "question"],
    template="""你是一个专业的技术文档助手。请严格根据提供的参考文档回答用户问题。

规则：
1. 只使用参考文档中的信息来回答
2. 在回答中引用来源，格式为 [来源: 文件名]
3. 如果参考文档中没有相关信息，请明确说"根据已有文档，我无法回答这个问题"
4. 回答要简洁、准确、分点列出

参考文档：
{context}

用户问题：{question}

请先回答问题，然后在最后列出参考来源：""",
)

# Template v4: 中英双语 + Markdown 格式 — 适合技术团队
rag_template_v4 = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a technical documentation assistant. Answer the user's question based ONLY on the provided reference documents.

Rules:
1. Only use information from the reference documents
2. Cite sources in the format [Source: filename]
3. If the documents don't contain relevant information, say "Based on available documents, I cannot answer this question"
4. Use markdown formatting with bullet points
5. Keep the answer concise but complete
6. Answer in the same language as the question

Reference Documents:
{context}

User Question: {question}

Answer:""",
)


# ============================================================
# 4. 准备测试数据
# ============================================================

# Simulated knowledge base documents for testing prompt templates
test_documents = [
    Document(
        page_content="""
React Server Components (RSC) 是 React 18 引入的新特性。

核心概念：
- Server Components 在服务端渲染，不会发送到客户端
- 可以直接访问数据库、文件系统等服务端资源
- 不能使用 useState、useEffect 等客户端 Hooks
- 可以导入 Client Components，但反过来不行

性能优势：
- 减少客户端 JavaScript 体积
- 数据获取在服务端完成，减少瀑布请求
- 自动代码分割
""",
        metadata={"source": "react-server-components.md"},
    ),
    Document(
        page_content="""
Prompt Engineering 最佳实践：

1. 明确角色：告诉 LLM 它是什么角色（"你是一个资深前端工程师"）
2. 提供上下文：给出足够的背景信息
3. 指定输出格式：要 JSON？Markdown？分点列出？
4. 给出示例（Few-shot）：提供输入-输出的例子
5. 设置约束：不要做什么，格式限制等
6. 分步思考（Chain of Thought）：让模型一步步推理

避免的问题：
- prompt 太长导致 LLM 忽略中间内容（"Lost in the Middle" 问题）
- 指令冲突
- 过于模糊的描述
""",
        metadata={"source": "prompt-engineering.md"},
    ),
    Document(
        page_content="""
LangChain Expression Language (LCEL) 是 LangChain 的声明式组合语法。

基本语法：
- 使用 | 管道符连接组件：prompt | llm | parser
- 支持并行执行：RunnableParallel
- 支持条件分支：RunnableBranch
- 自动处理输入/输出类型转换

优势：
- 代码更简洁
- 内置流式输出支持
- 自动异步支持
- 便于调试和追踪

对比旧版：
旧版用 LLMChain、SequentialChain 等类
新版用 LCEL 管道语法，更灵活
""",
        metadata={"source": "lcel-guide.md"},
    ),
]


# ============================================================
# 5. 对比不同模板的效果
# ============================================================

def build_test_vectorstore(documents: list[Document]) -> Chroma:
    """Build a vector store from test documents for template comparison"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
    )
    chunks = text_splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="week6_day2",
    )
    return vectorstore


def compare_templates():
    """
    Compare different prompt templates on the same question
    to demonstrate how template design affects answer quality.
    """

    print("=" * 60)
    print("Prompt 模板对比实验")
    print("=" * 60)

    # 构建向量库
    vectorstore = build_test_vectorstore(test_documents)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = Ollama(model="qwen2.5:7b", temperature=0.3)

    templates = {
        "v1 (基础版)": rag_template_v1,
        "v2 (角色+约束)": rag_template_v2,
        "v3 (引用来源)": rag_template_v3,
        "v4 (英文+Markdown)": rag_template_v4,
    }

    question = "React Server Components 有什么优势？在什么场景下使用？"

    for name, template in templates.items():
        print(f"\n{'=' * 60}")
        print(f"模板: {name}")
        print("=" * 60)

        # Create chain with custom prompt template
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": template},
        )

        result = qa_chain.invoke({"query": question})
        print(f"\n回答:\n{result['result']}")
        print(f"\n使用了 {len(result['source_documents'])} 个文档块")

    # 清理
    vectorstore.delete_collection()


# ============================================================
# 6. 构造带源文档信息的 context
# 让 LLM 知道每段内容来自哪个文件
# ============================================================

def format_docs_with_sources(docs: list[Document]) -> str:
    """
    Format retrieved documents with source information.
    This gives the LLM the ability to cite specific sources in its answer.
    """
    formatted_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        content = doc.page_content.strip()
        # Wrap each document with source metadata for citation
        formatted_parts.append(
            f"[文档 {i}] (来源: {source})\n{content}"
        )
    return "\n\n---\n\n".join(formatted_parts)


def demo_with_sources():
    """Demo showing how to format context with source information"""

    print("\n" + "=" * 60)
    print("带来源引用的 RAG 演示")
    print("=" * 60)

    vectorstore = build_test_vectorstore(test_documents)
    llm = Ollama(model="qwen2.5:7b", temperature=0.3)

    question = "Prompt Engineering 有哪些最佳实践？"

    # Step 1: 检索相关文档
    docs = vectorstore.similarity_search(question, k=3)

    # Step 2: 格式化文档（带来源信息）
    context = format_docs_with_sources(docs)
    print(f"\n格式化后的 context:\n{context[:300]}...")

    # Step 3: 用带来源的模板生成回答
    prompt = rag_template_v3.format(context=context, question=question)
    answer = llm.invoke(prompt)
    print(f"\n回答（带来源引用）:\n{answer}")

    # 清理
    vectorstore.delete_collection()


# ============================================================
# 7. 使用 LCEL 管道语法（新版 LangChain 推荐）
# JS 对比：类似 RxJS 的 pipe() 或 Unix 管道 cmd1 | cmd2 | cmd3
# ============================================================

def demo_lcel_pipeline():
    """
    Demonstrate the modern LCEL (LangChain Expression Language) approach
    for building RAG chains with custom prompts.
    """
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

    print("\n" + "=" * 60)
    print("LCEL 管道语法演示")
    print("=" * 60)

    vectorstore = build_test_vectorstore(test_documents)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = Ollama(model="qwen2.5:7b", temperature=0.3)

    # LCEL prompt template
    prompt = PromptTemplate.from_template(
        """根据以下参考文档回答问题。请在回答中引用来源。

参考文档：
{context}

问题：{question}

回答："""
    )

    # Build the LCEL chain using pipe syntax
    # 这条链的数据流：
    # 1. {"context": retriever, "question": passthrough} → 并行执行检索和传递问题
    # 2. prompt → 把检索结果和问题填入模板
    # 3. llm → 调用 LLM 生成回答
    # 4. StrOutputParser → 提取纯文本输出
    rag_chain = (
        {
            "context": retriever | format_docs_with_sources,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # 使用方式非常简单——直接传入问题字符串
    question = "LCEL 有什么优势？和旧版有什么区别？"
    print(f"\n问题: {question}")

    answer = rag_chain.invoke(question)
    print(f"\n回答:\n{answer}")

    # 清理
    vectorstore.delete_collection()


# ============================================================
# 8. Prompt 模板设计指南
# ============================================================

def print_prompt_design_guide():
    """Print a reference guide for designing RAG prompt templates"""

    guide = """
╔══════════════════════════════════════════════════════════════╗
║               RAG Prompt 模板设计指南                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. 角色设定 (System Role)                                    ║
║     ✅ "你是一个专业的技术文档助手"                              ║
║     ❌ "你是一个全能 AI"（太模糊）                              ║
║                                                              ║
║  2. 约束条件 (Constraints)                                    ║
║     ✅ "只使用参考文档中的信息"                                  ║
║     ✅ "如果不知道，说'我不知道'"                                ║
║     ❌ 没有约束（LLM 会自由发挥，可能编造）                       ║
║                                                              ║
║  3. 输出格式 (Output Format)                                  ║
║     ✅ "用 markdown 分点列出"                                  ║
║     ✅ "在回答中引用来源 [来源: xxx]"                            ║
║     ❌ 没有格式要求（输出不可控）                                ║
║                                                              ║
║  4. 变量顺序 (Variable Order)                                 ║
║     ✅ context 在前，question 在后                             ║
║     （LLM 对开头和结尾的内容更敏感）                              ║
║                                                              ║
║  5. 常见陷阱                                                  ║
║     ⚠️ prompt 过长 → "Lost in the Middle" 问题                ║
║     ⚠️ 指令冲突 → LLM 不知道该听哪个                           ║
║     ⚠️ context 没有来源标识 → LLM 无法引用                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(guide)


# ============================================================
# 9. 主入口
# ============================================================

if __name__ == "__main__":
    # 展示 Prompt 设计指南
    print_prompt_design_guide()

    # 对比不同模板效果
    compare_templates()

    # 演示带来源引用的 RAG
    demo_with_sources()

    # 演示 LCEL 管道语法
    demo_lcel_pipeline()


# ============================================================
# 练习题
# ============================================================

# TODO 1: 创建一个 rag_template_v5，要求 LLM 用以下格式回答：
#         ## 回答
#         （正文）
#         ## 参考来源
#         - [来源1]: 文件名
#         - [来源2]: 文件名
#         ## 置信度
#         高/中/低（根据文档覆盖程度自评）

# TODO 2: 创建一个面向非技术用户的模板，要求：
#         - 不使用技术术语
#         - 用比喻解释概念
#         - 回答控制在 3 句话以内

# TODO 3: 修改 format_docs_with_sources 函数，增加以下信息：
#         - 文档的 topic 字段
#         - 文档内容的字数
#         - 文档在检索结果中的排名

# TODO 4: 用 LCEL 语法构建一个"多语言 RAG"链：
#         - 检测用户问题的语言
#         - 用对应语言回答
#         提示：在 prompt 中加上 "Answer in the same language as the question"
