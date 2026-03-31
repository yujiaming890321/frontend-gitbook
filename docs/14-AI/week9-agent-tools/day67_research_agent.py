"""
Day 6-7: 综合 — 能搜文档 + 生成摘要的 Research Agent

这个项目综合运用本周所有知识点：
- Day 1: 工具函数（文件读取、文本搜索）
- Day 2: Tool Calling（让 LLM 选择工具）
- Day 3: ReAct 循环（Think → Act → Observe）
- Day 4: 最大迭代限制（防止死循环）
- Day 5: RAG 作为工具（语义搜索知识库）

用法:
  python day67_research_agent.py research "什么是 Agent 的 ReAct 模式"
  python day67_research_agent.py ingest ./docs
  python day67_research_agent.py interactive
"""

import sys
import json
import time
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import chromadb
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import from previous days
from day1_tool_functions import (
    ToolResult,
    read_file,
    search_text,
    list_directory,
)
from day3_react_loop import ReActStep, ReActTrace, StepType, parse_react_output
from day4_max_iterations import GuardConfig, GuardState, GuardChecker


# ============================================================
# 1. Research Agent 的设计
# ============================================================

"""
Research Agent 的工作流程：

用户提问: "解释 RAG 的工作原理"
                │
                ▼
┌──────────────────────────────┐
│ Step 1: THINK                │
│ "我需要搜索知识库中关于       │
│  RAG 的文档"                  │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Step 2: ACT - rag_search     │
│ query: "RAG 工作原理"         │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Step 3: OBSERVE              │
│ 找到 3 段相关文档              │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Step 4: THINK                │
│ "还需要看看具体代码示例"       │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Step 5: ACT - search_text    │
│ pattern: "RAG", ext: ".py"   │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Step 6: OBSERVE              │
│ 找到代码中的 RAG 实现          │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Step 7: ANSWER               │
│ 综合所有信息生成结构化摘要      │
└──────────────────────────────┘
"""


# ============================================================
# 2. 摘要生成工具
# ============================================================

def generate_summary(text: str, focus: str = "") -> ToolResult:
    """
    Generate a structured summary of the given text.
    When LLM is not available, produces a basic extractive summary.
    """
    try:
        if not text.strip():
            return ToolResult(success=False, data="", error="Empty text provided")

        # Try LLM-based summary first
        try:
            llm = Ollama(model="qwen2.5:7b")
            focus_instruction = f"\nFocus on: {focus}" if focus else ""
            prompt = f"""Please summarize the following text in Chinese.
Create a structured summary with:
1. Main topic (one sentence)
2. Key points (bullet list)
3. Conclusion
{focus_instruction}

Text:
{text[:3000]}

Summary:"""
            summary = llm.invoke(prompt)
            return ToolResult(
                success=True,
                data=summary,
                metadata={"method": "llm", "input_length": len(text)},
            )
        except Exception:
            pass

        # Fallback: basic extractive summary
        lines = text.strip().splitlines()
        non_empty = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]

        # Take first sentence, middle, and last sentence
        summary_parts = []
        if len(non_empty) >= 1:
            summary_parts.append(f"Opening: {non_empty[0][:200]}")
        if len(non_empty) >= 3:
            mid = len(non_empty) // 2
            summary_parts.append(f"Middle: {non_empty[mid][:200]}")
        if len(non_empty) >= 2:
            summary_parts.append(f"Closing: {non_empty[-1][:200]}")

        summary_parts.append(f"\n(Total: {len(lines)} lines, {len(text)} characters)")

        return ToolResult(
            success=True,
            data="\n".join(summary_parts),
            metadata={"method": "extractive", "input_length": len(text)},
        )

    except Exception as e:
        return ToolResult(success=False, data="", error=f"Summary error: {str(e)}")


# ============================================================
# 3. Research Agent 工具注册表
# ============================================================

class ResearchToolRegistry:
    """
    Tool registry for the Research Agent.
    Contains all tools needed for document research.
    """

    def __init__(self):
        self.tools: dict = {}
        self._kb = None
        self._register_default_tools()

    def _register_default_tools(self):
        """Register all built-in research tools"""
        self.tools = {
            "read_file": {
                "name": "read_file",
                "description": "Read the contents of a file. Use when you need to see specific file content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                    },
                    "required": ["file_path"],
                },
                "function": read_file,
            },
            "search_text": {
                "name": "search_text",
                "description": "Search for text patterns in files. Use for keyword-based code/doc search.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "Directory to search"},
                        "pattern": {"type": "string", "description": "Text/regex pattern"},
                        "file_extension": {"type": "string", "description": "File extension filter", "default": ".py"},
                    },
                    "required": ["directory", "pattern"],
                },
                "function": search_text,
            },
            "list_directory": {
                "name": "list_directory",
                "description": "List files and directories. Use to understand project structure.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "Directory path"},
                    },
                    "required": ["directory"],
                },
                "function": list_directory,
            },
            "generate_summary": {
                "name": "generate_summary",
                "description": "Generate a structured summary of text. Use after gathering enough information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to summarize"},
                        "focus": {"type": "string", "description": "Focus area for summary"},
                    },
                    "required": ["text"],
                },
                "function": generate_summary,
            },
            "rag_search": {
                "name": "rag_search",
                "description": "Semantic search in knowledge base. Use when you need to find conceptually related information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language query"},
                        "n_results": {"type": "integer", "description": "Number of results", "default": 5},
                    },
                    "required": ["query"],
                },
                "function": self._rag_search,
            },
        }

    def _rag_search(self, query: str, n_results: int = 5) -> ToolResult:
        """RAG search using the agent's knowledge base"""
        if self._kb is None:
            return ToolResult(
                success=False, data="",
                error="Knowledge base not initialized. Use 'ingest' command first.",
            )

        try:
            results = self._kb.query(
                query_texts=[query],
                n_results=min(n_results, self._kb.count()),
            )

            if not results["documents"][0]:
                return ToolResult(success=True, data="No results found.", metadata={"count": 0})

            lines = [f"Found {len(results['documents'][0])} results:\n"]
            for i, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                lines.append(f"--- Result #{i+1} (dist={dist:.4f}, source={meta.get('source', '?')}) ---")
                lines.append(doc[:500])
                lines.append("")

            return ToolResult(
                success=True,
                data="\n".join(lines),
                metadata={"count": len(results["documents"][0])},
            )
        except Exception as e:
            return ToolResult(success=False, data="", error=str(e))

    def set_knowledge_base(self, collection):
        """Set the Chroma collection for RAG search"""
        self._kb = collection

    def get_description(self) -> str:
        """Generate tool descriptions for the LLM prompt"""
        lines = ["Available tools:\n"]
        for name, tool in self.tools.items():
            lines.append(f"- {name}: {tool['description']}")
            for pname, pinfo in tool["parameters"]["properties"].items():
                req = pname in tool["parameters"].get("required", [])
                lines.append(f"    {pname}{'*' if req else ''}: {pinfo['description']}")
        return "\n".join(lines)

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name"""
        if tool_name not in self.tools:
            return ToolResult(
                success=False, data="",
                error=f"Unknown tool: {tool_name}. Available: {list(self.tools.keys())}",
            )
        return self.tools[tool_name]["function"](**kwargs)


# ============================================================
# 4. Research Agent 核心
# ============================================================

RESEARCH_SYSTEM_PROMPT = """You are a Research Agent that helps users understand codebases and documentation.

You follow the ReAct pattern: Think → Act → Observe → Think → ... → Answer

{tools_description}

For each step, use this format:

Thought: [Your reasoning]
Action: ```tool_call
{{"tool": "tool_name", "arguments": {{"arg1": "value1"}}}}
```

When you have enough information:

Thought: I have enough information to provide a comprehensive answer.
Answer: [Structured answer in Chinese with:
1. Overview (one sentence)
2. Key findings (bullet points)
3. Code examples (if relevant)
4. Summary]

IMPORTANT:
- Start by understanding the project structure (list_directory)
- Use rag_search for conceptual questions
- Use search_text for finding specific code
- Use read_file to see full file contents
- Generate a well-structured answer"""


class ResearchAgent:
    """
    A complete research agent that can explore codebases,
    search documentation, and generate structured summaries.
    """

    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        guard_config: Optional[GuardConfig] = None,
    ):
        self.model_name = model_name
        self.tool_registry = ResearchToolRegistry()
        self.guard_config = guard_config or GuardConfig(
            max_iterations=8,
            max_same_tool_calls=3,
            max_total_tool_calls=12,
            max_time_seconds=120.0,
        )
        self.guard_checker = GuardChecker(self.guard_config)

        # Knowledge base setup
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection("research_kb")
        self.tool_registry.set_knowledge_base(self.collection)

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50,
        )

        # Try to initialize LLM
        try:
            self.llm = Ollama(model=model_name)
            self._llm_available = True
        except Exception:
            self.llm = None
            self._llm_available = False

    def ingest_directory(self, directory: str) -> dict:
        """Ingest all documents from a directory into the knowledge base"""
        dir_path = Path(directory).resolve()
        stats = {"files": 0, "chunks": 0, "errors": []}

        extensions = [".py", ".md", ".txt", ".json"]
        for ext in extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                if any(p.startswith(".") or p in ("node_modules", "__pycache__", ".venv")
                       for p in file_path.parts):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8")
                    chunks = self.splitter.split_text(content)

                    if chunks:
                        ids = [f"{file_path.name}_{i}" for i in range(len(chunks))]
                        metadatas = [{"source": file_path.name, "path": str(file_path), "chunk": i}
                                     for i in range(len(chunks))]

                        # Avoid duplicate IDs
                        existing = set()
                        try:
                            existing_docs = self.collection.get()
                            existing = set(existing_docs["ids"])
                        except Exception:
                            pass

                        new_ids = []
                        new_chunks = []
                        new_metas = []
                        for id_, chunk, meta in zip(ids, chunks, metadatas):
                            if id_ not in existing:
                                new_ids.append(id_)
                                new_chunks.append(chunk)
                                new_metas.append(meta)

                        if new_ids:
                            self.collection.add(
                                ids=new_ids,
                                documents=new_chunks,
                                metadatas=new_metas,
                            )
                            stats["chunks"] += len(new_ids)

                        stats["files"] += 1

                except Exception as e:
                    stats["errors"].append(f"{file_path}: {e}")

        print(f"Ingested {stats['files']} files, {stats['chunks']} chunks")
        if stats["errors"]:
            print(f"Errors: {len(stats['errors'])}")
        return stats

    def research(self, question: str) -> ReActTrace:
        """Run the research loop for a question"""
        trace = ReActTrace(question=question)
        guard_state = GuardState(start_time=time.time())
        history_lines = []

        print(f"\n{'='*60}")
        print(f"Research Agent")
        print(f"Question: {question}")
        print(f"Knowledge base: {self.collection.count()} documents")
        print(f"{'='*60}")

        if not self._llm_available:
            # Fallback: use tools directly without LLM
            return self._research_without_llm(question, trace)

        while True:
            guard_state.iteration_count += 1
            trace.total_iterations = guard_state.iteration_count

            # Guard check
            stop_reason = self.guard_checker.check(guard_state)
            if stop_reason:
                print(f"\n  [GUARD] {stop_reason}")
                # Build answer from observations
                observations = [s.content for s in trace.steps if s.step_type == StepType.OBSERVE]
                trace.final_answer = f"Research stopped: {stop_reason}\n\nFindings:\n" + "\n".join(observations[:3])
                break

            # Build prompt
            history_text = "\n".join(history_lines) if history_lines else "(No previous steps)"
            prompt = f"""Question: {question}

{history_text}

Now continue. What is your next thought?"""

            if guard_state.iteration_count == 1:
                prompt = RESEARCH_SYSTEM_PROMPT.format(
                    tools_description=self.tool_registry.get_description(),
                ) + "\n\n" + prompt

            # LLM call
            iteration = guard_state.iteration_count
            print(f"\n  [Iteration {iteration}]")

            try:
                llm_output = self.llm.invoke(prompt)
            except Exception as e:
                trace.final_answer = f"[LLM Error: {e}]"
                break

            parsed = parse_react_output(llm_output)

            # Record thought
            if parsed["thought"]:
                step = ReActStep(step_type=StepType.THINK, content=parsed["thought"], iteration=iteration)
                trace.steps.append(step)
                history_lines.append(f"Thought: {parsed['thought']}")
                print(f"  [Thought] {parsed['thought'][:100]}...")

            # Final answer
            if parsed["answer"]:
                step = ReActStep(step_type=StepType.ANSWER, content=parsed["answer"], iteration=iteration)
                trace.steps.append(step)
                trace.final_answer = parsed["answer"]
                print(f"  [Answer] {parsed['answer'][:150]}...")
                break

            # Tool action
            if parsed["action"]:
                tool_name = parsed["action"]["tool"]
                tool_args = parsed["action"]["arguments"]
                guard_state.record_tool_call(tool_name)

                # Guard check after recording tool call
                stop_reason = self.guard_checker.check(guard_state)
                if stop_reason:
                    print(f"\n  [GUARD] {stop_reason}")
                    trace.final_answer = f"Stopped: {stop_reason}"
                    break

                act_step = ReActStep(
                    step_type=StepType.ACT, content=f"{tool_name}({json.dumps(tool_args, ensure_ascii=False)})",
                    tool_name=tool_name, tool_args=tool_args, iteration=iteration,
                )
                trace.steps.append(act_step)
                history_lines.append(f"Action: {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")
                print(f"  [Action] {tool_name}")

                tool_result = self.tool_registry.execute(tool_name, **tool_args)
                result_text = str(tool_result)[:2000]

                obs_step = ReActStep(
                    step_type=StepType.OBSERVE, content=result_text,
                    tool_result=result_text, iteration=iteration,
                )
                trace.steps.append(obs_step)
                history_lines.append(f"Observation: {result_text}")
                print(f"  [Observe] {result_text[:100]}...")
            else:
                history_lines.append("Observation: No action. Please use a tool or provide Answer.")

        elapsed = time.time() - guard_state.start_time
        print(f"\n  [Done] {trace.total_iterations} iterations, {guard_state.total_tool_calls} tools, {elapsed:.1f}s")
        return trace

    def _research_without_llm(self, question: str, trace: ReActTrace) -> ReActTrace:
        """Fallback research without LLM: use keyword-based tool selection"""
        print("  [Fallback] Running without LLM")

        # Step 1: Search knowledge base
        trace.steps.append(ReActStep(
            step_type=StepType.THINK,
            content="Searching knowledge base for relevant information",
            iteration=1,
        ))

        rag_result = self.tool_registry.execute("rag_search", query=question, n_results=3)
        trace.steps.append(ReActStep(
            step_type=StepType.OBSERVE, content=str(rag_result)[:500], iteration=1,
        ))

        # Step 2: Search in files
        trace.steps.append(ReActStep(
            step_type=StepType.THINK,
            content="Searching files for related keywords",
            iteration=2,
        ))

        # Extract key terms from question
        keywords = [w for w in question.split() if len(w) > 1]
        if keywords:
            search_result = self.tool_registry.execute(
                "search_text", directory=".", pattern=keywords[0], file_extension=".py",
            )
            trace.steps.append(ReActStep(
                step_type=StepType.OBSERVE, content=str(search_result)[:500], iteration=2,
            ))

        # Compile findings
        findings = [s.content for s in trace.steps if s.step_type == StepType.OBSERVE]
        trace.final_answer = f"Research findings for '{question}':\n\n" + "\n\n".join(findings)
        trace.total_iterations = 2
        return trace

    def interactive(self):
        """Run the agent in interactive mode"""
        print("\n" + "=" * 60)
        print("Research Agent - Interactive Mode")
        print("Commands: 'quit' to exit, 'ingest <dir>' to add documents")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            if user_input.startswith("ingest "):
                directory = user_input[7:].strip()
                self.ingest_directory(directory)
                continue

            if user_input == "stats":
                print(f"Knowledge base: {self.collection.count()} documents")
                print(f"LLM available: {self._llm_available}")
                continue

            trace = self.research(user_input)
            print("\n" + "=" * 40)
            print("Final Answer:")
            print("=" * 40)
            print(trace.final_answer)


# ============================================================
# 5. CLI 入口
# ============================================================

def print_usage():
    print("""
Research Agent — Week 9 综合项目

用法:
  python day67_research_agent.py research "<question>"     用 Agent 研究一个问题
  python day67_research_agent.py ingest <directory>        导入文档到知识库
  python day67_research_agent.py interactive               交互模式

示例:
  python day67_research_agent.py research "什么是 ReAct 模式"
  python day67_research_agent.py ingest .
  python day67_research_agent.py interactive
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1]
    agent = ResearchAgent()

    if command == "research" and len(sys.argv) >= 3:
        question = sys.argv[2]

        # Auto-ingest current directory
        print("Auto-ingesting current directory...")
        agent.ingest_directory(".")

        trace = agent.research(question)
        print("\n" + "=" * 60)
        print("Research Report")
        print("=" * 60)
        print(trace.display())

    elif command == "ingest" and len(sys.argv) >= 3:
        directory = sys.argv[2]
        agent.ingest_directory(directory)
        print(f"Knowledge base now has {agent.collection.count()} documents")

    elif command == "interactive":
        print("Auto-ingesting current directory...")
        agent.ingest_directory(".")
        agent.interactive()

    else:
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    # If no CLI args, run demo
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Day 6-7: Research Agent 演示")
        print("=" * 60)

        agent = ResearchAgent()

        # Ingest current directory
        print("\n--- Ingesting current directory ---")
        stats = agent.ingest_directory(".")
        print(f"Stats: {stats}")

        # Research question
        print("\n--- Research demo ---")
        trace = agent.research("这个项目里有哪些工具函数？它们的作用是什么？")
        print(trace.display())

    else:
        main()


    # ============================================================
    # 扩展练习（可选）
    # ============================================================

    # TODO 1: 添加 "compare" 命令
    # 比较两个文件的内容差异并生成报告
    # python day67_research_agent.py compare file1.py file2.py

    # TODO 2: 添加研究报告导出
    # 把 ReActTrace 导出为 Markdown 格式的研究报告
    # 包含思考链、工具调用记录和最终结论

    # TODO 3: 添加 "ask-followup" 能力
    # Agent 可以向用户提问来澄清需求
    # 比如：用户问 "解释这个函数"，Agent 反问 "你指的是哪个函数？"

    # TODO 4: 实现并行工具调用
    # 当 Agent 需要同时搜索多个关键词时，并行执行
    # 提示：用 asyncio.gather 或 concurrent.futures
