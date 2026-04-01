from tool import summarize_doc, extract_action_items

def main():
  summarized = summarize_doc.invoke("sample_notes.txt")
  extracted = extract_action_items.invoke("sample_notes.txt")
  print(summarized, extracted)

if __name__ == "__main__":
  main()


def logger(prompt):
    logger.info(prompt)
    return prompt
RunnableLambda(logger)
