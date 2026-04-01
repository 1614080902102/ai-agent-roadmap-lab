import os
from dotenv import load_dotenv
from chromadb import HttpClient

load_dotenv()

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MINIMAX_MODEL = "Minimax-M2.5"
MINIMAX_HEADERS = {
    "Authorization": f"Bearer {os.getenv('MINIMAX_API_KEY')}",
    "Content-Type": "application/json",
}

host = os.getenv("CHROMADB_HOST", "localhost")
port = int(os.getenv("CHROMADB_PORT", 8000))

chromadb_client = HttpClient(host=host, port=port)
