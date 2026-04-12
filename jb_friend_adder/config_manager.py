import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULTS = {
    # 절대 좌표 (캘리브레이션 후 저장)
    "search_box": None,    # [x, y]
    "search_btn": None,    # [x, y]
    "results_tl": None,    # [x, y] 결과 영역 좌상단
    "results_br": None,    # [x, y] 결과 영역 우하단
    # 타이밍
    "delay_after_search": 1.5,
    "delay_between_rows": 0.8,
    "delay_after_click": 0.3,
    # 결과 파싱
    "circle_x_offset": 22,      # 결과 영역 오른쪽 끝에서 원 아이콘까지 거리(px)
    "row_group_threshold": 15,  # OCR 결과를 같은 행으로 묶는 Y 허용 오차(px)
    "max_scroll_attempts": 10,  # 스크롤 최대 횟수
    # OCR
    "ocr_lang": ["ko", "en"],
}


class ConfigManager:
    def __init__(self):
        self._data = dict(DEFAULTS)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self._data.update(saved)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def is_calibrated(self):
        required = ["search_box", "search_btn", "results_tl", "results_br"]
        return all(self._data.get(k) is not None for k in required)
