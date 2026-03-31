# Week 2: AI 开发常用库

> 目标：掌握 AI 开发中最常用的 Python 库，能搭建基本的 API 服务

## 学习安排

| 天 | 文件 | 内容 | 时间 |
|---|------|------|------|
| Day 1 | `day1_http_requests.py` | requests / httpx（对比 fetch/axios） | 30min |
| Day 2 | `day2_pydantic.py` | pydantic 数据校验和序列化（对比 zod） | 30min |
| Day 3 | `day3_dotenv_json.py` | python-dotenv 环境变量 + JSON 处理 | 30min |
| Day 4 | `day4_fastapi_basics.py` | FastAPI 基础（对比 express） | 30min |
| Day 5-7 | `day57_fastapi_rest_api.py` | 用 FastAPI 写一个简单的 REST API | 90min |

## 环境准备

```bash
cd docs/14-AI/week2-ai-libraries

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装本周需要的库
pip install requests httpx pydantic python-dotenv fastapi uvicorn
```

## 如何使用

```bash
# 运行某天的练习
python day1_http_requests.py

# Day 4-7 的 FastAPI 需要用 uvicorn 启动
uvicorn day4_fastapi_basics:app --reload
```

## 学习方法

```
前 5 分钟：回顾昨天的内容
中间 20 分钟：写代码 / 跑示例 / 调试
最后 5 分钟：记录遇到的问题和明天要做的事
```
