# Week 11: MCP Server 开发

> 目标：用 TypeScript 开发一个完整的 MCP (Model Context Protocol) Server，让 AI 助手能访问自定义工具和数据源

## 前置条件

- Node.js >= 18
- TypeScript 基础（前端同学最熟悉的语言，终于回到主场了）
- 对 AI 助手（Claude Code / Cursor）有基本了解

## 学习安排

| 天 | 文件/目录 | 内容 | 时间 |
|---|---------|------|------|
| Day 1 | `day1_mcp_concepts.md` | MCP 架构概念：协议、角色、传输方式 | 30min |
| Day 2 | `day2_project_setup/` | 项目搭建 + 最小可运行的 MCP Server | 45min |
| Day 3 | `day3_search_tool/` | 实现 search_docs 工具，搜索 Markdown 文件 | 45min |
| Day 4 | `day4_resource_provider/` | 实现 Resource Provider，暴露文档给 AI | 45min |
| Day 5 | `day5_testing.md` | 测试与调试：Claude Code 集成、Inspector 工具 | 30min |
| Day 6-7 | `day67_publish/` | 完整 MCP Server + 发布到 npm | 60min |

## 环境准备

```bash
# 1. 确保 Node.js 版本
node -v  # >= 18

# 2. 全局安装 TypeScript（如果没有）
npm install -g typescript

# 3. 进入练习目录后，每个子项目独立安装依赖
cd docs/14-AI/week11-mcp-server/day2_project_setup
npm install

# 4. 构建并运行
npm run build
npm start
```

## 核心依赖

```
@modelcontextprotocol/sdk   - MCP 官方 SDK
zod                         - 参数校验（TypeScript 生态标配）
typescript                  - 编译器
```

## 学习方法

```
前 5 分钟：回顾昨天的内容
中间 30 分钟：写代码 / 跑示例 / 调试
最后 5-10 分钟：用 Claude Code 实际测试你写的 MCP Server
```

## 关键概念速记

```
MCP = AI 助手与外部工具/数据之间的标准协议
Server = 你写的，提供工具和数据
Client = AI 助手（Claude Code、Cursor 等）
Transport = 通信方式（stdio 最常用）
```
