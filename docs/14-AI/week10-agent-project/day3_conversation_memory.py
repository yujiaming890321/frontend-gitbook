"""
Day 3: Agent 的对话记忆管理
让 Agent 记住之前的对话和操作结果，实现多轮对话
类比前端：Session Storage / Redux Store / React Context
"""

import json
import time
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from langchain_community.llms import Ollama


# ============================================================
# 1. 记忆类型
# ============================================================

"""
Agent 记忆的三种类型：

┌──────────────────────────────────────────────────────┐
│                    Agent 记忆架构                      │
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Short-term   │  │ Long-term    │  │ Working      │ │
│  │ 短期记忆      │  │ 长期记忆      │  │ 工作记忆      │ │
│  │              │  │              │  │              │ │
│  │ 当前对话历史   │  │ 跨会话持久化   │  │ 当前任务状态  │ │
│  │ (最近 N 轮)   │  │ (文件/数据库)  │  │ (变量/上下文) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                        │
│  类比前端：                                             │
│  - 短期 → React state / Vue data                       │
│  - 长期 → localStorage / IndexedDB                     │
│  - 工作 → useRef / computed                            │
└──────────────────────────────────────────────────────┘
"""


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A single message in the conversation"""
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        role_prefix = {
            MessageRole.SYSTEM: "[System]",
            MessageRole.USER: "[User]",
            MessageRole.ASSISTANT: "[Agent]",
            MessageRole.TOOL: "[Tool]",
        }[self.role]
        return f"{role_prefix} {self.content[:100]}"


# ============================================================
# 2. 短期记忆（Sliding Window）
# ============================================================

class ShortTermMemory:
    """
    Keeps the most recent N messages in memory.
    Similar to a sliding window buffer.

    Frontend analogy: React state with a fixed-size array.
    When new messages arrive, oldest ones are dropped.
    """

    def __init__(self, max_messages: int = 20, max_tokens_estimate: int = 4000):
        self.max_messages = max_messages
        self.max_tokens_estimate = max_tokens_estimate
        self.messages: list[Message] = []
        self._system_message: Optional[Message] = None

    def set_system_message(self, content: str) -> None:
        """Set the system message (always kept at the beginning)"""
        self._system_message = Message(role=MessageRole.SYSTEM, content=content)

    def add_message(self, role: MessageRole, content: str, metadata: dict = None) -> None:
        """Add a message to memory, pruning oldest if needed"""
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self._prune()

    def _prune(self) -> None:
        """Remove oldest messages to stay within limits"""
        # Keep within message count limit
        while len(self.messages) > self.max_messages:
            self.messages.pop(0)

        # Estimate token usage and prune if needed
        total_tokens = self._estimate_tokens()
        while total_tokens > self.max_tokens_estimate and len(self.messages) > 2:
            self.messages.pop(0)
            total_tokens = self._estimate_tokens()

    def _estimate_tokens(self) -> int:
        """Rough token count estimate (1 token ~ 4 chars for English, ~2 for Chinese)"""
        total = sum(len(m.content) for m in self.messages)
        if self._system_message:
            total += len(self._system_message.content)
        return total // 3  # Conservative estimate for mixed content

    def get_messages(self) -> list[Message]:
        """Get all messages including system message"""
        result = []
        if self._system_message:
            result.append(self._system_message)
        result.extend(self.messages)
        return result

    def get_formatted_history(self) -> str:
        """Format messages as a string for LLM prompt"""
        lines = []
        for msg in self.get_messages():
            role_name = msg.role.value.capitalize()
            lines.append(f"{role_name}: {msg.content}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all messages (keep system message)"""
        self.messages.clear()

    def get_last_n(self, n: int) -> list[Message]:
        """Get the last N messages"""
        return self.messages[-n:]

    def get_stats(self) -> dict:
        return {
            "message_count": len(self.messages),
            "has_system_message": self._system_message is not None,
            "estimated_tokens": self._estimate_tokens(),
            "max_messages": self.max_messages,
        }


# ============================================================
# 3. 长期记忆（Persistent Storage）
# ============================================================

class LongTermMemory:
    """
    Persists conversation history to disk as JSON.
    Can load previous sessions and search through history.

    Frontend analogy: localStorage with JSON serialization.
    """

    def __init__(self, storage_dir: str = ".agent_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session_id: str, messages: list[Message]) -> str:
        """Save a conversation session to disk"""
        file_path = self.storage_dir / f"{session_id}.json"
        data = {
            "session_id": session_id,
            "created_at": time.time(),
            "message_count": len(messages),
            "messages": [m.to_dict() for m in messages],
        }
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(file_path)

    def load_session(self, session_id: str) -> list[Message]:
        """Load a conversation session from disk"""
        file_path = self.storage_dir / f"{session_id}.json"
        if not file_path.exists():
            return []

        data = json.loads(file_path.read_text(encoding="utf-8"))
        return [Message.from_dict(m) for m in data.get("messages", [])]

    def list_sessions(self) -> list[dict]:
        """List all saved sessions"""
        sessions = []
        for file_path in sorted(self.storage_dir.glob("*.json")):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                sessions.append({
                    "session_id": data.get("session_id", file_path.stem),
                    "created_at": data.get("created_at", 0),
                    "message_count": data.get("message_count", 0),
                })
            except Exception:
                continue
        return sessions

    def search_history(self, keyword: str) -> list[dict]:
        """Search through all sessions for a keyword"""
        results = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                for msg in data.get("messages", []):
                    if keyword.lower() in msg.get("content", "").lower():
                        results.append({
                            "session_id": data.get("session_id", file_path.stem),
                            "role": msg["role"],
                            "content": msg["content"][:200],
                        })
            except Exception:
                continue
        return results

    def delete_session(self, session_id: str) -> bool:
        """Delete a saved session"""
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# ============================================================
# 4. 工作记忆（Task Context）
# ============================================================

class WorkingMemory:
    """
    Stores temporary state for the current task.
    Includes tool results, extracted facts, and task progress.

    Frontend analogy: useRef or a class instance variable that
    persists across renders but doesn't trigger re-render.
    """

    def __init__(self):
        self.facts: dict[str, str] = {}        # Extracted facts: key -> value
        self.tool_results: list[dict] = []      # Recent tool execution results
        self.task_notes: list[str] = []          # Agent's notes about the task
        self.variables: dict[str, Any] = {}     # Named variables for computation

    def add_fact(self, key: str, value: str) -> None:
        """Store a discovered fact"""
        self.facts[key] = value

    def get_fact(self, key: str) -> Optional[str]:
        """Retrieve a fact"""
        return self.facts.get(key)

    def add_tool_result(self, tool_name: str, args: dict, result: str, success: bool) -> None:
        """Record a tool execution result"""
        self.tool_results.append({
            "tool": tool_name,
            "args": args,
            "result": result[:500],  # Truncate to save memory
            "success": success,
            "timestamp": time.time(),
        })

    def add_note(self, note: str) -> None:
        """Add a task-related note"""
        self.task_notes.append(note)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a named variable"""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a named variable"""
        return self.variables.get(name, default)

    def get_summary(self) -> str:
        """Get a summary of working memory for the LLM prompt"""
        lines = []

        if self.facts:
            lines.append("Known facts:")
            for key, value in self.facts.items():
                lines.append(f"  - {key}: {value}")

        if self.tool_results:
            lines.append(f"\nRecent tool results ({len(self.tool_results)} total):")
            for tr in self.tool_results[-3:]:  # Last 3 results
                status = "OK" if tr["success"] else "FAIL"
                lines.append(f"  - [{status}] {tr['tool']}: {tr['result'][:100]}...")

        if self.task_notes:
            lines.append(f"\nTask notes:")
            for note in self.task_notes[-5:]:
                lines.append(f"  - {note}")

        return "\n".join(lines) if lines else "(No working memory)"

    def clear(self) -> None:
        """Clear all working memory"""
        self.facts.clear()
        self.tool_results.clear()
        self.task_notes.clear()
        self.variables.clear()


# ============================================================
# 5. 统一记忆管理器
# ============================================================

class MemoryManager:
    """
    Unified memory manager that combines short-term, long-term,
    and working memory.

    Frontend analogy: Redux store with multiple slices.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        max_short_term: int = 20,
        storage_dir: str = ".agent_memory",
    ):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.short_term = ShortTermMemory(max_messages=max_short_term)
        self.long_term = LongTermMemory(storage_dir=storage_dir)
        self.working = WorkingMemory()

    def add_user_message(self, content: str) -> None:
        """Add a user message"""
        self.short_term.add_message(MessageRole.USER, content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant (agent) message"""
        self.short_term.add_message(MessageRole.ASSISTANT, content)

    def add_tool_message(self, tool_name: str, result: str) -> None:
        """Add a tool result message"""
        self.short_term.add_message(
            MessageRole.TOOL, result,
            metadata={"tool_name": tool_name},
        )

    def get_context_for_llm(self) -> str:
        """
        Build the full context string for the LLM prompt.
        Combines conversation history and working memory.
        """
        parts = []

        # Conversation history
        history = self.short_term.get_formatted_history()
        if history:
            parts.append("Conversation history:\n" + history)

        # Working memory summary
        working_summary = self.working.get_summary()
        if working_summary != "(No working memory)":
            parts.append("\nCurrent context:\n" + working_summary)

        return "\n\n".join(parts)

    def save(self) -> str:
        """Save current session to long-term memory"""
        return self.long_term.save_session(
            self.session_id,
            self.short_term.messages,
        )

    def load(self, session_id: str) -> None:
        """Load a previous session"""
        messages = self.long_term.load_session(session_id)
        self.short_term.clear()
        for msg in messages:
            self.short_term.messages.append(msg)
        self.session_id = session_id

    def new_session(self) -> None:
        """Start a new session (save current and clear)"""
        if self.short_term.messages:
            self.save()
        self.session_id = f"session_{int(time.time())}"
        self.short_term.clear()
        self.working.clear()

    def get_stats(self) -> dict:
        return {
            "session_id": self.session_id,
            "short_term": self.short_term.get_stats(),
            "long_term_sessions": len(self.long_term.list_sessions()),
            "working_memory_facts": len(self.working.facts),
            "working_memory_tools": len(self.working.tool_results),
        }


# ============================================================
# 6. 带记忆的 Agent
# ============================================================

class ConversationalAgent:
    """
    An agent with full memory capabilities.
    Maintains context across multiple turns of conversation.
    """

    def __init__(self, model_name: str = "qwen2.5:7b"):
        self.memory = MemoryManager()
        self.memory.short_term.set_system_message(
            "You are a helpful AI assistant. Use the conversation history to maintain context. "
            "Answer in Chinese. If you refer to previous messages, be specific."
        )

        try:
            self.llm = Ollama(model=model_name)
            self._llm_available = True
        except Exception:
            self.llm = None
            self._llm_available = False

    def chat(self, user_message: str) -> str:
        """Process a user message and return a response"""
        # Add user message to memory
        self.memory.add_user_message(user_message)

        # Build context
        context = self.memory.get_context_for_llm()

        if not self._llm_available:
            # Mock response for testing
            response = self._mock_response(user_message)
        else:
            # Real LLM call
            prompt = f"""{context}

Now respond to the latest user message. Be helpful and maintain context from the conversation history.
If the user refers to something mentioned earlier, use that context.

Response:"""
            try:
                response = self.llm.invoke(prompt)
            except Exception as e:
                response = f"[Error: {e}]"

        # Add response to memory
        self.memory.add_assistant_message(response)

        return response

    def _mock_response(self, user_message: str) -> str:
        """Generate a mock response based on conversation history"""
        history = self.memory.short_term.messages

        # Check if user is referring to previous messages
        if any(kw in user_message for kw in ["之前", "刚才", "上面", "previous", "earlier"]):
            prev_messages = [m for m in history if m.role == MessageRole.USER]
            if len(prev_messages) > 1:
                prev = prev_messages[-2]  # Second to last user message
                return f"[Mock] 你之前提到: '{prev.content[:50]}...' 基于此回答你的问题。"

        return f"[Mock] 收到你的消息: {user_message[:50]}... (对话轮次: {len(history)})"

    def save_session(self) -> str:
        """Save current conversation"""
        path = self.memory.save()
        return f"Session saved: {path}"

    def load_session(self, session_id: str) -> None:
        """Load a previous session"""
        self.memory.load(session_id)

    def list_sessions(self) -> list[dict]:
        """List all saved sessions"""
        return self.memory.long_term.list_sessions()

    def interactive(self):
        """Run interactive chat loop"""
        print("\n" + "=" * 60)
        print("Conversational Agent - Interactive Mode")
        print("Commands: 'quit', 'save', 'load <id>', 'sessions', 'memory', 'clear'")
        print("=" * 60)

        while True:
            try:
                user_input = input("\nYou> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == "quit":
                self.memory.save()
                print("Session saved. Goodbye!")
                break
            elif user_input.lower() == "save":
                path = self.save_session()
                print(f"  {path}")
                continue
            elif user_input.lower().startswith("load "):
                session_id = user_input[5:].strip()
                self.load_session(session_id)
                print(f"  Loaded session: {session_id}")
                continue
            elif user_input.lower() == "sessions":
                sessions = self.list_sessions()
                for s in sessions:
                    print(f"  {s['session_id']}: {s['message_count']} messages")
                continue
            elif user_input.lower() == "memory":
                print(f"  Stats: {json.dumps(self.memory.get_stats(), indent=2)}")
                continue
            elif user_input.lower() == "clear":
                self.memory.new_session()
                print("  New session started.")
                continue

            # Chat
            response = self.chat(user_input)
            print(f"\nAgent> {response}")


# ============================================================
# 7. 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 3: Conversation Memory 演示")
    print("=" * 60)

    # ---- Part A: Short-term memory ----
    print("\n--- Part A: 短期记忆 ---")
    stm = ShortTermMemory(max_messages=5)
    stm.set_system_message("You are a helpful assistant.")

    stm.add_message(MessageRole.USER, "你好，我叫小明")
    stm.add_message(MessageRole.ASSISTANT, "你好小明！有什么可以帮你的？")
    stm.add_message(MessageRole.USER, "我在学习 Python")
    stm.add_message(MessageRole.ASSISTANT, "Python 是很好的编程语言！你想学什么方面？")
    stm.add_message(MessageRole.USER, "我想学 AI 开发")
    stm.add_message(MessageRole.ASSISTANT, "推荐从 LangChain 开始")
    stm.add_message(MessageRole.USER, "好的，我该从哪里开始？")  # This should trigger pruning

    print(f"  Stats: {stm.get_stats()}")
    print(f"  Messages:")
    for msg in stm.get_messages():
        print(f"    {msg}")

    # ---- Part B: Working memory ----
    print("\n--- Part B: 工作记忆 ---")
    wm = WorkingMemory()
    wm.add_fact("user_name", "小明")
    wm.add_fact("learning_topic", "AI 开发")
    wm.add_fact("skill_level", "beginner")

    wm.add_tool_result("read_file", {"path": "readme.md"}, "# Project README...", True)
    wm.add_tool_result("search_text", {"pattern": "def "}, "Found 5 functions", True)

    wm.add_note("User wants to learn LangChain")
    wm.add_note("Recommended starting with Week 1 exercises")

    print(wm.get_summary())

    # ---- Part C: Long-term memory ----
    print("\n--- Part C: 长期记忆 ---")
    ltm = LongTermMemory(storage_dir="/tmp/agent_memory_test")

    # Save a session
    messages = [
        Message(role=MessageRole.USER, content="什么是 RAG？"),
        Message(role=MessageRole.ASSISTANT, content="RAG 是检索增强生成..."),
        Message(role=MessageRole.USER, content="它和 Agent 有什么关系？"),
        Message(role=MessageRole.ASSISTANT, content="Agent 可以把 RAG 作为工具使用..."),
    ]
    path = ltm.save_session("test_session_001", messages)
    print(f"  Saved to: {path}")

    # Load session
    loaded = ltm.load_session("test_session_001")
    print(f"  Loaded {len(loaded)} messages")
    for msg in loaded:
        print(f"    {msg}")

    # Search history
    results = ltm.search_history("RAG")
    print(f"\n  Search 'RAG': {len(results)} results")
    for r in results:
        print(f"    [{r['role']}] {r['content'][:60]}...")

    # List sessions
    sessions = ltm.list_sessions()
    print(f"\n  Sessions: {len(sessions)}")

    # Cleanup
    ltm.delete_session("test_session_001")

    # ---- Part D: Memory Manager ----
    print("\n--- Part D: 统一记忆管理器 ---")
    mm = MemoryManager(storage_dir="/tmp/agent_memory_test")
    mm.short_term.set_system_message("You are a helpful assistant.")

    mm.add_user_message("什么是 LangGraph？")
    mm.working.add_fact("topic", "LangGraph")
    mm.add_assistant_message("LangGraph 是一个用于构建有状态 Agent 的框架...")
    mm.add_user_message("它和 LangChain 什么关系？")

    context = mm.get_context_for_llm()
    print(f"  Context for LLM:\n{context}")
    print(f"\n  Stats: {json.dumps(mm.get_stats(), indent=2)}")

    # ---- Part E: Conversational Agent (mock) ----
    print("\n--- Part E: 对话 Agent ---")
    agent = ConversationalAgent()

    responses = []
    test_messages = [
        "你好，我叫小明",
        "我想学习 Agent 开发",
        "你还记得我叫什么名字吗？",
        "之前我说想学什么来着？",
    ]

    for msg in test_messages:
        print(f"\n  You> {msg}")
        response = agent.chat(msg)
        responses.append(response)
        print(f"  Agent> {response}")

    print(f"\n  Memory stats: {json.dumps(agent.memory.get_stats(), indent=2)}")


    # ============================================================
    # 练习题
    # ============================================================

    print("\n" + "=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 实现 "摘要式记忆"
    # 当短期记忆满了，不是简单丢弃旧消息
    # 而是用 LLM 把旧消息总结成一段摘要
    # 然后把摘要作为系统消息的一部分保留

    # TODO 2: 实现 "实体记忆" (Entity Memory)
    # 从对话中提取关键实体（人名、技术名词、日期）
    # 维护一个实体表，当用户提到时自动关联
    # 例如：用户说"小明"，自动关联到"正在学 AI 的用户"

    # TODO 3: 实现对话导出功能
    # 把对话历史导出为 Markdown 格式
    # 包含时间戳、角色标识和消息内容
