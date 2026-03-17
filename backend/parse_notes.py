def main():
  notes = load_notes('sample_notes.txt')
  print(notes)

def load_notes(filepath):
  todos = []
  with open(filepath, 'r', encoding="utf-8") as f:
    lines = f.read().splitlines()
    for line in lines:
      line = line.strip() # 去除多余空格
      if line.startswith("- [ ]") or line.startswith("TODO"):
        todos.append(line)
    return todos

if __name__ == "__main__":
  main()
