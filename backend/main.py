import os
import json
import requests
# from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi import UploadFile # 导入文件上传
from rag import index_document, rag_query
from utils import get_logger
from config import MINIMAX_API_KEY, MINIMAX_GROUP_ID, MINIMAX_BASE_URL, MINIMAX_HEADERS

logger = get_logger(__name__)

# 加载 .env 文件（路径相对于本文件所在目录）
# load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# ── FastAPI 实例 ──────────────────────────────────────────────────────────────
# 类比：const app = express()
app = FastAPI(title="AI Agent Demo", version="0.1.0")

# 允许前端开发服务器（localhost:5173）跨域调用后端
# 类比：Express 里的 cors() 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic 数据模型 ─────────────────────────────────────────────────────────
# 类比前端的 TypeScript interface，FastAPI 用它自动校验请求体
# 如果请求体缺字段或类型不对，会自动返回 422 错误，不用手写校验

# 类似前端的 ts，类型校验
class EchoRequest(BaseModel):
    message: str  # 必填，类型为字符串

class SummarizeRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class RagRequest(BaseModel):
    question: str


sessions = {}  # 用于存储会话历史，key 是 session_id，value 是消息列表

# ── Day 3 接口 ────────────────────────────────────────────────────────────────

# GET /health —— 健康检查，部署后用来确认服务是否正常
# 类比：app.get('/health', (req, res) => res.json({ status: 'ok' }))
@app.get("/health")
def health():
    return {"status": "ok"}


# POST /echo —— 原样返回用户输入，用来验证请求体解析是否正常
@app.post("/echo")
def echo(body: EchoRequest):
    # body.message 就是请求体里的 message 字段，Pydantic 已经帮你解析好了
    return {"echo": body.message}


# POST /summarize-mock —— 假的总结接口，返回硬编码结果
# 用途：让前端先联调格式，不依赖真实 AI 调用
@app.post("/summarize-mock")
def summarize_mock(body: SummarizeRequest):
    word_count = len(body.text)
    return {
        "summary": f"【Mock】这段文字共 {word_count} 个字符，内容已收到。",
        "original_length": word_count,
    }


# ── Day 4 接口 ────────────────────────────────────────────────────────────────

# POST /chat —— 真实调用 MiniMax，支持多轮对话
# 前端传 message（本次问题）+ history（历史消息列表）
# 后端返回 reply（AI 回复）+ updated_history（加入本轮后的完整历史）
@app.post("/chat")
def chat(body: ChatRequest):
    if not MINIMAX_API_KEY or not MINIMAX_GROUP_ID:
        logger.error("API key 未配置，检查 .env 文件")
        raise HTTPException(status_code=500, detail="API key 未配置，检查 .env 文件")

    # 拼装 messages：system + 历史 + 本次用户输入
    messages = [
        {"role": "system", "content": "你是一个简洁、友好、科学、严谨的 AI 助手。"}
    ]
    messages = messages + sessions.get(body.session_id, [])  # 获取历史消息，如果没有就用空列表
    messages.append({"role": "user", "content": body.message})

    try:
        resp = requests.post(
            MINIMAX_BASE_URL,
            headers=MINIMAX_HEADERS,
            json={"model": "MiniMax-M2.5", "messages": messages},
            timeout=30,  # 超过 30 秒视为超时
        )
        logger.info(f"MiniMax 响应状态码: {resp.status_code}")
        resp.raise_for_status()  # 4xx / 5xx 时抛异常

    except requests.Timeout:
        logger.error("模型响应超时，请重试")
        raise HTTPException(status_code=504, detail="模型响应超时，请重试")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"调用 MiniMax 失败：{e}")

    data = resp.json()

    if not data.get("choices"):
        logger.error(f"MiniMax 返回异常：{data.get('base_resp')}")
        raise HTTPException(status_code=502, detail=f"MiniMax 返回异常：{data.get('base_resp')}")

    reply = data["choices"][0]["message"]["content"]

    # 更新历史，返回给前端，让前端自己维护 history 状态
    updated_history = sessions.get(body.session_id, []) + [
        {"role": "user", "content": body.message},
        {"role": "assistant", "content": reply},
    ]
    sessions[body.session_id] = updated_history

    return {"reply": reply}


# ── Day 6 接口 ────────────────────────────────────────────────────────────────

# POST /chat/stream —— 流式返回，SSE 格式
# SSE（Server-Sent Events）：服务器主动推送数据给前端，一行一行发
# 格式固定：每条消息是 "data: 内容\n\n"，前端用 ReadableStream 逐块读取
@app.post("/chat/stream")
def chat_stream(body: ChatRequest):
    if not MINIMAX_API_KEY or not MINIMAX_GROUP_ID:
        raise HTTPException(status_code=500, detail="API key 未配置，检查 .env 文件")

    messages = [
        {"role": "system", "content": "你是一个简洁、友好、科学、严谨的 AI 助手。"}
    ]
    messages += sessions.get(body.session_id, [])
    messages.append({"role": "user", "content": body.message})

    def generate():
        # stream=True 告诉 requests 不要一次性读完，而是边收边给我们
        with requests.post(
            MINIMAX_BASE_URL,
            headers=MINIMAX_HEADERS,
            json={"model": "MiniMax-M2.5", "messages": messages, "stream": True},
            stream=True,
            timeout=60,
        ) as resp:
            full_reply = ""

            for line in resp.iter_lines():
                # 跳过空行
                if not line:
                    continue

                # decode 成字符串
                text = line.decode("utf-8")

                # SSE 行格式是 "data: {...}"，去掉前缀拿到 JSON
                if not text.startswith("data:"):
                    continue

                # strip() 去掉空格，只要 JSON 字符串
                data_str = text[len("data:"):].strip()

                # 流结束标志
                if data_str == "[DONE]":
                    break

                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                # MiniMax 流式响应里，每个 chunk 的增量内容在 delta.content
                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if delta:
                    full_reply += delta
                    # 把这段增量发给前端，格式：data: 文字\n\n
                    yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"

            # 流结束后，更新服务端 sessions，并通知前端流已结束
            sessions[body.session_id] = sessions.get(body.session_id, []) + [
                {"role": "user", "content": body.message},
                {"role": "assistant", "content": full_reply},
            ]
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    # StreamingResponse 类比：res.setHeader('Content-Type', 'text/event-stream') + res.write()
    return StreamingResponse(generate(), media_type="text/event-stream")


# POST /upload
@app.post("/upload")
def upload(file: UploadFile):
    try:
        # 1. 确保 uploads 目录存在
        os.makedirs("./uploads", exist_ok=True)

        # 2. 拼保存路径
        save_path = f"./uploads/{file.filename}"

        # 3. 读取上传内容，写入磁盘
        with open(save_path, "wb") as f:
            f.write(file.read())  # 这里填什么？提示：从 file 里读内容

        index_document(save_path)

        return {
            "message": "上传成功",
            "filename": file.filename
        }

    except Exception as e:
        logger.error(f"上传失败：{e}")
        raise HTTPException(status_code=500, detail=f"上传失败：{e}")


# POST /rag
@app.post("/rag")
def rag(body: RagRequest):
    try:
        result = rag_query(body.question)
        return result
    except Exception as e:
        logger.error(f"RAG 查询失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
