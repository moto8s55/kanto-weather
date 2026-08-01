import requests

# 都市名: (緯度, 経度)
CITIES = {
    "東京都": (35.6895, 139.6917),
    "神奈川県": (35.4478, 139.6425),
    "千葉県": (35.6047, 140.1233),
    "埼玉県": (35.8617, 139.6455),
}

# Open-Meteo の weathercode を日本語表記に変換
WEATHER_CODE_JA = {
    0: "快晴",
    1: "晴れ",
    2: "一部曇り",
    3: "曇り",
    45: "霧",
    48: "霧氷",
    51: "小雨(弱いにわか雨)",
    53: "小雨",
    55: "強い小雨",
    56: "着氷性の霧雨(弱い)",
    57: "着氷性の霧雨(強い)",
    61: "小雨",
    63: "雨",
    65: "大雨",
    66: "着氷性の雨(弱い)",
    67: "着氷性の雨(強い)",
    71: "小雪",
    73: "雪",
    75: "大雪",
    77: "霧雪",
    80: "にわか雨(弱い)",
    81: "にわか雨",
    82: "激しいにわか雨",
    85: "にわか雪(弱い)",
    86: "にわか雪(強い)",
    95: "雷雨",
    96: "雷雨(ひょうを伴う・弱い)",
    99: "雷雨(ひょうを伴う・強い)",
}


def weather_code_to_ja(code):
    return WEATHER_CODE_JA.get(code, f"不明({code})")


def fetch_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "precipitation_probability",
        "timezone": "Asia/Tokyo",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_current_precipitation_probability(data):
    # current_weather は15分刻み、hourly は1時間刻みのため、
    # 同じ日時の「時」までを切り詰めて一致させる
    current_hour = data["current_weather"]["time"][:13]  # "YYYY-MM-DDTHH"
    hourly_times = data["hourly"]["time"]
    hourly_probs = data["hourly"]["precipitation_probability"]

    for t, prob in zip(hourly_times, hourly_probs):
        if t[:13] == current_hour:
            return prob
    return None


def main():
    print("=== 関東地方 現在の天気 ===\n")

    for city_name, (lat, lon) in CITIES.items():
        try:
            data = fetch_weather(lat, lon)
            current = data["current_weather"]

            temperature = current["temperature"]
            windspeed = current["windspeed"]
            weather_ja = weather_code_to_ja(current["weathercode"])
            precip_prob = get_current_precipitation_probability(data)

            print(f"【{city_name}】")
            print(f"  天気     : {weather_ja}")
            print(f"  気温     : {temperature}℃")
            print(f"  降水確率 : {precip_prob if precip_prob is not None else '不明'}%")
            print(f"  風速     : {windspeed} km/h")
            print(f"  観測時刻 : {current['time']}")
            print()

        except requests.exceptions.RequestException as e:
            print(f"【{city_name}】データ取得エラー: {e}\n")
        except (KeyError, ValueError) as e:
            print(f"【{city_name}】データ解析エラー: {e}\n")


if __name__ == "__main__":
    main()
