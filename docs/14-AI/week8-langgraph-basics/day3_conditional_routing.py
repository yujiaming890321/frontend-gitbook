"""
Day 3: 条件边 -- 根据 LLM 判断结果路由到不同分支
这是 LangGraph 最强大的特性：让图根据运行时状态动态决定下一步

前端类比：
- Conditional Edge ~ React Router 的条件重定向 / 路由守卫
- 就像 Express 中间件里根据 req.user.role 决定跳到不同的 handler
- 或者像 Redux 中间件根据 action type 决定走哪个 reducer

传统 chain（链）只能走直线：A -> B -> C
有了条件边，graph 可以分叉：
       ┌──> B1 ──> END
  A ──>│
       └──> B2 ──> END
"""

from typing import TypedDict, Annotated, Literal
import operator
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama

# Initialize LLM
llm = Ollama(model="qwen2.5:7b", temperature=0.3)


# ============================================================
# 1. 基础条件路由 — 不用 LLM，先理解机制
# ============================================================

print("=" * 60)
print("1. 基础条件路由 (不用 LLM)")
print("=" * 60)


class RouterState(TypedDict):
    """State for basic routing demo"""
    number: int
    result: str
    route_taken: str


def check_number_node(state: RouterState) -> dict:
    """Classify the number — this is the 'decision' node"""
    n = state["number"]
    if n > 0:
        return {"route_taken": "positive"}
    elif n < 0:
        return {"route_taken": "negative"}
    else:
        return {"route_taken": "zero"}


def positive_node(state: RouterState) -> dict:
    """Handle positive numbers"""
    return {"result": f"{state['number']} is positive, its square is {state['number']**2}"}


def negative_node(state: RouterState) -> dict:
    """Handle negative numbers"""
    return {"result": f"{state['number']} is negative, its absolute value is {abs(state['number'])}"}


def zero_node(state: RouterState) -> dict:
    """Handle zero"""
    return {"result": "The number is zero — the identity element of addition"}


# The routing function: returns the NAME of the next node
# This is the KEY concept of conditional edges
def route_by_number(state: RouterState) -> str:
    """Decide which node to go to next based on state.

    This function is passed to add_conditional_edges().
    It must return the name of a node (or END).

    Front-end analogy:
    - Like a React Router loader that decides which page to redirect to
    - Like Express next('route') that skips to a different handler

    Returns the name of the next node to visit.
    """
    route = state["route_taken"]
    if route == "positive":
        return "handle_positive"
    elif route == "negative":
        return "handle_negative"
    else:
        return "handle_zero"


# Build the conditional graph
router_builder = StateGraph(RouterState)

# Add all nodes
router_builder.add_node("check", check_number_node)
router_builder.add_node("handle_positive", positive_node)
router_builder.add_node("handle_negative", negative_node)
router_builder.add_node("handle_zero", zero_node)

# Set entry point
router_builder.set_entry_point("check")

# Add CONDITIONAL edge from "check" node
# The second argument is the routing function
# The third argument maps return values to node names
router_builder.add_conditional_edges(
    "check",                    # Source node
    route_by_number,            # Routing function
    {                           # Map: routing function return value -> node name
        "handle_positive": "handle_positive",
        "handle_negative": "handle_negative",
        "handle_zero": "handle_zero",
    }
)

# All branches lead to END
router_builder.add_edge("handle_positive", END)
router_builder.add_edge("handle_negative", END)
router_builder.add_edge("handle_zero", END)

router_graph = router_builder.compile()

# Test with different numbers
for num in [42, -7, 0]:
    result = router_graph.invoke({"number": num, "result": "", "route_taken": ""})
    print(f"  Input: {num:3d} -> {result['result']}")

print("""
条件边的关键代码：

  graph.add_conditional_edges(
      "source_node",       # 从哪个节点出发
      routing_function,     # 路由函数（返回下一个节点名）
      {                     # 映射表：路由函数返回值 -> 节点名
          "option_a": "node_a",
          "option_b": "node_b",
      }
  )

前端类比：
  <Route path="/dashboard"
    loader={({request}) => {
      if (!isAuth) return redirect('/login')    // 条件路由
      return null
    }}
  />
""")


# ============================================================
# 2. LLM 驱动的条件路由 — 意图分类
# ============================================================

print("\n" + "=" * 60)
print("2. LLM 驱动的条件路由 -- 意图分类")
print("=" * 60)

# Real-world pattern: use LLM to classify user intent,
# then route to different handling branches


class IntentState(TypedDict):
    """State for intent classification and routing"""
    user_input: str
    intent: str          # classified intent
    response: str        # final response
    trace: Annotated[list[str], operator.add]


def classify_intent_node(state: IntentState) -> dict:
    """Use LLM to classify user intent.

    This is where LLM meets conditional routing:
    The LLM's output determines which branch to take.

    Front-end analogy:
    Like a form validator that checks input type
    before deciding which form handler to use.
    """
    prompt = f"""Classify the following user message into exactly ONE category.
Reply with ONLY the category name, nothing else.

Categories:
- question (user is asking a question)
- greeting (user is saying hello/goodbye)
- complaint (user is complaining or reporting a problem)
- other (anything else)

User message: "{state['user_input']}"

Category:"""

    intent = llm.invoke(prompt).strip().lower()

    # Normalize: ensure we get a valid intent
    valid_intents = ["question", "greeting", "complaint", "other"]
    if intent not in valid_intents:
        # Fallback: try to find a matching intent in the response
        for valid in valid_intents:
            if valid in intent:
                intent = valid
                break
        else:
            intent = "other"

    return {
        "intent": intent,
        "trace": [f"classified intent as: {intent}"],
    }


def handle_question_node(state: IntentState) -> dict:
    """Handle questions by generating an informative answer"""
    prompt = f"Answer this question concisely (2 sentences): {state['user_input']}"
    response = llm.invoke(prompt)
    return {
        "response": f"[Question Handler] {response.strip()}",
        "trace": ["routed to question handler"],
    }


def handle_greeting_node(state: IntentState) -> dict:
    """Handle greetings with a friendly response"""
    return {
        "response": "[Greeting Handler] Hello! How can I help you today?",
        "trace": ["routed to greeting handler"],
    }


def handle_complaint_node(state: IntentState) -> dict:
    """Handle complaints with empathy"""
    prompt = f"A user has a complaint: '{state['user_input']}'. Respond with empathy in 1-2 sentences."
    response = llm.invoke(prompt)
    return {
        "response": f"[Complaint Handler] {response.strip()}",
        "trace": ["routed to complaint handler"],
    }


def handle_other_node(state: IntentState) -> dict:
    """Handle unclassified inputs"""
    return {
        "response": "[Other Handler] I'm not sure how to handle that. Could you rephrase?",
        "trace": ["routed to other handler"],
    }


# Routing function for intent
def route_by_intent(state: IntentState) -> str:
    """Route to the appropriate handler based on classified intent"""
    intent = state["intent"]
    route_map = {
        "question": "handle_question",
        "greeting": "handle_greeting",
        "complaint": "handle_complaint",
        "other": "handle_other",
    }
    return route_map.get(intent, "handle_other")


# Build the intent routing graph
intent_builder = StateGraph(IntentState)
intent_builder.add_node("classify", classify_intent_node)
intent_builder.add_node("handle_question", handle_question_node)
intent_builder.add_node("handle_greeting", handle_greeting_node)
intent_builder.add_node("handle_complaint", handle_complaint_node)
intent_builder.add_node("handle_other", handle_other_node)

intent_builder.set_entry_point("classify")
intent_builder.add_conditional_edges(
    "classify",
    route_by_intent,
    {
        "handle_question": "handle_question",
        "handle_greeting": "handle_greeting",
        "handle_complaint": "handle_complaint",
        "handle_other": "handle_other",
    }
)

# All handlers lead to END
intent_builder.add_edge("handle_question", END)
intent_builder.add_edge("handle_greeting", END)
intent_builder.add_edge("handle_complaint", END)
intent_builder.add_edge("handle_other", END)

intent_graph = intent_builder.compile()

# Test with different inputs
test_inputs = [
    "Hello! How are you?",
    "What is LangGraph used for?",
    "Your service is terrible and slow!",
    "asdfghjkl",
]

for inp in test_inputs:
    result = intent_graph.invoke({
        "user_input": inp,
        "intent": "",
        "response": "",
        "trace": [],
    })
    print(f"  Input:    '{inp}'")
    print(f"  Intent:   {result['intent']}")
    print(f"  Response: {result['response'][:100]}")
    print(f"  Trace:    {result['trace']}")
    print()


# ============================================================
# 3. 循环条件路由 — 带重试逻辑
# ============================================================

print("\n" + "=" * 60)
print("3. 循环条件路由 -- 重试逻辑")
print("=" * 60)

# Graphs can have LOOPS! This is what makes them more powerful than chains.
# A node can route BACK to a previous node (retry pattern).
#
# Front-end analogy:
# - Like a form that keeps showing validation errors until input is correct
# - Like a React effect that re-fetches data on failure


class RetryState(TypedDict):
    """State for retry loop demo"""
    question: str
    answer: str
    is_valid: bool
    attempt: int
    max_attempts: int
    trace: Annotated[list[str], operator.add]


def generate_answer_node(state: RetryState) -> dict:
    """Generate an answer to the question"""
    attempt = state["attempt"] + 1
    prompt = f"""Answer this question in exactly ONE sentence.
Do NOT use more than one sentence.

Question: {state['question']}

One sentence answer:"""

    answer = llm.invoke(prompt).strip()
    return {
        "answer": answer,
        "attempt": attempt,
        "trace": [f"attempt {attempt}: generated answer ({len(answer)} chars)"],
    }


def validate_answer_node(state: RetryState) -> dict:
    """Validate that the answer meets our criteria.

    Check: answer must be one sentence (ends with period, no multiple periods).
    In real apps, you might validate format, safety, accuracy, etc.
    """
    answer = state["answer"]
    # Simple validation: check if it's roughly one sentence
    sentence_count = answer.count(".") + answer.count("!") + answer.count("?")
    is_valid = 1 <= sentence_count <= 2 and len(answer) < 500

    return {
        "is_valid": is_valid,
        "trace": [f"validation: {'PASS' if is_valid else 'FAIL'} (sentences: ~{sentence_count})"],
    }


def route_after_validation(state: RetryState) -> str:
    """Decide: accept the answer or retry?

    This creates a LOOP in the graph:
    generate -> validate -> generate (retry) -> validate -> ...

    The loop exits when validation passes OR max attempts reached.
    """
    if state["is_valid"]:
        return "accept"
    elif state["attempt"] >= state["max_attempts"]:
        return "accept"  # Give up after max attempts
    else:
        return "retry"


def accept_node(state: RetryState) -> dict:
    """Accept the final answer"""
    return {
        "trace": [f"accepted answer after {state['attempt']} attempt(s)"],
    }


# Build the retry graph (with a loop!)
retry_builder = StateGraph(RetryState)
retry_builder.add_node("generate", generate_answer_node)
retry_builder.add_node("validate", validate_answer_node)
retry_builder.add_node("accept", accept_node)

retry_builder.set_entry_point("generate")
retry_builder.add_edge("generate", "validate")

# Conditional edge that can loop back!
retry_builder.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "retry": "generate",   # Loop back to generate
        "accept": "accept",    # Move forward to accept
    }
)

retry_builder.add_edge("accept", END)
retry_graph = retry_builder.compile()

result = retry_graph.invoke({
    "question": "What is the capital of France?",
    "answer": "",
    "is_valid": False,
    "attempt": 0,
    "max_attempts": 3,
    "trace": [],
})

print(f"  Question: {result['question']}")
print(f"  Answer:   {result['answer'][:200]}")
print(f"  Attempts: {result['attempt']}")
print(f"  Valid:    {result['is_valid']}")
print(f"  Trace:")
for step in result["trace"]:
    print(f"    -> {step}")


# ============================================================
# 4. 多分支合并 — Fan-out / Fan-in 模式
# ============================================================

print("\n" + "=" * 60)
print("4. 多分支合并 -- 分析然后汇总")
print("=" * 60)

# Pattern: split into parallel branches, then merge results
# Front-end analogy: Promise.all([fetchA(), fetchB()]).then(mergeResults)
# Note: LangGraph executes branches sequentially by default,
# but the PATTERN is the same as parallel processing


class AnalysisState(TypedDict):
    """State for multi-branch analysis"""
    text: str
    sentiment: str
    keywords: str
    summary: str
    final_report: str
    trace: Annotated[list[str], operator.add]


def analyze_sentiment_node(state: AnalysisState) -> dict:
    """Analyze sentiment of the text"""
    prompt = f"""Analyze the sentiment of this text. Reply with only: positive, negative, or neutral.

Text: "{state['text']}"

Sentiment:"""
    sentiment = llm.invoke(prompt).strip().lower()
    return {
        "sentiment": sentiment,
        "trace": [f"sentiment analysis: {sentiment}"],
    }


def extract_keywords_node(state: AnalysisState) -> dict:
    """Extract keywords from the text"""
    prompt = f"""Extract 3-5 keywords from this text. List them comma-separated.

Text: "{state['text']}"

Keywords:"""
    keywords = llm.invoke(prompt).strip()
    return {
        "keywords": keywords,
        "trace": [f"keyword extraction: {keywords[:50]}"],
    }


def summarize_node(state: AnalysisState) -> dict:
    """Summarize the text in one sentence"""
    prompt = f"""Summarize this text in one sentence:

Text: "{state['text']}"

Summary:"""
    summary = llm.invoke(prompt).strip()
    return {
        "summary": summary,
        "trace": [f"summarization done"],
    }


def merge_report_node(state: AnalysisState) -> dict:
    """Merge all analysis results into a final report"""
    report = f"""
=== Text Analysis Report ===
Original: {state['text'][:100]}...

Sentiment: {state['sentiment']}
Keywords:  {state['keywords']}
Summary:   {state['summary']}
============================
""".strip()
    return {
        "final_report": report,
        "trace": ["merged into final report"],
    }


# Build analysis graph with sequential "fan-out" then merge
# Note: true parallel execution would use async, but the pattern matters
analysis_builder = StateGraph(AnalysisState)
analysis_builder.add_node("sentiment", analyze_sentiment_node)
analysis_builder.add_node("keywords", extract_keywords_node)
analysis_builder.add_node("summarize", summarize_node)
analysis_builder.add_node("merge", merge_report_node)

analysis_builder.set_entry_point("sentiment")
analysis_builder.add_edge("sentiment", "keywords")
analysis_builder.add_edge("keywords", "summarize")
analysis_builder.add_edge("summarize", "merge")
analysis_builder.add_edge("merge", END)

analysis_graph = analysis_builder.compile()

result = analysis_graph.invoke({
    "text": "LangGraph is an amazing framework for building AI agents. "
            "It makes complex workflows simple and maintainable. "
            "I highly recommend it for any AI project.",
    "sentiment": "",
    "keywords": "",
    "summary": "",
    "final_report": "",
    "trace": [],
})

print(result["final_report"])
print(f"\nTrace: {result['trace']}")


# ============================================================
# 5. 条件路由 + 循环的组合 — 质量控制管道
# ============================================================

print("\n" + "=" * 60)
print("5. 条件路由 + 循环 -- 质量控制管道")
print("=" * 60)


class QAState(TypedDict):
    """State for quality-controlled generation"""
    topic: str
    content: str
    quality_score: str      # "good", "acceptable", "poor"
    revision_count: int
    max_revisions: int
    trace: Annotated[list[str], operator.add]


def generate_content_node(state: QAState) -> dict:
    """Generate or regenerate content about the topic"""
    revision = state["revision_count"]

    if revision == 0:
        prompt = f"Write a 2-sentence explanation of {state['topic']}."
    else:
        prompt = f"""Improve this explanation of {state['topic']}.
Previous version: "{state['content']}"
Make it clearer and more concise. Write 2 sentences."""

    content = llm.invoke(prompt).strip()
    return {
        "content": content,
        "revision_count": revision + 1,
        "trace": [f"revision {revision + 1}: generated content"],
    }


def evaluate_quality_node(state: QAState) -> dict:
    """Evaluate the quality of generated content"""
    prompt = f"""Rate the quality of this explanation on a scale.
Reply with exactly one word: good, acceptable, or poor.

Text: "{state['content']}"

Quality:"""
    quality = llm.invoke(prompt).strip().lower()

    # Normalize quality score
    if "good" in quality:
        quality = "good"
    elif "acceptable" in quality or "ok" in quality:
        quality = "acceptable"
    else:
        quality = "poor"

    return {
        "quality_score": quality,
        "trace": [f"quality evaluation: {quality}"],
    }


def route_by_quality(state: QAState) -> str:
    """Route based on quality and revision count"""
    if state["quality_score"] == "good":
        return "finalize"
    elif state["revision_count"] >= state["max_revisions"]:
        return "finalize"  # Give up, accept current version
    else:
        return "revise"


def finalize_node(state: QAState) -> dict:
    """Accept the content as final"""
    return {
        "trace": [f"finalized after {state['revision_count']} revision(s), "
                  f"quality: {state['quality_score']}"],
    }


# Build QA graph with conditional loop
qa_builder = StateGraph(QAState)
qa_builder.add_node("generate", generate_content_node)
qa_builder.add_node("evaluate", evaluate_quality_node)
qa_builder.add_node("finalize", finalize_node)

qa_builder.set_entry_point("generate")
qa_builder.add_edge("generate", "evaluate")

qa_builder.add_conditional_edges(
    "evaluate",
    route_by_quality,
    {
        "revise": "generate",    # Loop back for revision
        "finalize": "finalize",  # Accept and finish
    }
)
qa_builder.add_edge("finalize", END)

qa_graph = qa_builder.compile()

result = qa_graph.invoke({
    "topic": "microservices architecture",
    "content": "",
    "quality_score": "",
    "revision_count": 0,
    "max_revisions": 3,
    "trace": [],
})

print(f"  Topic:     {result['topic']}")
print(f"  Content:   {result['content'][:200]}")
print(f"  Quality:   {result['quality_score']}")
print(f"  Revisions: {result['revision_count']}")
print(f"  Trace:")
for step in result["trace"]:
    print(f"    -> {step}")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 创建一个"语言检测 + 翻译"图：
# - classify_language 节点：用 LLM 判断输入是中文还是英文
# - translate_to_english 节点：如果是中文，翻译成英文
# - translate_to_chinese 节点：如果是英文，翻译成中文
# - 条件边根据语言分类结果路由

# TODO 2: 创建一个"代码审查"图，带重试循环：
# - generate_code 节点：生成代码
# - review_code 节点：用 LLM 审查代码质量
# - 条件边：如果审查通过则结束，否则重新生成
# - 最多重试 3 次

# TODO 3: 思考题 — 如果条件路由函数返回了一个不在映射表中的值，
# 会发生什么？如何防御这种情况？
# 提示：总是在路由函数中加一个 fallback 分支
