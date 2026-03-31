"""
Day 1: 定义工具函数 — 文件读取、文本搜索
Agent 的核心能力来自工具。工具就是普通的 Python 函数，加上描述让 LLM 知道什么时候该用它。
类比前端：工具 = API endpoint，Agent = 前端路由分发器
"""

import os
import json
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 1. 什么是 Agent Tool
# ============================================================

"""
Agent Tool 的本质：

┌─────────────────────────────────────────────────┐
│ Tool = 函数 + 名字 + 描述 + 参数说明             │
│                                                   │
│ 类比前端 REST API：                               │
│   name        → endpoint path (/api/read-file)    │
│   description → API 文档说明                       │
│   parameters  → request body schema               │
│   function    → handler 函数                       │
│                                                   │
│ LLM 看到工具描述后，决定要不要调用它                 │
│ 就像前端看 API 文档，决定用哪个接口                  │
└─────────────────────────────────────────────────┘
"""


# ============================================================
# 2. 工具结果数据结构
# ============================================================

@dataclass
class ToolResult:
    """Standardized return type for all tools, similar to API response format"""
    success: bool
    data: str
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        if self.success:
            return self.data
        return f"[Error] {self.error}"


# ============================================================
# 3. 工具函数：文件读取
# ============================================================

def read_file(file_path: str) -> ToolResult:
    """
    Read the contents of a file and return it as text.
    Supports text files: .txt, .py, .md, .json, .js, .ts, .html, .css
    """
    try:
        path = Path(file_path).resolve()

        # Security check: prevent reading sensitive files
        sensitive_patterns = [".env", "credentials", "secret", "password", "id_rsa"]
        if any(p in str(path).lower() for p in sensitive_patterns):
            return ToolResult(
                success=False,
                data="",
                error=f"Security: cannot read potentially sensitive file: {path.name}",
            )

        if not path.exists():
            return ToolResult(
                success=False,
                data="",
                error=f"File not found: {file_path}",
            )

        if not path.is_file():
            return ToolResult(
                success=False,
                data="",
                error=f"Not a file: {file_path}",
            )

        # Check file size (limit to 100KB)
        size = path.stat().st_size
        if size > 100 * 1024:
            return ToolResult(
                success=False,
                data="",
                error=f"File too large: {size:,} bytes (max 100KB)",
            )

        content = path.read_text(encoding="utf-8")
        return ToolResult(
            success=True,
            data=content,
            metadata={
                "file_path": str(path),
                "size_bytes": size,
                "line_count": content.count("\n") + 1,
                "extension": path.suffix,
            },
        )

    except UnicodeDecodeError:
        return ToolResult(
            success=False,
            data="",
            error=f"Cannot read binary file: {file_path}",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data="",
            error=f"Read error: {str(e)}",
        )


# ============================================================
# 4. 工具函数：文本搜索
# ============================================================

def search_text(
    directory: str,
    pattern: str,
    file_extension: str = ".py",
    max_results: int = 20,
) -> ToolResult:
    """
    Search for a text pattern in files under a directory.
    Returns matching lines with file path and line number.
    Similar to grep or VS Code's global search.
    """
    try:
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            return ToolResult(
                success=False,
                data="",
                error=f"Directory not found: {directory}",
            )

        if not dir_path.is_dir():
            return ToolResult(
                success=False,
                data="",
                error=f"Not a directory: {directory}",
            )

        # Compile regex pattern for efficiency
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return ToolResult(
                success=False,
                data="",
                error=f"Invalid regex pattern: {e}",
            )

        matches = []
        files_searched = 0

        # Walk through directory and search in matching files
        for file_path in sorted(dir_path.rglob(f"*{file_extension}")):
            # Skip hidden directories and common non-source directories
            parts = file_path.parts
            if any(p.startswith(".") or p in ("node_modules", "__pycache__", ".venv") for p in parts):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                files_searched += 1

                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        matches.append({
                            "file": str(file_path.relative_to(dir_path)),
                            "line": line_num,
                            "content": line.strip(),
                        })

                        if len(matches) >= max_results:
                            break

            except (UnicodeDecodeError, PermissionError):
                continue

            if len(matches) >= max_results:
                break

        # Format output similar to grep
        if not matches:
            result_text = f"No matches found for '{pattern}' in {files_searched} files"
        else:
            lines = [f"Found {len(matches)} matches in {files_searched} files:\n"]
            for m in matches:
                lines.append(f"  {m['file']}:{m['line']}  {m['content']}")
            result_text = "\n".join(lines)

        return ToolResult(
            success=True,
            data=result_text,
            metadata={
                "match_count": len(matches),
                "files_searched": files_searched,
                "pattern": pattern,
            },
        )

    except Exception as e:
        return ToolResult(
            success=False,
            data="",
            error=f"Search error: {str(e)}",
        )


# ============================================================
# 5. 工具函数：列出目录
# ============================================================

def list_directory(directory: str, max_depth: int = 2) -> ToolResult:
    """
    List files and subdirectories in a directory up to max_depth.
    Useful for the agent to understand project structure.
    """
    try:
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            return ToolResult(
                success=False,
                data="",
                error=f"Directory not found: {directory}",
            )

        lines = [f"Directory: {dir_path}\n"]
        file_count = 0
        dir_count = 0

        def _walk(path: Path, prefix: str, depth: int):
            nonlocal file_count, dir_count
            if depth > max_depth:
                return

            try:
                entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
            except PermissionError:
                lines.append(f"{prefix}[Permission Denied]")
                return

            for i, entry in enumerate(entries):
                # Skip hidden and common non-source entries
                if entry.name.startswith(".") or entry.name in ("node_modules", "__pycache__", ".venv"):
                    continue

                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                extension = "    " if is_last else "│   "

                if entry.is_dir():
                    dir_count += 1
                    lines.append(f"{prefix}{connector}{entry.name}/")
                    _walk(entry, prefix + extension, depth + 1)
                else:
                    file_count += 1
                    size = entry.stat().st_size
                    size_str = f"{size:,}B" if size < 1024 else f"{size // 1024}KB"
                    lines.append(f"{prefix}{connector}{entry.name} ({size_str})")

        _walk(dir_path, "", 0)
        lines.append(f"\n{dir_count} directories, {file_count} files")

        return ToolResult(
            success=True,
            data="\n".join(lines),
            metadata={"file_count": file_count, "dir_count": dir_count},
        )

    except Exception as e:
        return ToolResult(
            success=False,
            data="",
            error=f"List error: {str(e)}",
        )


# ============================================================
# 6. 工具注册表 — 集中管理所有工具
# ============================================================

"""
工具注册表的设计模式：
- 类比前端路由表 (React Router 的 route config)
- 每个工具有：name, description, parameters, function
- LLM 看到注册表后，根据任务选择工具

┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  用户提问    │ ──→ │ LLM 选择工具  │ ──→ │ 执行工具  │
│ "读取文件"   │     │ → read_file  │     │ 返回结果  │
└─────────────┘     └──────────────┘     └──────────┘
"""

# Tool registry: maps tool name to its metadata and function
TOOL_REGISTRY = {
    "read_file": {
        "name": "read_file",
        "description": "Read the contents of a file. Use this when you need to see what's inside a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
            },
            "required": ["file_path"],
        },
        "function": read_file,
    },
    "search_text": {
        "name": "search_text",
        "description": "Search for a text pattern in files under a directory. Use this when you need to find where something is defined or used.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to search in",
                },
                "pattern": {
                    "type": "string",
                    "description": "Text or regex pattern to search for",
                },
                "file_extension": {
                    "type": "string",
                    "description": "File extension to filter (default: .py)",
                    "default": ".py",
                },
            },
            "required": ["directory", "pattern"],
        },
        "function": search_text,
    },
    "list_directory": {
        "name": "list_directory",
        "description": "List files and subdirectories. Use this to understand project structure before reading specific files.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory path to list",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth to recurse (default: 2)",
                    "default": 2,
                },
            },
            "required": ["directory"],
        },
        "function": list_directory,
    },
}


def get_tools_description() -> str:
    """Generate a description of all available tools for the LLM prompt"""
    lines = ["Available tools:\n"]
    for name, tool in TOOL_REGISTRY.items():
        lines.append(f"- {name}: {tool['description']}")
        params = tool["parameters"]["properties"]
        for param_name, param_info in params.items():
            required = param_name in tool["parameters"].get("required", [])
            req_mark = " (required)" if required else " (optional)"
            lines.append(f"    {param_name}{req_mark}: {param_info['description']}")
    return "\n".join(lines)


def execute_tool(tool_name: str, **kwargs) -> ToolResult:
    """Execute a tool by name with given arguments"""
    if tool_name not in TOOL_REGISTRY:
        return ToolResult(
            success=False,
            data="",
            error=f"Unknown tool: {tool_name}. Available: {list(TOOL_REGISTRY.keys())}",
        )

    tool = TOOL_REGISTRY[tool_name]
    func = tool["function"]
    return func(**kwargs)


# ============================================================
# 7. 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 1: Tool Functions 演示")
    print("=" * 60)

    # Demo 1: 列出当前目录
    print("\n--- Demo 1: list_directory ---")
    result = list_directory(".")
    print(result)

    # Demo 2: 读取本文件
    print("\n--- Demo 2: read_file ---")
    result = read_file(__file__)
    if result.success:
        lines = result.data.splitlines()
        print(f"文件: {result.metadata['file_path']}")
        print(f"大小: {result.metadata['size_bytes']} bytes")
        print(f"行数: {result.metadata['line_count']}")
        print(f"前 5 行:\n" + "\n".join(lines[:5]))
    else:
        print(f"Error: {result.error}")

    # Demo 3: 搜索文本
    print("\n--- Demo 3: search_text ---")
    result = search_text(".", "def ", ".py", max_results=10)
    print(result)

    # Demo 4: 安全检查
    print("\n--- Demo 4: Security check ---")
    result = read_file(".env")
    print(result)

    # Demo 5: 工具注册表
    print("\n--- Demo 5: Tool Registry ---")
    print(get_tools_description())

    # Demo 6: 通过注册表执行工具
    print("\n--- Demo 6: execute_tool ---")
    result = execute_tool("read_file", file_path=__file__)
    print(f"execute_tool 结果: success={result.success}, lines={result.metadata.get('line_count', 0)}")

    result = execute_tool("unknown_tool")
    print(f"未知工具: {result}")


    # ============================================================
    # 练习题
    # ============================================================

    print("\n" + "=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 实现一个 write_file 工具函数
    # 参数: file_path (str), content (str)
    # 要求: 有安全检查（不能覆盖 .py / .env 文件），返回 ToolResult

    # TODO 2: 实现一个 count_words 工具函数
    # 参数: text (str)
    # 返回: 字数统计、字符数、段落数

    # TODO 3: 把 TODO 1 和 TODO 2 的工具注册到 TOOL_REGISTRY
    # 并用 execute_tool 调用它们
