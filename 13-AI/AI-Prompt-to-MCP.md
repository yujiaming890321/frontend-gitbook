# AI 交互演进：从提示词到 Function Calling 再到 LangChain

## 一、提示词时代（Prompt Engineering）

### 1. 最原始的交互：纯文本问答

早期 LLM（GPT-2、GPT-3）本质上就是一个**文本补全器**——你给一段文字，它接着往下写。

```
用户：1+1等于几？
LLM：1+1等于2。
```

没有任何结构化能力，你拿到的就是一段自然语言文本。LLM 无法：

- 获取实时信息（训练数据有截止日期）
- 执行计算（大模型做数学不可靠）
- 操作外部系统（数据库、API 等）

### 2. 用 Prompt 约束输出格式

想要结构化数据？只能在 prompt 里"求"它：

```
用户：请提取以下文本中的人名和城市，以 JSON 格式输出：
"张三住在北京，李四住在上海"

LLM：
好的，以下是提取结果：        ← 多余的废话
{"people": [{"name": "张三", "city": "北京"}, {"name": "李四", "city": "上海"}]}
```

**痛点：**

- 输出不稳定，有时夹带多余文字，JSON 解析直接报错
- 格式经常出错（多个逗号、缺少引号、单引号替代双引号）
- 需要大量 prompt 技巧来"约束"输出
- 开发者要写大量防御性解析代码

```python
def parse_llm_output(text):
    # 尝试提取 JSON
    # 有时 LLM 会输出 ```json ... ```
    # 有时直接输出 { ... }
    # 有时前面加一句 "好的，结果如下："
    # 有时 JSON 里有单引号而不是双引号...

    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        return json.loads(text)
    except:
        text = text.replace("'", '"')  # 修复单引号
        try:
            return json.loads(text)
        except:
            match = re.search(r'\{.*\}', text, re.DOTALL)  # 正则兜底
            if match:
                return json.loads(match.group())
            raise ValueError("无法解析 LLM 输出")
```

### 3. ReAct 模式：用 Prompt 模拟工具调用

#### 什么是 ReAct

ReAct = **Re**asoning + **Act**ing（推理 + 行动），2022 年由普林斯顿大学和 Google 联合发表的论文提出。

核心思想：**让 LLM 交替进行"思考"和"行动"，而不是一步到位给出答案。**

在 ReAct 之前，LLM 只能做两件事，而且是分开的：

```
方式一：纯推理（Chain-of-Thought, CoT）
用户：姚明的妻子比他矮多少？
LLM：让我想想... 姚明身高2.26米... 他妻子叶莉身高1.90米...
     所以矮了0.36米。                     ← 但数据可能是编的（幻觉）

方式二：纯行动（Act-only）
用户：姚明的妻子比他矮多少？
LLM：Action: search("姚明妻子身高")       ← 只会调工具，不会推理
     Observation: 叶莉，1.90米
     Action: search("姚明身高")
     Observation: 2.26米
     Final Answer: 0.36米                  ← 没有推理过程，复杂问题容易出错
```

**纯推理**容易产生幻觉（编造事实），**纯行动**缺少思考能力（遇到复杂问题不会拆解）。

#### ReAct 的做法：推理和行动交替进行

```
用户：姚明的妻子比他矮多少？

Thought: 我需要找到姚明和他妻子各自的身高，然后计算差值。先查姚明妻子是谁。
Action: search("姚明 妻子")
Observation: 姚明的妻子是叶莉，中国女篮运动员。

Thought: 知道了妻子是叶莉，现在需要查她的身高。
Action: search("叶莉 身高")
Observation: 叶莉身高1.90米。

Thought: 叶莉身高1.90米，现在需要查姚明的身高。
Action: search("姚明 身高")
Observation: 姚明身高2.26米。

Thought: 姚明2.26米，叶莉1.90米，差值 = 2.26 - 1.90 = 0.36米。我现在知道答案了。
Final Answer: 姚明的妻子叶莉比他矮0.36米（姚明2.26米，叶莉1.90米）。
```

关键区别：**每次行动前都有一步思考（Thought），思考决定下一步行动（Action），行动的结果（Observation）又反馈给下一轮思考。**

#### ReAct 的循环结构

```
┌──→ Thought（推理：我需要做什么？）
│         ↓
│    Action（行动：调用工具）
│         ↓
│    Observation（观察：工具返回了什么）
│         ↓
│    判断：够了吗？
│         ↓
└── 不够 ← ┘
          ↓ 够了
     Final Answer
```

#### ReAct vs CoT vs Act-only 对比

| | Chain-of-Thought (CoT) | Act-only | ReAct |
|---|---|---|---|
| **推理** | 有（但可能编造事实） | 无 | 有 |
| **工具使用** | 无 | 有（但不会拆解问题） | 有 |
| **幻觉风险** | 高（凭记忆回答） | 低（用工具获取事实） | 低 |
| **复杂问题** | 能拆解但数据不可靠 | 不会拆解 | 能拆解且数据可靠 |

#### 实现方式：全靠 Prompt

在 Function Calling 出现之前，ReAct 完全靠 **prompt 工程**实现——用 prompt 教 LLM 按固定格式输出，开发者用正则解析文本：

```
你是一个有用的助手，你可以使用以下工具：

1. search(query) - 搜索网页
2. calculator(expression) - 计算数学表达式

请严格按以下格式回答：

Thought: 我需要思考该怎么做
Action: 工具名称
Action Input: 工具的输入参数
Observation: （工具返回的结果，由系统填入）
... 可以重复多次 ...
Thought: 我现在知道答案了
Final Answer: 最终答案
```

LLM 的输出：

```
Thought: 用户想知道北京天气，我需要搜索一下
Action: search
Action Input: 北京今天天气
```

然后开发者的代码去**解析这段文本**，用正则表达式提取 `Action` 和 `Action Input`：

```python
REACT_PROMPT = """你可以使用以下工具：
- search(query): 搜索信息
- calculator(expr): 计算数学表达式

请严格按格式交替输出 Thought / Action / Action Input / Observation ..."""

# 开发者的代码循环
while True:
    output = llm.generate(prompt)

    # 如果 LLM 输出了最终答案，退出循环
    if "Final Answer:" in output:
        answer = output.split("Final Answer:")[-1].strip()
        break

    # 用正则解析 Action 和 Action Input
    action = re.search(r"Action:\s*(.+)", output).group(1).strip()
    action_input = re.search(r"Action Input:\s*(.+)", output).group(1).strip()

    # 执行工具
    observation = tools[action](action_input)

    # 把 Observation 拼回 prompt，继续下一轮
    prompt += output + f"\nObservation: {observation}\n"
```

早期的 LangChain Agent 就是用这种方式实现的。

#### ReAct 模式的痛点

- LLM 经常不按格式输出（多打一个换行就解析失败）
- 正则匹配脆弱，各种边界情况
- LLM 有时会"幻觉"出不存在的工具名
- 参数只能是字符串，无法传复杂对象
- 每次都靠"君子协定"，没有强制保证

#### ReAct 在技术栈中的位置

```
ReAct 是一种思维模式/论文方法论
      ↓
早期 LangChain 用 Prompt 实现 ReAct Agent
      ↓
Function Calling 出现后，ReAct 的 Action 部分被 Function Calling 取代
      ↓
但"交替推理和行动"的思想仍然是所有 Agent 框架的核心
```

**ReAct 不是一个工具或框架，而是一种设计模式**——"先想再做，做完再想"。Function Calling 取代了它不稳定的实现方式（文本解析），但核心思想被保留下来，成为了所有 AI Agent 的基本工作方式。

### 4. 提示词时代小结

这个阶段的核心特征是：**一切交互都是文本，一切约束都靠 prompt**。开发者和 LLM 之间没有"协议"，只有"约定"，而约定随时可能被打破。

---

## 二、Function Calling 时代

### 1. 什么是 Function Calling

2023 年 6 月，OpenAI 推出了 **Function Calling** 机制。

一句话：**让 LLM 以结构化的方式告诉你"我想调用哪个函数、传什么参数"，由 API 层面保证输出是合法 JSON。**

注意：LLM 自己**不执行**函数，它只是输出一个 JSON 格式的"调用意图"。

### 2. 工作方式

你在调用 API 时，告诉 LLM 有哪些函数可用（通过 JSON Schema 描述）：

```json
{
  "name": "get_weather",
  "description": "获取指定城市的天气",
  "parameters": {
    "type": "object",
    "properties": {
      "city": { "type": "string", "description": "城市名" }
    },
    "required": ["city"]
  }
}
```

LLM 判断用户意图后，返回结构化的调用请求：

```json
{
  "function_call": {
    "name": "get_weather",
    "arguments": "{\"city\": \"北京\"}"
  }
}
```

### 3. 完整流程

```
1. 用户："北京天气怎么样？"
              ↓
2. 你的代码把用户消息 + 函数定义 一起发给 LLM API
              ↓
3. LLM 返回：我想调用 get_weather(city="北京")    ← 结构化 JSON，不是文本
              ↓
4. 你的代码 真正执行 get_weather("北京")，拿到结果："晴，25°C"
              ↓
5. 你把函数执行结果 再发回给 LLM
              ↓
6. LLM 生成最终回答："北京今天天气晴朗，气温25°C，适合出行。"
```

代码示例：

```python
import openai

# 第一步：带上函数定义，发送用户消息
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "北京天气怎么样？"}],
    functions=[{
        "name": "get_weather",
        "description": "获取城市天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            }
        }
    }]
)

# 第二步：LLM 返回了函数调用意图
func_call = response.choices[0].message.function_call
# func_call.name == "get_weather"
# func_call.arguments == '{"city": "北京"}'

# 第三步：你自己执行函数
result = get_weather("北京")  # 你的代码，调真实 API

# 第四步：把结果返回给 LLM，让它生成最终回答
final = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "北京天气怎么样？"},
        {"role": "assistant", "function_call": func_call},
        {"role": "function", "name": "get_weather", "content": result}
    ]
)
# final → "北京今天晴朗，25°C..."
```

### 4. 核心要点

| 要点 | 说明 |
|------|------|
| **LLM 不执行函数** | 它只输出"想调用什么"，执行权在你手里 |
| **输出是结构化的** | API 层面保证返回合法 JSON，不会夹带多余文字 |
| **LLM 自己判断要不要调用** | 如果用户问"你好"，它不会调用 get_weather |
| **可以定义多个函数** | LLM 会根据意图选择合适的那个 |
| **可以并行调用** | 新版支持一次返回多个函数调用 |

### 5. 与提示词时代的对比

| | 提示词时代 | Function Calling 时代 |
|---|---|---|
| **输出格式** | 自然语言，靠 prompt 约束 | API 层面保证结构化 JSON |
| **解析方式** | 正则表达式 / 字符串匹配 | 直接拿到 JSON 对象 |
| **稳定性** | 经常输出不符合格式 | 格式稳定可靠 |
| **参数类型** | 只能是字符串 | 支持 number / boolean / object 等 |
| **多工具选择** | LLM 经常选错 / 幻觉 | 有 schema 约束，准确率高 |
| **开发体验** | 大量防御性代码 | 几行代码搞定 |

### 6. Function Calling 的本质

**把"约定"变成了"协议"**——从靠 prompt 的"君子协定"变成了 API 层面的强制保证。给 LLM 加了一个标准化的"工具使用接口"，LLM 负责理解意图和决策，你的代码负责真正执行，二者分工协作。

但 Function Calling 只解决了单个工具调用的问题，开发者仍然需要自己处理大量工作...

---

## 三、LangChain 时代

### 1. Function Calling 之后的新问题：胶水代码太多

Function Calling 解决了"LLM 怎么调用工具"，但要构建完整的 AI 应用，你还需要手动处理：

- Prompt 模板管理
- 多轮对话的上下文管理（Memory）
- 多个 Function Call 的编排和链式调用
- 不同 LLM 提供商的 API 适配（OpenAI / Claude / Gemini ...）
- 文档加载、切分、向量化（RAG）
- 错误处理、重试逻辑
- Agent 的循环决策逻辑（调用工具 → 观察结果 → 再决策 → 再调用）

每个开发者都在重复造轮子。

### 2. LangChain 的出现

LangChain（2022 年 10 月开源）是对上述所有问题的**统一抽象层**：

```
┌─────────────────────────────────────────────┐
│              LangChain 框架                  │
├──────────┬──────────┬───────────┬────────────┤
│  Chains  │  Agents  │  Memory   │   Tools    │
│ (链式调用)│(自主决策) │(上下文管理)│(外部工具)   │
├──────────┴──────────┴───────────┴────────────┤
│         LLM 抽象层 (OpenAI/Claude/...)        │
└─────────────────────────────────────────────┘
```

> 注意：LangChain 实际上比 Function Calling **更早**出现。早期 LangChain 用 ReAct prompt 模式实现 Agent，Function Calling 出现后 LangChain 迅速切换到了更稳定的 Function Calling 作为底层机制。

### 3. 核心抽象概念

| 概念 | 作用 | 与 Function Call 的关系 |
|------|------|----------------------|
| **Tools** | 封装外部函数 | 对 Function Call 的包装 |
| **Agents** | 让 LLM 自主决定调用哪些 Tools | 基于 Function Call 实现决策循环 |
| **Chains** | 将多个步骤串联 | 多个 Function Call 的编排 |
| **Memory** | 管理对话历史 | Function Call 本身不管这个 |
| **Retrievers** | RAG 检索（从文档中找相关内容） | Function Call 本身不管这个 |
| **Prompt Templates** | 管理和复用 prompt | 标准化 prompt 的构建 |

### 4. 关键关系：不是替代，是封装

```
提示词工程 是最初的交互方式（文本层）
      ↓
Function Call 是标准化的工具调用机制（协议层）
      ↓
LangChain 是构建完整应用的框架（应用层）
```

一个类比：

- **提示词** ≈ 直接用 TCP socket 发送原始字节
- **Function Call** ≈ HTTP 协议（标准化了请求/响应格式）
- **LangChain** ≈ Express / Django 这样的 Web 框架（提供路由、中间件、ORM 等）

### 5. Agent 的核心循环

LangChain 的 Agent 内部就是在用 Function Call 实现"决策 → 执行 → 观察 → 再决策"的循环：

```python
# LangChain Agent 的核心循环（简化版）
while not finished:
    # 1. LLM 决策（底层就是 Function Call）
    action = llm.decide(prompt + observations)

    # 2. 执行工具
    result = tool.run(action.input)

    # 3. 观察结果，加入上下文
    observations.append(result)

    # 4. LLM 判断是否结束
    if action.type == "final_answer":
        finished = True
```

### 6. 一个实际例子

用 LangChain 构建一个能搜索 + 计算的 Agent：

```python
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI

# 定义工具
tools = [
    Tool(name="Search", func=search_api, description="搜索网页信息"),
    Tool(name="Calculator", func=calculator, description="计算数学表达式"),
]

# 创建 Agent（内部自动处理 Function Call 循环）
agent = initialize_agent(tools, OpenAI(), agent="zero-shot-react-description")

# 一行代码完成复杂任务
agent.run("苹果公司当前市值是多少？换算成人民币是多少？")

# Agent 内部自动：
# 1. 调用 Search 搜索苹果市值 → 3.5万亿美元
# 2. 调用 Search 搜索当前汇率 → 1:7.2
# 3. 调用 Calculator 计算 3.5万亿 * 7.2
# 4. 返回最终答案
```

如果没有 LangChain，你需要自己写上面的循环、解析、错误处理、重试逻辑...

### 7. LangChain 的局限

LangChain 的 Agent 本质上是一个**线性循环**——思考 → 调用工具 → 观察 → 再思考。但真实场景往往更复杂：

- 根据结果走不同分支（条件路由）
- 多个 Agent 协作，互相传递结果
- 某个步骤失败了需要回退重试
- 需要人工审批后才继续
- 需要并行执行多个任务再汇总

LangChain 的 Chain 和 Agent 抽象太简单，表达不了这些复杂流程。这就催生了 LangGraph。

---

## 四、Agent（智能体）

### 1. 什么是 Agent

一句话：**Agent 就是一个能自主决策、循环调用工具来完成任务的 LLM 应用。**

普通 LLM 应用是"你问我答"，Agent 是"你给我一个目标，我自己想办法完成"。

```
普通 LLM 应用（一问一答）：
用户 → LLM → 回答                              ← 一次调用就结束

Agent（自主循环）：
用户 → LLM → 需要搜索 → 执行搜索 → 结果不够 → 再搜索 →
       → 还需要计算 → 执行计算 → 现在够了 → 最终回答
```

关键区别：**Agent 自己决定下一步做什么，做多少步，什么时候停。**

### 2. Agent 的核心三要素

```
┌────────────────────────────────────────┐
│              Agent                     │
├────────────┬────────────┬──────────────┤
│   大脑      │   工具      │   记忆       │
│  (LLM)     │  (Tools)   │  (Memory)    │
│            │            │              │
│ 理解意图    │ 搜索/计算   │ 对话历史     │
│ 制定计划    │ 读写文件    │ 中间结果     │
│ 做出决策    │ 调用 API   │ 长期知识     │
└────────────┴────────────┴──────────────┘
```

| 要素 | 作用 | 类比 |
|------|------|------|
| **LLM（大脑）** | 理解任务、拆解步骤、做决策 | 人的大脑 |
| **Tools（工具）** | 执行具体动作（搜索、计算、API 调用等） | 人的手和脚 |
| **Memory（记忆）** | 记住对话历史和中间结果 | 人的记忆 |

### 3. Agent 的工作循环

```
用户：帮我分析特斯拉最近的股价走势，写一份报告

Agent 内部：

循环 1:
  Think:   我需要先获取特斯拉最近的股价数据
  Act:     调用 stock_api("TSLA", last_30_days)
  Observe: [收到30天的股价数据]

循环 2:
  Think:   有了数据，我需要分析趋势。让我也看看最近的新闻
  Act:     调用 search("特斯拉 最近新闻")
  Observe: [收到新闻列表]

循环 3:
  Think:   股价数据和新闻都有了，我可以写报告了
  Act:     调用 write_file("report.md", 报告内容)
  Observe: [文件写入成功]

循环 4:
  Think:   报告已经写好了，任务完成
  Final Answer: 报告已生成到 report.md，主要发现是...
```

**没有人告诉 Agent 要调几次工具、调哪个工具——它自己决定。**

### 4. Agent 的类型

```
┌─────────────────────────────────────────────────┐
│                Agent 类型                        │
├─────────────────┬───────────────────────────────┤
│ ReAct Agent     │ 最经典的模式                   │
│                 │ 思考→行动→观察 循环             │
├─────────────────┼───────────────────────────────┤
│ Plan-and-Execute│ 先制定完整计划，再逐步执行      │
│                 │ 适合复杂任务                    │
├─────────────────┼───────────────────────────────┤
│ Multi-Agent     │ 多个 Agent 协作                │
│                 │ 如：研究员 + 写手 + 审核员       │
├─────────────────┼───────────────────────────────┤
│ Autonomous Agent│ 高度自主，能自己设定子目标      │
│                 │ 如：AutoGPT、Claude Code       │
└─────────────────┴───────────────────────────────┘
```

### 5. 实际例子：Claude Code 就是一个 Agent

```
你：帮我修复这个 bug

Claude Code（Agent）内部：
1. Think: 我需要先了解代码结构       → 读取文件
2. Think: 找到了可能出问题的地方     → 读取具体文件
3. Think: 确认了 bug 原因            → 编辑代码修复
4. Think: 修复后要验证               → 运行测试
5. Think: 测试通过了                 → 完成

整个过程你只说了一句话，Agent 自主完成了 5 个步骤
```

### 6. Agent 与前面技术的关系

```
提示词          →  让 LLM 能理解意图（Agent 的"大脑"基础）
ReAct           →  定义了 Agent 的思考模式（推理+行动交替）
Function Call   →  让 Agent 能可靠地调用工具（Agent 的"手"）
LangChain       →  提供了构建 Agent 的框架（开箱即用）
LangGraph       →  让 Agent 支持复杂工作流（条件分支、多 Agent 协作）
```

**Agent 不是某个具体技术，而是一种应用模式**——它把上面所有技术组合在一起，构成一个能自主完成任务的系统。

---

## 五、RAG（检索增强生成）

### 1. 问题：LLM 的知识是有限的

```
用户：我们公司的请假制度是什么？
LLM：我不知道你们公司的请假制度...         ← 训练数据里没有你公司的信息

用户：这个 API 最新版本的用法？
LLM：根据我的训练数据...                   ← 信息可能已过时
```

LLM 的知识局限在训练数据里，无法回答：

- 私有数据（公司文档、个人笔记）
- 最新信息（训练截止日期之后的）
- 专业领域的精确内容（容易产生幻觉）

### 2. 什么是 RAG

RAG = **R**etrieval **A**ugmented **G**eneration（检索增强生成）

一句话：**先从你的知识库中检索相关内容，再把检索到的内容和用户问题一起交给 LLM 回答。**

```
没有 RAG：
用户问题 ──→ LLM ──→ 回答（凭记忆，可能不准）

有 RAG：
用户问题 ──→ 检索知识库 ──→ 找到相关文档片段 ──→ 问题+文档 一起给 LLM ──→ 回答（基于真实资料）
```

### 3. 完整流程

```
                    离线阶段（提前准备）
┌──────────────────────────────────────────────┐
│                                              │
│  文档 ──→ 切分成小块 ──→ Embedding 向量化     │
│                              ↓               │
│                         存入向量数据库        │
│                                              │
└──────────────────────────────────────────────┘

                    在线阶段（实时查询）
┌──────────────────────────────────────────────┐
│                                              │
│  1. 用户提问："公司年假有几天？"               │
│         ↓                                    │
│  2. 问题 Embedding 向量化                     │
│         ↓                                    │
│  3. 在向量数据库中搜索最相似的文档块            │
│         ↓                                    │
│  4. 找到相关内容：                             │
│     "员工入职满1年享有5天年假，满5年10天..."    │
│         ↓                                    │
│  5. 把问题 + 检索到的内容一起发给 LLM：         │
│     "根据以下资料回答问题：                     │
│      资料：员工入职满1年享有5天年假...           │
│      问题：公司年假有几天？"                    │
│         ↓                                    │
│  6. LLM 回答："根据公司制度，入职满1年有5天..." │
│                                              │
└──────────────────────────────────────────────┘
```

### 4. 关键概念解释

#### Embedding（向量嵌入）

把文本转换成一组数字（向量），语义相近的文本对应的向量也相近：

```
"猫在沙发上睡觉"  →  [0.12, 0.85, 0.33, ...]
"小猫躺在沙发上"  →  [0.13, 0.84, 0.35, ...]  ← 语义相近，向量也接近
"今天股市大涨"    →  [0.91, 0.11, 0.67, ...]  ← 语义不相关，向量差异大
```

#### 向量数据库

专门存储和检索向量的数据库，能快速找到与查询向量最相似的文档：

```
常见向量数据库：Pinecone、Milvus、Chroma、FAISS、Weaviate
```

#### Chunking（文档切分）

把长文档切成小块，因为：

- LLM 的上下文窗口有限
- 小块内容检索更精确
- 避免把无关内容塞给 LLM

```
一份50页的员工手册
      ↓ 切分
[第1块] 请假制度：员工入职满1年...
[第2块] 薪资结构：基本工资由...
[第3块] 晋升流程：每年两次评估...
...
```

### 5. 代码示例

```python
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# ========== 离线阶段：准备知识库 ==========

# 1. 加载文档
loader = TextLoader("company_handbook.txt")
documents = loader.load()

# 2. 切分成小块
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# 3. 向量化 & 存入向量数据库
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# ========== 在线阶段：回答问题 ==========

# 4. 构建 RAG 链
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(),
    retriever=vectorstore.as_retriever(),
)

# 5. 提问
answer = qa_chain.run("公司年假有几天？")
# 内部自动：检索相关文档 → 拼接 prompt → LLM 回答
```

### 6. 为什么不直接把所有文档塞给 LLM？

```
方案一：全部塞进去
  - 50页文档 ≈ 10万 token
  - 超出上下文窗口限制
  - 就算放得下，费用也很高
  - LLM 在长文本中容易"迷路"，忽略关键信息

方案二：RAG（只检索相关的）
  - 只取最相关的 3-5 个文档块 ≈ 几百 token
  - 不超窗口，费用低
  - LLM 专注于少量相关信息，回答更准确
```

### 7. RAG vs Fine-tuning（微调）

| | RAG | Fine-tuning |
|---|---|---|
| **原理** | 检索外部知识，作为上下文给 LLM | 用数据重新训练 LLM 的权重 |
| **更新知识** | 更新文档即可，即时生效 | 需要重新训练，耗时耗钱 |
| **可溯源** | 可以引用来源文档 | 无法追溯知识来源 |
| **成本** | 低（只需向量数据库） | 高（需要 GPU 训练） |
| **幻觉** | 低（基于真实文档） | 可能仍有幻觉 |
| **适用场景** | 知识库问答、文档助手 | 改变模型风格/能力 |

### 8. RAG 与 Agent 的关系

RAG 可以作为 Agent 的一个**工具**：

```
Agent 收到问题
  ↓
  Think:   这个问题需要查公司文档
  Act:     调用 RAG 工具（检索 + 生成）
  Observe: 得到基于文档的回答
  ↓
  Think:   还需要计算一下
  Act:     调用 Calculator 工具
  Observe: 计算结果
  ↓
  Final Answer: 综合回答
```

**RAG 负责"让 LLM 知道它不知道的事"，Agent 负责"让 LLM 能做它做不了的事"**。两者经常组合使用。

---

## 六、LangGraph：图编排时代

### 1. 什么是 LangGraph

LangGraph（2024 年推出）是 LangChain 团队开发的**有状态图编排框架**，用**图（Graph）**来描述 Agent 的工作流：

```
┌──────────────────────────────────────────────────┐
│                 LangGraph                        │
│                                                  │
│   节点（Node）= 一个处理步骤（LLM调用/工具/代码）  │
│   边（Edge）= 步骤之间的流转关系                   │
│   状态（State）= 在节点之间传递的共享数据           │
│                                                  │
│          ┌──→ [分析] ──→ [写报告] ──┐            │
│   [输入] ─┤                         ├→ [输出]    │
│          └──→ [搜索] ──→ [总结]  ──┘            │
└──────────────────────────────────────────────────┘
```

核心思路：**把 Agent 的工作流建模为一个有向图，每个节点是一个步骤，边决定了流转逻辑。**

### 2. 代码示例

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 1. 定义状态（在节点之间共享的数据）
class AgentState(TypedDict):
    question: str
    search_results: str
    analysis: str
    final_answer: str

# 2. 定义节点（每个节点是一个函数）
def search_node(state):
    results = search_tool(state["question"])
    return {"search_results": results}

def analyze_node(state):
    analysis = llm.invoke(f"分析以下内容：{state['search_results']}")
    return {"analysis": analysis}

def answer_node(state):
    answer = llm.invoke(f"基于分析 {state['analysis']}，回答 {state['question']}")
    return {"final_answer": answer}

# 3. 条件路由（根据状态决定走哪条边）
def should_continue(state):
    if "不确定" in state["analysis"]:
        return "search"   # 回到搜索节点，重新搜
    return "answer"       # 进入回答节点

# 4. 构建图
graph = StateGraph(AgentState)
graph.add_node("search", search_node)
graph.add_node("analyze", analyze_node)
graph.add_node("answer", answer_node)

graph.set_entry_point("search")
graph.add_edge("search", "analyze")
graph.add_conditional_edges("analyze", should_continue, {
    "search": "search",    # 不确定 → 回去重新搜索
    "answer": "answer",    # 确定 → 生成答案
})
graph.add_edge("answer", END)

# 5. 运行
app = graph.compile()
result = app.invoke({"question": "量子计算的最新进展是什么？"})
```

### 3. LangGraph 的核心能力

| 能力 | 说明 |
|------|------|
| **条件路由** | 根据运行时状态走不同分支 |
| **循环** | 节点可以形成环，支持重试和迭代 |
| **持久化状态** | 状态可以保存到数据库，支持长时间运行 |
| **人工介入（Human-in-the-loop）** | 流程可以暂停，等待人工审批后继续 |
| **多 Agent 协作** | 多个 Agent 作为不同节点，协同工作 |
| **流式输出** | 支持每个节点的结果实时流式返回 |

### 4. LangChain vs LangGraph

```
LangChain Agent：我是一个循环  →  适合简单的"问答+工具"场景
LangGraph：     我是一个图    →  适合复杂的多步骤工作流
```

| | LangChain Agent | LangGraph |
|---|---|---|
| **流程模型** | 线性循环（while loop） | 有向图（Graph） |
| **分支** | 不支持 | 条件路由 |
| **状态管理** | 简单的内存变量 | 持久化、可序列化的 State |
| **人工介入** | 不原生支持 | 内置 Human-in-the-loop |
| **多 Agent** | 需要手动编排 | 原生支持多 Agent 节点 |
| **适用场景** | 简单问答 + 工具 | 复杂工作流、多步审批、协作 |

---

## 七、MCP：工具标准化时代

### 1. 问题背景

Function Calling 和 LangChain 解决了"LLM 怎么调用工具"的问题，但带来了一个新问题：

**每个 AI 应用都在自己写工具集成，导致大量重复工作。**

```
# 现状：每个 AI 应用各自集成（M × N 的问题）
Claude App  ──→ 自己写 GitHub 工具、Slack 工具、数据库工具...
ChatGPT App ──→ 自己写 GitHub 工具、Slack 工具、数据库工具...
Cursor      ──→ 自己写 GitHub 工具、Slack 工具、数据库工具...
```

这就像 Web 时代之前，每个应用都要自己实现网络通信协议一样。

### 2. MCP 是什么

MCP（Model Context Protocol，模型上下文协议）是 Anthropic 在 2024 年底推出的**开放标准协议**，定义了 AI 应用与外部工具/数据源之间的通信方式。

一句话：**MCP 是 AI 时代的 USB 接口**——让任何 AI 应用可以即插即用地连接任何外部工具。

```
# 之前：M × N 的集成问题
M 个 AI 应用 × N 个工具 = M×N 个集成代码

# MCP 之后：M + N
M 个 AI 应用 ──→ MCP 协议 ←── N 个工具
每个 AI 应用实现一次 MCP Client
每个工具实现一次 MCP Server
总共只需 M + N 个实现
```

### 3. 架构

```
┌─────────────┐     MCP 协议      ┌─────────────────┐
│  AI 应用     │ ←──────────────→  │  MCP Server      │
│ (MCP Client) │                   │  (工具提供方)     │
│              │  JSON-RPC 通信    │                   │
│ Claude Code  │  ← tools/list     │  GitHub Server    │
│ Cursor       │  ← tools/call     │  Slack Server     │
│ 自定义应用   │  ← resources/read │  Database Server  │
└─────────────┘                   └─────────────────┘
```

### 4. MCP 的三大核心概念

```
┌────────────────────────────────────────────────────┐
│                    MCP Server                       │
├────────────┬─────────────────┬──────────────────────┤
│   Tools    │   Resources     │   Prompts            │
│  (工具)    │  (资源)          │  (提示词模板)         │
│            │                 │                      │
│ 可执行的    │ 可读取的数据     │ 预定义的交互模板      │
│ 函数/动作   │ 文件/API/数据库  │                      │
│            │                 │                      │
│ 例：创建    │ 例：读取文件     │ 例：代码审查的        │
│ GitHub PR  │ 内容、查询数据库  │ 标准 prompt          │
└────────────┴─────────────────┴──────────────────────┘
```

| 概念 | 类比 | 说明 |
|------|------|------|
| **Tools** | Function Calling 里的函数 | AI 可以调用的动作（写文件、发消息、创建 PR） |
| **Resources** | REST API 的 GET 端点 | AI 可以读取的数据（文件内容、数据库记录） |
| **Prompts** | Prompt 模板库 | 预定义的交互模板（代码审查模板、分析模板） |

### 5. 通信方式

MCP 使用 **JSON-RPC 2.0** 协议通信，支持两种传输方式：

```
1. stdio（标准输入/输出）
   AI 应用 ──spawn──→ MCP Server 进程
   通过 stdin/stdout 通信
   适合本地工具

2. HTTP + SSE（服务器发送事件）/ Streamable HTTP
   AI 应用 ──HTTP──→ 远程 MCP Server
   适合云端服务
```

### 6. 实际使用示例

以 Claude Code 为例，配置一个 MCP Server：

```json
// .claude/settings.json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxx"
      }
    }
  }
}
```

配置后，Claude Code 就自动获得了 GitHub 相关的工具（创建 PR、查看 Issue 等），无需写任何代码。

### 7. MCP 与 Function Calling 的区别

| | Function Calling | MCP |
|---|---|---|
| **解决的问题** | LLM 怎么调用工具 | 工具怎么标准化提供和发现 |
| **定义方** | AI 应用开发者在代码里定义 | 工具提供方独立实现为 MCP Server |
| **作用域** | 单个 AI 应用内部 | 跨应用、跨平台 |
| **工具发现** | 硬编码在应用里 | 动态发现（tools/list） |
| **类比** | "这个应用能调用这些函数" | "这些函数作为服务发布，任何应用都能用" |

---

## 八、完整演进时间线

```
2020.06  GPT-3 发布（纯文本补全，只能靠 Prompt 交互）
2022.10  LangChain 开源（基于 ReAct Prompt 模式实现 Agent）
2022.11  ChatGPT 发布（对话式 AI 爆发）
2023.03  GPT-4 发布（能力增强，Agent 更可靠）
2023.06  OpenAI 推出 Function Calling（标准化工具调用，取代 ReAct 文本解析）
2023.11  OpenAI 推出 Assistants API（官方的"类 LangChain"方案）
2024     各家推出 Tool Use（Anthropic Tool Use、Google Function Calling 等）
2024.01  LangGraph 发布（有状态图编排，解决复杂工作流）
2024.11  Anthropic 发布 MCP 协议（标准化 AI 与外部工具的连接方式）
2025+    MCP 生态快速扩展，各大 AI 工具（Cursor、Claude Code 等）接入
```

---

## 九、总结

### 技术演进全景

```
提示词          →  Function Calling  →  LangChain       →  LangGraph        →  MCP
靠文本约定        靠 API 协议保证       提供应用框架        提供图编排框架       提供工具分发协议
解析不稳定        结构化输出稳定        开箱即用           复杂流程可控        即插即用
单次交互          单次工具调用          多步骤循环          多步骤有向图        跨应用工具共享
每个人造轮子      标准化了调用接口      标准化了应用架构    标准化了流程编排    标准化了工具生态
```

其中 **Agent** 和 **RAG** 是贯穿各阶段的核心应用模式：

```
Agent = LLM + Tools + Memory      → 自主决策、循环完成任务的应用模式
RAG   = Retrieval + LLM           → 用外部知识增强 LLM 回答的技术方案
```

### 各层关系类比

```
提示词         ≈  直接用 TCP socket 发送原始字节
Function Call  ≈  HTTP 协议（标准化了请求/响应格式）
LangChain      ≈  Express / Django（Web 应用框架）
LangGraph      ≈  Airflow / Temporal（工作流编排引擎）
MCP            ≈  USB / REST API 标准（即插即用的设备/服务接口）
Agent          ≈  一个能自主工作的员工（利用以上所有技术）
RAG            ≈  员工随身携带的参考资料库（解决知识不足问题）
```

### 它们解决的核心问题

| 技术 | 核心问题 |
|------|---------|
| **提示词** | LLM 怎么理解我的意图 |
| **ReAct** | LLM 怎么像人一样"先想再做" |
| **Function Calling** | LLM 怎么可靠地调用工具 |
| **LangChain** | 怎么把多个工具调用编排成应用 |
| **Agent** | 怎么让 LLM 自主决策、循环完成复杂任务 |
| **RAG** | 怎么让 LLM 基于真实资料回答（而不是编造） |
| **LangGraph** | 怎么处理复杂的、有分支有状态的工作流 |
| **MCP** | 怎么让工具生态标准化，实现跨应用即插即用 |

每一层都不是替代前一层，而是在前一层之上解决更高层次的问题。Agent 和 RAG 作为核心应用模式，贯穿于 LangChain、LangGraph 等框架之中。它们共同构成了当前 AI 应用开发的完整技术栈。
