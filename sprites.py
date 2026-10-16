import math

import pygame

import ui
from settings import *
from utils import hsv_color, darken, lighten, lerp_color

_cache = {}


def _surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _scaled(img, scale):
    if abs(scale - 1.0) < 0.05:
        return img
    w = max(2, int(round(img.get_width() * scale)))
    key = (id(img), w)
    hit = _cache.get(key)
    if hit is None:
        hit = _cache[key] = pygame.transform.scale(img, (w, w))
    return hit


def _blob(S, cx, cy, rx, ry):
    """Tập ô nằm trong hình elip."""
    inside = set()
    for y in range(S):
        for x in range(S):
            dx, dy = (x - cx) / rx, (y - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                inside.add((x, y))
    return inside


def _shade_blob(img, inside, cx, cy, rr, pal, ink):
    """Tô hình cầu có viền mực + 4 mức sáng tối (nguồn sáng ở trên-trái)."""
    for (x, y) in inside:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            img.fill(ink, (x, y, 1, 1))
            continue
        s = ((x - cx) * -0.55 + (y - cy) * -0.8) / rr
        c = pal[3] if s > 0.55 else pal[2] if s > 0.0 else pal[1] if s > -0.5 else pal[0]
        img.fill(c, (x, y, 1, 1))


# =====================================================================
# TÁO
# =====================================================================

def apple_img():
    hit = _cache.get("apple")
    if hit:
        return hit
    S = 10
    img = _surf(S, S)
    cx, cy = 4.5, 5.6
    inside = _blob(S, cx, cy, 4.7, 4.3)
    inside.discard((4, 1))
    inside.discard((5, 1))
    _shade_blob(img, inside, cx, cy, 4.6, [(140, 20, 46), (196, 36, 56), (232, 62, 70), (255, 132, 122)], (46, 6, 24))
    img.fill((255, 235, 225), (2, 4, 1, 1))
    img.fill((255, 235, 225), (3, 3, 1, 1))
    img.fill((46, 6, 24), (5, 1, 1, 1))
    img.fill((120, 76, 40), (5, 0, 1, 2))
    for (x, y, c) in ((6, 1, (70, 190, 90)), (7, 0, (96, 220, 110)), (7, 1, (50, 150, 70)), (8, 0, (70, 190, 90))):
        img.fill(c, (x, y, 1, 1))
    _cache["apple"] = img
    return img


def draw_apple(surf, cx, cy, size=10, t=0.0, scale=1.0):
    """Vẽ táo tại tâm (cx, cy). size giữ cho tương thích (bỏ qua)."""
    if scale <= 0.05:
        return
    img = _scaled(apple_img(), scale)
    bob = int(round(math.sin(t * 3.2) * 1.0))
    surf.blit(img, (int(cx - img.get_width() // 2), int(cy - img.get_height() // 2 + bob)))


# =====================================================================
# CẦU NĂNG LƯỢNG (tia chớp)
# =====================================================================

def orb_img(frame=0):
    key = ("orb", frame)
    hit = _cache.get(key)
    if hit:
        return hit
    S = 10
    img = _surf(S, S)
    inside = _blob(S, 4.5, 4.5, 4.7, 4.7)
    pal = [(110, 14, 80), (176, 22, 104), (222, 44, 128), (255, 130, 190)]
    if frame:
        pal = [lighten(c, 0.12) for c in pal]
    _shade_blob(img, inside, 4.5, 4.5, 4.7, pal, (50, 6, 38))
    for x, y in ((5, 2), (6, 2), (4, 3), (5, 3), (3, 4), (4, 4), (5, 4), (6, 4), (5, 5), (6, 5), (4, 6), (5, 6),
                 (3, 7), (4, 7)):
        img.fill((255, 255, 255), (x, y, 1, 1))
    _cache[key] = img
    return img


def draw_effect_orb(surf, cx, cy, size=10, t=0.0, scale=1.0):
    if scale <= 0.05:
        return
    img = _scaled(orb_img(int(t * 6) % 2), scale)
    bob = int(round(math.sin(t * 4.2) * 1.0))
    surf.blit(img, (int(cx - img.get_width() // 2), int(cy - img.get_height() // 2 + bob)))


# =====================================================================
# HỘP MAY RỦI (khối rune đổi màu)
# =====================================================================

_Q = ((3, 2), (4, 2), (5, 2), (2, 3), (6, 3), (5, 4), (4, 5), (4, 7), (3, 3))
_QM = ((3, 2), (4, 2), (5, 2), (2, 3), (6, 3), (6, 4), (5, 5), (4, 6), (4, 8))


def gamble_img(hue_step):
    key = ("gamble", hue_step)
    hit = _cache.get(key)
    if hit:
        return hit
    S = 10
    col = hsv_color(hue_step / 16.0, 0.75, 1.0)
    img = _surf(S, S)
    ink = darken(col, 0.28)
    img.fill(ink, (1, 0, 8, 10))
    img.fill(ink, (0, 1, 10, 8))
    img.fill(darken(col, 0.62), (1, 1, 8, 8))
    img.fill(col, (1, 1, 7, 7))
    img.fill(lighten(col, 0.5), (2, 1, 5, 1))
    img.fill(lighten(col, 0.5), (1, 2, 1, 4))
    for x, y in _QM:
        img.fill((255, 255, 255), (x + 0, y, 1, 1))
    _cache[key] = img
    return img


def draw_gamble(surf, cx, cy, size=10, t=0.0, scale=1.0):
    if scale <= 0.05:
        return
    img = _scaled(gamble_img(int(t * 5) % 16), scale)
    bob = int(round(math.sin(t * 3.7 + 1) * 1.0))
    surf.blit(img, (int(cx - img.get_width() // 2), int(cy - img.get_height() // 2 + bob)))


# =====================================================================
# THÙNG GỖ / MẢNH VỠ
# =====================================================================

def crate_img():
    hit = _cache.get("crate")
    if hit:
        return hit
    img = _surf(10, 10)
    ink, base, dark, light, nail = (36, 20, 10), (172, 124, 66), (112, 74, 36), (212, 164, 98), (236, 226, 206)
    img.fill(ink, (0, 0, 10, 10))
    img.fill(dark, (1, 1, 8, 8))
    img.fill(base, (2, 2, 6, 6))
    img.fill(light, (1, 1, 8, 1))
    img.fill(light, (1, 1, 1, 8))
    for i in range(2, 8):
        img.fill(dark, (i, i, 1, 1))
        img.fill(dark, (9 - i, i, 1, 1))
        if i < 7:
            img.fill(light, (i, i - 1, 1, 1)) if i - 1 >= 2 else None
    for x, y in ((1, 1), (8, 1), (1, 8), (8, 8)):
        img.fill(nail, (x, y, 1, 1))
    _cache["crate"] = img
    return img


def draw_crate(surf, x, y, k=1.0):
    img = crate_img()
    if k < 0.98:
        inset = int((1 - k) * 5)
        w = max(2, 10 - inset * 2)
        img = _scaled(img, w / 10.0)
        surf.blit(img, (x + (10 - w) // 2, y + (10 - w) // 2))
    else:
        surf.blit(img, (x, y))


def debris_img(color):
    key = ("debris", color)
    hit = _cache.get(key)
    if hit:
        return hit
    img = _surf(10, 10)
    ink = (24, 6, 12)
    body = darken(color, 0.5)
    img.fill(ink, (1, 0, 8, 10))
    img.fill(ink, (0, 1, 10, 8))
    img.fill(body, (1, 1, 8, 8))
    img.fill(lighten(body, 0.2), (2, 1, 5, 1))
    red = (232, 64, 70)
    for i in range(2, 8):
        img.fill(red, (i, i, 1, 1))
        img.fill(red, (9 - i, i, 1, 1))
    _cache[key] = img
    return img


def draw_debris(surf, x, y, color, life, t):
    if life < 1.5 and int(life * 10) % 2 == 0:
        return
    surf.blit(debris_img(tuple(color)), (x, y))


# =====================================================================
# ĐUỐC TƯỜNG
# =====================================================================

def draw_torch(surf, cx, cy, t, pal=ui.FLAME_PAL, seed=0):
    """Giá đuốc sắt + ngọn lửa. (cx, cy) = tâm ô."""
    ui.rect(surf, INK, cx - 2, cy - 1, 5, 9)
    ui.rect(surf, (70, 60, 78), cx - 1, cy, 3, 7)
    ui.rect(surf, (110, 98, 120), cx - 1, cy, 1, 7)
    ui.rect(surf, INK, cx - 3, cy - 2, 7, 3)
    ui.rect(surf, (96, 84, 104), cx - 2, cy - 2, 5, 1)
    ui.draw_flame(surf, cx, cy - 2, 6, 9, t, pal, seed)


# =====================================================================
# QUÁI VẬT (cầu gai)
# =====================================================================

def draw_enemy(surf, cx, cy, size=12, t=0.0, state="wander", prog=0.0):
    cx, cy = int(cx), int(cy)
    if state == "spawning":
        r = int(16 - 12 * prog)
        ui.ring(surf, (255, 70, 100), cx, cy, max(2, r))
        if r > 6:
            ui.ring(surf, (140, 30, 80), cx, cy, r - 4)
        ui.disc(surf, (140, 30, 90), cx, cy, max(1, int(3 * prog)))
        return
    charging = state == "charge"
    aim = state == "aim"
    stunned = state == "stunned"
    flash = aim and int(t * 14) % 2 == 0
    rot = t * (7.0 if charging else 1.5)
    spike = (255, 244, 130) if flash else (130, 130, 150) if stunned else (255, 74, 92)
    spike_hi = (255, 255, 220) if flash else (190, 190, 205) if stunned else (255, 170, 150)
    reach = 9.5 if charging else 8.4
    for k in range(8):
        a = rot + k * math.tau / 8
        c, s = math.cos(a), math.sin(a)
        bx, by = cx + c * 3.5, cy + s * 3.5
        tx, ty = cx + c * reach, cy + s * reach
        ui.line(surf, INK, bx + 1 if c > 0 else bx - 1, by, tx, ty)
        ui.line(surf, spike, bx, by, tx, ty)
        ui.px(surf, spike_hi, tx, ty)
    body = (255, 70, 70) if flash else (86, 86, 104) if stunned else (96, 26, 134)
    body_hi = lighten(body, 0.25)
    ui.disc(surf, INK, cx, cy, 5)
    ui.disc(surf, body, cx, cy, 4)
    ui.rect(surf, body_hi, cx - 2, cy - 3, 4, 1)
    ui.rect(surf, body_hi, cx - 3, cy - 2, 1, 2)
    for sgn in (-1, 1):
        ex, ey = cx + sgn * 2, cy - 1
        if stunned:
            ui.px(surf, (255, 255, 255), ex - 1, ey - 1)
            ui.px(surf, (255, 255, 255), ex, ey)
            ui.px(surf, (255, 255, 255), ex - 1, ey)
            ui.px(surf, (255, 255, 255), ex, ey - 1)
        else:
            ui.rect(surf, (255, 255, 255), ex - 1, ey - 1, 2, 3)
            ui.rect(surf, (255, 40, 50), ex - (1 if sgn < 0 else 0), ey, 1, 1)
            ui.px(surf, INK, ex - 1 + (0 if sgn < 0 else 1), ey - 2)
    if not stunned:
        ui.line(surf, INK, cx - 3, cy - 3, cx - 1, cy - 2)
        ui.line(surf, INK, cx + 3, cy - 3, cx + 1, cy - 2)
    else:
        for i in range(3):
            a = t * 4 + i * math.tau / 3
            ui.px(surf, (255, 230, 100), cx + math.cos(a) * 7, cy - 8 + math.sin(a) * 2)


def draw_brick_icon(surf, cx, cy, size=10):
    r = pygame.Rect(0, 0, 10, 10)
    r.center = (int(cx), int(cy))
    ui.rect(surf, INK, r.x - 1, r.y - 1, 12, 12)
    ui.rect(surf, (96, 78, 112), r.x, r.y, 10, 10)
    ui.rect(surf, (70, 140, 60), r.x, r.y, 10, 2)
    ui.rect(surf, (56, 44, 70), r.x, r.y + 5, 10, 1)
    ui.rect(surf, (56, 44, 70), r.x + 4, r.y + 2, 1, 3)
    ui.rect(surf, (56, 44, 70), r.x + 2, r.y + 6, 1, 4)
    ui.rect(surf, (56, 44, 70), r.x + 7, r.y + 6, 1, 4)


def draw_mini_snake(surf, cx, cy, skin, length=5, r=8, t=0.0):
    import snake as snake_mod
    snake_mod.draw_preview(surf, cx, cy, skin, length, t)
