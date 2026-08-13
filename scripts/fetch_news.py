import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

NEWS_URL = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
ITEM_COUNT = 8


def main():
    try:
        req = urllib.request.Request(
            NEWS_URL,
            headers={"User-Agent": "Mozilla/5.0 (compatible; kanto-weather-bot/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            xml_bytes = res.read()
        root = ET.fromstring(xml_bytes)
        titles = [
            (item.findtext("title") or "").strip()
            for item in root.findall(".//item")
        ]
        titles = [t for t in titles if t][:ITEM_COUNT]
    except Exception as e:
        print(f"WARN: failed to fetch news: {e}")
        titles = []

    jst = timezone(timedelta(hours=9))
    output = {
        "generated_at": datetime.now(jst).isoformat(),
        "titles": titles,
    }

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
