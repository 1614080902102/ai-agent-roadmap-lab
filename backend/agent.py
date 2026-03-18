import os
from tool import read_file, extract_todo
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

load_dotenv() # 加载环境变量

api_key = os.getenv('MINIMAX_API_KEY') # 读取环境变量
group_id = os.getenv("MINIMAX_GROUP_ID")

base_url = f"https://api.minimax.chat/v1"

llm = ChatOpenAI(model='Minimax-M2.5', api_key=api_key, base_url=base_url)

# create_agent 是 langchain 1.x 的新 API，内置 ReAct 循环，不再需要单独拉 prompt
agent = create_agent(llm, tools=[read_file, extract_todo])

# invoke 接收的一个是一个字典，需要 {} 包起来
def main():
  result = agent.invoke({"messages": [{"role": "user", "content": "请读取 backend/sample_notes.txt 文件里的内容，并返回出来"}]})
  print(result)

if __name__ == "__main__":
  main()
