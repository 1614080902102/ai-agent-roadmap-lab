import re
import logging

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_logger(name):
  return logging.getLogger(name)

def clean_think(answer):
  return re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
