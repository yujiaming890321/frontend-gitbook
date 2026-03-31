"""
Day 1: Graph / Node / Edge 概念 -- 创建最简单的 StateGraph
LangGraph 是构建 AI Agent 的状态图框架，把 Agent 的执行流程建模为一张"有向图"

前端类比：
- StateGraph ~ XState 状态机 / React useReducer
- Node ~ Express 中间件函数 / Redux reducer（接收 state，返回新 state）
- Edge ~ React Router 路由规则（从 A 页面跳到 B 页面）
- compile() ~ webpack build（把配置编译成可执行的应用）
- END ~ 路由终点 / return 语句
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

# ============================================================
# 1. 什么是 Graph？为什么需要它？
# ============================================================

# 传统 LLM 调用是线性的：
#   prompt -> LLM -> response
#
# 但真实的 Agent 需要：
#   1. 判断是否需要调用工具
#   2. 根据结果决定下一步
#   3. 循环执行直到完成
#
# 这就是"图"的用武之地：
#
#   [start] --> [think] --> [decide] --> [act] --> [think] (循环)
#                              |
#                              +--> [END] (完成)
#
# 前端类比：
# - 线性调用 = 简单的 fetch().then().then()
# - Graph = React Router + 状态机，根据条件决定下一步

print("=" * 60)
print("1. 理解 Graph 的基本概念")
print("=" * 60)

# LangGraph 的三个核心概念：
# 1. State — 在节点间传递的数据（类似 Redux store）
# 2. Node  — 处理 state 的函数（类似 reducer）
# 3. Edge  — 连接节点的路径（类似路由规则）

print("""
Graph 结构：

  ┌─────────┐     ┌─────────┐     ┌─────────┐
  │  Node A │────>│  Node B │────>│  Node C │──> END
  └─────────┘     └─────────┘     └─────────┘
       │                               │
       │          State 数据            │
       └───────── 在节点间流动 ─────────┘

前端类比：
  [LoginPage] --> [DashboardPage] --> [SettingsPage]
       │              │                    │
       └──── Redux Store 在页面间共享 ─────┘
""")


# ============================================================
# 2. 定义 State — 用 TypedDict
# ============================================================

# State 就是在所有节点间共享的数据结构
# 前端类比：Redux 的 store shape / React Context 的 value type

print("\n" + "=" * 60)
print("2. 定义 State (TypedDict)")
print("=" * 60)

# The simplest state: just a message string
class SimpleState(TypedDict):
    """The state that flows between nodes in our graph.
    Similar to defining a Redux store's state shape in TypeScript:
    interface SimpleState { message: string; }
    """
    message: str


print("""
TypedDict 定义了 State 的结构：

  class SimpleState(TypedDict):
      message: str

等价于 TypeScript：
  interface SimpleState {
    message: string;
  }
""")


# ============================================================
# 3. 定义 Node — 普通 Python 函数
# ============================================================

# Node 是一个接收 state、返回 state 更新的函数
# 前端类比：Redux reducer —— (state, action) => newState
# 区别：LangGraph node 只需要返回要更新的字段，不需要返回完整 state

print("\n" + "=" * 60)
print("3. 定义 Node 函数")
print("=" * 60)


# Node function: receives current state, returns state updates
def greeting_node(state: SimpleState) -> dict:
    """Add a greeting prefix to the message.

    Like a Redux reducer:
    - receives current state
    - returns only the fields to update (not the full state)
    """
    original = state["message"]
    return {"message": f"Hello! You said: {original}"}


# Another node function
def uppercase_node(state: SimpleState) -> dict:
    """Convert the message to uppercase.

    Like a middleware that transforms data before passing it on.
    """
    return {"message": state["message"].upper()}


# A third node function
def add_timestamp_node(state: SimpleState) -> dict:
    """Append a timestamp to the message.

    Demonstrates that nodes are just regular Python functions.
    """
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"message": f"{state['message']} [processed at {now}]"}


print("""
Node 函数签名：

  def my_node(state: MyState) -> dict:
      # 读取当前 state
      current_value = state["message"]
      # 返回要更新的字段（不需要返回完整 state）
      return {"message": new_value}

前端类比 (Redux reducer)：
  const reducer = (state, action) => ({
    ...state,           // LangGraph 自动处理这一步
    message: newValue   // 你只需要返回要更新的部分
  });
""")


# ============================================================
# 4. 构建 Graph — 组装节点和边
# ============================================================

print("\n" + "=" * 60)
print("4. 构建最简单的 Graph")
print("=" * 60)

# Step 1: Create a StateGraph with our state type
# Similar to: const store = createStore(reducer, initialState)
graph_builder = StateGraph(SimpleState)

# Step 2: Add nodes
# Similar to: app.use('/greeting', greetingMiddleware)
graph_builder.add_node("greeting", greeting_node)
graph_builder.add_node("uppercase", uppercase_node)
graph_builder.add_node("timestamp", add_timestamp_node)

# Step 3: Add edges (define the flow)
# Similar to: React Router routes — from page A to page B
graph_builder.set_entry_point("greeting")          # Start here (like "/" route)
graph_builder.add_edge("greeting", "uppercase")    # greeting -> uppercase
graph_builder.add_edge("uppercase", "timestamp")   # uppercase -> timestamp
graph_builder.add_edge("timestamp", END)           # timestamp -> END (finish)

# Step 4: Compile the graph (make it executable)
# Similar to: webpack build / app.listen()
simple_graph = graph_builder.compile()

print("""
Graph 构建步骤：

  1. graph = StateGraph(MyState)        # 创建图
  2. graph.add_node("name", func)       # 添加节点
  3. graph.set_entry_point("name")      # 设置入口
  4. graph.add_edge("a", "b")           # 连接节点
  5. graph.add_edge("b", END)           # 连接到终点
  6. app = graph.compile()              # 编译
  7. result = app.invoke(initial_state)  # 执行

前端类比：
  1. const router = createBrowserRouter()
  2. router.addRoute('/greeting', GreetingPage)
  3. router.setDefault('/greeting')
  4. router.addRedirect('/greeting', '/uppercase')
  5. // END = 最终渲染
  6. const app = router.build()
  7. app.navigate({message: "hi"})
""")


# ============================================================
# 5. 执行 Graph
# ============================================================

print("\n" + "=" * 60)
print("5. 执行 Graph")
print("=" * 60)

# invoke() runs the graph from start to END
# Similar to: store.dispatch(action) or app.navigate(url)
result = simple_graph.invoke({"message": "LangGraph is awesome"})
print(f"Input:  'LangGraph is awesome'")
print(f"Output: '{result['message']}'")
print()

# The state flows through: greeting -> uppercase -> timestamp
# Each node transforms the message

# Try another input
result2 = simple_graph.invoke({"message": "hello world"})
print(f"Input:  'hello world'")
print(f"Output: '{result2['message']}'")


# ============================================================
# 6. 理解 State 的更新机制
# ============================================================

print("\n" + "=" * 60)
print("6. State 更新机制 — Reducer 模式")
print("=" * 60)

# By default, returning a field from a node REPLACES its value
# But we can use Annotated + operator to ACCUMULATE values
# This is like Redux reducers with different merge strategies

import operator


class AccumulatorState(TypedDict):
    """State with an accumulating list.
    The Annotated type tells LangGraph HOW to merge updates.
    operator.add for lists means: extend the list (not replace).
    """
    messages: Annotated[list[str], operator.add]   # Append, don't replace
    count: int                                      # Replace (default)


# Node that adds a message to the list
def step_one(state: AccumulatorState) -> dict:
    """Add first processing message"""
    return {
        "messages": ["Step 1: initialized"],
        "count": 1,
    }


def step_two(state: AccumulatorState) -> dict:
    """Add second processing message"""
    return {
        "messages": ["Step 2: processed"],
        "count": 2,
    }


def step_three(state: AccumulatorState) -> dict:
    """Add final processing message"""
    return {
        "messages": [f"Step 3: completed (total steps: {state['count']})"],
        "count": 3,
    }


# Build the accumulator graph
acc_builder = StateGraph(AccumulatorState)
acc_builder.add_node("step1", step_one)
acc_builder.add_node("step2", step_two)
acc_builder.add_node("step3", step_three)
acc_builder.set_entry_point("step1")
acc_builder.add_edge("step1", "step2")
acc_builder.add_edge("step2", "step3")
acc_builder.add_edge("step3", END)
acc_graph = acc_builder.compile()

result = acc_graph.invoke({"messages": [], "count": 0})
print("Accumulator result:")
print(f"  messages: {result['messages']}")
print(f"  count: {result['count']}")

print("""
State 更新策略：

  1. 默认 (Replace):
     count: int
     节点返回 {"count": 5} -> count 变成 5

  2. 累加 (Accumulate with operator.add):
     messages: Annotated[list[str], operator.add]
     节点返回 {"messages": ["new"]} -> 追加到列表末尾

前端类比：
  - Replace = React setState({count: 5})
  - Accumulate = React setState(prev => ({items: [...prev.items, newItem]}))
""")


# ============================================================
# 7. Graph 的可视化 — 理解执行流程
# ============================================================

print("\n" + "=" * 60)
print("7. 理解执行流程")
print("=" * 60)

# We can trace the execution by printing state at each node
class DebugState(TypedDict):
    """State with trace logging for debugging"""
    value: int
    trace: Annotated[list[str], operator.add]


def double_node(state: DebugState) -> dict:
    """Double the value and log the operation"""
    old = state["value"]
    new = old * 2
    return {
        "value": new,
        "trace": [f"double: {old} -> {new}"],
    }


def add_ten_node(state: DebugState) -> dict:
    """Add 10 to the value and log the operation"""
    old = state["value"]
    new = old + 10
    return {
        "value": new,
        "trace": [f"add_ten: {old} -> {new}"],
    }


def square_node(state: DebugState) -> dict:
    """Square the value and log the operation"""
    old = state["value"]
    new = old ** 2
    return {
        "value": new,
        "trace": [f"square: {old} -> {new}"],
    }


# Build a debug graph: double -> add_ten -> square
debug_builder = StateGraph(DebugState)
debug_builder.add_node("double", double_node)
debug_builder.add_node("add_ten", add_ten_node)
debug_builder.add_node("square", square_node)
debug_builder.set_entry_point("double")
debug_builder.add_edge("double", "add_ten")
debug_builder.add_edge("add_ten", "square")
debug_builder.add_edge("square", END)
debug_graph = debug_builder.compile()

# Run with initial value 3: double(3)=6 -> add_ten(6)=16 -> square(16)=256
result = debug_graph.invoke({"value": 3, "trace": []})
print(f"Start value: 3")
print(f"Final value: {result['value']}")
print(f"Execution trace:")
for step in result["trace"]:
    print(f"  -> {step}")


# ============================================================
# 8. 错误处理
# ============================================================

print("\n" + "=" * 60)
print("8. 错误处理")
print("=" * 60)


class ErrorDemoState(TypedDict):
    """State for error handling demo"""
    input_text: str
    result: str
    error: str


def validate_input(state: ErrorDemoState) -> dict:
    """Validate input and set error if invalid"""
    text = state["input_text"]
    if not text or not text.strip():
        return {"error": "Input cannot be empty", "result": ""}
    return {"error": "", "result": ""}


def process_input(state: ErrorDemoState) -> dict:
    """Process the input only if no error occurred"""
    if state.get("error"):
        return {"result": f"SKIPPED due to error: {state['error']}"}
    return {"result": f"Processed: {state['input_text'].upper()}"}


error_builder = StateGraph(ErrorDemoState)
error_builder.add_node("validate", validate_input)
error_builder.add_node("process", process_input)
error_builder.set_entry_point("validate")
error_builder.add_edge("validate", "process")
error_builder.add_edge("process", END)
error_graph = error_builder.compile()

# Test with valid input
r1 = error_graph.invoke({"input_text": "hello", "result": "", "error": ""})
print(f"Valid input -> result: '{r1['result']}'")

# Test with empty input
r2 = error_graph.invoke({"input_text": "", "result": "", "error": ""})
print(f"Empty input -> result: '{r2['result']}'")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 创建一个 State，包含 name (str) 和 steps (Annotated list)
# 然后创建 3 个节点：
#   - clean_name: 去掉 name 的首尾空格
#   - capitalize_name: 把 name 首字母大写
#   - format_name: 把 name 变成 "Mr./Ms. {name}"
# 用 Edge 连接它们，运行后打印最终 name 和执行步骤

# class NameState(TypedDict):
#     name: str
#     steps: Annotated[list[str], operator.add]
#
# def clean_name(state: NameState) -> dict:
#     ???
#
# 参考答案：
# class NameState(TypedDict):
#     name: str
#     steps: Annotated[list[str], operator.add]
#
# def clean_name(state: NameState) -> dict:
#     return {"name": state["name"].strip(), "steps": ["cleaned"]}
#
# def capitalize_name(state: NameState) -> dict:
#     return {"name": state["name"].title(), "steps": ["capitalized"]}
#
# def format_name(state: NameState) -> dict:
#     return {"name": f"Mr./Ms. {state['name']}", "steps": ["formatted"]}

# TODO 2: 创建一个计数器图：
# - State: {"count": int, "history": Annotated[list[int], operator.add]}
# - 3 个节点各自将 count + 1，并记录当前值到 history
# - 运行后 count 应该是 3，history 应该是 [1, 2, 3]

# TODO 3: 思考题 — 如果把 TODO 2 的 history 改成 Annotated[list[int], operator.add]
# 但是节点返回的不是列表而是单个 int，会发生什么？
# 提示：operator.add 对 list 是 extend，所以返回值必须是 list
