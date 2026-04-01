from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from embedding_client import embeddings
from llm_client import llm
import re
from utils import get_logger
from config import chromadb_client

COLLECTION_NAME = "my_docs"
RETRIEVER_K = 3

def _get_retriever():
  db = Chroma(
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME,
    client=chromadb_client
  )
  return db.as_retriever(search_kwargs={"k": RETRIEVER_K})


def _get_source(metadata):
  if not metadata:
    return "未知来源"
  return metadata.get("source") or "未知来源"


def _build_sources(docs):
  return [
    {"content": doc.page_content, "file": _get_source(doc.metadata)}
    for doc in docs
  ]


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

def rag_query(question):
  retriever = _get_retriever()
  docs = retriever.invoke(question)
  context = _format_docs(docs)
  prompt = ChatPromptTemplate.from_template(
    """请仅根据提供的检索内容回答问题，不要补充检索内容中没有的信息。

      如果检索内容不足以支持答案，请明确回答“未找到”。

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
