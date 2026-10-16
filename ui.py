import math
import random

import pygame

import pixfont
from settings import *
from utils import *

# =====================================================================
# 1. HÌNH KHỐI PIXEL (không khử răng cưa - cố tình để giữ nét pixel art)
# =====================================================================


def rect(surf, color, x, y, w, h):
    w, h = int(w), int(h)
    if w > 0 and h > 0:
        surf.fill(color, (int(x), int(y), w, h))


def px(surf, color, x, y):
    surf.fill(color, (int(x), int(y), 1, 1))


def hline(surf, color, x, y, w):
    rect(surf, color, x, y, w, 1)


def vline(surf, color, x, y, h):
    rect(surf, color, x, y, 1, h)


def frame(surf, color, x, y, w, h, t=1):
    rect(surf, color, x, y, w, t)
    rect(surf, color, x, y + h - t, w, t)
    rect(surf, color, x, y + t, t, h - 2 * t)
    rect(surf, color, x + w - t, y + t, t, h - 2 * t)


def line(surf, color, x0, y0, x1, y1):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    if y0 == y1:
        rect(surf, color, min(x0, x1), y0, abs(x1 - x0) + 1, 1)
        return
    if x0 == x1:
        rect(surf, color, x0, min(y0, y1), 1, abs(y1 - y0) + 1)
        return
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        surf.fill(color, (x0, y0, 1, 1))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(surf, color, cx, cy, r):
    cx, cy, r = int(cx), int(cy), int(r)
    if r <= 0:
        px(surf, color, cx, cy)
        return
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(r * r - dy * dy) + 0.5)
        surf.fill(color, (cx - dx, cy + dy, dx * 2 + 1, 1))


def ring(surf, color, cx, cy, r):
    cx, cy, r = int(cx), int(cy), int(r)
    if r <= 1:
        disc(surf, color, cx, cy, r)
        return
    ri = r - 1
    for dy in range(-r, r + 1):
        xo = int(math.sqrt(r * r - dy * dy) + 0.5)
        if abs(dy) >= ri:
            surf.fill(color, (cx - xo, cy + dy, xo * 2 + 1, 1))
            continue
        xi = int(math.sqrt(ri * ri - dy * dy) + 0.5)
        w = max(1, xo - xi)
        surf.fill(color, (cx - xo, cy + dy, w, 1))
        surf.fill(color, (cx + xo - w + 1, cy + dy, w, 1))


def dashed_ring(surf, color, cx, cy, r, rot, dashes=8, fill=0.55):
    """Vòng tròn đứt nét xoay quanh (dùng cho khiên)."""
    steps = max(24, int(r * 7))
    for i in range(steps):
        a = i / steps
        if ((a * dashes + rot) % 1.0) > fill:
            continue
        ang = a * math.tau
        surf.fill(color, (int(round(cx + math.cos(ang) * r)), int(round(cy + math.sin(ang) * r)), 1, 1))


_tmp_cache = {}


def fill_a(surf, x, y, w, h, color):
    """Tô hình chữ nhật bán trong suốt lên surface (color có alpha)."""
    w, h = int(w), int(h)
    if w <= 0 or h <= 0:
        return
    a = color[3] if len(color) > 3 else 255
    if a >= 255:
        surf.fill(color[:3], (int(x), int(y), w, h))
        return
    if a <= 0:
        return
    key = (w, h)
    t = _tmp_cache.get(key)
    if t is None:
        if len(_tmp_cache) > 160:
            _tmp_cache.clear()
        t = pygame.Surface((w, h), pygame.SRCALPHA)
        _tmp_cache[key] = t
    t.fill((color[0], color[1], color[2], int(a)))
    surf.blit(t, (int(x), int(y)))


def dim(surf, alpha):
    fill_a(surf, 0, 0, surf.get_width(), surf.get_height(), (0, 0, 0, int(alpha)))


def tint(surf, color, alpha):
    fill_a(surf, 0, 0, surf.get_width(), surf.get_height(), (color[0], color[1], color[2], int(alpha)))


def vertical_gradient(w, h, top, bottom, bands=None):
    """Gradient dạng dải màu (posterize) cho đúng chất pixel art."""
    s = pygame.Surface((w, h))
    bands = bands or max(2, h // 3)
    bh = max(1, h // bands)
    for i in range(0, h, bh):
        s.fill(lerp_color(top, bottom, i / max(1, h - 1)), (0, i, w, bh))
    return s


# =====================================================================
# 2. CHỮ PIXEL
# =====================================================================

_text_cache = {}


def _runs(text):
    pts, w = pixfont.layout(text)
    rows = {}
    for x, y in pts:
        rows.setdefault(y, []).append(x)
    runs = []
    for y, xs in rows.items():
        xs.sort()
        start = prev = xs[0]
        for x in xs[1:]:
            if x == prev + 1:
                prev = x
                continue
            runs.append((start, y, prev - start + 1))
            start = prev = x
        runs.append((start, y, prev - start + 1))
    return runs, w


def _build_text(text, s, color, outline, shadow):
    runs, w = _runs(text)
    o = 0
    if outline is not None:
        o = 1 if s <= 3 else 2 if s <= 8 else 3
    sh = int(shadow)
    top = pixfont.MARGIN_TOP * s
    W = max(1, w * s + 2 * o + sh)
    H = (pixfont.MARGIN_TOP + pixfont.CAP_H + pixfont.MARGIN_BOTTOM) * s + 2 * o + sh
    img = pygame.Surface((W, H), pygame.SRCALPHA)
    ox, oy = o, top + o
    if sh:
        sc = (0, 0, 0, 150)
        for x, y, n in runs:
            img.fill(sc, (ox + x * s + sh, oy + y * s + sh, n * s, s))
    if outline is not None:
        for x, y, n in runs:
            img.fill(outline, (ox + x * s - o, oy + y * s - o, n * s + 2 * o, s + 2 * o))
    multi = isinstance(color[0], tuple)
    for x, y, n in runs:
        if multi:
            c = color[max(0, min(len(color) - 1, y))]
        else:
            c = color
        img.fill(c, (ox + x * s, oy + y * s, n * s, s))
    return img, w * s, o


def text(surf, txt, s, color, pos, anchor="topleft", outline=INK, shadow=0, alpha=255):
    """Vẽ chữ pixel. s = hệ số phóng (1, 2, 3...). Neo theo khung chữ hoa 7 hàng.
    color có thể là 1 màu hoặc tuple 7 màu (gradient theo từng hàng pixel)."""
    txt = str(txt)
    if not txt:
        return pygame.Rect(pos[0], pos[1], 0, pixfont.CAP_H * s)
    key = (txt, s, color, outline, shadow)
    hit = _text_cache.get(key)
    if hit is None:
        if len(_text_cache) > 700:
            _text_cache.clear()
        hit = _text_cache[key] = _build_text(txt, s, color, outline, shadow)
    img, wpx, o = hit
    cap = pygame.Rect(0, 0, wpx, pixfont.CAP_H * s)
    setattr(cap, anchor, (int(pos[0]), int(pos[1])))
    img.set_alpha(int(alpha))
    surf.blit(img, (cap.x - o, cap.y - pixfont.MARGIN_TOP * s - o))
    return cap


def text_w(txt, s=1):
    return pixfont.text_width(str(txt), s)


def text_wrapped(surf, txt, s, color, x, y, max_w, line_h=None, anchor="left", outline=INK, alpha=255):
    """Vẽ đoạn văn tự xuống dòng. Trả về y sau dòng cuối."""
    line_h = line_h or (pixfont.CAP_H * s + 5 * s)
    for ln in pixfont.wrap(txt, s, max_w):
        if anchor == "center":
            text(surf, ln, s, color, (x + max_w // 2, y), "midtop", outline=outline, alpha=alpha)
        else:
            text(surf, ln, s, color, (x, y), "topleft", outline=outline, alpha=alpha)
        y += line_h
    return y


# =====================================================================
# 3. ICON PIXEL (tự thêm viền mực)
# =====================================================================
# '#': màu chính  l: sáng  d: tối  w: trắng  r: đỏ  o: cam  y: vàng  .: trống

ICONS = {
    "play": ("l........", "ll.......", "l##......", "l####....", "l#####...", "l######..", "l#####...",
             "l####....", "l##......", "ll.......", "l........"),
    "help": ("..#####..", ".##...##.", "##.....##", "#...###.#", "#..#...##", "#.....##.", "#....##..",
             "#........", "#....##..", "##...##.#", ".#######."),
    "settings": ("....#....", ".#.###.#.", "..#####..", ".###.###.", "####.####", ".###.###.",
                 "..#####..", ".#.###.#.", "....#...."),
    "credits": ("....l....", "....#....", "...l##...", "l########", ".l######.", "..######.", "..##.##..",
                ".##...##.", ".#.....#."),
    "quit": ("##.....##", "###...###", ".###.###.", "..#####..", "...###...", "..#####..", ".###.###.",
             "###...###", "##.....##"),
    "retry": (".#####...", "##...##.#", "#.....###", "#.....##.", "#........", "#.......#", "##.....##",
              ".##...##.", "..#####.."),
    "menu": ("#########", ".........", "#########", ".........", "#########"),
    "dash": ("l..l.....", ".l..l....", "..#..#...", "...#..#..", "....#..#.", "...#..#..", "..#..#...",
             ".l..l....", "l..l....."),
    "teleport": ("..#####..", ".#lll..#.", "#l.###.d#", "#.#...#.#", "#.#.#.#.#", "#.#...#.#", "#d.###.l#",
                 ".#d...dd.", "..#####.."),
    "shield": ("#########", "#l#####d#", "#l#####d#", "#l#####d#", "##l###d##", ".##l#d##.", "..##d##..",
               "...###...", "....#...."),
    "lock": ("..#####..", ".#.....#.", ".#.....#.", "#########", "#########", "####.####", "####.####",
             "#########", "#########"),
    "skull": ("..#####..", ".#######.", "#########", "##..#..##", "##..#..##", "#########", ".#######.",
              "..#.#.#..", "..#####.."),
    "bolt": ("...yyy", "..yyy.", ".yyy..", "yyyyy.", "..yyy.", ".yyy..", "yyy...", "yy...."),
    "hourglass": ("#######", ".#####.", "..###..", "...#...", "..#.#..", ".#####.", "#######"),
    "crown": ("y...y...y", "yy.yyy.yy", "yyyyyyyyy", "yyyyyyyyy", "ddddddddd"),
    "apple": ("....o.gg.", "....o.g..", "..rrrorr.", ".rlrrrrrr", ".rlrrrrrd", ".rrrrrrrd", ".rrrrrrdd",
              "..rrrrdd.", "...dddd.."),
    "cross": ("#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "tick": ("......#", ".....##", "#...##.", "##.##..", ".###...", "..#...."),
    "ruler": ("#.#.#.#.#.#", "###########", "#.#.#.#.#.#"),
    "arrow_r": ("..#..", "..##.", "#####", "..##.", "..#.."),
    "arrow_l": ("..#..", ".##..", "#####", ".##..", "..#.."),
    "star": ("....y....", "...yyy...", "yyyyyyyyy", ".yyyyyyy.", "..yyyyy..", ".yyy.yyy.", ".yy...yy."),
}

_icon_cache = {}


def icon_surface(name, color=TEXT, scale=1):
    key = (name, color, scale)
    hit = _icon_cache.get(key)
    if hit is not None:
        return hit
    rows = ICONS[name]
    w = max(len(r) for r in rows)
    h = len(rows)
    pal = {"#": color, "l": lighten(color, 0.55), "d": darken(color, 0.5), "w": (255, 255, 255),
           "r": (232, 62, 70), "o": (255, 150, 50), "y": (255, 224, 110), "g": (90, 210, 100)}
    grid = {}
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c in pal:
                grid[(x, y)] = pal[c]
    surf = pygame.Surface(((w + 2) * scale, (h + 2) * scale), pygame.SRCALPHA)
    for (x, y) in grid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n not in grid:
                    surf.fill(INK, ((n[0] + 1) * scale, (n[1] + 1) * scale, scale, scale))
    for (x, y), c in grid.items():
        surf.fill(c, ((x + 1) * scale, (y + 1) * scale, scale, scale))
    _icon_cache[key] = surf
    return surf


def draw_icon(surf, name, cx, cy, color=TEXT, scale=1, alpha=255):
    img = icon_surface(name, tuple(color), scale)
    img.set_alpha(alpha)
    r = img.get_rect(center=(int(cx), int(cy)))
    surf.blit(img, r)
    return r


# =====================================================================
# 4. KHUNG / PANEL / THANH
# =====================================================================


def panel(surf, r, accent=GOLD, fill=(14, 12, 26), alpha=235, border=STONE_3, shadow=True, studs=True):
    x, y, w, h = [int(v) for v in r]
    if shadow:
        fill_a(surf, x + 2, y + 3, w, h, (0, 0, 0, 90))
    # thân (góc vát)
    fill_a(surf, x + 1, y, w - 2, 1, (fill[0], fill[1], fill[2], alpha))
    fill_a(surf, x, y + 1, w, h - 2, (fill[0], fill[1], fill[2], alpha))
    fill_a(surf, x + 1, y + h - 1, w - 2, 1, (fill[0], fill[1], fill[2], alpha))
    # viền mực ngoài
    rect(surf, INK, x + 1, y, w - 2, 1)
    rect(surf, INK, x + 1, y + h - 1, w - 2, 1)
    rect(surf, INK, x, y + 1, 1, h - 2)
    rect(surf, INK, x + w - 1, y + 1, 1, h - 2)
    # viền đá
    rect(surf, border, x + 2, y + 1, w - 4, 1)
    rect(surf, darken(border, 0.55), x + 2, y + h - 2, w - 4, 1)
    rect(surf, border, x + 1, y + 2, 1, h - 4)
    rect(surf, darken(border, 0.55), x + w - 2, y + 2, 1, h - 4)
    rect(surf, lighten(border, 0.25), x + 3, y + 2, w - 6, 1)
    if accent is not None:
        rect(surf, accent, x + w // 2 - 14, y, 28, 2)
        rect(surf, darken(accent, 0.5), x + w // 2 - 14, y + 2, 28, 1)
    if studs and w > 24 and h > 24:
        for sx, sy in ((x + 4, y + 4), (x + w - 6, y + 4), (x + 4, y + h - 6), (x + w - 6, y + h - 6)):
            rect(surf, darken(accent or border, 0.6), sx, sy, 2, 2)
            px(surf, lighten(accent or border, 0.3), sx, sy)


def bar(surf, x, y, w, h, frac, color, bg=(26, 22, 40), segments=0, glow=0.0):
    """Thanh tiến độ pixel: nền tối, viền mực, vạch sáng phía trên."""
    frac = clamp(frac, 0.0, 1.0)
    rect(surf, INK, x - 1, y - 1, w + 2, h + 2)
    rect(surf, bg, x, y, w, h)
    fw = int(w * frac)
    if fw > 0:
        rect(surf, color, x, y, fw, h)
        rect(surf, lighten(color, 0.45), x, y, fw, max(1, h // 3))
        rect(surf, darken(color, 0.55), x, y + h - 1, fw, 1)
        if glow > 0:
            rect(surf, lighten(color, 0.8), x, y, fw, 1)
    if segments > 1:
        for i in range(1, segments):
            sx = x + int(w * i / segments)
            rect(surf, INK, sx, y, 1, h)


def key_cap(surf, label, cx, cy, active=True):
    w = max(9, text_w(label, 1) + 6)
    r = pygame.Rect(0, 0, w, 11)
    r.center = (int(cx), int(cy))
    rect(surf, INK, r.x, r.y + 1, r.w, r.h)
    rect(surf, STONE_4 if active else STONE_2, r.x, r.y, r.w, r.h - 1)
    rect(surf, STONE_2 if active else STONE_1, r.x + 1, r.y + 1, r.w - 2, r.h - 3)
    rect(surf, lighten(STONE_4, 0.2), r.x + 1, r.y, r.w - 2, 1)
    text(surf, label, 1, TEXT if active else TEXT_DIM, (r.centerx, r.centery - 1), "center", outline=None)
    return r


def stat_pill(surf, x, y, w, h, label, value, color, bump=0.0):
    panel(surf, (x, y, w, h), accent=None, alpha=215, border=darken(color, 0.55), shadow=False, studs=False)
    rect(surf, color, x + 4, y + 5, 2, h - 10)
    text(surf, label, 1, TEXT_DIM, (x + 10, y + 5), outline=None)
    s = 2
    text(surf, str(value), s, (255, 255, 255), (x + 10, y + h - 5), "bottomleft", shadow=1 if bump > 0.2 else 0)


def draw_arrow(surf, x, y, direction, color, size=3):
    """Mũi tên tam giác pixel (direction: -1 trái, +1 phải, 'u', 'd')."""
    if direction == 1:
        for i in range(size + 1):
            rect(surf, color, x + i, y - (size - i), 1, (size - i) * 2 + 1)
    elif direction == -1:
        for i in range(size + 1):
            rect(surf, color, x - i, y - (size - i), 1, (size - i) * 2 + 1)
    elif direction == "d":
        for i in range(size + 1):
            rect(surf, color, x - (size - i), y + i, (size - i) * 2 + 1, 1)
    else:
        for i in range(size + 1):
            rect(surf, color, x - (size - i), y - i, (size - i) * 2 + 1, 1)


def ribbon(surf, label, cx, y, s=2, color=GOLD, width=None):
    """Băng rôn tiêu đề với 2 vạch trang trí hai bên."""
    tw = text_w(label, s)
    r = text(surf, label, s, color, (cx, y), "midtop", shadow=1)
    wing = width if width else 36
    mid = r.centery
    for sgn in (-1, 1):
        x0 = cx + sgn * (tw // 2 + 8)
        x1 = x0 + sgn * wing
        rect(surf, color, min(x0, x1), mid - 1, wing, 1)
        rect(surf, darken(color, 0.5), min(x0, x1), mid, wing, 1)
        rect(surf, color, x0 - (1 if sgn > 0 else 0), mid - 2, 1, 4)
    return r


# =====================================================================
# 5. ÁNH SÁNG PIXEL (lightmap + sprite sáng posterize có dither)
# =====================================================================

_BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
_light_cache = {}
_level_cache = {}


def _levels(radius, power, bands):
    key = (radius, power, bands)
    hit = _level_cache.get(key)
    if hit is not None:
        return hit
    d = radius * 2
    grid = []
    for y in range(d):
        row = []
        for x in range(d):
            dist = math.hypot(x - radius + 0.5, y - radius + 0.5) / radius
            v = 0.0 if dist >= 1.0 else (1.0 - dist) ** power
            f = v * bands
            base = int(f)
            if f - base > _BAYER[y & 3][x & 3] / 16.0:
                base += 1
            row.append(min(bands, base))
        grid.append(row)
    _level_cache[key] = grid
    return grid


def light_sprite(radius, color, power=1.8, bands=7):
    radius = max(3, int(radius) // 2 * 2)
    q = tuple(min(255, int(c) // 12 * 12) for c in color[:3])
    key = (radius, q, power, bands)
    hit = _light_cache.get(key)
    if hit is not None:
        return hit
    if len(_light_cache) > 260:
        _light_cache.clear()
    grid = _levels(radius, power, bands)
    d = radius * 2
    s = pygame.Surface((d, d))
    pal = [(q[0] * i // bands, q[1] * i // bands, q[2] * i // bands) for i in range(bands + 1)]
    for y, row in enumerate(grid):
        x = 0
        while x < d:
            v = row[x]
            x2 = x + 1
            while x2 < d and row[x2] == v:
                x2 += 1
            if v:
                s.fill(pal[v], (x, y, x2 - x, 1))
            x = x2
    _light_cache[key] = s
    return s


def add_light(target, cx, cy, radius, color, k=1.0, power=1.8):
    """Cộng ánh sáng (cộng dồn màu) vào lightmap hoặc canvas (bloom)."""
    if k <= 0.02:
        return
    c = (int(color[0] * k), int(color[1] * k), int(color[2] * k))
    s = light_sprite(radius, c, power)
    target.blit(s, (int(cx - s.get_width() // 2), int(cy - s.get_height() // 2)),
                special_flags=pygame.BLEND_RGB_ADD)


_vignette_cache = {}


def get_vignette(w, h, strength=190, inner=0.62, bands=7):
    """Vignette dạng dải (posterize), vẽ 1 lần."""
    key = (w, h, strength, inner, bands)
    hit = _vignette_cache.get(key)
    if hit is not None:
        return hit
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w / 2.0, h / 2.0
    for y in range(h):
        ny = (y + 0.5 - cy) / cy
        prev_a, run_start = None, 0
        for x in range(w + 1):
            if x < w:
                nx = (x + 0.5 - cx) / cx
                d = math.sqrt(nx * nx * 0.8 + ny * ny)
                t = clamp((d - inner) / (1.28 - inner), 0.0, 1.0)
                a = int(strength * (int(t * t * bands) / bands))
            else:
                a = -1
            if a != prev_a:
                if prev_a:
                    s.fill((4, 3, 10, prev_a), (run_start, y, x - run_start, 1))
                prev_a, run_start = a, x
    _vignette_cache[key] = s
    return s


# =====================================================================
# 6. NGỌN LỬA & HẠT
# =====================================================================

FLAME_PAL = ((200, 40, 36), (255, 120, 40), (255, 196, 80), (255, 248, 200))


def draw_flame(surf, cx, by, width, height, t, pal=FLAME_PAL, seed=0):
    """Ngọn lửa pixel: các cột cao thấp nhấp nháy theo thời gian (12 khung/giây)."""
    frame_i = int(t * 12)
    rnd = random.Random(seed * 131 + frame_i)
    half = width / 2.0
    for dx in range(-int(half), int(half) + 1):
        prof = 1.0 - (abs(dx) / (half + 0.6)) ** 1.6
        flick = 0.72 + 0.28 * rnd.random()
        hh = int(height * prof * flick)
        if hh <= 0:
            continue
        x = int(cx + dx)
        for i, c in enumerate(pal):
            layer = int(hh * (1.0 - i * 0.27))
            if i >= 2 and abs(dx) > half * (0.7 if i == 2 else 0.4):
                continue
            if layer > 0:
                surf.fill(c, (x, int(by) - layer, 1, layer))


class ParticleSystem:
    """Hạt vuông pixel. burst() giữ nguyên chữ ký cũ cho tương thích."""

    def __init__(self):
        self.items = []
        self.enabled = True

    def burst(self, x, y, color, n=14, speed=170, size=(2.5, 5.5), life=(0.35, 0.85), gravity=240):
        if not self.enabled:
            return
        speed *= 0.5      # canvas nhỏ gấp đôi nên tốc độ cũng nhỏ đi
        gravity *= 0.5
        size = (size[0] * 0.6, size[1] * 0.6)
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(speed * 0.3, speed)
            lf = random.uniform(*life)
            self.items.append([x, y, math.cos(a) * sp, math.sin(a) * sp, lf, lf,
                               random.uniform(*size), color, gravity])

    def update(self, dt):
        alive = []
        for p in self.items:
            p[4] -= dt
            if p[4] <= 0:
                continue
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += p[8] * dt
            drag = max(0.0, 1 - dt * 1.6)
            p[2] *= drag
            alive.append(p)
        self.items = alive

    def draw(self, surf):
        for x, y, vx, vy, life, maxlife, size, color, g in self.items:
            k = life / maxlife
            r = max(1, int(round(size * (0.4 + 0.6 * k))))
            c = color if k > 0.35 else lerp_color(darken(color, 0.4), color, k / 0.35)
            surf.fill(c, (int(x) - r // 2, int(y) - r // 2, r, r))

    def lights(self):
        return []


class FloatingText:
    def __init__(self, text, x, y, color, size=22, life=0.9, vy=-55):
        self.text, self.x, self.y = text, x, y
        self.color = color
        self.s = 2 if size >= 24 else 1
        self.life, self.vy = life, vy * 0.5
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        self.y += self.vy * dt * (1.0 - min(1.0, self.t / self.life) * 0.7)
        return self.t < self.life

    def draw(self, surf):
        p = self.t / self.life
        alpha = 255 if p < 0.6 else int(255 * (1 - (p - 0.6) / 0.4))
        s = self.s + (1 if p < 0.12 and self.s == 1 else 0)
        text(surf, self.text, s, self.color, (self.x, self.y), "center", alpha=alpha)


# =====================================================================
# 7. MENU DẠNG DANH SÁCH (dùng cho menu chính, tạm dừng, game over)
# =====================================================================

class MenuList:
    """Các mục chữ lớn, mục đang chọn có thanh sáng + ngọn lửa nhỏ hai bên."""

    def __init__(self, items, cx, top, w=210, row_h=26, s=2):
        # items: list of (label, icon, color)
        self.items = items
        self.cx, self.top, self.w, self.row_h, self.s = cx, top, w, row_h, s
        self.selected = 0
        self.hl = [1.0 if i == 0 else 0.0 for i in range(len(items))]
        self.rects = [pygame.Rect(cx - w // 2, top + i * row_h, w, row_h - 2) for i in range(len(items))]
        self.time = 0.0

    def handle_event(self, e, audio=None):
        n = len(self.items)
        if e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos) and self.selected != i:
                    self.selected = i
                    if audio:
                        audio.play("move")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self.selected = i
                    return i
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % n
                if audio:
                    audio.play("move")
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % n
                if audio:
                    audio.play("move")
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.selected
        return None

    def update(self, dt):
        self.time += dt
        for i in range(len(self.items)):
            tgt = 1.0 if i == self.selected else 0.0
            self.hl[i] += (tgt - self.hl[i]) * min(1.0, dt * 16)

    def draw(self, surf):
        t = self.time
        for i, (label, icon, color) in enumerate(self.items):
            r, h = self.rects[i], self.hl[i]
            sel = i == self.selected
            if h > 0.05:
                a = int(200 * h)
                fill_a(surf, r.x, r.y, r.w, r.h, (color[0] // 4, color[1] // 4, color[2] // 4, a))
                rect(surf, darken(color, 0.55), r.x, r.y, r.w, 1)
                rect(surf, darken(color, 0.55), r.x, r.bottom - 1, r.w, 1)
                # vạch sáng chạy
                k = int((t * 60) % (r.w + 40)) - 20
                fill_a(surf, r.x + max(0, k), r.y + 1, min(12, r.w - max(0, k)), r.h - 2, (255, 255, 255, int(24 * h)))
            col = lerp_color(TEXT_DIM, (255, 240, 200) if sel else TEXT, h)
            if sel:
                col = lerp_color(color, (255, 250, 230), 0.55)
            ty = r.centery
            if icon:
                draw_icon(surf, icon, r.x + 20, ty, lerp_color(darken(color, 0.7), color, h), 1)
            text(surf, label.upper(), self.s, col, (self.cx + 6, ty), "center", shadow=1 if sel else 0)
            if h > 0.3:
                bob = int(2 * math.sin(t * 9))
                draw_arrow(surf, r.x + 6 + bob, ty, 1, color, 3)
                draw_arrow(surf, r.right - 7 - bob, ty, -1, color, 3)
