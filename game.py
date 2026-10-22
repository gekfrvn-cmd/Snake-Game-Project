import os
import pygame

from settings import (
    WIDTH,
    HEIGHT,
    SIZE,
    FPS,
    MOVE_DELAY,
    BACKGROUND_TILE_A,
    BACKGROUND_TILE_B,
    GRID_COLOR,
    BACKGROUND_IMAGES,
    SIGN_COLOR
)

from snake import Snake
from food import Food
from effects import Effects
from terrain import Terrain


class Game:

    def __init__(self):

        # =========================
        # PYGAME
        # =========================

        pygame.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

        self.background_surface = pygame.Surface((WIDTH, HEIGHT)).convert()
        background_path = next(
            (path for path in BACKGROUND_IMAGES if os.path.isfile(path)), None
        )
        if background_path:
            loaded_background = pygame.image.load(background_path).convert()
            self.background_surface = pygame.transform.smoothscale(
                loaded_background, (WIDTH, HEIGHT)
            )
        else:
            for row in range(HEIGHT // SIZE):
                for col in range(WIDTH // SIZE):
                    color = BACKGROUND_TILE_A if (row + col) % 2 == 0 else BACKGROUND_TILE_B
                    pygame.draw.rect(
                        self.background_surface, color,
                        (col * SIZE, row * SIZE, SIZE, SIZE)
                    )

        # Kẻ lưới một lần trên nền để không phải dựng lại mỗi khung hình.
        grid = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        grid_color = (*GRID_COLOR, 115)
        for x in range(0, WIDTH + 1, SIZE):
            pygame.draw.line(grid, grid_color, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT + 1, SIZE):
            pygame.draw.line(grid, grid_color, (0, y), (WIDTH, y), 1)
        self.background_surface.blit(grid, (0, 0))

        pygame.display.set_caption("Snake Game")

        self.clock = pygame.time.Clock()

        # =========================
        # FONT
        # =========================

        self.font_small = pygame.font.SysFont(
            "sans",
            20
        )

        self.font_big = pygame.font.SysFont(
            "sans",
            45
        )

        # =========================
        # GAME OBJECTS
        # =========================

        self.snake = Snake()

        self.food = Food()

        self.effects = Effects()

        self.score = 0

        self.game_over = False

        self.terrain = Terrain()

        # =========================
        # TIMER
        # =========================

        self.last_move_time = pygame.time.get_ticks()
        self.end_of_effect = 0
        self.current_time = pygame.time.get_ticks()
        self.tmp_move_delay = MOVE_DELAY

        # Food không nằm trên Snake

        self.food.spawn(self.snake.pos, self.effects.effect_pos, self.effects.gambling_pos, self.terrain.wall)
        self.effects.spawn_effect(self.snake.pos, self.effects.gambling_pos, self.food.pos, self.terrain.wall)
        self.effects.spawn_gambling(self.snake.pos, self.effects.effect_pos, self.food.pos, self.terrain.wall)

    # =========================
    # INPUT
    # =========================

    def handle_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:

                # Restart
                if event.key == pygame.K_SPACE:

                    if self.game_over:
                        self.restart()

                # Direction
                if not self.game_over:

                    if event.key == pygame.K_w:
                        self.snake.change_direction("up")

                    elif event.key == pygame.K_s:
                        self.snake.change_direction("down")

                    elif event.key == pygame.K_a:
                        self.snake.change_direction("left")

                    elif event.key == pygame.K_d:
                        self.snake.change_direction("right")

        return True

    # =========================
    # GET EFFECTS
    # =========================

    def get_effects(self, effect_name):
        if effect_name == ["speed_up"]:
            self.end_of_effect = self.current_time + 5000
            self.tmp_move_delay //= 2
            print(self.tmp_move_delay)
        elif effect_name == ["slow_down"]:
            self.end_of_effect = self.current_time + 5000
            self.tmp_move_delay *= 2
            print(self.tmp_move_delay)
        elif effect_name == ["longer_tail_by_20"]:
            for i in range(20):
                self.snake.pos.insert(0, self.snake.pos[0])
        elif effect_name == ["100_points"]:
            self.score += 100
        elif effect_name == ["halve_points"]:
            self.score //= 2
        elif effect_name == ["die_instantly"]:
            self.game_over = True
        elif effect_name == ["shorten_tail_50%"]:
            if len(self.snake.pos) != 1:
                self.snake.pos = self.snake.pos[(len(self.snake.pos) // 2):-1]
        elif effect_name == ["become_1_pixel"]:
            self.snake.pos = [self.snake.pos[0]]
        elif effect_name == ["lost_all_points"]:
            self.score = 0

    # =========================
    # UPDATE
    # =========================

    def update(self):

        if self.game_over:
            return

        self.current_time = pygame.time.get_ticks()

        # Chưa đến thời gian di chuyển
        if self.current_time - self.last_move_time < self.tmp_move_delay:
            return

        # =========================
        # CHECK FOOD
        # =========================

        # Commit direction trước khi tính đầu mới
        self.snake.direction = self.snake.next_direction

        new_head = self.snake.get_new_head()

        # Chặn ngay trước khi di chuyển để đầu rắn không lọt vào ô tường.
        if self.terrain.hit_wall(new_head):
            self.game_over = True
            self.last_move_time = self.current_time
            return

        eating = False
        ate = ""

        if new_head == self.food.pos:
            eating = True
            ate = "apple"
        elif new_head == self.effects.effect_pos:
            eating = True
            ate = self.effects.random_effect()
        elif new_head == self.effects.gambling_pos:
            eating = True
            ate = self.effects.random_gambling()

        # =========================
        # MOVE
        # =========================

        self.snake.move(grow=eating, type=ate)

        # =========================
        # EAT
        # =========================

        if eating:
            if ate == "apple":
                self.score += 1
                self.food.spawn(self.snake.pos, self.effects.effect_pos, self.effects.gambling_pos, self.terrain.wall)
            else:
                print(ate)
                self.get_effects(ate)
                if new_head == self.effects.effect_pos:
                    self.effects.spawn_effect(self.snake.pos, self.effects.gambling_pos, self.food.pos,
                                              self.terrain.wall)
                else:
                    self.effects.spawn_gambling(self.snake.pos, self.effects.effect_pos, self.food.pos,
                                                self.terrain.wall)

        if self.current_time >= self.end_of_effect:
            self.tmp_move_delay = MOVE_DELAY
            self.end_of_effect = 0

        # =========================
        # COLLISION
        # =========================

        if self.snake.hit_body():

            self.game_over = True

        # =========================
        # UPDATE TIMER
        # =========================

        self.last_move_time = self.current_time

    # =========================
    # DRAW
    # =========================

    def draw_background(self):
        self.screen.blit(self.background_surface, (0, 0))

    def draw(self):

        self.draw_background()

        # =========================
        # DRAW OBJECTS
        # =========================
        self.terrain.draw(self.screen)

        self.snake.draw(self.screen)

        self.food.draw(self.screen)

        self.effects.draw_effect(self.screen)

        self.effects.draw_gambling(self.screen)

        # =========================
        # SCORE
        # =========================

        score_text = self.font_small.render(
            f"Score: {self.score}",
            True,
            SIGN_COLOR
        )

        self.screen.blit(
            score_text,
            (0, 0)
        )

        # =========================
        # GAME OVER
        # =========================

        if self.game_over:
            game_over_text = self.font_big.render(
                f"GAME OVER, SCORE: {self.score}",
                True,
                SIGN_COLOR
            )

            self.screen.blit(
                game_over_text,
                (
                    WIDTH // 6,
                    HEIGHT // 3
                )
            )

            restart_text = self.font_big.render(
                "Press SPACE to restart",
                True,
                SIGN_COLOR
            )

            self.screen.blit(
                restart_text,
                (
                    WIDTH // 5,
                    HEIGHT // 3 + 50
                )
            )

        pygame.display.flip()

    # =========================
    # RESTART
    # =========================

    def restart(self):

        self.snake.reset()

        self.score = 0

        self.game_over = False

        self.tmp_move_delay = MOVE_DELAY
        self.end_of_effect = 0
        self.current_time = pygame.time.get_ticks()
        self.last_move_time = self.current_time

        self.food.spawn(self.snake.pos, self.effects.effect_pos, self.effects.gambling_pos, self.terrain.wall)
        self.effects.spawn_effect(
            self.snake.pos, self.effects.gambling_pos, self.food.pos, self.terrain.wall
        )
        self.effects.spawn_gambling(
            self.snake.pos, self.effects.effect_pos, self.food.pos, self.terrain.wall
        )

    # =========================
    # RUN
    # =========================

    def run(self):

        running = True

        while running:
            # INPUT
            running = self.handle_events()

            # UPDATE
            self.update()

            # DRAW
            self.draw()

            # FPS
            self.clock.tick(FPS)

        pygame.quit()
