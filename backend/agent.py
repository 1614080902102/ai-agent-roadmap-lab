from tool import read_file, extract_todo, summarize_doc, extract_action_items
from llm_client import llm
from langchain.agents import create_agent

agent = create_agent(llm, tools=[read_file, extract_todo, summarize_doc, extract_action_items])

# invoke 接收的一个是一个字典，需要 {} 包起来
def main():
  result = agent.invoke({"messages": [{"role": "user", "content": "请从 sample_notes.txt 中提取行动项"}]})
  print(result["messages"][-1].content)

if __name__ == "__main__":
  main()
