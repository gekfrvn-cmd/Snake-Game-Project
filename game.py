import random

import pygame

import ui
from settings import *
from config import Config
from audio import Audio
from background import Background
from menu import MenuScene, HelpScene, SettingsScene, CreditsScene
from play import PlayScene

SCENES = {
    "menu": MenuScene,
    "help": HelpScene,
    "settings": SettingsScene,
    "credits": CreditsScene,
    "play": PlayScene,
}

BLOCK = 15


class Game:
    """Vòng lặp chính + chuyển cảnh kiểu tan khối pixel."""

    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()

        self.config = Config()
        self.running = True
        self.screen = None
        self.apply_display()
        pygame.display.set_caption("Snake Game")
        self._set_icon()
        try:
            pygame.mouse.set_visible(False)
        except Exception:
            pass

        self.clock = pygame.time.Clock()
        self.audio = Audio(self.config)
        self.background = Background(WIDTH, HEIGHT)
        self.mouse = (WIDTH // 2, HEIGHT // 2)
        self.mouse_seen = False

        # chuyển cảnh: các khối đen xuất hiện/biến mất theo thứ tự ngẫu nhiên
        bx, by = WIDTH // BLOCK + 1, HEIGHT // BLOCK + 1
        rnd = random.Random(5)
        order = [(x, y) for x in range(bx) for y in range(by)]
        rnd.shuffle(order)
        self.blocks = [(x * BLOCK, y * BLOCK, i / len(order)) for i, (x, y) in enumerate(order)]
        self.trans = None            # {"phase": "out"/"in", "t": 0, "name": str}

        self.scene = None
        self._make_scene("menu")
        self.trans = {"phase": "in", "t": 0.0, "name": None}

    # =========================
    # MÀN HÌNH
    # =========================

    def apply_display(self):
        flags = pygame.SCALED
        if self.config.fullscreen:
            flags |= pygame.FULLSCREEN
        try:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        except pygame.error:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

    def _set_icon(self):
        try:
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            icon.fill((10, 8, 18), (2, 2, 28, 28))
            icon.fill((52, 196, 110), (4, 4, 24, 24))
            icon.fill((120, 240, 150), (4, 4, 24, 4))
            for ex in (9, 19):
                icon.fill((255, 255, 255), (ex, 11, 6, 6))
                icon.fill((10, 8, 18), (ex + 4, 11, 2, 6))
            icon.fill((232, 52, 76), (15, 21, 2, 8))
            pygame.display.set_icon(icon)
        except Exception:
            pass

    def toggle_fullscreen(self):
        self.config.set("fullscreen", not self.config.fullscreen)
        self.apply_display()

    # =========================
    # CẢNH
    # =========================

    def _make_scene(self, name):
        self.scene = SCENES[name](self)

    def change_scene(self, name):
        if self.trans and self.trans["phase"] == "out":
            return
        self.trans = {"phase": "out", "t": 0.0, "name": name}

    def _update_transition(self, dt):
        tr = self.trans
        if not tr:
            return
        tr["t"] += dt
        if tr["phase"] == "out" and tr["t"] >= 0.28:
            self._make_scene(tr["name"])
            self.trans = {"phase": "in", "t": 0.0, "name": None}
        elif tr["phase"] == "in" and tr["t"] >= 0.28:
            self.trans = None

    def _draw_transition(self, screen):
        tr = self.trans
        if not tr:
            return
        p = min(1.0, tr["t"] / 0.28)
        cover = p if tr["phase"] == "out" else 1.0 - p
        for x, y, th in self.blocks:
            if th < cover:
                screen.fill((6, 4, 12), (x, y, BLOCK, BLOCK))
                if th > cover - 0.04:
                    screen.fill((60, 40, 90), (x + 2, y + 2, BLOCK - 4, BLOCK - 4))

    # =========================
    # CON TRỎ PIXEL
    # =========================

    def _draw_cursor(self, screen):
        if not self.mouse_seen:
            return
        x, y = self.mouse
        if isinstance(self.scene, PlayScene) and self.scene.state in ("playing", "countdown"):
            c = (255, 240, 200)
            for dx, dy, w, h in ((-5, 0, 3, 1), (3, 0, 3, 1), (0, -5, 1, 3), (0, 3, 1, 3)):
                screen.fill(ui.INK, (x + dx - 1, y + dy - 1, w + 2, h + 2))
            for dx, dy, w, h in ((-5, 0, 3, 1), (3, 0, 3, 1), (0, -5, 1, 3), (0, 3, 1, 3)):
                screen.fill(c, (x + dx, y + dy, w, h))
            return
        pat = ("k.......", "kk......", "kwk.....", "kwwk....", "kwwwk...", "kwwwwk..", "kwwwwwk.", "kwwkkk..",
               "kwk.....", ".k......")
        for j, row in enumerate(pat):
            for i, ch in enumerate(row):
                if ch == "k":
                    screen.fill(ui.INK, (x + i, y + j, 1, 1))
                elif ch == "w":
                    screen.fill((255, 236, 190), (x + i, y + j, 1, 1))

    # =========================
    # RUN
    # =========================

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.toggle_fullscreen()
                else:
                    if e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                        self.mouse = tuple(e.pos)
                        self.mouse_seen = True
                    if not (self.trans and self.trans["phase"] == "out"):
                        self.scene.handle_event(e)

            self.scene.update(dt)
            self.scene.draw(self.screen)
            self._update_transition(dt)
            self._draw_transition(self.screen)
            self._draw_cursor(self.screen)

            pygame.display.flip()

        self.config.save()
        pygame.quit()
