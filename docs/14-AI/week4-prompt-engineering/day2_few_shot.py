"""
Day 2: Few-Shot — 用示例引导 LLM 输出固定格式
给 LLM 几个"示范"，它就能学会输出你要的格式
这是让 LLM 输出稳定、可预测结果的最实用技巧
"""

from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "qwen2.5:7b"


def chat(messages: list[dict], **kwargs) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL, messages=messages,
            temperature=kwargs.get("temperature", 0.3),
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[错误: {e}]"


# ============================================================
# 1. Zero-Shot vs Few-Shot
# ============================================================

# Zero-Shot: 没有示例，直接给指令
zero_shot_messages = [
    {"role": "system", "content": "把用户输入的文本分类为 positive、negative 或 neutral。只输出分类标签。"},
    {"role": "user", "content": "这个产品太棒了，我非常满意！"},
]
print(f"Zero-Shot: {chat(zero_shot_messages)}")

# Few-Shot: 给几个示例，LLM 学会格式
few_shot_messages = [
    {"role": "system", "content": "把用户输入的文本分类为 positive、negative 或 neutral。"},
    # Example 1
    {"role": "user", "content": "今天天气真好"},
    {"role": "assistant", "content": "positive"},
    # Example 2
    {"role": "user", "content": "这个服务太差了"},
    {"role": "assistant", "content": "negative"},
    # Example 3
    {"role": "user", "content": "明天是周三"},
    {"role": "assistant", "content": "neutral"},
    # Actual input
    {"role": "user", "content": "这个产品太棒了，我非常满意！"},
]
print(f"Few-Shot:  {chat(few_shot_messages)}")


# ============================================================
# 2. Few-Shot 结构化输出 — 让 LLM 稳定输出 JSON
# ============================================================

def classify_with_examples(text: str) -> dict:
    """Classify text using few-shot examples to ensure JSON output"""
    messages = [
        {"role": "system", "content": "分析用户评论的情感和关键主题。严格按 JSON 格式输出。"},

        # Few-shot examples teach the exact output format
        {"role": "user", "content": "手机拍照效果很好，但电池不太耐用"},
        {"role": "assistant", "content": json.dumps({
            "sentiment": "mixed",
            "score": 0.6,
            "topics": ["camera", "battery"],
            "summary": "拍照好评，电池差评"
        }, ensure_ascii=False)},

        {"role": "user", "content": "物流很快，包装也不错"},
        {"role": "assistant", "content": json.dumps({
            "sentiment": "positive",
            "score": 0.9,
            "topics": ["logistics", "packaging"],
            "summary": "物流和包装都满意"
        }, ensure_ascii=False)},

        # Actual input
        {"role": "user", "content": text},
    ]

    result = chat(messages, temperature=0)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"raw": result, "error": "JSON parse failed"}

print("\n--- Few-Shot JSON 输出 ---")
review = classify_with_examples("价格太贵了，但质量确实不错，客服态度也很好")
print(json.dumps(review, indent=2, ensure_ascii=False))


# ============================================================
# 3. Few-Shot 代码生成 — 教 LLM 你的代码风格
# ============================================================

CODE_STYLE_EXAMPLES = [
    {"role": "system", "content": """你是一个 Python 代码生成器。
按照以下代码风格生成函数：
- 使用 type hints
- 函数有英文 docstring
- 用 dataclass 或 pydantic 定义数据结构
- 错误处理用 try/except，不用 if/else 检查"""},

    # Example 1: show the coding style
    {"role": "user", "content": "写一个函数：根据用户 ID 获取用户信息"},
    {"role": "assistant", "content": """```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    name: str
    email: str

def get_user(user_id: int) -> Optional[User]:
    \"\"\"Fetch user by ID from database\"\"\"
    try:
        data = db.query("SELECT * FROM users WHERE id = ?", user_id)
        return User(**data) if data else None
    except DatabaseError as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        return None
```"""},

    # Example 2: reinforce the style
    {"role": "user", "content": "写一个函数：批量发送消息"},
    {"role": "assistant", "content": """```python
from dataclasses import dataclass

@dataclass
class SendResult:
    success: int
    failed: int
    errors: list[str]

async def send_batch_messages(
    messages: list[str],
    recipients: list[str],
) -> SendResult:
    \"\"\"Send messages to multiple recipients concurrently\"\"\"
    errors = []
    success = 0
    for recipient in recipients:
        try:
            await send_message(recipient, messages)
            success += 1
        except SendError as e:
            errors.append(f"{recipient}: {e}")

    return SendResult(
        success=success,
        failed=len(errors),
        errors=errors,
    )
```"""},
]

def generate_code(task: str) -> str:
    """Generate code following the few-shot style examples"""
    messages = CODE_STYLE_EXAMPLES + [{"role": "user", "content": task}]
    return chat(messages)

print("\n--- Few-Shot 代码生成 ---")
print(generate_code("写一个函数：搜索文档并返回最相关的 3 条结果"))


# ============================================================
# 4. Few-Shot 数据提取
# ============================================================

def extract_entities(text: str) -> dict:
    """Extract structured entities from unstructured text"""
    messages = [
        {"role": "system", "content": "从文本中提取结构化信息。严格按示例格式输出 JSON。"},

        {"role": "user", "content": "张三，手机号 13800138000，住在北京市朝阳区"},
        {"role": "assistant", "content": json.dumps({
            "name": "张三",
            "phone": "13800138000",
            "address": {"city": "北京", "district": "朝阳区"},
        }, ensure_ascii=False)},

        {"role": "user", "content": "李四的邮箱是 lisi@example.com，在上海浦东新区工作"},
        {"role": "assistant", "content": json.dumps({
            "name": "李四",
            "email": "lisi@example.com",
            "address": {"city": "上海", "district": "浦东新区"},
        }, ensure_ascii=False)},

        {"role": "user", "content": text},
    ]
    result = chat(messages, temperature=0)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"raw": result}

print("\n--- Few-Shot 数据提取 ---")
extracted = extract_entities("王五是一名工程师，联系电话 15912345678，目前在深圳南山区上班")
print(json.dumps(extracted, indent=2, ensure_ascii=False))


# ============================================================
# 5. Few-Shot 最佳实践
# ============================================================

"""
Few-Shot 最佳实践:

1. 示例数量：2-5 个就够了
   - 太少：LLM 可能没学会格式
   - 太多：浪费 token，可能过拟合

2. 示例要有代表性
   - 覆盖不同的边界情况
   - 包含"正面"和"负面"的例子
   - 包含"简单"和"复杂"的例子

3. 保持示例和实际输入的格式一致
   ❌ 示例用英文，输入用中文
   ✅ 示例和输入用同一种语言/格式

4. 用 assistant 角色提供示例回答
   - user → 输入示例
   - assistant → 期望的输出示例
   这比在 system prompt 中写示例更有效

5. 搭配 temperature=0 使用
   Few-shot + 低 temperature = 最稳定的输出
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 用 Few-Shot 实现一个"Git Commit Message 分类器"
# 输入一条 commit message，输出分类：
# {"type": "feat|fix|refactor|docs|test|chore", "scope": "模块名", "description": "简述"}
# 写 3 个示例来教 LLM 格式

# TODO 2: 用 Few-Shot 实现一个"错误日志解析器"
# 输入一段错误日志，提取：
# {"error_type": "...", "message": "...", "file": "...", "line": 42, "severity": "critical|warning|info"}

# TODO 3: 用 Few-Shot 教 LLM 翻译代码注释风格
# 输入带中文注释的代码 → 输出带英文注释的代码
# 要求注释风格一致（如 docstring 用 Google style）
