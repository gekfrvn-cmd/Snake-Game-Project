import os
import pygame

from settings import (
    WIDTH,
    HEIGHT,
    SIZE,
    FPS,
    BACKGROUND_TILE_A,
    BACKGROUND_TILE_B,
    GRID_COLOR,
    BACKGROUND_IMAGES,
    SIGN_COLOR,
    DIFFICULTIES,
    HUD_HEIGHT,
    HUD_BG,
    HUD_LINE,
    options,
)

from snake import Snake
from food import Food
from effects import Effects
from terrain import Terrain
from menu import MenuScreen, SettingsScreen, render_text, make_font

EFFECT_MESSAGES = {
    "speed_up": "Tăng tốc 5 giây!",
    "slow_down": "Chậm lại 5 giây",
    "longer_tail_by_20": "Đuôi dài thêm 20 ô",
    "die_instantly": "Chết ngay!",
    "halve_points": "Điểm giảm một nửa",
    "100_points": "+100 điểm!",
    "shorten_tail_50%": "Đuôi ngắn đi một nửa",
    "become_1_pixel": "Thu nhỏ còn 1 ô",
    "lost_all_points": "Mất hết điểm",
}

KEY_TO_DIRECTION = {
    pygame.K_w: "up", pygame.K_UP: "up",
    pygame.K_s: "down", pygame.K_DOWN: "down",
    pygame.K_a: "left", pygame.K_LEFT: "left",
    pygame.K_d: "right", pygame.K_RIGHT: "right",
}


class Game:

    def __init__(self):

        # =========================
        # PYGAME
        # =========================

        pygame.init()

        # Cửa sổ = thanh thông tin (trên) + khu vực chơi (dưới).
        # self.screen chỉ là phần khu vực chơi nên toàn bộ code vẽ cũ giữ nguyên.
        self.window = pygame.display.set_mode((WIDTH, HEIGHT + HUD_HEIGHT))
        self.screen = self.window.subsurface((0, HUD_HEIGHT, WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.running = True

        self.build_backgrounds()

        # =========================
        # FONT
        # =========================

        self.font_small = make_font(22, True)
        self.font_mid = make_font(32)
        self.font_big = make_font(64, True)
        self.font_hud = make_font(26, True)

        self.hud_bar = pygame.Surface((WIDTH, HUD_HEIGHT)).convert()
        self.hud_bar.fill(HUD_BG)
        pygame.draw.rect(self.hud_bar, HUD_LINE, (0, HUD_HEIGHT - 3, WIDTH, 3))

        # =========================
        # GAME OBJECTS
        # =========================

        self.snake = Snake()
        self.food = Food()
        self.effects = Effects()
        self.terrain = Terrain(options.walls)

        self.score = 0
        self.game_over = False
        self.play_time = 0.0   # thời gian chơi (giây)

        # =========================
        # TIMER
        # =========================

        self.base_delay = DIFFICULTIES[options.difficulty][1]
        self.tmp_move_delay = self.base_delay
        self.end_of_effect = 0
        self.current_time = pygame.time.get_ticks()
        self.last_move_time = self.current_time

        self.dir_queue = []          # hàng đợi phím: bấm nhanh 2 phím vẫn ăn đủ
        self.toast = ("", 0)         # thông báo hiệu ứng vừa ăn
        self._toast_surface = None
        self._toast_text = None
        self._hud_score = None
        self._hud_surface = None

        # =========================
        # UI
        # =========================

        self.overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150))
        self.overlay = self.overlay.convert_alpha()

        self.fade_surface = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.fade_surface.fill((0, 0, 0))
        self.fade = 255.0

        self.screens = {
            "menu": MenuScreen(self.start_game, lambda: self.set_state("settings"), self.quit_game),
            "settings": SettingsScreen(lambda: self.set_state("menu")),
        }
        self.state = "menu"

    # =========================
    # NỀN
    # =========================

    def build_backgrounds(self):
        self.bg_plain = pygame.Surface((WIDTH, HEIGHT)).convert()
        background_path = next(
            (path for path in BACKGROUND_IMAGES if os.path.isfile(path)), None
        )
        if background_path:
            loaded = pygame.image.load(background_path).convert()
            self.bg_plain = pygame.transform.smoothscale(loaded, (WIDTH, HEIGHT))
        else:
            for row in range(HEIGHT // SIZE):
                for col in range(WIDTH // SIZE):
                    color = BACKGROUND_TILE_A if (row + col) % 2 == 0 else BACKGROUND_TILE_B
                    pygame.draw.rect(
                        self.bg_plain, color,
                        (col * SIZE, row * SIZE, SIZE, SIZE)
                    )

        # Dựng sẵn bản có lưới, để bật/tắt lưới trong Cài đặt không tốn gì.
        grid = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        grid_color = (*GRID_COLOR, 115)
        for x in range(0, WIDTH + 1, SIZE):
            pygame.draw.line(grid, grid_color, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT + 1, SIZE):
            pygame.draw.line(grid, grid_color, (0, y), (WIDTH, y), 1)
        self.bg_grid = self.bg_plain.copy()
        self.bg_grid.blit(grid, (0, 0))

    # =========================
    # TRẠNG THÁI
    # =========================

    def set_state(self, name):
        self.state = name
        self.fade = 255.0   # mờ dần từ đen -> hiện màn mới

    def quit_game(self):
        self.running = False

    def start_game(self):
        # Áp dụng tuỳ chọn từ màn Cài đặt
        self.base_delay = DIFFICULTIES[options.difficulty][1]
        self.terrain = Terrain(options.walls)
        self.restart()
        self.set_state("playing")

    # =========================
    # SPAWN
    # =========================

    def respawn_food(self):
        self.food.spawn(
            self.snake.pos,
            [self.effects.effect_pos],
            [self.effects.gambling_pos],
            self.terrain.wall,
        )

    def respawn_effect(self):
        self.effects.spawn_effect(
            self.snake.pos,
            [self.effects.gambling_pos],
            [self.food.pos],
            self.terrain.wall,
        )

    def respawn_gambling(self):
        self.effects.spawn_gambling(
            self.snake.pos,
            self.effects.effect_pos,
            [self.food.pos],
            self.terrain.wall,
        )

    # =========================
    # INPUT
    # =========================

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.state == "playing":
                self.handle_game_event(event)
            else:
                # Chuột: đổi toạ độ từ cửa sổ sang khu vực chơi (trừ chiều cao thanh trên)
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                    data = dict(event.dict)
                    data["pos"] = (event.pos[0], event.pos[1] - HUD_HEIGHT)
                    event = pygame.event.Event(event.type, data)
                self.screens[self.state].handle_event(event)
        return self.running

    def handle_game_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.set_state("menu")
            return

        if self.game_over:
            if event.key == pygame.K_SPACE:
                self.restart()
            return

        direction = KEY_TO_DIRECTION.get(event.key)
        if direction and len(self.dir_queue) < 3:
            if not self.dir_queue or self.dir_queue[-1] != direction:
                self.dir_queue.append(direction)

    # =========================
    # GET EFFECTS
    # =========================

    def get_effects(self, name):
        if name == "speed_up":
            self.end_of_effect = self.current_time + 5000
            self.tmp_move_delay = max(40, self.base_delay // 2)
        elif name == "slow_down":
            self.end_of_effect = self.current_time + 5000
            self.tmp_move_delay = self.base_delay * 2
        elif name == "longer_tail_by_20":
            for _ in range(20):
                self.snake.pos.insert(0, list(self.snake.pos[0]))
        elif name == "100_points":
            self.score += 100
        elif name == "halve_points":
            self.score //= 2
        elif name == "die_instantly":
            self.game_over = True
        elif name == "shorten_tail_50%":
            if len(self.snake.pos) > 1:
                # Giữ nửa sau (có đầu rắn). Bản cũ cắt luôn cả đầu -> có thể crash.
                self.snake.pos = self.snake.pos[len(self.snake.pos) // 2:]
        elif name == "become_1_pixel":
            self.snake.pos = [self.snake.pos[-1]]
        elif name == "lost_all_points":
            self.score = 0

    # =========================
    # UPDATE
    # =========================

    def update(self):

        if self.state != "playing" or self.game_over:
            return

        self.current_time = pygame.time.get_ticks()

        # Chưa đến thời gian di chuyển
        if self.current_time - self.last_move_time < self.tmp_move_delay:
            return

        # Lấy 1 phím từ hàng đợi cho mỗi bước đi
        if self.dir_queue:
            self.snake.change_direction(self.dir_queue.pop(0))

        # Commit direction trước khi tính đầu mới
        self.snake.direction = self.snake.next_direction

        new_head = self.snake.get_new_head()

        # Chặn ngay trước khi di chuyển để đầu rắn không lọt vào ô tường.
        if self.terrain.hit_wall(new_head):
            self.game_over = True
            self.last_move_time = self.current_time
            return

        ate = ""
        picked = None

        if new_head == self.food.pos:
            ate = "apple"
        elif new_head == self.effects.effect_pos:
            ate = self.effects.random_effect()[0]
            picked = "effect"
        elif new_head == self.effects.gambling_pos:
            ate = self.effects.random_gambling()[0]
            picked = "gambling"

        # =========================
        # MOVE
        # =========================

        self.snake.move(grow=(ate != ""), type=ate)

        # =========================
        # EAT
        # =========================

        if ate == "apple":
            self.score += 1
            self.respawn_food()
        elif picked:
            self.get_effects(ate)
            self.toast = (EFFECT_MESSAGES.get(ate, ate), self.current_time + 1800)
            if picked == "effect":
                self.respawn_effect()
            else:
                self.respawn_gambling()

        if self.end_of_effect and self.current_time >= self.end_of_effect:
            self.tmp_move_delay = self.base_delay
            self.end_of_effect = 0

        # =========================
        # COLLISION
        # =========================

        if self.snake.hit_body():
            self.game_over = True

        self.last_move_time = self.current_time

    # =========================
    # DRAW
    # =========================

    def draw_hud(self):
        # Thanh thông tin phía trên, nằm ngoài khu vực chơi.
        self.window.blit(self.hud_bar, (0, 0))
        if self.state != "playing":
            return

        minutes, sec = divmod(int(self.play_time), 60)
        score = render_text(self.font_hud, f"Điểm: {self.score}", SIGN_COLOR)
        timer = render_text(self.font_hud, f"Thời gian: {minutes:02d}:{sec:02d}", SIGN_COLOR)

        cy = (HUD_HEIGHT - 3) // 2
        self.window.blit(score, score.get_rect(midleft=(20, cy)))
        self.window.blit(timer, timer.get_rect(midright=(WIDTH - 20, cy)))
        self.draw_toast()

    def draw_toast(self):
        message, until = self.toast
        if not message or pygame.time.get_ticks() >= until:
            return
        if self._toast_text != message:
            text = render_text(self.font_small, message, SIGN_COLOR)
            pill = pygame.Surface(
                (text.get_width() + 36, text.get_height() + 12), pygame.SRCALPHA
            )
            pygame.draw.rect(pill, (44, 52, 66), pill.get_rect(), border_radius=14)
            pill.blit(text, (18, 6))
            self._toast_surface = pill
            self._toast_text = message
        self.window.blit(
            self._toast_surface,
            self._toast_surface.get_rect(center=(WIDTH // 2, (HUD_HEIGHT - 3) // 2)),
        )

    def draw_game_over(self):
        self.screen.blit(self.overlay, (0, 0))

        title = render_text(self.font_big, "GAME OVER", (255, 90, 90))
        score = render_text(self.font_mid, f"Điểm: {self.score}", SIGN_COLOR)
        hint = render_text(
            self.font_small, "SPACE: chơi lại   •   ESC: về menu", SIGN_COLOR
        )

        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70)))
        minutes, sec = divmod(int(self.play_time), 60)
        time_text = render_text(self.font_mid, f"Thời gian: {minutes:02d}:{sec:02d}", SIGN_COLOR)

        self.screen.blit(score, score.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        self.screen.blit(time_text, time_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 110)))

    def draw(self):
        background = self.bg_grid if options.show_grid else self.bg_plain

        if self.state == "playing":
            self.screen.blit(background, (0, 0))
            self.terrain.draw(self.screen)
            self.snake.draw(self.screen)
            self.food.draw(self.screen)
            self.effects.draw_effect(self.screen)
            self.effects.draw_gambling(self.screen)
            if self.game_over:
                self.draw_game_over()
        else:
            self.screens[self.state].draw(self.screen, background)

        self.draw_hud()

        # Chuyển cảnh mờ dần
        if self.fade > 0:
            self.fade_surface.set_alpha(int(self.fade))
            self.screen.blit(self.fade_surface, (0, 0))

        pygame.display.flip()

    # =========================
    # RESTART
    # =========================

    def restart(self):
        self.snake.reset()
        self.score = 0
        self.game_over = False
        self.play_time = 0.0
        self.dir_queue.clear()
        self.toast = ("", 0)

        self.tmp_move_delay = self.base_delay
        self.end_of_effect = 0

        self.respawn_food()
        self.respawn_effect()
        self.respawn_gambling()

        self.last_move_time = pygame.time.get_ticks()

    # =========================
    # RUN
    # =========================

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            if self.state == "playing" and not self.game_over:
                self.play_time += dt

            self.handle_events()

            if self.state in self.screens:
                self.screens[self.state].update(dt)

            if self.fade > 0:
                self.fade = max(0.0, self.fade - 900.0 * dt)

            self.update()
            self.draw()

        pygame.quit()
