"""
Day 3: 环境变量管理 + JSON 处理
AI 开发中常用：管理 API Key、加载配置、解析 LLM 输出
你已经熟悉 dotenv 和 JSON，Python 的用法几乎一样
"""

import json
import os
from pathlib import Path

# ============================================================
# 1. python-dotenv — 环境变量管理
# JS: require("dotenv").config()  →  Python: load_dotenv()
# ============================================================

from dotenv import load_dotenv

# Load .env file (looks for .env in current directory and parents)
# JS equivalent: require("dotenv").config()
load_dotenv()

# Read env vars — same as JS process.env.VARIABLE_NAME
api_key = os.getenv("DEEPSEEK_API_KEY", "not-set")
model = os.getenv("LLM_MODEL", "qwen2.5:7b")
temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

print(f"API Key: {api_key[:10]}..." if len(api_key) > 10 else f"API Key: {api_key}")
print(f"Model: {model}")
print(f"Temperature: {temperature}")

# Create a sample .env file for demonstration
sample_env = """
# LLM API Configuration
DEEPSEEK_API_KEY=sk-your-key-here
DASHSCOPE_API_KEY=sk-your-dashscope-key

# Model settings
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1000

# RAG settings
DOCS_DIR=./docs
CHUNK_SIZE=500
CHUNK_OVERLAP=50
CHROMA_DB_PATH=./chroma_db
""".strip()

print(f"\n示例 .env 文件内容:\n{sample_env}")


# ============================================================
# 2. 配置管理最佳实践
# AI 项目中推荐：pydantic + dotenv 组合
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional


class AppConfig(BaseModel):
    """Application config loaded from environment variables"""
    # LLM settings
    deepseek_api_key: str = Field(default="not-set")
    dashscope_api_key: str = Field(default="not-set")
    llm_model: str = Field(default="qwen2.5:7b")
    llm_temperature: float = Field(default=0.7, ge=0, le=2)
    llm_max_tokens: int = Field(default=1000, gt=0)

    # RAG settings
    docs_dir: str = Field(default="./docs")
    chunk_size: int = Field(default=500, gt=0)
    chunk_overlap: int = Field(default=50, ge=0)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load config from environment variables"""
        load_dotenv()
        return cls(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "not-set"),
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", "not-set"),
            llm_model=os.getenv("LLM_MODEL", "qwen2.5:7b"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            docs_dir=os.getenv("DOCS_DIR", "./docs"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
        )

config = AppConfig.from_env()
print(f"\n配置: {config.model_dump_json(indent=2)}")


# ============================================================
# 3. JSON 处理
# JS: JSON.stringify / JSON.parse  →  Python: json.dumps / json.loads
# ============================================================

# --- 序列化 (Python object → JSON string) ---
# JS: JSON.stringify(obj)  →  Python: json.dumps(obj)

data = {
    "model": "qwen2.5:7b",
    "messages": [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"},
    ],
    "temperature": 0.7,
}

# Basic serialization
json_str = json.dumps(data)
print(f"\nJSON string: {json_str[:80]}...")

# Pretty print — like JSON.stringify(obj, null, 2)
pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
print(f"\n格式化 JSON:\n{pretty_json}")

# ensure_ascii=False is important for Chinese characters
# Without it: "你好" → "\\u4f60\\u597d"
# With it:    "你好" → "你好"

# --- 反序列化 (JSON string → Python object) ---
# JS: JSON.parse(str)  →  Python: json.loads(str)

json_text = '{"name": "Alice", "scores": [0.85, 0.92]}'
parsed = json.loads(json_text)
print(f"\n解析: {parsed}")
print(f"类型: {type(parsed)}")  # <class 'dict'>

# --- 文件读写 ---
# JS: fs.readFileSync / fs.writeFileSync with JSON.parse/stringify

# Write JSON file
output_path = Path("/tmp/ai_config.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"\n写入文件: {output_path}")

# Read JSON file
with open(output_path, "r", encoding="utf-8") as f:
    loaded = json.load(f)
print(f"读取文件: {loaded['model']}")


# ============================================================
# 4. AI 场景：解析 LLM 的 JSON 输出
# LLM 有时返回的 JSON 不是标准格式，需要容错处理
# ============================================================

def parse_llm_json(text: str) -> dict | None:
    """
    Parse JSON from LLM output, handling common issues like
    markdown code blocks and trailing text.
    """
    # Strip markdown code block wrapper if present
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return None


# LLM often wraps JSON in markdown code blocks
llm_outputs = [
    # Clean JSON
    '{"intent": "greeting", "confidence": 0.95}',

    # Wrapped in markdown code block
    '```json\n{"intent": "question", "confidence": 0.87}\n```',

    # With extra text
    '```\n{"issues": [{"severity": "high", "message": "bug found"}]}\n```',
]

print("\n--- 解析 LLM JSON 输出 ---")
for output in llm_outputs:
    result = parse_llm_json(output)
    print(f"  输入: {output[:40]}... → 解析: {result}")


# ============================================================
# 5. pathlib — 现代路径处理
# JS: path.join / path.resolve  →  Python: Path
# ============================================================

# pathlib is more Pythonic than os.path
docs_dir = Path("./docs/14-AI")

# Path operations — like Node.js path module
print(f"\n当前目录: {Path.cwd()}")
print(f"home 目录: {Path.home()}")
print(f"拼接路径: {docs_dir / 'week1' / 'day1.py'}")  # JS: path.join(...)
print(f"绝对路径: {docs_dir.resolve()}")                # JS: path.resolve(...)
print(f"文件名: {Path('docs/rag.md').name}")             # JS: path.basename(...)
print(f"后缀名: {Path('docs/rag.md').suffix}")           # JS: path.extname(...)
print(f"父目录: {Path('docs/14-AI/rag.md').parent}")     # JS: path.dirname(...)

# Glob — find files by pattern (like Node.js glob package)
if docs_dir.exists():
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"\n找到 {len(md_files)} 个 .md 文件")
    for f in md_files[:5]:
        print(f"  {f}")


# ============================================================
# 6. JSON + dotenv + pathlib 对比速查表
# ============================================================

"""
JS/TS                              Python                          说明
─────                              ──────                          ────
JSON.stringify(obj)                json.dumps(obj)                  序列化
JSON.stringify(obj, null, 2)       json.dumps(obj, indent=2)        格式化
JSON.parse(str)                    json.loads(str)                  反序列化
fs.readFileSync(path)              Path(path).read_text()           读文件
fs.writeFileSync(path, data)       Path(path).write_text(data)      写文件
require("dotenv").config()         load_dotenv()                    加载 .env
process.env.KEY                    os.getenv("KEY")                 读环境变量
path.join(a, b)                    Path(a) / b                      拼接路径
path.resolve(p)                    Path(p).resolve()                绝对路径
glob("**/*.md")                    Path.glob("**/*.md")             文件匹配
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 写一个 load_docs_config 函数
# 从 .env 读取 DOCS_DIR，遍历目录下所有 .md 文件
# 返回 [{"path": "xxx.md", "size_kb": 12.3, "title": "文件名"}, ...]

# def load_docs_config() -> list[dict]:
#     ???

# TODO 2: 写一个更健壮的 parse_llm_json 函数
# 能处理以下情况：
# - JSON 前后有多余文字："好的，结果如下：{...} 希望对你有帮助"
# - 单引号替代双引号：{'key': 'value'}
# - 末尾多余逗号：{"a": 1, "b": 2,}

# def robust_parse_json(text: str) -> dict | None:
#     ???

# TODO 3: 写一个 ConfigManager 类
# - 支持从 .env 文件、JSON 文件、环境变量三种来源加载配置
# - 优先级：环境变量 > .env > JSON 文件（和 JS 生态习惯一样）
# - 提供 get(key, default) 方法

# class ConfigManager:
#     ???
