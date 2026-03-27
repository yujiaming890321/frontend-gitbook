"""
Day 3: 类与面向对象 — class、__init__、继承、dataclass
AI 开发中常用：定义数据结构、封装 API 客户端、构建 Agent 状态
"""

# ============================================================
# 1. 基本类
# JS: class Foo { constructor() {} }  →  Python: class Foo: def __init__(self)
# ============================================================

class ChatMessage:
    """Represent a single chat message in OpenAI format"""

    def __init__(self, role: str, content: str):
        # JS 的 this.role = role  →  Python 的 self.role = role
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        """Convert to dict for API request"""
        return {"role": self.role, "content": self.content}

    def __repr__(self) -> str:
        """Debug-friendly string representation (like JS toString())"""
        return f"ChatMessage(role='{self.role}', content='{self.content[:20]}...')"

msg = ChatMessage("user", "什么是 RAG？")
print(msg)           # ChatMessage(role='user', content='什么是 RAG？...')
print(msg.to_dict()) # {'role': 'user', 'content': '什么是 RAG？'}


# ============================================================
# 2. 继承
# JS: class Child extends Parent  →  Python: class Child(Parent)
# ============================================================

class BaseLLMClient:
    """Base class for LLM API clients"""

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url

    def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError("Subclass must implement chat()")

    def _format_request(self, messages: list[dict]) -> dict:
        """Build the request payload"""
        return {
            "model": self.model,
            "messages": messages,
        }


class OllamaClient(BaseLLMClient):
    """Client for local Ollama server"""

    def __init__(self, model: str = "qwen2.5:7b"):
        # JS: super(model, url)  →  Python: super().__init__(model, url)
        super().__init__(model, "http://localhost:11434/v1")

    def chat(self, messages: list[dict]) -> str:
        request = self._format_request(messages)
        # Simulate API call
        return f"[Ollama/{self.model}] 模拟回复: 收到 {len(messages)} 条消息"


class DeepSeekClient(BaseLLMClient):
    """Client for DeepSeek API"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        super().__init__(model, "https://api.deepseek.com")
        self.api_key = api_key

    def chat(self, messages: list[dict]) -> str:
        request = self._format_request(messages)
        return f"[DeepSeek/{self.model}] 模拟回复: 收到 {len(messages)} 条消息"


# 多态：同样的接口，不同的实现
clients = [
    OllamaClient(),
    DeepSeekClient(api_key="fake-key"),
]

messages = [{"role": "user", "content": "你好"}]
for client in clients:
    print(client.chat(messages))


# ============================================================
# 3. dataclass — Python 的利器
# 类似 TypeScript 的 interface + 自动生成 constructor
# AI 开发中大量使用：定义配置、API 参数、Agent 状态
# ============================================================

from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """Configuration for LLM API calls — auto-generates __init__, __repr__, __eq__"""
    model: str = "qwen2.5:7b"
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False
    stop_sequences: list[str] = field(default_factory=list)

# 不需要写 __init__，自动生成！
config1 = LLMConfig()
config2 = LLMConfig(model="deepseek-chat", temperature=0.3)
print(config1)
print(config2)
print(f"config1 == config2: {config1 == config2}")  # 自动生成 __eq__


@dataclass
class Document:
    """Represent a document chunk for RAG"""
    content: str
    source: str
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        """Property — like JS getter: get charCount() {}"""
        return len(self.content)

    def preview(self, length: int = 50) -> str:
        """Return a truncated preview of the content"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + "..."

doc = Document(
    content="RAG（检索增强生成）是一种结合检索和生成的 AI 技术，它通过从知识库中检索相关文档来增强 LLM 的回答质量。",
    source="docs/14-AI/AI-Application-Engineering/2-RAG.md",
    metadata={"title": "RAG 入门"}
)
print(f"文档预览: {doc.preview()}")
print(f"字符数: {doc.char_count}")


# ============================================================
# 4. 特殊方法 (Magic Methods / Dunder Methods)
# 类似 JS 的 Symbol.iterator、toString 等
# ============================================================

@dataclass
class SearchResults:
    """Container for search results with Python magic methods"""
    results: list[Document] = field(default_factory=list)

    def __len__(self) -> int:
        """Enable len(results) — like JS: results.length"""
        return len(self.results)

    def __getitem__(self, index):
        """Enable results[0] — like JS array indexing"""
        return self.results[index]

    def __iter__(self):
        """Enable for doc in results — like JS Symbol.iterator"""
        return iter(self.results)

    def __contains__(self, source: str) -> bool:
        """Enable 'file.md' in results — membership test"""
        return any(doc.source == source for doc in self.results)

# 使用起来像内置类型一样自然
results = SearchResults(results=[
    Document("内容1", "doc1.md"),
    Document("内容2", "doc2.md"),
    Document("内容3", "doc3.md"),
])

print(f"结果数量: {len(results)}")
print(f"第一个: {results[0]}")
print(f"包含 doc2.md: {'doc2.md' in results}")

for doc in results:
    print(f"  - {doc.source}: {doc.preview(10)}")


# ============================================================
# 5. AI 场景：Agent 状态管理
# ============================================================

from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentState:
    """Manage the state of an AI agent across execution steps"""
    question: str
    status: AgentStatus = AgentStatus.IDLE
    thoughts: list[str] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)
    answer: str = ""
    max_steps: int = 5

    @property
    def step_count(self) -> int:
        return len(self.actions)

    @property
    def can_continue(self) -> bool:
        """Check if agent hasn't exceeded max steps"""
        return self.step_count < self.max_steps and self.status != AgentStatus.ERROR

    def add_thought(self, thought: str):
        """Record a thinking step"""
        self.thoughts.append(thought)
        self.status = AgentStatus.THINKING

    def add_action(self, tool: str, input_data: str, output: str):
        """Record a tool action"""
        self.actions.append({"tool": tool, "input": input_data, "output": output})
        self.status = AgentStatus.ACTING

    def finish(self, answer: str):
        """Mark agent as done with final answer"""
        self.answer = answer
        self.status = AgentStatus.DONE


# 模拟 Agent 执行
state = AgentState(question="RAG 和 Fine-tuning 有什么区别？")
state.add_thought("需要先搜索相关文档")
state.add_action("search_docs", "RAG vs Fine-tuning", "找到 3 篇相关文档")
state.add_thought("根据文档总结区别")
state.finish("RAG 是检索增强，Fine-tuning 是模型微调，适用场景不同...")

print(f"\n状态: {state.status.value}")
print(f"思考步骤: {len(state.thoughts)}")
print(f"工具调用: {state.step_count}")
print(f"回答: {state.answer[:50]}...")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 用 dataclass 定义一个 Conversation 类
# - messages: list[ChatMessage]  (用上面定义的 ChatMessage)
# - model: str (默认 "qwen2.5:7b")
# - 方法 add_message(role, content): 添加消息
# - 方法 to_api_format(): 返回 [{"role": ..., "content": ...}, ...]
# - property token_estimate: 粗略估算 token 数（中文 1 字 ≈ 2 tokens）

# @dataclass
# class Conversation:
#     ???

# TODO 2: 继承 BaseLLMClient，实现一个 GroqClient
# base_url = "https://api.groq.com/openai/v1"
# 默认 model = "llama-3.1-8b-instant"
# 需要 api_key 参数

# class GroqClient(BaseLLMClient):
#     ???

# TODO 3: 给 SearchResults 添加一个 top(n) 方法
# 假设 Document 有一个 score 字段，返回分数最高的 n 个结果
# 提示：可以用 sorted() + lambda
