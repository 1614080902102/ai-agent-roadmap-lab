import os
import json
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

def load_system_prompt(filepath):
  with open(filepath, "r", encoding="utf-8") as f:
    return f.read().strip()

def load_history(filepath):
  if not os.path.exists(filepath):
    return []
  with open(filepath, "r", encoding="utf-8") as f:
    return json.load(f)

def save_history(filepath, history):
  with open(filepath, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

def chat(system_prompt, history, user_input):
  messages = [{"role": "system", "content": system_prompt}] + history
  messages.append({"role": "user", "content": user_input})

  body = {
    "model": "Minimax-M2.5",
    "messages": messages
  }
  resp = requests.post(url, headers=headers, json=body)
  data = resp.json()

  if data.get("choices"):
    return data["choices"][0]["message"]["content"]
  return f"Error: {data.get('base_resp')}"

def main():
  system_prompt = load_system_prompt("system_prompt.txt")
  history = load_history("history.json")

  print("对话开始(exit 退出) \n")

  while True:
    user_input = input("你：").strip()
    if user_input.lower() == "exit":
      break
    if not user_input:
      continue

    reply = chat(system_prompt, history, user_input)
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": reply})
    save_history("history.json", history)

    print(f"AI: {reply} \n")

if __name__ == "__main__":
  main()
