import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MINIMAX_API_KEY")
group_id = os.getenv("MINIMAX_GROUP_ID")

url = f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}"

headers = {
  "Authorization": f"Bearer {api_key}",
  "Content-Type": "application/json"
}

body = {
  "model": "MiniMax-M2.5",
  "messages": [{
    "role": "user",
    "content": "你好，请用一句话介绍你自己"
  }]
}

resp = requests.post(url, headers=headers, json=body)
data = resp.json()
print(data)  # 先看完整响应
if data.get("choices"):
    print(data["choices"][0]["message"]["content"])
else:
    print("Error:", data.get("base_resp"))
