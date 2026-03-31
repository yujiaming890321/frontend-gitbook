"""
Day 2: Pydantic — 数据校验和序列化
AI 开发中的标配：定义 API 请求/响应结构、校验 LLM 输出、配置管理
你已经熟悉 zod，pydantic 就是 Python 版的 zod
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

# ============================================================
# 1. 基本模型定义
# JS/zod: z.object({ name: z.string(), age: z.number() })
# Python/pydantic: class User(BaseModel): name: str; age: int
# ============================================================

class User(BaseModel):
    """Basic user model — like zod schema"""
    name: str
    age: int
    email: Optional[str] = None  # Optional field with default None

# Create instance — pydantic auto-validates types
user = User(name="Alice", age=30)
print(user)
print(user.model_dump())  # → dict, like zod .parse() result

# Type coercion — pydantic converts compatible types automatically
user2 = User(name="Bob", age="25")  # str "25" → int 25
print(f"age type: {type(user2.age)}")  # <class 'int'>

# Validation error — like zod throwing ZodError
try:
    bad_user = User(name="Charlie", age="not a number")
except Exception as e:
    print(f"\n校验错误: {e}")


# ============================================================
# 2. AI 场景：定义 LLM API 请求/响应结构
# ============================================================

class ChatMessage(BaseModel):
    """Single message in OpenAI chat format"""
    role: Literal["system", "user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    """Request payload for LLM API — validates before sending"""
    model: str = "qwen2.5:7b"
    messages: list[ChatMessage]
    temperature: float = Field(default=0.7, ge=0, le=2)  # ge=0, le=2 → 0 <= temp <= 2
    max_tokens: int = Field(default=1000, gt=0)
    stream: bool = False

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class Choice(BaseModel):
    message: ChatMessage
    finish_reason: str

class ChatResponse(BaseModel):
    """Response from LLM API — parse and validate the response"""
    choices: list[Choice]
    usage: Usage

# Build a validated request
request = ChatRequest(
    messages=[
        ChatMessage(role="system", content="你是一个有用的助手"),
        ChatMessage(role="user", content="什么是 RAG？"),
    ],
    temperature=0.3,
)
print(f"\n请求: {request.model_dump_json(indent=2)}")

# Parse API response
raw_response = {
    "choices": [
        {
            "message": {"role": "assistant", "content": "RAG 是检索增强生成..."},
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 20, "completion_tokens": 50, "total_tokens": 70}
}
response = ChatResponse(**raw_response)
print(f"回复: {response.choices[0].message.content}")
print(f"Token 用量: {response.usage.total_tokens}")


# ============================================================
# 3. Field — 字段约束
# JS/zod: z.string().min(1).max(100)
# Python/pydantic: Field(min_length=1, max_length=100)
# ============================================================

class DocumentChunk(BaseModel):
    """RAG document chunk with field constraints"""
    content: str = Field(min_length=1, description="The text content of this chunk")
    source: str = Field(description="Source file path")
    chunk_index: int = Field(ge=0, description="Zero-based index of this chunk")
    score: float = Field(default=0.0, ge=0, le=1, description="Relevance score")
    metadata: dict = Field(default_factory=dict)

chunk = DocumentChunk(
    content="RAG 是一种结合检索和生成的技术...",
    source="docs/rag.md",
    chunk_index=0,
    score=0.92,
)
print(f"\nChunk: {chunk}")

# Field validation catches errors
try:
    bad_chunk = DocumentChunk(content="", source="test.md", chunk_index=-1)
except Exception as e:
    print(f"字段约束错误: {e}")


# ============================================================
# 4. Validator — 自定义校验
# JS/zod: z.string().refine(val => val.startsWith("sk-"))
# Python/pydantic: @field_validator("field_name")
# ============================================================

class LLMConfig(BaseModel):
    """Configuration with custom validation rules"""
    api_key: str
    model: str = "qwen2.5:7b"
    temperature: float = 0.7
    chunk_size: int = 500
    chunk_overlap: int = 50

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """API key must start with 'sk-' prefix"""
        if not v.startswith("sk-"):
            raise ValueError("API key must start with 'sk-'")
        return v

    @model_validator(mode="after")
    def validate_chunk_settings(self):
        """Chunk overlap must be less than chunk size"""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return self

# Valid config
config = LLMConfig(api_key="sk-abc123", chunk_size=500, chunk_overlap=50)
print(f"\n配置: {config}")

# Invalid config
try:
    bad_config = LLMConfig(api_key="invalid-key")
except Exception as e:
    print(f"自定义校验错误: {e}")

try:
    bad_config = LLMConfig(api_key="sk-abc", chunk_size=100, chunk_overlap=200)
except Exception as e:
    print(f"跨字段校验错误: {e}")


# ============================================================
# 5. 嵌套模型和序列化
# 和 zod 嵌套 schema 一样
# ============================================================

class ToolCall(BaseModel):
    """Function call from LLM (Function Calling)"""
    name: str
    arguments: dict

class AgentStep(BaseModel):
    """Single step in agent execution"""
    step_number: int
    thought: str
    action: Optional[ToolCall] = None
    observation: Optional[str] = None

class AgentResult(BaseModel):
    """Complete agent execution result"""
    question: str
    steps: list[AgentStep]
    final_answer: str
    total_tokens: int = 0

# Build a complex nested structure
result = AgentResult(
    question="北京今天天气怎么样？",
    steps=[
        AgentStep(
            step_number=1,
            thought="需要查询天气信息",
            action=ToolCall(name="search_weather", arguments={"city": "北京"}),
            observation="北京今天晴，25°C",
        ),
        AgentStep(
            step_number=2,
            thought="已获得天气信息，可以回答",
        ),
    ],
    final_answer="北京今天天气晴朗，气温 25°C。",
    total_tokens=150,
)

# Serialization
print(f"\nJSON 输出:\n{result.model_dump_json(indent=2)}")

# Deserialization — parse from dict
raw_data = result.model_dump()
parsed = AgentResult(**raw_data)
print(f"解析后步骤数: {len(parsed.steps)}")


# ============================================================
# 6. pydantic vs zod 对比速查表
# ============================================================

"""
zod                                  pydantic                           说明
───                                  ────────                           ────
z.object({...})                      class Foo(BaseModel):              定义 schema
z.string()                           str                                字符串类型
z.number().min(0).max(1)             Field(ge=0, le=1)                  数字约束
z.string().optional()                Optional[str] = None               可选字段
z.enum(["a", "b"])                   Literal["a", "b"]                  枚举
z.array(z.string())                  list[str]                          数组
schema.parse(data)                   Model(**data)                      解析+校验
schema.safeParse(data)               try: Model(**data)                 安全解析
z.string().refine(fn)                @field_validator("field")          自定义校验
z.infer<typeof schema>               (直接用 class 本身)                 类型推断
data.toJSON()                        model.model_dump_json()            序列化
JSON.parse(str)                      Model.model_validate_json(str)     从 JSON 解析

关键区别：
- zod 是运行时 + 编译时校验
- pydantic 是纯运行时校验（配合 mypy 可以做静态检查）
- pydantic v2 性能极好（Rust 核心）
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 定义一个 RAGQuery pydantic 模型
# - query: str (必填, 至少 1 个字符)
# - top_k: int (默认 3, 范围 1-20)
# - threshold: float (默认 0.7, 范围 0-1)
# - filter_sources: Optional[list[str]] (可选, 限制搜索的文件)
# 并写一个 validator: 如果 top_k > 10, 自动将 threshold 提高到 0.8

# class RAGQuery(BaseModel):
#     ???

# TODO 2: 用 pydantic 解析以下 LLM 的 JSON 输出
# 定义合适的模型来接收并校验这个结构
llm_output = {
    "intent": "code_review",
    "confidence": 0.95,
    "issues": [
        {"severity": "high", "line": 42, "message": "可能的空指针"},
        {"severity": "low", "line": 10, "message": "变量命名不规范"},
    ],
    "summary": "代码整体质量良好，有一个高风险问题需要修复"
}
# parsed = CodeReviewResult(**llm_output)

# TODO 3: 写一个 Settings 模型，用 pydantic 管理 AI 应用的配置
# - 从环境变量读取（提示：pydantic-settings 库）
# - 支持 .env 文件
# - 包含: api_key, model, temperature, docs_dir 等字段
