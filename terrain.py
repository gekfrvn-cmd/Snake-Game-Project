import math
import random

import pygame

import ui
import sprites
from settings import *
from utils import lighten, darken, lerp_color, clamp


# =====================================================================
# GẠCH & SÀN (dùng chung cho nền menu)
# =====================================================================

def brick_surface(w, h, seed, base, mortar, hi, brick_w=10, brick_h=5, var=10, moss=0.0):
    """Tường gạch so le, mỗi viên một sắc độ khác nhau, có vữa và vạch sáng."""
    rnd = random.Random(seed)
    s = pygame.Surface((w, h))
    s.fill(mortar)
    rows = h // brick_h + 1
    for r in range(rows):
        y = r * brick_h
        off = (brick_w // 2) * (r % 2)
        x = -off
        while x < w:
            sh = rnd.randint(-var, var)
            c = (clamp(base[0] + sh, 0, 255), clamp(base[1] + sh, 0, 255), clamp(base[2] + sh, 0, 255))
            ui.rect(s, c, x, y, brick_w - 1, brick_h - 1)
            ui.rect(s, hi if sh > -var // 3 else lerp_color(c, hi, 0.4), x, y, brick_w - 1, 1)
            ui.rect(s, darken(c, 0.82), x, y + brick_h - 2, brick_w - 1, 1)
            if rnd.random() < 0.18:      # vết sứt
                ui.px(s, mortar, x + rnd.randint(1, brick_w - 3), y + rnd.randint(1, brick_h - 2))
            if moss and rnd.random() < moss:
                mx = x + rnd.randint(0, brick_w - 3)
                ui.rect(s, (46, 90, 60), mx, y + brick_h - 3, rnd.randint(2, 4), 2)
                ui.px(s, (84, 140, 84), mx, y + brick_h - 3)
            x += brick_w
    return s


def make_floor():
    """Sàn đá 510x390: ô caro, vữa, nứt, rêu, sỏi - tất cả vẽ 1 lần."""
    rnd = random.Random(2024)
    s = pygame.Surface((WIDTH, HEIGHT))
    A, B = (42, 44, 70), (47, 50, 79)
    for cy in range(ROWS):
        for cx in range(COLS):
            x, y = cx * SIZE, cy * SIZE
            v = math.sin(cx * 0.31 + math.sin(cy * 0.23) * 2.0) + math.cos(cy * 0.37 + cx * 0.17)
            off = 5 if v > 0.9 else -5 if v < -0.9 else 0
            base = A if (cx + cy) % 2 else B
            c = (clamp(base[0] + off + rnd.randint(-1, 1), 0, 255), clamp(base[1] + off + rnd.randint(-1, 1), 0, 255),
                 clamp(base[2] + off + rnd.randint(-1, 1), 0, 255))
            ui.rect(s, c, x, y, SIZE, SIZE)
            ui.rect(s, darken(c, 0.72), x, y + SIZE - 1, SIZE, 1)
            ui.rect(s, darken(c, 0.78), x + SIZE - 1, y, 1, SIZE - 1)
            ui.rect(s, lighten(c, 0.07), x, y, SIZE - 1, 1)
            ui.rect(s, lighten(c, 0.04), x, y + 1, 1, SIZE - 2)
            r = rnd.random()
            if r < 0.07:       # vết nứt
                px0, py0 = x + rnd.randint(2, 6), y + rnd.randint(1, 4)
                for i in range(rnd.randint(3, 5)):
                    ui.px(s, darken(c, 0.55), px0 + i // 2, py0 + i)
                    if rnd.random() < 0.4:
                        ui.px(s, darken(c, 0.55), px0 + i // 2 + 1, py0 + i)
            elif r < 0.12:     # rêu
                for _ in range(3):
                    ui.px(s, (50, 96, 66), x + rnd.randint(1, 7), y + rnd.randint(1, 7))
            elif r < 0.16:     # sỏi
                gx, gy = x + rnd.randint(2, 6), y + rnd.randint(2, 6)
                ui.rect(s, lighten(c, 0.22), gx, gy, 2, 1)
                ui.px(s, darken(c, 0.6), gx, gy + 1)
    return s


# =====================================================================
# CỘT TƯỜNG
# =====================================================================

class Terrain:

    def __init__(self):
        self.wall = []
        walls = [
            (7, 8, 10, 30),
            (18, 8, 21, 30),
            (29, 8, 32, 30),
            (40, 8, 43, 30),
        ]
        self.pillars = walls
        for x1, y1, x2, y2 in walls:
            for x in range(x1, x2 + 1):
                for y in range(y1, y2):
                    self.wall.append([x, y])
        self.cells = {tuple(c) for c in self.wall}
        self.torches = []
        self._build_surface()

    def hit_wall(self, pos):
        return tuple(pos) in self.cells

    # Vẽ sẵn 1 lần
    def _build_surface(self):
        S = SIZE
        self.surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        rnd = random.Random(42)
        # bóng đổ xuống sàn
        for x, y in self.wall:
            self.surface.fill((0, 0, 0, 120), (x * S + 3, y * S + 4, S, S))
        for pi, (x1, y1, x2, y2) in enumerate(self.pillars):
            px0, py0 = x1 * S, y1 * S
            pw, ph = (x2 - x1 + 1) * S, (y2 - y1) * S
            body = brick_surface(pw, ph, 100 + pi, (88, 78, 112), (30, 25, 44), (124, 114, 150), var=11, moss=0.10)
            self.surface.blit(body, (px0, py0))
            # đổ bóng dọc: trái sáng, phải tối (khối 3D)
            ui.rect(self.surface, (150, 140, 176), px0, py0, 1, ph)
            ui.rect(self.surface, (118, 108, 144), px0 + 1, py0, 1, ph)
            ui.rect(self.surface, (40, 34, 58), px0 + pw - 2, py0, 1, ph)
            ui.rect(self.surface, (22, 18, 34), px0 + pw - 1, py0, 1, ph)
            # gờ đá ngang
            for gy in range(py0 + 40, py0 + ph - 20, 60):
                ui.rect(self.surface, (24, 19, 36), px0, gy, pw, 1)
                ui.rect(self.surface, (146, 136, 172), px0, gy + 1, pw, 1)
                ui.rect(self.surface, (60, 52, 82), px0, gy + 2, pw, 2)
                ui.rect(self.surface, (24, 19, 36), px0, gy + 4, pw, 1)
            # chân cột tối dần
            for i in range(10):
                fill_y = py0 + ph - 10 + i
                ui.fill_a(self.surface, px0, fill_y, pw, 1, (6, 4, 16, int(14 * (i + 1))))
            # vết nứt
            for _ in range(5):
                cx0, cy0 = px0 + rnd.randint(3, pw - 4), py0 + rnd.randint(14, ph - 20)
                for i in range(rnd.randint(5, 11)):
                    ui.px(self.surface, (24, 19, 36), cx0 + (i // 3) * rnd.choice((-1, 1)), cy0 + i)
            # sọ người gắn tường
            for _ in range(2):
                sx0, sy0 = px0 + rnd.randint(5, pw - 12), py0 + rnd.randint(30, ph - 40)
                self._skull(sx0, sy0)
            # dây leo từ trên rủ xuống
            for vx in range(px0 + 1, px0 + pw - 1, 3):
                if rnd.random() < 0.7:
                    ln = rnd.randint(4, 26)
                    for i in range(ln):
                        c = (60, 130, 74) if i % 5 else (90, 170, 96)
                        ui.px(self.surface, c, vx + (1 if (i // 4) % 2 else 0), py0 + 3 + i)
                        if i % 6 == 3:
                            ui.px(self.surface, (110, 190, 110), vx + 2, py0 + 3 + i)
            # viền mực quanh cột
            ui.frame(self.surface, INK, px0 - 1, py0 - 1, pw + 2, ph + 2)
            # nắp rêu phía trên
            ui.rect(self.surface, (46, 100, 64), px0 - 1, py0 - 2, pw + 2, 5)
            ui.rect(self.surface, (84, 160, 88), px0 - 1, py0 - 2, pw + 2, 2)
            ui.rect(self.surface, (130, 210, 120), px0 - 1, py0 - 2, pw + 2, 1)
            for gx in range(px0, px0 + pw, 2):
                if rnd.random() < 0.7:
                    h = rnd.randint(1, 3)
                    ui.rect(self.surface, (84, 160, 88), gx, py0 - 2 - h, 1, h)
                    if rnd.random() < 0.3:
                        ui.px(self.surface, (160, 230, 130), gx, py0 - 2 - h)
            for gx in range(px0, px0 + pw, 3):
                if rnd.random() < 0.6:
                    ui.rect(self.surface, (46, 100, 64), gx, py0 + 3, 1, rnd.randint(1, 3))
            # đuốc gắn tường
            side = 1 if pi % 2 == 0 else pw // S - 2
            for ty in (y1 + 6, y1 + 16):
                self.torches.append((px0 + side * S + S // 2, ty * S + S // 2 - 1))
                side = (pw // S - 1) - side if pw // S > 2 else side

    def _skull(self, x, y):
        s = self.surface
        pat = ("..###..", ".#####.", "##.#.##", "#######", ".#####.", "..#.#..")
        ui.rect(s, INK, x - 1, y - 1, 9, 8)
        for j, row in enumerate(pat):
            for i, c in enumerate(row):
                if c == "#":
                    ui.px(s, (200, 194, 180), x + i, y + j)
                else:
                    pass
        ui.px(s, INK, x + 2, y + 2)
        ui.px(s, INK, x + 4, y + 2)
        ui.px(s, INK, x + 3, y + 3)

    def draw(self, screen):
        screen.blit(self.surface, (0, 0))

    def draw_torches(self, screen, t, pal):
        for i, (cx, cy) in enumerate(self.torches):
            sprites.draw_torch(screen, cx, cy, t, pal, seed=i)

    def lights(self, t, color):
        out = []
        for i, (cx, cy) in enumerate(self.torches):
            k = 0.85 + 0.15 * math.sin(t * 9 + i * 2.3) + 0.06 * math.sin(t * 23 + i)
            out.append((cx, cy - 4, 70, color, k))
        return out
