"""
Day 6-7: 综合练习 — 代码审查助手

综合运用本周所有 Prompt Engineering 技巧：
- Day 1: System Prompt（角色设计）
- Day 2: Few-Shot（输出格式示范）
- Day 3: CoT（分步分析）
- Day 4: 结构化输出（JSON 解析）
- Day 5: Function Calling（工具调用）

用法:
  python day67_code_reviewer.py review file.py       # 审查文件
  python day67_code_reviewer.py review file.py -l zh  # 中文审查
  python day67_code_reviewer.py suggest file.py       # 重构建议
"""

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Literal
from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "qwen2.5:7b"


# ============================================================
# Pydantic models — Day 4: structured output
# ============================================================

class CodeIssue(BaseModel):
    """Single issue found during code review"""
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: Literal["bug", "security", "performance", "style", "maintainability"]
    line: Optional[int] = None
    message: str
    suggestion: str
    code_before: Optional[str] = None
    code_after: Optional[str] = None


class ReviewResult(BaseModel):
    """Complete code review result"""
    file_name: str
    language: str
    issues: list[CodeIssue] = Field(default_factory=list)
    score: int = Field(ge=0, le=100, description="Overall quality score")
    summary: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


# ============================================================
# Day 1: System Prompt design
# ============================================================

REVIEW_SYSTEM_PROMPT = """你是一个资深代码审查专家，拥有 10 年以上的编程经验。

## 审查维度
1. **Bug 风险**: 空指针、越界、逻辑错误、竞态条件
2. **安全性**: SQL 注入、XSS、敏感信息泄露、命令注入
3. **性能**: 不必要的循环、内存泄漏、N+1 查询
4. **代码风格**: 命名规范、函数长度、注释质量
5. **可维护性**: 重复代码、耦合度、错误处理

## 规则
- 你必须按严重程度排序问题（critical > high > medium > low > info）
- 每个问题必须给出具体的修改建议和代码示例
- 如果代码质量好，给出肯定，不要为了找问题而挑刺
- 得分标准：90+ 优秀, 70-89 良好, 50-69 一般, <50 需要重写

## 输出格式
严格输出 JSON（不要 markdown 包装），结构如下：
{
  "file_name": "文件名",
  "language": "编程语言",
  "issues": [...],
  "score": 0-100,
  "summary": "一句话总结",
  "strengths": ["优点1", ...],
  "improvements": ["改进建议1", ...]
}"""


# ============================================================
# Day 2: Few-Shot examples
# ============================================================

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """审查以下代码：
```python
def get_user(id):
    user = db.query("SELECT * FROM users WHERE id = " + str(id))
    return user
```""",
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "file_name": "user.py",
            "language": "python",
            "issues": [
                {
                    "severity": "critical",
                    "category": "security",
                    "line": 2,
                    "message": "SQL 注入漏洞：直接拼接用户输入到 SQL 语句",
                    "suggestion": "使用参数化查询",
                    "code_before": 'db.query("SELECT * FROM users WHERE id = " + str(id))',
                    "code_after": 'db.query("SELECT * FROM users WHERE id = ?", (id,))',
                },
                {
                    "severity": "medium",
                    "category": "style",
                    "line": 1,
                    "message": "函数缺少类型提示和文档字符串",
                    "suggestion": "添加 type hints 和 docstring",
                    "code_before": "def get_user(id):",
                    "code_after": 'def get_user(user_id: int) -> Optional[User]:\n    """Fetch user by ID from database"""',
                },
            ],
            "score": 35,
            "summary": "存在严重安全漏洞，需要立即修复",
            "strengths": ["逻辑清晰简洁"],
            "improvements": ["使用参数化查询", "添加类型提示", "添加错误处理"],
        }, ensure_ascii=False),
    },
]


# ============================================================
# Review Engine
# ============================================================

def review_code(code: str, file_name: str = "unknown") -> ReviewResult:
    """
    Review code using system prompt + few-shot + CoT + structured output.
    """
    messages = [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        *FEW_SHOT_EXAMPLES,  # Day 2: Few-Shot
        {"role": "user", "content": f"审查以下代码：\n```\n{code}\n```\n\n请先在心里分析每个维度，然后输出 JSON 结果。"},  # Day 3: CoT hint
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,  # Low temperature for consistent output
            max_tokens=2000,
        )

        raw_output = response.choices[0].message.content

        # Day 4: Robust JSON parsing
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        result = ReviewResult.model_validate_json(cleaned)
        result.file_name = file_name
        return result

    except Exception as e:
        return ReviewResult(
            file_name=file_name,
            language="unknown",
            score=0,
            summary=f"审查失败: {e}",
        )


def suggest_refactoring(code: str) -> str:
    """Generate refactoring suggestions using CoT"""
    messages = [
        {"role": "system", "content": """你是代码重构专家。分析代码并给出重构建议。

请按以下步骤分析：
1. 识别代码异味 (Code Smells)
2. 确定适用的重构手法
3. 给出重构后的完整代码
4. 解释改进了什么"""},
        {"role": "user", "content": f"```\n{code}\n```"},
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.3, max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[错误: {e}]"


# ============================================================
# Display
# ============================================================

def display_review(result: ReviewResult):
    """Pretty-print review result"""
    severity_icons = {
        "critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪",
    }

    print(f"\n{'=' * 60}")
    print(f"Code Review: {result.file_name}")
    print(f"Language: {result.language}  |  Score: {result.score}/100")
    print(f"{'=' * 60}")

    if result.issues:
        print(f"\n问题 ({len(result.issues)} 个):")
        for issue in result.issues:
            icon = severity_icons.get(issue.severity, "⚪")
            line_info = f" (line {issue.line})" if issue.line else ""
            print(f"\n  {icon} [{issue.severity.upper()}]{line_info} {issue.message}")
            print(f"     类型: {issue.category}")
            print(f"     建议: {issue.suggestion}")
            if issue.code_before and issue.code_after:
                print(f"     修改: {issue.code_before}")
                print(f"        → {issue.code_after}")

    if result.strengths:
        print(f"\n优点:")
        for s in result.strengths:
            print(f"  ✅ {s}")

    if result.improvements:
        print(f"\n改进建议:")
        for imp in result.improvements:
            print(f"  💡 {imp}")

    print(f"\n总结: {result.summary}")


# ============================================================
# CLI Entry
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="AI Code Reviewer")
    parser.add_argument("command", choices=["review", "suggest"], help="review or suggest")
    parser.add_argument("file", help="File to review")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        sys.exit(1)

    code = file_path.read_text(encoding="utf-8")

    if args.command == "review":
        result = review_code(code, file_name=file_path.name)
        display_review(result)
    elif args.command == "suggest":
        print(suggest_refactoring(code))


if __name__ == "__main__":
    # If no args, run demo
    if len(sys.argv) < 2:
        demo_code = """
import os

def process(data, flag):
    results = []
    for i in range(len(data)):
        item = data[i]
        if flag == True:
            if item != None:
                try:
                    val = int(item)
                    if val > 0:
                        results.append(val * 2)
                except:
                    pass
    password = "admin123"
    connection_string = "postgresql://user:pass@localhost/db"
    return results
"""
        print("--- 代码审查演示 ---")
        result = review_code(demo_code, "demo.py")
        display_review(result)

        print("\n\n--- 重构建议演示 ---")
        print(suggest_refactoring(demo_code))
    else:
        main()


# ============================================================
# 扩展练习
# ============================================================

# TODO 1: 添加 "批量审查" 功能
# python day67_code_reviewer.py batch src/
# 遍历目录下所有 .py 文件，生成汇总报告

# TODO 2: 添加 "diff 审查" 功能
# 接收 git diff 输出，只审查变更的代码
# python day67_code_reviewer.py diff HEAD~1

# TODO 3: 输出 Markdown 报告
# 把审查结果格式化为 Markdown 文件
# 包含统计图表（问题分布、严重程度饼图的文本表示）
