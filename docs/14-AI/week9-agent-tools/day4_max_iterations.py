"""
Day 4: 添加最大迭代次数限制，防止死循环
Agent 可能陷入无限循环（一直调用工具却无法得到答案），必须有安全机制
类比前端：请求超时 (axios timeout)、递归深度限制、watchdog timer
"""

import json
import time
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from langchain_community.llms import Ollama

# Import from previous days
from day1_tool_functions import (
    TOOL_REGISTRY,
    ToolResult,
    execute_tool,
    get_tools_description,
)
from day3_react_loop import (
    ReActStep,
    ReActTrace,
    StepType,
    parse_react_output,
    REACT_SYSTEM_PROMPT,
    REACT_STEP_PROMPT,
)


# ============================================================
# 1. 为什么需要迭代限制
# ============================================================

"""
Agent 可能死循环的场景：

1. 工具返回不相关的结果 → Agent 反复调用同一工具
2. LLM 理解错误 → 反复做同一件事
3. 任务太复杂 → Agent 不断拆分子任务但无法收敛
4. 工具持续失败 → 无限重试

类比前端：
┌─────────────────────────────────────────────────────┐
│ 前端防无限循环的方式           Agent 对应方案         │
├─────────────────────────────────────────────────────┤
│ axios.timeout                 max_iterations         │
│ React re-render limit (50)    最大步骤数             │
│ retry with maxRetries         重试次数上限           │
│ AbortController               强制终止               │
│ useEffect cleanup             资源清理               │
│ setTimeout fallback           超时降级回答           │
└─────────────────────────────────────────────────────┘
"""


# ============================================================
# 2. 守护配置
# ============================================================

@dataclass
class GuardConfig:
    """Configuration for agent safety guards"""
    # Maximum number of ReAct iterations
    max_iterations: int = 10
    # Maximum time in seconds for the entire run
    max_time_seconds: float = 120.0
    # Maximum consecutive calls to the same tool
    max_same_tool_calls: int = 3
    # Maximum total tool calls across all iterations
    max_total_tool_calls: int = 15
    # Whether to provide a fallback answer on timeout
    fallback_on_timeout: bool = True
    # Fallback answer template
    fallback_message: str = "I wasn't able to fully answer your question within the time/iteration limit. Here's what I found so far:\n{partial_info}"


@dataclass
class GuardState:
    """Runtime state for guard checks"""
    iteration_count: int = 0
    total_tool_calls: int = 0
    tool_call_counts: dict = field(default_factory=dict)  # tool_name -> count
    consecutive_same_tool: int = 0
    last_tool_name: Optional[str] = None
    start_time: float = 0.0
    stop_reason: Optional[str] = None

    def record_tool_call(self, tool_name: str) -> None:
        """Record a tool call and update counters"""
        self.total_tool_calls += 1
        self.tool_call_counts[tool_name] = self.tool_call_counts.get(tool_name, 0) + 1

        if tool_name == self.last_tool_name:
            self.consecutive_same_tool += 1
        else:
            self.consecutive_same_tool = 1
        self.last_tool_name = tool_name


# ============================================================
# 3. 守护检查器
# ============================================================

class GuardChecker:
    """
    Checks safety conditions before each iteration.
    Similar to middleware in Express.js that checks request limits.
    """

    def __init__(self, config: GuardConfig):
        self.config = config

    def check(self, state: GuardState) -> Optional[str]:
        """
        Check all guard conditions.
        Returns None if OK, or a reason string if the agent should stop.
        """
        # Check 1: Max iterations
        if state.iteration_count >= self.config.max_iterations:
            return f"Reached max iterations ({self.config.max_iterations})"

        # Check 2: Max time
        elapsed = time.time() - state.start_time
        if elapsed > self.config.max_time_seconds:
            return f"Timeout: {elapsed:.1f}s > {self.config.max_time_seconds}s"

        # Check 3: Same tool called too many times consecutively
        if state.consecutive_same_tool >= self.config.max_same_tool_calls:
            return (
                f"Tool '{state.last_tool_name}' called {state.consecutive_same_tool} "
                f"times consecutively (max: {self.config.max_same_tool_calls})"
            )

        # Check 4: Total tool calls
        if state.total_tool_calls >= self.config.max_total_tool_calls:
            return f"Total tool calls ({state.total_tool_calls}) reached limit ({self.config.max_total_tool_calls})"

        return None


# ============================================================
# 4. 带守护的 ReAct Agent
# ============================================================

class GuardedReActAgent:
    """
    ReAct Agent with safety guards to prevent infinite loops.
    Extends the basic ReActAgent from Day 3 with guard checks.
    """

    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        guard_config: Optional[GuardConfig] = None,
        on_step: Optional[Callable[[ReActStep], None]] = None,
    ):
        self.llm = Ollama(model=model_name)
        self.guard_config = guard_config or GuardConfig()
        self.guard_checker = GuardChecker(self.guard_config)
        self.on_step = on_step  # Callback for each step (for UI updates)

    def _emit_step(self, step: ReActStep) -> None:
        """Notify listener about a new step"""
        if self.on_step:
            self.on_step(step)

    def _build_fallback_answer(self, trace: ReActTrace, reason: str) -> str:
        """Build a fallback answer from partial information"""
        # Collect all observations as partial info
        observations = [
            s.content for s in trace.steps
            if s.step_type == StepType.OBSERVE
        ]
        partial_info = "\n".join(observations) if observations else "No information gathered."

        return self.guard_config.fallback_message.format(
            partial_info=partial_info[:1000],
        ) + f"\n\n(Stopped: {reason})"

    def run(self, question: str) -> ReActTrace:
        """Execute the ReAct loop with safety guards"""
        trace = ReActTrace(question=question)
        guard_state = GuardState(start_time=time.time())
        history_lines = []

        print(f"\n{'='*60}")
        print(f"Guarded ReAct Agent")
        print(f"Question: {question}")
        print(f"Guards: max_iter={self.guard_config.max_iterations}, "
              f"max_time={self.guard_config.max_time_seconds}s, "
              f"max_same_tool={self.guard_config.max_same_tool_calls}")
        print(f"{'='*60}")

        while True:
            guard_state.iteration_count += 1
            trace.total_iterations = guard_state.iteration_count

            # ---- Guard Check (before each iteration) ----
            stop_reason = self.guard_checker.check(guard_state)
            if stop_reason:
                print(f"\n  [GUARD] Stopping: {stop_reason}")
                guard_state.stop_reason = stop_reason
                trace.final_answer = self._build_fallback_answer(trace, stop_reason)
                break

            # ---- Build prompt ----
            history_text = "\n".join(history_lines) if history_lines else "(No previous steps)"
            prompt = REACT_STEP_PROMPT.format(
                question=question,
                history=history_text,
            )
            if guard_state.iteration_count == 1:
                prompt = REACT_SYSTEM_PROMPT.format(
                    tools_description=get_tools_description(),
                ) + "\n\n" + prompt

            # ---- LLM call ----
            iteration = guard_state.iteration_count
            print(f"\n  [Iteration {iteration}] Asking LLM...")

            try:
                llm_output = self.llm.invoke(prompt)
            except Exception as e:
                trace.final_answer = f"[LLM Error: {e}]"
                break

            # ---- Parse ----
            parsed = parse_react_output(llm_output)

            # Record thought
            if parsed["thought"]:
                step = ReActStep(
                    step_type=StepType.THINK,
                    content=parsed["thought"],
                    iteration=iteration,
                )
                trace.steps.append(step)
                self._emit_step(step)
                history_lines.append(f"Thought: {parsed['thought']}")
                print(f"  [Thought] {parsed['thought'][:100]}...")

            # Check for final answer
            if parsed["answer"]:
                step = ReActStep(
                    step_type=StepType.ANSWER,
                    content=parsed["answer"],
                    iteration=iteration,
                )
                trace.steps.append(step)
                self._emit_step(step)
                trace.final_answer = parsed["answer"]
                print(f"  [Answer] {parsed['answer'][:100]}...")
                break

            # Execute tool action
            if parsed["action"]:
                tool_name = parsed["action"]["tool"]
                tool_args = parsed["action"]["arguments"]

                # Record tool call for guard tracking
                guard_state.record_tool_call(tool_name)

                # Check guard again after recording the tool call
                stop_reason = self.guard_checker.check(guard_state)
                if stop_reason:
                    print(f"\n  [GUARD] Stopping: {stop_reason}")
                    trace.final_answer = self._build_fallback_answer(trace, stop_reason)
                    break

                # Record action step
                act_step = ReActStep(
                    step_type=StepType.ACT,
                    content=f"Calling {tool_name}",
                    tool_name=tool_name,
                    tool_args=tool_args,
                    iteration=iteration,
                )
                trace.steps.append(act_step)
                self._emit_step(act_step)
                history_lines.append(f"Action: {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")
                print(f"  [Action] {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")

                # Execute tool
                tool_result = execute_tool(tool_name, **tool_args)
                result_text = str(tool_result)
                if len(result_text) > 1500:
                    result_text = result_text[:1500] + "\n... (truncated)"

                # Record observation
                obs_step = ReActStep(
                    step_type=StepType.OBSERVE,
                    content=result_text,
                    tool_result=result_text,
                    iteration=iteration,
                )
                trace.steps.append(obs_step)
                self._emit_step(obs_step)
                history_lines.append(f"Observation: {result_text}")
                print(f"  [Observe] {result_text[:100]}...")

            else:
                # No action and no answer
                history_lines.append("Observation: No action taken. Please either call a tool or provide an Answer.")

        # Print timing info
        elapsed = time.time() - guard_state.start_time
        print(f"\n  [Done] {guard_state.iteration_count} iterations, "
              f"{guard_state.total_tool_calls} tool calls, "
              f"{elapsed:.1f}s elapsed")
        if guard_state.stop_reason:
            print(f"  [Stop reason] {guard_state.stop_reason}")

        return trace


# ============================================================
# 5. Mock Guarded Agent（不需要 Ollama）
# ============================================================

class MockGuardedAgent:
    """
    Simulates a guarded agent that intentionally triggers guard limits.
    Useful for testing guard logic without LLM.
    """

    def __init__(self, guard_config: Optional[GuardConfig] = None):
        self.guard_config = guard_config or GuardConfig(max_iterations=5)
        self.guard_checker = GuardChecker(self.guard_config)

    def run_infinite_loop_demo(self) -> ReActTrace:
        """Demo: agent that keeps calling the same tool (triggers same-tool guard)"""
        trace = ReActTrace(question="Demo: infinite loop detection")
        guard_state = GuardState(start_time=time.time())

        print(f"\n{'='*60}")
        print("Demo: Same-tool guard (max_same_tool_calls)")
        print(f"{'='*60}")

        while True:
            guard_state.iteration_count += 1
            trace.total_iterations = guard_state.iteration_count

            # Check guard
            stop_reason = self.guard_checker.check(guard_state)
            if stop_reason:
                print(f"  [GUARD] Stopped at iteration {guard_state.iteration_count}: {stop_reason}")
                trace.final_answer = f"Stopped: {stop_reason}"
                break

            # Simulate calling list_directory every time (will trigger same-tool guard)
            guard_state.record_tool_call("list_directory")
            print(f"  [Iteration {guard_state.iteration_count}] Called list_directory "
                  f"(consecutive: {guard_state.consecutive_same_tool})")

            trace.steps.append(ReActStep(
                step_type=StepType.ACT,
                content="Calling list_directory again",
                tool_name="list_directory",
                iteration=guard_state.iteration_count,
            ))

        return trace

    def run_timeout_demo(self) -> ReActTrace:
        """Demo: agent that runs too long (triggers timeout guard)"""
        config = GuardConfig(max_time_seconds=2.0, max_iterations=100)
        checker = GuardChecker(config)
        trace = ReActTrace(question="Demo: timeout detection")
        guard_state = GuardState(start_time=time.time())

        print(f"\n{'='*60}")
        print(f"Demo: Timeout guard (max_time={config.max_time_seconds}s)")
        print(f"{'='*60}")

        while True:
            guard_state.iteration_count += 1
            trace.total_iterations = guard_state.iteration_count

            stop_reason = checker.check(guard_state)
            if stop_reason:
                elapsed = time.time() - guard_state.start_time
                print(f"  [GUARD] Stopped at {elapsed:.1f}s: {stop_reason}")
                trace.final_answer = f"Stopped: {stop_reason}"
                break

            # Simulate slow work
            time.sleep(0.5)
            guard_state.record_tool_call("slow_tool")
            print(f"  [Iteration {guard_state.iteration_count}] "
                  f"Elapsed: {time.time() - guard_state.start_time:.1f}s")

        return trace

    def run_total_calls_demo(self) -> ReActTrace:
        """Demo: agent that makes too many total tool calls"""
        config = GuardConfig(max_total_tool_calls=5, max_same_tool_calls=10, max_iterations=20)
        checker = GuardChecker(config)
        trace = ReActTrace(question="Demo: total tool calls limit")
        guard_state = GuardState(start_time=time.time())

        print(f"\n{'='*60}")
        print(f"Demo: Total tool calls guard (max={config.max_total_tool_calls})")
        print(f"{'='*60}")

        tools = ["read_file", "search_text", "list_directory"]
        i = 0

        while True:
            guard_state.iteration_count += 1

            stop_reason = checker.check(guard_state)
            if stop_reason:
                print(f"  [GUARD] Stopped: {stop_reason}")
                trace.final_answer = f"Stopped: {stop_reason}"
                break

            tool = tools[i % len(tools)]
            guard_state.record_tool_call(tool)
            i += 1
            print(f"  [Iteration {guard_state.iteration_count}] Called {tool} "
                  f"(total calls: {guard_state.total_tool_calls})")

        trace.total_iterations = guard_state.iteration_count
        return trace


# ============================================================
# 6. 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 4: Max Iterations & Guards 演示")
    print("=" * 60)

    mock = MockGuardedAgent(
        guard_config=GuardConfig(
            max_iterations=10,
            max_same_tool_calls=3,
            max_time_seconds=120.0,
        )
    )

    # Demo 1: Same tool guard
    trace1 = mock.run_infinite_loop_demo()
    print(f"\n  Result: {trace1.final_answer}")

    # Demo 2: Timeout guard
    trace2 = mock.run_timeout_demo()
    print(f"\n  Result: {trace2.final_answer}")

    # Demo 3: Total calls guard
    trace3 = mock.run_total_calls_demo()
    print(f"\n  Result: {trace3.final_answer}")

    # Demo 4: Real guarded agent (requires Ollama)
    print("\n--- Real Guarded Agent (requires Ollama) ---")
    try:
        agent = GuardedReActAgent(
            guard_config=GuardConfig(
                max_iterations=3,
                max_same_tool_calls=2,
                max_time_seconds=60.0,
            ),
            on_step=lambda step: print(f"    [Callback] {step}"),
        )
        trace = agent.run("读取 day1_tool_functions.py 的前 10 行内容")
        print(trace.display())
    except Exception as e:
        print(f"[Ollama not available: {e}]")


    # ============================================================
    # 练习题
    # ============================================================

    print("\n" + "=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 添加 "token budget" 守护
    # 估算每次 LLM 调用的 token 数量，当总 token 超过预算时停止
    # 提示：可以用 len(text) // 4 粗略估算 token 数

    # TODO 2: 实现 "指数退避" (exponential backoff)
    # 当同一工具连续调用时，每次增加等待时间
    # 第 1 次: 0s, 第 2 次: 1s, 第 3 次: 2s, 第 4 次: 4s

    # TODO 3: 实现 "循环检测" (loop detection)
    # 如果 Agent 连续两步的 Thought 内容高度相似（>80%），判定为循环
    # 提示：可以用 difflib.SequenceMatcher 计算相似度
