"""
Day 6-7: 综合练习 — 用 Python 写一个 JSON 格式化/校验 CLI 工具

这个项目综合运用本周所有知识点：
- Day 1: dict/list 操作（解析 JSON 数据）
- Day 2: 函数、装饰器（错误处理装饰器）
- Day 3: class/dataclass（组织代码结构）
- Day 4: async/await（异步读取多个文件）
- Day 5: 类型提示（完整标注）

用法:
  python day67_json_tool.py format input.json              # 格式化
  python day67_json_tool.py validate input.json            # 校验
  python day67_json_tool.py query input.json "users[0].name"  # 查询字段
  python day67_json_tool.py stats input.json               # 统计信息
  python day67_json_tool.py batch *.json                   # 批量校验
"""

import json
import sys
import asyncio
import time
import functools
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional, Literal
from enum import Enum


# ============================================================
# Day 2 知识: 装饰器 — 错误处理
# ============================================================

def handle_errors(func):
    """Catch and display errors gracefully instead of raw tracebacks"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            print(f"❌ 文件未找到: {e.filename}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析错误 (行 {e.lineno}, 列 {e.colno}): {e.msg}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 错误: {e}")
            sys.exit(1)
    return wrapper


# ============================================================
# Day 3 知识: dataclass — 数据结构定义
# ============================================================

class Severity(Enum):
    """Validation result severity levels"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of JSON validation"""
    file_path: str
    is_valid: bool
    severity: Severity
    message: str
    line: Optional[int] = None
    column: Optional[int] = None

    def display(self) -> str:
        """Format validation result for terminal output"""
        icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}[self.severity.value]
        location = f" (行 {self.line}, 列 {self.column})" if self.line else ""
        return f"{icon} {self.file_path}{location}: {self.message}"


@dataclass
class JsonStats:
    """Statistics about a JSON document"""
    file_path: str
    size_bytes: int
    key_count: int = 0
    max_depth: int = 0
    array_count: int = 0
    object_count: int = 0
    null_count: int = 0
    data_types: dict[str, int] = field(default_factory=dict)

    def display(self) -> str:
        """Format stats for terminal output"""
        lines = [
            f"📊 统计信息: {self.file_path}",
            f"   文件大小: {self.size_bytes:,} bytes",
            f"   键总数: {self.key_count}",
            f"   最大嵌套深度: {self.max_depth}",
            f"   数组数量: {self.array_count}",
            f"   对象数量: {self.object_count}",
            f"   null 值数量: {self.null_count}",
            f"   数据类型分布: {self.data_types}",
        ]
        return "\n".join(lines)


# ============================================================
# Day 1 知识: dict/list 操作 — JSON 数据处理
# ============================================================

# Day 5 knowledge: full type annotations
def query_json(data: Any, path: str) -> Any:
    """
    Query a JSON value by dot-notation path.
    Supports array indexing: "users[0].name"
    Similar concept to lodash _.get() in JS.
    """
    parts = path.replace("[", ".[").split(".")
    current = data

    for part in parts:
        if not part:
            continue
        # Handle array index like [0]
        if part.startswith("[") and part.endswith("]"):
            index = int(part[1:-1])
            if not isinstance(current, list) or index >= len(current):
                return None
            current = current[index]
        # Handle dict key
        elif isinstance(current, dict):
            current = current.get(part)
            if current is None:
                return None
        else:
            return None

    return current


def calculate_stats(data: Any, depth: int = 0) -> dict[str, int]:
    """
    Recursively analyze JSON structure and collect statistics.
    Uses dict operations and list comprehensions.
    """
    stats = {
        "key_count": 0,
        "max_depth": depth,
        "array_count": 0,
        "object_count": 0,
        "null_count": 0,
    }
    # Count data types
    type_counts: dict[str, int] = {}

    if isinstance(data, dict):
        stats["object_count"] = 1
        stats["key_count"] = len(data)
        for value in data.values():
            # Record type of each value
            type_name = type(value).__name__
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            # Recurse into nested structures
            child = calculate_stats(value, depth + 1)
            stats["key_count"] += child["key_count"]
            stats["max_depth"] = max(stats["max_depth"], child["max_depth"])
            stats["array_count"] += child["array_count"]
            stats["object_count"] += child["object_count"]
            stats["null_count"] += child["null_count"]

    elif isinstance(data, list):
        stats["array_count"] = 1
        for item in data:
            child = calculate_stats(item, depth + 1)
            stats["key_count"] += child["key_count"]
            stats["max_depth"] = max(stats["max_depth"], child["max_depth"])
            stats["array_count"] += child["array_count"]
            stats["object_count"] += child["object_count"]
            stats["null_count"] += child["null_count"]

    elif data is None:
        stats["null_count"] = 1

    stats["type_counts"] = type_counts
    return stats


# ============================================================
# Day 4 知识: async — 批量文件处理
# ============================================================

async def read_file_async(file_path: str) -> str:
    """
    Read a file asynchronously.
    Note: for true async file I/O, use aiofiles library.
    Here we simulate with asyncio for learning purposes.
    """
    # In real code: async with aiofiles.open(file_path) as f: return await f.read()
    await asyncio.sleep(0.01)  # Simulate I/O delay
    return Path(file_path).read_text(encoding="utf-8")


async def validate_file_async(file_path: str) -> ValidationResult:
    """Validate a single JSON file asynchronously"""
    try:
        content = await read_file_async(file_path)
        json.loads(content)
        return ValidationResult(
            file_path=file_path,
            is_valid=True,
            severity=Severity.OK,
            message="JSON 格式正确",
        )
    except json.JSONDecodeError as e:
        return ValidationResult(
            file_path=file_path,
            is_valid=False,
            severity=Severity.ERROR,
            message=e.msg,
            line=e.lineno,
            column=e.colno,
        )
    except FileNotFoundError:
        return ValidationResult(
            file_path=file_path,
            is_valid=False,
            severity=Severity.ERROR,
            message="文件未找到",
        )


async def batch_validate(file_paths: list[str]) -> list[ValidationResult]:
    """Validate multiple JSON files concurrently"""
    # asyncio.gather — run all validations in parallel
    results = await asyncio.gather(
        *[validate_file_async(path) for path in file_paths]
    )
    return list(results)


# ============================================================
# 主要命令实现
# ============================================================

CommandType = Literal["format", "validate", "query", "stats", "batch"]


@handle_errors
def cmd_format(file_path: str, indent: int = 2) -> None:
    """Format a JSON file with proper indentation"""
    content = Path(file_path).read_text(encoding="utf-8")
    data = json.loads(content)
    formatted = json.dumps(data, indent=indent, ensure_ascii=False)
    print(formatted)


@handle_errors
def cmd_validate(file_path: str) -> None:
    """Validate a JSON file and report errors"""
    content = Path(file_path).read_text(encoding="utf-8")
    data = json.loads(content)
    result = ValidationResult(
        file_path=file_path,
        is_valid=True,
        severity=Severity.OK,
        message=f"JSON 格式正确 (顶层类型: {type(data).__name__})",
    )
    print(result.display())


@handle_errors
def cmd_query(file_path: str, path: str) -> None:
    """Query a specific field in a JSON file"""
    content = Path(file_path).read_text(encoding="utf-8")
    data = json.loads(content)
    result = query_json(data, path)
    if result is None:
        print(f"⚠️ 路径 '{path}' 未找到")
    else:
        # Pretty print the result
        if isinstance(result, (dict, list)):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)


@handle_errors
def cmd_stats(file_path: str) -> None:
    """Show statistics about a JSON file"""
    content = Path(file_path).read_text(encoding="utf-8")
    data = json.loads(content)
    raw_stats = calculate_stats(data)

    stats = JsonStats(
        file_path=file_path,
        size_bytes=len(content.encode("utf-8")),
        key_count=raw_stats["key_count"],
        max_depth=raw_stats["max_depth"],
        array_count=raw_stats["array_count"],
        object_count=raw_stats["object_count"],
        null_count=raw_stats["null_count"],
        data_types=raw_stats.get("type_counts", {}),
    )
    print(stats.display())


def cmd_batch(file_paths: list[str]) -> None:
    """Batch validate multiple JSON files concurrently"""
    results = asyncio.run(batch_validate(file_paths))

    valid_count = sum(1 for r in results if r.is_valid)
    print(f"\n📋 批量校验结果: {valid_count}/{len(results)} 个文件通过\n")
    for result in results:
        print(f"  {result.display()}")


# ============================================================
# CLI 入口
# ============================================================

def print_usage():
    print("""
JSON Tool — Python 练习项目

用法:
  python day67_json_tool.py format <file>              格式化 JSON
  python day67_json_tool.py validate <file>            校验 JSON
  python day67_json_tool.py query <file> <path>        查询字段 (如 "users[0].name")
  python day67_json_tool.py stats <file>               统计信息
  python day67_json_tool.py batch <file1> [file2...]   批量校验

示例:
  python day67_json_tool.py format package.json
  python day67_json_tool.py query data.json "results[0].score"
  python day67_json_tool.py batch *.json
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1]

    if command == "format" and len(sys.argv) >= 3:
        cmd_format(sys.argv[2])
    elif command == "validate" and len(sys.argv) >= 3:
        cmd_validate(sys.argv[2])
    elif command == "query" and len(sys.argv) >= 4:
        cmd_query(sys.argv[2], sys.argv[3])
    elif command == "stats" and len(sys.argv) >= 3:
        cmd_stats(sys.argv[2])
    elif command == "batch" and len(sys.argv) >= 3:
        cmd_batch(sys.argv[2:])
    else:
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()


# ============================================================
# 扩展练习（可选）
# ============================================================

# TODO 1: 添加 diff 命令 — 比较两个 JSON 文件的差异
# python day67_json_tool.py diff file1.json file2.json

# TODO 2: 添加 minify 命令 — 压缩 JSON（去掉空格和换行）

# TODO 3: 添加 --output 参数 — 把结果写入文件而不是打印

# TODO 4: 添加 merge 命令 — 合并多个 JSON 文件
# python day67_json_tool.py merge a.json b.json > merged.json
