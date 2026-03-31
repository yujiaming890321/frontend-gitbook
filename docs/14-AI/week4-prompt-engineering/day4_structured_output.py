"""
Day 4: 结构化输出 — 让 LLM 稳定输出 JSON
AI 应用必备：LLM 的输出需要被程序解析，JSON 是最常用的格式
"""

from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal
import json

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "qwen2.5:7b"


def chat(messages: list[dict], **kwargs) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL, messages=messages,
            temperature=kwargs.get("temperature", 0),
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[错误: {e}]"


# ============================================================
# 1. 方法一：在 Prompt 中指定 JSON 格式
# 最通用的方法，所有模型都支持
# ============================================================

def extract_intent(user_input: str) -> dict:
    """Extract user intent using prompt-based JSON output"""
    messages = [
        {"role": "system", "content": """分析用户输入的意图。

你必须严格输出以下 JSON 格式，不要输出任何其他文本：
{
  "intent": "question | command | greeting | complaint",
  "confidence": 0.0 到 1.0,
  "entities": ["提取的关键实体"],
  "response_type": "text | code | list"
}"""},
        {"role": "user", "content": user_input},
    ]

    result = chat(messages)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from text
        if "{" in result and "}" in result:
            json_str = result[result.index("{"):result.rindex("}") + 1]
            return json.loads(json_str)
        return {"raw": result, "error": "parse_failed"}

print("--- Prompt-based JSON ---")
for text in ["帮我写一个排序算法", "你好啊", "这个功能怎么老是出 bug"]:
    result = extract_intent(text)
    print(f"  输入: {text}")
    print(f"  结果: {json.dumps(result, ensure_ascii=False)}\n")


# ============================================================
# 2. 方法二：Pydantic 定义 Schema，作为 Prompt 的一部分
# 用 pydantic 定义期望的输出结构
# ============================================================

class CodeIssue(BaseModel):
    severity: Literal["critical", "warning", "info"]
    line: Optional[int] = None
    message: str
    suggestion: str

class CodeReviewResult(BaseModel):
    """Expected output structure for code review"""
    issues: list[CodeIssue]
    score: int = Field(ge=0, le=100, description="Overall code quality score")
    summary: str

def review_code(code: str) -> CodeReviewResult:
    """Review code and return structured result validated by pydantic"""
    # Use pydantic schema as part of the prompt
    schema_hint = json.dumps(CodeReviewResult.model_json_schema(), indent=2, ensure_ascii=False)

    messages = [
        {"role": "system", "content": f"""你是代码审查专家。
审查代码并严格按以下 JSON Schema 输出结果：

{schema_hint}

只输出 JSON，不要其他文字。"""},
        {"role": "user", "content": f"审查这段代码：\n```python\n{code}\n```"},
    ]

    result = chat(messages)
    try:
        # Clean potential markdown wrapper
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        # Parse and validate with pydantic
        return CodeReviewResult.model_validate_json(cleaned)
    except Exception as e:
        print(f"  解析失败: {e}")
        return CodeReviewResult(issues=[], score=0, summary=f"解析失败: {result[:100]}")


print("--- Pydantic Schema 方法 ---")
sample_code = """
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] != None:
            result.append(data[i] * 2)
    return result
"""
review = review_code(sample_code)
print(f"  分数: {review.score}")
print(f"  摘要: {review.summary}")
for issue in review.issues:
    print(f"  [{issue.severity}] {issue.message}")


# ============================================================
# 3. 方法三：JSON Mode（部分 API 支持）
# ============================================================

def json_mode_example(prompt: str) -> dict:
    """
    Some APIs support native JSON mode via response_format parameter.
    This forces the model to output valid JSON.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "你是一个数据分析助手。输出 JSON 格式。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},  # Force JSON output
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # Not all models/providers support response_format
        print(f"  JSON Mode 不支持: {e}")
        return {}

print("\n--- JSON Mode ---")
result = json_mode_example("分析这段文本的情感：'这个产品挺好用的，就是价格有点贵'")
print(f"  {json.dumps(result, indent=2, ensure_ascii=False)}")


# ============================================================
# 4. 健壮的 JSON 解析器
# 实际项目中 LLM 输出的 JSON 经常有小问题
# ============================================================

def robust_json_parse(text: str) -> dict | list | None:
    """
    Parse JSON from LLM output, handling common issues:
    - Markdown code blocks
    - Extra text before/after JSON
    - Trailing commas
    - Single quotes
    """
    cleaned = text.strip()

    # Step 1: Remove markdown code block wrappers
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Step 2: Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Step 3: Extract JSON from surrounding text
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = cleaned.find(start_char)
        end_idx = cleaned.rfind(end_char)
        if start_idx != -1 and end_idx > start_idx:
            json_candidate = cleaned[start_idx:end_idx + 1]
            try:
                return json.loads(json_candidate)
            except json.JSONDecodeError:
                # Step 4: Fix trailing commas
                import re
                fixed = re.sub(r',\s*([}\]])', r'\1', json_candidate)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    pass

    return None

# Test with messy LLM outputs
test_cases = [
    '```json\n{"key": "value"}\n```',
    '好的，结果如下：{"score": 85, "grade": "B"} 希望对你有帮助！',
    '{"items": ["a", "b", "c",]}',  # trailing comma
]

print("\n--- 健壮 JSON 解析 ---")
for text in test_cases:
    result = robust_json_parse(text)
    print(f"  输入: {text[:50]}...")
    print(f"  解析: {result}\n")


# ============================================================
# 5. 输出格式对比
# ============================================================

"""
方法                     可靠性   通用性   实现复杂度
──────────              ──────   ──────   ──────────
Prompt 指定 JSON 格式    中       高       低
Few-Shot + JSON          高       高       中
Pydantic Schema          中-高    高       中
JSON Mode (API 参数)     最高     低       最低
Function Calling         最高     中       中

推荐组合：
1. 简单场景 → Prompt + 健壮解析器
2. 复杂场景 → Few-Shot + Pydantic 校验
3. 生产环境 → Function Calling（Day 5 学习）
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 用 pydantic 定义一个 "会议纪要" 的结构
# MeetingMinutes: title, date, attendees, action_items, decisions
# 写 prompt 让 LLM 把一段会议文字转成这个结构

# TODO 2: 实现一个 OutputValidator 类
# 接收 pydantic model 和 LLM 输出
# 自动尝试解析 → 如果失败，用 LLM 修正格式 → 再次解析
# 最多重试 3 次

# class OutputValidator:
#     def validate(self, model_class, llm_output: str, max_retries: int = 3):
#         ???

# TODO 3: 实现 "自动表格提取器"
# 输入：一段包含表格信息的文字
# 输出：JSON 数组 [{"col1": "val1", "col2": "val2"}, ...]
# 用 Few-Shot 让 LLM 学会表格格式
