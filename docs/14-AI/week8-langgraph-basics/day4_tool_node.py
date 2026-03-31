"""
Day 4: 工具节点 -- 让 Agent 调用自定义工具
Agent 的核心能力：不只是生成文字，还能调用工具（函数）来完成任务

前端类比：
- Tool Node ~ API Route Handler / Serverless Function
- Agent 决定调用哪个工具 ~ React Router 根据 URL 选择哪个 handler
- 工具注册 ~ Express router.use() 注册路由
- 工具调用 ~ fetch() 调用后端 API

Agent = LLM（大脑）+ Tools（手脚）
LLM 负责思考，Tools 负责执行
"""

from typing import TypedDict, Annotated
import operator
import math
import json
import re
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama

# Initialize LLM
llm = Ollama(model="qwen2.5:7b", temperature=0)


# ============================================================
# 1. 什么是 Tool? — 先定义一些工具函数
# ============================================================

print("=" * 60)
print("1. 定义工具函数")
print("=" * 60)

# Tools are just regular Python functions that do specific things
# The LLM decides WHEN to call them and with WHAT arguments
# Front-end analogy: tools are like API endpoints the frontend can call


def tool_get_weather(city: str) -> str:
    """Get current weather for a city.
    In production, this would call a real weather API.
    Like: fetch(`/api/weather?city=${city}`)
    """
    # Simulated weather data
    weather_data = {
        "beijing": "Sunny, 25C",
        "shanghai": "Cloudy, 22C",
        "tokyo": "Rainy, 18C",
        "new york": "Partly cloudy, 20C",
        "london": "Foggy, 15C",
    }
    city_lower = city.lower().strip()
    return weather_data.get(city_lower, f"Weather data not available for {city}")


def tool_calculate(expression: str) -> str:
    """Evaluate a math expression safely.
    Like a calculator API endpoint.
    """
    try:
        # Only allow safe math operations
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return f"Error: invalid characters in expression '{expression}'"
        result = eval(expression)  # Safe because we validated chars
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def tool_get_time(timezone: str = "UTC") -> str:
    """Get current time.
    Like: new Date().toLocaleString()
    """
    now = datetime.now()
    return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} (local)"


def tool_string_length(text: str) -> str:
    """Count the length of a string.
    Like: text.length in JavaScript
    """
    return f"The text has {len(text)} characters"


# Register tools in a dictionary for easy lookup
# Front-end analogy: like Express routes or API endpoint registry
TOOLS = {
    "get_weather": {
        "function": tool_get_weather,
        "description": "Get weather for a city. Input: city name.",
    },
    "calculate": {
        "function": tool_calculate,
        "description": "Calculate a math expression. Input: math expression like '2+3*4'.",
    },
    "get_time": {
        "function": tool_get_time,
        "description": "Get the current time. Input: not needed.",
    },
    "string_length": {
        "function": tool_string_length,
        "description": "Count the length of a text. Input: the text to count.",
    },
}

print("Registered tools:")
for name, info in TOOLS.items():
    print(f"  - {name}: {info['description']}")
print()


# ============================================================
# 2. 手动工具调用 — 理解基本流程
# ============================================================

print("\n" + "=" * 60)
print("2. 手动工具调用 -- 理解基本流程")
print("=" * 60)

# Before automating with LLM, let's understand the manual process:
# 1. User asks a question
# 2. We decide which tool to use
# 3. We call the tool
# 4. We format the result


class ManualToolState(TypedDict):
    """State for manual tool calling demo"""
    user_input: str
    tool_name: str
    tool_input: str
    tool_output: str
    final_response: str


def select_tool_node(state: ManualToolState) -> dict:
    """Manually select a tool based on keywords.
    In the next section, we'll let the LLM do this automatically.
    """
    user_input = state["user_input"].lower()

    if "weather" in user_input:
        # Extract city name (simple heuristic)
        words = state["user_input"].split()
        city = words[-1] if words else "beijing"  # Last word as city
        return {"tool_name": "get_weather", "tool_input": city}
    elif any(c in user_input for c in "+-*/"):
        # Extract math expression
        expr = re.findall(r'[\d\+\-\*/\.\(\) ]+', user_input)
        return {"tool_name": "calculate", "tool_input": expr[0].strip() if expr else "0"}
    elif "time" in user_input:
        return {"tool_name": "get_time", "tool_input": ""}
    else:
        return {"tool_name": "none", "tool_input": ""}


def execute_tool_node(state: ManualToolState) -> dict:
    """Execute the selected tool.
    Like calling the appropriate API endpoint.
    """
    tool_name = state["tool_name"]
    tool_input = state["tool_input"]

    if tool_name in TOOLS:
        tool_fn = TOOLS[tool_name]["function"]
        result = tool_fn(tool_input)
        return {"tool_output": result}
    else:
        return {"tool_output": "No tool needed for this query"}


def format_response_node(state: ManualToolState) -> dict:
    """Format the tool output into a user-friendly response"""
    return {
        "final_response": f"Tool: {state['tool_name']}\n"
                         f"Input: {state['tool_input']}\n"
                         f"Result: {state['tool_output']}"
    }


# Build manual tool graph
manual_builder = StateGraph(ManualToolState)
manual_builder.add_node("select_tool", select_tool_node)
manual_builder.add_node("execute_tool", execute_tool_node)
manual_builder.add_node("format_response", format_response_node)
manual_builder.set_entry_point("select_tool")
manual_builder.add_edge("select_tool", "execute_tool")
manual_builder.add_edge("execute_tool", "format_response")
manual_builder.add_edge("format_response", END)
manual_graph = manual_builder.compile()

# Test manual tool calling
for query in ["What's the weather in Tokyo", "Calculate 15 * 23 + 7", "What time is it"]:
    result = manual_graph.invoke({
        "user_input": query,
        "tool_name": "",
        "tool_input": "",
        "tool_output": "",
        "final_response": "",
    })
    print(f"  Query: {query}")
    print(f"  {result['final_response']}")
    print()


# ============================================================
# 3. LLM 驱动的工具调用 — 让 AI 决定用哪个工具
# ============================================================

print("\n" + "=" * 60)
print("3. LLM 驱动的工具调用")
print("=" * 60)

# Now the exciting part: let the LLM decide which tool to use!
# This is what makes an "Agent" — LLM + Tools + Decision-making


class AgentToolState(TypedDict):
    """State for LLM-driven tool calling"""
    user_input: str
    llm_decision: str       # Raw LLM output (tool selection)
    tool_name: str
    tool_input: str
    tool_output: str
    final_response: str
    trace: Annotated[list[str], operator.add]


# Build the tool description string for the prompt
def get_tool_descriptions() -> str:
    """Build a description of available tools for the LLM prompt"""
    descriptions = []
    for name, info in TOOLS.items():
        descriptions.append(f"- {name}: {info['description']}")
    return "\n".join(descriptions)


def llm_decide_tool_node(state: AgentToolState) -> dict:
    """Ask the LLM which tool to use.

    This is the 'brain' of the agent:
    The LLM reads the user input and available tools,
    then decides which tool to call and with what input.
    """
    prompt = f"""You are a helpful assistant with access to tools.
Given the user's message, decide which tool to use.

Available tools:
{get_tool_descriptions()}
- none: No tool needed, just answer directly.

Reply in this EXACT JSON format (no other text):
{{"tool": "tool_name", "input": "tool_input_value"}}

User message: "{state['user_input']}"

JSON:"""

    decision = llm.invoke(prompt).strip()

    # Parse the LLM's JSON response
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'\{[^}]+\}', decision)
        if json_match:
            parsed = json.loads(json_match.group())
            tool_name = parsed.get("tool", "none")
            tool_input = parsed.get("input", "")
        else:
            tool_name = "none"
            tool_input = ""
    except (json.JSONDecodeError, AttributeError):
        tool_name = "none"
        tool_input = ""

    return {
        "llm_decision": decision,
        "tool_name": tool_name,
        "tool_input": str(tool_input),
        "trace": [f"LLM decided: tool={tool_name}, input={tool_input}"],
    }


def agent_execute_tool_node(state: AgentToolState) -> dict:
    """Execute the tool chosen by the LLM"""
    tool_name = state["tool_name"]
    tool_input = state["tool_input"]

    if tool_name in TOOLS:
        tool_fn = TOOLS[tool_name]["function"]
        result = tool_fn(tool_input)
        return {
            "tool_output": result,
            "trace": [f"executed {tool_name}('{tool_input}') -> {result}"],
        }
    else:
        return {
            "tool_output": "",
            "trace": ["no tool executed"],
        }


def route_after_tool_decision(state: AgentToolState) -> str:
    """Route: if a tool was selected, execute it; otherwise, respond directly"""
    if state["tool_name"] in TOOLS:
        return "execute_tool"
    else:
        return "direct_response"


def direct_response_node(state: AgentToolState) -> dict:
    """Respond directly without using a tool"""
    prompt = f"Answer this briefly: {state['user_input']}"
    response = llm.invoke(prompt).strip()
    return {
        "final_response": response,
        "trace": ["generated direct response (no tool needed)"],
    }


def synthesize_response_node(state: AgentToolState) -> dict:
    """Generate a natural language response using the tool output.

    This is the 'answer synthesis' step:
    Take the raw tool output and make it conversational.
    """
    prompt = f"""The user asked: "{state['user_input']}"
You used the tool "{state['tool_name']}" and got this result: {state['tool_output']}

Write a natural, helpful response based on this result. Keep it brief (1-2 sentences)."""

    response = llm.invoke(prompt).strip()
    return {
        "final_response": response,
        "trace": ["synthesized final response from tool output"],
    }


# Build the LLM-driven tool agent graph
agent_builder = StateGraph(AgentToolState)
agent_builder.add_node("decide_tool", llm_decide_tool_node)
agent_builder.add_node("execute_tool", agent_execute_tool_node)
agent_builder.add_node("direct_response", direct_response_node)
agent_builder.add_node("synthesize", synthesize_response_node)

agent_builder.set_entry_point("decide_tool")

# Conditional: tool selected -> execute -> synthesize
#              no tool -> direct response
agent_builder.add_conditional_edges(
    "decide_tool",
    route_after_tool_decision,
    {
        "execute_tool": "execute_tool",
        "direct_response": "direct_response",
    }
)
agent_builder.add_edge("execute_tool", "synthesize")
agent_builder.add_edge("synthesize", END)
agent_builder.add_edge("direct_response", END)

agent_graph = agent_builder.compile()

# Test the agent with various queries
test_queries = [
    "What's the weather like in Shanghai?",
    "How much is 123 * 456?",
    "What time is it now?",
    "Tell me a joke",  # No tool needed
]

for query in test_queries:
    result = agent_graph.invoke({
        "user_input": query,
        "llm_decision": "",
        "tool_name": "",
        "tool_input": "",
        "tool_output": "",
        "final_response": "",
        "trace": [],
    })
    print(f"  Q: {query}")
    print(f"  A: {result['final_response'][:200]}")
    print(f"  Trace: {result['trace']}")
    print()


# ============================================================
# 4. 多工具调用 — Agent 循环
# ============================================================

print("\n" + "=" * 60)
print("4. 多工具调用 -- Agent 循环")
print("=" * 60)

# Real agents often need to call MULTIPLE tools to answer one question
# This requires a LOOP: think -> act -> observe -> think -> act -> ...
# This is the ReAct (Reasoning + Acting) pattern
#
# Front-end analogy:
# Like a complex form wizard that makes multiple API calls
# based on previous responses before showing final result


class MultiToolState(TypedDict):
    """State for multi-tool agent loop"""
    user_input: str
    scratchpad: Annotated[list[str], operator.add]  # Agent's working memory
    tool_name: str
    tool_input: str
    tool_output: str
    final_answer: str
    step_count: int
    max_steps: int
    is_done: bool
    trace: Annotated[list[str], operator.add]


def think_node(state: MultiToolState) -> dict:
    """Agent thinks about what to do next.
    Uses scratchpad (working memory) to track progress.

    This is the 'reasoning' part of the ReAct loop.
    """
    scratchpad_text = "\n".join(state["scratchpad"]) if state["scratchpad"] else "No previous actions."

    prompt = f"""You are a helpful assistant with tools. Think step by step.

Available tools:
{get_tool_descriptions()}

User question: "{state['user_input']}"

Your previous actions:
{scratchpad_text}

Based on the above, decide your next action.
If you have enough information to answer, reply with:
{{"tool": "final_answer", "input": "your complete answer here"}}

If you need to use a tool, reply with:
{{"tool": "tool_name", "input": "tool_input_value"}}

Reply with ONLY the JSON, nothing else:"""

    decision = llm.invoke(prompt).strip()

    try:
        json_match = re.search(r'\{[^}]+\}', decision)
        if json_match:
            parsed = json.loads(json_match.group())
            tool_name = parsed.get("tool", "final_answer")
            tool_input = str(parsed.get("input", ""))
        else:
            tool_name = "final_answer"
            tool_input = "I couldn't process your request."
    except (json.JSONDecodeError, AttributeError):
        tool_name = "final_answer"
        tool_input = "I couldn't process your request."

    is_done = tool_name == "final_answer"

    return {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "is_done": is_done,
        "step_count": state["step_count"] + 1,
        "final_answer": tool_input if is_done else state.get("final_answer", ""),
        "trace": [f"step {state['step_count'] + 1}: decided {'DONE' if is_done else tool_name}"],
    }


def act_node(state: MultiToolState) -> dict:
    """Execute the tool and record the observation in scratchpad"""
    tool_name = state["tool_name"]
    tool_input = state["tool_input"]

    if tool_name in TOOLS:
        tool_fn = TOOLS[tool_name]["function"]
        result = tool_fn(tool_input)
    else:
        result = f"Unknown tool: {tool_name}"

    # Record in scratchpad for next think step
    observation = f"Action: {tool_name}({tool_input}) -> Result: {result}"
    return {
        "tool_output": result,
        "scratchpad": [observation],
        "trace": [f"executed: {observation[:100]}"],
    }


def route_after_think(state: MultiToolState) -> str:
    """Route: if done, finish; if max steps reached, finish; else continue loop"""
    if state["is_done"]:
        return "finish"
    elif state["step_count"] >= state["max_steps"]:
        return "finish"
    else:
        return "act"


def finish_node(state: MultiToolState) -> dict:
    """Finalize the agent's response"""
    if not state["final_answer"]:
        return {
            "final_answer": "I wasn't able to determine the answer.",
            "trace": ["finished without definitive answer"],
        }
    return {"trace": [f"finished with answer after {state['step_count']} steps"]}


# Build the multi-tool agent graph (ReAct loop)
multi_builder = StateGraph(MultiToolState)
multi_builder.add_node("think", think_node)
multi_builder.add_node("act", act_node)
multi_builder.add_node("finish", finish_node)

multi_builder.set_entry_point("think")

# Think -> (act -> think) loop or finish
multi_builder.add_conditional_edges(
    "think",
    route_after_think,
    {
        "act": "act",
        "finish": "finish",
    }
)
multi_builder.add_edge("act", "think")  # After acting, think again
multi_builder.add_edge("finish", END)

multi_graph = multi_builder.compile()

# Test: a question that might need multiple tool calls
result = multi_graph.invoke({
    "user_input": "What's the weather in Beijing and what is 25 * 1.8 + 32?",
    "scratchpad": [],
    "tool_name": "",
    "tool_input": "",
    "tool_output": "",
    "final_answer": "",
    "step_count": 0,
    "max_steps": 5,
    "is_done": False,
    "trace": [],
})

print(f"  Question: {result['user_input']}")
print(f"  Answer:   {result['final_answer'][:300]}")
print(f"  Steps:    {result['step_count']}")
print(f"  Trace:")
for step in result["trace"]:
    print(f"    -> {step}")


# ============================================================
# 5. 自定义工具模式 — 工具注册表
# ============================================================

print("\n" + "=" * 60)
print("5. 自定义工具注册模式")
print("=" * 60)

# A reusable pattern for registering tools
# Front-end analogy: like Express Router or plugin registration


class ToolRegistry:
    """Registry for tools that an agent can use.

    Front-end analogy:
    Like an Express router that registers route handlers:
      router.get('/weather', weatherHandler)
      router.get('/calc', calcHandler)
    """

    def __init__(self):
        self._tools: dict = {}

    def register(self, name: str, description: str):
        """Decorator to register a tool function.

        Usage:
            @registry.register("my_tool", "Does something cool")
            def my_tool(input: str) -> str:
                return "result"
        """
        def decorator(func):
            self._tools[name] = {
                "function": func,
                "description": description,
            }
            return func
        return decorator

    def get_tool(self, name: str):
        """Get a tool by name"""
        return self._tools.get(name)

    def execute(self, name: str, input_str: str) -> str:
        """Execute a tool by name with given input"""
        tool = self._tools.get(name)
        if tool:
            return tool["function"](input_str)
        return f"Tool '{name}' not found"

    def get_descriptions(self) -> str:
        """Get formatted descriptions of all tools for LLM prompts"""
        lines = []
        for name, info in self._tools.items():
            lines.append(f"- {name}: {info['description']}")
        return "\n".join(lines)

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())


# Create a registry and register tools using decorators
registry = ToolRegistry()


@registry.register("word_count", "Count words in a text. Input: the text.")
def word_count_tool(text: str) -> str:
    """Count words in text"""
    count = len(text.split())
    return f"Word count: {count}"


@registry.register("reverse", "Reverse a string. Input: the text to reverse.")
def reverse_tool(text: str) -> str:
    """Reverse a string"""
    return f"Reversed: {text[::-1]}"


@registry.register("uppercase", "Convert text to uppercase. Input: the text.")
def uppercase_tool(text: str) -> str:
    """Convert to uppercase"""
    return text.upper()


print(f"Registered tools: {registry.tool_names}")
print(f"Descriptions:\n{registry.get_descriptions()}")
print()

# Test the registry
for tool_name in registry.tool_names:
    result = registry.execute(tool_name, "hello world")
    print(f"  {tool_name}('hello world') -> {result}")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 添加一个新工具到 TOOLS 字典:
# - "translate": 接收 "en:你好" 格式的输入，调用 LLM 翻译
# 然后用 agent_graph 测试翻译功能

# TODO 2: 使用 ToolRegistry 模式，创建一个"文本处理"工具集：
# - lowercase: 转小写
# - title_case: 首字母大写
# - remove_spaces: 去掉空格
# 创建一个 agent 图来使用这些工具

# TODO 3: 思考题 — 如果 LLM 返回的 JSON 格式不正确（比如缺少引号），
# 你的代码会怎么处理？如何让解析更健壮？
# 提示：可以用正则表达式提取关键信息，不完全依赖 JSON 解析
