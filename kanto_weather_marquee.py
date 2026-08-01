import threading
import time
import tkinter as tk

from kanto_weather import (
    CITIES,
    fetch_weather,
    get_current_precipitation_probability,
    weather_code_to_ja,
)

CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 150
FONT = ("Menlo", 40, "bold")
TEXT_COLOR = "#ffcc00"
BG_COLOR = "black"

SCROLL_SPEED = 4          # 1フレームで移動するピクセル数
FRAME_INTERVAL_MS = 30    # フレーム更新間隔(ミリ秒)
REFRESH_INTERVAL_SEC = 5 * 60  # 天気データの再取得間隔(秒)

SEPARATOR = "　　★　　"


def build_display_text():
    parts = []
    for city_name, (lat, lon) in CITIES.items():
        try:
            data = fetch_weather(lat, lon)
            current = data["current_weather"]
            weather_ja = weather_code_to_ja(current["weathercode"])
            precip_prob = get_current_precipitation_probability(data)
            precip_text = f"{precip_prob}%" if precip_prob is not None else "不明"
            parts.append(
                f"{city_name}　{weather_ja}　気温{current['temperature']}℃　"
                f"降水確率{precip_text}"
            )
        except Exception:
            parts.append(f"{city_name}　データ取得エラー")
    return SEPARATOR.join(parts) + SEPARATOR


class WeatherMarquee:
    def __init__(self, root):
        self.root = root
        root.title("関東地方 天気情報表示")
        root.configure(bg=BG_COLOR)

        self.canvas = tk.Canvas(
            root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
            bg=BG_COLOR, highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.text_id = self.canvas.create_text(
            0, CANVAS_HEIGHT // 2, text="天気情報を取得中...", fill=TEXT_COLOR,
            font=FONT, anchor="w",
        )
        self.canvas.update_idletasks()

        self.x = self.canvas.winfo_width()
        self.canvas.coords(self.text_id, self.x, CANVAS_HEIGHT // 2)

        self.pending_text = None
        self.lock = threading.Lock()

        threading.Thread(target=self.refresh_loop, daemon=True).start()
        self.root.after(FRAME_INTERVAL_MS, self.scroll)

    def scroll(self):
        with self.lock:
            if self.pending_text is not None:
                self.canvas.itemconfig(self.text_id, text=self.pending_text)
                self.pending_text = None

        self.x -= SCROLL_SPEED
        bbox = self.canvas.bbox(self.text_id)
        text_width = (bbox[2] - bbox[0]) if bbox else 0
        canvas_width = self.canvas.winfo_width()

        if self.x + text_width < 0:
            self.x = canvas_width

        self.canvas.coords(self.text_id, self.x, CANVAS_HEIGHT // 2)
        self.root.after(FRAME_INTERVAL_MS, self.scroll)

    def refresh_loop(self):
        while True:
            new_text = build_display_text()
            with self.lock:
                self.pending_text = new_text
            time.sleep(REFRESH_INTERVAL_SEC)


def main():
    root = tk.Tk()
    root.geometry(f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}")
    WeatherMarquee(root)
    root.mainloop()


if __name__ == "__main__":
    main()
