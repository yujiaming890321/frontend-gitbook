"""
Day 2: Tool Calling — 让 LLM 决定调用哪个工具
核心思想：LLM 不直接回答问题，而是分析需求后选择合适的工具来获取信息
类比前端：LLM 就像一个 API Gateway，根据请求路由到不同的后端服务
"""

import json
import re
from typing import Optional
from dataclasses import dataclass
from langchain_community.llms import Ollama

# Import tools from Day 1
from day1_tool_functions import (
    TOOL_REGISTRY,
    ToolResult,
    execute_tool,
    get_tools_description,
    read_file,
    search_text,
    list_directory,
)


# ============================================================
# 1. Tool Calling 的原理
# ============================================================

"""
Tool Calling 的工作流程：

┌─────────┐     ┌───────────────────┐     ┌──────────┐
│ 用户提问  │ ──→ │ LLM (带工具描述)   │ ──→ │ 输出 JSON │
│          │     │ "你可以用这些工具:" │     │ 工具调用  │
└─────────┘     └───────────────────┘     └──────────┘
                                                │
                                                ▼
                                          ┌──────────┐
                                          │ 解析 JSON │
                                          │ 执行工具   │
                                          │ 返回结果   │
                                          └──────────┘

类比前端：
- 就像 GraphQL：客户端描述需要什么数据，服务端自动选择数据源
- 就像 React Query：声明式数据获取，框架决定如何执行

关键点：
1. LLM 不会真的执行工具，它只输出"我想调用哪个工具"的 JSON
2. 我们的代码解析 JSON，执行工具，把结果返回给 LLM
3. 这就是 Function Calling / Tool Calling 的本质
"""


# ============================================================
# 2. 构造 Tool Calling Prompt
# ============================================================

TOOL_CALLING_PROMPT = """You are an AI assistant with access to tools.
When you need to use a tool, respond with a JSON block in this EXACT format:

```tool_call
{{"tool": "tool_name", "arguments": {{"arg1": "value1", "arg2": "value2"}}}}
```

If you don't need any tool, just respond normally.

{tools_description}

RULES:
1. Only call ONE tool at a time
2. Always use the exact tool names and parameter names listed above
3. If you're unsure which tool to use, use list_directory first to understand the project structure
4. After receiving tool results, provide a clear answer to the user

User question: {question}"""


def build_tool_prompt(question: str) -> str:
    """Build a prompt that instructs the LLM to use tools"""
    return TOOL_CALLING_PROMPT.format(
        tools_description=get_tools_description(),
        question=question,
    )


# ============================================================
# 3. 解析 LLM 的 Tool Call 输出
# ============================================================

@dataclass
class ToolCall:
    """Parsed tool call from LLM output"""
    tool_name: str
    arguments: dict
    raw_text: str  # Original LLM output for debugging


def parse_tool_call(llm_output: str) -> Optional[ToolCall]:
    """
    Parse LLM output to extract tool call JSON.
    The LLM should output a JSON block wrapped in ```tool_call``` markers.
    We also handle common LLM quirks like extra whitespace, missing markers, etc.
    """
    # Strategy 1: Look for ```tool_call ... ``` block
    pattern = r"```tool_call\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, llm_output, re.DOTALL)

    if not match:
        # Strategy 2: Look for any JSON with "tool" and "arguments" keys
        pattern2 = r'\{[^{}]*"tool"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}[^{}]*\}'
        match = re.search(pattern2, llm_output, re.DOTALL)

    if not match:
        # Strategy 3: Look for JSON code block
        pattern3 = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        match = re.search(pattern3, llm_output, re.DOTALL)

    if not match:
        return None

    json_str = match.group(1) if match.lastindex else match.group(0)
    json_str = json_str.strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # Try to fix common JSON issues
        json_str = json_str.replace("'", '"')
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return None

    if "tool" not in data:
        return None

    return ToolCall(
        tool_name=data["tool"],
        arguments=data.get("arguments", {}),
        raw_text=llm_output,
    )


# ============================================================
# 4. Tool Calling 执行器
# ============================================================

class ToolCaller:
    """
    Orchestrates the tool calling process.
    Similar to an API Gateway that routes requests to the right service.
    """

    def __init__(self, model_name: str = "qwen2.5:7b"):
        self.llm = Ollama(model=model_name)
        self.call_history: list[dict] = []

    def ask_with_tools(self, question: str) -> str:
        """
        Send a question to the LLM, let it decide which tool to use,
        execute the tool, and return the final answer.
        """
        # Step 1: Build prompt with tool descriptions
        prompt = build_tool_prompt(question)
        print(f"\n{'='*50}")
        print(f"Question: {question}")
        print(f"{'='*50}")

        # Step 2: Get LLM's response
        print("\n[Step 1] Asking LLM to choose a tool...")
        try:
            llm_response = self.llm.invoke(prompt)
        except Exception as e:
            return f"[LLM Error: {e}]"

        print(f"[LLM Response]\n{llm_response[:300]}...")

        # Step 3: Parse tool call
        tool_call = parse_tool_call(llm_response)

        if tool_call is None:
            # LLM decided to answer directly without tools
            print("\n[No tool call detected - LLM answered directly]")
            self.call_history.append({
                "question": question,
                "tool_used": None,
                "answer": llm_response,
            })
            return llm_response

        print(f"\n[Step 2] Tool call detected: {tool_call.tool_name}")
        print(f"  Arguments: {json.dumps(tool_call.arguments, ensure_ascii=False)}")

        # Step 4: Execute the tool
        print(f"\n[Step 3] Executing tool: {tool_call.tool_name}...")
        tool_result = execute_tool(tool_call.tool_name, **tool_call.arguments)
        print(f"  Result: success={tool_result.success}")

        # Step 5: Send tool result back to LLM for final answer
        print("\n[Step 4] Sending tool result to LLM for final answer...")
        followup_prompt = f"""You previously asked to use the tool "{tool_call.tool_name}" with arguments {json.dumps(tool_call.arguments)}.

Here is the tool's result:
---
{tool_result.data[:2000]}
---

Now please answer the user's original question based on this information.

Original question: {question}

Provide a clear, helpful answer in Chinese."""

        try:
            final_answer = self.llm.invoke(followup_prompt)
        except Exception as e:
            final_answer = f"[LLM Error on followup: {e}]\n\nTool result was:\n{tool_result.data}"

        # Record call history
        self.call_history.append({
            "question": question,
            "tool_used": tool_call.tool_name,
            "tool_args": tool_call.arguments,
            "tool_result_success": tool_result.success,
            "answer": final_answer,
        })

        return final_answer

    def get_history(self) -> list[dict]:
        """Return the call history for debugging"""
        return self.call_history


# ============================================================
# 5. 不用 LLM 的模拟 Tool Caller（用于测试）
# ============================================================

class MockToolCaller:
    """
    A mock tool caller that uses keyword matching instead of LLM.
    Useful for testing tool logic without starting Ollama.
    """

    def __init__(self):
        self.call_history: list[dict] = []

    def _select_tool(self, question: str) -> Optional[ToolCall]:
        """Select tool based on keywords in the question"""
        question_lower = question.lower()

        # Keyword-based routing (similar to a simple intent classifier)
        if any(kw in question_lower for kw in ["read", "file", "content", "show", "读取", "文件", "查看"]):
            # Try to extract file path from question
            path_match = re.search(r'["\']([^"\']+\.\w+)["\']', question)
            if path_match:
                return ToolCall(
                    tool_name="read_file",
                    arguments={"file_path": path_match.group(1)},
                    raw_text=question,
                )

        if any(kw in question_lower for kw in ["search", "find", "grep", "搜索", "查找"]):
            pattern_match = re.search(r'["\']([^"\']+)["\']', question)
            return ToolCall(
                tool_name="search_text",
                arguments={
                    "directory": ".",
                    "pattern": pattern_match.group(1) if pattern_match else "TODO",
                },
                raw_text=question,
            )

        if any(kw in question_lower for kw in ["list", "directory", "structure", "目录", "结构"]):
            return ToolCall(
                tool_name="list_directory",
                arguments={"directory": "."},
                raw_text=question,
            )

        return None

    def ask_with_tools(self, question: str) -> str:
        """Mock version: use keyword matching to select tools"""
        print(f"\n{'='*50}")
        print(f"[Mock] Question: {question}")
        print(f"{'='*50}")

        tool_call = self._select_tool(question)

        if tool_call is None:
            return "I don't know which tool to use for this question."

        print(f"[Mock] Selected tool: {tool_call.tool_name}")
        print(f"[Mock] Arguments: {tool_call.arguments}")

        result = execute_tool(tool_call.tool_name, **tool_call.arguments)
        print(f"[Mock] Result: success={result.success}")

        self.call_history.append({
            "question": question,
            "tool_used": tool_call.tool_name,
            "result": str(result),
        })

        return str(result)


# ============================================================
# 6. 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 2: Tool Calling 演示")
    print("=" * 60)

    # ---- Part A: Parse tool call test ----
    print("\n--- Part A: 解析 Tool Call ---")

    test_outputs = [
        # Format 1: proper tool_call block
        """I need to read the file. Let me use the read_file tool.

```tool_call
{"tool": "read_file", "arguments": {"file_path": "README.md"}}
```""",
        # Format 2: JSON in generic code block
        """```json
{"tool": "search_text", "arguments": {"directory": ".", "pattern": "import"}}
```""",
        # Format 3: no tool call
        "The answer to your question is 42. No tools needed.",
    ]

    for i, output in enumerate(test_outputs, 1):
        parsed = parse_tool_call(output)
        if parsed:
            print(f"  Test {i}: tool={parsed.tool_name}, args={parsed.arguments}")
        else:
            print(f"  Test {i}: No tool call detected")

    # ---- Part B: Mock Tool Caller ----
    print("\n--- Part B: Mock Tool Caller ---")
    mock_caller = MockToolCaller()

    questions = [
        '帮我读取 "day1_tool_functions.py" 文件的内容',
        '搜索 "ToolResult" 在哪里定义的',
        "列出当前目录结构",
        "今天天气怎么样？",
    ]

    for q in questions:
        answer = mock_caller.ask_with_tools(q)
        print(f"  Answer preview: {str(answer)[:100]}...\n")

    # ---- Part C: Real LLM Tool Caller (requires Ollama) ----
    print("\n--- Part C: LLM Tool Caller (requires Ollama) ---")
    try:
        caller = ToolCaller()
        answer = caller.ask_with_tools("列出当前目录下的文件结构")
        print(f"\nFinal answer:\n{answer[:500]}")
    except Exception as e:
        print(f"[Ollama not available: {e}]")
        print("Use MockToolCaller for testing without Ollama.")


    # ============================================================
    # 练习题
    # ============================================================

    print("\n" + "=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 改进 parse_tool_call，支持解析多个工具调用
    # 比如 LLM 输出了两个 tool_call 块

    # TODO 2: 给 ToolCaller 添加工具调用次数统计
    # 统计每个工具被调用了多少次

    # TODO 3: 实现一个 "smart router"
    # 根据问题类型自动选择最合适的工具
    # 比如：文件相关 → read_file，搜索相关 → search_text
    # 不用 LLM，用简单的关键词匹配或正则
