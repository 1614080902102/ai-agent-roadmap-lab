from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from embedding_client import embeddings
from llm_client import llm

COLLECTION_NAME = "my_docs"

def index_document(filepath):
  documents = TextLoader(filepath).load()
  splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(documents)
  Chroma.from_documents(splitter, embeddings, persist_directory='./chroma_db', collection_name=COLLECTION_NAME)

def rag_query(question):
  db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings, collection_name="my_docs")
  retriever = db.as_retriever(search_kwargs={"k": 3})
  docs = retriever.invoke(question)
  content = "\n".join([doc.page_content for doc in docs]) # 拼内容
  prompt = f"根据以下内容回答问题：\n\n{content}\n\n问题：{question}"
  answer = llm.invoke(prompt)
  res = {
    "answer": answer.content,
    "sources": [
      {"content": doc.page_content, "file": doc.metadata["source"]}
      for doc in docs
    ]
  }
  return res
