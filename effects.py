import math
import random

from settings import SIZE, GOOD, BAD, WARN, INFO
from utils import pick_free_cell, ease_out_back, hsv_color
import sprites

# tên, mô tả, màu
EFFECT_INFO = {
    "speed_up": ("TĂNG TỐC!", "Nhanh gấp đôi trong 5 giây", WARN),
    "slow_down": ("LÀM CHẬM", "Chậm gấp đôi trong 5 giây", INFO),
}

# tên, mô tả, màu, có lợi không
GAMBLING_INFO = {
    "longer_tail_by_20": ("ĐUÔI DÀI THÊM 20", "Rắn đang mọc dài ra...", GOOD, True),
    "die_instantly": ("XUI QUÁ!", "Chết ngay lập tức", BAD, False),
    "halve_points": ("ĐIỂM GIẢM MỘT NỬA", "Điểm bị chia đôi", BAD, False),
    "100_points": ("+100 ĐIỂM!", "Trúng lớn rồi!", GOOD, True),
    "shorten_tail_50%": ("ĐUÔI NGẮN 50%", "Mất một nửa thân", WARN, False),
    "become_1_pixel": ("THU NHỎ!", "Chỉ còn lại 1 ô", BAD, False),
    "lost_all_points": ("MẤT SẠCH ĐIỂM", "Điểm về 0", BAD, False),
}


class Effects:

    def __init__(self):
        self.effect = ["speed_up", "slow_down"]
        self.gambling = ["longer_tail_by_20", "die_instantly", "halve_points", "100_points",
                         "shorten_tail_50%", "become_1_pixel", "lost_all_points"]
        self.effect_pos = None
        self.gambling_pos = None
        self.effect_age = 0.0
        self.gambling_age = 0.0

    def random_effect(self):
        return random.choices(self.effect, weights=[1, 1], k=1)[0]

    def random_gambling(self):
        return random.choices(self.gambling, weights=[5, 1, 11, 60, 2, 1, 20], k=1)[0]

    def spawn_effect(self, occupied):
        self.effect_pos = list(pick_free_cell(occupied))
        self.effect_age = 0.0

    def spawn_gambling(self, occupied):
        self.gambling_pos = list(pick_free_cell(occupied))
        self.gambling_age = 0.0

    def update(self, dt):
        self.effect_age += dt
        self.gambling_age += dt

    @staticmethod
    def _c(pos):
        return pos[0] * SIZE + SIZE // 2, pos[1] * SIZE + SIZE // 2

    def lights(self, t):
        out = []
        if self.effect_pos is not None:
            cx, cy = self._c(self.effect_pos)
            out.append((cx, cy, 32, (255, 50, 140), 0.8 + 0.2 * math.sin(t * 6)))
        if self.gambling_pos is not None:
            cx, cy = self._c(self.gambling_pos)
            out.append((cx, cy, 34, hsv_color(t * 0.6, 0.8, 1.0), 0.9))
        return out

    def draw_effect(self, screen, t=0.0):
        if self.effect_pos is None:
            return
        cx, cy = self._c(self.effect_pos)
        sprites.draw_effect_orb(screen, cx, cy, SIZE, t, ease_out_back(self.effect_age / 0.35))

    def draw_gambling(self, screen, t=0.0):
        if self.gambling_pos is None:
            return
        cx, cy = self._c(self.gambling_pos)
        sprites.draw_gamble(screen, cx, cy, SIZE, t, ease_out_back(self.gambling_age / 0.35))
