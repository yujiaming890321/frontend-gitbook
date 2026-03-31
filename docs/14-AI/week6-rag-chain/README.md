# Week 6: 构建完整 RAG 问答链

> 目标：把 Week 5 的向量检索升级为完整的 RAG 问答系统，能根据文档回答问题、引用来源、处理边界情况

## 学习安排

| 天 | 文件 | 内容 | 时间 |
|---|------|------|------|
| Day 1 | `day1_retrieval_qa.py` | RetrievalQA Chain：把检索 + LLM 串成问答链 | 30min |
| Day 2 | `day2_prompt_template.py` | 优化 prompt 模板：让回答引用来源文档 | 30min |
| Day 3 | `day3_tuning.py` | 调优 chunk_size 和 k 值，观察效果变化 | 30min |
| Day 4 | `day4_no_answer.py` | 处理检索不到的情况：让 AI 说"我不知道"而不是编造 | 30min |
| Day 5 | `day5_conversational_rag.py` | 添加对话历史：支持追问（Conversational RAG） | 30min |
| Day 6-7 | `day67_testing.py` | 测试和调优：用真实文档测试各种问题 | 60min |

## 前置依赖

```bash
# 安装依赖
pip install langchain langchain-community langchain-chroma chromadb

# 确保 Ollama 已启动并拉取了模型
ollama serve
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

## 如何使用

```bash
# 1. 进入目录
cd docs/14-AI/week6-rag-chain

# 2. 运行某天的练习
python day1_retrieval_qa.py

# 3. 每个文件中有 TODO 标记的地方是练习题，自己动手填写
# 4. 参考答案在注释中，先试着自己写再看答案
```

## 学习方法

```
前 5 分钟：回顾昨天的内容
中间 20 分钟：写代码 / 跑示例 / 调试
最后 5 分钟：记录遇到的问题和明天要做的事
```

## 知识递进

```
Week 5: 文档加载 + 切分 + 向量化 + 检索
    ↓
Week 6: 检索 + LLM → 完整问答链 (本周)
    ↓
Week 7: Agent 基础
```
