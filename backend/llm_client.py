import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv('MINIMAX_API_KEY') # 读取环境变量
group_id = os.getenv("MINIMAX_GROUP_ID")
base_url = f"https://api.minimax.chat/v1"

llm = ChatOpenAI(model='Minimax-M2.5', api_key=api_key, base_url=base_url)
