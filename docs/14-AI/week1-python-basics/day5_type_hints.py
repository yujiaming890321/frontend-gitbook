"""
Day 5: 类型提示 — typing 模块
你已经习惯 TypeScript 的类型系统，Python 的类型提示会很亲切
AI 开发中大量使用：定义 API 数据结构、Agent 状态、函数签名
"""

from typing import (
    Optional,
    Union,
    Literal,
    TypedDict,
    Any,
    Callable,
)
from dataclasses import dataclass

# ============================================================
# 1. 基本类型提示
# TS: function greet(name: string): string
# Python: def greet(name: str) -> str
# ============================================================

def greet(name: str) -> str:
    return f"Hello, {name}!"

# 基本类型对应
# TS: string    → Python: str
# TS: number    → Python: int / float
# TS: boolean   → Python: bool
# TS: string[]  → Python: list[str]
# TS: null      → Python: None

# 集合类型（Python 3.9+ 可以直接用小写）
def process_tags(tags: list[str]) -> set[str]:
    """Remove duplicates from tag list"""
    return set(tags)

def get_config() -> dict[str, Any]:
    """Return configuration dictionary"""
    return {"model": "qwen2.5:7b", "temperature": 0.7}

scores: list[float] = [0.85, 0.92, 0.78]
word_count: dict[str, int] = {"hello": 5, "world": 5}


# ============================================================
# 2. Optional 和 Union
# TS: string | null      → Python: Optional[str] 或 str | None
# TS: string | number    → Python: Union[str, int] 或 str | int
# ============================================================

# Optional = 可能是 None（和 TS 的 string | null 一样）
def find_document(query: str) -> Optional[dict]:
    """Search for a document, return None if not found"""
    if query == "RAG":
        return {"title": "RAG 入门", "content": "..."}
    return None

# Union = 多种类型之一（和 TS 的 union type 一样）
# Python 3.10+ 可以用 | 语法
def parse_input(value: str | int) -> str:
    """Accept either string or int input"""
    return str(value)

# AI 场景：LLM 返回值可能是字符串或结构化数据
def get_llm_output(structured: bool = False) -> str | dict:
    """Return raw text or parsed JSON from LLM"""
    if structured:
        return {"answer": "RAG 是检索增强生成", "confidence": 0.95}
    return "RAG 是检索增强生成"


# ============================================================
# 3. Literal — 字面量类型
# TS: type Role = "system" | "user" | "assistant"
# Python: Literal["system", "user", "assistant"]
# ============================================================

Role = Literal["system", "user", "assistant"]

def create_message(role: Role, content: str) -> dict:
    """Create a message with a validated role"""
    return {"role": role, "content": content}

# IDE 会提示 role 只能是这三个值
msg = create_message("user", "你好")
# create_message("admin", "你好")  # IDE 会警告


# ============================================================
# 4. TypedDict — 结构化字典
# TS: interface Message { role: string; content: string }
# Python: class Message(TypedDict): role: str; content: str
# ============================================================

class Message(TypedDict):
    """OpenAI message format — like TS interface"""
    role: str
    content: str

class ChatCompletionChoice(TypedDict):
    message: Message
    finish_reason: str

class Usage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(TypedDict):
    """Full API response type — nested TypedDict"""
    choices: list[ChatCompletionChoice]
    usage: Usage

# TypedDict lets you define the shape of dict data
# IDE will auto-complete keys and check types
def parse_response(response: ChatCompletionResponse) -> str:
    """Extract content from a typed API response"""
    return response["choices"][0]["message"]["content"]

# Example usage
response: ChatCompletionResponse = {
    "choices": [
        {
            "message": {"role": "assistant", "content": "你好！"},
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
}
print(parse_response(response))


# ============================================================
# 5. Callable — 函数类型
# TS: (prompt: string) => Promise<string>
# Python: Callable[[str], str]
# ============================================================

# Callable[[参数类型], 返回类型]
def apply_to_chunks(
    chunks: list[str],
    processor: Callable[[str], str]
) -> list[str]:
    """Apply a processing function to each chunk"""
    return [processor(chunk) for chunk in chunks]

# 使用
chunks = ["  hello  ", "  world  "]
cleaned = apply_to_chunks(chunks, str.strip)
print(cleaned)  # ['hello', 'world']

# AI 场景：可插拔的 embedding 函数
EmbeddingFunc = Callable[[str], list[float]]

def build_index(
    documents: list[str],
    embed_fn: EmbeddingFunc
) -> list[list[float]]:
    """Build a vector index using a configurable embedding function"""
    return [embed_fn(doc) for doc in documents]


# ============================================================
# 6. 泛型 — 类型变量
# TS: function first<T>(arr: T[]): T
# Python: def first[T](arr: list[T]) -> T  (3.12+)
# ============================================================

# Python 3.12+ 的新语法（更接近 TS）
# def first[T](items: list[T]) -> T:
#     return items[0]

# Python 3.9-3.11 用 TypeVar
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    """Return the first item of a list, preserving type"""
    return items[0]

# 类型推断和 TS 一样
name = first(["a", "b", "c"])    # 推断为 str
number = first([1, 2, 3])        # 推断为 int


# ============================================================
# 7. dataclass + 类型提示（AI 开发的最佳实践）
# ============================================================

@dataclass
class RAGConfig:
    """Typed configuration for RAG pipeline — combines dataclass with type hints"""
    # Required fields
    docs_dir: str
    embedding_model: str

    # Optional fields with defaults
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3
    similarity_threshold: float = 0.7
    llm_model: str = "qwen2.5:7b"
    temperature: float = 0.3

    def validate(self) -> bool:
        """Runtime validation (type hints alone are not enforced at runtime)"""
        assert self.chunk_size > 0, "chunk_size must be positive"
        assert 0 <= self.temperature <= 2, "temperature must be 0-2"
        assert self.chunk_overlap < self.chunk_size, "overlap must be less than chunk_size"
        return True

config = RAGConfig(
    docs_dir="./docs",
    embedding_model="nomic-embed-text",
    chunk_size=800,
)
print(config)
config.validate()


# ============================================================
# 8. TS vs Python 类型对比速查表
# ============================================================

"""
TypeScript                          Python                          说明
──────────                          ──────                          ────
string                              str                             字符串
number                              int / float                     数字
boolean                             bool                            布尔
string[]                            list[str]                       数组/列表
[string, number]                    tuple[str, int]                 元组
Record<string, number>              dict[str, int]                  字典
string | null                       Optional[str] / str | None      可空
string | number                     Union[str, int] / str | int     联合
"a" | "b" | "c"                     Literal["a", "b", "c"]          字面量
interface Foo { x: string }         class Foo(TypedDict): x: str    结构化对象
(x: string) => number              Callable[[str], int]             函数类型
T                                   TypeVar("T")                    泛型
any                                 Any                             任意类型
unknown                             object                          未知类型
void                                None                            无返回值
Partial<Foo>                        没有直接等价（用 Optional 逐字段） 部分可选

重要区别：
- TS 的类型在编译时检查，Python 的类型提示默认不强制
- 要在 Python 中强制检查，用 pydantic 或 mypy
- AI 项目中通常用 pydantic 做运行时校验（第 2 周学习）
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 用 TypedDict 定义一个 ToolCall 类型
# 包含: name (str), arguments (dict[str, Any]), id (str)
# 然后写一个函数 execute_tool(tool_call: ToolCall) -> str

# class ToolCall(TypedDict):
#     ???

# TODO 2: 用 Literal 和 TypedDict 定义 Agent 的 action 类型
# action_type: "search" | "calculate" | "respond"
# 每种 action_type 对应不同的 payload 结构
# 提示：可以用 Union 组合多个 TypedDict

# TODO 3: 写一个泛型函数 batch_process
# 接收 items: list[T] 和 processor: Callable[[T], R]
# 返回 list[R]
# 用它来批量处理文档字符串，转成 Document 对象
