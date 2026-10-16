"""Cấp độ XP và 3 kỹ năng: Lướt (Dash), Dịch chuyển (Teleport), Khiên (Shield)."""

MAX_LEVEL = 14
SKILL_MAX = 3


def xp_needed(level):
    """Số XP cần để lên cấp kế tiếp. Cấp cuối cùng cần 20 quả táo, các cấp trước tăng dần tới đó."""
    if level >= MAX_LEVEL:
        return 0
    return int(round(3 + 17 * ((level - 1) / (MAX_LEVEL - 2)) ** 1.4))


SKILLS = {
    "dash": {
        "name": "Lướt", "key": "Space", "color": (255, 190, 70), "icon": "dash",
        "cells": [4, 6, 8], "cd": [9, 8, 7],
    },
    "teleport": {
        "name": "Dịch chuyển", "key": "E", "color": (190, 140, 255), "icon": "teleport",
        "range": [10, 16, 24], "cd": [14, 11, 8],
    },
    "shield": {
        "name": "Khiên", "key": "Q", "color": (110, 200, 255), "icon": "shield",
        "dur": [5, 8, 12], "hits": [1, 1, 2], "cd": [18, 15, 12],
    },
}
ORDER = ["dash", "teleport", "shield"]


def describe(name, level):
    """2 dòng mô tả sức mạnh của kỹ năng ở cấp `level` (1..3)."""
    s, i = SKILLS[name], level - 1
    if name == "dash":
        return [f"Lướt {s['cells'][i]} ô, phá vật cản", f"Hồi chiêu {s['cd'][i]} giây"]
    if name == "teleport":
        return ["Dịch chuyển tới con trỏ chuột", f"Tối đa {s['range'][i]} ô · hồi {s['cd'][i]} giây"]
    return [f"Khiên {s['dur'][i]} giây, chặn {s['hits'][i]} đòn", f"Hồi chiêu {s['cd'][i]} giây"]


class SkillState:

    def __init__(self):
        self.level = {n: 0 for n in ORDER}
        self.cd = {n: 0.0 for n in ORDER}
        self.cd_total = {n: 1.0 for n in ORDER}
        self.flash = {n: 0.0 for n in ORDER}     # nháy sáng khi hồi xong

    def update(self, dt):
        for n in ORDER:
            if self.cd[n] > 0:
                self.cd[n] = max(0.0, self.cd[n] - dt)
                if self.cd[n] == 0 and self.level[n] > 0:
                    self.flash[n] = 0.6
            self.flash[n] = max(0.0, self.flash[n] - dt)

    def ready(self, n):
        return self.level[n] > 0 and self.cd[n] <= 0

    def start_cd(self, n):
        v = float(SKILLS[n]["cd"][self.level[n] - 1])
        self.cd[n] = v
        self.cd_total[n] = v

    def upgradable(self):
        return [n for n in ORDER if self.level[n] < SKILL_MAX]

    def upgrade(self, n):
        if self.level[n] < SKILL_MAX:
            self.level[n] += 1

    def param(self, n, key):
        return SKILLS[n][key][self.level[n] - 1]
