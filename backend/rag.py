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

def query(question):
  db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings, collection_name=COLLECTION_NAME)
  return db.similarity_search(question, k=3)

def rag_query(question):
  docs = query(question)
  content = "\n".join([doc.page_content for doc in docs])
  prompt = f"根据以下内容回答问题：\n\n{content}\n\n问题：{question}"
  return llm.invoke(prompt)
