from langchain_core.tools import tool

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

if __name__ == "__main__":
  main()
