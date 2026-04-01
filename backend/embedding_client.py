from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings


@lru_cache(maxsize=1)
def get_embeddings():
  return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


class LazyEmbeddings:
  """Delay model loading until Chroma actually needs embeddings."""

  def embed_documents(self, texts):
    return get_embeddings().embed_documents(texts)

  def embed_query(self, text):
    return get_embeddings().embed_query(text)

  def __getattr__(self, name):
    return getattr(get_embeddings(), name)


embeddings = LazyEmbeddings()
