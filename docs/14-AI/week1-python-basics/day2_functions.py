"""
Day 2: 函数 — *args / **kwargs、lambda、装饰器
AI 开发中常用：封装 API 调用、配置传递、日志/重试装饰器
"""

# ============================================================
# 1. 基本函数
# JS: function / arrow function  →  Python: def
# ============================================================

# Python 用缩进而不是花括号
def greet(name: str) -> str:
    return f"Hello, {name}!"

# 默认参数（和 JS 一样）
def call_llm(prompt: str, model: str = "qwen2.5:7b", temperature: float = 0.7) -> str:
    """Simulate an LLM API call with configurable parameters"""
    return f"[{model} @ temp={temperature}] Response to: {prompt}"

print(call_llm("你好"))
print(call_llm("你好", model="deepseek-chat", temperature=0.3))


# ============================================================
# 2. *args 和 **kwargs
# JS: ...args (rest parameters)  →  Python: *args, **kwargs
# ============================================================

# *args: 接收任意数量的位置参数 → tuple
def merge_messages(*messages):
    """Merge multiple message strings into one conversation"""
    return "\n".join(messages)

print(merge_messages("你好", "请帮我写代码", "谢谢"))

# **kwargs: 接收任意数量的关键字参数 → dict
def create_api_request(endpoint: str, **params):
    """Build an API request with arbitrary parameters"""
    print(f"POST {endpoint}")
    for key, value in params.items():
        print(f"{key}: {value}")

create_api_request(
    "/v1/chat/completions",
    model="qwen2.5:7b",
    temperature=0.3,
    max_tokens=1000,
    stream=True
)

# 实际 AI 开发中的常见用法：透传参数
def smart_call(prompt: str, **llm_kwargs):
    """Wrapper that forwards all extra kwargs to the LLM client"""
    defaults = {"model": "qwen2.5:7b", "temperature": 0.7}
    config = {**defaults, **llm_kwargs}  # kwargs 覆盖 defaults
    return f"Calling LLM with config: {config}, prompt: {prompt}"

print(smart_call("你好", temperature=0.3, max_tokens=500))


# ============================================================
# 3. Lambda 表达式
# JS: (x) => x * 2  →  Python: lambda x: x * 2
# ============================================================

# 简单 lambda
double = lambda x: x * 2
print(double(5))  # 10

# 常见用法：排序的 key 函数
documents = [
    {"title": "RAG 入门", "score": 0.85},
    {"title": "Agent 实战", "score": 0.92},
    {"title": "Prompt 技巧", "score": 0.78},
]

# Sort by relevance score, highest first
sorted_docs = sorted(documents, key=lambda doc: doc["score"], reverse=True)
for doc in sorted_docs:
    print(f"{doc['score']:.2f} - {doc['title']}")

# AI 场景：按 token 数排序 chunks（模拟）
chunks = ["短文本", "这是一段稍微长一些的文本内容", "中等长度的内容"]
sorted_chunks = sorted(chunks, key=lambda c: len(c))
print(f"按长度排序: {sorted_chunks}")


# ============================================================
# 4. 高阶函数
# JS: map / filter / reduce  →  Python: map / filter / functools.reduce
# ============================================================

# Python 推荐用列表推导式替代 map/filter，但了解它们仍有用

# map — 但推荐用列表推导式
print("map — 但推荐用列表推导式")
scores = [0.85, 0.92, 0.78, 0.65]
# JS: scores.map(s => Math.round(s * 100))
percentages = [round(s * 100) for s in scores]  # Pythonic way
print(percentages)  # [85, 92, 78, 65]

# filter — 但推荐用列表推导式
print("filter — 但推荐用列表推导式")
# JS: scores.filter(s => s > 0.8)
high_scores = [s for s in scores if s > 0.8]  # Pythonic way
print(high_scores)  # [0.85, 0.92]

# enumerate — Python 独有，遍历时同时获取索引
print("numerate — Python 独有，遍历时同时获取索引")
# JS: arr.forEach((item, index) => ...)
for i, score in enumerate(scores):
    print(f"#{i+1}: {score}")

# zip — 同时遍历多个列表
print("zip — 同时遍历多个列表")
# JS: 没有直接等价物
models = ["gpt-4", "deepseek", "qwen"]
speeds = [30, 80, 50]
for model, speed in zip(models, speeds):
    print(f"{model}: {speed} tokens/s")


# ============================================================
# 5. 装饰器 (Decorator)
# JS: 没有原生装饰器（TC39 Stage 3），Python 内置支持
# 装饰器 = 一个接收函数并返回新函数的高阶函数
# ============================================================

import time
import functools

# 装饰器：计时器（AI 开发中常用来测量 API 调用耗时）
def timer(func):
    """Measure and print the execution time of the wrapped function"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱ {func.__name__} 执行耗时: {elapsed:.3f}s")
        return result
    return wrapper

@timer
def slow_function():
    """Simulate a slow API call"""
    time.sleep(0.5)
    return "done"

slow_function()

# 装饰器：重试机制（API 调用失败时自动重试）
def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry the wrapped function up to max_attempts times on failure"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"  Attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise Exception(f"{func.__name__} failed after {max_attempts} attempts")
        return wrapper
    return decorator

@retry(max_attempts=3, delay=0.1)
def unstable_api_call():
    """Simulate an API call that fails randomly"""
    import random
    if random.random() < 0.7:
        raise ConnectionError("API timeout")
    return "Success!"

try:
    result = unstable_api_call()
    print(f"Result: {result}")
except Exception as e:
    print(f"Final error: {e}")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 写一个函数 build_messages，接收 system_prompt 和任意数量的 user 消息
# 返回 OpenAI 格式的 messages 数组
# 示例: build_messages("你是助手", "你好", "帮我写代码")
# 返回: [{"role": "system", "content": "你是助手"},
#        {"role": "user", "content": "你好"},
#        {"role": "user", "content": "帮我写代码"}]

def build_messages(system_prompt: str, *user_messages) -> list[dict]:
    return [{"role": "system", "content": system_prompt}, *[{"role": "user", "content": message} for message in user_messages]]

print(build_messages("你是助手", "你好", "帮我写代码"))

# TODO 2: 写一个装饰器 log_call，打印函数名和参数
# @log_call
# def add(a, b): return a + b
# add(1, 2)  → 打印: "Calling add(1, 2)" 然后返回 3

def log_call(func):
    @functiontools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print(f"Calling {func.__name__}({args}, {kwargs})")
        return result
    return wrapper

@log_call
def add(a, b):
    return a + b
print(add(1, 2))

# TODO 3: 给定一组文档和分数，用 zip + sorted 按分数从高到低排序，
# 然后只返回分数 > 0.8 的文档标题
titles = ["RAG 入门", "Agent 实战", "Prompt 技巧", "LLM 基础", "向量数据库"]
relevance = [0.85, 0.92, 0.78, 0.95, 0.65]
# top_titles = ???
# print(top_titles)  # ["向量数据库", "Agent 实战", "RAG 入门"] 不对，应该是分数>0.8的
