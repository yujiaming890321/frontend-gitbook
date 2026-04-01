# Python for AI Development

> 学 Python 的知识记录，重点关注 AI 开发中常用的部分。

```python
# strip() = trim()
"###hello###".strip("#")  # "hello"
valid_messages = [m for m in messages if m["content"].strip()] # if content is truthy
```

## Unpacking

### 列表解构

```python
first, *rest = [1, 2, 3, 4, 5]
print(first)  # 1
print(rest)   # [2, 3, 4, 5]  — JS 的 rest 参数 ...rest
```

### 元组解构（函数返回多个值）

```python
def get_model_info():
    """Return model name and its parameter count"""
    return "qwen2.5:7b", 7_000_000_000

name, params = get_model_info()
print(f"模型: {name}, 参数量: {params:,}")
```

### 字典解构

```python
for key, value in user.items():
    print(f"{key}: {value}")
```

## List (JS: Array)

### 基本操作

```python
fruits = ["apple", "banana", "cherry"]
fruits.append("date")         # JS: push()
fruits.insert(1, "avocado")   # JS: splice(1, 0, "avocado")
removed = fruits.pop()        # JS: pop()
fruits.remove("banana")       # JS: splice(indexOf("banana"), 1)
```

### 切片 (Slicing) — Python 独有的强大特性，JS 没有直接等价物

```python
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
print(numbers[2:5])    # [2, 3, 4]   — 从索引2到5（不含5）
print(numbers[:3])     # [0, 1, 2]   — 前3个
print(numbers[-3:])    # [7, 8, 9]   — 最后3个
print(numbers[::2])    # [0, 2, 4, 6, 8] — 每隔2个取一个
```

### 列表推导式 (List Comprehension)

```python
# 完整语法
[表达式 for 变量 in 可迭代对象 if 条件]

# 对应 JS
可迭代对象.filter(变量 => 条件).map(变量 => 表达式)
```

```python
# 1. 最简单：只有 map
[x * 2 for x in [1, 2, 3]]           # [2, 4, 6]
# JS: [1,2,3].map(x => x * 2)

# 2. 带条件：filter + map
[x * 2 for x in [1, 2, 3, 4, 5] if x > 2]   # [6, 8, 10]
# JS: [1,2,3,4,5].filter(x => x > 2).map(x => x * 2)

# 3. 表达式可以是任何东西
[len(word) for word in ["hello", "hi", "hey"]]        # [5, 2, 3]
[word.upper() for word in ["hello", "world"]]          # ['HELLO', 'WORLD']
[{"role": "user", "content": msg} for msg in ["你好", "帮我写代码"]]

# 4. 嵌套循环（展平二维数组）
# 阅读顺序：从左到右，和写 for 循环的顺序一样
[item for sublist in [[1,2],[3,4]] for item in sublist]   # [1, 2, 3, 4]
# 等价于：
# for sublist in [[1,2],[3,4]]:
#     for item in sublist:
#         result.append(item)
```

> **核心理解**：把它看作一个倒过来写的 for 循环 —— 先写你要什么（表达式），再写从哪来（for），最后写筛选条件（if）。

### AI 场景：文档切分（简化版）

```python
document = "这是一段很长的文档内容，需要切分成小块来做 RAG 检索。" * 10
chunk_size = 50
# Split document into chunks of chunk_size characters
chunks = [document[i:i+chunk_size] for i in range(0, len(document), chunk_size)]
print(f"文档长度: {len(document)}, 切分成 {len(chunks)} 块")
```

#### 字符串切分的其他写法

```python
text = "abcdefghijklmnop"
size = 5

# 1. 列表推导式（最常用，推荐）
# [表达式 for 变量 in 可迭代对象 if 条件]
chunks = [text[i:i+chunk_size] for i in range(0, len(text), step)]

# 2. textwrap.wrap — 标准库，专门做固定宽度切分
# ⚠️ 注意：wrap 会在空格处断行，不一定严格按 size 切，适合英文文本
import textwrap
chunks = textwrap.wrap(text, width=size)

# 3. re.findall — 正则，简洁但可读性差
import re
chunks = re.findall(f'.{{1,{size}}}', text)

# 4. itertools + 生成器 — 适合处理超大数据（惰性求值，不一次性加载到内存）
from itertools import islice
def chunk_iter(s, size):
    it = iter(s)
    while batch := ''.join(islice(it, size)):
        yield batch
chunks = list(chunk_iter(text, size))
```

> **实际 AI 开发中**：文档切分一般用 LangChain 的 `RecursiveCharacterTextSplitter`，它会在语义边界（段落、句子）处切分，而不是硬切字符数。日常写代码用方法 1（列表推导式）就够了。

## Dict (JS: Object / Map)

### 基本操作

```python
user = {"name": "Alice", "age": 30, "role": "engineer"}
print(user["name"])           # JS: user.name 或 user["name"]
print(user.get("email", "N/A"))  # 安全取值，不存在返回默认值（JS 没有直接等价物）
```

### AI 场景：解析 LLM API 返回值（这个结构你会天天见到）

```python
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
```

### 字典推导式 (Dict Comprehension)

```python
# 完整语法
{key表达式: value表达式 for 变量 in 可迭代对象 if 条件}

# 1. 基本用法
{word: len(word) for word in ["hello", "world"]}
# {'hello': 5, 'world': 5}
# JS: Object.fromEntries(["hello","world"].map(w => [w, w.length]))

# 2. 带条件过滤
scores = {"Alice": 85, "Bob": 60, "Charlie": 92}
{key: value for key, value in scores.items() if value > 70}
# {'Alice': 85, 'Charlie': 92}

# 3. 值转换（类似 map）
{name: score / 100 for name, score in scores.items()}
# {'Alice': 0.85, 'Bob': 0.6, 'Charlie': 0.92}

# 4. 反转 key-value
original = {"a": 1, "b": 2, "c": 3}
{v: k for k, v in original.items()}
# {1: 'a', 2: 'b', 3: 'c'}

# 5. 从两个列表构建字典
keys = ["model", "temperature", "max_tokens"]
values = ["qwen2.5:7b", 0.7, 1000]
{k: v for k, v in zip(keys, values)}
# {'model': 'qwen2.5:7b', 'temperature': 0.7, 'max_tokens': 1000}
# 注意：这个场景直接用 dict(zip(keys, values)) 更简洁
```

> **核心理解**：和列表推导式完全一样的思路，只是每次产出一个 `key: value` 对而不是单个值。

### 合并字典

```python
defaults = {"temperature": 0.7, "max_tokens": 1000, "model": "gpt-4"}
overrides = {"temperature": 0.3, "model": "qwen2.5:7b"}
config = {**defaults,**overrides}  # JS: {...defaults, ...overrides}
print(config)
```

## Function (JS: Fucntion)

### basic function

```python
from __future__ import annotations
def basic_function(str: str, *array) -> list[dict]:
```

### lambda （JS 匿名函数）

```python
# 这两个完全等价
lambda x: x * 2          # Python lambda
# (x) => x * 2           // JS 箭头函数
```

### Decorator

```python
def decorator_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # example(1, 2, name="Alice", age=30)
        # args   = (1, 2)
        # kwargs = {"name": "Alice", "age": 30}
        result = func(*args, **kwargs)
        print(f"Calling {func.__name__}({args})")
        return result
    return wrapper

@decorator_function
def basic_function(a: int, b: int) -> int: return a + b
```

### zip （JS: generator)

```python
titles = ["RAG 入门", "Agent 实战", "Prompt 技巧", "LLM 基础", "向量数据库"]
relevance = [0.85, 0.92, 0.78, 0.95, 0.65]
documents = zip(titles, relevance) # [("RAG 入门",0.85), ("Agent 实战", 0.92), ("Prompt 技巧",0.78),("LLM 基础", 0.95), ("向量数据库", 0.65)]
#   for title, score in documents:
#       print(title, score)       # ✅ 第一次遍历正常
#   for title, score in documents:
#       print(title, score)       # ❌ 第二次什么都不会输出，已经耗尽了
#   如果需要多次使用，先转成 list：documents = list(zip(titles, relevance))。
```

### sorted

```python
sorted(可迭代对象, key=排序依据, reverse=是否倒序)
```
