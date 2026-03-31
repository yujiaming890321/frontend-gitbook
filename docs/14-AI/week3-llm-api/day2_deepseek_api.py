"""
Day 2: 用 DeepSeek API 调用云端 LLM
DeepSeek 兼容 OpenAI 格式，注册送 500 万 tokens
AI 开发中常用：云端推理、生产环境部署
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. 连接 DeepSeek API
# 和 Ollama 一样用 OpenAI SDK，只是 base_url 和 api_key 不同
# ============================================================

deepseek_client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-placeholder"),
)

# ============================================================
# 2. 连接通义千问 DashScope API
# 阿里云的 Qwen 模型，中文能力强
# ============================================================

dashscope_client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY", "sk-placeholder"),
)


# ============================================================
# 3. 统一的调用封装
# 不同的 provider，相同的 API 格式
# ============================================================

def create_client(provider: str = "ollama") -> tuple[OpenAI, str]:
    """
    Create an OpenAI-compatible client for different LLM providers.
    Returns (client, default_model) tuple.
    """
    providers = {
        "ollama": {
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "model": "qwen2.5:7b",
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "model": "deepseek-chat",
        },
        "dashscope": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
            "model": "qwen-turbo",
        },
    }

    config = providers.get(provider)
    if not config:
        raise ValueError(f"Unknown provider: {provider}. Use: {list(providers.keys())}")

    client = OpenAI(base_url=config["base_url"], api_key=config["api_key"])
    return client, config["model"]


def chat(
    prompt: str,
    provider: str = "ollama",
    system_prompt: str = "你是一个有用的助手",
    temperature: float = 0.7,
) -> str:
    """Unified chat function that works with any provider"""
    client, model = create_client(provider)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[{provider} 调用失败: {e}]"


# ============================================================
# 4. 对比不同 provider 的输出
# ============================================================

def compare_providers(prompt: str) -> None:
    """Compare responses from different LLM providers"""
    import time

    providers = ["ollama"]  # Add "deepseek", "dashscope" if you have API keys

    if os.getenv("DEEPSEEK_API_KEY"):
        providers.append("deepseek")
    if os.getenv("DASHSCOPE_API_KEY"):
        providers.append("dashscope")

    print(f"\n问题: {prompt}\n")
    for provider in providers:
        start = time.time()
        result = chat(prompt, provider=provider)
        elapsed = time.time() - start
        print(f"[{provider}] ({elapsed:.2f}s)")
        print(f"  {result[:150]}...")
        print()

compare_providers("用一句话解释什么是 RAG")


# ============================================================
# 5. API Key 安全管理
# ============================================================

"""
API Key 安全管理最佳实践:

1. 永远不要把 API Key 硬编码在代码中
   ❌ api_key = "sk-abc123..."
   ✅ api_key = os.getenv("DEEPSEEK_API_KEY")

2. 用 .env 文件管理 Key，并加入 .gitignore
   echo ".env" >> .gitignore

3. 生产环境用环境变量或密钥管理服务
   - AWS Secrets Manager
   - Azure Key Vault
   - Docker secrets

4. 定期轮换 Key，设置使用限额

5. 不同环境用不同的 Key
   - .env.development
   - .env.production
"""


# ============================================================
# 6. 错误处理和降级策略
# ============================================================

def resilient_chat(prompt: str, providers: list[str] | None = None) -> str:
    """
    Try multiple providers in order, fall back to next one on failure.
    Useful for production: if cloud API is down, fall back to local Ollama.
    """
    if providers is None:
        providers = ["deepseek", "dashscope", "ollama"]

    for provider in providers:
        try:
            result = chat(prompt, provider=provider)
            if not result.startswith("["):  # Not an error message
                print(f"  使用 {provider} 成功")
                return result
        except Exception:
            continue

    return "所有 LLM provider 都不可用"

print("\n--- 降级策略 ---")
result = resilient_chat("你好")
print(f"结果: {result[:100]}")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 扩展 create_client 函数，支持 Groq provider
# base_url: "https://api.groq.com/openai/v1"
# model: "llama-3.1-8b-instant"
# api_key: os.getenv("GROQ_API_KEY")

# TODO 2: 写一个 benchmark 函数
# 向每个可用的 provider 发送 5 个不同的问题
# 记录每个 provider 的平均响应时间和 token 使用量
# 输出一个对比表格

# TODO 3: 实现一个 CostTracker 类
# 记录每次 API 调用的 token 用量
# 根据不同 provider 的定价计算累计费用
# DeepSeek: 输入 ¥1/M tokens, 输出 ¥2/M tokens
# DashScope qwen-turbo: 免费额度内免费
