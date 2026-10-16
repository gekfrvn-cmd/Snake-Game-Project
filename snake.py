import math

import pygame

import ui
from settings import COLS, ROWS, SIZE, SKINS, INK
from utils import lerp_color, hsv_color, lighten, darken, clamp, ease_out_cubic

OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
DIR_VEC = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}

S = SIZE
EYE_POS = {
    "right": ((5, 1), (5, 6)),
    "left": ((2, 1), (2, 6)),
    "up": ((1, 2), (6, 2)),
    "down": ((1, 5), (6, 5)),
}


class Snake:

    def __init__(self):
        self.reset()

    # =========================
    # RESET
    # =========================

    def reset(self):
        self.pos = [[1, 4], [2, 4], [3, 4]]   # đuôi ... đầu
        self.direction = "right"
        self.queue = []                        # hàng đợi phím (tối đa 2)
        self.growth = 0                        # số đốt còn phải mọc thêm
        self.prev = None                       # vị trí trước bước đi (để trượt mượt)

    def snap(self):
        """Gọi khi thân rắn bị đổi đột ngột (bị cắt, co ngắn...) để bỏ nội suy."""
        self.prev = None

    # =========================
    # HƯỚNG ĐI (có hàng đợi để bấm nhanh không bị mất phím)
    # =========================

    def change_direction(self, direction):
        last = self.queue[-1] if self.queue else self.direction
        if direction == last or direction == OPPOSITE[last]:
            return
        if len(self.queue) < 2:
            self.queue.append(direction)

    def apply_queued_direction(self):
        if self.queue:
            self.direction = self.queue.pop(0)

    # =========================
    # DI CHUYỂN
    # =========================

    def get_new_head(self):
        hx, hy = self.pos[-1]
        dx, dy = DIR_VEC[self.direction]
        return [(hx + dx) % COLS, (hy + dy) % ROWS]   # xuyên qua mép màn hình

    def grow(self, n=1):
        self.growth += n

    def move(self, new_head=None):
        if new_head is None:
            new_head = self.get_new_head()
        self.prev = [tuple(p) for p in self.pos]
        self.pos.append(list(new_head))
        if self.growth > 0:
            self.growth -= 1
        else:
            self.pos.pop(0)

    def hit_body(self):
        return self.pos[-1] in self.pos[:-1]

    # =========================
    # VỊ TRÍ HIỂN THỊ (trượt mượt giữa 2 ô, luôn bám lưới pixel)
    # =========================

    def visual_positions(self, frac=1.0):
        cur = self.pos
        prev = self.prev
        if prev is None or frac >= 0.999:
            return [(p[0] * S, p[1] * S) for p in cur]
        lp = len(prev)
        out = []
        for j, c in enumerate(cur):
            p = prev[min(j, lp - 1)]
            dx, dy = c[0] - p[0], c[1] - p[1]
            if abs(dx) > 1 or abs(dy) > 1:
                out.append((c[0] * S, c[1] * S))
            else:
                out.append((int(round((p[0] + dx * frac) * S)), int(round((p[1] + dy * frac) * S))))
        return out

    # =========================
    # VẼ
    # =========================

    def draw(self, screen, t=0.0, skin=None, dead=False, frac=1.0):
        skin = skin or SKINS[0]
        vpos = self.visual_positions(frac)
        draw_chain(screen, vpos, t, skin, self.direction, dead)

    def head_pixel(self, frac=1.0):
        x, y = self.visual_positions(frac)[-1]
        return x + S // 2, y + S // 2


def _union(ax, ay, aw, bx, by, bw):
    """Hình chữ nhật bao 2 hình vuông cạnh aw và bw."""
    x0, y0 = min(ax, bx), min(ay, by)
    x1, y1 = max(ax + aw, bx + bw), max(ay + aw, by + bw)
    return x0, y0, x1 - x0, y1 - y0


def _cross(surf, color, x, y, w, h):
    """Hình chữ nhật cắt góc 1 pixel (bo tròn kiểu pixel art)."""
    if w <= 2 or h <= 2:
        ui.rect(surf, color, x, y, w, h)
        return
    ui.rect(surf, color, x + 1, y, w - 2, h)
    ui.rect(surf, color, x, y + 1, w, h - 2)


def segment_colors(n, skin, t):
    cols = []
    rainbow = skin.get("rainbow", False)
    for i in range(n):
        if rainbow:
            cols.append(hsv_color(t * 0.2 - i * 0.025, 0.65, 0.95))
        else:
            cols.append(lerp_color(skin["tail"], skin["body"], min(1.0, i / max(1, min(n - 1, 14)))))
    return cols


def draw_chain(screen, vpos, t, skin, direction, dead=False, outline=INK):
    """Vẽ rắn từ danh sách toạ độ pixel (góc trên-trái của từng đốt), đuôi -> đầu."""
    n = len(vpos)
    if n == 0:
        return
    rainbow = skin.get("rainbow", False)
    cols = segment_colors(n, skin, t)
    head_col = hsv_color(t * 0.2 - n * 0.025, 0.35, 1.0) if rainbow else skin["head"]
    body_n = n - 1

    def inset(i):
        return 1 + max(0, 2 - i)

    # --- lượt 1: viền mực ---
    for i in range(body_n):
        x, y = vpos[i]
        k = inset(i)
        o = k - 1
        w = S - 2 * o
        _cross(screen, outline, x + o, y + o, w, w)
        nx, ny = vpos[i + 1]
        if abs(nx - x) <= S + 1 and abs(ny - y) <= S + 1:
            nk = inset(i + 1) if i + 1 < body_n else 1
            no = nk - 1
            ux, uy, uw, uh = _union(x + o, y + o, w, nx + no, ny + no, S - 2 * no)
            ui.rect(screen, outline, ux, uy, uw, uh)

    # --- lượt 2: thân ---
    for i in range(body_n):
        x, y = vpos[i]
        k = inset(i)
        sz = S - 2 * k
        _cross(screen, cols[i], x + k, y + k, sz, sz)
        nx, ny = vpos[i + 1]
        if abs(nx - x) <= S + 1 and abs(ny - y) <= S + 1:
            nk = inset(i + 1) if i + 1 < body_n else 1
            nsz = S - 2 * nk
            ux, uy, uw, uh = _union(x + k, y + k, sz, nx + nk, ny + nk, nsz)
            ui.rect(screen, cols[i], ux, uy, uw, uh)

    # --- lượt 3: chi tiết (vạch sáng, bóng, hoa văn vảy) ---
    for i in range(body_n):
        x, y = vpos[i]
        k = inset(i)
        sz = S - 2 * k
        if sz < 4:
            continue
        c = cols[i]
        light = lerp_color(c, skin["light"], 0.55)
        ui.rect(screen, light, x + k + 1, y + k, sz - 2, 1)
        ui.rect(screen, darken(c, 0.68), x + k + 1, y + k + sz - 1, sz - 2, 1)
        if sz >= 8 and i % 2 == 0:
            ui.rect(screen, lerp_color(c, skin["belly"], 0.7), x + 4, y + 4, 2, 2)
            ui.px(screen, lerp_color(c, skin["light"], 0.9), x + 4, y + 4)
        elif sz >= 8:
            ui.px(screen, darken(c, 0.78), x + 2, y + 6)
            ui.px(screen, darken(c, 0.78), x + 7, y + 3)

    # --- đầu ---
    hx, hy = vpos[-1]
    if skin.get("ember") and not dead:
        ui.draw_flame(screen, hx + 5, hy + 2, 9, 11, t, ((120, 30, 30), (255, 110, 30), (255, 190, 70), (255, 245, 190)), seed=3)
    _cross(screen, outline, hx - 1, hy - 1, S + 2, S + 2)
    # cổ nối đầu với thân
    if body_n > 0:
        bx, by = vpos[body_n - 1]
        if abs(hx - bx) <= S + 1 and abs(hy - by) <= S + 1:
            ux, uy, uw, uh = _union(bx + 1, by + 1, S - 2, hx, hy, S)
            ui.rect(screen, cols[body_n - 1], ux, uy, uw, uh)
    _cross(screen, head_col, hx, hy, S, S)
    ui.rect(screen, lighten(head_col, 0.4), hx + 2, hy, S - 4, 1)
    ui.rect(screen, darken(head_col, 0.7), hx + 2, hy + S - 1, S - 4, 1)
    if skin.get("ember"):
        ui.rect(screen, (60, 50, 74), hx + 1, hy + 1, S - 2, S - 2)
        ui.rect(screen, lighten((60, 50, 74), 0.25), hx + 2, hy + 1, S - 4, 1)

    d = DIR_VEC[direction]
    if not dead and math.sin(t * 5) > 0.55:
        tongue = (232, 52, 76)
        for k in range(3):
            if d[0]:
                tx = hx + (S + k if d[0] > 0 else -1 - k)
                ui.px(screen, tongue, tx, hy + 4)
            else:
                ty = hy + (S + k if d[1] > 0 else -1 - k)
                ui.px(screen, tongue, hx + 4, ty)
        if d[0]:
            fx = hx + (S + 3 if d[0] > 0 else -4)
            ui.px(screen, tongue, fx, hy + 3)
            ui.px(screen, tongue, fx, hy + 5)
        else:
            fy = hy + (S + 3 if d[1] > 0 else -4)
            ui.px(screen, tongue, hx + 3, fy)
            ui.px(screen, tongue, hx + 5, fy)

    eye_col = (255, 190, 60) if skin.get("ember") else (255, 255, 255)
    for ex, ey in EYE_POS[direction]:
        ex, ey = hx + ex, hy + ey
        if dead:
            ui.px(screen, INK, ex, ey)
            ui.px(screen, INK, ex + 2, ey)
            ui.px(screen, INK, ex + 1, ey + 1)
            ui.px(screen, INK, ex, ey + 2)
            ui.px(screen, INK, ex + 2, ey + 2)
            continue
        ui.rect(screen, eye_col, ex, ey, 3, 3)
        if direction == "right":
            ui.rect(screen, INK, ex + 2, ey, 1, 3)
        elif direction == "left":
            ui.rect(screen, INK, ex, ey, 1, 3)
        elif direction == "up":
            ui.rect(screen, INK, ex, ey, 3, 1)
        else:
            ui.rect(screen, INK, ex, ey + 2, 3, 1)


def draw_preview(surf, cx, cy, skin, length=6, t=0.0):
    """Rắn nằm ngang, đầu bên phải, dùng cho xem trước skin / biểu tượng."""
    total = length * S
    x0 = int(cx - total // 2)
    y = int(cy - S // 2)
    vpos = [(x0 + i * S, y + int(round(math.sin(t * 4 + i * 0.7) * 0.0))) for i in range(length)]
    draw_chain(surf, vpos, t, skin, "right")
