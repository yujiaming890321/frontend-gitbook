"""
Day 5: 状态管理 -- State 如何在节点间传递，TypedDict 状态深入
掌握 LangGraph 的状态机制，这是构建复杂 Agent 的基础

前端类比：
- State 管理 ~ Redux Store / React Context
- TypedDict ~ TypeScript interface
- Annotated reducer ~ Redux reducer function
- State channel ~ Redux slice / Zustand store slice
- checkpoint ~ Redux DevTools 时间旅行 / localStorage 持久化
"""

from typing import TypedDict, Annotated, Any, Optional
import operator
import json
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama

# Initialize LLM
llm = Ollama(model="qwen2.5:7b", temperature=0.3)


# ============================================================
# 1. State 的三种更新策略
# ============================================================

print("=" * 60)
print("1. State 的三种更新策略")
print("=" * 60)

# Strategy 1: REPLACE (default) — like React setState with a value
# Strategy 2: APPEND (operator.add on list) — like Redux array push
# Strategy 3: CUSTOM reducer — like a custom Redux reducer

print("""
三种更新策略：

1. Replace（替换）— 默认行为
   count: int
   return {{"count": 5}}  # count 直接变成 5

2. Append（追加）— 用 Annotated + operator.add
   items: Annotated[list, operator.add]
   return {{"items": ["new"]}}  # 追加到列表末尾

3. Custom Reducer（自定义）— 用 Annotated + 自定义函数
   total: Annotated[int, my_reducer]
   # 由自定义函数决定如何合并

前端类比：
1. Replace = React: setState(5)
2. Append  = Redux: state.items = [...state.items, newItem]
3. Custom  = Redux: customReducer(state, action)
""")


# ============================================================
# 2. Replace 策略 — 最简单的更新方式
# ============================================================

print("\n" + "=" * 60)
print("2. Replace 策略")
print("=" * 60)


class ReplaceState(TypedDict):
    """State where all fields use replace strategy (default).
    Like a simple React component state.
    """
    name: str
    age: int
    active: bool


def set_name(state: ReplaceState) -> dict:
    """Replace the name field.
    Like: setState({name: 'Alice'})
    """
    return {"name": "Alice (updated by set_name)"}


def set_age(state: ReplaceState) -> dict:
    """Replace the age field.
    Only returns the fields to update — other fields remain unchanged.
    Like: setState(prev => ({...prev, age: 30}))
    """
    return {"age": 30}


def activate(state: ReplaceState) -> dict:
    """Set active to True"""
    return {"active": True}


replace_builder = StateGraph(ReplaceState)
replace_builder.add_node("set_name", set_name)
replace_builder.add_node("set_age", set_age)
replace_builder.add_node("activate", activate)
replace_builder.set_entry_point("set_name")
replace_builder.add_edge("set_name", "set_age")
replace_builder.add_edge("set_age", "activate")
replace_builder.add_edge("activate", END)
replace_graph = replace_builder.compile()

result = replace_graph.invoke({"name": "Unknown", "age": 0, "active": False})
print(f"  name:   {result['name']}")
print(f"  age:    {result['age']}")
print(f"  active: {result['active']}")


# ============================================================
# 3. Append 策略 — 累积列表数据
# ============================================================

print("\n" + "=" * 60)
print("3. Append 策略 (operator.add)")
print("=" * 60)


class AppendState(TypedDict):
    """State with append strategy for lists.

    Annotated[list[str], operator.add] means:
    When a node returns {"logs": ["new entry"]},
    it APPENDS to the existing list instead of replacing it.

    Front-end analogy:
    Like a Redux reducer that always spreads the previous array:
    case 'ADD_LOG': return [...state.logs, action.payload]
    """
    current_step: str                                    # Replace strategy
    logs: Annotated[list[str], operator.add]             # Append strategy
    errors: Annotated[list[str], operator.add]           # Append strategy


def step_init(state: AppendState) -> dict:
    """Initialize: demonstrates that logs ACCUMULATE"""
    return {
        "current_step": "init",
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Init started"],
    }


def step_process(state: AppendState) -> dict:
    """Process: logs are ADDED to existing list, not replaced"""
    return {
        "current_step": "process",
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Processing data"],
    }


def step_validate(state: AppendState) -> dict:
    """Validate: can append to multiple Annotated lists"""
    return {
        "current_step": "validate",
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Validation complete"],
        "errors": [],  # No errors — empty list appended (no effect)
    }


def step_finish(state: AppendState) -> dict:
    """Finish: final log entry"""
    return {
        "current_step": "done",
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] All done! "
                 f"Total steps processed."],
    }


append_builder = StateGraph(AppendState)
append_builder.add_node("init", step_init)
append_builder.add_node("process", step_process)
append_builder.add_node("validate", step_validate)
append_builder.add_node("finish", step_finish)
append_builder.set_entry_point("init")
append_builder.add_edge("init", "process")
append_builder.add_edge("process", "validate")
append_builder.add_edge("validate", "finish")
append_builder.add_edge("finish", END)
append_graph = append_builder.compile()

result = append_graph.invoke({
    "current_step": "",
    "logs": ["[START] Pipeline began"],  # Initial log entry
    "errors": [],
})

print(f"  Current step: {result['current_step']}")
print(f"  Logs ({len(result['logs'])} entries):")
for log in result["logs"]:
    print(f"    {log}")
print(f"  Errors: {result['errors']}")


# ============================================================
# 4. Custom Reducer — 自定义合并逻辑
# ============================================================

print("\n" + "=" * 60)
print("4. Custom Reducer -- 自定义合并逻辑")
print("=" * 60)


# Custom reducer function: keeps only the last N items
def keep_last_n(existing: list, new: list, n: int = 3) -> list:
    """Custom reducer that keeps only the last N items.

    Like a sliding window or circular buffer.
    Front-end analogy: like a toast notification system
    that only shows the last 3 messages.
    """
    combined = existing + new
    return combined[-n:]


# Wrapper to match the reducer signature (current, update) -> merged
def last_three_reducer(current: list, update: list) -> list:
    """Keep only the last 3 items in the list"""
    return keep_last_n(current, update, n=3)


class SlidingWindowState(TypedDict):
    """State with a sliding window for recent items.
    The custom reducer ensures we never keep more than 3 items.
    """
    step: int
    recent_actions: Annotated[list[str], last_three_reducer]


def action_a(state: SlidingWindowState) -> dict:
    return {
        "step": 1,
        "recent_actions": ["action_a executed"],
    }


def action_b(state: SlidingWindowState) -> dict:
    return {
        "step": 2,
        "recent_actions": ["action_b executed"],
    }


def action_c(state: SlidingWindowState) -> dict:
    return {
        "step": 3,
        "recent_actions": ["action_c executed"],
    }


def action_d(state: SlidingWindowState) -> dict:
    return {
        "step": 4,
        "recent_actions": ["action_d executed"],
    }


def action_e(state: SlidingWindowState) -> dict:
    return {
        "step": 5,
        "recent_actions": ["action_e executed"],
    }


window_builder = StateGraph(SlidingWindowState)
window_builder.add_node("a", action_a)
window_builder.add_node("b", action_b)
window_builder.add_node("c", action_c)
window_builder.add_node("d", action_d)
window_builder.add_node("e", action_e)
window_builder.set_entry_point("a")
window_builder.add_edge("a", "b")
window_builder.add_edge("b", "c")
window_builder.add_edge("c", "d")
window_builder.add_edge("d", "e")
window_builder.add_edge("e", END)
window_graph = window_builder.compile()

result = window_graph.invoke({"step": 0, "recent_actions": []})
print(f"  Final step: {result['step']}")
print(f"  Recent actions (last 3 only): {result['recent_actions']}")
# Even though 5 nodes added items, only the last 3 are kept!


# ============================================================
# 5. 复杂 State 设计 — 聊天 Agent 状态
# ============================================================

print("\n" + "=" * 60)
print("5. 复杂 State 设计 -- 聊天 Agent")
print("=" * 60)

# Real-world agent state is complex. Here's a production-like example.
# Front-end analogy: like a complex Redux store with multiple slices


# Custom reducer: merge dicts (like Object.assign in JS)
def merge_dict_reducer(current: dict, update: dict) -> dict:
    """Merge update dict into current dict.
    Like: {...current, ...update} in JavaScript.
    """
    merged = {**current, **update}
    return merged


class ChatAgentState(TypedDict):
    """Production-like chat agent state.

    Front-end analogy — this is like a Redux store:
    {
      messages: [],        // Chat history (append-only)
      context: {},         // Session context (merge updates)
      current_input: '',   // Current user message (replace)
      response: '',        // Current AI response (replace)
      tool_calls: [],      // Tool call history (append)
      metadata: {},        // Session metadata (merge)
    }
    """
    # Chat history — append only (never lose messages)
    messages: Annotated[list[dict], operator.add]

    # Current turn — replaced each turn
    current_input: str
    response: str

    # Tool call log — append only
    tool_calls: Annotated[list[dict], operator.add]

    # Session context — merged (not replaced)
    context: Annotated[dict, merge_dict_reducer]

    # Processing metadata — merged
    metadata: Annotated[dict, merge_dict_reducer]


def receive_input_node(state: ChatAgentState) -> dict:
    """Receive and preprocess user input.
    Like a React form onSubmit handler.
    """
    user_input = state["current_input"].strip()
    user_msg = {"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()}

    return {
        "messages": [user_msg],
        "context": {"last_user_input": user_input},
        "metadata": {"input_length": len(user_input)},
    }


def check_tools_needed_node(state: ChatAgentState) -> dict:
    """Decide if tools are needed for this query"""
    user_input = state["current_input"].lower()

    # Simple heuristic: check for keywords
    needs_tool = any(kw in user_input for kw in ["calculate", "weather", "time", "date"])

    return {
        "context": {"needs_tool": needs_tool},
        "metadata": {"checked_tools": True},
    }


def generate_response_node(state: ChatAgentState) -> dict:
    """Generate AI response using LLM.

    Uses accumulated messages for context (multi-turn).
    """
    # Build conversation from message history
    conversation = ""
    for msg in state["messages"][-5:]:  # Last 5 messages for context
        conversation += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""Based on this conversation, respond briefly (1-2 sentences):

{conversation}

assistant:"""

    response = llm.invoke(prompt).strip()

    assistant_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "response": response,
        "messages": [assistant_msg],
        "metadata": {
            "response_length": len(response),
            "total_messages": len(state["messages"]) + 1,
        },
    }


def update_context_node(state: ChatAgentState) -> dict:
    """Update session context after responding.
    Like updating Redux store with derived data.
    """
    return {
        "context": {
            "turn_count": state["context"].get("turn_count", 0) + 1,
            "last_response_length": len(state["response"]),
        },
    }


# Build the chat agent graph
chat_builder = StateGraph(ChatAgentState)
chat_builder.add_node("receive", receive_input_node)
chat_builder.add_node("check_tools", check_tools_needed_node)
chat_builder.add_node("generate", generate_response_node)
chat_builder.add_node("update_context", update_context_node)

chat_builder.set_entry_point("receive")
chat_builder.add_edge("receive", "check_tools")
chat_builder.add_edge("check_tools", "generate")
chat_builder.add_edge("generate", "update_context")
chat_builder.add_edge("update_context", END)
chat_graph = chat_builder.compile()

# Simulate a multi-turn conversation
initial_state = {
    "messages": [],
    "current_input": "",
    "response": "",
    "tool_calls": [],
    "context": {},
    "metadata": {},
}

# Turn 1
print("--- Turn 1 ---")
state = chat_graph.invoke({
    **initial_state,
    "current_input": "What is LangGraph?",
})
print(f"  User: What is LangGraph?")
print(f"  AI:   {state['response'][:200]}")
print(f"  Messages: {len(state['messages'])}")
print(f"  Context:  {state['context']}")

# Turn 2 — carry forward accumulated state
print("\n--- Turn 2 ---")
state = chat_graph.invoke({
    **state,  # Carry all accumulated state
    "current_input": "How is it different from LangChain?",
})
print(f"  User: How is it different from LangChain?")
print(f"  AI:   {state['response'][:200]}")
print(f"  Messages: {len(state['messages'])}")
print(f"  Context:  {state['context']}")

# Turn 3
print("\n--- Turn 3 ---")
state = chat_graph.invoke({
    **state,
    "current_input": "Give me a simple example",
})
print(f"  User: Give me a simple example")
print(f"  AI:   {state['response'][:200]}")
print(f"  Messages: {len(state['messages'])}")
print(f"  Context:  {state['context']}")
print(f"  Metadata: {state['metadata']}")


# ============================================================
# 6. State 不可变性和调试
# ============================================================

print("\n" + "=" * 60)
print("6. State 不可变性和调试技巧")
print("=" * 60)

# IMPORTANT: Never mutate state directly!
# Always return a NEW dict from your node functions.
#
# Front-end analogy:
# - Like Redux: never mutate state, always return new state
# - Like React: never do state.value = x, always setState({value: x})

print("""
State 不可变性规则：

  # WRONG — 直接修改 state（会导致 bug！）
  def bad_node(state):
      state["count"] += 1       # 直接修改了 state!
      state["items"].append(x)  # 直接修改了 list!
      return state               # 返回了同一个对象

  # CORRECT — 返回新的更新
  def good_node(state):
      return {{
          "count": state["count"] + 1,    # 返回新值
          "items": [new_item],             # 如果用 Annotated，返回要追加的项
      }}

前端类比：
  # WRONG (React)
  state.count += 1
  setCount(state.count)

  # CORRECT (React)
  setCount(prev => prev + 1)
""")


# Debugging pattern: create a debug node that logs state
class DebugState(TypedDict):
    """State with debug logging"""
    value: str
    debug_log: Annotated[list[str], operator.add]


def debug_snapshot(node_name: str):
    """Factory function that creates a debug wrapper for any node.

    This is like Redux DevTools — logs every state change.
    Front-end analogy: React DevTools component profiler.
    """
    def debug_node(state: DebugState) -> dict:
        snapshot = {k: str(v)[:50] for k, v in state.items() if k != "debug_log"}
        return {
            "debug_log": [f"[{node_name}] state snapshot: {json.dumps(snapshot)}"],
        }
    return debug_node


def transform_value(state: DebugState) -> dict:
    """Transform the value"""
    return {"value": state["value"].upper() + "!"}


# Build debug graph
dbg_builder = StateGraph(DebugState)
dbg_builder.add_node("debug_before", debug_snapshot("before_transform"))
dbg_builder.add_node("transform", transform_value)
dbg_builder.add_node("debug_after", debug_snapshot("after_transform"))

dbg_builder.set_entry_point("debug_before")
dbg_builder.add_edge("debug_before", "transform")
dbg_builder.add_edge("transform", "debug_after")
dbg_builder.add_edge("debug_after", END)
dbg_graph = dbg_builder.compile()

result = dbg_graph.invoke({"value": "hello world", "debug_log": []})
print("Debug log:")
for entry in result["debug_log"]:
    print(f"  {entry}")


# ============================================================
# 7. State 设计最佳实践
# ============================================================

print("\n" + "=" * 60)
print("7. State 设计最佳实践")
print("=" * 60)

print("""
State 设计原则（和 Redux Store 设计原则类似）：

1. 最小化 State
   - 只存储必要的数据
   - 派生数据用节点计算，不存在 state 里
   - 前端类比：Redux 不存 computed values

2. 扁平化结构
   - 避免深层嵌套
   - 前端类比：Redux normalization

3. 分清 Replace 和 Append
   - 临时数据（当前输入、当前响应）→ Replace
   - 历史数据（消息记录、日志）→ Append (Annotated)
   - 前端类比：
     current_page: replace
     notifications: append

4. 类型安全
   - 用 TypedDict 定义所有字段
   - 用 Optional 标记可选字段
   - 前端类比：TypeScript interface

5. 初始化所有字段
   - invoke() 时提供所有字段的初始值
   - 前端类比：Redux initialState

示例 — 好的 State 设计：

  class GoodState(TypedDict):
      # 当前轮次数据 (replace)
      current_input: str
      current_response: str

      # 累积数据 (append)
      messages: Annotated[list[dict], operator.add]
      tool_calls: Annotated[list[dict], operator.add]

      # 配置 (replace, 通常不变)
      model_name: str
      temperature: float

      # 上下文 (merge dict)
      context: Annotated[dict, merge_dict_reducer]
""")


# ============================================================
# 8. 实战：带状态管理的问答 Agent
# ============================================================

print("\n" + "=" * 60)
print("8. 实战：带状态管理的问答 Agent")
print("=" * 60)


# Counter reducer: always increment by the update value
def increment_reducer(current: int, update: int) -> int:
    """Add update to current value"""
    return current + update


class QAAgentState(TypedDict):
    """State for a Q&A agent with proper state management"""
    # Current turn
    question: str
    answer: str
    confidence: str  # "high", "medium", "low"

    # History (append)
    qa_history: Annotated[list[dict], operator.add]

    # Metrics (custom reducer — increment)
    total_questions: Annotated[int, increment_reducer]
    total_tokens_estimate: Annotated[int, increment_reducer]

    # Context (merge)
    session_info: Annotated[dict, merge_dict_reducer]


def analyze_question_node(state: QAAgentState) -> dict:
    """Analyze the question complexity and topic"""
    question = state["question"]

    # Simple heuristic for question complexity
    word_count = len(question.split())
    if word_count > 20:
        complexity = "complex"
    elif word_count > 8:
        complexity = "moderate"
    else:
        complexity = "simple"

    return {
        "session_info": {
            "question_complexity": complexity,
            "question_word_count": word_count,
        },
    }


def answer_question_node(state: QAAgentState) -> dict:
    """Generate answer using LLM"""
    complexity = state["session_info"].get("question_complexity", "simple")

    if complexity == "simple":
        prompt = f"Answer briefly in 1 sentence: {state['question']}"
    else:
        prompt = f"Answer thoroughly in 2-3 sentences: {state['question']}"

    answer = llm.invoke(prompt).strip()

    # Estimate confidence based on answer length and complexity
    if len(answer) > 100:
        confidence = "high"
    elif len(answer) > 30:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "answer": answer,
        "confidence": confidence,
        "total_tokens_estimate": len(answer.split()),  # Rough estimate
    }


def record_qa_node(state: QAAgentState) -> dict:
    """Record this Q&A pair in history"""
    qa_entry = {
        "question": state["question"],
        "answer": state["answer"][:100],
        "confidence": state["confidence"],
        "timestamp": datetime.now().isoformat(),
    }
    return {
        "qa_history": [qa_entry],
        "total_questions": 1,  # Increment by 1 via custom reducer
        "session_info": {
            "last_question_time": datetime.now().isoformat(),
        },
    }


# Build QA agent graph
qa_builder = StateGraph(QAAgentState)
qa_builder.add_node("analyze", analyze_question_node)
qa_builder.add_node("answer", answer_question_node)
qa_builder.add_node("record", record_qa_node)
qa_builder.set_entry_point("analyze")
qa_builder.add_edge("analyze", "answer")
qa_builder.add_edge("answer", "record")
qa_builder.add_edge("record", END)
qa_agent = qa_builder.compile()

# Simulate multiple Q&A turns
base_state = {
    "question": "",
    "answer": "",
    "confidence": "",
    "qa_history": [],
    "total_questions": 0,
    "total_tokens_estimate": 0,
    "session_info": {"session_start": datetime.now().isoformat()},
}

questions = [
    "What is Python?",
    "Explain the difference between a list and a tuple in Python",
    "How does garbage collection work in Python's CPython implementation?",
]

state = base_state
for q in questions:
    state = qa_agent.invoke({**state, "question": q})
    print(f"  Q: {q}")
    print(f"  A: {state['answer'][:150]}...")
    print(f"  Confidence: {state['confidence']}")
    print()

print(f"Session summary:")
print(f"  Total questions: {state['total_questions']}")
print(f"  Total tokens (est.): {state['total_tokens_estimate']}")
print(f"  QA history entries: {len(state['qa_history'])}")
print(f"  Session info: {json.dumps(state['session_info'], indent=2, default=str)}")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 创建一个 State，同时使用三种策略：
# - name: str (replace)
# - tags: Annotated[list[str], operator.add] (append)
# - stats: Annotated[dict, merge_dict_reducer] (merge)
# 创建 3 个节点分别更新它们，验证各策略的行为

# TODO 2: 实现一个 "最大值" 自定义 reducer：
# def max_reducer(current: int, update: int) -> int:
#     return max(current, update)
# 创建一个 State 用这个 reducer 追踪最高分数

# TODO 3: 参考 ChatAgentState 的设计，为一个"代码审查 Agent"设计 State：
# - 需要跟踪：代码、审查评论、修改历史、严重程度统计
# - 想想哪些字段用 replace，哪些用 append，哪些用 merge
