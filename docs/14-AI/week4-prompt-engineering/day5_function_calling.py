"""
Day 5: Function Calling — 让 LLM 调用函数
Function Calling 让 LLM 自己决定调用哪个函数、传什么参数
这是构建 Agent 的基础（Week 8-10 会深入）
"""

from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "qwen2.5:7b"


# ============================================================
# 1. 定义工具 (Tools)
# 告诉 LLM 有哪些函数可以调用
# ============================================================

# Tool definitions follow OpenAI's function calling format
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search documents in the knowledge base by keyword",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword or phrase",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g., 北京, Shanghai)",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a mathematical calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression to evaluate (e.g., '2 + 3 * 4')",
                    },
                },
                "required": ["expression"],
            },
        },
    },
]


# ============================================================
# 2. 实现工具函数
# ============================================================

def search_documents(query: str, top_k: int = 3) -> str:
    """Simulate document search"""
    fake_results = [
        {"title": "RAG 入门指南", "score": 0.95, "snippet": "RAG 是检索增强生成..."},
        {"title": "Agent 实战教程", "score": 0.87, "snippet": "Agent 能自主决策..."},
        {"title": "Prompt 技巧", "score": 0.82, "snippet": "好的 prompt 包含..."},
    ]
    results = [r for r in fake_results if query.lower() in r["title"].lower() or query.lower() in r["snippet"].lower()]
    return json.dumps(results[:top_k], ensure_ascii=False)


def get_weather(city: str) -> str:
    """Simulate weather API call"""
    weather_data = {
        "北京": {"temp": 25, "condition": "晴", "humidity": 40},
        "上海": {"temp": 28, "condition": "多云", "humidity": 65},
        "深圳": {"temp": 32, "condition": "阵雨", "humidity": 80},
    }
    data = weather_data.get(city, {"temp": 20, "condition": "未知", "humidity": 50})
    return json.dumps({"city": city, **data}, ensure_ascii=False)


def calculate(expression: str) -> str:
    """Safely evaluate a math expression"""
    try:
        # Only allow safe math operations
        allowed = set("0123456789+-*/.() ")
        if all(c in allowed for c in expression):
            result = eval(expression)
            return json.dumps({"expression": expression, "result": result})
        return json.dumps({"error": "Invalid expression"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# Map function names to actual functions
TOOL_FUNCTIONS = {
    "search_documents": search_documents,
    "get_weather": get_weather,
    "calculate": calculate,
}


# ============================================================
# 3. Function Calling 流程
# ============================================================

def function_calling_chat(user_input: str) -> str:
    """
    Complete function calling flow:
    1. Send user input + tool definitions to LLM
    2. LLM decides whether to call a function
    3. If yes, execute the function and send result back
    4. LLM generates final response using function result
    """
    messages = [
        {"role": "system", "content": "你是一个有用的助手，可以搜索文档、查天气、做计算。"},
        {"role": "user", "content": user_input},
    ]

    try:
        # Step 1: Send to LLM with tools
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",  # Let LLM decide whether to use tools
        )

        message = response.choices[0].message

        # Step 2: Check if LLM wants to call a function
        if message.tool_calls:
            print(f"  LLM 决定调用工具:")

            # Execute each tool call
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                print(f"    → {func_name}({func_args})")

                # Execute the function
                func = TOOL_FUNCTIONS.get(func_name)
                if func:
                    result = func(**func_args)
                    print(f"    ← 结果: {result[:100]}...")

                    # Add tool call and result to messages
                    messages.append(message.model_dump())
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            # Step 3: Send results back to LLM for final answer
            final_response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
            )
            return final_response.choices[0].message.content
        else:
            # LLM answered directly without tools
            return message.content

    except Exception as e:
        return f"[错误: {e}]"


print("--- Function Calling ---")
test_inputs = [
    "帮我搜一下关于 RAG 的文档",
    "北京今天天气怎么样？",
    "计算 (15 + 27) * 3",
    "你好",  # Should not trigger any tool
]

for user_input in test_inputs:
    print(f"\n用户: {user_input}")
    result = function_calling_chat(user_input)
    print(f"助手: {result[:150]}...")


# ============================================================
# 4. 手动模拟 Function Calling
# 如果模型不支持原生 function calling，用 prompt 模拟
# ============================================================

MANUAL_FC_PROMPT = """你是一个助手，可以使用以下工具：

工具列表:
1. search_documents(query: str, top_k: int = 3) - 搜索文档
2. get_weather(city: str) - 查询天气
3. calculate(expression: str) - 数学计算

使用工具时，按以下 JSON 格式输出：
{"tool": "工具名", "arguments": {"参数名": "参数值"}}

如果不需要工具，直接回答用户问题。
如果需要工具，只输出 JSON，不要其他文字。"""

def manual_function_calling(user_input: str) -> str:
    """Simulate function calling via prompt engineering"""
    messages = [
        {"role": "system", "content": MANUAL_FC_PROMPT},
        {"role": "user", "content": user_input},
    ]

    result = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0,
    ).choices[0].message.content

    # Try to parse as tool call
    try:
        tool_call = json.loads(result)
        if "tool" in tool_call:
            func = TOOL_FUNCTIONS.get(tool_call["tool"])
            if func:
                tool_result = func(**tool_call["arguments"])
                # Send tool result back for final answer
                messages.append({"role": "assistant", "content": result})
                messages.append({"role": "user", "content": f"工具返回结果：{tool_result}\n请根据结果回答用户的问题。"})
                final = client.chat.completions.create(
                    model=MODEL, messages=messages, temperature=0.3,
                ).choices[0].message.content
                return final
    except (json.JSONDecodeError, TypeError, KeyError):
        pass

    return result

print("\n--- 手动 Function Calling ---")
print(manual_function_calling("北京天气如何？"))


# ============================================================
# 5. Function Calling vs Prompt 解析 对比
# ============================================================

"""
                    原生 Function Calling           Prompt 手动解析
可靠性              高（API 保证格式）               中（依赖 prompt 质量）
支持情况            OpenAI, DeepSeek 等              所有模型
实现复杂度          低（SDK 封装好了）                中（需要写解析逻辑）
多工具选择          强（LLM 自动选择）                依赖 prompt 质量
并行调用            支持                             需要自己实现
适用场景            生产环境                         本地模型 / 不支持 FC 的模型
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 添加一个新工具 "translate"
# 接收 text 和 target_language 参数
# 实现翻译功能（可以调用 LLM 翻译）
# 测试：用户说"把 Hello World 翻译成日语"

# TODO 2: 实现并行 Function Calling
# 当 LLM 返回多个 tool_calls 时，用 asyncio.gather 并行执行
# 测试："北京和上海的天气分别怎么样？"

# TODO 3: 实现一个 ToolRegistry 类
# 能用装饰器注册工具函数，自动生成 tool definition
# @tool_registry.register(description="Search documents")
# def search(query: str, top_k: int = 3) -> str: ...
# 提示：用 inspect 模块获取函数签名
