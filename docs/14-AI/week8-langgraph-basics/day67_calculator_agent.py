"""
Day 6-7: 综合练习 -- Calculator Agent，自动判断是否需要计算

这个项目综合运用本周所有知识点：
- Day 1: Graph / Node / Edge 基础（StateGraph 构建）
- Day 2: LLM 集成（Ollama 调用）
- Day 3: 条件路由（判断是否需要计算）
- Day 4: 工具节点（计算器工具）
- Day 5: 状态管理（TypedDict + Annotated）

Agent 工作流程：
  用户输入 -> 意图判断 -> 需要计算? -> 调用计算器 -> 生成回答
                           |
                           不需要 -> 直接回答

用法:
  python day67_calculator_agent.py                    # 运行所有示例
  python day67_calculator_agent.py interactive        # 交互模式
  python day67_calculator_agent.py "What is 15 * 23?" # 单个问题
"""

import sys
import re
import math
import json
import operator
from typing import TypedDict, Annotated, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama


# ============================================================
# Day 1 & Day 5: State 定义 — 综合运用 TypedDict 和 Annotated
# ============================================================

# Custom reducer: merge dict without overwriting existing keys' old values
def merge_dict(current: dict, update: dict) -> dict:
    """Merge update into current dict. Like: {...current, ...update}"""
    return {**current, **update}


# Custom reducer: keep count by incrementing
def increment(current: int, update: int) -> int:
    """Increment counter by update value"""
    return current + update


class CalculatorState(TypedDict):
    """
    Comprehensive state for the Calculator Agent.

    Design decisions (Day 5 best practices):
    - current turn data: replace strategy
    - history: append strategy (Annotated + operator.add)
    - metrics: increment strategy (custom reducer)
    - context: merge strategy (custom reducer)
    """
    # Current turn — replace
    user_input: str
    intent: str                   # "calculate", "chat", "help"
    expression: str               # Extracted math expression
    calculation_result: str       # Result from calculator
    final_response: str           # Response shown to user

    # History — append (Day 5 knowledge)
    messages: Annotated[list[dict], operator.add]
    tool_calls: Annotated[list[dict], operator.add]
    trace: Annotated[list[str], operator.add]

    # Metrics — increment
    total_queries: Annotated[int, increment]
    total_calculations: Annotated[int, increment]

    # Context — merge
    session: Annotated[dict, merge_dict]


# ============================================================
# Day 4: 计算器工具集
# ============================================================

class Calculator:
    """A calculator tool with various math operations.

    Front-end analogy: like a utility library (lodash for math).
    Each method is a 'tool' the agent can call.
    """

    @staticmethod
    def evaluate(expression: str) -> dict:
        """Safely evaluate a math expression.

        Supports: +, -, *, /, **, (), sqrt(), sin(), cos(), pi, e
        Returns dict with result and explanation.
        """
        # Clean the expression
        expr = expression.strip()

        # Replace common math symbols and functions
        replacements = {
            "^": "**",
            "sqrt": "math.sqrt",
            "sin": "math.sin",
            "cos": "math.cos",
            "tan": "math.tan",
            "log": "math.log",
            "pi": str(math.pi),
            "PI": str(math.pi),
            "e": str(math.e) if expr.strip() == "e" else "e",
        }

        processed = expr
        for old, new in replacements.items():
            # Only replace standalone math constants, not parts of words
            if old in ("pi", "PI", "e"):
                processed = re.sub(rf'\b{old}\b', new, processed)
            else:
                processed = processed.replace(old, new)

        # Validate: only allow safe characters
        safe_pattern = re.compile(r'^[\d\s\+\-\*\/\.\(\)math\.sqrtsincotaglope]+$')
        if not safe_pattern.match(processed):
            return {
                "success": False,
                "result": None,
                "error": f"Unsafe expression: {expr}",
                "expression": expr,
            }

        try:
            # Evaluate with math module available
            result = eval(processed, {"__builtins__": {}, "math": math}, {})
            # Format result
            if isinstance(result, float):
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 6)

            return {
                "success": True,
                "result": result,
                "error": None,
                "expression": expr,
                "processed": processed,
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "expression": expr,
            }

    @staticmethod
    def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
        """Convert between common units.

        Supported: km/miles, kg/lbs, C/F, cm/inches
        """
        conversions = {
            ("km", "miles"): lambda v: v * 0.621371,
            ("miles", "km"): lambda v: v * 1.60934,
            ("kg", "lbs"): lambda v: v * 2.20462,
            ("lbs", "kg"): lambda v: v * 0.453592,
            ("c", "f"): lambda v: v * 9/5 + 32,
            ("f", "c"): lambda v: (v - 32) * 5/9,
            ("cm", "inches"): lambda v: v * 0.393701,
            ("inches", "cm"): lambda v: v * 2.54,
        }

        key = (from_unit.lower(), to_unit.lower())
        if key in conversions:
            result = round(conversions[key](value), 4)
            return {"success": True, "result": result, "from": f"{value} {from_unit}", "to": f"{result} {to_unit}"}
        else:
            return {"success": False, "error": f"Unknown conversion: {from_unit} -> {to_unit}"}

    @staticmethod
    def percentage(value: float, total: float) -> dict:
        """Calculate percentage"""
        if total == 0:
            return {"success": False, "error": "Cannot divide by zero"}
        pct = round((value / total) * 100, 2)
        return {"success": True, "result": pct, "description": f"{value} is {pct}% of {total}"}


# Initialize calculator and LLM
calc = Calculator()
llm = Ollama(model="qwen2.5:7b", temperature=0)


# ============================================================
# Day 2 & Day 3: Node 函数定义 — LLM 集成 + 条件路由
# ============================================================

def receive_input_node(state: CalculatorState) -> dict:
    """Receive user input and add to message history.
    Day 1 concept: basic node that updates state.
    """
    user_msg = {
        "role": "user",
        "content": state["user_input"],
        "timestamp": datetime.now().isoformat(),
    }
    return {
        "messages": [user_msg],
        "total_queries": 1,
        "trace": [f"received input: '{state['user_input'][:50]}'"],
    }


def classify_intent_node(state: CalculatorState) -> dict:
    """Use LLM to classify whether user needs calculation.

    Day 3 concept: LLM-driven conditional routing.
    The LLM's classification determines which branch to take.
    """
    prompt = f"""Classify this user message into exactly ONE category.
Reply with ONLY the category name, nothing else.

Categories:
- calculate: user wants to do math, compute something, convert units, or calculate percentage
- help: user wants to know what this agent can do
- chat: anything else (general questions, greetings, etc.)

User message: "{state['user_input']}"

Category:"""

    intent = llm.invoke(prompt).strip().lower()

    # Normalize intent
    valid_intents = ["calculate", "help", "chat"]
    if intent not in valid_intents:
        for valid in valid_intents:
            if valid in intent:
                intent = valid
                break
        else:
            intent = "chat"

    return {
        "intent": intent,
        "trace": [f"classified intent: {intent}"],
        "session": {"last_intent": intent},
    }


def extract_expression_node(state: CalculatorState) -> dict:
    """Use LLM to extract the math expression from natural language.

    This is a key Agent capability: translating natural language
    into structured tool input.
    """
    prompt = f"""Extract the math expression from this user message.
If it's a unit conversion, format as: value from_unit to to_unit (e.g., "100 km to miles")
If it's a percentage, format as: value percentage of total (e.g., "25 percentage of 200")
Otherwise, return just the math expression (e.g., "15 * 23 + 7")

Reply with ONLY the expression, nothing else.

User message: "{state['user_input']}"

Expression:"""

    expression = llm.invoke(prompt).strip()

    return {
        "expression": expression,
        "trace": [f"extracted expression: '{expression}'"],
    }


def execute_calculation_node(state: CalculatorState) -> dict:
    """Execute the calculation using the Calculator tool.

    Day 4 concept: tool node that calls a registered tool.
    """
    expression = state["expression"]
    timestamp = datetime.now().isoformat()

    # Detect calculation type and route to appropriate method
    if "to" in expression.lower() and any(
        unit in expression.lower()
        for unit in ["km", "miles", "kg", "lbs", "c", "f", "cm", "inches"]
    ):
        # Unit conversion
        parts = re.split(r'\s+to\s+', expression, flags=re.IGNORECASE)
        if len(parts) == 2:
            # Parse "100 km" -> (100, "km")
            value_match = re.match(r'([\d.]+)\s*(\w+)', parts[0].strip())
            if value_match:
                value = float(value_match.group(1))
                from_unit = value_match.group(2)
                to_unit = parts[1].strip()
                result = calc.convert_units(value, from_unit, to_unit)
            else:
                result = {"success": False, "error": f"Cannot parse: {expression}"}
        else:
            result = {"success": False, "error": f"Cannot parse conversion: {expression}"}

    elif "percentage" in expression.lower() or "percent" in expression.lower():
        # Percentage calculation
        match = re.search(r'([\d.]+)\s*(?:percentage|percent)\s*(?:of)\s*([\d.]+)', expression, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            total = float(match.group(2))
            result = calc.percentage(value, total)
        else:
            result = {"success": False, "error": f"Cannot parse percentage: {expression}"}

    else:
        # Regular math expression
        result = calc.evaluate(expression)

    # Record tool call
    tool_call = {
        "tool": "calculator",
        "input": expression,
        "output": result,
        "timestamp": timestamp,
    }

    calc_result = ""
    if result["success"]:
        calc_result = str(result["result"])
    else:
        calc_result = f"Error: {result.get('error', 'Unknown error')}"

    return {
        "calculation_result": calc_result,
        "tool_calls": [tool_call],
        "total_calculations": 1,
        "trace": [f"calculation: {expression} = {calc_result}"],
    }


def generate_calc_response_node(state: CalculatorState) -> dict:
    """Generate a natural language response with the calculation result.

    Day 2 concept: LLM integration for response synthesis.
    """
    prompt = f"""The user asked: "{state['user_input']}"
The calculation expression was: {state['expression']}
The result is: {state['calculation_result']}

Write a clear, helpful response that presents this result naturally.
Keep it brief (1-2 sentences). Include the result prominently.

Response:"""

    response = llm.invoke(prompt).strip()

    assistant_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "final_response": response,
        "messages": [assistant_msg],
        "trace": ["generated calculation response"],
    }


def generate_chat_response_node(state: CalculatorState) -> dict:
    """Generate a conversational response for non-calculation queries.

    Uses message history for context (Day 5 state management).
    """
    # Build context from recent messages
    recent = state["messages"][-6:]  # Last 6 messages
    context = "\n".join(
        f"{m['role']}: {m['content']}" for m in recent
    )

    prompt = f"""You are a Calculator Agent. You can help with math, unit conversions,
and percentages. For non-math questions, answer briefly and remind the user
about your calculation capabilities.

Conversation context:
{context}

Current question: "{state['user_input']}"

Respond briefly (1-2 sentences):"""

    response = llm.invoke(prompt).strip()

    assistant_msg = {
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "final_response": response,
        "messages": [assistant_msg],
        "trace": ["generated chat response"],
    }


def generate_help_response_node(state: CalculatorState) -> dict:
    """Generate a help message explaining agent capabilities"""
    help_text = """I'm a Calculator Agent! Here's what I can do:

1. Math calculations: "What is 15 * 23 + 7?" or "Calculate sqrt(144)"
2. Unit conversions: "Convert 100 km to miles" or "What is 30 C in F?"
3. Percentages: "What percentage is 25 of 200?"
4. Complex expressions: "Calculate (3.14 * 5^2) / 2"

Supported operations: +, -, *, /, ^ (power), sqrt(), sin(), cos(), tan(), log()
Supported units: km/miles, kg/lbs, C/F, cm/inches

Just ask me any math question!"""

    assistant_msg = {
        "role": "assistant",
        "content": help_text,
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "final_response": help_text,
        "messages": [assistant_msg],
        "trace": ["generated help response"],
    }


# ============================================================
# Day 3: 条件路由函数
# ============================================================

def route_by_intent(state: CalculatorState) -> str:
    """Route to the appropriate handler based on intent.

    Day 3 concept: conditional edges determine execution flow.
    This is the 'decision point' in the graph.

    Graph structure:
                        ┌──> extract -> calculate -> respond_calc ──> END
    receive -> classify ├──> respond_chat ──────────────────────────> END
                        └──> respond_help ──────────────────────────> END
    """
    intent = state["intent"]
    if intent == "calculate":
        return "extract_expression"
    elif intent == "help":
        return "respond_help"
    else:
        return "respond_chat"


# ============================================================
# Day 1: Graph 构建 — 把所有节点组装成完整的 Agent
# ============================================================

def build_calculator_agent():
    """Build the complete Calculator Agent graph.

    This assembles all the pieces:
    - Nodes (Day 1): individual processing functions
    - LLM calls (Day 2): Ollama integration
    - Conditional edges (Day 3): intent-based routing
    - Tool nodes (Day 4): calculator tools
    - State management (Day 5): TypedDict + Annotated

    Returns a compiled graph ready to use.
    """
    builder = StateGraph(CalculatorState)

    # Add all nodes
    builder.add_node("receive", receive_input_node)
    builder.add_node("classify", classify_intent_node)
    builder.add_node("extract_expression", extract_expression_node)
    builder.add_node("calculate", execute_calculation_node)
    builder.add_node("respond_calc", generate_calc_response_node)
    builder.add_node("respond_chat", generate_chat_response_node)
    builder.add_node("respond_help", generate_help_response_node)

    # Set entry point
    builder.set_entry_point("receive")

    # Linear edges
    builder.add_edge("receive", "classify")
    builder.add_edge("extract_expression", "calculate")
    builder.add_edge("calculate", "respond_calc")

    # Conditional edge from classify (Day 3)
    builder.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "extract_expression": "extract_expression",
            "respond_chat": "respond_chat",
            "respond_help": "respond_help",
        }
    )

    # All response nodes lead to END
    builder.add_edge("respond_calc", END)
    builder.add_edge("respond_chat", END)
    builder.add_edge("respond_help", END)

    return builder.compile()


# Build the agent
agent = build_calculator_agent()


# ============================================================
# Helper: create initial state
# ============================================================

def create_initial_state() -> CalculatorState:
    """Create a fresh initial state for the agent"""
    return {
        "user_input": "",
        "intent": "",
        "expression": "",
        "calculation_result": "",
        "final_response": "",
        "messages": [],
        "tool_calls": [],
        "trace": [],
        "total_queries": 0,
        "total_calculations": 0,
        "session": {"start_time": datetime.now().isoformat()},
    }


def ask(state: CalculatorState, question: str) -> CalculatorState:
    """Send a question to the agent and return updated state.

    Carries forward accumulated state (messages, metrics, etc.)
    for multi-turn conversation.
    """
    result = agent.invoke({
        **state,
        "user_input": question,
        # Reset per-turn fields
        "intent": "",
        "expression": "",
        "calculation_result": "",
        "final_response": "",
    })
    return result


# ============================================================
# 运行示例
# ============================================================

def run_examples():
    """Run example queries to demonstrate the agent"""
    print("=" * 60)
    print("Calculator Agent -- Examples")
    print("=" * 60)

    state = create_initial_state()

    examples = [
        # Math calculations
        "What is 15 * 23 + 7?",
        "Calculate the square root of 144",
        "What is 2 to the power of 10?",
        # Unit conversions
        "Convert 100 km to miles",
        "What is 37 C in Fahrenheit?",
        # Percentage
        "What percentage is 45 of 200?",
        # Chat (no calculation needed)
        "Hello! What can you do?",
        "What is the capital of France?",
        # Help
        "help",
    ]

    for question in examples:
        print(f"\n{'─' * 50}")
        state = ask(state, question)
        print(f"  Q: {question}")
        print(f"  Intent: {state['intent']}")
        if state['expression']:
            print(f"  Expression: {state['expression']}")
        if state['calculation_result']:
            print(f"  Calc result: {state['calculation_result']}")
        print(f"  A: {state['final_response'][:200]}")

    # Print session summary
    print(f"\n{'=' * 60}")
    print("Session Summary")
    print(f"{'=' * 60}")
    print(f"  Total queries:       {state['total_queries']}")
    print(f"  Total calculations:  {state['total_calculations']}")
    print(f"  Message history:     {len(state['messages'])} messages")
    print(f"  Tool calls:          {len(state['tool_calls'])} calls")
    print(f"  Session info:        {json.dumps(state['session'], indent=2, default=str)}")

    print(f"\nExecution trace:")
    for step in state["trace"]:
        print(f"  -> {step}")


def run_interactive():
    """Run the agent in interactive mode"""
    print("=" * 60)
    print("Calculator Agent -- Interactive Mode")
    print("Type 'quit' to exit, 'history' to see conversation")
    print("=" * 60)

    state = create_initial_state()

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input.lower() == "history":
            print("\nConversation history:")
            for msg in state["messages"]:
                role = msg["role"]
                content = msg["content"][:100]
                print(f"  [{role}] {content}")
            print(f"\n  Stats: {state['total_queries']} queries, "
                  f"{state['total_calculations']} calculations")
            continue

        if user_input.lower() == "trace":
            print("\nExecution trace:")
            for step in state["trace"][-10:]:  # Last 10 trace entries
                print(f"  -> {step}")
            continue

        state = ask(state, user_input)
        print(f"Agent: {state['final_response']}")


def run_single(question: str):
    """Run a single query"""
    state = create_initial_state()
    state = ask(state, question)

    print(f"Q: {question}")
    print(f"Intent: {state['intent']}")
    if state['expression']:
        print(f"Expression: {state['expression']}")
    if state['calculation_result']:
        print(f"Calculation: {state['calculation_result']}")
    print(f"A: {state['final_response']}")
    print(f"Trace: {state['trace']}")


# ============================================================
# CLI 入口
# ============================================================

def print_usage():
    """Print usage information"""
    print("""
Calculator Agent -- LangGraph Week 8 综合练习

用法:
  python day67_calculator_agent.py                     运行示例
  python day67_calculator_agent.py interactive         交互模式
  python day67_calculator_agent.py "What is 15*23?"    单个问题
  python day67_calculator_agent.py test                运行计算器测试

示例问题:
  "What is 15 * 23 + 7?"
  "Calculate sqrt(144)"
  "Convert 100 km to miles"
  "What is 30 C in Fahrenheit?"
  "What percentage is 25 of 200?"
""")


def run_calculator_tests():
    """Test the Calculator class directly (no LLM needed)"""
    print("=" * 60)
    print("Calculator Unit Tests")
    print("=" * 60)

    # Test basic math
    test_cases = [
        ("2 + 3", 5),
        ("10 * 5", 50),
        ("100 / 4", 25),
        ("2 ** 10", 1024),
        ("(3 + 4) * 2", 14),
        ("sqrt(144)", 12),
        ("sqrt(2)", 1.414214),
    ]

    print("\nMath expressions:")
    passed = 0
    for expr, expected in test_cases:
        result = calc.evaluate(expr)
        actual = result["result"]
        status = "PASS" if actual == expected else "FAIL"
        if status == "PASS":
            passed += 1
        print(f"  {status}: {expr} = {actual} (expected {expected})")

    # Test unit conversion
    print("\nUnit conversions:")
    conv_tests = [
        (100, "km", "miles", 62.1371),
        (0, "c", "f", 32.0),
        (100, "c", "f", 212.0),
    ]

    for value, from_u, to_u, expected in conv_tests:
        result = calc.convert_units(value, from_u, to_u)
        actual = result["result"]
        status = "PASS" if actual == expected else "FAIL"
        if status == "PASS":
            passed += 1
        print(f"  {status}: {value} {from_u} -> {to_u} = {actual} (expected {expected})")

    # Test percentage
    print("\nPercentage:")
    pct_result = calc.percentage(25, 200)
    status = "PASS" if pct_result["result"] == 12.5 else "FAIL"
    if status == "PASS":
        passed += 1
    print(f"  {status}: 25 of 200 = {pct_result['result']}% (expected 12.5%)")

    total = len(test_cases) + len(conv_tests) + 1
    print(f"\nResults: {passed}/{total} tests passed")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        run_examples()
    elif sys.argv[1] == "interactive":
        run_interactive()
    elif sys.argv[1] == "test":
        run_calculator_tests()
    elif sys.argv[1] in ("-h", "--help"):
        print_usage()
    else:
        # Treat the argument as a question
        question = " ".join(sys.argv[1:])
        run_single(question)


if __name__ == "__main__":
    main()


# ============================================================
# 扩展练习（可选）
# ============================================================

# TODO 1: 添加"历史回溯"功能：
# 让 Agent 能回答 "What was my last calculation?" 这样的问题
# 提示：从 state["tool_calls"] 中提取最近的计算记录

# TODO 2: 添加"连续计算"功能：
# 让 Agent 支持 "Now multiply that by 2" 这样的追问
# 提示：在 state 中保存上一次的计算结果，构建 prompt 时传入

# TODO 3: 添加更多工具：
# - 统计工具：平均值、中位数、标准差
# - 几何工具：面积、周长计算
# - 金融工具：复利计算、贷款月供
# 使用 Day 4 的 ToolRegistry 模式注册这些工具

# TODO 4: 添加错误恢复循环 (Day 3 循环路由)：
# 如果计算失败，让 Agent 重新提取表达式再试一次
# 最多重试 2 次
