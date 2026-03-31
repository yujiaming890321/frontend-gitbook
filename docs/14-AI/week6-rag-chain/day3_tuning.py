"""
Day 3: 调优 chunk_size 和 k 值 — 观察效果变化
AI 开发中最实际的技能：参数调优决定了 RAG 系统的好坏

关键参数：
  - chunk_size：文档切分的块大小（字符数）
  - chunk_overlap：相邻块的重叠区域
  - k：检索时返回的文档块数量
  - temperature：LLM 回答的随机性

JS/TS 对比：
  - 类似前端性能调优：你调 debounce 的 delay、虚拟列表的 item_size
  - RAG 调优也是在"信息量"和"噪音量"之间找平衡
"""

import time
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


# ============================================================
# 1. 准备较长的测试文档
# 需要足够长的文档才能看出 chunk_size 的差异
# ============================================================

# Simulated long-form technical documentation for tuning experiments
long_documents = [
    Document(
        page_content="""
# React 状态管理完全指南

## 1. useState — 组件内部状态

useState 是最基本的状态管理 Hook。适用于简单的、局部的状态。

使用场景：
- 表单输入值
- UI 状态（开关、展开/折叠）
- 简单的计数器

注意事项：
- useState 是异步更新的，不能在设置后立即读取新值
- 对于对象和数组状态，必须创建新引用（不可变更新）
- 频繁更新的状态考虑使用 useReducer

## 2. useReducer — 复杂状态逻辑

当状态更新逻辑复杂时，useReducer 比 useState 更合适。

适用场景：
- 多个相关的状态需要同时更新
- 状态更新依赖于之前的状态
- 状态更新逻辑需要测试

与 Redux 的关系：
- useReducer 的 API 和 Redux 几乎一样（dispatch + reducer）
- 但 useReducer 是局部的，Redux 是全局的
- 小项目用 useReducer + Context，大项目考虑 Redux/Zustand

## 3. useContext — 跨组件共享状态

Context 用于在组件树中共享数据，避免 prop drilling。

适用场景：
- 主题（dark/light mode）
- 用户认证信息
- 语言/国际化设置

性能注意：
- Context 值变化会导致所有消费者重新渲染
- 拆分 Context 或使用 useMemo 优化
- 频繁更新的数据不适合放在 Context 中

## 4. Zustand — 轻量级状态管理库

Zustand 是一个小巧、快速、可扩展的状态管理库。

优势：
- API 简单，学习成本低
- 不需要 Provider 包裹
- 支持中间件（persist、devtools 等）
- TypeScript 支持好
- 包体积小（约 1KB）

与 Redux 对比：
- Zustand 更简洁，没有 action type、action creator 等样板代码
- Redux 生态更丰富，适合超大规模应用
- 推荐新项目使用 Zustand，除非团队已有 Redux 经验

## 5. 状态管理选择决策树

- 简单局部状态 → useState
- 复杂局部状态 → useReducer
- 跨组件共享（低频更新） → useContext
- 跨组件共享（高频更新） → Zustand / Jotai
- 服务端状态 → React Query / SWR
- 超大规模应用 → Redux Toolkit
""",
        metadata={"source": "react-state-guide.md", "topic": "React State Management"},
    ),
    Document(
        page_content="""
# CSS 布局方案演进

## 1. Flexbox 布局

Flexbox 是一维布局方案，适合处理行或列方向的布局。

核心属性：
- display: flex — 启用 flex 布局
- flex-direction — 主轴方向（row/column）
- justify-content — 主轴对齐
- align-items — 交叉轴对齐
- flex-wrap — 是否换行
- gap — 元素间距（现代浏览器都支持）

常见场景：
- 导航栏水平排列
- 卡片列表
- 居中（justify-content + align-items）
- 等高列布局

## 2. Grid 布局

Grid 是二维布局方案，适合处理行和列同时存在的复杂布局。

核心属性：
- display: grid
- grid-template-columns / rows — 定义列/行
- grid-gap — 网格间距
- grid-area — 命名区域
- repeat() / minmax() / auto-fill — 响应式技巧

与 Flexbox 的区别：
- Flexbox 是一维的，Grid 是二维的
- 简单对齐用 Flexbox，复杂布局用 Grid
- 实际开发中两者配合使用

## 3. Container Queries

Container Queries 是 CSS 新特性，允许组件根据容器大小（而不是视口大小）响应式布局。

优势：
- 组件级别的响应式，而非页面级别
- 更好的组件复用性
- 不依赖 JavaScript

浏览器支持：
- Chrome 105+、Safari 16+、Firefox 110+
- 可以用 @supports 做渐进增强

## 4. CSS-in-JS vs Tailwind

CSS-in-JS（styled-components, emotion）：
- 组件级别的样式隔离
- 动态样式方便
- 但有运行时性能开销
- React Server Components 不支持运行时 CSS-in-JS

Tailwind CSS：
- 实用工具类优先
- 零运行时开销
- 学习曲线陡峭，但上手后效率极高
- 配合 AI 代码生成效果极好（因为类名就是描述）

## 5. 现代 CSS 推荐方案

2024-2025 推荐：
- 布局：Grid + Flexbox 配合
- 样式方案：Tailwind CSS（或 CSS Modules）
- 响应式：Container Queries + Media Queries
- 动画：CSS Animations + Framer Motion
""",
        metadata={"source": "css-layout-guide.md", "topic": "CSS Layout"},
    ),
    Document(
        page_content="""
# TypeScript 高级类型技巧

## 1. 条件类型 (Conditional Types)

条件类型根据条件选择不同的类型，类似三元表达式。

```typescript
type IsString<T> = T extends string ? true : false;
type Result = IsString<"hello">; // true
type Result2 = IsString<42>;     // false
```

实际应用：
- 根据输入类型自动推断返回类型
- API 响应类型的动态推导
- 库的类型定义

## 2. 映射类型 (Mapped Types)

映射类型遍历已有类型的属性，生成新类型。

```typescript
// 把所有属性变为可选
type Partial<T> = { [K in keyof T]?: T[K] };

// 把所有属性变为只读
type Readonly<T> = { readonly [K in keyof T]: T[K] };
```

常用内置映射类型：
- Partial<T> — 所有属性可选
- Required<T> — 所有属性必选
- Pick<T, K> — 选取部分属性
- Omit<T, K> — 排除部分属性
- Record<K, V> — 构建键值对类型

## 3. 模板字面量类型 (Template Literal Types)

TypeScript 4.1 引入，可以在类型层面操作字符串。

```typescript
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
type ApiRoute = `/api/${string}`;
type Endpoint = `${HttpMethod} ${ApiRoute}`;
// "GET /api/users" | "POST /api/users" | ...
```

## 4. 类型体操实战

- infer 关键字：在条件类型中提取类型
- 递归类型：处理深层嵌套结构
- 类型守卫：运行时类型收窄

这些高级技巧在写 AI SDK 的类型定义时非常有用，
比如根据模型名称自动推断返回类型。

## 5. 实用建议

- 不要过度使用高级类型，可读性第一
- 优先使用内置工具类型
- 复杂类型加注释说明意图
- 用 type-challenges 练习类型体操
""",
        metadata={"source": "typescript-advanced.md", "topic": "TypeScript Advanced"},
    ),
]


# ============================================================
# 2. chunk_size 参数实验
# 核心问题：块太小 → 信息碎片化；块太大 → 噪音太多
# ============================================================

def experiment_chunk_size():
    """
    Experiment with different chunk_size values and observe
    how they affect the number of chunks and retrieval quality.
    """

    print("=" * 60)
    print("实验 1: chunk_size 对文档切分的影响")
    print("=" * 60)

    chunk_sizes = [100, 200, 500, 1000]
    overlap = 50

    for size in chunk_sizes:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", "。", "，", " ", ""],
        )
        chunks = splitter.split_documents(long_documents)

        # Calculate statistics about the chunks
        lengths = [len(c.page_content) for c in chunks]
        avg_len = sum(lengths) / len(lengths) if lengths else 0

        print(f"\nchunk_size={size}, overlap={overlap}")
        print(f"  切分块数: {len(chunks)}")
        print(f"  平均块长度: {avg_len:.0f} 字符")
        print(f"  最短块: {min(lengths)} 字符")
        print(f"  最长块: {max(lengths)} 字符")
        print(f"  第一块预览: {chunks[0].page_content[:60].strip()}...")


# ============================================================
# 3. chunk_overlap 参数实验
# overlap 保证信息不在边界处丢失
# ============================================================

def experiment_chunk_overlap():
    """
    Experiment with different chunk_overlap values.
    Overlap ensures information at chunk boundaries is preserved.
    """

    print("\n" + "=" * 60)
    print("实验 2: chunk_overlap 对切分的影响")
    print("=" * 60)

    chunk_size = 300
    overlaps = [0, 30, 50, 100, 150]

    for overlap in overlaps:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )
        chunks = splitter.split_documents(long_documents)

        # Calculate overlap ratio
        overlap_ratio = overlap / chunk_size * 100

        print(f"\nchunk_size={chunk_size}, overlap={overlap} ({overlap_ratio:.0f}%)")
        print(f"  切分块数: {len(chunks)}")

        # Show boundary between first two chunks to visualize overlap
        if len(chunks) >= 2:
            end_of_first = chunks[0].page_content[-30:].strip()
            start_of_second = chunks[1].page_content[:30].strip()
            print(f"  第1块结尾: ...{end_of_first}")
            print(f"  第2块开头: {start_of_second}...")


# ============================================================
# 4. k 值实验 — 检索数量的影响
# k 太小 → 漏掉关键信息；k 太大 → 引入噪音、拖慢速度
# ============================================================

def experiment_k_value():
    """
    Experiment with different k values in retrieval.
    k controls how many document chunks are retrieved for each query.
    """

    print("\n" + "=" * 60)
    print("实验 3: k 值对检索结果的影响")
    print("=" * 60)

    # 用固定的 chunk_size 构建向量库
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(long_documents)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="k_experiment"
    )

    question = "React 中如何选择状态管理方案？"
    k_values = [1, 3, 5, 10]

    for k in k_values:
        print(f"\n--- k={k} ---")
        # Retrieve k documents and measure time
        start = time.time()
        results = vectorstore.similarity_search(question, k=k)
        elapsed = time.time() - start

        print(f"  检索耗时: {elapsed:.3f}s")
        print(f"  返回 {len(results)} 个文档块:")

        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "unknown")
            preview = doc.page_content[:60].replace("\n", " ").strip()
            print(f"    [{i}] ({source}) {preview}...")

    vectorstore.delete_collection()


# ============================================================
# 5. 综合实验：chunk_size + k 组合
# 找到最佳参数组合
# ============================================================

def experiment_combined():
    """
    Combined experiment: test different chunk_size and k combinations
    on the same question and compare answer quality.
    """

    print("\n" + "=" * 60)
    print("实验 4: chunk_size + k 组合对比")
    print("=" * 60)

    question = "Zustand 和 Redux 有什么区别？该怎么选？"
    llm = Ollama(model="qwen2.5:7b", temperature=0.3)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    prompt_template = PromptTemplate.from_template(
        """根据以下参考文档回答问题。如果文档中没有相关信息，请说"我不知道"。

参考文档：
{context}

问题：{question}

回答："""
    )

    # Test different parameter combinations
    configs = [
        {"chunk_size": 100, "k": 3, "label": "小块+少检索"},
        {"chunk_size": 100, "k": 8, "label": "小块+多检索"},
        {"chunk_size": 500, "k": 2, "label": "大块+少检索"},
        {"chunk_size": 500, "k": 5, "label": "大块+多检索"},
        {"chunk_size": 300, "k": 3, "label": "中等（推荐）"},
    ]

    for config in configs:
        print(f"\n{'=' * 50}")
        print(f"配置: {config['label']} (chunk_size={config['chunk_size']}, k={config['k']})")
        print("=" * 50)

        # Build vector store with this chunk_size
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_size"] // 5,
        )
        chunks = splitter.split_documents(long_documents)
        collection_name = f"combined_{config['chunk_size']}_{config['k']}"
        vectorstore = Chroma.from_documents(
            chunks, embeddings, collection_name=collection_name
        )

        # Create QA chain with this k value
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": config["k"]}
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt_template},
        )

        # Measure time and run query
        start = time.time()
        result = qa_chain.invoke({"query": question})
        elapsed = time.time() - start

        print(f"\n切分块数: {len(chunks)}")
        print(f"检索到: {len(result['source_documents'])} 块")
        print(f"耗时: {elapsed:.2f}s")
        print(f"\n回答:\n{result['result']}")

        vectorstore.delete_collection()


# ============================================================
# 6. temperature 参数实验
# temperature 影响 LLM 回答的随机性
# ============================================================

def experiment_temperature():
    """
    Experiment with different temperature values.
    Lower temperature = more deterministic, higher = more creative.
    """

    print("\n" + "=" * 60)
    print("实验 5: temperature 对回答风格的影响")
    print("=" * 60)

    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = splitter.split_documents(long_documents)
    vectorstore = Chroma.from_documents(
        chunks, embeddings, collection_name="temp_experiment"
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    question = "CSS-in-JS 和 Tailwind 该怎么选？"
    temperatures = [0.0, 0.3, 0.7, 1.0]

    prompt_template = PromptTemplate.from_template(
        """根据参考文档回答问题。

参考文档：
{context}

问题：{question}

回答："""
    )

    for temp in temperatures:
        print(f"\n--- temperature={temp} ---")

        llm = Ollama(model="qwen2.5:7b", temperature=temp)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt_template},
        )

        result = qa_chain.invoke({"query": question})
        # Show first 200 chars to compare style differences
        answer = result["result"][:200]
        print(f"  回答（前200字）: {answer}...")

    vectorstore.delete_collection()


# ============================================================
# 7. 参数调优指南
# ============================================================

def print_tuning_guide():
    """Print a reference guide for RAG parameter tuning"""

    print("""
╔══════════════════════════════════════════════════════════════╗
║                 RAG 参数调优指南                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  chunk_size（块大小）                                         ║
║  ┌─────────┬─────────────────────────────────────┐           ║
║  │ 100-200 │ 精细检索，适合 FAQ / 短答案           │           ║
║  │ 300-500 │ 平衡选择，大多数场景推荐              │           ║
║  │ 500-1000│ 保留上下文，适合长篇分析              │           ║
║  └─────────┴─────────────────────────────────────┘           ║
║                                                              ║
║  chunk_overlap（重叠量）                                      ║
║  建议: chunk_size 的 10%-20%                                  ║
║  过小 → 信息在边界丢失；过大 → 冗余太多                         ║
║                                                              ║
║  k（检索数量）                                                ║
║  ┌─────┬──────────────────────────────────────┐              ║
║  │ 1-2 │ 精确匹配，适合事实性问题                │              ║
║  │ 3-5 │ 平衡选择，大多数场景推荐                │              ║
║  │ 5-10│ 综合分析，适合需要多方信息的问题        │              ║
║  └─────┴──────────────────────────────────────┘              ║
║                                                              ║
║  temperature（温度）                                          ║
║  ┌─────────┬───────────────────────────────────┐             ║
║  │ 0.0-0.3 │ 确定性回答，适合事实问答             │             ║
║  │ 0.3-0.7 │ 平衡选择                            │             ║
║  │ 0.7-1.0 │ 创造性回答，适合头脑风暴             │             ║
║  └─────────┴───────────────────────────────────┘             ║
║                                                              ║
║  调优流程：                                                   ║
║  1. 先用默认值（chunk=300, k=3, temp=0.3）                    ║
║  2. 收集一批测试问题和期望答案                                 ║
║  3. 每次只改一个参数，对比效果                                 ║
║  4. 记录每组参数的表现，找到最优组合                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


# ============================================================
# 8. 主入口
# ============================================================

if __name__ == "__main__":
    # 参数调优指南
    print_tuning_guide()

    # 运行各项实验
    experiment_chunk_size()
    experiment_chunk_overlap()
    experiment_k_value()
    experiment_combined()
    experiment_temperature()


# ============================================================
# 练习题
# ============================================================

# TODO 1: 添加一个 experiment_separators 函数
#         测试不同的 separators 参数对切分效果的影响
#         例如：["\n\n", "\n", "。"]  vs  ["\n\n", "\n", " "]
#         观察中文文档和英文文档的差异

# TODO 2: 在 experiment_combined 中添加一个评估指标
#         为每个配置的回答打分（1-5分），记录到一个 dict 中
#         提示：可以手动评分，也可以用 LLM 自动评分

# TODO 3: 添加一个 experiment_search_type 函数
#         对比 similarity 和 mmr (Maximal Marginal Relevance) 两种检索策略
#         retriever = vectorstore.as_retriever(search_type="mmr")
#         MMR 会在相关性和多样性之间取平衡

# TODO 4: 用你自己的文档（比如项目的 README 或技术文档）替换 long_documents
#         找到适合你文档的最佳参数组合
