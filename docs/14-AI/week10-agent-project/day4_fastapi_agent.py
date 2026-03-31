"""
Day 4: 把 Agent 包装成 FastAPI API
让 Agent 可以通过 HTTP 接口调用，支持 SSE streaming
类比前端：把一个 Redux store 的功能暴露为 REST API + WebSocket

用法:
  pip install fastapi uvicorn
  python day4_fastapi_agent.py
  # 然后访问 http://localhost:8000/docs 看交互式 API 文档
"""

import json
import time
import asyncio
import uuid
import re
from typing import Optional, AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path

from langchain_community.llms import Ollama

# Import from previous days
from day1_multi_tools import (
    ToolResult,
    MULTI_TOOL_REGISTRY,
    execute_tool,
    get_tools_description,
)
from day2_error_handling import RobustToolExecutor, RetryConfig, RetryStrategy
from day3_conversation_memory import MemoryManager, MessageRole


# ============================================================
# 1. API 架构设计
# ============================================================

"""
FastAPI Agent 的架构：

Client (React UI)
  POST /chat          GET /chat/stream (SSE)
  POST /tools/execute GET /sessions
        |                    |
  FastAPI Endpoints    SSE Streaming
        |                    |
        +--- Agent Core -----+
        |  Tool Executor  |  Memory Manager  |

类比前端 BFF (Backend for Frontend)：
- FastAPI = Express.js / Next.js API routes
- SSE = EventSource API
- Session = Session cookie + Redis
"""


# ============================================================
# 2. Agent Service（业务逻辑层）
# ============================================================

TOOL_CALL_INSTRUCTION = (
    'To use a tool, respond with:\n'
    '```tool_call\n'
    '{"tool": "tool_name", "arguments": {"arg1": "value1"}}\n'
    '```\n'
    'If no tool is needed, just answer directly.'
)


class AgentService:
    """
    Core agent service that handles chat, tool execution, and memory.
    Separated from the HTTP layer for testability.
    """

    def __init__(self, model_name: str = "qwen2.5:7b"):
        self.model_name = model_name
        self.sessions: dict[str, MemoryManager] = {}
        self.tool_executor = RobustToolExecutor(
            retry_config=RetryConfig(max_retries=2, strategy=RetryStrategy.EXPONENTIAL),
        )

        # Try to connect to Ollama
        try:
            self.llm = Ollama(model=model_name)
            self._llm_available = True
        except Exception:
            self.llm = None
            self._llm_available = False
            print("[Warning] Ollama not available. Using mock responses.")

    def _get_session(self, session_id: Optional[str] = None) -> tuple[str, MemoryManager]:
        """Get or create a session"""
        if session_id and session_id in self.sessions:
            return session_id, self.sessions[session_id]

        new_id = session_id or str(uuid.uuid4())[:8]
        memory = MemoryManager(session_id=new_id)
        memory.short_term.set_system_message(
            "You are a helpful AI assistant with tool capabilities. "
            "Answer in Chinese. Be concise and helpful."
        )
        self.sessions[new_id] = memory
        return new_id, memory

    def chat(self, message: str, session_id: Optional[str] = None, use_tools: bool = True) -> dict:
        """Process a chat message and return a response"""
        sid, memory = self._get_session(session_id)
        memory.add_user_message(message)
        context = memory.get_context_for_llm()

        tool_calls = []
        thinking_steps = []

        if self._llm_available and use_tools:
            response = self._chat_with_tools(message, context, tool_calls, thinking_steps)
        elif self._llm_available:
            try:
                prompt = context + "\n\nUser: " + message + "\n\nAssistant:"
                response = self.llm.invoke(prompt)
            except Exception as e:
                response = "[LLM Error: " + str(e) + "]"
        else:
            response = self._mock_chat(message, memory)

        memory.add_assistant_message(response)

        return {
            "session_id": sid,
            "message": response,
            "tool_calls": tool_calls,
            "thinking_steps": thinking_steps,
            "metadata": {
                "model": self.model_name,
                "llm_available": self._llm_available,
                "message_count": len(memory.short_term.messages),
            },
        }

    def _chat_with_tools(self, message: str, context: str, tool_calls: list, thinking_steps: list) -> str:
        """Chat with tool support using simple ReAct"""
        tools_desc = get_tools_description()

        prompt_parts = [
            "You are an AI assistant with tools. Answer in Chinese.\n",
            tools_desc,
            "\n",
            TOOL_CALL_INSTRUCTION,
            "\n",
            context,
            "\nUser: " + message,
        ]
        prompt = "\n".join(prompt_parts)

        try:
            llm_output = self.llm.invoke(prompt)
        except Exception as e:
            return "[LLM Error: " + str(e) + "]"

        thinking_steps.append({"type": "think", "content": llm_output[:200]})

        # Parse tool call from output
        tool_call_match = re.search(r"```tool_call\s*\n?(.*?)\n?\s*```", llm_output, re.DOTALL)
        if not tool_call_match:
            tool_call_match = re.search(r'```(?:json)?\s*\n?(\{[^}]*"tool"[^}]*\})\n?\s*```', llm_output, re.DOTALL)

        if not tool_call_match:
            return llm_output

        # Execute the tool
        try:
            call_data = json.loads(tool_call_match.group(1).strip())
            tool_name = call_data.get("tool", "")
            tool_args = call_data.get("arguments", {})
        except json.JSONDecodeError:
            return llm_output

        tool_calls.append({"tool": tool_name, "arguments": tool_args})
        thinking_steps.append({"type": "action", "tool": tool_name, "args": tool_args})

        result = self.tool_executor.execute(tool_name, **tool_args)
        thinking_steps.append({"type": "observe", "result": str(result)[:200]})

        # Ask LLM to summarize the result
        followup = (
            "Tool " + tool_name + " returned:\n"
            + str(result)[:1500]
            + "\n\nBased on this result, answer the user's question in Chinese.\n"
            + "User question: " + message
        )

        try:
            final_answer = self.llm.invoke(followup)
        except Exception as e:
            final_answer = "Tool result:\n" + str(result)[:500]

        return final_answer

    def _mock_chat(self, message: str, memory: MemoryManager) -> str:
        """Generate mock response without LLM"""
        msg_count = len(memory.short_term.messages)
        return "[Mock] 收到消息: " + message[:50] + "... (第 " + str(msg_count) + " 轮对话)"

    def execute_tool_directly(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool directly without LLM"""
        result = self.tool_executor.execute(tool_name, **arguments)
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata,
        }

    def get_session_list(self) -> list[dict]:
        """List all active sessions"""
        return [
            {
                "session_id": sid,
                "message_count": len(mem.short_term.messages),
            }
            for sid, mem in self.sessions.items()
        ]

    def get_session_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session"""
        if session_id not in self.sessions:
            return []
        memory = self.sessions[session_id]
        return [msg.to_dict() for msg in memory.short_term.get_messages()]

    def get_available_tools(self) -> list[dict]:
        """List all available tools with their descriptions"""
        tools = []
        for name, tool in MULTI_TOOL_REGISTRY.items():
            tools.append({
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
            })
        return tools


# ============================================================
# 3. SSE Event Generator
# ============================================================

class SSEFormatter:
    """
    Format data as Server-Sent Events (SSE).
    SSE is the simplest way to stream data from server to client.

    Frontend analogy: EventSource API
      const es = new EventSource('/chat/stream?message=hello');
      es.onmessage = (e) => console.log(JSON.parse(e.data));
    """

    @staticmethod
    def format_event(data: dict, event_type: str = "message") -> str:
        """Format a single SSE event"""
        json_data = json.dumps(data, ensure_ascii=False)
        return "event: " + event_type + "\ndata: " + json_data + "\n\n"

    @staticmethod
    def format_done() -> str:
        """Format the done event"""
        return 'event: done\ndata: {"status": "complete"}\n\n'


async def stream_chat_response(
    service: AgentService,
    message: str,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Generate SSE events for a chat response.
    Yields events as the agent thinks, acts, and responds.
    """
    # Event 1: Acknowledge the message
    yield SSEFormatter.format_event(
        {"type": "start", "message": "Processing your message..."},
        event_type="status",
    )

    # Event 2: Thinking step
    yield SSEFormatter.format_event(
        {"type": "thinking", "content": "Analyzing the question..."},
        event_type="step",
    )
    await asyncio.sleep(0.1)  # Small delay for visual effect

    # Event 3: Get the response (run blocking code in executor)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: service.chat(message, session_id),
    )

    # Event 4: Send thinking steps
    for step in result.get("thinking_steps", []):
        yield SSEFormatter.format_event(step, event_type="step")
        await asyncio.sleep(0.05)

    # Event 5: Send tool calls
    for tc in result.get("tool_calls", []):
        yield SSEFormatter.format_event(tc, event_type="tool_call")

    # Event 6: Send final response (character by character for typing effect)
    response_text = result.get("message", "")
    chunk_size = 10  # Send 10 chars at a time
    for i in range(0, len(response_text), chunk_size):
        chunk = response_text[i:i + chunk_size]
        yield SSEFormatter.format_event(
            {"type": "content", "content": chunk},
            event_type="message",
        )
        await asyncio.sleep(0.02)

    # Event 7: Done
    yield SSEFormatter.format_event(
        {"type": "done", "session_id": result.get("session_id", "")},
        event_type="done",
    )


# ============================================================
# 4. FastAPI Application
# ============================================================

def create_app() -> "FastAPI":
    """Create and configure the FastAPI application"""
    try:
        from fastapi import FastAPI, Query, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import StreamingResponse, HTMLResponse
        from pydantic import BaseModel, Field
    except ImportError:
        print("FastAPI not installed. Run: pip install fastapi uvicorn")
        print("Running in demo mode instead.")
        return None

    # Pydantic models for request/response
    class ChatRequest(BaseModel):
        message: str = Field(..., description="User message")
        session_id: Optional[str] = Field(None, description="Session ID")
        use_tools: bool = Field(True, description="Enable tool usage")

    class ToolRequest(BaseModel):
        tool_name: str
        arguments: dict = Field(default_factory=dict)

    # Create FastAPI app
    app = FastAPI(
        title="Agent API",
        description="AI Agent with tools, memory, and streaming support",
        version="1.0.0",
    )

    # CORS middleware (allow frontend access)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared agent service
    service = AgentService()

    # ---- Endpoints ----

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Root endpoint with API info"""
        return """
        <html>
        <body>
            <h1>Agent API</h1>
            <p>Visit <a href="/docs">/docs</a> for interactive API documentation.</p>
            <h2>Endpoints:</h2>
            <ul>
                <li>POST /chat - Send a chat message</li>
                <li>GET /chat/stream - Stream a chat response (SSE)</li>
                <li>POST /tools/execute - Execute a tool directly</li>
                <li>GET /tools - List available tools</li>
                <li>GET /sessions - List active sessions</li>
                <li>GET /sessions/{session_id}/history - Get session history</li>
            </ul>
        </body>
        </html>
        """

    @app.post("/chat")
    async def chat(request: ChatRequest):
        """Send a chat message and get a response"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: service.chat(
                request.message,
                request.session_id,
                request.use_tools,
            ),
        )
        return result

    @app.get("/chat/stream")
    async def chat_stream(
        message: str = Query(..., description="User message"),
        session_id: Optional[str] = Query(None, description="Session ID"),
    ):
        """Stream a chat response using Server-Sent Events"""
        return StreamingResponse(
            stream_chat_response(service, message, session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/tools/execute")
    async def execute_tool_endpoint(request: ToolRequest):
        """Execute a tool directly"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: service.execute_tool_directly(request.tool_name, request.arguments),
        )
        return result

    @app.get("/tools")
    async def list_tools():
        """List all available tools"""
        return {"tools": service.get_available_tools()}

    @app.get("/sessions")
    async def list_sessions():
        """List all active sessions"""
        return {"sessions": service.get_session_list()}

    @app.get("/sessions/{session_id}/history")
    async def get_history(session_id: str):
        """Get conversation history for a session"""
        history = service.get_session_history(session_id)
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session_id": session_id, "messages": history}

    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "ok",
            "llm_available": service._llm_available,
            "model": service.model_name,
            "active_sessions": len(service.sessions),
            "tools_count": len(MULTI_TOOL_REGISTRY),
        }

    return app


# ============================================================
# 5. 演示（不启动 server）
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 4: FastAPI Agent 演示")
    print("=" * 60)

    # ---- Part A: Agent Service test ----
    print("\n--- Part A: Agent Service (no HTTP) ---")
    service = AgentService()

    # Chat
    result = service.chat("你好！请介绍一下你自己")
    print("  Response:", result["message"][:100])
    print("  Session:", result["session_id"])

    # Follow-up in same session
    result2 = service.chat("帮我计算 42 * 3.14", session_id=result["session_id"])
    print("  Follow-up:", result2["message"][:100])

    # Direct tool execution
    tool_result = service.execute_tool_directly("calculator", {"expression": "42 * 3.14"})
    print("  Direct tool:", tool_result)

    # List tools
    tools = service.get_available_tools()
    print("\n  Available tools:")
    for t in tools:
        print("    -", t["name"] + ":", t["description"][:50])

    # Sessions
    sessions = service.get_session_list()
    print("\n  Active sessions:", sessions)

    # ---- Part B: SSE format test ----
    print("\n--- Part B: SSE Format ---")
    event = SSEFormatter.format_event({"type": "message", "content": "Hello"})
    print("  SSE event:")
    print("  " + event.replace("\n", "\n  "))

    # ---- Part C: Start server ----
    print("\n--- Part C: FastAPI Server ---")
    app = create_app()
    if app:
        print("  App created successfully!")
        print("  To start the server, run:")
        print("    uvicorn day4_fastapi_agent:app --reload --port 8000")
        print("  Then visit http://localhost:8000/docs")

        # Create the module-level app for uvicorn
        import sys
        if "--serve" in sys.argv:
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("  FastAPI not installed. Run: pip install fastapi uvicorn")

    # ---- Part D: curl examples ----
    print("\n--- Part D: API Usage Examples ---")
    print("""
  # Chat
  curl -X POST http://localhost:8000/chat \\
    -H "Content-Type: application/json" \\
    -d '{"message": "Hello!", "use_tools": true}'

  # Stream
  curl -N http://localhost:8000/chat/stream?message=Hello

  # Execute tool
  curl -X POST http://localhost:8000/tools/execute \\
    -H "Content-Type: application/json" \\
    -d '{"tool_name": "calculator", "arguments": {"expression": "2+2"}}'

  # List tools
  curl http://localhost:8000/tools

  # Health check
  curl http://localhost:8000/health
""")


    # ============================================================
    # 练习题
    # ============================================================

    print("=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 添加 WebSocket 端点
    # 替代 SSE，实现双向实时通信
    # 提示：from fastapi import WebSocket

    # TODO 2: 添加认证中间件
    # 用 API Key 保护端点
    # 提示：from fastapi.security import APIKeyHeader

    # TODO 3: 添加请求限流
    # 每个 session 每分钟最多 20 个请求
    # 提示：用 dict 记录请求时间戳，检查窗口内数量


# Module-level app for uvicorn (uvicorn day4_fastapi_agent:app)
app = create_app()
