from rag import index_document, rag_query
import shutil

shutil.rmtree("chroma_db", ignore_errors=True)


def test_rag():
  # 索引文档
  index_document("sample_notes.txt")

  # 测试查询
  question = "今日代办还有哪些没做完？"
  answer = rag_query(question)
  print(answer)

if __name__ == "__main__":
  test_rag()
