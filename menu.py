import math
import random

import pygame

import ui
import sprites
from settings import *
from utils import *
from ui import MenuList, text, text_w, panel, rect, px
from snake import Snake, draw_preview

FIRE7 = ((255, 250, 214), (255, 228, 134), (255, 194, 84), (255, 154, 58), (236, 104, 42), (190, 58, 42), (132, 34, 46))
GOLD7 = ((255, 246, 200), (255, 232, 150), (246, 208, 110), (232, 180, 84), (204, 146, 66), (160, 106, 52), (110, 70, 44))
ICE7 = ((235, 252, 255), (190, 238, 255), (150, 220, 255), (110, 196, 250), (84, 166, 230), (62, 130, 200), (46, 94, 160))


def _footer(screen, txt, y=HEIGHT - 12):
    text(screen, txt, 1, TEXT_DIM, (WIDTH // 2, y), "center")


def _title(screen, txt, y=26, pal=GOLD7):
    r = text(screen, txt, 3, pal, (WIDTH // 2, y), "midtop", shadow=2)
    rect(screen, INK, WIDTH // 2 - 41, r.bottom + 6, 82, 4)
    rect(screen, GOLD, WIDTH // 2 - 40, r.bottom + 7, 80, 2)
    return r


# =========================
# RẮN BIỂU DIỄN Ở MENU
# =========================

class DemoSnake:
    """Rắn tự chạy trên dải sàn dưới đáy menu, săn táo - cho menu có sức sống."""
    ROW0, ROW1 = 33, 37
    DELAY = 0.12

    def __init__(self):
        self.s = Snake()
        self.s.pos = [[x, 35] for x in range(2, 9)]
        self.s.direction = "right"
        self.apple = None
        self.acc = 0.0
        self._new_apple()

    def _new_apple(self):
        body = {tuple(p) for p in self.s.pos}
        for _ in range(40):
            c = (random.randint(4, COLS - 5), random.randint(self.ROW0, self.ROW1))
            if c not in body:
                self.apple = c
                return
        self.apple = (10, 35)

    def _choose(self):
        from snake import DIR_VEC, OPPOSITE
        hx, hy = self.s.pos[-1]
        ax, ay = self.apple
        body = {tuple(p) for p in self.s.pos[1:]}
        cands = []
        for d, (dx, dy) in DIR_VEC.items():
            if d == OPPOSITE[self.s.direction]:
                continue
            nx, ny = (hx + dx) % COLS, hy + dy
            if ny < self.ROW0 or ny > self.ROW1 or (nx, ny) in body:
                continue
            cands.append((abs(nx - ax) + abs(ny - ay) + (0.3 if d != self.s.direction else 0), d))
        if cands:
            self.s.direction = min(cands)[1]

    def update(self, dt):
        self.acc += dt
        while self.acc >= self.DELAY:
            self.acc -= self.DELAY
            self._choose()
            nh = self.s.get_new_head()
            self.s.grow(0)
            self.s.move(nh)
            if tuple(nh) == self.apple:
                self.s.grow(2)
                self._new_apple()

    def draw(self, screen, t, skin):
        frac = ease_out_cubic(min(1.0, self.acc / (self.DELAY * 0.6)))
        ax, ay = self.apple
        sprites.draw_apple(screen, ax * SIZE + 5, ay * SIZE + 5, SIZE, t)
        ui.add_light(screen, ax * SIZE + 5, ay * SIZE + 5, 20, (200, 50, 50), 0.5)
        self.s.draw(screen, t, skin, frac=frac)
        hx, hy = self.s.head_pixel(frac)
        ui.add_light(screen, hx, hy, 26, darken(skin["glow"], 0.7), 0.5)


# =========================
# MENU CHÍNH
# =========================

class MenuScene:

    ITEMS = [
        ("Chơi game", "play", GOLD, "play"),
        ("Cách chơi", "help", INFO, "help"),
        ("Cài đặt", "settings", (190, 150, 255), "settings"),
        ("Credit", "credits", WARN, "credits"),
        ("Thoát", "quit", BAD, "quit"),
    ]

    def __init__(self, app):
        self.app = app
        self.time = 0.0
        self.group = MenuList([(l, i, c) for l, i, c, _ in self.ITEMS], WIDTH // 2, 126, w=206, row_h=26, s=2)
        self.demo = DemoSnake()

    def handle_event(self, e):
        idx = self.group.handle_event(e, self.app.audio)
        if idx is not None:
            self.activate(idx)

    def activate(self, idx):
        action = self.ITEMS[idx][3]
        self.app.audio.play("select")
        if action == "quit":
            self.app.running = False
        else:
            self.app.change_scene(action)

    def update(self, dt):
        self.time += dt
        self.app.background.update(dt)
        self.group.update(dt)
        self.demo.update(dt)

    def draw(self, screen):
        t = self.time
        self.app.background.draw(screen)
        self.draw_title(screen)
        self.group.draw(screen)
        skin = SKINS[self.app.config.skin % len(SKINS)]
        self.demo.draw(screen, t, skin)
        ui.stat_pill(screen, WIDTH - 92, 6, 86, 33, "KỶ LỤC", self.app.config.high_score, WARN)
        text(screen, f"v{VERSION}", 1, TEXT_DIM, (6, HEIGHT - 10), "midleft")
        _footer(screen, "W/S HOẶC LÊN/XUỐNG: CHỌN  ·  ENTER: XÁC NHẬN  ·  F11: TOÀN MÀN HÌNH", y=300)

    def draw_title(self, screen):
        t = self.time
        s = 7
        letters = GAME_TITLE
        pitch = 5 * s + 6
        total = pitch * len(letters) - 6
        x0 = WIDTH // 2 - total // 2
        y0 = 22
        ui.add_light(screen, WIDTH // 2, y0 + 26, 110, (255, 120, 40), 0.28 + 0.06 * math.sin(t * 2))
        for i, ch in enumerate(letters):
            wave = int(round(math.sin(t * 2.6 + i * 0.9) * 2))
            x = x0 + i * pitch
            text(screen, ch, s, FIRE7, (x, y0 + wave), "topleft", outline=INK, shadow=3)
        # tia sáng quét ngang qua logo
        k = int((t * 70) % (total + 120)) - 60
        for j in range(3):
            ui.fill_a(screen, x0 + k + j * 3, y0, 2, 7 * s, (255, 255, 255, 30 - j * 8))
        text(screen, "SĂN TÁO  ·  NÉ TƯỜNG  ·  THỬ VẬN MAY", 1, TEXT_DIM, (WIDTH // 2, y0 + 7 * s + 14), "midtop")


# =========================
# CÁCH CHƠI
# =========================

SKILLS_COL = {"dash": (255, 190, 70), "teleport": (190, 140, 255), "shield": (110, 200, 255)}


class HelpScene:

    PAGES = 2

    def __init__(self, app):
        self.app = app
        self.time = 0.0
        self.page = 0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.back()
            elif e.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.flip(1)
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self.flip(-1)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.flip(1)

    def flip(self, d):
        n = self.page + d
        if n < 0:
            return
        if n >= self.PAGES:
            self.back()
            return
        self.page = n
        self.app.audio.play("select")

    def back(self):
        self.app.audio.play("back")
        self.app.change_scene("menu")

    def update(self, dt):
        self.time += dt
        self.app.background.update(dt)

    def draw(self, screen):
        t = self.time
        self.app.background.draw(screen, glow=False, ground=False)
        _title(screen, "CÁCH CHƠI" if self.page == 0 else "ĐIỀU KHIỂN", y=14, pal=ICE7)
        px0, py0, pw, ph = 22, 56, WIDTH - 44, 276
        panel(screen, (px0, py0, pw, ph), accent=INFO)
        if self.page == 0:
            self.draw_items(screen, px0, py0, pw, t)
        else:
            self.draw_controls(screen, px0, py0, pw, t)
        for i in range(self.PAGES):
            c = GOLD if i == self.page else STONE_3
            rect(screen, INK, WIDTH // 2 - 14 + i * 16, 340, 10, 6)
            rect(screen, c, WIDTH // 2 - 13 + i * 16, 341, 8, 4)
        _footer(screen, "TRÁI/PHẢI: ĐỔI TRANG  ·  ESC: QUAY LẠI  ·  P/ESC KHI CHƠI: TẠM DỪNG", y=366)

    def draw_items(self, screen, px0, py0, pw, t):
        skin = SKINS[self.app.config.skin % len(SKINS)]
        rows = [
            ("ĐIỀU KHIỂN RẮN", "W A S D hoặc phím mũi tên. Rắn đi xuyên qua mép màn hình.", "snake"),
            ("QUẢ TÁO", "+1 điểm, +1 XP, rắn dài thêm một ô.", "apple"),
            ("CẦU NĂNG LƯỢNG", "Tăng tốc hoặc làm chậm rắn trong 5 giây.", "effect"),
            ("HỘP MAY RỦI", "Quay vòng may rủi: có thể +100 điểm... hoặc mất sạch!", "gamble"),
            ("VẬT CẢN", "Tường, thùng gỗ, mảnh vỡ: chạm vào là thua (Lướt có thể phá thùng).", "wall"),
            ("QUÁI VẬT", "Thấy rắn là lao tới cắt đôi, phần đuôi hóa mảnh vỡ nguy hiểm.", "enemy"),
            ("CẤP ĐỘ", "Ăn để lên cấp, chọn nâng cấp kỹ năng. Mỗi 3 cấp đổi khu vực, khó hơn.", "xp"),
        ]
        for i, (title, desc, icon) in enumerate(rows):
            y = py0 + 8 + i * 37
            ui.fill_a(screen, px0 + 8, y, pw - 16, 34, (30, 26, 52, 150))
            rect(screen, STONE_2, px0 + 8, y + 33, pw - 16, 1)
            cx, cy = px0 + 36, y + 17
            if icon == "snake":
                draw_preview(screen, cx, cy, skin, 3, t)
            elif icon == "apple":
                sprites.draw_apple(screen, cx, cy, 10, t, 1.4)
            elif icon == "effect":
                ui.add_light(screen, cx, cy, 20, (255, 50, 140), 0.8)
                sprites.draw_effect_orb(screen, cx, cy, 10, t, 1.4)
            elif icon == "gamble":
                ui.add_light(screen, cx, cy, 20, hsv_color(t * 0.6, 0.8, 1.0), 0.8)
                sprites.draw_gamble(screen, cx, cy, 10, t, 1.4)
            elif icon == "wall":
                sprites.draw_brick_icon(screen, cx - 8, cy)
                sprites.draw_crate(screen, cx + 2, cy - 5, 1.0)
            elif icon == "enemy":
                sprites.draw_enemy(screen, cx, cy, 12, t, "wander")
            elif icon == "xp":
                ui.bar(screen, cx - 14, cy - 3, 28, 6, 0.5 + 0.4 * math.sin(t * 2), TEAL)
            text(screen, title, 1, GOLD, (px0 + 70, y + 5))
            ui.text_wrapped(screen, desc.upper(), 1, TEXT, px0 + 70, y + 17, pw - 90, line_h=10)

    def draw_controls(self, screen, px0, py0, pw, t):
        rows = [
            (("W", "A", "S", "D"), "ĐIỀU KHIỂN RẮN (HOẶC PHÍM MŨI TÊN)", None),
            (("SPACE",), "LƯỚT: PHÁ VẬT CẢN, BẤT TỬ KHI LƯỚT", "dash"),
            (("E",), "DỊCH CHUYỂN TỚI CON TRỎ (CHUỘT PHẢI CŨNG ĐƯỢC)", "teleport"),
            (("Q",), "KHIÊN: CHẶN ĐÒN TẤN CÔNG TRONG THỜI GIAN NGẮN", "shield"),
            (("P",), "TẠM DỪNG (ESC CŨNG ĐƯỢC)", None),
            (("F11",), "BẬT / TẮT TOÀN MÀN HÌNH", None),
        ]
        for i, (keys, desc, icon) in enumerate(rows):
            y = py0 + 12 + i * 34
            ui.fill_a(screen, px0 + 8, y, pw - 16, 30, (30, 26, 52, 150))
            kx = px0 + 22
            for k in keys:
                r = ui.key_cap(screen, k, kx + max(5, (text_w(k, 1) + 6) // 2), y + 15)
                kx = r.right + 4
            text(screen, desc, 1, TEXT, (px0 + 120, y + 15), "midleft")
            if icon:
                ui.draw_icon(screen, icon, px0 + pw - 28, y + 15, SKILLS_COL[icon], 2)
        ui.text_wrapped(screen, "MẸO: MỖI LẦN LÊN CẤP BẠN CHỌN 1 KỸ NĂNG ĐỂ NÂNG CẤP (TỐI ĐA CẤP 3). "
                        "KHIÊN VÀ LƯỚT SẼ CỨU BẠN KHỎI QUÁI VẬT.", 1, TEXT_DIM, px0 + 16, py0 + 222, pw - 32,
                        line_h=11, anchor="center")


# =========================
# CÀI ĐẶT
# =========================

class SettingsScene:

    ROW_H, GAP = 21, 3

    def __init__(self, app):
        self.app = app
        self.time = 0.0
        self.sel = 0
        self.drag_row = None
        cfg = app.config
        self.rows = [
            {"key": "difficulty", "label": "Độ khó", "type": "choice", "choices": [n.upper() for n in DIFFICULTY_NAMES]},
            {"key": "volume", "label": "Âm thanh", "type": "slider", "max": 10},
            {"key": "music", "label": "Nhạc nền", "type": "slider", "max": 10},
            {"key": "skin", "label": "Màu rắn", "type": "choice", "choices": [s["name"].upper() for s in SKINS]},
            {"key": "lighting", "label": "Ánh sáng động", "type": "toggle"},
            {"key": "particles", "label": "Hiệu ứng hạt", "type": "toggle"},
            {"key": "shake", "label": "Rung màn hình", "type": "toggle"},
            {"key": "crt", "label": "Hiệu ứng CRT", "type": "toggle"},
            {"key": "grid", "label": "Hiện lưới", "type": "toggle"},
            {"key": "fullscreen", "label": "Toàn màn hình", "type": "toggle"},
            {"key": None, "label": "Quay lại", "type": "back"},
        ]
        px0, top = WIDTH // 2 - 190, 60
        for i, row in enumerate(self.rows):
            row["rect"] = pygame.Rect(px0, top + i * (self.ROW_H + self.GAP), 380, self.ROW_H)
            row["hl"] = 1.0 if i == 0 else 0.0
            row["anim"] = 1.0 if (row["type"] == "toggle" and getattr(cfg, row["key"])) else 0.0

    def track_rect(self, row):
        r = row["rect"]
        return pygame.Rect(r.right - 150, r.centery - 3, 109, 7)

    def ctrl_rect(self, row):
        r = row["rect"]
        return pygame.Rect(r.right - 170, r.y, 168, r.h)

    def change(self, i, delta):
        row = self.rows[i]
        cfg = self.app.config
        key, typ = row["key"], row["type"]
        if typ == "choice":
            cfg.set(key, (getattr(cfg, key) + delta) % len(row["choices"]))
            self.app.audio.play("move")
        elif typ == "slider":
            cfg.set(key, int(clamp(getattr(cfg, key) + delta, 0, row["max"])))
            if key == "music":
                self.app.audio.apply_music_volume()
            else:
                self.app.audio.play("eat")
        elif typ == "toggle":
            cfg.set(key, not getattr(cfg, key))
            self.app.audio.play("select")
            if key == "fullscreen":
                self.app.apply_display()

    def set_slider(self, i, mx):
        row = self.rows[i]
        tr = self.track_rect(row)
        v = int(round(clamp((mx - tr.x) / tr.w, 0, 1) * row["max"]))
        if v != getattr(self.app.config, row["key"]):
            self.app.config.set(row["key"], v)
            if row["key"] == "music":
                self.app.audio.apply_music_volume()
            else:
                self.app.audio.play("move")

    def back(self):
        self.app.config.save()
        self.app.audio.play("back")
        self.app.change_scene("menu")

    def handle_event(self, e):
        n = len(self.rows)
        if e.type == pygame.KEYDOWN:
            k = e.key
            if k == pygame.K_ESCAPE:
                self.back()
            elif k in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % n
                self.app.audio.play("move")
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % n
                self.app.audio.play("move")
            elif k in (pygame.K_LEFT, pygame.K_a):
                self.change(self.sel, -1)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.change(self.sel, +1)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.rows[self.sel]["type"] == "back":
                    self.back()
                else:
                    self.change(self.sel, +1)
        elif e.type == pygame.MOUSEMOTION:
            for i, row in enumerate(self.rows):
                if row["rect"].collidepoint(e.pos) and self.sel != i:
                    self.sel = i
                    self.app.audio.play("move")
            if self.drag_row is not None:
                self.set_slider(self.drag_row, e.pos[0])
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, row in enumerate(self.rows):
                if not row["rect"].collidepoint(e.pos):
                    continue
                self.sel = i
                typ = row["type"]
                if typ == "back":
                    self.back()
                elif typ == "toggle":
                    self.change(i, +1)
                elif typ == "choice":
                    cr = self.ctrl_rect(row)
                    if cr.collidepoint(e.pos):
                        self.change(i, -1 if e.pos[0] < cr.centerx else +1)
                elif typ == "slider":
                    if self.track_rect(row).inflate(10, 14).collidepoint(e.pos):
                        self.drag_row = i
                        self.set_slider(i, e.pos[0])
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag_row = None

    def update(self, dt):
        self.time += dt
        self.app.background.update(dt)
        cfg = self.app.config
        for i, row in enumerate(self.rows):
            row["hl"] += ((1.0 if i == self.sel else 0.0) - row["hl"]) * min(1.0, dt * 14)
            if row["type"] == "toggle":
                target = 1.0 if getattr(cfg, row["key"]) else 0.0
                row["anim"] += (target - row["anim"]) * min(1.0, dt * 16)

    def draw(self, screen):
        t = self.time
        cfg = self.app.config
        self.app.background.draw(screen, glow=False, ground=False)
        _title(screen, "CÀI ĐẶT", y=14, pal=ICE7)
        panel(screen, (WIDTH // 2 - 200, 50, 400, 11 * (self.ROW_H + self.GAP) + 16), accent=INFO)
        for i, row in enumerate(self.rows):
            r, hl = row["rect"], row["hl"]
            if hl > 0.05:
                ui.fill_a(screen, r.x, r.y, r.w, r.h, (70, 52, 24, int(190 * hl)))
                rect(screen, GOLD, r.x, r.y, r.w, 1)
                rect(screen, darken(GOLD, 0.5), r.x, r.bottom - 1, r.w, 1)
                ui.draw_arrow(screen, r.x + 5 + int(1.5 * math.sin(t * 9)), r.centery, 1, GOLD, 3)
            else:
                ui.fill_a(screen, r.x, r.y, r.w, r.h, (28, 24, 46, 110))
            typ = row["type"]
            lab = lerp_color(TEXT_DIM, (255, 240, 200), hl)
            if typ == "back":
                text(screen, row["label"].upper(), 2, lerp_color(TEXT, GOLD, hl), r.center, "center")
                continue
            text(screen, row["label"].upper(), 1, lab, (r.x + 16, r.centery), "midleft")
            arrow = lerp_color(TEXT_DIM, GOLD, hl)

            if typ == "choice":
                cr = self.ctrl_rect(row)
                val = getattr(cfg, row["key"])
                name = row["choices"][val % len(row["choices"])]
                cy = r.centery
                ui.draw_arrow(screen, cr.x + 6, cy, -1, arrow, 3)
                ui.draw_arrow(screen, cr.right - 6, cy, 1, arrow, 3)
                text(screen, name, 1, (255, 255, 255), (cr.centerx, cy), "center")
                if row["key"] == "skin":
                    draw_preview(screen, r.x + 120, cy, SKINS[val % len(SKINS)], 5, t)
            elif typ == "slider":
                tr = self.track_rect(row)
                v = getattr(cfg, row["key"])
                for k in range(row["max"]):
                    bx = tr.x + k * 11
                    on = k < v
                    rect(screen, INK, bx - 1, tr.y - 1, 11, tr.h + 2)
                    rect(screen, (TEAL if on else STONE_2), bx, tr.y, 9, tr.h)
                    if on:
                        rect(screen, lighten(TEAL, 0.5), bx, tr.y, 9, 2)
                text(screen, f"{v * 10}%", 1, (255, 255, 255), (r.right - 22, r.centery), "center")
            elif typ == "toggle":
                a = row["anim"]
                sw = pygame.Rect(r.right - 46, r.centery - 5, 28, 11)
                rect(screen, INK, sw.x - 1, sw.y - 1, sw.w + 2, sw.h + 2)
                rect(screen, lerp_color(STONE_2, (40, 160, 100), a), sw.x, sw.y, sw.w, sw.h)
                kx = sw.x + 1 + int(16 * a)
                rect(screen, (255, 255, 255), kx, sw.y + 1, 9, 9)
                rect(screen, (196, 190, 210), kx, sw.y + 8, 9, 2)
                text(screen, "BẬT" if a > 0.5 else "TẮT", 1, lerp_color(TEXT_DIM, GOOD, a), (sw.x - 8, sw.centery), "midright")
        _footer(screen, "LÊN/XUỐNG: CHỌN  ·  TRÁI/PHẢI: THAY ĐỔI  ·  ESC: QUAY LẠI", y=370)


# =========================
# CREDIT
# =========================

class CreditsScene:

    LINES = [
        ("SNAKE", "big"), ("Phiên bản đồ họa pixel indie", "sub"), ("", "gap"),
        ("THIẾT KẾ & LẬP TRÌNH", "h"), (AUTHOR_NAME, "p"), ("", "gap"),
        ("NÂNG CẤP ĐỒ HỌA, UI/UX", "h"), ("Claude  ·  Anthropic", "p"), ("", "gap"),
        ("CÔNG NGHỆ", "h"), ("Python", "p"), ("Pygame", "p"), ("", "gap"),
        ("HÌNH ẢNH & ÂM THANH", "h"), ("Pixel art, font, ánh sáng: vẽ hoàn toàn bằng code", "p"),
        ("Nhạc nền, âm thanh: tổng hợp bằng code", "p"), ("Không dùng file ảnh hay âm thanh ngoài", "p"), ("", "gap"),
        ("CẢM ƠN BẠN ĐÃ CHƠI!", "big2"),
    ]
    H = {"big": 64, "big2": 40, "sub": 26, "h": 24, "p": 20, "gap": 20}

    def __init__(self, app):
        self.app = app
        self.time = 0.0
        self.panel = pygame.Rect(WIDTH // 2 - 190, 66, 380, 270)
        self.scroll = 0.0
        self.total = sum(self.H[s] for _, s in self.LINES)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER,
                                                  pygame.K_SPACE, pygame.K_BACKSPACE):
            self.back()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.back()

    def back(self):
        self.app.audio.play("back")
        self.app.change_scene("menu")

    def update(self, dt):
        self.time += dt
        self.app.background.update(dt)
        self.scroll += dt * 26
        if self.scroll > self.total + self.panel.h:
            self.scroll = 0.0

    def draw(self, screen):
        t = self.time
        self.app.background.draw(screen, glow=False, ground=False)
        _title(screen, "CREDIT", y=14)
        panel(screen, self.panel, accent=WARN)
        screen.set_clip(self.panel.inflate(-8, -12))
        y = self.panel.bottom - self.scroll
        cx = self.panel.centerx
        for txt, style in self.LINES:
            h = self.H[style]
            if -40 < y < self.panel.bottom + 10 and style != "gap":
                if style == "big":
                    text(screen, txt, 6, FIRE7, (cx, y), "midtop", shadow=2)
                elif style == "big2":
                    text(screen, txt, 2, GOLD7, (cx, y + 6), "midtop", shadow=1)
                elif style == "sub":
                    text(screen, txt.upper(), 1, TEXT_DIM, (cx, y + 4), "midtop")
                elif style == "h":
                    text(screen, txt, 1, GOLD, (cx, y + 8), "midtop")
                else:
                    text(screen, txt.upper(), 1, (255, 255, 255), (cx, y + 6), "midtop")
            y += h
        screen.set_clip(None)
        _footer(screen, "NHẤN ESC HOẶC BẤM CHUỘT ĐỂ QUAY LẠI", y=366)
