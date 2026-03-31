"""
Day 1: RetrievalQA Chain — 把检索 + LLM 串成问答链
AI 开发核心流程：用户问问题 → 检索相关文档 → 把文档+问题一起发给 LLM → 返回基于文档的回答

这是 RAG 的核心：让 LLM 基于你的私有数据回答问题，而不是凭"记忆"胡编。

JS/TS 对比：
  - JS 中你可能用 fetch 调 API + 手动拼 prompt
  - Python + LangChain 把整个流程抽象成了一条"链"(Chain)
"""

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


# ============================================================
# 1. 准备示例文档
# 在实际项目中，这些数据来自文件/数据库/API
# ============================================================

# Simulated knowledge base documents about a frontend team's tech stack
sample_documents = [
    Document(
        page_content="""
React Hooks 是 React 16.8 引入的特性，允许在函数组件中使用状态和其他 React 特性。
常用的 Hooks 包括：
- useState：管理组件状态
- useEffect：处理副作用（数据获取、订阅等）
- useContext：访问上下文
- useMemo：缓存计算结果
- useCallback：缓存回调函数
- useRef：持有可变值的引用

Hooks 的规则：
1. 只在顶层调用 Hooks，不要在循环或条件语句中调用
2. 只在 React 函数组件或自定义 Hooks 中调用
""",
        metadata={"source": "react-docs.md", "topic": "React Hooks"},
    ),
    Document(
        page_content="""
TypeScript 是 JavaScript 的超集，添加了静态类型系统。

核心概念：
- interface：定义对象的形状（结构类型）
- type：类型别名，可以表示联合类型、交叉类型等
- generic：泛型，让函数/类/接口支持多种类型
- enum：枚举类型

TypeScript 在 AI 应用中的作用：
1. 为 API 返回值定义类型，减少运行时错误
2. 提供代码补全和重构支持
3. 在 MCP Server 开发中是主流语言
""",
        metadata={"source": "typescript-docs.md", "topic": "TypeScript"},
    ),
    Document(
        page_content="""
RAG（Retrieval-Augmented Generation）是一种将检索和生成结合的技术。

RAG 的工作流程：
1. 索引阶段：将文档切分成块，转成向量，存入向量数据库
2. 检索阶段：用户问题转成向量，在向量数据库中搜索相似的文档块
3. 生成阶段：把检索到的文档块和用户问题一起发给 LLM，生成回答

RAG 的优势：
- 不需要微调模型，成本低
- 知识可以实时更新
- 回答可以引用来源，提高可信度
- 适合企业内部知识库场景
""",
        metadata={"source": "rag-guide.md", "topic": "RAG"},
    ),
    Document(
        page_content="""
Next.js 是基于 React 的全栈框架。

核心特性：
- App Router：基于文件系统的路由
- Server Components：服务端组件，减少客户端 JS 体积
- API Routes：内置 API 端点
- SSR/SSG/ISR：多种渲染策略

Next.js 在 AI 应用中的常见用法：
1. 作为 AI 聊天应用的前端框架
2. 通过 API Routes 代理 LLM 调用
3. 使用 Vercel AI SDK 实现流式输出
4. Server Components 中直接调用 AI API
""",
        metadata={"source": "nextjs-docs.md", "topic": "Next.js"},
    ),
    Document(
        page_content="""
向量数据库是 RAG 系统的核心组件。

常用向量数据库对比：
- Chroma：轻量级，适合本地开发和原型，Python 原生
- Pinecone：云端托管，生产环境首选，免运维
- Weaviate：开源，支持混合搜索（向量+关键词）
- Milvus：高性能，适合大规模数据
- pgvector：PostgreSQL 插件，适合已有 PG 的团队

选择建议：
- 学习和原型：Chroma（零配置，本地运行）
- 生产小规模：Pinecone 或 Supabase pgvector
- 生产大规模：Milvus 或 Weaviate
""",
        metadata={"source": "vector-db-guide.md", "topic": "Vector Database"},
    ),
]


# ============================================================
# 2. 文档切分 + 向量化 + 存储
# 复习 Week 5 的内容，这里快速搭建
# ============================================================

def build_vector_store(documents: list[Document]) -> Chroma:
    """Split documents into chunks, embed them, and store in Chroma vector DB"""

    # 切分文档
    # chunk_size=300：每块最多 300 字符
    # chunk_overlap=50：相邻块重叠 50 字符，避免信息在边界丢失
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "，", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    print(f"文档切分完成：{len(documents)} 篇文档 → {len(chunks)} 个块")

    # 向量化 + 存入 Chroma
    # OllamaEmbeddings：用本地 Ollama 运行的 nomic-embed-text 模型
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="week6_day1",
    )
    print(f"向量存储构建完成，共 {vectorstore._collection.count()} 条向量")

    return vectorstore


# ============================================================
# 3. RetrievalQA Chain — 核心概念
# JS 对比：这相当于把 fetch + prompt 拼接 + API 调用封装成一个函数
# ============================================================

def create_qa_chain(vectorstore: Chroma) -> RetrievalQA:
    """
    Create a RetrievalQA chain that connects the vector store retriever to an LLM.

    The chain does 3 things automatically:
    1. Takes user question → searches vectorstore for relevant docs
    2. Stuffs the retrieved docs into a prompt template
    3. Sends the prompt to LLM and returns the answer
    """

    # 初始化本地 LLM
    llm = Ollama(
        model="qwen2.5:7b",
        temperature=0.3,   # 低温度 = 更确定性的回答，适合知识问答
    )

    # 创建检索器
    # k=3：每次检索返回最相关的 3 个文档块
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )

    # 组装 RetrievalQA Chain
    # chain_type="stuff"：把所有检索到的文档"塞进"一个 prompt（适合文档量不大的情况）
    # 其他 chain_type：
    #   - "map_reduce"：每个文档单独处理，再合并（适合大量文档）
    #   - "refine"：逐个文档迭代优化答案
    #   - "map_rerank"：每个文档单独回答并打分，取最高分
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,  # 返回检索到的源文档
        verbose=True,                  # 打印中间过程，方便调试
    )

    return qa_chain


# ============================================================
# 4. chain_type 详解
# 不同的 chain_type 适用于不同场景
# ============================================================

def explain_chain_types():
    """Explain the different chain types available in RetrievalQA"""

    chain_types = {
        "stuff": {
            "description": "把所有检索到的文档塞进一个 prompt",
            "pros": "简单、快速、一次 LLM 调用",
            "cons": "文档太多会超过 context window 限制",
            "use_case": "文档量不大（< 4 个块），日常问答",
            # JS 对比：相当于把所有数据 concat 成一个字符串传给 API
        },
        "map_reduce": {
            "description": "每个文档单独处理（map），然后合并结果（reduce）",
            "pros": "可以处理大量文档，可并行",
            "cons": "多次 LLM 调用，速度慢、成本高",
            "use_case": "需要综合大量文档的信息",
            # JS 对比：相当于 Promise.all(docs.map(d => callLLM(d))).then(merge)
        },
        "refine": {
            "description": "用第一个文档生成初始答案，然后逐个文档迭代优化",
            "pros": "答案质量高，考虑了所有文档",
            "cons": "串行处理，最慢",
            "use_case": "需要精细、完整的答案",
            # JS 对比：相当于 docs.reduce(async (answer, doc) => refine(answer, doc))
        },
        "map_rerank": {
            "description": "每个文档单独回答并给出置信度分数，取最高分",
            "pros": "能选出最佳答案",
            "cons": "适合单一答案的问题，不适合需要综合信息的问题",
            "use_case": "事实性问题：'X 是什么？'",
        },
    }

    print("\n" + "=" * 60)
    print("RetrievalQA Chain Types 对比")
    print("=" * 60)

    for name, info in chain_types.items():
        print(f"\n📋 {name}")
        print(f"   说明: {info['description']}")
        print(f"   优点: {info['pros']}")
        print(f"   缺点: {info['cons']}")
        print(f"   适用: {info['use_case']}")


# ============================================================
# 5. 运行问答示例
# ============================================================

def run_qa_demo():
    """Run a complete RAG Q&A demo with sample questions"""

    print("=" * 60)
    print("RAG 问答演示：构建向量库 → 创建问答链 → 提问")
    print("=" * 60)

    # Step 1: 构建向量库
    print("\n[Step 1] 构建向量库...")
    vectorstore = build_vector_store(sample_documents)

    # Step 2: 创建问答链
    print("\n[Step 2] 创建 RetrievalQA 链...")
    qa_chain = create_qa_chain(vectorstore)

    # Step 3: 提问
    questions = [
        "什么是 RAG？它有什么优势？",
        "React Hooks 有哪些常用的 Hook？",
        "推荐用什么向量数据库做本地开发？",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'=' * 60}")
        print(f"问题 {i}: {question}")
        print("=" * 60)

        # invoke the chain and get response
        result = qa_chain.invoke({"query": question})

        print(f"\n回答: {result['result']}")

        # Display source documents used for this answer
        if "source_documents" in result:
            print(f"\n参考来源 ({len(result['source_documents'])} 个文档块):")
            for j, doc in enumerate(result["source_documents"], 1):
                source = doc.metadata.get("source", "unknown")
                preview = doc.page_content[:80].replace("\n", " ").strip()
                print(f"  [{j}] {source}: {preview}...")

    # 清理
    vectorstore.delete_collection()
    print("\n向量库已清理")


# ============================================================
# 6. 手动实现 RAG 流程（理解原理）
# ============================================================

def manual_rag_demo():
    """
    Manually implement RAG pipeline step by step, without using RetrievalQA chain.
    This helps you understand what the chain does under the hood.
    """

    print("\n" + "=" * 60)
    print("手动实现 RAG 流程（不用 RetrievalQA）")
    print("=" * 60)

    # Step 1: 构建向量库
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = text_splitter.split_documents(sample_documents)
    vectorstore = Chroma.from_documents(chunks, embeddings, collection_name="manual_rag")

    # Step 2: 检索相关文档
    question = "TypeScript 在 AI 应用中有什么作用？"
    print(f"\n问题: {question}")

    # Retrieve top-k relevant documents
    relevant_docs = vectorstore.similarity_search(question, k=3)

    print(f"\n检索到 {len(relevant_docs)} 个相关文档块:")
    context_parts = []
    for i, doc in enumerate(relevant_docs, 1):
        preview = doc.page_content[:100].replace("\n", " ").strip()
        print(f"  [{i}] {preview}...")
        context_parts.append(doc.page_content)

    # Step 3: 手动拼接 prompt
    # 这就是 RetrievalQA 内部做的事情
    context = "\n\n---\n\n".join(context_parts)

    # Build the prompt that combines context and question
    prompt = f"""基于以下参考文档回答用户的问题。如果文档中没有相关信息，请说"我不知道"。

参考文档：
{context}

用户问题：{question}

回答："""

    print(f"\n构造的 prompt（前 200 字）:\n{prompt[:200]}...")

    # Step 4: 调用 LLM
    llm = Ollama(model="qwen2.5:7b", temperature=0.3)
    answer = llm.invoke(prompt)

    print(f"\nLLM 回答:\n{answer}")

    # 清理
    vectorstore.delete_collection()


# ============================================================
# 7. 主入口
# ============================================================

if __name__ == "__main__":
    # 先展示 chain_type 对比（纯文本，不需要模型）
    explain_chain_types()

    # 运行完整 RAG 问答演示
    run_qa_demo()

    # 运行手动 RAG 实现（帮助理解原理）
    manual_rag_demo()


# ============================================================
# 练习题
# ============================================================

# TODO 1: 修改 create_qa_chain 函数，尝试使用 chain_type="map_reduce"
#         对比 "stuff" 和 "map_reduce" 的回答质量和速度差异
#         提示：可以用 time.time() 计时

# TODO 2: 修改检索器的 k 值（从 3 改为 1 和 5），观察回答质量变化
#         k 太小 → 信息不足；k 太大 → 噪音太多

# TODO 3: 添加你自己的文档到 sample_documents 列表中
#         比如你最熟悉的前端框架的知识点，然后针对这些知识提问
#         观察 RAG 是否能正确回答

# TODO 4: 在 manual_rag_demo 中，尝试修改 prompt 模板
#         让 LLM 用 markdown 格式、分点回答
#         提示：在 prompt 中加上"请用 markdown 格式分点回答"
