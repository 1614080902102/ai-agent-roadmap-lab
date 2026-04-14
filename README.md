# AI Agent 知识助手

一个基于 FastAPI + Vue3 + LangChain 的 AI 知识助手，支持多轮对话、RAG 检索问答、Tool Calling、Agent 自动路由，以及公众号文章知识库构建。

## 技术架构

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Vue3 前端     │◄────►│  FastAPI 后端    │◄────►│  MiniMax API    │
│  (Vite + TS)    │      │  (Python 3.12)   │      │   (大模型)      │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                │
                                ▼
                         ┌──────────────────┐
                         │   LangChain      │
                         │  Agent / RAG     │
                         └──────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
        ┌───────────────┐              ┌───────────────┐
        │   Chroma DB   │              │   Tool Set    │
        │  (向量数据库)  │              │  (文件/摘要)  │
        └───────────────┘              └───────────────┘
```

## 核心能力

- **多轮对话**：支持 session_id 级别的上下文历史，流式 SSE 输出
- **RAG 检索问答**：文档上传 → 文本切块 → Embedding → Chroma 存储 → 检索生成，回答附带引用来源
- **Tool Calling**：`read_file`、`extract_todo`、`summarize_doc`、`extract_action_items` 等工具
- **Agent 自动路由**：基于 ReAct 模式，自动判断用户意图并选择调用工具或走 RAG
- **公众号知识库**：输入公众号文章链接，自动抓取、索引、问答，引用支持点击跳转原文
- **工程化**：日志记录、异常处理、超时重试、配置管理、Docker 容器化部署

## 技术栈

- **后端**：Python 3.12 / FastAPI / Pydantic / LangChain / ChromaDB
- **前端**：Vue 3 / TypeScript / Vite
- **模型**：MiniMax (MiniMax-M2.5) via OpenAI-compatible API
- **向量嵌入**：HuggingFace `all-MiniLM-L6-v2`
- **部署**：Docker + docker-compose

## 快速启动

### 1. 克隆仓库

```bash
git clone <repo-url>
cd ai-agent-roadmap-lab
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入：
# MINIMAX_API_KEY=你的key
# MINIMAX_GROUP_ID=你的group_id
```

### 3. Docker 一键启动

```bash
docker-compose up --build
```

启动后访问：
- 前端页面：http://localhost:5173
- 后端接口文档：http://localhost:8000/docs

### 4. 本地开发启动

**后端**

```bash
cd backend
source ../.venv/bin/activate
uvicorn main:app --reload
```

**前端**

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
ai-agent-roadmap-lab/
├── backend/
│   ├── main.py           # FastAPI 入口（聊天 / RAG / 公众号索引 / 上传）
│   ├── rag.py            # RAG 核心链路 + 公众号知识库
│   ├── agent.py          # LangChain Agent 初始化
│   ├── tool.py           # Tool Calling 工具定义
│   ├── llm_client.py     # MiniMax LLM 封装
│   ├── embedding_client.py  # Embedding 封装（懒加载）
│   ├── config.py         # 配置与环境变量
│   ├── utils.py          # 日志、通用工具
│   ├── Dockerfile
│   └── uploads/          # 上传文件存储目录
├── frontend/
│   ├── src/App.vue       # 主页面（Chat / RAG / 公众号 三模式）
│   ├── Dockerfile
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## 主要接口

| 接口 | 说明 |
|------|------|
| `POST /chat` | 多轮对话 |
| `POST /chat/stream` | 流式多轮对话（SSE） |
| `POST /rag` | 基于上传文档的 RAG 问答 |
| `POST /rag/wechat` | 基于公众号文章的 RAG 问答 |
| `POST /index` | 抓取公众号文章并建立索引 |
| `POST /upload` | 上传本地文档 |
| `GET /health` | 健康检查 |

## 学习路径

本项目是个人从全栈前端向 AI Agent 开发转型的实战项目，覆盖以下核心技能：

- FastAPI 服务搭建与工程化
- LLM API 调用与流式输出
- Prompt Engineering 与 System Prompt 设计
- LangChain 工具注册与 Agent 编排（ReAct）
- RAG 完整链路：Loader → Splitter → Embedding → Vector Store → Retrieval → Generation
- Docker 容器化与多服务编排

---

欢迎交流学习，有问题随时提 Issue。
