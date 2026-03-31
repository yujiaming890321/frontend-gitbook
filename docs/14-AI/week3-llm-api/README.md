# Week 3: 调通 LLM API

> 目标：能熟练调用各种 LLM API，理解核心参数和用法

## 学习安排

| 天 | 文件 | 内容 | 时间 |
|---|------|------|------|
| Day 1 | `day1_ollama_local.py` | 用 Ollama 本地调用 LLM | 30min |
| Day 2 | `day2_deepseek_api.py` | 用 DeepSeek API 调用云端 LLM | 30min |
| Day 3 | `day3_openai_format.py` | OpenAI 兼容格式详解 | 30min |
| Day 4 | `day4_streaming.py` | 流式响应（SSE）实现打字机效果 | 30min |
| Day 5 | `day5_multi_turn.py` | 多轮对话：管理 messages 历史 | 30min |
| Day 6-7 | `day67_cli_chatbot.py` | 综合练习：命令行聊天机器人 | 60min |

## 环境准备

```bash
cd docs/14-AI/week3-llm-api
python -m venv .venv && source .venv/bin/activate

# 安装 OpenAI SDK（兼容 Ollama / DeepSeek / DashScope）
pip install openai python-dotenv

# 确保 Ollama 在运行
ollama serve
ollama pull qwen2.5:7b
```

## .env 配置

```bash
# .env
DEEPSEEK_API_KEY=sk-your-key
DASHSCOPE_API_KEY=sk-your-key
```
