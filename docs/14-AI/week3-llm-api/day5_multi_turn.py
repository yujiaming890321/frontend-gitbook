"""
Day 5: 多轮对话 — 管理 messages 历史
AI 应用的核心挑战：如何维护对话上下文
LLM 本身无状态，上下文全靠 messages 数组传递
"""

from openai import OpenAI
from dataclasses import dataclass, field
from typing import Literal

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# ============================================================
# 1. 基本多轮对话
# ============================================================

def basic_multi_turn():
    """Simple multi-turn conversation by accumulating messages"""
    messages = [
        {"role": "system", "content": "你是一个 Python 编程助手，回答简洁。"},
    ]

    # Simulate a 3-turn conversation
    user_inputs = [
        "Python 的列表和元组有什么区别？",
        "那字典呢？",
        "这三种数据结构分别什么时候用？",
    ]

    print("--- 多轮对话 ---")
    for user_input in user_inputs:
        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model="qwen2.5:7b",
                messages=messages,
            )
            assistant_reply = response.choices[0].message.content

            # Add assistant reply to history — this is crucial for context
            messages.append({"role": "assistant", "content": assistant_reply})

            print(f"\n用户: {user_input}")
            print(f"助手: {assistant_reply[:150]}...")
        except Exception as e:
            print(f"[错误: {e}]")
            break

    print(f"\n对话历史长度: {len(messages)} 条消息")

basic_multi_turn()


# ============================================================
# 2. Conversation 类 — 封装多轮对话
# ============================================================

@dataclass
class Conversation:
    """
    Manage a multi-turn conversation with an LLM.
    Handles message history, token limits, and context window.
    """
    system_prompt: str = "你是一个有用的助手"
    model: str = "qwen2.5:7b"
    max_history: int = 20  # Max messages to keep (prevent context overflow)
    messages: list[dict] = field(default_factory=list)

    def __post_init__(self):
        """Initialize with system message"""
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def chat(self, user_input: str) -> str:
        """Send a message and get a response, maintaining history"""
        self.messages.append({"role": "user", "content": user_input})

        # Trim history if too long — keep system + recent messages
        self._trim_history()

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )
            reply = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"[错误: {e}]"

    def _trim_history(self):
        """Keep conversation within max_history limit"""
        if len(self.messages) > self.max_history:
            # Always keep system message + last N messages
            system = self.messages[0]
            recent = self.messages[-(self.max_history - 1):]
            self.messages = [system] + recent

    def clear(self):
        """Reset conversation history"""
        self.__post_init__()

    @property
    def turn_count(self) -> int:
        """Count conversation turns (user-assistant pairs)"""
        return sum(1 for m in self.messages if m["role"] == "user")

    @property
    def estimated_tokens(self) -> int:
        """Rough token estimate (1 Chinese char ≈ 2 tokens, 1 English word ≈ 1.3 tokens)"""
        total_chars = sum(len(m["content"]) for m in self.messages)
        return int(total_chars * 1.5)


# Usage
print("\n--- Conversation 类 ---")
conv = Conversation(system_prompt="你是 Python 专家，回答简洁，不超过 2 句话。")
questions = ["什么是装饰器？", "给一个简单例子", "它和高阶函数有什么关系？"]

for q in questions:
    reply = conv.chat(q)
    print(f"\n[Turn {conv.turn_count}] 用户: {q}")
    print(f"助手: {reply[:150]}...")

print(f"\n估算 token 量: {conv.estimated_tokens}")


# ============================================================
# 3. 上下文窗口管理策略
# ============================================================

"""
LLM 有上下文窗口限制（如 qwen2.5:7b 是 32K tokens）
当对话太长时，需要策略来管理：

策略 1: 截断（最简单）
  保留 system + 最近 N 条消息
  ✅ 简单  ❌ 丢失早期上下文

策略 2: 摘要压缩
  把旧对话用 LLM 总结成一条 system message
  ✅ 保留关键信息  ❌ 多一次 LLM 调用

策略 3: 滑动窗口 + 关键信息提取
  保留最近 N 条 + 从旧对话中提取的关键点
  ✅ 平衡效果  ❌ 实现复杂
"""

def summarize_and_compress(conv: Conversation) -> str:
    """Compress old messages into a summary to save context window"""
    if len(conv.messages) <= 5:
        return "对话太短，不需要压缩"

    # Take old messages (skip system + keep recent 4)
    old_messages = conv.messages[1:-4]
    if not old_messages:
        return "没有需要压缩的旧消息"

    old_text = "\n".join(f"{m['role']}: {m['content']}" for m in old_messages)

    try:
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": "用 2-3 句话总结以下对话的要点："},
                {"role": "user", "content": old_text},
            ],
            temperature=0,
            max_tokens=200,
        )
        summary = response.choices[0].message.content

        # Replace old messages with summary
        system = conv.messages[0]
        recent = conv.messages[-4:]
        conv.messages = [
            system,
            {"role": "system", "content": f"之前的对话摘要：{summary}"},
            *recent,
        ]
        return summary
    except Exception as e:
        return f"[压缩失败: {e}]"


# ============================================================
# 4. 对话分支 — 保存和恢复
# ============================================================

import copy

def conversation_branching():
    """Save and restore conversation states — like git branches"""
    conv = Conversation(system_prompt="你是编程助手")
    conv.chat("Python 和 JavaScript 哪个更适合初学者？")

    # Save state — like git commit
    saved_state = copy.deepcopy(conv.messages)

    # Branch A: continue with Python
    conv.chat("好的，我选 Python，从哪里开始学？")
    branch_a_reply = conv.messages[-1]["content"]

    # Restore and take Branch B
    conv.messages = saved_state
    conv.chat("好的，我选 JavaScript，从哪里开始学？")
    branch_b_reply = conv.messages[-1]["content"]

    print("\n--- 对话分支 ---")
    print(f"分支 A (Python): {branch_a_reply[:80]}...")
    print(f"分支 B (JS):     {branch_b_reply[:80]}...")

conversation_branching()


# ============================================================
# 5. 实际项目模式：对话 + 工具结果
# ============================================================

def conversation_with_tool_results():
    """
    In agent systems, tool outputs are injected into the conversation.
    This shows how messages history includes tool results.
    """
    messages = [
        {"role": "system", "content": "你是一个研究助手，可以搜索文档。"},
        {"role": "user", "content": "什么是 RAG？"},
        {"role": "assistant", "content": "让我搜索一下相关文档..."},
        # Tool result injected as a user message (or system message)
        {"role": "user", "content": "[搜索结果]\n"
            "文档1: RAG（检索增强生成）是一种将检索和生成结合的技术。\n"
            "文档2: RAG 先从知识库检索相关文档，再用 LLM 生成回答。"},
        {"role": "assistant", "content": "根据搜索结果，RAG 是..."},
        {"role": "user", "content": "它和 Fine-tuning 有什么区别？"},
    ]

    print("\n--- 包含工具结果的对话 ---")
    print(f"消息数: {len(messages)}")
    for m in messages:
        prefix = {"system": "SYS", "user": "USR", "assistant": "BOT"}[m["role"]]
        print(f"  [{prefix}] {m['content'][:60]}...")

conversation_with_tool_results()


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 给 Conversation 类添加 save_to_file / load_from_file 方法
# 把对话历史保存为 JSON 文件，下次可以恢复
# 提示：用 json.dump / json.load

# TODO 2: 实现"对话摘要"功能
# 当对话超过 10 轮时，自动把前面的对话总结成摘要
# 放入 system message 中，保持上下文
# 提示：用上面的 summarize_and_compress 函数

# TODO 3: 实现一个 ConversationPool 类
# 管理多个独立的对话（类似聊天应用的多个会话）
# 支持：create_conversation(id), get_conversation(id), list_conversations()
# 每个对话有独立的 messages 历史

# class ConversationPool:
#     ???
