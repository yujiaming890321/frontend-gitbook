"""
Day 5: Conversational RAG — 添加对话历史，支持追问
AI 开发进阶：让 RAG 系统记住上下文，支持多轮对话

普通 RAG 的问题：
  - 用户问 "React Hooks 有哪些？" → 回答了
  - 用户追问 "它们的使用场景呢？" → RAG 不知道"它们"指什么
  - 因为每次检索都是独立的，没有上下文

Conversational RAG 的解决方案：
  1. 记录对话历史
  2. 用对话历史改写用户的追问（"它们"→ "React Hooks"）
  3. 用改写后的问题去检索

JS/TS 对比：
  - 类似 React 中的 useReducer：每次 dispatch 都带着历史 state
  - 或者 WebSocket 聊天：服务端维护会话上下文
"""

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


# ============================================================
# 1. 准备知识库文档
# ============================================================

# Technical documentation knowledge base for conversational RAG demo
docs = [
    Document(
        page_content="""
React Hooks 完全指南。

useState Hook：
- 用途：在函数组件中管理状态
- 语法：const [state, setState] = useState(initialValue)
- 特点：状态更新是异步的，触发组件重新渲染
- 使用场景：表单输入、开关状态、计数器

useEffect Hook：
- 用途：处理副作用（数据获取、DOM 操作、订阅）
- 语法：useEffect(() => { ... }, [dependencies])
- 清理函数：return () => { cleanup }
- 使用场景：API 调用、事件监听、定时器

useCallback Hook：
- 用途：缓存回调函数，避免不必要的子组件重渲染
- 语法：const cb = useCallback(() => { ... }, [deps])
- 使用场景：传给 React.memo 包裹的子组件的回调

useMemo Hook：
- 用途：缓存计算结果，避免重复计算
- 语法：const value = useMemo(() => compute(a, b), [a, b])
- 使用场景：昂贵的计算、复杂的数据转换
""",
        metadata={"source": "react-hooks-guide.md"},
    ),
    Document(
        page_content="""
React 性能优化策略。

1. 避免不必要的重渲染：
   - 使用 React.memo 包裹纯展示组件
   - 使用 useCallback 缓存传给子组件的回调
   - 使用 useMemo 缓存复杂计算结果

2. 代码分割 (Code Splitting)：
   - React.lazy + Suspense 实现路由级别的懒加载
   - 使用 dynamic import 按需加载组件
   - 减少首屏加载的 JavaScript 体积

3. 虚拟列表 (Virtual List)：
   - 使用 react-window 或 react-virtuoso
   - 只渲染可视区域内的元素
   - 适合长列表场景（1000+ 条数据）

4. 状态管理优化：
   - 状态下沉：把状态放在最近的需要它的组件中
   - 避免在顶层组件存放频繁更新的状态
   - 使用 zustand 的 selector 实现精细粒度的订阅

5. 图片优化：
   - 使用 next/image 自动优化
   - 懒加载：loading="lazy"
   - 使用 WebP/AVIF 格式
""",
        metadata={"source": "react-performance.md"},
    ),
    Document(
        page_content="""
TypeScript 与 React 的最佳实践。

组件类型定义：
```typescript
// 函数组件类型
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ label, onClick, variant = 'primary' }) => {
  return <button onClick={onClick}>{label}</button>;
};
```

常用类型：
- React.FC<Props>：函数组件类型
- React.ReactNode：可渲染的内容（JSX、字符串、数字等）
- React.ChangeEvent<HTMLInputElement>：表单事件
- React.MouseEvent<HTMLButtonElement>：鼠标事件

Hooks 的类型：
- useState<T>(initial: T)：自动推断类型
- useRef<T>(initial: T | null)：指定引用类型
- useReducer<R>(reducer: R, initial: S)：推断 state 和 action 类型

泛型组件：
```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
}

function List<T>({ items, renderItem }: ListProps<T>) {
  return <ul>{items.map(renderItem)}</ul>;
}
```
""",
        metadata={"source": "typescript-react.md"},
    ),
    Document(
        page_content="""
Next.js App Router 路由系统。

文件系统路由：
- app/page.tsx → /
- app/about/page.tsx → /about
- app/blog/[slug]/page.tsx → /blog/:slug
- app/[...slug]/page.tsx → 捕获所有路由

布局系统：
- layout.tsx：共享布局，嵌套组合
- template.tsx：每次导航都重新创建的布局
- loading.tsx：加载状态（自动包裹 Suspense）
- error.tsx：错误边界
- not-found.tsx：404 页面

数据获取：
- Server Components 中直接 async/await
- 不需要 getServerSideProps / getStaticProps
- 支持 fetch 自动去重和缓存
- revalidate 控制缓存刷新频率

路由组 (Route Groups)：
- (marketing)/page.tsx：用括号分组，不影响 URL
- 用于组织代码，不同组可以有不同的布局
""",
        metadata={"source": "nextjs-app-router.md"},
    ),
]


# ============================================================
# 2. 理解对话历史的问题
# 没有对话历史的 RAG 无法理解追问中的代词
# ============================================================

def demo_problem_without_history():
    """
    Demonstrate the problem: without conversation history,
    the RAG system cannot understand follow-up questions with pronouns.
    """

    print("=" * 60)
    print("问题演示：没有对话历史的 RAG 无法理解追问")
    print("=" * 60)

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="conv_problem"
    )

    # 模拟一段对话
    conversation = [
        "React 有哪些常用的 Hooks？",
        "它们的使用场景分别是什么？",    # "它们"指什么？RAG 不知道
        "性能优化相关的 Hook 有哪些？",  # 需要上文的 React Hooks 上下文
    ]

    print("\n普通 RAG（无对话历史）的检索结果：")
    for i, question in enumerate(conversation, 1):
        results = vectorstore.similarity_search(question, k=2)
        print(f"\n第 {i} 轮问题: {question}")
        print(f"  检索到的文档:")
        for doc in results:
            source = doc.metadata.get("source", "unknown")
            preview = doc.page_content[:50].replace("\n", " ").strip()
            print(f"    - ({source}) {preview}...")

    print("\n注意第 2 个问题 '它们的使用场景分别是什么？'")
    print("RAG 不知道'它们'指 React Hooks，可能检索到不相关的文档")

    vectorstore.delete_collection()


# ============================================================
# 3. 问题改写 (Question Rewriting)
# 用 LLM 把追问改写成独立的完整问题
# ============================================================

# Prompt template for rewriting follow-up questions into standalone questions
question_rewrite_prompt = PromptTemplate.from_template(
    """给定以下对话历史和用户的最新问题，把最新问题改写成一个独立的、完整的问题。

改写规则：
1. 把代词（它、它们、这个、那个等）替换成具体的名词
2. 补充上下文中隐含的信息
3. 保持问题的原始意图
4. 如果最新问题已经是独立的，直接返回原问题

对话历史：
{chat_history}

最新问题：{question}

改写后的独立问题："""
)


def format_chat_history(history: list[tuple[str, str]]) -> str:
    """Format chat history as a readable string for the prompt"""
    if not history:
        return "（无历史对话）"
    lines = []
    for user_msg, ai_msg in history:
        lines.append(f"用户: {user_msg}")
        lines.append(f"AI: {ai_msg}")
    return "\n".join(lines)


def rewrite_question(
    llm: Ollama,
    question: str,
    chat_history: list[tuple[str, str]],
) -> str:
    """
    Rewrite a follow-up question into a standalone question
    using conversation history for context.
    """
    if not chat_history:
        return question  # No history, no need to rewrite

    history_text = format_chat_history(chat_history)
    prompt = question_rewrite_prompt.format(
        chat_history=history_text,
        question=question,
    )
    rewritten = llm.invoke(prompt).strip()
    return rewritten


def demo_question_rewriting():
    """Demo: how question rewriting resolves pronoun references"""

    print("\n" + "=" * 60)
    print("问题改写演示")
    print("=" * 60)

    llm = Ollama(model="qwen2.5:7b", temperature=0.1)

    # Simulated conversation history
    test_cases = [
        {
            "history": [
                ("React 有哪些常用的 Hooks？", "常用的 Hooks 有 useState、useEffect、useMemo、useCallback 等。"),
            ],
            "question": "它们的使用场景分别是什么？",
        },
        {
            "history": [
                ("Next.js 的路由系统是什么样的？", "Next.js 使用文件系统路由，在 app 目录下创建文件夹和 page.tsx 即可。"),
                ("支持动态路由吗？", "支持，使用 [slug] 这样的方括号语法。"),
            ],
            "question": "那错误处理呢？",
        },
        {
            "history": [
                ("如何优化 React 性能？", "可以使用 React.memo、useCallback、useMemo 等方法。"),
            ],
            "question": "长列表场景怎么处理？",
        },
        {
            "history": [],
            "question": "TypeScript 有哪些常用的工具类型？",
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i} ---")
        if case["history"]:
            print(f"对话历史:")
            for user_msg, ai_msg in case["history"]:
                print(f"  用户: {user_msg}")
                print(f"  AI: {ai_msg}")
        else:
            print("对话历史: （无）")
        print(f"原始问题: {case['question']}")

        rewritten = rewrite_question(llm, case["question"], case["history"])
        print(f"改写后: {rewritten}")


# ============================================================
# 4. Conversational RAG 完整实现
# 核心流程：改写问题 → 检索 → 回答 → 更新历史
# ============================================================

class ConversationalRAG:
    """
    A RAG system that maintains conversation history
    and rewrites follow-up questions for better retrieval.

    Architecture:
    1. User asks a question
    2. If there's history, rewrite the question to be standalone
    3. Use the rewritten question for retrieval
    4. Generate answer from retrieved docs + original question
    5. Store the Q&A pair in history
    """

    def __init__(
        self,
        documents: list[Document],
        chunk_size: int = 400,
        chunk_overlap: int = 50,
        k: int = 3,
        max_history: int = 5,
    ):
        """Initialize the conversational RAG system with documents and parameters"""
        self.llm = Ollama(model="qwen2.5:7b", temperature=0.3)
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.k = k
        self.max_history = max_history
        # Store conversation history as list of (user_msg, ai_msg) tuples
        self.chat_history: list[tuple[str, str]] = []

        # Build vector store
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = splitter.split_documents(documents)
        self.vectorstore = Chroma.from_documents(
            chunks,
            self.embeddings,
            collection_name="conversational_rag",
        )
        print(f"Conversational RAG 初始化完成：{len(chunks)} 个文档块")

    def ask(self, question: str) -> dict:
        """
        Ask a question with conversation context.
        Returns answer, rewritten question, sources, and history length.
        """

        # Step 1: 改写问题（如果有对话历史）
        if self.chat_history:
            rewritten_question = rewrite_question(
                self.llm, question, self.chat_history
            )
        else:
            rewritten_question = question

        # Step 2: 用改写后的问题检索
        retrieved_docs = self.vectorstore.similarity_search(
            rewritten_question, k=self.k
        )
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        sources = [doc.metadata.get("source", "unknown") for doc in retrieved_docs]

        # Step 3: 构造包含对话历史的 prompt
        history_text = format_chat_history(self.chat_history)

        # Build the prompt with history context for coherent conversation
        prompt = f"""你是一个专业的前端技术助手。请根据参考文档和对话历史回答用户问题。

规则：
1. 优先使用参考文档中的信息
2. 如果参考文档中没有相关信息，说"我不知道"
3. 回答要考虑对话的上下文，保持连贯性
4. 回答简洁、准确

对话历史：
{history_text}

参考文档：
{context}

用户问题：{question}

回答："""

        answer = self.llm.invoke(prompt)

        # Step 4: 更新对话历史
        self.chat_history.append((question, answer))
        # Keep only the most recent conversations to avoid context overflow
        if len(self.chat_history) > self.max_history:
            self.chat_history = self.chat_history[-self.max_history:]

        return {
            "answer": answer,
            "original_question": question,
            "rewritten_question": rewritten_question,
            "sources": list(set(sources)),
            "history_length": len(self.chat_history),
        }

    def reset(self):
        """Clear conversation history to start a new conversation"""
        self.chat_history = []
        print("对话历史已清除")

    def cleanup(self):
        """Clean up the vector store"""
        self.vectorstore.delete_collection()


def demo_conversational_rag():
    """Demo: complete conversational RAG with multi-turn dialogue"""

    print("\n" + "=" * 60)
    print("Conversational RAG 完整演示")
    print("=" * 60)

    rag = ConversationalRAG(docs)

    # 模拟多轮对话
    conversation_flow = [
        "React 有哪些常用的 Hooks？",
        "它们的使用场景分别是什么？",                # 追问：代词"它们"
        "在性能优化中，哪些 Hook 最有用？",           # 追问：上下文关联
        "Next.js 的路由系统是什么样的？",             # 话题切换
        "它支持哪些类型的页面文件？",                  # 追问新话题
    ]

    for i, question in enumerate(conversation_flow, 1):
        print(f"\n{'━' * 50}")
        print(f"第 {i} 轮对话")
        print(f"{'━' * 50}")
        print(f"用户: {question}")

        result = rag.ask(question)

        if result["original_question"] != result["rewritten_question"]:
            print(f"改写后: {result['rewritten_question']}")

        print(f"AI: {result['answer'][:300]}...")
        print(f"来源: {', '.join(result['sources'])}")
        print(f"历史轮数: {result['history_length']}")

    # 清理
    rag.cleanup()


# ============================================================
# 5. 使用 LCEL 构建 Conversational RAG
# 更现代的实现方式
# ============================================================

def demo_lcel_conversational_rag():
    """
    Build conversational RAG using LCEL (LangChain Expression Language).
    More concise and composable than the class-based approach.
    """

    print("\n" + "=" * 60)
    print("LCEL 版本的 Conversational RAG")
    print("=" * 60)

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="conv_lcel"
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = Ollama(model="qwen2.5:7b", temperature=0.3)

    # Question condenser chain: rewrites follow-up into standalone question
    condenser_prompt = PromptTemplate.from_template(
        """给定对话历史和最新问题，把最新问题改写成独立的完整问题。
如果最新问题已经是独立的，直接返回原问题。只返回改写后的问题，不要其他内容。

对话历史：
{chat_history}

最新问题：{question}

独立问题："""
    )

    # Answer generation prompt
    answer_prompt = PromptTemplate.from_template(
        """根据参考文档回答问题。如果文档中没有相关信息，说"我不知道"。

参考文档：
{context}

问题：{question}

回答："""
    )

    # Build the LCEL pipeline
    condenser_chain = condenser_prompt | llm | StrOutputParser()

    def format_retrieved_docs(docs_list):
        """Format a list of retrieved documents into a single context string"""
        return "\n\n".join([d.page_content for d in docs_list])

    # 手动实现对话流程（LCEL 版本）
    chat_history: list[tuple[str, str]] = []

    questions = [
        "TypeScript 在 React 中怎么定义组件类型？",
        "泛型组件呢？怎么写？",
        "常用的事件类型有哪些？",
    ]

    for question in questions:
        print(f"\n用户: {question}")

        # Step 1: 改写问题
        history_text = format_chat_history(chat_history)
        if chat_history:
            standalone = condenser_chain.invoke({
                "chat_history": history_text,
                "question": question,
            })
            print(f"改写: {standalone}")
        else:
            standalone = question

        # Step 2: 检索
        retrieved = retriever.invoke(standalone)
        context = format_retrieved_docs(retrieved)

        # Step 3: 回答
        answer = (answer_prompt | llm | StrOutputParser()).invoke({
            "context": context,
            "question": question,
        })
        print(f"AI: {answer[:250]}...")

        # Step 4: 更新历史
        chat_history.append((question, answer[:200]))

    vectorstore.delete_collection()


# ============================================================
# 6. 对话历史管理策略
# 历史太长会超过 LLM 的 context window
# ============================================================

def demo_history_strategies():
    """
    Demonstrate different strategies for managing conversation history
    to prevent context window overflow.
    """

    print("\n" + "=" * 60)
    print("对话历史管理策略")
    print("=" * 60)

    # 模拟一段很长的对话历史
    long_history = [
        (f"问题 {i}", f"这是第 {i} 个问题的回答，包含一些详细的技术内容..." * 3)
        for i in range(1, 20)
    ]

    # Strategy 1: 固定窗口 — 只保留最近 N 轮
    def window_strategy(history: list, window_size: int = 5) -> list:
        """Keep only the most recent N conversation turns"""
        return history[-window_size:]

    # Strategy 2: Token 限制 — 根据字符/token 数限制
    def token_limit_strategy(history: list, max_chars: int = 2000) -> list:
        """Keep recent history within a character limit"""
        result = []
        total_chars = 0
        # Iterate from most recent to oldest conversation
        for user_msg, ai_msg in reversed(history):
            pair_chars = len(user_msg) + len(ai_msg)
            if total_chars + pair_chars > max_chars:
                break
            result.insert(0, (user_msg, ai_msg))
            total_chars += pair_chars
        return result

    # Strategy 3: 摘要策略 — 把旧对话压缩成摘要
    def summarize_strategy(
        history: list,
        llm: Ollama,
        keep_recent: int = 3,
    ) -> str:
        """Summarize old history and keep recent turns as-is"""
        if len(history) <= keep_recent:
            return format_chat_history(history)

        # Summarize old conversations
        old_history = history[:-keep_recent]
        old_text = format_chat_history(old_history)
        summary = llm.invoke(
            f"请用 2-3 句话概括以下对话的要点：\n{old_text}\n\n概括："
        )

        # Combine summary with recent history
        recent = history[-keep_recent:]
        recent_text = format_chat_history(recent)

        return f"[之前对话的概括] {summary}\n\n[最近对话]\n{recent_text}"

    # 对比各策略
    print(f"\n原始历史: {len(long_history)} 轮对话")

    windowed = window_strategy(long_history, 5)
    print(f"\n策略1 - 固定窗口 (保留5轮): {len(windowed)} 轮")

    token_limited = token_limit_strategy(long_history, 2000)
    print(f"策略2 - Token 限制 (2000字): {len(token_limited)} 轮")

    print(f"策略3 - 摘要策略: 压缩旧对话 + 保留最近3轮")
    print("  (需要 LLM 调用，这里只展示思路)")

    print("""
╔══════════════════════════════════════════════════════════════╗
║               对话历史管理策略对比                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  策略              │ 优点              │ 缺点                ║
║  ─────────────────┼──────────────────┼──────────────────    ║
║  固定窗口          │ 简单快速          │ 可能丢失重要上下文    ║
║  Token 限制        │ 精确控制长度      │ 可能在对话中间截断    ║
║  摘要策略          │ 保留所有信息      │ 额外 LLM 调用        ║
║  混合策略          │ 最佳效果          │ 实现复杂              ║
║                                                              ║
║  推荐：                                                      ║
║  - 简单场景：固定窗口（5-10 轮）                               ║
║  - 生产环境：Token 限制 + 摘要策略的混合                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


# ============================================================
# 7. 交互式对话界面（命令行版）
# ============================================================

def interactive_chat():
    """
    Run an interactive conversational RAG chatbot in the terminal.
    Type 'quit' to exit, 'reset' to clear history, 'history' to view history.
    """

    print("\n" + "=" * 60)
    print("交互式 Conversational RAG 聊天")
    print("=" * 60)
    print("命令: 'quit' 退出, 'reset' 清除历史, 'history' 查看历史")
    print("=" * 60)

    rag = ConversationalRAG(docs, max_history=10)

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
            rag.reset()
            continue
        elif question.lower() == "history":
            if not rag.chat_history:
                print("（暂无对话历史）")
            else:
                for i, (q, a) in enumerate(rag.chat_history, 1):
                    print(f"\n第 {i} 轮:")
                    print(f"  用户: {q}")
                    print(f"  AI: {a[:100]}...")
            continue

        result = rag.ask(question)

        if result["original_question"] != result["rewritten_question"]:
            print(f"[改写] {result['rewritten_question']}")

        print(f"\nAI: {result['answer']}")
        print(f"\n[来源: {', '.join(result['sources'])}]")

    rag.cleanup()
    print("\n再见！")


# ============================================================
# 8. 主入口
# ============================================================

if __name__ == "__main__":
    # 演示无对话历史的问题
    demo_problem_without_history()

    # 演示问题改写
    demo_question_rewriting()

    # 完整 Conversational RAG 演示
    demo_conversational_rag()

    # LCEL 版本演示
    demo_lcel_conversational_rag()

    # 对话历史管理策略
    demo_history_strategies()

    # 交互式聊天（取消注释以启用）
    # interactive_chat()


# ============================================================
# 练习题
# ============================================================

# TODO 1: 修改 ConversationalRAG 类，添加以下功能：
#         - save_history(filepath): 把对话历史保存到 JSON 文件
#         - load_history(filepath): 从 JSON 文件加载对话历史
#         这样用户可以在下次继续之前的对话

# TODO 2: 实现 summarize_strategy 中的摘要功能：
#         当对话超过 5 轮时，自动把前面的对话压缩成摘要
#         提示：用 LLM 调用来生成摘要

# TODO 3: 给 ConversationalRAG 添加"话题检测"功能：
#         当用户切换话题时（比如从 React 切到 Next.js），
#         自动清除之前的对话历史，避免旧历史干扰新话题
#         提示：可以用 LLM 判断新问题是否是追问还是新话题

# TODO 4: 取消 interactive_chat() 的注释，运行交互式聊天
#         测试以下场景：
#         a. 连续追问同一个话题
#         b. 中途切换话题
#         c. 用代词引用之前的内容
#         记录哪些场景效果好，哪些需要改进
