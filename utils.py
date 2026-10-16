import colorsys
import random

from settings import COLS, ROWS


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def hsv_color(h, s=1.0, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def darken(c, f):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


def lighten(c, f):
    return (
        int(c[0] + (255 - c[0]) * f),
        int(c[1] + (255 - c[1]) * f),
        int(c[2] + (255 - c[2]) * f),
    )


def mul_color(c, k):
    """Nhân màu với k (có thể > 1), tự cắt về 0..255."""
    return (int(clamp(c[0] * k, 0, 255)), int(clamp(c[1] * k, 0, 255)), int(clamp(c[2] * k, 0, 255)))


def ease_out_cubic(t):
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3


def ease_out_back(t):
    t = clamp(t, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def pick_free_cell(occupied):
    """Chọn 1 ô trống ngẫu nhiên (occupied là set các tuple (x, y))."""
    for _ in range(80):
        c = (random.randrange(COLS), random.randrange(ROWS))
        if c not in occupied:
            return c
    free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in occupied]
    return random.choice(free) if free else (0, 0)
