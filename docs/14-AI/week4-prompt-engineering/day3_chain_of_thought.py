"""
Day 3: Chain-of-Thought (CoT) — 让 LLM 分步推理
让 LLM "想一想再回答"，显著提升复杂问题的准确率
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
            max_tokens=kwargs.get("max_tokens", 1000),
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[错误: {e}]"


# ============================================================
# 1. 基本 CoT — "请一步一步思考"
# ============================================================

# Without CoT — LLM might jump to wrong answer
no_cot = chat([
    {"role": "user", "content": "一个商店有 23 个苹果，卖掉了 15 个，又进货了 8 个，客户退回了 3 个。现在有多少苹果？"},
])
print(f"无 CoT: {no_cot[:100]}")

# With CoT — add "请一步一步思考"
with_cot = chat([
    {"role": "user", "content": "一个商店有 23 个苹果，卖掉了 15 个，又进货了 8 个，客户退回了 3 个。现在有多少苹果？\n\n请一步一步思考。"},
])
print(f"\n有 CoT: {with_cot[:200]}")


# ============================================================
# 2. 结构化 CoT — 定义推理步骤
# ============================================================

STRUCTURED_COT_PROMPT = """你是一个 bug 分析专家。分析用户描述的 bug，按以下步骤推理：

Step 1: 理解问题
  描述 bug 的表现是什么

Step 2: 分析原因
  列出可能的原因（至少 3 个）

Step 3: 定位根因
  从可能的原因中推断最可能的根因

Step 4: 解决方案
  给出具体的修复方案

Step 5: 预防措施
  如何避免类似 bug 再次发生

请严格按照 Step 1-5 的格式回答。"""

bug_description = """
用户反馈：在 React 应用中，列表页面滚动到底部加载更多数据时，
偶尔会出现重复数据。刷新页面后正常，但继续滚动又会重复。
"""

print("\n--- 结构化 CoT ---")
result = chat([
    {"role": "system", "content": STRUCTURED_COT_PROMPT},
    {"role": "user", "content": bug_description},
])
print(result[:500])


# ============================================================
# 3. CoT + JSON — 推理过程 + 结构化结果
# ============================================================

def analyze_with_cot(question: str) -> dict:
    """
    Ask LLM to think step-by-step, then output structured result.
    The thinking part improves accuracy, the JSON part ensures parseability.
    """
    messages = [
        {"role": "system", "content": """你是一个分析专家。对于每个问题：
1. 先在 <thinking> 标签中分步推理
2. 然后输出最终答案的 JSON

格式：
<thinking>
推理步骤...
</thinking>

```json
{"answer": "最终答案", "confidence": 0.0-1.0, "reasoning_steps": 3}
```"""},
        {"role": "user", "content": question},
    ]

    result = chat(messages, temperature=0)

    # Parse thinking and JSON separately
    thinking = ""
    json_result = {}
    if "<thinking>" in result and "</thinking>" in result:
        thinking = result.split("<thinking>")[1].split("</thinking>")[0].strip()

    # Extract JSON from code block
    if "```json" in result:
        json_str = result.split("```json")[1].split("```")[0].strip()
        try:
            json_result = json.loads(json_str)
        except json.JSONDecodeError:
            json_result = {"raw": json_str}

    return {"thinking": thinking, "result": json_result, "raw": result}

print("\n--- CoT + JSON ---")
analysis = analyze_with_cot("比较 RAG 和 Fine-tuning，在什么场景下应该用哪个？")
print(f"推理过程: {analysis['thinking'][:200]}...")
print(f"结构化结果: {json.dumps(analysis['result'], indent=2, ensure_ascii=False)}")


# ============================================================
# 4. Self-Consistency — 多次推理取共识
# ============================================================

def self_consistent_answer(question: str, n: int = 3) -> dict:
    """
    Run the same question N times and pick the most common answer.
    Higher temperature adds diversity, majority vote improves accuracy.
    """
    answers = []
    for i in range(n):
        result = chat([
            {"role": "system", "content": "简洁回答问题，只给出最终答案。"},
            {"role": "user", "content": f"{question}\n\n请先思考，然后给出答案。"},
        ], temperature=0.7)
        answers.append(result)

    # Find most common answer (simplified — in practice use semantic similarity)
    print(f"\n--- Self-Consistency ({n} 次推理) ---")
    for i, ans in enumerate(answers):
        print(f"  回答 {i+1}: {ans[:80]}...")

    return {"answers": answers, "count": n}

self_consistent_answer("Python 3.12 最重要的新特性是什么？", n=3)


# ============================================================
# 5. ReAct 模式 — 推理 + 行动
# Agent 的核心模式，Week 8 会深入学习
# ============================================================

REACT_PROMPT = """你是一个研究助手。解决问题时按以下模式交替进行：

Thought: 分析当前情况，决定下一步
Action: 需要执行的操作（search/calculate/answer）
Observation: 操作的结果

当你有足够信息时，用 Action: answer 给出最终回答。

示例：
Thought: 用户问了关于 RAG 的问题，我需要先搜索相关信息
Action: search("RAG definition")
Observation: RAG (Retrieval-Augmented Generation) 是一种...
Thought: 现在我有了定义，可以回答了
Action: answer("RAG 是检索增强生成，它通过...")
"""

print("\n--- ReAct 模式 ---")
result = chat([
    {"role": "system", "content": REACT_PROMPT},
    {"role": "user", "content": "比较 LangChain 和 LlamaIndex 的优缺点"},
])
print(result[:400])


# ============================================================
# 6. CoT 技巧总结
# ============================================================

"""
CoT 使用场景               推荐方式                    说明
──────────               ────────                    ────
简单推理                  "请一步一步思考"              最简单，适合大部分场景
复杂分析                  结构化 Step 1-N               定义推理框架
需要 JSON 输出            <thinking> + JSON             推理和结果分离
高风险决策                Self-Consistency               多次推理投票
多步骤任务                ReAct 模式                    思考 + 行动交替

什么时候用 CoT：
✅ 数学/逻辑推理
✅ 多步骤问题
✅ 需要比较分析的问题
✅ 代码 debug / bug 分析

什么时候不需要 CoT：
❌ 简单的事实查询
❌ 简单的格式转换
❌ 翻译任务
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 实现一个 "代码复杂度分析器"
# 用结构化 CoT：
# Step 1: 识别代码结构（循环、条件、函数调用）
# Step 2: 计算圈复杂度
# Step 3: 识别可优化的部分
# Step 4: 输出 JSON 结果

# TODO 2: 用 Self-Consistency 方法判断一段代码是否有 bug
# 运行 5 次分析，如果 3 次以上说有 bug，就标记为有 bug
# 比较单次 vs 多次分析的准确率

# TODO 3: 实现一个简单的 ReAct Agent
# 定义 3 个工具：search, calculate, answer
# 解析 LLM 输出的 Action，模拟执行，把结果放回对话
# 循环直到 Action 是 answer
