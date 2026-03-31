"""
Day 1: 用 Ollama 本地调用 LLM
Ollama 让你在本地运行开源模型，完全免费，无需 API Key
AI 开发中常用：本地调试、离线开发、隐私敏感场景
"""

from openai import OpenAI

# ============================================================
# 1. 连接本地 Ollama
# Ollama 兼容 OpenAI API 格式，用 OpenAI SDK 直接调用
# ============================================================

# Ollama runs on localhost:11434, compatible with OpenAI format
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama doesn't need a real key
)

# ============================================================
# 2. 基本调用 — Chat Completions
# ============================================================

def basic_chat(prompt: str, model: str = "qwen2.5:7b") -> str:
    """Send a single message and get a response"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[错误: {e}]"

result = basic_chat("用一句话解释什么是 Python")
print(f"回复: {result}\n")


# ============================================================
# 3. 理解 response 结构
# ============================================================

def detailed_call(prompt: str) -> None:
    """Show the full response structure from LLM API"""
    try:
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": prompt}],
        )

        # Response structure breakdown
        print("--- Response 结构 ---")
        print(f"model:          {response.model}")
        print(f"choices 数量:    {len(response.choices)}")

        choice = response.choices[0]
        print(f"finish_reason:  {choice.finish_reason}")  # "stop" = normal completion
        print(f"message.role:   {choice.message.role}")
        print(f"message.content: {choice.message.content[:100]}...")

        if response.usage:
            print(f"\n--- Token 用量 ---")
            print(f"prompt_tokens:     {response.usage.prompt_tokens}")
            print(f"completion_tokens: {response.usage.completion_tokens}")
            print(f"total_tokens:      {response.usage.total_tokens}")
    except Exception as e:
        print(f"[Ollama 未启动: {e}]")

detailed_call("什么是 RAG？")


# ============================================================
# 4. 关键参数实验
# ============================================================

def experiment_temperature(prompt: str) -> None:
    """Show how temperature affects output randomness"""
    print("\n--- Temperature 实验 ---")
    for temp in [0.0, 0.5, 1.0]:
        try:
            response = client.chat.completions.create(
                model="qwen2.5:7b",
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=50,  # Limit output length for comparison
            )
            content = response.choices[0].message.content
            print(f"  temp={temp}: {content[:80]}...")
        except Exception as e:
            print(f"  temp={temp}: [错误: {e}]")

experiment_temperature("写一句关于编程的话")


# ============================================================
# 5. System Prompt — 角色设定
# ============================================================

def chat_with_role(system_prompt: str, user_prompt: str) -> str:
    """Chat with a specific system role"""
    try:
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[错误: {e}]"

# Different roles produce different styles of answers
roles = [
    ("你是一个耐心的编程老师，用简单的比喻解释技术概念", "解释什么是 API"),
    ("你是一个高级工程师，回答精炼，直奔主题", "解释什么是 API"),
    ("你是一个幽默的程序员，喜欢用段子解释技术", "解释什么是 API"),
]

print("\n--- System Prompt 实验 ---")
for system, user in roles:
    print(f"\n角色: {system[:20]}...")
    result = chat_with_role(system, user)
    print(f"回答: {result[:100]}...\n")


# ============================================================
# 6. 查看可用模型
# ============================================================

def list_models() -> None:
    """List all locally available Ollama models"""
    try:
        models = client.models.list()
        print("--- 本地可用模型 ---")
        for model in models.data:
            print(f"  {model.id}")
    except Exception as e:
        print(f"[无法获取模型列表: {e}]")

list_models()


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 写一个函数 compare_models，同时用不同模型回答同一个问题
# 比较输出质量和速度
# 提示：可以用 time.time() 计时

# def compare_models(prompt: str, models: list[str]) -> None:
#     ???

# TODO 2: 实现一个 token_counter 函数
# 调用 LLM 时记录每次的 token 用量
# 累加显示总共消耗了多少 tokens

# TODO 3: 实现 max_tokens 参数实验
# 用不同的 max_tokens 值 (50, 100, 500) 调用 LLM
# 观察输出长度和 finish_reason 的变化
# 当 finish_reason 是 "length" 时表示输出被截断了
