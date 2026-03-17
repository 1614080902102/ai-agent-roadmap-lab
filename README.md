# AI Agent Demo - Week 1

## 项目简介

该项目是我个人从全栈偏前端开发转 AI Agent 开发的代码仓库，一些项目 demo，欢迎一起学习交流。

## 技术栈

Python / FastAPI / MiniMax API / Vue3 / Vite

## 本周完成

- 搭建 FastAPI 服务，实现 `GET /health`、`POST /echo`、`POST /summarize-mock` 接口
- 接入 MiniMax API，实现多轮对话（`POST /chat`），支持会话历史
- 实现 SSE 流式输出（`POST /chat/stream`），前端打字机效果
- Vue3 前端聊天页，支持 ReadableStream 读取流式响应
- 前后端联调完成，配置 CORS

## 快速启动

### 环境要求

- Python 3.12+
- Node.js 18+

### 后端

```bash
# 激活虚拟环境
source ~/venv/bin/activate

# 安装依赖（首次）
pip install fastapi uvicorn requests python-dotenv

# 配置环境变量
cp backend/.env.example backend/.env
# 填入 MINIMAX_API_KEY 和 MINIMAX_GROUP_ID

# 启动服务
cd backend
uvicorn main:app --reload
```

访问 `http://localhost:8000/docs` 查看接口文档。

### 前端

```bash
cd frontend

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

访问 `http://localhost:5173` 打开聊天页面。
