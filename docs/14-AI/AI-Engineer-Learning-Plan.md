# 前端程序员转 AI 应用工程师：12 周学习计划

## 前提条件

- **当前背景**：前端程序员（React/TypeScript），写过一点 Python
- **已有知识**：读过 Prompt Engineering、RAG、AI Workflow、Agent、AI Eval 的概念文章
- **时间投入**：每天 30 分钟（工作日下班后），周末可适当多投入
- **总预算**：约 45 小时
- **目标**：3 个月后具备 AI 应用工程师岗位的基本面试能力

## 免费工具清单

没有 API key 也能学 AI，以下是完全免费的方案：

| 工具 | 用途 | 免费额度 |
|------|------|---------|
| **Google AI Studio** | 调用 Gemini API，免费额度最大方 | 免费调用，有 RPM 限制 |
| **Ollama** | 本地运行开源模型（Llama、Qwen 等） | 完全免费，需 8GB+ 内存 |
| **Groq** | 云端调用开源模型，速度极快 | 免费 tier，有速率限制 |
| **HuggingFace** | 模型托管 + Inference API | 免费 tier |
| **Chroma** | 本地向量数据库 | 完全免费 |
| **LangChain / LangGraph** | Agent 框架 | 开源免费 |
| **Claude Code** | AI 编程助手（你已经在用） | 按计划付费 |

**推荐组合**：Google AI Studio（云端 LLM）+ Ollama（本地 LLM）+ Chroma（向量数据库）

### Ollama 安装

```bash
# macOS
brew install ollama

# 启动服务
ollama serve

# 下载模型（推荐 qwen2.5，中文能力强）
ollama pull qwen2.5:7b

# 测试
curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"你好"}'
```

### Google AI Studio 获取免费 API Key

```
1. 访问 https://aistudio.google.com/
2. 登录 Google 账号
3. 点击 "Get API Key" → "Create API Key"
4. 保存 key，后续代码中使用
```

---

## 总览：12 周路线图

```
第 1-2 周   Python 补强（基础语法 + AI 常用库）
第 3-4 周   LLM API 实操（调通 API + Prompt Engineering 实战）
第 5-7 周   RAG 项目实战（构建知识库问答系统）
第 8-10 周  Agent 项目实战（构建自主决策 Agent）
第 11 周    MCP Server 开发（用 TypeScript，发挥你的优势）
第 12 周    项目整理 + 面试准备
```

```
知识递进关系：

Python 基础 → LLM API 调用 → Prompt 实战 → RAG 系统 → Agent 系统 → MCP 开发
                                              ↑           ↑
                                         你已读过概念    你已读过概念
                                         现在做实操      现在做实操
```

---

## 第 0 步：搭建 Python 开发环境

> 在开始学习前，先把环境搭好。整个过程 10-15 分钟。

### 安装 pyenv（Python 版本管理）

`pyenv` 之于 Python，就像 `nvm` 之于 Node.js——管理多个 Python 版本，随时切换。

```bash
# 1. 安装 pyenv
brew install pyenv

# 2. 配置 shell（zsh）
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# 3. 安装 Python（推荐 3.12，AI 库兼容性最好）
pyenv install 3.12
pyenv global 3.12

# 4. 验证
python --version   # Python 3.12.x
pip --version      # pip 24.x
```

### 虚拟环境（项目依赖隔离）

Python 的虚拟环境 = Node.js 的 `node_modules`，每个项目有独立的依赖，互不干扰。

```bash
# 创建项目目录
mkdir my-ai-project && cd my-ai-project

# 创建虚拟环境（.venv 目录，类似 node_modules）
python -m venv .venv

# 激活虚拟环境（激活后终端前面会出现 (.venv) 标识）
source .venv/bin/activate

# 安装依赖
pip install requests

# 导出依赖列表（类似 package.json 的 dependencies）
pip freeze > requirements.txt

# 从 requirements.txt 安装（类似 npm install）
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

### 与 JS/TS 生态的完整对应

```
Node.js 生态             Python 生态               用途
─────────────            ──────────               ────
nvm                      pyenv                    版本管理
node_modules/            .venv/                   项目依赖隔离
npm init                 python -m venv .venv     初始化项目
npm install              pip install              安装包
npm install -r           pip install -r           从文件安装
package.json             requirements.txt         依赖声明
                         pyproject.toml           现代依赖声明（类似 package.json）
npx                      python -m / pipx         执行命令行工具
.nvmrc                   .python-version          指定项目 Python 版本
```

### 推荐的 VS Code 配置

```bash
# 安装 Python 扩展
code --install-extension ms-python.python

# VS Code 会自动识别 .venv，按 Cmd+Shift+P 搜索 "Python: Select Interpreter"
# 选择 .venv 中的 Python 即可
```

### .gitignore 补充

```bash
# 在项目的 .gitignore 中添加
echo '.venv/' >> .gitignore
echo '__pycache__/' >> .gitignore
echo '*.pyc' >> .gitignore
```

> **提示**：每次开始写 Python 代码前，记得先 `source .venv/bin/activate` 激活虚拟环境。如果终端前面没有 `(.venv)` 标识，说明没激活，安装的包会装到全局。

---

## 第 1-2 周：Python 补强

> 目标：能用 Python 写 AI 应用代码，不需要精通，够用就行

你写过一点 Python，所以重点补 AI 开发中高频使用的部分，跳过你已经会的基础语法。

### 第 1 周：Python 核心语法快速过

**每天 30 分钟，共 3.5 小时**

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | 数据结构：list / dict / set 操作、列表推导式 | 30min |
| Day 2 | 函数：`*args` / `**kwargs`、lambda、装饰器基础 | 30min |
| Day 3 | 类与面向对象：`class`、`__init__`、继承、dataclass | 30min |
| Day 4 | 异步编程：`async` / `await`、`asyncio`（AI API 调用大量使用） | 30min |
| Day 5 | 类型提示：`typing` 模块（`List`、`Dict`、`Optional`、`TypedDict`） | 30min |
| Day 6-7 | 练习：用 Python 重写一个你熟悉的 JS 小工具 | 60min |

**重点掌握**（AI 开发中天天用）：

```python
# 1. dict 操作（API 返回值都是 dict）
response = {"choices": [{"message": {"content": "你好"}}]}
content = response["choices"][0]["message"]["content"]

# 2. 列表推导式（数据处理常用）
chunks = [doc[i:i+500] for i in range(0, len(doc), 500)]

# 3. async/await（API 调用）
async def call_llm(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 4. TypedDict（结构化数据）
from typing import TypedDict

class Message(TypedDict):
    role: str
    content: str
```

**学习资源**：
- [Python 官方教程](https://docs.python.org/zh-cn/3/tutorial/) — 挑着看，跳过你会的
- 遇到不懂的语法直接问 Claude Code

### 第 2 周：AI 开发常用库

**每天 30 分钟，共 3.5 小时**

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | `requests` / `httpx`：HTTP 请求（对比 fetch/axios） | 30min |
| Day 2 | `pydantic`：数据校验和序列化（AI 项目标配，对比 zod） | 30min |
| Day 3 | `python-dotenv`：环境变量管理 + JSON 处理 | 30min |
| Day 4 | `FastAPI` 基础：写一个简单 API 服务（对比 express） | 30min |
| Day 5-7 | 练习：用 FastAPI 写一个简单的 REST API | 90min |

> 环境管理（venv / pip）和生态对应关系已在"第 0 步"中介绍，这里不再重复。

**第 2 周结束时的检验**：能运行以下代码并理解每一行

```python
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:7b", "prompt": request.message, "stream": False}
        )
    return {"reply": response.json()["response"]}
```

---

## 第 3-4 周：LLM API 实操

> 目标：能熟练调用 LLM API，掌握 Prompt Engineering 实战技巧

### 第 3 周：调通 LLM API

**每天 30 分钟，共 3.5 小时**

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | 用 Ollama 本地调用 LLM（REST API 方式） | 30min |
| Day 2 | 用 Google AI Studio 获取 API key，调用 Gemini API | 30min |
| Day 3 | 学习 OpenAI 兼容格式（messages 数组、role、temperature） | 30min |
| Day 4 | 流式响应（streaming）：理解 SSE，实现打字机效果 | 30min |
| Day 5 | 多轮对话：管理 messages 历史 | 30min |
| Day 6-7 | 练习：用 Python 写一个命令行聊天机器人 | 60min |

**核心概念**：

```python
# OpenAI 兼容格式（几乎所有 LLM API 都遵循这个格式）
# Ollama、Gemini、Groq 都支持这个格式

from openai import OpenAI

# 连接本地 Ollama（免费）
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Ollama 不需要真实 key
)

# 或者连接 Google Gemini（免费）
# pip install google-genai
# client = OpenAI(
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
#     api_key="your-gemini-api-key"
# )

response = client.chat.completions.create(
    model="qwen2.5:7b",  # Gemini 用 "gemini-2.0-flash"
    messages=[
        {"role": "system", "content": "你是一个有用的助手"},
        {"role": "user", "content": "解释什么是 React hooks"}
    ],
    temperature=0.7,  # 0=确定性输出，1=更随机
)

print(response.choices[0].message.content)
```

**关键参数理解**：

```
messages     → 对话历史（数组），包含 system/user/assistant 消息
temperature  → 控制输出随机性，0 最确定，1 最随机
max_tokens   → 限制输出长度
stream       → 是否流式输出（true = 逐字返回）
```

### 第 4 周：Prompt Engineering 实战

**每天 30 分钟，共 3.5 小时**

你已经读过 Prompt Engineering 的文章，这周重点是**动手练**。

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | System Prompt 设计：写 3 个不同角色的 system prompt | 30min |
| Day 2 | Few-Shot：用示例引导 LLM 输出固定格式 | 30min |
| Day 3 | CoT（Chain-of-Thought）：让 LLM 分步推理 | 30min |
| Day 4 | 结构化输出：让 LLM 输出 JSON（用 pydantic 校验） | 30min |
| Day 5 | Function Calling 实操：定义函数 schema，让 LLM 调用 | 30min |
| Day 6-7 | 综合练习：做一个"代码审查助手" | 60min |

**实战练习：代码审查助手**

```python
# code_reviewer.py — 你的第一个实用 AI 工具

from openai import OpenAI
import json
import sys

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

SYSTEM_PROMPT = """你是一个资深代码审查员。请审查用户提供的代码，从以下角度给出反馈：
1. Bug 风险
2. 性能问题
3. 可读性
4. 安全隐患

输出格式为 JSON：
{
  "issues": [
    {"severity": "high|medium|low", "line": 行号, "message": "问题描述", "suggestion": "修改建议"}
  ],
  "summary": "总体评价"
}"""

def review_code(code: str) -> dict:
    response = client.chat.completions.create(
        model="qwen2.5:7b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请审查以下代码：\n```\n{code}\n```"}
        ],
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    code = open(sys.argv[1]).read()
    result = review_code(code)
    for issue in result["issues"]:
        print(f"[{issue['severity'].upper()}] Line {issue['line']}: {issue['message']}")
        print(f"  → {issue['suggestion']}\n")
```

**第 4 周结束时的检验**：
- 能独立写出上面的代码审查助手
- 理解 temperature、system prompt、few-shot 对输出的影响
- 能让 LLM 稳定输出 JSON 格式

---

## 第 5-7 周：RAG 项目实战

> 目标：构建一个完整的知识库问答系统
> 项目：把你的 gitbook 文档变成可问答的 AI 助手

这是你的**第一个完整 AI 项目**，也是面试中最常被问到的技术。

### 第 5 周：理解 RAG 核心组件

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | 安装 LangChain + Chroma，跑通官方 quickstart | 30min |
| Day 2 | 文档加载器（Document Loader）：加载 Markdown 文件 | 30min |
| Day 3 | 文档切分（Text Splitter）：理解 chunk_size 和 overlap | 30min |
| Day 4 | Embedding：用 Ollama 的 embedding 模型做向量化 | 30min |
| Day 5 | 向量检索：用 Chroma 存储和检索向量 | 30min |
| Day 6-7 | 把以上串起来：加载一个 md 文件 → 切分 → 向量化 → 检索 | 60min |

**环境搭建**：

```bash
pip install langchain langchain-community langchain-chroma
pip install chromadb
# Ollama 也提供 embedding 模型
ollama pull nomic-embed-text
```

**核心代码骨架**：

```python
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

# 1. 加载你的 gitbook 文档
loader = DirectoryLoader(
    "docs/14-AI/AI-Application-Engineering",
    glob="**/*.md",
    loader_cls=TextLoader
)
documents = loader.load()

# 2. 切分成小块
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # 每块 500 字符
    chunk_overlap=50,    # 块之间重叠 50 字符，防止信息被切断
)
chunks = splitter.split_documents(documents)

# 3. 向量化 & 存入 Chroma
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")

# 4. 检索
results = vectorstore.similarity_search("什么是 RAG？", k=3)
for doc in results:
    print(doc.page_content[:200])
    print("---")
```

### 第 6 周：构建完整 RAG 问答链

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | RetrievalQA Chain：把检索 + LLM 串成问答链 | 30min |
| Day 2 | 优化 prompt 模板：让回答引用来源文档 | 30min |
| Day 3 | 调优 chunk_size 和 k 值，观察效果变化 | 30min |
| Day 4 | 处理检索不到的情况：让 AI 说"我不知道"而不是编造 | 30min |
| Day 5 | 添加对话历史：支持追问（Conversational RAG） | 30min |
| Day 6-7 | 测试和调优：用你的 gitbook 文档测试各种问题 | 60min |

**完整 RAG 问答代码**：

```python
from langchain_community.llms import Ollama
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# 加载已有的向量数据库
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

# 自定义 prompt 模板
template = """基于以下参考资料回答问题。如果资料中没有相关信息，请说"根据现有资料无法回答"。

参考资料：
{context}

问题：{question}

回答："""

prompt = PromptTemplate(template=template, input_variables=["context", "question"])

# 构建 RAG 链
qa_chain = RetrievalQA.from_chain_type(
    llm=Ollama(model="qwen2.5:7b"),
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True,
)

# 问答
result = qa_chain.invoke({"query": "Agent 的核心组件有哪些？"})
print(result["result"])
print("\n来源文档：")
for doc in result["source_documents"]:
    print(f"  - {doc.metadata['source']}")
```

### 第 7 周：给 RAG 加上 Web 界面

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | 用 FastAPI 把 RAG 包装成 API 接口 | 30min |
| Day 2 | 实现流式输出接口（SSE） | 30min |
| Day 3 | 用 React 写一个简单的 Chat UI | 30min |
| Day 4 | 对接流式 API，实现打字机效果 | 30min |
| Day 5 | 添加"来源引用"展示（显示参考了哪些文档） | 30min |
| Day 6-7 | 美化 UI + 整理代码，形成完整项目 | 60min |

**这周发挥你的前端优势**——后端 RAG 是 Python，前端 Chat UI 是 React/TypeScript，这就是你的复合竞争力。

**第 7 周结束时的成果**：
- 一个完整的知识库问答应用
- 后端：Python + LangChain + Chroma + FastAPI
- 前端：React + TypeScript + 流式输出
- 能问你 gitbook 里的所有 AI 知识
- **这就是你简历上的第一个 AI 项目**

---

## 第 8-10 周：Agent 项目实战

> 目标：构建一个能自主决策、使用工具的 Agent
> 项目：一个能搜索信息 + 分析数据 + 生成报告的研究助手

### 第 8 周：LangGraph 基础

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | 安装 LangGraph，理解 Graph / Node / Edge 概念 | 30min |
| Day 2 | 写一个最简单的 Graph：输入 → LLM 处理 → 输出 | 30min |
| Day 3 | 添加条件路由：根据 LLM 判断走不同分支 | 30min |
| Day 4 | 添加工具节点：让 Agent 调用自定义工具 | 30min |
| Day 5 | 状态管理：理解 State 如何在节点间传递 | 30min |
| Day 6-7 | 练习：写一个简单的"计算器 Agent"（能判断是否需要计算） | 60min |

**LangGraph 最小示例**：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from langchain_community.llms import Ollama
import operator

# 1. 定义状态
class AgentState(TypedDict):
    question: str
    thinking: str
    answer: str

# 2. 定义节点
llm = Ollama(model="qwen2.5:7b")

def think_node(state: AgentState) -> dict:
    thinking = llm.invoke(f"分析这个问题，列出解决步骤：{state['question']}")
    return {"thinking": thinking}

def answer_node(state: AgentState) -> dict:
    answer = llm.invoke(
        f"问题：{state['question']}\n分析：{state['thinking']}\n请给出最终回答："
    )
    return {"answer": answer}

# 3. 构建图
graph = StateGraph(AgentState)
graph.add_node("think", think_node)
graph.add_node("answer", answer_node)
graph.set_entry_point("think")
graph.add_edge("think", "answer")
graph.add_edge("answer", END)

# 4. 运行
app = graph.compile()
result = app.invoke({"question": "React 和 Vue 的核心区别是什么？"})
print(result["answer"])
```

### 第 9 周：添加工具和循环

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | 定义工具函数：文件读取、文本搜索 | 30min |
| Day 2 | Tool Calling：让 LLM 决定调用哪个工具 | 30min |
| Day 3 | 实现 ReAct 循环：思考 → 调用工具 → 观察 → 再思考 | 30min |
| Day 4 | 添加最大迭代次数限制，防止无限循环 | 30min |
| Day 5 | 把 RAG 作为 Agent 的一个工具集成进来 | 30min |
| Day 6-7 | 综合练习：Agent 能搜索你的文档 + 生成总结 | 60min |

### 第 10 周：完善 Agent 项目

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | 添加多个工具：文件读写、网页摘要、代码执行 | 30min |
| Day 2 | 错误处理：工具调用失败时的重试和降级 | 30min |
| Day 3 | 对话记忆：Agent 能记住之前的对话 | 30min |
| Day 4 | 用 FastAPI 包装成 API | 30min |
| Day 5 | 用 React 写 Agent 交互界面（展示思考过程） | 30min |
| Day 6-7 | 整理代码，写 README，形成完整项目 | 60min |

**第 10 周结束时的成果**：
- 一个能自主决策的 Agent 应用
- 支持多工具调用（搜索文档、生成报告等）
- 有 Web 界面，能看到 Agent 的思考过程
- **这是你简历上的第二个 AI 项目**

---

## 第 11 周：MCP Server 开发

> 目标：用 TypeScript 开发一个 MCP Server，发挥你的前端优势
> 项目：一个能查询你 gitbook 文档的 MCP Server

这周**用 TypeScript 写**，是你最熟悉的语言。

| 天 | 内容 | 时间 |
|---|------|------|
| Day 1 | 阅读 MCP 官方 TypeScript SDK 文档，理解 Server 结构 | 30min |
| Day 2 | 搭建项目骨架：初始化 + 配置 + 最简单的 tool | 30min |
| Day 3 | 实现 `search_docs` 工具：搜索 gitbook 文档内容 | 30min |
| Day 4 | 实现 `get_doc` 资源：读取指定文档的完整内容 | 30min |
| Day 5 | 在 Claude Code 中测试你的 MCP Server | 30min |
| Day 6-7 | 发布到 npm + 写使用文档 | 60min |

**MCP Server 代码骨架**：

```typescript
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as fs from "fs";
import * as path from "path";

const server = new McpServer({
  name: "gitbook-docs",
  version: "1.0.0",
});

// Tool: search docs by keyword
server.tool(
  "search_docs",
  "Search gitbook documents by keyword",
  { keyword: z.string().describe("The keyword to search for") },
  async ({ keyword }) => {
    // search logic: read markdown files and find matches
    const docsDir = process.env.DOCS_DIR || "./docs";
    const results = searchFiles(docsDir, keyword);
    return {
      content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
    };
  }
);

// start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

**在 Claude Code 中测试**：

```bash
# 添加你的 MCP Server
claude mcp add gitbook-docs node dist/index.js

# 然后在 Claude Code 对话中就能使用
# "搜索我的文档中关于 RAG 的内容"
# → Claude Code 会自动调用你的 search_docs 工具
```

**第 11 周结束时的成果**：
- 一个可用的 MCP Server（TypeScript）
- 发布到 npm，任何人都能安装使用
- 能在 Claude Code / Cursor 中即插即用
- **这是你简历上的第三个 AI 项目，也是你独特的竞争力**

---

## 第 12 周：项目整理 + 面试准备

### 项目整理（Day 1-3）

把三个项目整理成可展示的状态：

```
项目一：RAG 知识库问答
  ├── GitHub 仓库 + README
  ├── 技术栈：Python + LangChain + Chroma + FastAPI + React
  ├── 功能：文档加载 → 向量化 → 检索 → 问答 → 流式输出
  └── 亮点：前后端完整、支持流式、引用来源

项目二：Agent 研究助手
  ├── GitHub 仓库 + README
  ├── 技术栈：Python + LangGraph + Ollama + FastAPI + React
  ├── 功能：多工具调用、自主决策、思考过程可视化
  └── 亮点：ReAct 循环、工具编排、RAG 集成

项目三：MCP Server
  ├── GitHub 仓库 + README + npm 包
  ├── 技术栈：TypeScript + MCP SDK
  ├── 功能：文档搜索、内容读取、即插即用
  └── 亮点：npm 发布、跨 AI 工具兼容
```

### 面试知识点复习（Day 4-5）

高频面试题及你应该能回答的程度：

```
概念题（你读过文章 + 做过项目，应该没问题）：
  ├── 什么是 RAG？为什么不直接把文档塞给 LLM？
  ├── 什么是 Agent？和普通 LLM 调用的区别？
  ├── 什么是 Function Calling？和 Prompt 解析工具调用的区别？
  ├── 什么是 MCP？解决了什么问题？
  ├── Embedding 是什么？向量数据库的原理？
  └── RAG vs Fine-tuning 的区别和选择？

实操题（你做过项目，应该能答）：
  ├── RAG 中 chunk_size 怎么选？太大太小有什么问题？
  ├── 检索结果不准怎么优化？（重排序、混合检索）
  ├── Agent 无限循环怎么处理？
  ├── 怎么评估 RAG 系统的效果？（你读过 Eval 文章）
  └── 怎么让 LLM 稳定输出 JSON？

加分题（展示深度）：
  ├── LangChain 和 LangGraph 的区别？什么时候用哪个？
  ├── MCP 和 Function Calling 的关系？
  └── 你的 MCP Server 是怎么设计的？
```

### 简历亮点提炼（Day 6-7）

```
你的差异化优势（面试时重点讲）：

1. 前端 + AI 的复合能力
   "我不只会调 LLM API，还能把 AI 能力做成用户友好的产品"

2. 工程化能力
   "我的项目有完整的前后端、流式输出、错误处理，不是 Jupyter Notebook demo"

3. 对 AI 工具生态的理解
   "我不只会用 AI 工具，我还开发过 MCP Server，理解 AI 工具的扩展机制"

4. 实际使用 AI 编程的经验
   "我日常使用 Claude Code 开发，理解 AI 辅助编程的最佳实践"
```

---

## 关键提醒

### 1. 30 分钟的使用方式

```
不要这样：
  打开教程 → 从头到尾看 30 分钟 → 关掉 → 第二天忘了大半

要这样：
  前 5 分钟：回顾昨天的内容（看自己写的代码）
  中间 20 分钟：写代码 / 跑示例 / 调试
  最后 5 分钟：记录遇到的问题和明天要做的事
```

### 2. 遇到问题的处理

```
首选：问 Claude Code（你已经在用了）
次选：查官方文档
最后：搜索 / 社区提问

不要在一个问题上卡超过 15 分钟（你每天只有 30 分钟）
```

### 3. 跳过 vs 深入

```
可以跳过的：
  - Python 高级特性（元编程、描述符等）
  - 模型训练和微调的细节
  - 数学原理（向量空间、注意力机制公式）
  - LangChain 的所有组件（只学你项目用到的）

需要深入的：
  - LLM API 的调用方式（天天用）
  - RAG 的完整流程（面试必问）
  - Prompt Engineering（核心技能）
  - 至少一个完整项目的端到端实现
```

### 4. 周末弹性时间

计划按每天 30 分钟设计，但实际执行中：
- 工作日可能有些天没时间 → 周末补
- 某个知识点卡住了 → 周末多花时间攻克
- 项目做到兴奋停不下来 → 那就多做一会儿

---

## 3 个月后你的技能树

```
                    ┌─ Prompt Engineering（实战）
                    ├─ LLM API 调用（Ollama / Gemini）
你现在的能力 ────────┤
(前端 + JS/TS)      ├─ RAG 全栈（文档→向量→检索→问答→UI）
                    ├─ Agent 开发（LangGraph + 工具编排）
                    ├─ MCP Server 开发（TypeScript）
                    ├─ Python AI 开发（LangChain 生态）
                    └─ 3 个完整项目 + 面试准备

匹配岗位：AI 应用工程师 / LLM 应用开发 / AI 全栈工程师
```
