"""
Day 1: HTTP 请求 — requests / httpx
AI 开发中常用：调用 LLM API、获取外部数据、与向量数据库通信
你已经熟悉 fetch/axios，这两个库概念一模一样
"""

import json

# ============================================================
# 1. requests — 同步 HTTP 请求
# JS: fetch / axios  →  Python: requests
# ============================================================

import requests

# --- GET 请求 ---
# JS: const res = await fetch("https://api.github.com/users/octocat")
# JS: const data = await res.json()

response = requests.get("https://api.github.com/users/octocat")
print(f"状态码: {response.status_code}")    # JS: res.status
print(f"Content-Type: {response.headers['content-type']}")

# Parse JSON response
data = response.json()                       # JS: await res.json()
print(f"用户: {data['login']}")
print(f"头像: {data['avatar_url']}")

# --- POST 请求 ---
# JS: await fetch(url, { method: "POST", headers: {...}, body: JSON.stringify(data) })

# Simulate calling Ollama's local API
def call_ollama(prompt: str, model: str = "qwen2.5:7b") -> str:
    """Send a chat completion request to local Ollama server"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={                              # json= 自动设置 Content-Type 和序列化
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,                         # JS: AbortController + setTimeout
        )
        response.raise_for_status()             # Throw on 4xx/5xx (like axios)
        return response.json()["response"]
    except requests.ConnectionError:
        return "[Ollama 未启动，跳过实际调用]"
    except requests.Timeout:
        return "[请求超时]"

result = call_ollama("用一句话解释什么是 Python")
print(f"\nOllama 回复: {result}")

# --- 请求头和认证 ---
# JS: fetch(url, { headers: { "Authorization": "Bearer xxx" } })

def call_deepseek(prompt: str, api_key: str) -> str:
    """Call DeepSeek API with authentication header"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[API 调用失败: {e}]"

# print(call_deepseek("你好", "your-api-key"))


# ============================================================
# 2. httpx — 支持同步和异步的 HTTP 客户端
# 更现代，API 和 requests 几乎一样，但支持 async
# AI 开发中推荐用 httpx 替代 requests
# ============================================================

import httpx

# --- 同步用法（和 requests 一样） ---
response = httpx.get("https://api.github.com/users/octocat")
print(f"\nhttpx 状态码: {response.status_code}")

# --- 异步用法（AI 开发主力） ---
import asyncio

async def async_http_example():
    """Demonstrate async HTTP requests with httpx"""
    # AsyncClient — like creating an axios instance
    async with httpx.AsyncClient() as client:
        # Single request
        response = await client.get("https://api.github.com/users/octocat")
        print(f"\nasync 请求状态码: {response.status_code}")

        # Concurrent requests — like Promise.all with fetch
        urls = [
            "https://api.github.com/users/octocat",
            "https://api.github.com/users/github",
        ]
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        for r in responses:
            data = r.json()
            print(f"  用户: {data['login']}")

asyncio.run(async_http_example())


# ============================================================
# 3. Session / Client — 连接复用
# JS: 创建 axios instance  →  Python: requests.Session / httpx.Client
# ============================================================

# requests Session — reuse TCP connections and default headers
session = requests.Session()
session.headers.update({
    "User-Agent": "AI-Learning-Bot/1.0",
    "Accept": "application/json",
})

# All requests through this session share the same headers and connection pool
r1 = session.get("https://api.github.com/users/octocat")
r2 = session.get("https://api.github.com/users/github")
print(f"\nSession 请求: {r1.json()['login']}, {r2.json()['login']}")
session.close()

# httpx Client — same concept, also supports base_url
# Useful for LLM APIs: set base_url once, reuse for all calls
with httpx.Client(
    base_url="https://api.github.com",
    headers={"User-Agent": "AI-Learning-Bot/1.0"},
    timeout=10.0,
) as client:
    r = client.get("/users/octocat")
    print(f"httpx Client: {r.json()['login']}")


# ============================================================
# 4. 流式响应 (Streaming)
# AI 场景：接收 LLM 的流式输出（打字机效果）
# JS: for await (const chunk of response.body) {}
# ============================================================

def stream_ollama(prompt: str):
    """Stream response from Ollama — like reading SSE from ChatGPT"""
    try:
        # stream=True enables chunked transfer
        with requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:7b", "prompt": prompt, "stream": True},
            stream=True,
            timeout=30,
        ) as response:
            print("\n流式输出: ", end="")
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    print(data.get("response", ""), end="", flush=True)
                    if data.get("done"):
                        break
            print()  # newline at end
    except requests.ConnectionError:
        print("\n[Ollama 未启动，跳过流式演示]")

stream_ollama("用一句话说什么是 RAG")


# ============================================================
# 5. requests vs httpx vs fetch/axios 对比
# ============================================================

"""
JS/TS                        Python requests           Python httpx            说明
─────                        ───────────────           ────────────            ────
fetch(url)                   requests.get(url)         httpx.get(url)          GET 请求
await res.json()             res.json()                res.json()              解析 JSON
fetch(url, {method:"POST"})  requests.post(url, ...)   httpx.post(url, ...)    POST 请求
axios.create({baseURL})      requests.Session()        httpx.Client(base_url)  复用连接
AbortController + timeout    timeout=30                timeout=30              超时
response.ok                  res.ok / res.status_code  res.is_success          状态检查
res.body (ReadableStream)    stream=True, iter_lines   stream()                流式读取

推荐选择：
- 简单脚本 → requests（生态最成熟）
- AI 项目 → httpx（支持 async，FastAPI 默认推荐）
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 用 httpx.AsyncClient 写一个函数，并发请求 3 个不同的 GitHub 用户信息
# 返回一个列表：[{"login": "xxx", "followers": 123}, ...]
# 提示：用 asyncio.gather

# async def fetch_github_users(usernames: list[str]) -> list[dict]:
#     ???

# TODO 2: 用 requests.Session 封装一个简单的 LLM 客户端类
# - __init__ 接收 base_url 和 api_key
# - chat(prompt) 方法发送请求并返回回复内容
# - 自动设置 Authorization header

# class SimpleLLMClient:
#     ???

# TODO 3: 实现一个带重试的 HTTP 请求函数
# - 遇到 5xx 错误或超时时，最多重试 3 次
# - 每次重试间隔翻倍（1s, 2s, 4s）
# - 返回最终的 response 或抛出异常

# def resilient_request(method: str, url: str, **kwargs) -> requests.Response:
#     ???
