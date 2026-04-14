"""
批量抓取微信读书公众号文章列表
接口: GET https://weread.qq.com/web/mp/articles?bookId=...&offset=...
每页 20 条，循环翻页直到返回空
"""

import os
import requests
import json
import time

BOOK_ID = "MP_WXS_3277367297"

# Cookie 从浏览器复制，过期后需重新粘贴
COOKIE_STR = "wr_gid=258352847; wr_fp=1559540758; wr_skey=YFIc4ZCU; wr_vid=932443918; wr_ql=0; wr_rt=web%40091wGO_WlgXOVmELfDa_AL; wr_localvid=3093299083793f70e309459; wr_name=AI%E5%B2%A9"

HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "referer": "https://weread.qq.com/",
    "accept": "application/json, text/plain, */*",
    "cookie": COOKIE_STR,
}

OUTPUT_FILE = "articles.json"


def fetch_articles():
    all_articles = []
    seen_ids = set()
    offset = -1
    empty_streak = 0
    MAX_EMPTY = 3  # 连续空 3 次才真正停

    while True:
        url = f"https://weread.qq.com/web/mp/articles?bookId={BOOK_ID}&offset={offset}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
        except requests.RequestException as e:
            print(f"网络错误: {e}，offset={offset}")
            break

        if resp.status_code != 200:
            print(f"请求失败: {resp.status_code}，offset={offset}")
            print(resp.text[:300])
            break

        data = resp.json()
        reviews = data.get("reviews", [])

        if not reviews:
            empty_streak += 1
            print(f"offset={offset} 返回空（连续第 {empty_streak} 次）")
            if empty_streak >= MAX_EMPTY:
                print("连续空 3 次，抓取结束")
                break
            offset += 20
            time.sleep(1)
            continue

        empty_streak = 0

        for item in reviews:
            for sub in item.get("subReviews", []):
                mp_info = sub.get("review", {}).get("mpInfo", {})
                original_id = mp_info.get("originalId", "")
                title = mp_info.get("title", "")
                if original_id and original_id not in seen_ids:
                    seen_ids.add(original_id)
                    all_articles.append({
                        "title": title,
                        "url": f"https://mp.weixin.qq.com/s/{original_id}",
                        "original_id": original_id,
                        "time": mp_info.get("time", 0),
                        "read_num": mp_info.get("readNum", 0),
                        "like_num": mp_info.get("likeNum", 0),
                    })

        print(f"offset={offset}，本页 {len(reviews)} 条，累计 {len(all_articles)} 篇")
        offset += 20
        time.sleep(1)

    return all_articles


if __name__ == "__main__":
    # 加载已有数据，避免覆盖
    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = json.load(f)
        print(f"已有 {len(existing)} 篇，继续追加...")

    existing_ids = {a["original_id"] for a in existing}

    print(f"开始抓取公众号文章列表，bookId={BOOK_ID}")
    new_articles = fetch_articles()

    # 去重合并，只有新增数据时才写入，防止频率限制导致清空已有数据
    added = 0
    for a in new_articles:
        if a["original_id"] not in existing_ids:
            existing.append(a)
            existing_ids.add(a["original_id"])
            added += 1

    if added == 0 and new_articles == []:
        print(f"\n⚠️  未抓到任何数据（可能频率限制），已有 {len(existing)} 篇数据保留不动，未写入")
    else:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"\n完成！新增 {added} 篇，总计 {len(existing)} 篇，已保存到 {OUTPUT_FILE}")
