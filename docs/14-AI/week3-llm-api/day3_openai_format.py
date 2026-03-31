"""
Day 3: OpenAI 兼容格式详解
几乎所有 LLM API 都遵循 OpenAI 格式，学会这个格式就能调用任何 LLM
"""

from openai import OpenAI
from typing import Literal

# ============================================================
# 1. Messages 数组 — 对话的核心数据结构
# ============================================================

"""
messages 是一个数组，包含三种角色：

┌─────────────┬──────────────────────────────────────────┐
│ role        │ 用途                                      │
├─────────────┼──────────────────────────────────────────┤
│ system      │ 设定 AI 的行为和角色（只在开头出现一次）    │
│ user        │ 用户的输入                                │
│ assistant   │ AI 的回复（用于多轮对话的历史记录）         │
└─────────────┴──────────────────────────────────────────┘
"""

# A complete conversation history
messages = [
    # System message — sets the AI's behavior (like a prompt template)
    {"role": "system", "content": "你是一个 Python 专家，回答简洁精准。"},

    # First round: user asks, assistant responds
    {"role": "user", "content": "Python 的 list 和 tuple 有什么区别？"},
    {"role": "assistant", "content": "list 可变，tuple 不可变。list 用 []，tuple 用 ()。"},

    # Second round: follow-up question
    {"role": "user", "content": "什么时候该用 tuple？"},
]

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

try:
    response = client.chat.completions.create(
        model="qwen2.5:7b",
        messages=messages,
    )
    print(f"回复: {response.choices[0].message.content}\n")
except Exception as e:
    print(f"[Ollama 未启动: {e}]\n")


# ============================================================
# 2. 关键参数详解
# ============================================================

"""
参数               类型      默认    说明
──────────        ──────    ────   ────
model             string    -      模型名称（必填）
messages          array     -      对话历史（必填）
temperature       float     1.0    输出随机性 (0=确定性, 2=最随机)
max_tokens        int       -      最大输出 token 数
top_p             float     1.0    核采样参数 (和 temperature 二选一调)
frequency_penalty float     0.0    重复惩罚 (-2.0 到 2.0)
presence_penalty  float     0.0    新话题鼓励 (-2.0 到 2.0)
stop              list      -      停止序列（遇到这些字符串就停止生成）
stream            bool      false  是否流式输出
n                 int       1      生成几个候选回复
seed              int       -      随机种子（相同 seed + prompt → 相同输出）
"""


# ============================================================
# 3. 参数调优指南
# ============================================================

def demonstrate_params():
    """Show how different parameters affect output"""

    base_messages = [
        {"role": "system", "content": "你是一个写作助手"},
        {"role": "user", "content": "写一句关于春天的诗"},
    ]

    configs = [
        {"name": "精确回答 (代码/事实类)", "temperature": 0, "top_p": 1.0},
        {"name": "平衡模式 (日常对话)", "temperature": 0.7, "top_p": 0.9},
        {"name": "创意模式 (写作/头脑风暴)", "temperature": 1.2, "top_p": 0.95},
    ]

    print("--- 参数调优示例 ---")
    for config in configs:
        try:
            response = client.chat.completions.create(
                model="qwen2.5:7b",
                messages=base_messages,
                temperature=config["temperature"],
                top_p=config["top_p"],
                max_tokens=50,
            )
            print(f"\n{config['name']}:")
            print(f"  temperature={config['temperature']}, top_p={config['top_p']}")
            print(f"  → {response.choices[0].message.content}")
        except Exception as e:
            print(f"\n{config['name']}: [错误: {e}]")

demonstrate_params()


# ============================================================
# 4. Stop 序列 — 控制输出终止
# ============================================================

def stop_sequence_demo():
    """Show how stop sequences control output"""
    try:
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[
                {"role": "user", "content": "列出 3 个编程语言:\n1."},
            ],
            stop=["\n4."],  # Stop before generating the 4th item
            temperature=0,
        )
        print(f"\n--- Stop 序列 ---")
        print(f"输出: 1.{response.choices[0].message.content}")
        print(f"finish_reason: {response.choices[0].finish_reason}")
    except Exception as e:
        print(f"[错误: {e}]")

stop_sequence_demo()


# ============================================================
# 5. 多候选回复 (n > 1)
# ============================================================

def multi_response_demo():
    """Generate multiple candidate responses for the same prompt"""
    try:
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[{"role": "user", "content": "给我的 Python 项目起一个名字"}],
            n=3,          # Generate 3 different responses
            temperature=1.0,
            max_tokens=30,
        )
        print(f"\n--- 多候选回复 (n=3) ---")
        for i, choice in enumerate(response.choices):
            print(f"  候选 {i+1}: {choice.message.content}")
    except Exception as e:
        # Some providers don't support n > 1
        print(f"\n[n > 1 不支持: {e}]")

multi_response_demo()


# ============================================================
# 6. 场景推荐参数
# ============================================================

"""
场景                    temperature   max_tokens   建议
──────────             ───────────   ──────────   ────
代码生成/审查            0 - 0.3       500-2000     低随机性，确保正确性
事实问答 (RAG)           0 - 0.3       200-500      精确回答，减少幻觉
日常聊天                 0.7           500-1000     自然流畅
创意写作                 0.9 - 1.2     1000-2000    更多创意和变化
头脑风暴                 1.0 - 1.5     500          鼓励发散思维
数据提取/格式化           0             200-500      严格按格式输出
翻译                    0.3           根据原文       准确翻译

经验法则：
- 需要精确 → 低 temperature
- 需要创意 → 高 temperature
- temperature 和 top_p 不要同时调（通常只调 temperature）
"""


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 写一个 find_best_temperature 函数
# 给定一个 prompt 和期望的输出格式
# 尝试 temperature 从 0 到 1（步长 0.2）
# 评估每个温度下输出是否符合预期格式（如 JSON）
# 返回最佳 temperature

# def find_best_temperature(prompt: str, expected_format: str) -> float:
#     ???

# TODO 2: 写一个 chat_with_retry 函数
# 如果 LLM 的回答不满足条件（如不包含某个关键词）
# 自动重试，最多 3 次，每次提高 temperature
# 这在实际 AI 开发中很常用

# TODO 3: 构造一组 messages，实现以下多轮对话场景：
# 1. 用户问一个编程问题
# 2. AI 回答
# 3. 用户说"请给出代码示例"
# 4. AI 给出代码
# 5. 用户说"请解释第 3 行"
# 验证 AI 能正确理解上下文
