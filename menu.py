import math
import pygame

from settings import (
    WIDTH,
    HEIGHT,
    DIFFICULTIES,
    UI_FONT_NAMES,
    options,
)

# =========================
# MÀU GIAO DIỆN
# =========================

BTN_COLOR = (44, 52, 66)
BTN_ACTIVE = (34, 170, 80)
BTN_SHADOW = (12, 14, 18)
TITLE_COLOR = (80, 235, 120)
TEXT_COLOR = (255, 255, 255)
HINT_COLOR = (190, 196, 205)

# =========================
# TIỆN ÍCH
# =========================

_text_cache = {}


def make_font(size, bold=False):
    return pygame.font.SysFont(UI_FONT_NAMES, size, bold=bold)


def render_text(font, text, color):
    """Chữ chỉ render một lần rồi lưu lại -> mượt hơn, đỡ tốn CPU."""
    key = (id(font), text, color)
    surf = _text_cache.get(key)
    if surf is None:
        if len(_text_cache) > 300:
            _text_cache.clear()
        surf = font.render(text, True, color)
        _text_cache[key] = surf
    return surf


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# =========================
# NÚT BẤM
# =========================

class Button:

    def __init__(self, label, center, action, adjustable=False, size=(380, 58)):
        self.label = label              # chuỗi hoặc hàm trả về chuỗi
        self.action = action            # action(step) - step = +1 hoặc -1
        self.adjustable = adjustable    # True: có thể đổi giá trị bằng A/D hoặc ←/→
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        self.hover = 0.0                # 0..1, tự trượt mượt

    @property
    def text(self):
        return self.label() if callable(self.label) else self.label

    def draw(self, surface, font):
        t = self.hover
        grow = int(10 * t)
        rect = self.rect.inflate(grow * 2, grow)

        pygame.draw.rect(surface, BTN_SHADOW, rect.move(0, 5), border_radius=16)
        pygame.draw.rect(surface, mix(BTN_COLOR, BTN_ACTIVE, t), rect, border_radius=16)

        label = render_text(font, self.text, TEXT_COLOR)
        surface.blit(label, label.get_rect(center=rect.center))


# =========================
# MÀN HÌNH CƠ SỞ
# =========================

class Screen:

    def __init__(self, title, hint="", on_escape=None):
        self.title = title
        self.hint = hint
        self.on_escape = on_escape
        self.buttons = []
        self.selected = 0
        self.time = 0.0

        self.font_title = make_font(78, True)
        self.font_btn = make_font(28, True)
        self.font_hint = make_font(18)

        self.dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.dim.fill((10, 14, 20, 175))
        self.dim = self.dim.convert_alpha()

    def set_buttons(self, items):
        """items: danh sách (label, action, adjustable)."""
        self.buttons = []
        start_y = int(HEIGHT * 0.46)
        gap = 76
        for i, (label, action, adjustable) in enumerate(items):
            center = (WIDTH // 2, start_y + i * gap)
            self.buttons.append(Button(label, center, action, adjustable))

    def handle_event(self, event):
        n = len(self.buttons)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % n
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % n
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.buttons[self.selected].action(1)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                if self.buttons[self.selected].adjustable:
                    self.buttons[self.selected].action(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                if self.buttons[self.selected].adjustable:
                    self.buttons[self.selected].action(1)
            elif event.key == pygame.K_ESCAPE and self.on_escape:
                self.on_escape()

        elif event.type == pygame.MOUSEMOTION:
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos):
                    self.selected = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint(event.pos):
                    self.selected = i
                    b.action(1)
                    break

    def update(self, dt):
        self.time += dt
        k = min(1.0, dt * 14)
        for i, b in enumerate(self.buttons):
            target = 1.0 if i == self.selected else 0.0
            b.hover += (target - b.hover) * k

    def draw(self, surface, background):
        surface.blit(background, (0, 0))
        surface.blit(self.dim, (0, 0))

        # Tiêu đề nhấp nhô nhẹ
        bob = math.sin(self.time * 2.2) * 5
        title = render_text(self.font_title, self.title, TITLE_COLOR)
        shadow = render_text(self.font_title, self.title, (0, 0, 0))
        rect = title.get_rect(center=(WIDTH // 2, int(HEIGHT * 0.24 + bob)))
        surface.blit(shadow, rect.move(4, 5))
        surface.blit(title, rect)

        for b in self.buttons:
            b.draw(surface, self.font_btn)

        if self.hint:
            hint = render_text(self.font_hint, self.hint, HINT_COLOR)
            surface.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))


# =========================
# MENU CHÍNH
# =========================

class MenuScreen(Screen):

    def __init__(self, on_play, on_settings, on_quit):
        super().__init__(
            "SNAKE GAME",
            hint="W/S hoặc chuột để chọn  •  Enter để xác nhận",
        )
        self.set_buttons([
            ("Chơi game", lambda step: on_play(), False),
            ("Cài đặt", lambda step: on_settings(), False),
            ("Thoát", lambda step: on_quit(), False),
        ])


# =========================
# CÀI ĐẶT
# =========================

class SettingsScreen(Screen):

    def __init__(self, on_back):
        super().__init__(
            "CÀI ĐẶT",
            hint="A/D hoặc ←/→ để đổi giá trị  •  Esc để quay lại",
            on_escape=on_back,
        )

        def change_difficulty(step):
            options.difficulty = (options.difficulty + step) % len(DIFFICULTIES)

        def toggle_grid(step):
            options.show_grid = not options.show_grid

        def toggle_walls(step):
            options.walls = not options.walls

        def on_off(value):
            return "Bật" if value else "Tắt"

        self.set_buttons([
            (lambda: f"Độ khó: {DIFFICULTIES[options.difficulty][0]}", change_difficulty, True),
            (lambda: f"Lưới nền: {on_off(options.show_grid)}", toggle_grid, True),
            (lambda: f"Tường: {on_off(options.walls)}", toggle_walls, True),
            ("Quay lại", lambda step: on_back(), False),
        ])
