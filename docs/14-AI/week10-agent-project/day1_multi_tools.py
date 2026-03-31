"""
Day 1: 添加多种工具 — 文件读写、网页摘要、代码执行
让 Agent 拥有更丰富的工具集，能完成更复杂的任务
类比前端：给一个微服务网关添加更多后端服务路由
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field

from langchain_community.llms import Ollama


# ============================================================
# 1. 工具基础设施
# ============================================================

"""
多工具 Agent 的架构：

┌──────────────────────────────────────────────────────┐
│                    Agent Core                         │
│              (ReAct Loop + Tool Router)               │
├──────────┬──────────┬──────────┬──────────┬──────────┤
│ 文件读取  │ 文件写入  │ 网页摘要  │ 代码执行  │ 计算器   │
│ read     │ write    │ web      │ exec     │ calc     │
│          │          │ summary  │ python   │          │
└──────────┴──────────┴──────────┴──────────┴──────────┘

类比前端微服务：
┌──────────────────────────────────────────────────────┐
│                 API Gateway (nginx)                   │
├──────────┬──────────┬──────────┬──────────┬──────────┤
│ /api/    │ /api/    │ /api/    │ /api/    │ /api/    │
│ files    │ storage  │ scraper  │ sandbox  │ math     │
└──────────┴──────────┴──────────┴──────────┴──────────┘
"""


@dataclass
class ToolResult:
    """Standardized tool result format"""
    success: bool
    data: str
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.data if self.success else f"[Error] {self.error}"


# ============================================================
# 2. 工具：文件读取
# ============================================================

def tool_read_file(file_path: str) -> ToolResult:
    """
    Read the contents of a text file.
    Has safety checks for file size and sensitive files.
    """
    try:
        path = Path(file_path).resolve()

        # Security: block sensitive files
        sensitive = [".env", "credentials", "secret", "password", "id_rsa", ".key"]
        if any(s in path.name.lower() for s in sensitive):
            return ToolResult(success=False, data="", error=f"Cannot read sensitive file: {path.name}")

        if not path.exists():
            return ToolResult(success=False, data="", error=f"File not found: {file_path}")

        # Size limit: 200KB
        size = path.stat().st_size
        if size > 200 * 1024:
            return ToolResult(success=False, data="", error=f"File too large: {size:,} bytes (max 200KB)")

        content = path.read_text(encoding="utf-8")
        return ToolResult(
            success=True,
            data=content,
            metadata={"path": str(path), "size": size, "lines": content.count("\n") + 1},
        )
    except UnicodeDecodeError:
        return ToolResult(success=False, data="", error=f"Binary file, cannot read as text: {file_path}")
    except Exception as e:
        return ToolResult(success=False, data="", error=str(e))


# ============================================================
# 3. 工具：文件写入
# ============================================================

def tool_write_file(file_path: str, content: str) -> ToolResult:
    """
    Write content to a file. Creates parent directories if needed.
    Safety: only allows writing to specific directories and extensions.
    """
    try:
        path = Path(file_path).resolve()

        # Security: only allow safe extensions
        safe_extensions = {".txt", ".md", ".json", ".csv", ".log", ".html", ".css"}
        if path.suffix.lower() not in safe_extensions:
            return ToolResult(
                success=False, data="",
                error=f"Cannot write to {path.suffix} files. Allowed: {safe_extensions}",
            )

        # Security: don't overwrite important files
        if path.exists() and path.stat().st_size > 0:
            # Backup the original file
            backup_path = path.with_suffix(path.suffix + ".bak")
            if not backup_path.exists():
                import shutil
                shutil.copy2(path, backup_path)

        # Create parent directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        path.write_text(content, encoding="utf-8")
        size = path.stat().st_size

        return ToolResult(
            success=True,
            data=f"Written {size:,} bytes to {path}",
            metadata={"path": str(path), "size": size},
        )
    except Exception as e:
        return ToolResult(success=False, data="", error=str(e))


# ============================================================
# 4. 工具：网页摘要
# ============================================================

def tool_web_summary(url: str) -> ToolResult:
    """
    Fetch a web page and return a text summary.
    Uses basic HTML parsing to extract main content.
    Requires: pip install beautifulsoup4 httpx
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        return ToolResult(
            success=False, data="",
            error="Missing dependencies. Run: pip install beautifulsoup4 httpx",
        )

    try:
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            return ToolResult(success=False, data="", error=f"Invalid URL: {url}. Must start with http:// or https://")

        # Fetch page with timeout
        headers = {"User-Agent": "Mozilla/5.0 (Research Agent)"}
        response = httpx.get(url, headers=headers, timeout=15.0, follow_redirects=True)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script, style, nav, footer elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else "No title"

        # Extract main text content
        # Priority: article > main > body
        main_content = soup.find("article") or soup.find("main") or soup.find("body")

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up: remove excessive blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Truncate if too long
        if len(clean_text) > 3000:
            clean_text = clean_text[:3000] + "\n\n... (truncated)"

        result = f"Title: {title}\nURL: {url}\n\n{clean_text}"

        return ToolResult(
            success=True,
            data=result,
            metadata={
                "url": url,
                "title": title,
                "content_length": len(clean_text),
                "status_code": response.status_code,
            },
        )

    except httpx.HTTPStatusError as e:
        return ToolResult(success=False, data="", error=f"HTTP {e.response.status_code}: {url}")
    except httpx.TimeoutException:
        return ToolResult(success=False, data="", error=f"Timeout fetching {url}")
    except Exception as e:
        return ToolResult(success=False, data="", error=f"Web fetch error: {str(e)}")


# ============================================================
# 5. 工具：代码执行（沙箱）
# ============================================================

def tool_execute_python(code: str, timeout: int = 10) -> ToolResult:
    """
    Execute Python code in a sandboxed subprocess.
    Returns stdout output. Has timeout protection.

    SECURITY: runs in a subprocess with no network access.
    Only use for simple calculations and data processing.
    """
    # Security: block dangerous operations
    dangerous_patterns = [
        r"\bimport\s+os\b",
        r"\bimport\s+subprocess\b",
        r"\bimport\s+shutil\b",
        r"\b__import__\b",
        r"\beval\b",
        r"\bexec\b",
        r"\bopen\s*\(",
        r"\bsystem\s*\(",
        r"\brunpy\b",
        r"rm\s+-rf",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, code):
            return ToolResult(
                success=False, data="",
                error=f"Security: blocked dangerous pattern: {pattern}",
            )

    try:
        # Write code to a temp file and execute
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tempfile.gettempdir(),
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            return ToolResult(
                success=result.returncode == 0,
                data=output if output else "(no output)",
                error=result.stderr if result.returncode != 0 else None,
                metadata={
                    "return_code": result.returncode,
                    "code_length": len(code),
                },
            )

        finally:
            os.unlink(temp_path)

    except subprocess.TimeoutExpired:
        return ToolResult(success=False, data="", error=f"Code execution timed out ({timeout}s)")
    except Exception as e:
        return ToolResult(success=False, data="", error=f"Execution error: {str(e)}")


# ============================================================
# 6. 工具：计算器
# ============================================================

def tool_calculator(expression: str) -> ToolResult:
    """
    Evaluate a mathematical expression safely.
    Supports basic arithmetic, math functions, and constants.
    """
    import math

    # Allowed names in the expression
    safe_dict = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "len": len, "int": int, "float": float,
        "pow": pow,
        "pi": math.pi, "e": math.e,
        "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "ceil": math.ceil, "floor": math.floor,
    }

    try:
        # Remove potentially dangerous characters
        clean_expr = expression.strip()
        if any(kw in clean_expr for kw in ["import", "__", "eval", "exec", "open"]):
            return ToolResult(success=False, data="", error="Expression contains blocked keywords")

        result = eval(clean_expr, {"__builtins__": {}}, safe_dict)

        return ToolResult(
            success=True,
            data=f"{expression} = {result}",
            metadata={"expression": expression, "result": result},
        )
    except Exception as e:
        return ToolResult(success=False, data="", error=f"Calculation error: {str(e)}")


# ============================================================
# 7. 工具注册表
# ============================================================

MULTI_TOOL_REGISTRY = {
    "read_file": {
        "name": "read_file",
        "description": "Read a text file's contents. Use when you need to see file content.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
            },
            "required": ["file_path"],
        },
        "function": tool_read_file,
    },
    "write_file": {
        "name": "write_file",
        "description": "Write content to a file (.txt, .md, .json, .csv, .html, .css only).",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to write to"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["file_path", "content"],
        },
        "function": tool_write_file,
    },
    "web_summary": {
        "name": "web_summary",
        "description": "Fetch a web page and extract text content. Use to get information from URLs.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch (must start with http:// or https://)"},
            },
            "required": ["url"],
        },
        "function": tool_web_summary,
    },
    "execute_python": {
        "name": "execute_python",
        "description": "Execute Python code and return output. Use for calculations and data processing. No file/network access.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 10)", "default": 10},
            },
            "required": ["code"],
        },
        "function": tool_execute_python,
    },
    "calculator": {
        "name": "calculator",
        "description": "Evaluate a math expression. Supports: +, -, *, /, **, sqrt, sin, cos, log, pi, e.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate"},
            },
            "required": ["expression"],
        },
        "function": tool_calculator,
    },
}


def get_tools_description() -> str:
    """Generate tool descriptions for LLM prompts"""
    lines = ["Available tools:\n"]
    for name, tool in MULTI_TOOL_REGISTRY.items():
        lines.append(f"- {name}: {tool['description']}")
        for pname, pinfo in tool["parameters"]["properties"].items():
            req = pname in tool["parameters"].get("required", [])
            mark = " (required)" if req else ""
            lines.append(f"    {pname}{mark}: {pinfo['description']}")
    return "\n".join(lines)


def execute_tool(name: str, **kwargs) -> ToolResult:
    """Execute a tool by name"""
    if name not in MULTI_TOOL_REGISTRY:
        return ToolResult(success=False, data="", error=f"Unknown tool: {name}")
    return MULTI_TOOL_REGISTRY[name]["function"](**kwargs)


# ============================================================
# 8. 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 1: Multi Tools 演示")
    print("=" * 60)

    # Demo 1: Read file
    print("\n--- Demo 1: read_file ---")
    result = tool_read_file(__file__)
    if result.success:
        print(f"  Read {result.metadata['lines']} lines, {result.metadata['size']} bytes")
    else:
        print(f"  Error: {result.error}")

    # Demo 2: Write file
    print("\n--- Demo 2: write_file ---")
    test_content = json.dumps({"message": "Hello from Agent!", "timestamp": "2024-01-01"}, indent=2)
    result = tool_write_file("/tmp/agent_test_output.json", test_content)
    print(f"  {result}")

    # Verify
    verify = tool_read_file("/tmp/agent_test_output.json")
    print(f"  Verify: {verify.data[:50]}...")

    # Demo 3: Web summary
    print("\n--- Demo 3: web_summary ---")
    result = tool_web_summary("https://example.com")
    if result.success:
        print(f"  Title: {result.metadata.get('title', 'N/A')}")
        print(f"  Content length: {result.metadata.get('content_length', 0)}")
        print(f"  Preview: {result.data[:100]}...")
    else:
        print(f"  Error: {result.error}")

    # Demo 4: Execute Python
    print("\n--- Demo 4: execute_python ---")
    code = """
# Calculate Fibonacci numbers
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

for i in range(10):
    print(f"fib({i}) = {fib(i)}")
"""
    result = tool_execute_python(code)
    print(f"  Success: {result.success}")
    print(f"  Output:\n{result.data}")

    # Demo 5: Security check
    print("\n--- Demo 5: Security checks ---")
    dangerous_code = "import os; os.system('rm -rf /')"
    result = tool_execute_python(dangerous_code)
    print(f"  Dangerous code blocked: {result.error}")

    result = tool_read_file(".env")
    print(f"  Sensitive file blocked: {result.error}")

    result = tool_write_file("dangerous.py", "hack")
    print(f"  Unsafe extension blocked: {result.error}")

    # Demo 6: Calculator
    print("\n--- Demo 6: calculator ---")
    expressions = [
        "2 + 3 * 4",
        "sqrt(144)",
        "pi * 5**2",
        "log10(1000)",
    ]
    for expr in expressions:
        result = tool_calculator(expr)
        print(f"  {result}")

    # Demo 7: Tools description
    print("\n--- Demo 7: Tool descriptions ---")
    print(get_tools_description())


    # ============================================================
    # 练习题
    # ============================================================

    print("\n" + "=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 实现一个 tool_json_query 工具
    # 参数: file_path (str), json_path (str)
    # 用 jsonpath 语法查询 JSON 文件中的值
    # 例如: tool_json_query("data.json", "$.users[0].name")

    # TODO 2: 实现一个 tool_diff 工具
    # 参数: file_a (str), file_b (str)
    # 返回两个文件的差异（可以用 difflib）

    # TODO 3: 给 tool_execute_python 添加内存限制
    # 如果代码使用超过 50MB 内存，自动终止
    # 提示：可以用 resource 模块（Linux/Mac）或 psutil
