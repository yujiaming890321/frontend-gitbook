"""
Day 6-7: 完整项目整合 — 把所有组件串联成一个完整的 Agent 应用

这个项目综合运用 Week 10 所有知识点：
- Day 1: 多工具管理（文件读写、网页摘要、代码执行、计算器）
- Day 2: 错误处理（重试、回退、错误建议）
- Day 3: 对话记忆（短期、长期、工作记忆）
- Day 4: FastAPI API（HTTP 接口 + SSE streaming）
- Day 5: React UI（思考过程可视化）

用法:
  python day67_full_project.py demo         运行完整演示
  python day67_full_project.py serve        启动 API 服务
  python day67_full_project.py interactive  交互模式
  python day67_full_project.py scaffold     生成项目脚手架
"""

import sys
import json
import time
import re
import os
import uuid
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from langchain_community.llms import Ollama

# Import from all previous days
from day1_multi_tools import (
    ToolResult,
    MULTI_TOOL_REGISTRY,
    execute_tool,
    get_tools_description,
    tool_read_file,
    tool_write_file,
    tool_calculator,
    tool_execute_python,
    tool_web_summary,
)
from day2_error_handling import (
    RobustToolExecutor,
    RetryConfig,
    RetryStrategy,
    ErrorAdvisor,
    FallbackChain,
)
from day3_conversation_memory import (
    MemoryManager,
    MessageRole,
    ShortTermMemory,
    LongTermMemory,
    WorkingMemory,
)
from day4_fastapi_agent import AgentService, SSEFormatter


# ============================================================
# 1. 完整 Agent 的设计
# ============================================================

"""
Complete Agent Architecture:

+-----------------------------------------------------------+
|                     React UI (Day 5)                       |
|  Thinking Process | Chat | Tool Calls | Stream Display     |
+-----------------------------------------------------------+
                            |
+-----------------------------------------------------------+
|                   FastAPI Server (Day 4)                    |
|  POST /chat | GET /stream | POST /tools | GET /sessions    |
+-----------------------------------------------------------+
                            |
+-----------------------------------------------------------+
|                    Full Agent Core                          |
|                                                             |
|  +-------------+  +--------------+  +-----------+          |
|  | ReAct Loop  |  | Multi-Tools  |  | Memory    |          |
|  | Think/Act/  |  | read/write/  |  | Short +   |          |
|  | Observe     |  | web/exec/    |  | Long +    |          |
|  | (Week 9)    |  | calc (Day 1) |  | Working   |          |
|  +-------------+  +--------------+  | (Day 3)   |          |
|                                      +-----------+          |
|  +-------------+  +--------------+                          |
|  | Error       |  | Guard        |                          |
|  | Handling    |  | Max iter     |                          |
|  | Retry +     |  | Timeout      |                          |
|  | Fallback    |  | Loop detect  |                          |
|  | (Day 2)     |  | (Week 9)     |                          |
|  +-------------+  +--------------+                          |
+-----------------------------------------------------------+
                            |
+-----------------------------------------------------------+
|        Ollama (LLM)       |       Chroma (Vector DB)       |
+-----------------------------------------------------------+
"""


# ============================================================
# 2. ReAct 解析器（从 Week 9 简化版）
# ============================================================

TOOL_CALL_INSTRUCTION = (
    'To use a tool, respond with:\n'
    '```tool_call\n'
    '{"tool": "tool_name", "arguments": {"arg1": "value1"}}\n'
    '```\n\n'
    'When done, respond with:\n'
    'Answer: [your final answer]'
)


def parse_agent_output(text: str) -> dict:
    """Parse LLM output for thought, action, and answer"""
    result = {"thought": "", "action": None, "answer": None}

    # Extract thought
    thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|Answer:|```|$)", text, re.DOTALL)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()

    # Extract answer
    answer_match = re.search(r"Answer:\s*(.+?)$", text, re.DOTALL)
    if answer_match:
        result["answer"] = answer_match.group(1).strip()
        return result

    # Extract tool call
    tc_match = re.search(r"```(?:tool_call|json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if tc_match:
        try:
            data = json.loads(tc_match.group(1).strip())
            if "tool" in data:
                result["action"] = {
                    "tool": data["tool"],
                    "arguments": data.get("arguments", {}),
                }
        except json.JSONDecodeError:
            pass

    return result


# ============================================================
# 3. Full Agent
# ============================================================

@dataclass
class AgentConfig:
    """Configuration for the full agent"""
    model_name: str = "qwen2.5:7b"
    max_iterations: int = 8
    max_time_seconds: float = 120.0
    max_same_tool_calls: int = 3
    retry_max: int = 2
    memory_max_messages: int = 30
    memory_storage_dir: str = ".agent_sessions"


class FullAgent:
    """
    A complete agent combining all Week 9 and Week 10 components.
    Supports multi-tool, error handling, memory, and ReAct loop.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

        # Initialize memory
        self.memory = MemoryManager(
            max_short_term=self.config.memory_max_messages,
            storage_dir=self.config.memory_storage_dir,
        )
        self.memory.short_term.set_system_message(
            "You are a helpful AI assistant with access to tools. "
            "Follow the ReAct pattern: Think, then Act (use tool), then Observe. "
            "Answer in Chinese. Be thorough but concise."
        )

        # Initialize tool executor with error handling
        self.tool_executor = RobustToolExecutor(
            retry_config=RetryConfig(
                max_retries=self.config.retry_max,
                strategy=RetryStrategy.EXPONENTIAL,
            ),
        )

        # Initialize LLM
        try:
            self.llm = Ollama(model=self.config.model_name)
            self._llm_available = True
        except Exception:
            self.llm = None
            self._llm_available = False
            print("[Warning] Ollama not available. Using mock mode.")

        # Statistics
        self.stats = {
            "total_chats": 0,
            "total_tool_calls": 0,
            "total_errors": 0,
            "sessions_created": 0,
        }

    def chat(self, message: str, use_tools: bool = True) -> dict:
        """
        Main chat method. Implements the full ReAct loop with
        error handling, memory, and guard checks.
        """
        self.stats["total_chats"] += 1
        self.memory.add_user_message(message)

        start_time = time.time()
        thinking_steps = []
        tool_calls = []
        iteration = 0
        same_tool_count = 0
        last_tool = None

        if not self._llm_available or not use_tools:
            response = self._simple_chat(message)
            self.memory.add_assistant_message(response)
            return self._build_response(response, thinking_steps, tool_calls)

        # Build initial prompt with tools and memory context
        context = self.memory.get_context_for_llm()
        tools_desc = get_tools_description()

        system_prompt = (
            "You are a helpful AI assistant with tools. Answer in Chinese.\n\n"
            + tools_desc + "\n\n"
            + TOOL_CALL_INSTRUCTION + "\n\n"
            + "Start with 'Thought:' to analyze what you need to do."
        )

        history_lines = []

        while iteration < self.config.max_iterations:
            iteration += 1

            # Guard: time limit
            elapsed = time.time() - start_time
            if elapsed > self.config.max_time_seconds:
                thinking_steps.append({"type": "error", "content": "Timeout reached"})
                break

            # Build prompt
            history_text = "\n".join(history_lines) if history_lines else ""
            prompt = system_prompt + "\n\n" + context
            if history_text:
                prompt += "\n\n" + history_text
            prompt += "\n\nUser: " + message + "\n\nAssistant:"

            # LLM call
            try:
                llm_output = self.llm.invoke(prompt)
            except Exception as e:
                thinking_steps.append({"type": "error", "content": "LLM error: " + str(e)})
                break

            # Parse output
            parsed = parse_agent_output(llm_output)

            # Record thought
            if parsed["thought"]:
                thinking_steps.append({"type": "think", "content": parsed["thought"][:200]})
                history_lines.append("Thought: " + parsed["thought"])

            # Check for answer
            if parsed["answer"]:
                response = parsed["answer"]
                self.memory.add_assistant_message(response)
                return self._build_response(response, thinking_steps, tool_calls)

            # Execute tool action
            if parsed["action"]:
                tool_name = parsed["action"]["tool"]
                tool_args = parsed["action"]["arguments"]

                # Guard: same tool repeated too many times
                if tool_name == last_tool:
                    same_tool_count += 1
                else:
                    same_tool_count = 1
                    last_tool = tool_name

                if same_tool_count >= self.config.max_same_tool_calls:
                    thinking_steps.append({
                        "type": "error",
                        "content": "Tool " + tool_name + " called too many times",
                    })
                    history_lines.append(
                        "Observation: Tool called too many times. "
                        "Please try a different approach or provide an Answer."
                    )
                    continue

                thinking_steps.append({
                    "type": "action",
                    "tool": tool_name,
                    "content": json.dumps(tool_args, ensure_ascii=False)[:100],
                })
                tool_calls.append({"tool": tool_name, "arguments": tool_args})
                self.stats["total_tool_calls"] += 1

                # Execute with error handling
                result = self.tool_executor.execute(tool_name, **tool_args)
                result_text = str(result)[:1500]

                if not result.success:
                    self.stats["total_errors"] += 1
                    advice = ErrorAdvisor.analyze(result.error or "", tool_name, tool_args)
                    thinking_steps.append({
                        "type": "error",
                        "content": (result.error or "Unknown error")[:100],
                    })
                    history_lines.append(
                        "Action: " + tool_name + "\n"
                        "Observation: ERROR - " + (result.error or "") + "\n"
                        "Suggestion: " + advice["suggestion"]
                    )
                else:
                    thinking_steps.append({
                        "type": "observe",
                        "content": result_text[:200],
                    })
                    history_lines.append(
                        "Action: " + tool_name + "\n"
                        "Observation: " + result_text
                    )

                # Store tool result in working memory
                self.memory.working.add_tool_result(
                    tool_name, tool_args, result_text, result.success,
                )
            else:
                # No action and no answer: nudge the LLM
                history_lines.append(
                    "Observation: No action taken. "
                    "Please use a tool or provide 'Answer: ...' with your final response."
                )

        # Fell through: compile answer from observations
        observations = [s["content"] for s in thinking_steps if s["type"] == "observe"]
        if observations:
            response = "Based on my research:\n\n" + "\n".join(observations[:3])
        else:
            response = "I wasn't able to complete the task within the iteration limit."

        self.memory.add_assistant_message(response)
        return self._build_response(response, thinking_steps, tool_calls)

    def _simple_chat(self, message: str) -> str:
        """Simple chat without tools (fallback)"""
        if self._llm_available:
            try:
                context = self.memory.get_context_for_llm()
                prompt = context + "\nUser: " + message + "\nAssistant:"
                return self.llm.invoke(prompt)
            except Exception as e:
                return "[Error: " + str(e) + "]"
        return "[Mock] " + message[:50]

    def _build_response(self, message: str, steps: list, tool_calls: list) -> dict:
        """Build the final response dict"""
        return {
            "session_id": self.memory.session_id,
            "message": message,
            "thinking_steps": steps,
            "tool_calls": tool_calls,
            "metadata": {
                "model": self.config.model_name,
                "llm_available": self._llm_available,
                "stats": dict(self.stats),
            },
        }

    def save_session(self) -> str:
        """Save current session"""
        return self.memory.save()

    def new_session(self) -> None:
        """Start a new session"""
        self.memory.new_session()
        self.stats["sessions_created"] += 1

    def get_stats(self) -> dict:
        """Get agent statistics"""
        return {
            **self.stats,
            "memory": self.memory.get_stats(),
            "tool_executor": self.tool_executor.get_stats(),
        }


# ============================================================
# 4. Project Scaffold Generator
# ============================================================

PROJECT_README_TEMPLATE = """# My Agent Project

> An AI Agent built with LangChain, LangGraph, Ollama, and Chroma

## Quick Start

```bash
# 1. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Start Ollama
ollama pull qwen2.5:7b

# 3. Run the agent
python main.py interactive

# 4. Or start the API server
python main.py serve
# Visit http://localhost:8000/docs
```

## Project Structure

```
my-agent-project/
  main.py              # Entry point
  agent/
    __init__.py
    core.py            # Agent core (ReAct loop)
    tools.py           # Tool definitions
    memory.py          # Memory management
    errors.py          # Error handling
  api/
    __init__.py
    server.py          # FastAPI server
    models.py          # Request/Response models
  ui/
    index.html         # React UI (CDN, standalone)
  tests/
    test_tools.py      # Tool tests
    test_agent.py      # Agent tests
  requirements.txt
  README.md
```

## Architecture

```
React UI --> FastAPI Server --> Agent Core
                                   |
                            +------+------+
                            |      |      |
                          Tools  Memory  Guards
                            |
                      +-----+-----+
                      |     |     |
                    File   Web   Code
                    R/W  Summary  Exec
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /chat | Send a chat message |
| GET | /chat/stream | Stream response (SSE) |
| POST | /tools/execute | Execute a tool directly |
| GET | /tools | List available tools |
| GET | /sessions | List active sessions |
| GET | /health | Health check |

## Tech Stack

- **LLM**: Ollama (qwen2.5:7b)
- **Framework**: LangChain + LangGraph
- **Vector DB**: Chroma
- **API**: FastAPI
- **UI**: React (CDN)
"""

REQUIREMENTS_TEMPLATE = """langchain>=0.1.0
langchain-community>=0.0.10
langchain-chroma>=0.1.0
chromadb>=0.4.0
langgraph>=0.0.20
fastapi>=0.104.0
uvicorn>=0.24.0
openai>=1.0.0
python-dotenv>=1.0.0
httpx>=0.25.0
beautifulsoup4>=4.12.0
pydantic>=2.0.0
"""


def generate_scaffold(output_dir: str = "./my-agent-project") -> dict:
    """Generate a project scaffold with all necessary files"""
    base = Path(output_dir).resolve()
    created_files = []

    # Create directories
    dirs = [
        base,
        base / "agent",
        base / "api",
        base / "ui",
        base / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Create files
    files = {
        "README.md": PROJECT_README_TEMPLATE,
        "requirements.txt": REQUIREMENTS_TEMPLATE,
        "agent/__init__.py": '"""Agent core module"""\n',
        "api/__init__.py": '"""API server module"""\n',
        "tests/__init__.py": "",
    }

    for filename, content in files.items():
        filepath = base / filename
        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
            created_files.append(str(filepath))

    return {
        "output_dir": str(base),
        "files_created": created_files,
        "total_files": len(created_files),
    }


# ============================================================
# 5. 演示和 CLI
# ============================================================

def run_demo():
    """Run a complete demo of the full agent"""
    print("=" * 60)
    print("Full Agent Demo")
    print("=" * 60)

    agent = FullAgent()

    # Demo 1: Simple chat
    print("\n--- Demo 1: Simple chat ---")
    result = agent.chat("Hello! What can you do?", use_tools=False)
    print("  Response:", result["message"][:100])

    # Demo 2: Calculator
    print("\n--- Demo 2: Tool usage (calculator) ---")
    result = agent.chat("Calculate the area of a circle with radius 7")
    print("  Response:", result["message"][:200])
    print("  Steps:", len(result["thinking_steps"]))
    for step in result["thinking_steps"]:
        print("    [" + step["type"] + "]", step.get("content", "")[:80])

    # Demo 3: File reading
    print("\n--- Demo 3: File reading ---")
    result = agent.chat("Read the file day1_multi_tools.py and tell me what tools are defined")
    print("  Response:", result["message"][:200])
    print("  Tool calls:", len(result["tool_calls"]))

    # Demo 4: Multi-turn conversation
    print("\n--- Demo 4: Multi-turn ---")
    agent.new_session()
    result1 = agent.chat("My name is Alice", use_tools=False)
    print("  Turn 1:", result1["message"][:100])
    result2 = agent.chat("What's my name?", use_tools=False)
    print("  Turn 2:", result2["message"][:100])

    # Demo 5: Error handling
    print("\n--- Demo 5: Error handling ---")
    result = agent.chat("Read the file /nonexistent/path/file.txt")
    print("  Response:", result["message"][:200])
    print("  Errors in steps:", sum(1 for s in result["thinking_steps"] if s["type"] == "error"))

    # Stats
    print("\n--- Agent Stats ---")
    stats = agent.get_stats()
    print("  Total chats:", stats["total_chats"])
    print("  Total tool calls:", stats["total_tool_calls"])
    print("  Total errors:", stats["total_errors"])

    # Save session
    path = agent.save_session()
    print("  Session saved:", path)


def run_interactive():
    """Run the agent in interactive mode"""
    agent = FullAgent()

    print("\n" + "=" * 60)
    print("Full Agent - Interactive Mode")
    print("=" * 60)
    print("Commands:")
    print("  quit          - Exit")
    print("  /tools        - List available tools")
    print("  /stats        - Show agent statistics")
    print("  /save         - Save session")
    print("  /new          - Start new session")
    print("  /no-tools     - Disable tools for next message")
    print("=" * 60)

    use_tools = True

    while True:
        try:
            user_input = input("\nYou> ").strip()
        except (KeyboardInterrupt, EOFError):
            agent.save_session()
            print("\nSession saved. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            agent.save_session()
            print("Session saved. Goodbye!")
            break
        elif user_input == "/tools":
            print("\n  Available tools:")
            for name, tool in MULTI_TOOL_REGISTRY.items():
                print("    -", name + ":", tool["description"][:60])
            continue
        elif user_input == "/stats":
            stats = agent.get_stats()
            print("  Stats:", json.dumps(stats, indent=2, ensure_ascii=False, default=str))
            continue
        elif user_input == "/save":
            path = agent.save_session()
            print("  Saved:", path)
            continue
        elif user_input == "/new":
            agent.new_session()
            print("  New session started.")
            continue
        elif user_input == "/no-tools":
            use_tools = False
            print("  Tools disabled for next message.")
            continue

        # Chat
        result = agent.chat(user_input, use_tools=use_tools)
        use_tools = True  # Reset

        # Show thinking steps
        if result["thinking_steps"]:
            print("\n  --- Thinking ---")
            for step in result["thinking_steps"]:
                step_type = step["type"].upper()
                content = step.get("content", "")[:100]
                tool = step.get("tool", "")
                prefix = "    [" + step_type + "]"
                if tool:
                    prefix += " " + tool
                print(prefix, content)

        print("\nAgent>", result["message"])


def run_serve():
    """Start the FastAPI server"""
    try:
        import uvicorn
        from day4_fastapi_agent import create_app
        app = create_app()
        if app:
            print("Starting Agent API server...")
            print("Visit http://localhost:8000/docs for API documentation")
            print("Open day5_react_agent_ui/index.html for the UI")
            uvicorn.run(app, host="0.0.0.0", port=8000)
        else:
            print("Failed to create app. Install: pip install fastapi uvicorn")
    except ImportError:
        print("FastAPI not installed. Run: pip install fastapi uvicorn")


def run_scaffold():
    """Generate project scaffold"""
    print("\n--- Generating Project Scaffold ---")
    result = generate_scaffold()
    print("  Output:", result["output_dir"])
    print("  Files created:", result["total_files"])
    for f in result["files_created"]:
        print("    -", f)


def print_usage():
    print("""
Full Agent Project - Week 10 Final

Usage:
  python day67_full_project.py demo          Run complete demo
  python day67_full_project.py serve         Start FastAPI server
  python day67_full_project.py interactive   Interactive chat mode
  python day67_full_project.py scaffold      Generate project template

Architecture:
  React UI --> FastAPI --> Agent Core --> Tools + Memory + Guards
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    if command == "demo":
        run_demo()
    elif command == "serve":
        run_serve()
    elif command == "interactive":
        run_interactive()
    elif command == "scaffold":
        run_scaffold()
    else:
        print_usage()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default: run demo
        run_demo()
    else:
        main()


    # ============================================================
    # 扩展练习（可选）
    # ============================================================

    # TODO 1: 添加 "Agent 评估" 功能
    # 定义一组测试问题和预期答案
    # 自动运行 Agent 并评估回答质量
    # 输出评估报告（正确率、平均延迟、工具使用情况）

    # TODO 2: 实现 "Multi-Agent" 模式
    # 创建多个 Agent，每个有不同的专长
    # 一个 Router Agent 负责把问题分发给合适的专家 Agent
    # 例如：代码 Agent、搜索 Agent、写作 Agent

    # TODO 3: 添加 "Agent 日志系统"
    # 用 Python logging 记录所有操作
    # 支持不同日志级别（DEBUG, INFO, WARNING, ERROR）
    # 日志输出到文件，方便事后分析

    # TODO 4: 实现 "Agent 配置热更新"
    # 支持在运行时修改配置（如 max_iterations, model_name）
    # 不需要重启 Agent
    # 提示：用 watchdog 监听配置文件变化
