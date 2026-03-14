import os # 标准库，用来读取环境变量
import requests # 导入 HTTP 请求库，用来调 API
from dotenv import load_dotenv # 从 dotenv 库导入函数，用与加载 .env 文件

load_dotenv() # 执行加载，把 .env 里的变量注入到环境中

api_key = os.getenv("MINIMAX_API_KEY") # 从环境变量读取 apikey
group_id = os.getenv("MINIMAX_GROUP_ID")

# f 是 Python 的 f-string（格式化字符串），可以在字符串里直接嵌入变量（类似于前端的 ``）
url = f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}"

headers = {
  "Authorization": f"Bearer {api_key}",
  "Content-Type": "application/json"
}

def chat(messages): # 定义函数
  body = {
    "model": "MiniMax-M2.5",
    "messages": messages
  }
  # 发 HTTP 请求
  resp = requests.post(url, headers=headers, json=body)
  data = resp.json() # 把响应解析成 Python 字典
  if data.get("choices"):
    return data["choices"][0]["message"]["content"]
  else:
    return f"Error: {data.get('base_resp')}"

def main():
  history = []
  print("开始对话（输入 exit 退出）\n")

  while True: # 无限循环，等用户输入 exit 才停止
    user_input = input("你：").strip() # 读取用户输入，去掉首位空格
    if user_input.lower() == "exit": # 输入 exit（大小写） 则退出循环
        break
    if not user_input:
        continue

    history.append({
      "role": "user",
      "content": user_input
    }) # 用户消息加入历史
    reply = chat(history) # 调用 chat 函数获取 AI 回复
    history.append({
      "role": "assistant",
      "content": reply
    }) # AI 回复也加入历史

    print(f"AI: {reply} \n") # 打印 AI 回复

# 固定写法，只有运行这个文件才执行 main()
if __name__ == "__main__":
    main()
