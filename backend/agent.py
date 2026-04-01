from tool import read_file, extract_todo, summarize_doc, extract_action_items, search_docs
from llm_client import llm
from langchain.agents import create_agent
from utils import clean_think

agent = create_agent(llm, tools=[read_file, extract_todo, summarize_doc, extract_action_items, search_docs])

# invoke 接收的一个是一个字典，需要 {} 包起来
def main():
  result = agent.invoke({"messages": [{"role": "user", "content": "请总结 sample_notes.txt 的要点 "}]})
  print(clean_think(result["messages"][-1].content))

if __name__ == "__main__":
  main()
