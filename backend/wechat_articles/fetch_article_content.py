"""
批量抓取公众号文章正文
成功的存入 contents/，失败的记录到 failed_articles.json
"""

import json
import time
import os
import warnings
import requests
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")

INPUT_FILE = "articles.json"
CONTENTS_DIR = "contents"
FAILED_FILE = "failed_articles.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 MicroMessenger/8.0.38(0x1800262c) NetType/WIFI Language/zh_CN"
}


def fetch_content(url: str):
    resp = requests.get(url, headers=HEADERS, verify=False, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    title_tag = soup.find("h1", class_="rich_media_title") or soup.find("h2", class_="rich_media_title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    content_tag = soup.find(id="js_content")
    content = content_tag.get_text(separator="\n", strip=True) if content_tag else ""
    return title, content


def main():
    os.makedirs(CONTENTS_DIR, exist_ok=True)

    with open(INPUT_FILE, encoding="utf-8") as f:
        articles = json.load(f)

    failed = []
    success = 0

    for i, article in enumerate(articles):
        url = article["url"]
        original_id = article["original_id"]
        save_path = os.path.join(CONTENTS_DIR, f"{original_id}.json")

        # 已抓过的跳过
        if os.path.exists(save_path):
            success += 1
            continue

        try:
            title, content = fetch_content(url)

            if not content:
                raise ValueError("正文为空（可能是 JS 渲染或已删除）")

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump({
                    "title": title or article["title"],
                    "url": url,
                    "original_id": original_id,
                    "content": content,
                }, f, ensure_ascii=False, indent=2)

            success += 1
            print(f"[{i+1}/{len(articles)}] ✓ {article['title'][:40]} ({len(content)} 字)")

        except Exception as e:
            reason = str(e)
            failed.append({**article, "fail_reason": reason})
            print(f"[{i+1}/{len(articles)}] ✗ {article['title'][:40]} | {reason}")

        time.sleep(0.5)

    # 保存失败列表
    with open(FAILED_FILE, "w", encoding="utf-8") as f:
        json.dump(failed, f, ensure_ascii=False, indent=2)

    print(f"\n完成！成功 {success} 篇，失败 {len(failed)} 篇")
    print(f"失败列表已保存到 {FAILED_FILE}")


if __name__ == "__main__":
    main()
