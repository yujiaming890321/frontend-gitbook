"""
Day 1: 数据结构 — list / dict / set 操作、列表推导式
AI 开发中天天用：API 返回值解析、数据处理、文档切分
"""

# ============================================================
# 1. List 操作
# JS: Array     →  Python: list
# ============================================================

# 基本操作
fruits = ["apple", "banana", "cherry"]
fruits.append("date")         # JS: push()
fruits.insert(1, "avocado")   # JS: splice(1, 0, "avocado")
removed = fruits.pop()        # JS: pop()
fruits.remove("banana")       # JS: splice(indexOf("banana"), 1)

# 切片 (Slicing) — Python 独有的强大特性，JS 没有直接等价物
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
print(numbers[2:5])    # [2, 3, 4]   — 从索引2到5（不含5）
print(numbers[:3])     # [0, 1, 2]   — 前3个
print(numbers[-3:])    # [7, 8, 9]   — 最后3个
print(numbers[::2])    # [0, 2, 4, 6, 8] — 每隔2个取一个

# AI 场景：文档切分（简化版）
document = "这是一段很长的文档内容，需要切分成小块来做 RAG 检索。" * 10
chunk_size = 50
# Split document into chunks of chunk_size characters
chunks = [document[i:i+chunk_size] for i in range(0, len(document), chunk_size)]
print(f"文档长度: {len(document)}, 切分成 {len(chunks)} 块")

#### 字符串切分的其他写法

text = "abcdefghijklmnop"
size = 5

# 1. 列表推导式（最常用，推荐）
chunks = [text[i:i+size] for i in range(0, len(text), size)]
print(chunks)  # ['abcde', 'fghij', 'klmno', 'p']

# 2. textwrap.wrap — 标准库，专门做固定宽度切分
# ⚠️ 注意：wrap 会在空格处断行，不一定严格按 size 切，适合英文文本
# import textwrap
# chunks = textwrap.wrap(text, width=size)

# 3. re.findall — 正则，简洁但可读性差
# import re
# chunks = re.findall(f'.{{1,{size}}}', text)

# 4. itertools + 生成器 — 适合处理超大数据（惰性求值，不一次性加载到内存）
# from itertools import islice
# def chunk_iter(s, size):
#     it = iter(s)
#     while batch := ''.join(islice(it, size)):
#         yield batch
# chunks = list(chunk_iter(text, size))

# **实际 AI 开发中**：文档切分一般用 LangChain 的 `RecursiveCharacterTextSplitter`，它会在语义边界（段落、句子）处切分，而不是硬切字符数。日常写代码用方法 1（列表推导式）就够了。


# ============================================================
# 2. Dict 操作
# JS: Object / Map  →  Python: dict
# ============================================================

# 基本操作
user = {"name": "Alice", "age": 30, "role": "engineer"}
print(user["name"])           # JS: user.name 或 user["name"]
print(user.get("email", "N/A"))  # 安全取值，不存在返回默认值（JS 没有直接等价物）

# AI 场景：解析 LLM API 返回值（这个结构你会天天见到）
api_response = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "React hooks 是一种让函数组件拥有状态的机制"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 25, "total_tokens": 35}
}

# Extract the reply content from API response
content = api_response["choices"][0]["message"]["content"]
tokens_used = api_response["usage"]["total_tokens"]
print(f"回复: {content}")
print(f"消耗 tokens: {tokens_used}")

# 字典推导式
# JS: Object.fromEntries(arr.map(x => [x, x.length]))
# dict = { obj: len(obj) for obj in ["hello", "world", "python"]}
word_lengths = {word: len(word) for word in ["hello", "world", "python"]}
print(word_lengths)  # {'hello': 5, 'world': 5, 'python': 6}

# 合并字典
defaults = {"temperature": 0.7, "max_tokens": 1000, "model": "gpt-4"}
overrides = {"temperature": 0.3, "model": "qwen2.5:7b"}
config = {**defaults, **overrides}  # JS: {...defaults, ...overrides}
print(config)


# ============================================================
# 3. Set 操作
# JS: Set  →  Python: set
# ============================================================

tags_a = {"python", "ai", "langchain"}
tags_b = {"python", "react", "typescript"}

print(tags_a & tags_b)   # 交集: {'python'}
print(tags_a | tags_b)   # 并集: {'python', 'ai', 'langchain', 'react', 'typescript'}
print(tags_a - tags_b)   # 差集: {'ai', 'langchain'}
print(tags_b - tags_a)   # 差集: {'react', 'typescript'}

# AI 场景：去重（比如去除重复的检索结果）
search_results = ["doc1.md", "doc2.md", "doc1.md", "doc3.md", "doc2.md"]
unique_results = list(set(search_results))
print(f"去重后: {unique_results}")


# ============================================================
# 4. 列表推导式 (List Comprehension)
# JS: array.map().filter()  →  Python: [expr for x in iter if cond]
# ============================================================

# 基本推导
# JS: [1,2,3,4,5].map(x => x * 2)
doubled = [x * 2 for x in [1, 2, 3, 4, 5]]

# 带条件的推导
# JS: [1,2,3,4,5].filter(x => x > 2).map(x => x * 2)
filtered_doubled = [x * 2 for x in [1, 2, 3, 4, 5] if x > 2]

# AI 场景：过滤有效的聊天消息
messages = [
    {"role": "system", "content": "你是助手"},
    {"role": "user", "content": ""},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮你？"},
]
# Filter out messages with empty content
valid_messages = [m for m in messages if m["content"].strip()]
print(f"有效消息: {len(valid_messages)} 条")

# 嵌套推导（展平列表）
# JS: [[1,2],[3,4],[5,6]].flat()
nested = [[1, 2], [3, 4], [5, 6]]
flat = [item for sublist in nested for item in sublist]
print(flat)  # [1, 2, 3, 4, 5, 6]


# ============================================================
# 5. 解构 (Unpacking)
# JS: const [a, b] = arr / const {name} = obj
# ============================================================

# 列表解构
first, *rest = [1, 2, 3, 4, 5]
print(first)  # 1
print(rest)   # [2, 3, 4, 5]  — JS 的 rest 参数 ...rest

# 元组解构（函数返回多个值）
def get_model_info():
    """Return model name and its parameter count"""
    return "qwen2.5:7b", 7_000_000_000

name, params = get_model_info()
print(f"模型: {name}, 参数量: {params:,}")

# 字典解构（Python 没有 JS 那种直接解构，但可以用 .values()）
for key, value in user.items():
    print(f"{key}: {value}")


# ============================================================
# 练习题
# ============================================================

print("\n" + "=" * 50)
print("练习题")
print("=" * 50)

# TODO 1: 给定一个 API 响应，提取所有 choice 的 content
multi_choice_response = {
    "choices": [
        {"message": {"content": "答案A"}},
        {"message": {"content": "答案B"}},
        {"message": {"content": "答案C"}},
    ]
}
# 用列表推导式提取所有 content → ["答案A", "答案B", "答案C"]
contents = [choice["message"]["content"] for choice in multi_choice_response["choices"]]
print(contents)

# TODO 2: 给定一段文本，切分成每块 100 字符，块之间重叠 20 字符
text = "Python 是 AI 开发的主流语言。" * 20
overlap = 20
overlapping_chunks = [text[i:i+100] for i in range(0, len(text), 100 - overlap)]
print(f"重叠切分: {len(overlapping_chunks)} 块")

# TODO 3: 合并两个配置字典，后者覆盖前者，并过滤掉值为 None 的项
config_a = {"model": "gpt-4", "temperature": 0.7, "max_tokens": None}
config_b = {"temperature": 0.3, "top_p": 0.9, "max_tokens": 500}
merged = {key: value for key, value in {**config_a, **config_b}.items() if value is not None}
print(merged)
