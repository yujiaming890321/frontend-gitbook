"""
Day 4: 流式响应 (Streaming) — 实现打字机效果
AI 应用的核心体验：让用户看到 AI 正在"思考和打字"
JS: for await (const chunk of stream) {}
Python: for chunk in stream:
"""

from openai import OpenAI
import asyncio
import json
import time

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# ============================================================
# 1. 基本流式调用
# ============================================================

def stream_basic(prompt: str):
    """Basic streaming — print each chunk as it arrives"""
    print("--- 流式输出 ---")
    try:
        stream = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
            stream=True,  # Enable streaming
        )

        full_response = ""
        for chunk in stream:
            # Each chunk contains a delta (partial content)
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                full_response += delta.content

        print(f"\n\n完整回复长度: {len(full_response)} 字符")
    except Exception as e:
        print(f"[错误: {e}]")

stream_basic("用 3 句话解释 Python 的优点")


# ============================================================
# 2. 理解 Stream Chunk 结构
# ============================================================

def stream_debug(prompt: str):
    """Show the raw structure of each stream chunk"""
    print("\n--- Chunk 结构分析 ---")
    try:
        stream = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=30,  # Short output for debugging
        )

        for i, chunk in enumerate(stream):
            choice = chunk.choices[0]
            print(f"Chunk {i:3d}: "
                  f"role={choice.delta.role or '-':>9s}  "
                  f"content={repr(choice.delta.content or ''):>10s}  "
                  f"finish={choice.finish_reason or '-'}")

            if i > 15:
                print("  ... (truncated for readability)")
                break
    except Exception as e:
        print(f"[错误: {e}]")

stream_debug("你好")


# ============================================================
# 3. 收集流式响应 + 计时
# ============================================================

def stream_with_metrics(prompt: str) -> dict:
    """Stream response and collect timing metrics"""
    try:
        start = time.time()
        first_token_time = None

        stream = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        full_response = ""
        token_count = 0

        print("\n--- 流式输出 + 指标 ---")
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                if first_token_time is None:
                    first_token_time = time.time()
                print(content, end="", flush=True)
                full_response += content
                token_count += 1

        elapsed = time.time() - start
        ttft = first_token_time - start if first_token_time else 0

        metrics = {
            "total_time": round(elapsed, 2),
            "time_to_first_token": round(ttft, 2),  # TTFT — key UX metric
            "tokens": token_count,
            "tokens_per_second": round(token_count / elapsed, 1) if elapsed > 0 else 0,
        }
        print(f"\n\n指标: {json.dumps(metrics, ensure_ascii=False)}")
        return metrics
    except Exception as e:
        print(f"[错误: {e}]")
        return {}

stream_with_metrics("列出 5 个 Python 数据类型")


# ============================================================
# 4. 流式回调模式 — 实际项目中的用法
# ============================================================

def stream_with_callback(
    prompt: str,
    on_token: callable = None,
    on_complete: callable = None,
) -> str:
    """
    Stream with callback functions.
    This pattern is common in production: decouple streaming from display.
    """
    try:
        stream = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        full_response = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                if on_token:
                    on_token(content)

        if on_complete:
            on_complete(full_response)

        return full_response
    except Exception as e:
        return f"[错误: {e}]"

# Usage with callbacks
print("\n--- 回调模式 ---")
stream_with_callback(
    "一句话说什么是 FastAPI",
    on_token=lambda t: print(t, end="", flush=True),
    on_complete=lambda full: print(f"\n[完成, 共 {len(full)} 字符]"),
)


# ============================================================
# 5. 异步流式 — 用于 FastAPI / Web 应用
# ============================================================

async def async_stream(prompt: str) -> str:
    """Async streaming — used in FastAPI SSE endpoints"""
    from openai import AsyncOpenAI

    async_client = AsyncOpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    try:
        stream = await async_client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        full_response = ""
        print("\n--- 异步流式 ---")
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                full_response += content

        print()
        return full_response
    except Exception as e:
        print(f"[错误: {e}]")
        return ""

asyncio.run(async_stream("一句话说什么是 async"))


# ============================================================
# 6. 流式 vs 非流式对比
# ============================================================

"""
                    非流式 (stream=False)        流式 (stream=True)
──────────         ──────────────────           ────────────────
返回方式            等全部生成完再返回              逐 token 返回
用户体验            等待 → 突然出现全文              打字机效果，即时反馈
TTFT               等于总时间                      很短（几百ms）
适用场景            后台处理、批量任务              面向用户的聊天界面
代码复杂度          简单                           稍复杂（需要处理 chunk）
错误处理            简单 try/catch                 需要处理中途断流

生产环境建议：
- 面向用户 → 流式（TTFT 是核心 UX 指标）
- 后台批处理 → 非流式（代码简单）
- 流式 + 非流式可以并存在同一个应用中
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 实现一个 stream_to_sse 生成器
# 把流式 chunk 转换成 SSE 格式: "data: {...}\n\n"
# 这就是 FastAPI 流式接口需要的格式

# def stream_to_sse(prompt: str):
#     """Yield SSE-formatted chunks"""
#     ???

# TODO 2: 实现流式中断功能
# 当检测到特定关键词（如 "停止"）时中断流式输出
# 提示：在循环中检查条件并 break

# TODO 3: 实现流式输出的 Markdown 渲染
# 收集流式输出，当检测到完整的代码块（```...```）时
# 打印 "[代码块]" 标记而不是原始 markdown
# 这是前端 Chat UI 需要做的事情
