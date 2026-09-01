import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API_KEY = os.environ["ODPT_API_KEY"]

OPERATORS = [
    "odpt.Operator:JR-East",
    "odpt.Operator:TokyoMetro",
    "odpt.Operator:Toei",
    "odpt.Operator:Odakyu",
    "odpt.Operator:Keio",
    "odpt.Operator:Keikyu",
    "odpt.Operator:Keisei",
    "odpt.Operator:Seibu",
    "odpt.Operator:Tobu",
    "odpt.Operator:Tokyu",
    "odpt.Operator:TWR",
    "odpt.Operator:Yurikamome",
    "odpt.Operator:TokyoMonorail",
    "odpt.Operator:Sotetsu",
]

# ODPTの路線ID -> 表示用の日本語路線名(主要路線のみ。無いものはID末尾をそのまま使う)
RAILWAY_NAMES = {
    "JR-East.Yamanote": "山手線",
    "JR-East.ChuoRapid": "中央線快速",
    "JR-East.ChuoSobuLocal": "中央・総武線各駅停車",
    "JR-East.KeihinTohokuNegishi": "京浜東北線",
    "JR-East.Tokaido": "東海道線",
    "JR-East.Yokosuka": "横須賀線",
    "JR-East.Utsunomiya": "宇都宮線",
    "JR-East.Takasaki": "高崎線",
    "JR-East.Joban": "常磐線",
    "JR-East.Saikyo": "埼京線",
    "JR-East.ShonanShinjuku": "湘南新宿ライン",
    "JR-East.SobuRapid": "総武快速線",
    "JR-East.Keiyo": "京葉線",
    "TokyoMetro.Ginza": "銀座線",
    "TokyoMetro.Marunouchi": "丸ノ内線",
    "TokyoMetro.Hibiya": "日比谷線",
    "TokyoMetro.Tozai": "東西線",
    "TokyoMetro.Chiyoda": "千代田線",
    "TokyoMetro.Yurakucho": "有楽町線",
    "TokyoMetro.Hanzomon": "半蔵門線",
    "TokyoMetro.Namboku": "南北線",
    "TokyoMetro.Fukutoshin": "副都心線",
    "Toei.Asakusa": "都営浅草線",
    "Toei.Mita": "都営三田線",
    "Toei.Shinjuku": "都営新宿線",
    "Toei.Oedo": "都営大江戸線",
    "Odakyu.Odawara": "小田急小田原線",
    "Odakyu.Tama": "小田急多摩線",
    "Odakyu.Enoshima": "小田急江ノ島線",
    "Keio.Keio": "京王線",
    "Keio.Inokashira": "京王井の頭線",
    "Keio.Sagamihara": "京王相模原線",
    "Keio.Takao": "京王高尾線",
    "Keikyu.Main": "京急本線",
    "Keikyu.Airport": "京急空港線",
    "Keikyu.Daishi": "京急大師線",
    "Keikyu.Zushi": "京急逗子線",
    "Keisei.Main": "京成本線",
    "Keisei.Oshiage": "京成押上線",
    "Keisei.Kanamachi": "京成金町線",
    "Keisei.Higashi-Narita": "京成東成田線",
    "Keisei.Chihara": "京成千原線",
    "Keisei.NaritaSkyAccess": "成田スカイアクセス線",
    "Seibu.Ikebukuro": "西武池袋線",
    "Seibu.Shinjuku": "西武新宿線",
    "Seibu.Yurakucho": "西武有楽町線",
    "Seibu.Sayama": "西武狭山線",
    "Seibu.Toshima": "西武豊島線",
    "Seibu.Kokubunji": "西武国分寺線",
    "Seibu.Tamako": "西武多摩湖線",
    "Seibu.Tamagawa": "西武多摩川線",
    "Seibu.Seibuen": "西武西武園線",
    "Seibu.Chichibu": "西武秩父線",
    "Tobu.TobuSkytree": "東武スカイツリーライン",
    "Tobu.TobuUrbanPark": "東武アーバンパークライン",
    "Tobu.Tojo": "東武東上線",
    "Tobu.Nikko": "東武日光線",
    "Tobu.Kinugawa": "東武鬼怒川線",
    "Tobu.TobuDaishi": "東武大師線",
    "Tobu.Kameido": "東武亀戸線",
    "Tobu.TobuUtsunomiya": "東武宇都宮線",
    "Tokyu.ToyokoLine": "東急東横線",
    "Tokyu.DenEnToshiLine": "東急田園都市線",
    "Tokyu.MeguroLine": "東急目黒線",
    "Tokyu.OimachiLine": "東急大井町線",
    "Tokyu.IkegamiLine": "東急池上線",
    "Tokyu.TokyuTamagawaLine": "東急多摩川線",
    "Tokyu.SetagayaLine": "東急世田谷線",
    "Tokyu.KodomonokuniLine": "東急こどもの国線",
    "TWR.Rinkai": "りんかい線",
    "Yurikamome.Yurikamome": "ゆりかもめ",
    "TokyoMonorail.HanedaAirport": "東京モノレール羽田空港線",
    "Sotetsu.Main": "相鉄本線",
    "Sotetsu.Izumino": "相鉄いずみ野線",
}

# このキーワードを含む場合は「平常運転」とみなして表示しない
NORMAL_KEYWORDS = ["平常"]


def fetch_operator(operator_id):
    params = {
        "odpt:operator": operator_id,
        "acl:consumerKey": API_KEY,
    }
    url = "https://api.odpt.org/api/v4/odpt:TrainInformation?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; kanto-weather-bot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode("utf-8"))


def railway_display_name(railway_id):
    if not railway_id:
        return None
    key = railway_id.replace("odpt.Railway:", "")
    return RAILWAY_NAMES.get(key, key.split(".", 1)[-1])


def main():
    lines = []

    for operator_id in OPERATORS:
        try:
            entries = fetch_operator(operator_id)
        except Exception as e:
            print(f"WARN: failed to fetch {operator_id}: {e}", file=sys.stderr)
            continue

        for entry in entries:
            text = (entry.get("odpt:trainInformationText") or {}).get("ja", "").strip()
            if not text or any(kw in text for kw in NORMAL_KEYWORDS):
                continue

            lines.append({
                "operator": operator_id.split(":", 1)[-1],
                "railway": railway_display_name(entry.get("odpt:railway")),
                "text": text,
            })

    jst = timezone(timedelta(hours=9))
    output = {
        "generated_at": datetime.now(jst).isoformat(),
        "lines": lines,
    }

    with open("train.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
