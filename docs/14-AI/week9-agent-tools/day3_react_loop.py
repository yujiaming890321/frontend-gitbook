"""
Day 3: ReAct 循环 — Think -> Call Tool -> Observe -> Think again
ReAct = Reasoning + Acting，让 Agent 交替"思考"和"行动"
类比前端：类似 Redux Saga 的 yield 模式，或事件循环的 process → dispatch → process
"""

import json
import re
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
from langchain_community.llms import Ollama

# Import tools from Day 1
from day1_tool_functions import (
    TOOL_REGISTRY,
    ToolResult,
    execute_tool,
    get_tools_description,
)


# ============================================================
# 1. ReAct 模式详解
# ============================================================

"""
ReAct 循环的工作流程：

┌──────────────────────────────────────────────────────────┐
│                    ReAct 循环                             │
│                                                          │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐              │
│  │ THINK   │──→│  ACT     │──→│ OBSERVE │──→ 继续?      │
│  │ 分析问题 │   │ 调用工具  │   │ 查看结果 │     │         │
│  │ 制定计划 │   │ 执行动作  │   │ 提取信息 │     ▼         │
│  └─────────┘   └──────────┘   └─────────┘   ┌───┐      │
│       ▲                                      │ 是 │      │
│       └──────────────── 需要更多信息 ──────────┘   │      │
│                                              ┌───┐      │
│                                              │ 否 │      │
│                                              └─┬─┘      │
│                                                │         │
│                                          ┌─────────┐    │
│                                          │ ANSWER  │    │
│                                          │ 最终回答 │    │
│                                          └─────────┘    │
└──────────────────────────────────────────────────────────┘

类比前端 Redux Saga：
  function* fetchDataSaga(action) {
    const plan = yield think(action);     // THINK
    const data = yield call(api, plan);   // ACT
    const result = yield put(data);       // OBSERVE
    if (needMore) goto THINK;             // LOOP
    yield put(finalResult);               // ANSWER
  }
"""


# ============================================================
# 2. ReAct Step 数据结构
# ============================================================

class StepType(Enum):
    """Type of step in the ReAct loop"""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    ANSWER = "answer"


@dataclass
class ReActStep:
    """One step in the ReAct reasoning chain"""
    step_type: StepType
    content: str
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    tool_result: Optional[str] = None
    iteration: int = 0

    def __str__(self) -> str:
        prefix = {
            StepType.THINK: "Thought",
            StepType.ACT: "Action",
            StepType.OBSERVE: "Observation",
            StepType.ANSWER: "Answer",
        }[self.step_type]
        return f"[{prefix} #{self.iteration}] {self.content[:200]}"


@dataclass
class ReActTrace:
    """Complete trace of a ReAct execution"""
    question: str
    steps: list[ReActStep] = field(default_factory=list)
    final_answer: str = ""
    total_iterations: int = 0

    def display(self) -> str:
        """Format the full trace for display"""
        lines = [
            f"\n{'='*60}",
            f"ReAct Trace: {self.question}",
            f"{'='*60}",
        ]
        for step in self.steps:
            lines.append(str(step))
        lines.append(f"\nFinal Answer: {self.final_answer[:500]}")
        lines.append(f"Total iterations: {self.total_iterations}")
        return "\n".join(lines)


# ============================================================
# 3. ReAct Prompt 模板
# ============================================================

REACT_SYSTEM_PROMPT = """You are a helpful assistant that follows the ReAct pattern to answer questions.

You have access to the following tools:
{tools_description}

For each step, you MUST use this EXACT format:

Thought: [Your reasoning about what to do next]
Action: ```tool_call
{{"tool": "tool_name", "arguments": {{"arg1": "value1"}}}}
```

After receiving an observation (tool result), you'll think again.

When you have enough information to answer, respond with:

Thought: I now have enough information to answer.
Answer: [Your final answer here]

IMPORTANT:
- Always start with a Thought
- Only call ONE tool per step
- Be specific in your reasoning
- Answer in Chinese when appropriate"""


REACT_STEP_PROMPT = """Question: {question}

{history}

Now continue the ReAct process. What is your next thought?"""


# ============================================================
# 4. ReAct 解析器
# ============================================================

def parse_react_output(llm_output: str) -> dict:
    """
    Parse LLM output to extract Thought, Action, and Answer.
    Returns a dict with keys: thought, action (optional), answer (optional)
    """
    result = {
        "thought": "",
        "action": None,
        "answer": None,
    }

    # Extract Thought
    thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|Answer:|$)", llm_output, re.DOTALL)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()

    # Extract Answer (check this before Action)
    answer_match = re.search(r"Answer:\s*(.+?)$", llm_output, re.DOTALL)
    if answer_match:
        result["answer"] = answer_match.group(1).strip()
        return result  # If there's an answer, we're done

    # Extract Action (tool call)
    action_pattern = r"```tool_call\s*\n?(.*?)\n?\s*```"
    action_match = re.search(action_pattern, llm_output, re.DOTALL)

    if not action_match:
        # Fallback: look for JSON with tool key
        action_pattern2 = r"```(?:json)?\s*\n?(\{[^}]*\"tool\"[^}]*\})\n?\s*```"
        action_match = re.search(action_pattern2, llm_output, re.DOTALL)

    if action_match:
        try:
            action_data = json.loads(action_match.group(1).strip())
            result["action"] = {
                "tool": action_data.get("tool", ""),
                "arguments": action_data.get("arguments", {}),
            }
        except json.JSONDecodeError:
            pass

    return result


# ============================================================
# 5. ReAct Agent 核心
# ============================================================

class ReActAgent:
    """
    An agent that follows the ReAct pattern.
    Think → Act → Observe → Think → ... → Answer
    """

    def __init__(self, model_name: str = "qwen2.5:7b", max_iterations: int = 5):
        self.llm = Ollama(model=model_name)
        self.max_iterations = max_iterations

    def run(self, question: str) -> ReActTrace:
        """Execute the ReAct loop for a given question"""
        trace = ReActTrace(question=question)
        history_lines = []

        for iteration in range(1, self.max_iterations + 1):
            trace.total_iterations = iteration

            # Build prompt with history
            history_text = "\n".join(history_lines) if history_lines else "(No previous steps)"
            prompt = REACT_STEP_PROMPT.format(
                question=question,
                history=history_text,
            )

            # Add system prompt on first iteration
            if iteration == 1:
                prompt = REACT_SYSTEM_PROMPT.format(
                    tools_description=get_tools_description(),
                ) + "\n\n" + prompt

            # Get LLM response
            print(f"\n  [Iteration {iteration}] Asking LLM...")
            try:
                llm_output = self.llm.invoke(prompt)
            except Exception as e:
                trace.final_answer = f"[LLM Error: {e}]"
                break

            # Parse the response
            parsed = parse_react_output(llm_output)

            # Record thought
            if parsed["thought"]:
                step = ReActStep(
                    step_type=StepType.THINK,
                    content=parsed["thought"],
                    iteration=iteration,
                )
                trace.steps.append(step)
                history_lines.append(f"Thought: {parsed['thought']}")
                print(f"  [Thought] {parsed['thought'][:100]}...")

            # Check if we have a final answer
            if parsed["answer"]:
                step = ReActStep(
                    step_type=StepType.ANSWER,
                    content=parsed["answer"],
                    iteration=iteration,
                )
                trace.steps.append(step)
                trace.final_answer = parsed["answer"]
                print(f"  [Answer] {parsed['answer'][:100]}...")
                break

            # Execute tool if action was requested
            if parsed["action"]:
                tool_name = parsed["action"]["tool"]
                tool_args = parsed["action"]["arguments"]

                # Record action step
                act_step = ReActStep(
                    step_type=StepType.ACT,
                    content=f"Calling {tool_name} with {json.dumps(tool_args, ensure_ascii=False)}",
                    tool_name=tool_name,
                    tool_args=tool_args,
                    iteration=iteration,
                )
                trace.steps.append(act_step)
                history_lines.append(f"Action: {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")
                print(f"  [Action] {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")

                # Execute the tool
                tool_result = execute_tool(tool_name, **tool_args)

                # Truncate result if too long to avoid context overflow
                result_text = str(tool_result)
                if len(result_text) > 1500:
                    result_text = result_text[:1500] + "\n... (truncated)"

                # Record observation step
                obs_step = ReActStep(
                    step_type=StepType.OBSERVE,
                    content=result_text,
                    tool_result=result_text,
                    iteration=iteration,
                )
                trace.steps.append(obs_step)
                history_lines.append(f"Observation: {result_text}")
                print(f"  [Observe] {result_text[:100]}...")

            else:
                # No action and no answer: LLM might be stuck
                if not parsed["answer"]:
                    history_lines.append(f"Observation: No action taken. Please either call a tool or provide an Answer.")

        # If we exhausted iterations without an answer
        if not trace.final_answer:
            trace.final_answer = "Reached maximum iterations without a final answer."

        return trace


# ============================================================
# 6. Mock ReAct Agent（不需要 Ollama）
# ============================================================

class MockReActAgent:
    """
    A mock ReAct agent that simulates the loop without LLM.
    Useful for understanding the flow and testing.
    """

    def run(self, question: str) -> ReActTrace:
        """Simulate a ReAct loop with hardcoded steps"""
        trace = ReActTrace(question=question)

        # Simulated step 1: Think
        trace.steps.append(ReActStep(
            step_type=StepType.THINK,
            content="I need to understand the project structure first. Let me list the directory.",
            iteration=1,
        ))

        # Simulated step 2: Act
        trace.steps.append(ReActStep(
            step_type=StepType.ACT,
            content='Calling list_directory with {"directory": "."}',
            tool_name="list_directory",
            tool_args={"directory": "."},
            iteration=1,
        ))

        # Execute the real tool
        result = execute_tool("list_directory", directory=".")
        result_text = str(result)[:500]

        # Simulated step 3: Observe
        trace.steps.append(ReActStep(
            step_type=StepType.OBSERVE,
            content=result_text,
            tool_result=result_text,
            iteration=1,
        ))

        # Simulated step 4: Think again
        trace.steps.append(ReActStep(
            step_type=StepType.THINK,
            content="Now I can see the project structure. Let me look for Python files to answer the question.",
            iteration=2,
        ))

        # Simulated step 5: Act again
        trace.steps.append(ReActStep(
            step_type=StepType.ACT,
            content='Calling search_text with {"directory": ".", "pattern": "def "}',
            tool_name="search_text",
            tool_args={"directory": ".", "pattern": "def "},
            iteration=2,
        ))

        search_result = execute_tool("search_text", directory=".", pattern="def ")
        search_text_result = str(search_result)[:500]

        trace.steps.append(ReActStep(
            step_type=StepType.OBSERVE,
            content=search_text_result,
            tool_result=search_text_result,
            iteration=2,
        ))

        # Final answer
        trace.steps.append(ReActStep(
            step_type=StepType.ANSWER,
            content=f"Based on the directory listing and function search, I found the project structure and key functions.",
            iteration=3,
        ))

        trace.final_answer = "Mock agent completed the ReAct loop successfully."
        trace.total_iterations = 3
        return trace


# ============================================================
# 7. 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Day 3: ReAct Loop 演示")
    print("=" * 60)

    # ---- Part A: Parse ReAct output ----
    print("\n--- Part A: 解析 ReAct 输出 ---")

    test_output_1 = """Thought: I need to find out what files are in the current directory.
Action: ```tool_call
{"tool": "list_directory", "arguments": {"directory": "."}}
```"""

    test_output_2 = """Thought: I now have enough information to answer.
Answer: The project contains 3 Python files that define tool functions for the agent."""

    for i, output in enumerate([test_output_1, test_output_2], 1):
        parsed = parse_react_output(output)
        print(f"\n  Test {i}:")
        print(f"    Thought: {parsed['thought'][:80]}")
        print(f"    Action: {parsed['action']}")
        print(f"    Answer: {parsed['answer']}")

    # ---- Part B: Mock ReAct Agent ----
    print("\n--- Part B: Mock ReAct Agent ---")
    mock_agent = MockReActAgent()
    trace = mock_agent.run("这个项目里有哪些函数？")
    print(trace.display())

    # ---- Part C: Real ReAct Agent (requires Ollama) ----
    print("\n--- Part C: Real ReAct Agent (requires Ollama) ---")
    try:
        agent = ReActAgent(max_iterations=3)
        trace = agent.run("列出当前目录的文件结构，并告诉我有哪些 Python 文件")
        print(trace.display())
    except Exception as e:
        print(f"[Ollama not available: {e}]")
        print("Use MockReActAgent for testing without Ollama.")


    # ============================================================
    # 练习题
    # ============================================================

    print("\n" + "=" * 50)
    print("练习题")
    print("=" * 50)

    # TODO 1: 给 ReActTrace 添加一个 to_markdown() 方法
    # 把整个思考链格式化为 Markdown 文档
    # 包含每步的类型、内容和工具调用

    # TODO 2: 实现 "思考链可视化"
    # 用 ASCII art 画出每步的流程
    # 例如:  [THINK] → [ACT: read_file] → [OBSERVE] → [THINK] → [ANSWER]

    # TODO 3: 给 ReActAgent 添加 "反思" 能力
    # 如果工具执行失败，让 LLM 分析原因并尝试用其他工具
