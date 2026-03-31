"""
Day 2: Input -> LLM 处理 -> Output 完整图
把真实的 LLM 调用集成到 LangGraph 中，构建一个完整的 AI 处理管道

前端类比：
- 这就像一个 Express 中间件链：
  request -> parseBody -> validateInput -> callAPI -> formatResponse -> send
- 每个中间件（节点）处理一部分，state 就是 req/res 对象
"""

from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama

# ============================================================
# 1. 连接 Ollama LLM
# ============================================================

print("=" * 60)
print("1. 连接 Ollama LLM")
print("=" * 60)

# Initialize the LLM — make sure Ollama is running: `ollama serve`
llm = Ollama(model="qwen2.5:7b", temperature=0.7)

# Quick test to verify connection
test_response = llm.invoke("Say 'hello' in one word")
print(f"LLM connection test: {test_response[:50]}...")
print()


# ============================================================
# 2. 最简单的 LLM Graph: Input -> LLM -> Output
# ============================================================

print("=" * 60)
print("2. 最简单的 LLM Graph")
print("=" * 60)


class BasicLLMState(TypedDict):
    """State for basic LLM graph.
    Like a simple API request/response:
    - user_input: the request body
    - llm_output: the response body
    """
    user_input: str
    llm_output: str


# Node: call the LLM with user input
def call_llm_node(state: BasicLLMState) -> dict:
    """Send user input to LLM and store the response.
    Like an Express route handler that calls an external API.
    """
    response = llm.invoke(state["user_input"])
    return {"llm_output": response}


# Build the simplest possible LLM graph
basic_builder = StateGraph(BasicLLMState)
basic_builder.add_node("call_llm", call_llm_node)
basic_builder.set_entry_point("call_llm")
basic_builder.add_edge("call_llm", END)
basic_graph = basic_builder.compile()

# Run it
result = basic_graph.invoke({
    "user_input": "What is Python? Answer in one sentence.",
    "llm_output": "",
})
print(f"Input: {result['user_input']}")
print(f"Output: {result['llm_output'][:200]}")
print()


# ============================================================
# 3. 三步管道: Preprocess -> LLM -> Postprocess
# ============================================================

print("\n" + "=" * 60)
print("3. 三步管道: Preprocess -> LLM -> Postprocess")
print("=" * 60)

# This is the most common pattern in AI apps:
# 1. Preprocess: clean/format user input
# 2. LLM: generate response
# 3. Postprocess: format/filter output
#
# Front-end analogy:
#   middleware chain in Express:
#   app.use(parseBody)     -> preprocess
#   app.use(callService)   -> LLM call
#   app.use(formatOutput)  -> postprocess


class PipelineState(TypedDict):
    """State for a 3-step LLM pipeline"""
    raw_input: str         # Original user input
    processed_input: str   # Cleaned/formatted input
    llm_response: str      # Raw LLM response
    final_output: str      # Formatted final output
    metadata: dict         # Processing metadata


def preprocess_node(state: PipelineState) -> dict:
    """Clean and format user input before sending to LLM.

    Like Express body-parser middleware:
    - Trim whitespace
    - Add system context
    - Record metadata
    """
    raw = state["raw_input"].strip()

    # Build a structured prompt with context
    processed = f"""You are a helpful AI assistant for frontend developers.
Answer the following question concisely (2-3 sentences max):

Question: {raw}"""

    return {
        "processed_input": processed,
        "metadata": {
            "original_length": len(raw),
            "processed_length": len(processed),
        },
    }


def llm_node(state: PipelineState) -> dict:
    """Call the LLM with the processed input.

    The core processing step — like calling an external API service.
    """
    response = llm.invoke(state["processed_input"])
    return {"llm_response": response}


def postprocess_node(state: PipelineState) -> dict:
    """Format the LLM response for display.

    Like a response formatter middleware:
    - Clean up the response
    - Add metadata
    - Format for the UI
    """
    response = state["llm_response"].strip()
    metadata = state["metadata"]

    # Build a formatted output
    formatted = f"""
--- AI Response ---
{response}

--- Metadata ---
Input length: {metadata.get('original_length', 0)} chars
Prompt length: {metadata.get('processed_length', 0)} chars
Response length: {len(response)} chars
-------------------
""".strip()

    return {"final_output": formatted}


# Build the pipeline graph
pipeline_builder = StateGraph(PipelineState)
pipeline_builder.add_node("preprocess", preprocess_node)
pipeline_builder.add_node("llm", llm_node)
pipeline_builder.add_node("postprocess", postprocess_node)

# Connect: preprocess -> llm -> postprocess -> END
pipeline_builder.set_entry_point("preprocess")
pipeline_builder.add_edge("preprocess", "llm")
pipeline_builder.add_edge("llm", "postprocess")
pipeline_builder.add_edge("postprocess", END)

pipeline_graph = pipeline_builder.compile()

# Run the pipeline
result = pipeline_graph.invoke({
    "raw_input": "  What is React hooks?  ",
    "processed_input": "",
    "llm_response": "",
    "final_output": "",
    "metadata": {},
})
print(result["final_output"])
print()


# ============================================================
# 4. 多轮对话 Graph — 带历史记录
# ============================================================

print("\n" + "=" * 60)
print("4. 多轮对话 Graph -- 带历史记录")
print("=" * 60)

# A chat graph that maintains conversation history
# Front-end analogy: like React state that accumulates chat messages


class ChatState(TypedDict):
    """State for multi-turn chat.
    messages accumulates over time (like a chat log).
    """
    messages: Annotated[list[dict], operator.add]  # Accumulate messages
    current_input: str
    current_response: str


def add_user_message_node(state: ChatState) -> dict:
    """Add the user's message to the conversation history.
    Like dispatching an ADD_MESSAGE action in Redux.
    """
    user_msg = {"role": "user", "content": state["current_input"]}
    return {"messages": [user_msg]}


def generate_response_node(state: ChatState) -> dict:
    """Generate an LLM response based on conversation history.
    Builds a prompt that includes all previous messages for context.
    """
    # Build conversation context from history
    conversation = ""
    for msg in state["messages"]:
        role = msg["role"]
        content = msg["content"]
        conversation += f"{role}: {content}\n"

    prompt = f"""Here is the conversation so far:
{conversation}
Please respond as the assistant. Keep it brief (1-2 sentences)."""

    response = llm.invoke(prompt)
    return {"current_response": response.strip()}


def add_assistant_message_node(state: ChatState) -> dict:
    """Add the assistant's response to the conversation history."""
    assistant_msg = {"role": "assistant", "content": state["current_response"]}
    return {"messages": [assistant_msg]}


# Build the chat graph
chat_builder = StateGraph(ChatState)
chat_builder.add_node("add_user_msg", add_user_message_node)
chat_builder.add_node("generate", generate_response_node)
chat_builder.add_node("add_assistant_msg", add_assistant_message_node)

chat_builder.set_entry_point("add_user_msg")
chat_builder.add_edge("add_user_msg", "generate")
chat_builder.add_edge("generate", "add_assistant_msg")
chat_builder.add_edge("add_assistant_msg", END)

chat_graph = chat_builder.compile()

# Simulate a multi-turn conversation
print("--- Turn 1 ---")
state = chat_graph.invoke({
    "messages": [],
    "current_input": "What is LangGraph?",
    "current_response": "",
})
print(f"User: {state['current_input']}")
print(f"AI: {state['current_response']}")
print(f"History length: {len(state['messages'])} messages")

print("\n--- Turn 2 ---")
# Pass the accumulated state to the next turn
state = chat_graph.invoke({
    "messages": state["messages"],  # Carry forward history
    "current_input": "How is it different from LangChain?",
    "current_response": "",
})
print(f"User: {state['current_input']}")
print(f"AI: {state['current_response']}")
print(f"History length: {len(state['messages'])} messages")

print("\nFull conversation history:")
for i, msg in enumerate(state["messages"]):
    print(f"  [{i}] {msg['role']}: {msg['content'][:80]}...")


# ============================================================
# 5. 带模板的 Prompt 管道
# ============================================================

print("\n" + "=" * 60)
print("5. Prompt 模板管道")
print("=" * 60)

# A reusable pattern: fill a prompt template, then call LLM
# Front-end analogy: like a template engine (Handlebars, EJS)


class TemplateState(TypedDict):
    """State for template-based LLM calls"""
    topic: str
    audience: str          # e.g., "frontend developer", "beginner"
    style: str             # e.g., "concise", "detailed", "funny"
    prompt: str            # Filled template
    response: str          # LLM response


# Prompt templates (like React component templates)
EXPLAIN_TEMPLATE = """Explain {topic} to a {audience}.
Use a {style} style.
Keep it under 3 sentences."""


def fill_template_node(state: TemplateState) -> dict:
    """Fill the prompt template with state values.
    Like template literal interpolation in JS:
    `Explain ${topic} to a ${audience}`
    """
    prompt = EXPLAIN_TEMPLATE.format(
        topic=state["topic"],
        audience=state["audience"],
        style=state["style"],
    )
    return {"prompt": prompt}


def call_template_llm_node(state: TemplateState) -> dict:
    """Call LLM with the filled template"""
    response = llm.invoke(state["prompt"])
    return {"response": response.strip()}


# Build template graph
tmpl_builder = StateGraph(TemplateState)
tmpl_builder.add_node("fill_template", fill_template_node)
tmpl_builder.add_node("call_llm", call_template_llm_node)
tmpl_builder.set_entry_point("fill_template")
tmpl_builder.add_edge("fill_template", "call_llm")
tmpl_builder.add_edge("call_llm", END)
tmpl_graph = tmpl_builder.compile()

# Example 1: Explain for beginners
result = tmpl_graph.invoke({
    "topic": "React Virtual DOM",
    "audience": "frontend developer",
    "style": "concise",
    "prompt": "",
    "response": "",
})
print(f"Topic: {result['topic']}")
print(f"Style: {result['style']}")
print(f"Response: {result['response'][:300]}")
print()

# Example 2: Explain for beginners with humor
result2 = tmpl_graph.invoke({
    "topic": "async/await in JavaScript",
    "audience": "beginner programmer",
    "style": "funny",
    "prompt": "",
    "response": "",
})
print(f"Topic: {result2['topic']}")
print(f"Style: {result2['style']}")
print(f"Response: {result2['response'][:300]}")


# ============================================================
# 6. 串联多个 LLM 调用
# ============================================================

print("\n" + "=" * 60)
print("6. 串联多个 LLM 调用 (Chain)")
print("=" * 60)

# Sometimes you need multiple LLM calls in sequence
# E.g., generate -> review -> refine
# Front-end analogy: multiple API calls in sequence with data dependency


class ChainState(TypedDict):
    """State for chained LLM calls"""
    topic: str
    draft: str         # First LLM output
    critique: str      # Second LLM output (review)
    final: str         # Third LLM output (refined)
    steps: Annotated[list[str], operator.add]


def draft_node(state: ChainState) -> dict:
    """Generate initial draft about the topic"""
    prompt = f"Write a 2-sentence explanation of {state['topic']} for developers."
    response = llm.invoke(prompt)
    return {
        "draft": response.strip(),
        "steps": ["draft: generated initial explanation"],
    }


def critique_node(state: ChainState) -> dict:
    """Review the draft and suggest improvements"""
    prompt = f"""Review this explanation and suggest ONE improvement in 1 sentence:

"{state['draft']}"

Improvement suggestion:"""
    response = llm.invoke(prompt)
    return {
        "critique": response.strip(),
        "steps": ["critique: reviewed and suggested improvement"],
    }


def refine_node(state: ChainState) -> dict:
    """Refine the draft based on the critique"""
    prompt = f"""Improve this explanation based on the feedback:

Original: "{state['draft']}"
Feedback: "{state['critique']}"

Improved version (2 sentences):"""
    response = llm.invoke(prompt)
    return {
        "final": response.strip(),
        "steps": ["refine: produced final version"],
    }


# Build the chain graph: draft -> critique -> refine
chain_builder = StateGraph(ChainState)
chain_builder.add_node("draft", draft_node)
chain_builder.add_node("critique", critique_node)
chain_builder.add_node("refine", refine_node)
chain_builder.set_entry_point("draft")
chain_builder.add_edge("draft", "critique")
chain_builder.add_edge("critique", "refine")
chain_builder.add_edge("refine", END)
chain_graph = chain_builder.compile()

result = chain_graph.invoke({
    "topic": "WebSocket",
    "draft": "",
    "critique": "",
    "final": "",
    "steps": [],
})

print(f"Topic: {result['topic']}")
print(f"\nDraft:    {result['draft'][:200]}")
print(f"\nCritique: {result['critique'][:200]}")
print(f"\nFinal:    {result['final'][:200]}")
print(f"\nSteps: {result['steps']}")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 创建一个"翻译管道"图：
# State: {text: str, source_lang: str, target_lang: str, translation: str}
# 节点 1: build_prompt — 构建翻译 prompt
# 节点 2: translate — 调用 LLM 翻译
# 测试：把一段中文翻译成英文

# TODO 2: 创建一个"代码解释器"图：
# State: {code: str, language: str, explanation: str, examples: str}
# 节点 1: explain — 让 LLM 解释代码
# 节点 2: generate_examples — 让 LLM 生成使用示例
# 测试：解释一段 JavaScript 代码

# TODO 3: 修改上面的 Chain 图，增加第四步 "summarize"
# 让 LLM 用一句话总结 draft -> critique -> refine 的整个过程
