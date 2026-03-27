"""
Day 4: 异步编程 — async / await、asyncio
AI 开发中大量使用：并发调用多个 LLM API、流式响应处理
你已经熟悉 JS 的 async/await，Python 的概念几乎一样
"""

import asyncio
import time

# ============================================================
# 1. 基本 async/await
# JS: async function foo() { await bar() }
# Python: async def foo(): await bar()
# ============================================================

async def fetch_llm_response(prompt: str, delay: float = 1.0) -> str:
    """Simulate an async LLM API call"""
    print(f"  → 开始请求: {prompt[:20]}...")
    await asyncio.sleep(delay)  # 模拟网络延迟
    print(f"  ← 收到回复: {prompt[:20]}...")
    return f"Response to: {prompt}"

async def basic_example():
    # 和 JS 一模一样的用法
    result = await fetch_llm_response("什么是 RAG？", delay=0.5)
    print(f"结果: {result}")

asyncio.run(basic_example())


# ============================================================
# 2. 并发执行 — asyncio.gather
# JS: Promise.all([p1, p2, p3])  →  Python: asyncio.gather(c1, c2, c3)
# ============================================================

async def concurrent_example():
    """Call multiple LLMs concurrently — huge time savings"""
    prompts = [
        "解释 RAG",
        "解释 Agent",
        "解释 Prompt Engineering",
    ]

    print("\n--- 串行调用（慢）---")
    start = time.time()
    serial_results = []
    for prompt in prompts:
        result = await fetch_llm_response(prompt, delay=0.5)
        serial_results.append(result)
    print(f"串行耗时: {time.time() - start:.2f}s")

    print("\n--- 并发调用（快）---")
    start = time.time()
    # Create all coroutines and run them concurrently
    concurrent_results = await asyncio.gather(
        *[fetch_llm_response(p, delay=0.5) for p in prompts]
    )
    print(f"并发耗时: {time.time() - start:.2f}s")
    # 3 个请求各 0.5s，串行 1.5s，并发只要 0.5s

asyncio.run(concurrent_example())


# ============================================================
# 3. 异步生成器 — async for (流式响应)
# JS: for await (const chunk of stream) {}
# Python: async for chunk in stream:
# ============================================================

async def stream_response(prompt: str):
    """Simulate streaming LLM response (like ChatGPT typing effect)"""
    words = f"这是对「{prompt}」的回复，模拟流式输出效果。".split("")
    for char in words:
        await asyncio.sleep(0.05)  # Simulate streaming delay
        yield char  # yield 逐字返回

async def streaming_example():
    print("\n--- 流式输出 ---")
    # async for — iterate over an async generator
    full_response = ""
    async for char in stream_response("什么是 RAG"):
        print(char, end="", flush=True)
        full_response += char
    print(f"\n完整回复长度: {len(full_response)}")

asyncio.run(streaming_example())


# ============================================================
# 4. 错误处理和超时
# JS: Promise.race + timeout  →  Python: asyncio.wait_for + timeout
# ============================================================

async def slow_api_call():
    """Simulate a very slow API that might timeout"""
    await asyncio.sleep(10)
    return "终于完成了"

async def timeout_example():
    print("\n--- 超时处理 ---")
    try:
        # Set a 1 second timeout for the API call
        result = await asyncio.wait_for(slow_api_call(), timeout=1.0)
        print(f"结果: {result}")
    except asyncio.TimeoutError:
        print("API 调用超时！使用降级策略...")

asyncio.run(timeout_example())


# ============================================================
# 5. asyncio.Semaphore — 并发限制
# 避免同时发太多请求导致 API 限流 (rate limiting)
# JS: 通常用第三方库 p-limit
# ============================================================

async def rate_limited_example():
    """Control concurrency to avoid API rate limits"""
    # Allow max 2 concurrent requests
    semaphore = asyncio.Semaphore(2)

    async def limited_call(prompt: str) -> str:
        async with semaphore:
            return await fetch_llm_response(prompt, delay=0.5)

    print("\n--- 限流并发 (max 2 concurrent) ---")
    prompts = [f"问题 {i}" for i in range(5)]
    start = time.time()
    results = await asyncio.gather(*[limited_call(p) for p in prompts])
    elapsed = time.time() - start
    print(f"5 个请求, 限流 2 并发, 耗时: {elapsed:.2f}s")
    # Expected: ~1.5s (ceil(5/2) * 0.5s)

asyncio.run(rate_limited_example())


# ============================================================
# 6. 实际 AI 场景：并发处理多个文档
# ============================================================

async def process_document(doc_path: str) -> dict:
    """Simulate processing a document for RAG: load → chunk → embed"""
    await asyncio.sleep(0.3)  # Simulate embedding API call
    return {
        "path": doc_path,
        "chunks": 5,
        "status": "embedded"
    }

async def batch_process_example():
    """Process multiple documents concurrently for RAG ingestion"""
    print("\n--- 批量文档处理 ---")
    doc_paths = [
        "docs/1-RAG.md",
        "docs/2-Agent.md",
        "docs/3-Prompt.md",
        "docs/4-LLM.md",
        "docs/5-Eval.md",
    ]

    start = time.time()
    results = await asyncio.gather(*[process_document(p) for p in doc_paths])
    elapsed = time.time() - start

    total_chunks = sum(r["chunks"] for r in results)
    print(f"处理 {len(results)} 个文档, 共 {total_chunks} 个 chunks")
    print(f"并发处理耗时: {elapsed:.2f}s (串行预计 {len(doc_paths) * 0.3:.1f}s)")

asyncio.run(batch_process_example())


# ============================================================
# 7. JS vs Python 异步对比速查表
# ============================================================

"""
JS                              Python                          说明
─────────────                   ──────────                      ────
async function f() {}           async def f():                  声明异步函数
await promise                   await coroutine                 等待异步结果
Promise.all([p1, p2])           asyncio.gather(c1, c2)          并发执行
Promise.race([p1, p2])          asyncio.wait_for(c, timeout)    超时/竞速
for await (x of stream)         async for x in stream:          异步迭代
new Promise((resolve) => ...)   asyncio.Future()                底层 promise
setTimeout(fn, 1000)            asyncio.sleep(1)                延时
p-limit                         asyncio.Semaphore               并发限制
fetch()                         httpx.AsyncClient()             HTTP 请求
EventEmitter                    asyncio.Queue                   事件通信

关键区别：
- JS 是单线程事件循环，async 是唯一的并发方式
- Python 有多线程、多进程、async 三种并发方式
- AI 开发中主要用 async（I/O 密集型，等 API 响应）
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 写一个 async 函数 multi_model_query
# 同时向 3 个模型发送同一个问题（模拟），返回最快的结果
# 提示：用 asyncio.gather，每个模型延迟不同

# async def multi_model_query(prompt: str) -> str:
#     ???

# TODO 2: 写一个异步生成器 chunked_stream
# 接收一个长文本，每次 yield 一个 chunk（模拟流式处理）
# 每次 yield 之间有 0.1s 的延迟

# async def chunked_stream(text: str, chunk_size: int = 10):
#     ???

# TODO 3: 实现一个带重试的异步函数 resilient_call
# - 最多重试 3 次
# - 每次重试间隔翻倍（1s, 2s, 4s）— exponential backoff
# - 超时 5 秒

# async def resilient_call(func, *args, max_retries=3):
#     ???
