# Week 5: RAG 核心组件

> 目标：理解 RAG 的每个组件，能跑通完整的 RAG pipeline

## 学习安排

| 天 | 文件 | 内容 | 时间 |
|---|------|------|------|
| Day 1 | `day1_langchain_setup.py` | 安装 LangChain + Chroma，跑通 quickstart | 30min |
| Day 2 | `day2_document_loader.py` | 文档加载器：加载 Markdown 文件 | 30min |
| Day 3 | `day3_text_splitter.py` | 文档切分：chunk_size 和 overlap | 30min |
| Day 4 | `day4_embedding.py` | Embedding：用 Ollama 做向量化 | 30min |
| Day 5 | `day5_vector_search.py` | 向量检索：用 Chroma 存储和检索 | 30min |
| Day 6-7 | `day67_rag_pipeline.py` | 串联：加载 → 切分 → 向量化 → 检索 | 60min |

## 环境准备

```bash
cd docs/14-AI/week5-rag-basics
python -m venv .venv && source .venv/bin/activate
pip install langchain langchain-community langchain-chroma chromadb
pip install openai python-dotenv

# Ollama embedding model
ollama pull nomic-embed-text
```
