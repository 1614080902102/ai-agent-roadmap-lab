import os
from langchain_openai import ChatOpenAI
from config import MINIMAX_API_KEY, MINIMAX_BASE_URL, MINIMAX_MODEL, MINIMAX_GROUP_ID

api_key = MINIMAX_API_KEY # 读取环境变量
group_id = MINIMAX_GROUP_ID
base_url = MINIMAX_BASE_URL

llm = ChatOpenAI(model='Minimax-M2.5', api_key=api_key, base_url=base_url)
