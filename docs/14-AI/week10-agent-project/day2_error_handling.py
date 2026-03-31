"""
Day 2: 错误处理 — 工具失败时的重试和回退
Agent 的工具可能会失败（网络超时、文件不存在、LLM 无响应），需要优雅处理
类比前端：axios 拦截器的错误重试、React Error Boundary、Service Worker 离线回退
"""

import time
import json
import random
import functools
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from day1_multi_tools import ToolResult, MULTI_TOOL_REGISTRY, execute_tool


# ============================================================
# 1. 错误处理策略
# ============================================================

"""
Agent 错误处理的分层策略：

┌─────────────────────────────────────────────┐
│ Level 3: Agent-Level Recovery                │
│ "换一种方式解决问题"                          │
│ 例：read_file 失败 → 尝试 search_text        │
├─────────────────────────────────────────────┤
│ Level 2: Tool-Level Retry                    │
│ "同一个工具重试几次"                          │
│ 例：网络超时 → 等 1s → 重试 → 等 2s → 重试    │
├─────────────────────────────────────────────┤
│ Level 1: Error Wrapping                      │
│ "把错误包装成结构化信息"                       │
│ 例：Exception → ToolResult(success=False)     │
└─────────────────────────────────────────────┘

类比前端:
- Level 1: try-catch + 错误对象          (Error class)
- Level 2: axios retry interceptor       (重试拦截器)
- Level 3: React Error Boundary fallback (降级 UI)
"""


# ============================================================
# 2. 重试策略配置
# ============================================================

class RetryStrategy(Enum):
    """How to wait between retries"""
    FIXED = "fixed"              # Always wait the same amount
    LINEAR = "linear"            # Wait increases linearly: 1s, 2s, 3s
    EXPONENTIAL = "exponential"  # Wait doubles: 1s, 2s, 4s, 8s
    JITTER = "jitter"            # Exponential + random jitter


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0        # Base delay in seconds
    max_delay: float = 30.0        # Maximum delay cap
    retryable_errors: list[str] = field(default_factory=lambda: [
        "timeout", "connection", "rate limit", "temporary", "503", "429",
    ])

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number (0-based)"""
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.JITTER:
            exp_delay = self.base_delay * (2 ** attempt)
            delay = exp_delay * (0.5 + random.random())  # 50%-150% of exponential
        else:
            delay = self.base_delay

        return min(delay, self.max_delay)

    def is_retryable(self, error_message: str) -> bool:
        """Check if an error message indicates a retryable error"""
        error_lower = error_message.lower()
        return any(keyword in error_lower for keyword in self.retryable_errors)


# ============================================================
# 3. 重试装饰器
# ============================================================

def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator that adds retry logic to a tool function.
    Similar to axios-retry or fetch-retry in frontend.

    Usage:
        @with_retry(RetryConfig(max_retries=3))
        def my_tool(arg1, arg2):
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> ToolResult:
            last_error = None

            for attempt in range(config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # If the tool returned a ToolResult, check success
                    if isinstance(result, ToolResult):
                        if result.success:
                            return result

                        # Check if error is retryable
                        if result.error and config.is_retryable(result.error):
                            last_error = result.error
                            if attempt < config.max_retries:
                                delay = config.get_delay(attempt)
                                print(f"  [Retry] Attempt {attempt + 1}/{config.max_retries}: "
                                      f"{result.error[:50]}... Waiting {delay:.1f}s")
                                time.sleep(delay)
                                continue

                        # Not retryable, return as-is
                        return result

                    # If not a ToolResult, wrap it
                    return ToolResult(success=True, data=str(result))

                except Exception as e:
                    last_error = str(e)
                    if config.is_retryable(str(e)) and attempt < config.max_retries:
                        delay = config.get_delay(attempt)
                        print(f"  [Retry] Attempt {attempt + 1}/{config.max_retries}: "
                              f"{str(e)[:50]}... Waiting {delay:.1f}s")
                        time.sleep(delay)
                        continue

                    return ToolResult(
                        success=False, data="",
                        error=f"Failed after {attempt + 1} attempts: {str(e)}",
                    )

            # All retries exhausted
            return ToolResult(
                success=False, data="",
                error=f"All {config.max_retries} retries exhausted. Last error: {last_error}",
                metadata={"retries_used": config.max_retries},
            )

        return wrapper
    return decorator


# ============================================================
# 4. 回退（Fallback）机制
# ============================================================

@dataclass
class FallbackChain:
    """
    Chain of fallback tools. If the primary tool fails,
    try alternatives in order.

    Similar to:
    - CSS fallback fonts: font-family: "Custom", "Arial", sans-serif
    - Service Worker: cache first, then network, then offline page
    """
    primary: str               # Primary tool name
    fallbacks: list[str]       # Fallback tool names in priority order
    arg_transforms: dict = field(default_factory=dict)  # How to transform args for fallback

    def get_execution_order(self) -> list[str]:
        """Return tools in execution order"""
        return [self.primary] + self.fallbacks


# Predefined fallback chains
FALLBACK_CHAINS = {
    # If reading a file fails, try searching for its content
    "read_file": FallbackChain(
        primary="read_file",
        fallbacks=["web_summary"],
        arg_transforms={
            "web_summary": lambda args: {"url": f"file://{args.get('file_path', '')}"},
        },
    ),
    # If web fetch fails, try a simpler approach
    "web_summary": FallbackChain(
        primary="web_summary",
        fallbacks=["read_file"],
        arg_transforms={
            "read_file": lambda args: {"file_path": args.get("url", "").replace("file://", "")},
        },
    ),
}


class FallbackExecutor:
    """Execute tools with fallback chains"""

    def __init__(self, registry: dict, chains: Optional[dict] = None):
        self.registry = registry
        self.chains = chains or FALLBACK_CHAINS

    def execute_with_fallback(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Try the primary tool, then fallbacks if it fails.
        Returns the first successful result.
        """
        chain = self.chains.get(tool_name)

        # No fallback chain: just execute directly
        if chain is None:
            return execute_tool(tool_name, **kwargs)

        errors = []

        for i, current_tool in enumerate(chain.get_execution_order()):
            # Transform arguments for fallback tools
            if i > 0 and current_tool in chain.arg_transforms:
                transform = chain.arg_transforms[current_tool]
                try:
                    current_kwargs = transform(kwargs)
                except Exception as e:
                    errors.append(f"{current_tool}: arg transform failed: {e}")
                    continue
            else:
                current_kwargs = kwargs

            # Execute the tool
            is_fallback = i > 0
            label = "Fallback" if is_fallback else "Primary"
            print(f"  [{label}] Trying {current_tool}...")

            result = execute_tool(current_tool, **current_kwargs)

            if result.success:
                if is_fallback:
                    result.metadata["fallback_from"] = chain.primary
                    result.metadata["fallback_tool"] = current_tool
                return result

            errors.append(f"{current_tool}: {result.error}")
            print(f"  [{label}] Failed: {result.error}")

        # All tools failed
        return ToolResult(
            success=False, data="",
            error=f"All tools failed:\n" + "\n".join(f"  - {e}" for e in errors),
            metadata={"tools_tried": chain.get_execution_order()},
        )


# ============================================================
# 5. 错误恢复建议器
# ============================================================

class ErrorAdvisor:
    """
    Analyzes tool errors and suggests recovery actions.
    Like a smart error message that tells you what to do next.
    """

    # Error pattern → (suggestion, alternative_tool, arg_hint)
    ERROR_PATTERNS = {
        "file not found": (
            "Check if the file path is correct. Try list_directory to see available files.",
            "list_directory",
            lambda args: {"directory": str(Path(args.get("file_path", ".")).parent)},
        ),
        "permission denied": (
            "The file cannot be accessed. Try reading a different file.",
            None,
            None,
        ),
        "timeout": (
            "The request timed out. Try again or use a different URL.",
            None,
            None,
        ),
        "binary file": (
            "This is a binary file. Try listing the directory to find text files.",
            "list_directory",
            lambda args: {"directory": str(Path(args.get("file_path", ".")).parent)},
        ),
        "too large": (
            "The file is too large. Try searching for specific content instead.",
            "search_text",
            None,
        ),
        "sensitive file": (
            "Cannot read sensitive files for security reasons.",
            None,
            None,
        ),
        "http 404": (
            "Page not found. Check the URL.",
            None,
            None,
        ),
        "http 429": (
            "Rate limited. Wait and try again.",
            None,
            None,
        ),
    }

    @classmethod
    def analyze(cls, error: str, tool_name: str, tool_args: dict) -> dict:
        """
        Analyze an error and return recovery suggestions.
        Returns dict with: suggestion, alternative_tool, alternative_args
        """
        error_lower = error.lower()

        for pattern, (suggestion, alt_tool, arg_fn) in cls.ERROR_PATTERNS.items():
            if pattern in error_lower:
                result = {
                    "error": error,
                    "suggestion": suggestion,
                    "alternative_tool": alt_tool,
                }
                if alt_tool and arg_fn:
                    try:
                        result["alternative_args"] = arg_fn(tool_args)
                    except Exception:
                        result["alternative_args"] = None
                return result

        # Generic suggestion
        return {
            "error": error,
            "suggestion": f"Tool '{tool_name}' failed. Check the arguments and try again.",
            "alternative_tool": None,
        }


# ============================================================
# 6. 带错误处理的工具执行器
# ============================================================

class RobustToolExecutor:
    """
    Combines retry, fallback, and error analysis into one executor.
    This is the recommended way to execute tools in production agents.
    """

    def __init__(
        self,
        registry: dict = None,
        retry_config: Optional[RetryConfig] = None,
        fallback_chains: Optional[dict] = None,
    ):
        self.registry = registry or MULTI_TOOL_REGISTRY
        self.retry_config = retry_config or RetryConfig(max_retries=2, strategy=RetryStrategy.EXPONENTIAL)
        self.fallback_executor = FallbackExecutor(self.registry, fallback_chains)
        self.execution_log: list[dict] = []

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool with full error handling"""
        start_time = time.time()
        log_entry = {
            "tool": tool_name,
            "args": kwargs,
            "attempts": 0,
            "success": False,
        }

        # Try with retries
        last_result = None
        for attempt in range(self.retry_config.max_retries + 1):
            log_entry["attempts"] = attempt + 1

            # Try with fallback
            result = self.fallback_executor.execute_with_fallback(tool_name, **kwargs)

            if result.success:
                log_entry["success"] = True
                log_entry["elapsed"] = time.time() - start_time
                self.execution_log.append(log_entry)
                return result

            last_result = result

            # Check if retryable
            if result.error and self.retry_config.is_retryable(result.error):
                if attempt < self.retry_config.max_retries:
                    delay = self.retry_config.get_delay(attempt)
                    print(f"  [Retry] Attempt {attempt + 1}: waiting {delay:.1f}s...")
                    time.sleep(delay)
                    continue

            # Not retryable, get advice
            advice = ErrorAdvisor.analyze(result.error or "", tool_name, kwargs)
            result.metadata["advice"] = advice
            break

        # All attempts failed
        log_entry["elapsed"] = time.time() - start_time
        log_entry["error"] = last_result.error if last_result else "Unknown error"
        self.execution_log.append(log_entry)

        return last_result or ToolResult(success=False, data="", error="Unknown error")

    def get_stats(self) -> dict:
        """Get execution statistics"""
        total = len(self.execution_log)
        success = sum(1 for e in self.execution_log if e["success"])
        avg_attempts = sum(e["attempts"] for e in self.execution_log) / max(total, 1)

        return {
            "total_executions": total,
            "successful": success,
            "failed": total - success,
            "success_rate": f"{success / max(total, 1) * 100:.1f}%",
            "avg_attempts": f"{avg_attempts:.1f}",
        }


# ============================================================
# 7. 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 2: Error Handling 演示")
    print("=" * 60)

    # ---- Part A: Retry strategies ----
    print("\n--- Part A: 重试策略 ---")
    configs = [
        ("Fixed", RetryConfig(strategy=RetryStrategy.FIXED, base_delay=1.0)),
        ("Linear", RetryConfig(strategy=RetryStrategy.LINEAR, base_delay=0.5)),
        ("Exponential", RetryConfig(strategy=RetryStrategy.EXPONENTIAL, base_delay=0.5)),
        ("Jitter", RetryConfig(strategy=RetryStrategy.JITTER, base_delay=0.5)),
    ]

    for name, config in configs:
        delays = [config.get_delay(i) for i in range(5)]
        print(f"  {name:12}: {[f'{d:.1f}s' for d in delays]}")

    # ---- Part B: Retry decorator ----
    print("\n--- Part B: 重试装饰器 ---")

    call_count = 0

    @with_retry(RetryConfig(max_retries=3, strategy=RetryStrategy.FIXED, base_delay=0.1))
    def flaky_tool(succeed_on: int = 3) -> ToolResult:
        """A tool that fails a few times before succeeding"""
        nonlocal call_count
        call_count += 1
        if call_count < succeed_on:
            return ToolResult(success=False, data="", error="Temporary connection error")
        return ToolResult(success=True, data=f"Success on attempt {call_count}")

    call_count = 0
    result = flaky_tool(succeed_on=3)
    print(f"  Flaky tool result: {result}")

    # ---- Part C: Error advisor ----
    print("\n--- Part C: 错误建议 ---")

    test_errors = [
        ("read_file", "File not found: /tmp/nonexistent.txt", {"file_path": "/tmp/nonexistent.txt"}),
        ("read_file", "Cannot read binary file: image.png", {"file_path": "image.png"}),
        ("web_summary", "HTTP 429: rate limited", {"url": "https://example.com"}),
        ("read_file", "File too large: 500KB", {"file_path": "huge.log"}),
    ]

    for tool, error, args in test_errors:
        advice = ErrorAdvisor.analyze(error, tool, args)
        print(f"\n  Error: {error}")
        print(f"  Suggestion: {advice['suggestion']}")
        if advice.get("alternative_tool"):
            print(f"  Try: {advice['alternative_tool']}")

    # ---- Part D: Robust executor ----
    print("\n--- Part D: 健壮执行器 ---")

    executor = RobustToolExecutor()

    # Success case
    result = executor.execute("read_file", file_path=__file__)
    print(f"\n  Read self: success={result.success}, lines={result.metadata.get('lines', '?')}")

    # Failure case
    result = executor.execute("read_file", file_path="/nonexistent/file.txt")
    print(f"  Nonexistent: success={result.success}, error={result.error}")
    if "advice" in result.metadata:
        print(f"  Advice: {result.metadata['advice']['suggestion']}")

    # Calculator (no fallback needed)
    result = executor.execute("calculator", expression="42 * 3.14")
    print(f"  Calculator: {result}")

    # Stats
    print(f"\n  Execution stats: {executor.get_stats()}")


    # ============================================================
    # 练习题
    # ============================================================

    print("\n" + "=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 实现 Circuit Breaker 模式
    # 如果一个工具连续失败 N 次，暂时"熔断"它，直接返回错误
    # 过一段时间后再"半开"尝试
    # 类比前端：API 熔断器，避免持续请求已经宕机的服务

    # TODO 2: 给 ErrorAdvisor 添加更多错误模式
    # - 编码错误 (UnicodeDecodeError)
    # - 内存不足 (MemoryError)
    # - JSON 解析错误 (JSONDecodeError)

    # TODO 3: 实现错误分类和统计
    # 统计每种错误类型出现的次数
    # 生成错误报告，帮助优化工具实现
