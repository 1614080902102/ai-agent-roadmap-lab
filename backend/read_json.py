import json # 导入内置的 json 模块，将 dict/list 与 JSON 字符串/文件互相转换

def load_json(filepath):
  # open 是打开文件，r 是只读模式
  # with ... as f 自动管理文件开关，类似于前端 try/finally，用完自动关闭
  with open(filepath, "r", encoding="utf-8") as f:
    return json.load(f) # 将文件解析城 Python dict/list（JSON.parse)

def print_messages(messages):
  # 遍历列表，每次取一个元素，类似于 JS 的 for...of
  for msg in messages:
    print(f"{msg['role']}: {msg['content']}")

def add_message(message, role, content):
  # append 在列表末尾追加一个元素，等同于 JS 的 array.push
  message.append({"role": role, "content": content})
  return message

# __name__ 是 Python 自动设置的内部变量，不需要定义，Python 运行时会自动赋值
# 直接运行，Python 将 __name__ 设置为字符串 "__main__"
# 被其他文件 import 时：Python 将 __name__ 设置为文件名（如"read_json")
# __main__ 不是函数名，是一个特殊的字符串，用来判断"当前文件是不是入口文件"
if __name__ == "__main__":
  history = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮你？"}
  ]

  print("=== 当前对话 ===")
  print_messages(history)

  history = add_message(history, "user", "今天天气怎么样？")
  print("\n=== 添加后 ===")
  print_messages(history)

  # w: 写入模式；json.dump(history, f, ...)   把 Python 对象写入文件
  # ensure_ascii=False：允许中文直接写入，不转成 \uXXXX
  # indent=2 格式化缩进，让 JSON 文件可读
  with open("history.json", "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
  print("\n已保存到 history.json")

  # 调用上面定义的函数，重新从文件读回来，验证写入成功
  loaded = load_json("history.json")
  print(f"\n读取到 {len(loaded)} 条消息")
