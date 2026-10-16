import json
import os

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")

DEFAULTS = {
    "difficulty": 1,
    "volume": 7,
    "music": 5,
    "best_level": 1,
    "skin": 0,
    "grid": False,
    "particles": True,
    "shake": True,
    "fullscreen": False,
    "high_score": 0,
    "lighting": True,
    "crt": False,
}


class Config:
    """Lưu cài đặt và kỷ lục vào save.json cạnh file code."""

    def __init__(self):
        self.data = dict(DEFAULTS)
        self.load()

    def load(self):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for k, default in DEFAULTS.items():
                if k in saved and isinstance(saved[k], type(default)):
                    self.data[k] = saved[k]
        except Exception:
            pass

    def save(self):
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set(self, key, value):
        self.data[key] = value

    def __getattr__(self, name):
        data = self.__dict__.get("data")
        if data is not None and name in data:
            return data[name]
        raise AttributeError(name)
