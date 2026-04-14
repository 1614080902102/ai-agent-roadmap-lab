from langchain_community.document_loaders import TextLoader, WebBaseLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from embedding_client import embeddings
from llm_client import llm
import re
import requests
import urllib3
from bs4 import BeautifulSoup
from utils import get_logger
from config import chromadb_client

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COLLECTION_NAME = "my_docs"
WECHAT_COLLECTION_NAME = "wechat_articles"
RETRIEVER_K = 6

def _get_retriever(collection_name=COLLECTION_NAME):
  db = Chroma(
    embedding_function=embeddings,
    collection_name=collection_name,
    client=chromadb_client
  )
  return db.as_retriever(search_kwargs={"k": RETRIEVER_K})


def _get_source(metadata):
  if not metadata:
    return "未知来源"
  return metadata.get("source") or "未知来源"


def _build_sources(docs):
  sources = []
  for doc in docs:
    meta = doc.metadata or {}
    source = {
      "content": doc.page_content,
      "file": meta.get("source") or meta.get("url") or "未知来源",
      "title": meta.get("title") or "",
      "url": meta.get("url") or "",
    }
    sources.append(source)
  return sources


def _format_docs(docs):
  if not docs:
    return "未找到相关检索内容。"
  return "\n\n".join(
    [f"【来源：{_get_source(doc.metadata)}】\n{doc.page_content}" for doc in docs]
  )

def index_document(filepath):
  documents = TextLoader(filepath).load()
  splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(documents)
  Chroma.from_documents(splitter, embeddings, client=chromadb_client, collection_name=COLLECTION_NAME)


def _fetch_wechat_article(url: str):
  """使用微信移动端 UA 抓取公众号文章，返回 (title, content)"""
  headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 MicroMessenger/8.0.38(0x1800262c) NetType/WIFI Language/zh_CN",
  }
  resp = requests.get(url, headers=headers, verify=False, timeout=30)
  resp.raise_for_status()
  soup = BeautifulSoup(resp.text, "html.parser")

  title_tag = soup.find("h1", class_="rich_media_title") or soup.find("h2", class_="rich_media_title")
  title = title_tag.get_text(strip=True) if title_tag else ""

  content_tag = soup.find(id="js_content")
  content = content_tag.get_text(separator="\n", strip=True) if content_tag else ""

  return title, content


def index_url(url: str):
  if "mp.weixin.qq.com" in url:
    title, content = _fetch_wechat_article(url)
    documents = [Document(page_content=content, metadata={"source": url, "url": url, "title": title})]
  else:
    loader = WebBaseLoader(url, requests_kwargs={"verify": False})
    documents = loader.load()
    for doc in documents:
      doc.metadata.setdefault("source", url)
      doc.metadata.setdefault("url", url)
      if not doc.metadata.get("title"):
        doc.metadata["title"] = ""

  splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(documents)
  Chroma.from_documents(splitter, embeddings, client=chromadb_client, collection_name=WECHAT_COLLECTION_NAME)
  return {"message": "索引成功", "url": url, "title": documents[0].metadata.get("title", "") if documents else ""}


def rag_query(question, collection_name=COLLECTION_NAME):
  retriever = _get_retriever(collection_name)
  docs = retriever.invoke(question)
  context = _format_docs(docs)
  prompt = ChatPromptTemplate.from_template(
    """请仅根据提供的检索内容回答问题，不要补充检索内容中没有的信息。

      如果检索内容不足以支持答案，请明确回答"未找到"。

      回答请按以下结构组织：
      1. 结论
      2. 依据
      3. 来源

      默认使用中文回答，必要时保留英文专有名词。

      检索内容：
      {context}

      问题：
      {question}"""
        )
  parser = StrOutputParser()
  chain = prompt | llm | parser
  answer = chain.invoke({"context": context, "question": question})
  # print(f"回答长度: {len(answer)}")

  logger = get_logger(__name__)
  logger.info(f"回答长度: {len(answer)}")

  return {
    "answer": re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip(),
    "sources": _build_sources(docs),
  }


def rag_query_wechat(question):
  return rag_query(question, collection_name=WECHAT_COLLECTION_NAME)

@tool
def search_docs(question):
  """
    根据用户问题，从已上传的文档中检索语义最相关的片段
    返回：对应匹配的文档内容
  """
  retriever = _get_retriever()
  docs = retriever.invoke(question)
  return _format_docs(docs)



# RunnableLambda 接收的是函数！！！

  # answer = llm.invoke(prompt)
  # res = {
  #   "answer": answer.content,
  #   "sources": [
  #     {"content": doc.page_content, "file": doc.metadata["source"]}
  #     for doc in docs
  #   ]
  # }


# question = "LangChain 是什么呢？"
# prompt = ChatPromptTemplate.from_template(
#     "根据以下内容回答问题：\n{context}\n\n问题：{question}"
# )
# llm = ChatOpenAI(model="GPT-5.4")
# parser = StrOutputParser()

# chain = {
#     "context": retriever,  # retriever 检索到的
#     "question": RunnablePassthrough(),           # 原样传递的
#     "language": lambda _: "中文"
# } | llm | parser

# result = chain.invoke(question)

# def clean_docs(docs):
#     # 自定义处理逻辑
#     return "\n".join([doc.page_content for doc in docs])

# clean_step = RunnableLambda(clean_docs)

# question = "LangChain 是什么？"
# prompt = ChatPromptTemplate.from_template(
#   "根据以下内容回答问题：\n{context}\n\n问题：{question}"
# )
# llm = ChatOpenAI(model="GPT-5.4")
# parser = StrOutputParser()
# chain = {
#     "context": retriever | clean_step,  # retriever 检索到的
#     "question": RunnablePassthrough(),           # 原样传递的
#     "language": lambda _: "中文"
# }
# | llm | parser
# result = chain.invoke(question)


# # 方式 A：先定义函数
# def truncate(text):
#     if len(text) > 100:
#         return f"{text[:100]}…"
#     return text

# chain = prompt | llm | parser | truncate

# # 方式 B：用 lambda（但 lambda 只能写单行表达式）
# chain = prompt | llm | parser | (lambda text: f"{text[:100]}…" if len(text) > 100 else text)

# def rag_test(question):
#   db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings, collection_name="my_docs")
#   retriever = db.as_retriever(search_kwargs={"k": 3})
#   prompt = ChatPromptTemplate.from_template(
#     "根据以下内容回答问题：\n\n{context}\n\n问题：{question}"
#   )
#   def format_docs(docs):
#     return "\n".join([doc.page_content for doc in docs])
#   chain = {
#     "context": retriever | format_docs,
#     "question": RunnablePassthrough()
#   } | prompt | llm | parser
#   return chain.invoke(question)
