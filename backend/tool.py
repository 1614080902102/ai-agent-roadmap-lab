from langchain_core.tools import tool
from llm_client import llm
from langchain_chroma import Chroma
from embedding_client import embeddings
from utils import clean_think
from config import chromadb_client

def main():
  print(extract_todo.name)
  print(extract_todo.description)
  print(read_file.name)
  print(read_file.description)
  # 变成 LangChain 的 StructuredTool 对象之后，不能像函数一样调用
  # notes1 = extract_todo('sample_notes.txt')
  # notes2 = read_file('sample_notes.txt')

@tool
def extract_todo(filepath):
  """
    读取指定文件，提取待办事项。
    提取规则：其中以 '- [ ]' 或 'TODO' 开头的待办事项。
    返回：待办事项列表
  """
  todos = []
  with open(filepath, 'r', encoding="utf-8") as f:
    lines = f.read().splitlines()
    for line in lines:
      line = line.strip() # 去除多余空格
      if line.startswith("- [ ]") or line.startswith("TODO"):
        todos.append(line)
  return todos


@tool
def read_file(filepath):
  """
    读取指定文件，返回文件内容。
    返回：完整文本内容
  """
  with open(filepath, 'r', encoding="utf-8") as f:
    return f.read()

@tool
def summarize_doc(filepath):
  """
    读取指定文件，总结要点
    返回：总结的要点内容
  """
  with open(filepath, 'r', encoding="utf-8") as f:
    content = f.read()
    prompt = f"""请面向项目负责人总结以下文档的要点。

请优先按以下维度组织输出：
1. 任务
2. 要求
3. 节点
4. 交付

如果原文没有明确提到某一项，请写“未提及”，不要补充原文中没有的信息。

文档内容：
{content}"""
  result = llm.invoke(prompt)
  return clean_think(result.content)

@tool
def extract_action_items(filepath):
  """
    读取指定文件，提取行动项
    返回：提取的行动项内容
  """
  with open(filepath, 'r', encoding="utf-8") as f:
    content = f.read()
    prompt = f"""请从以下文档中提取出需要执行的行动项。

输出要求：
- 每个行动项单独一行
- 只提取明确需要执行、跟进、完成或推进的事项
- 不要把普通背景信息、描述性内容或结论当作行动项
- 如果没有明确行动项，请直接输出“无行动项”
- 不要补充原文中没有的信息

文档内容：
{content}"""
  result = llm.invoke(prompt)
  return clean_think(result.content)

@tool
def search_docs(question):
  """
    根据用户问题，从已上传的文档中检索语义最相关的片段
    返回：对应匹配的文档内容
  """
  db = Chroma(
    collection_name="my_docs",
    embedding_function=embeddings,
    client=chromadb_client
  )
  retriever = db.as_retriever(search_kwargs={"k": 3})
  docs = retriever.invoke(question)
  def format_docs(docs):
    if not docs:
      return "未找到相关检索内容。"
    return "\n\n".join(
      [f"【来源：{doc.metadata.get('source') or '未知来源'}】\n{doc.page_content}" for doc in docs]
    )
  return format_docs(docs)


if __name__ == "__main__":
  main()
