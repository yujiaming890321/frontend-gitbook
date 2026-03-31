# Week 8: LangGraph 基础 -- 构建 Agent 的状态图框架

> 目标：掌握 LangGraph 的核心概念，能用 StateGraph 构建有条件分支和工具调用的 Agent

## 学习安排

| 天 | 文件 | 内容 | 时间 |
|---|------|------|------|
| Day 1 | `day1_graph_basics.py` | Graph / Node / Edge 概念，创建最简单的 StateGraph | 40min |
| Day 2 | `day2_simple_graph.py` | Input -> LLM 处理 -> Output 完整图 | 40min |
| Day 3 | `day3_conditional_routing.py` | 条件边：根据 LLM 判断结果路由到不同分支 | 45min |
| Day 4 | `day4_tool_node.py` | 工具节点：让 Agent 调用自定义工具 | 45min |
| Day 5 | `day5_state_management.py` | 状态管理：State 如何在节点间传递，TypedDict 状态 | 45min |
| Day 6-7 | `day67_calculator_agent.py` | 综合练习：Calculator Agent，自动判断是否需要计算 | 60min |

## 环境准备

```bash
# 1. 安装依赖
pip install langgraph langchain langchain-community

# 2. 确保 Ollama 已安装并运行
ollama serve

# 3. 拉取模型（如果还没有）
ollama pull qwen2.5:7b
```

## 如何使用

```bash
# 1. 进入目录
cd docs/14-AI/week8-langgraph-basics

# 2. 运行某天的练习
python day1_graph_basics.py

# 3. 每个文件中有 TODO 标记的地方是练习题，自己动手填写
# 4. 参考答案在注释中，先试着自己写再看答案
```

## 核心概念速览（前端类比）

```
LangGraph 概念        前端类比
─────────────────────────────────────────
StateGraph            React 状态机 / XState
Node                  Express 中间件 / Redux reducer
Edge                  React Router 路由规则
Conditional Edge      React Router 的条件重定向
State (TypedDict)     Redux Store / React Context
END                   路由终点 / return 语句
compile()             webpack build / 路由注册
```

## 学习方法

```
前 5 分钟：回顾昨天的内容
中间 30 分钟：写代码 / 跑示例 / 调试
最后 5 分钟：记录遇到的问题和明天要做的事
```
