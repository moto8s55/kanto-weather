import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API_URL = "https://api.notion.com/v1/blocks/{}/children"
NOTION_VERSION = "2022-06-28"


def fetch_blocks(block_id, token):
    blocks = []
    cursor = None
    while True:
        url = API_URL.format(block_id) + "?page_size=100"
        if cursor:
            url += "&start_cursor=" + urllib.parse.quote(cursor)
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION},
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            return blocks
        cursor = data["next_cursor"]


def unchecked_todo_texts(blocks):
    """チェックの入っていないToDoブロック(ページ直下)の文字だけを順番に返す。"""
    items = []
    for block in blocks:
        if block.get("type") != "to_do":
            continue
        todo = block["to_do"]
        if todo.get("checked"):
            continue
        text = "".join(t.get("plain_text", "") for t in todo.get("rich_text", [])).strip()
        if text:
            items.append(text)
    return items


def main():
    # 貼り付け時に混ざりやすい前後の空白・改行や「Bearer 」を取り除く
    token = os.environ["NOTION_TOKEN"].strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    page_id = os.environ["NOTION_PAGE_ID"].strip()

    try:
        items = unchecked_todo_texts(fetch_blocks(page_id, token))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        # 失敗時は前回のtodo.jsonを残す(一時的なエラーでリストが空になるのを防ぐ)
        print(f"WARN: failed to fetch Notion page: HTTP {e.code} body={body!r}", file=sys.stderr)
        if e.code == 401:
            # 原因切り分け用(長さと先頭4文字のみ。Notionのトークンは通常 ntn_ か secret_ で始まる)
            print(f"INFO: token length={len(token)} prefix={token[:4]!r}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"WARN: failed to fetch Notion page: {e}", file=sys.stderr)
        sys.exit(1)

    jst = timezone(timedelta(hours=9))
    output = {"generated_at": datetime.now(jst).isoformat(), "items": items}
    with open("todo.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
