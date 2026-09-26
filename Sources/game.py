import pygame

from settings import (
    WIDTH,
    HEIGHT,
    FPS,
    MOVE_DELAY,
    MAP_COLOR,
    # LINE_COLOR,
    SIGN_COLOR
)

from snake import Snake
from food import Food
from effects import Effects

class Game:

    def __init__(self):

        # =========================
        # PYGAME
        # =========================

        pygame.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT)
        )

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

        self.effects= Effects()

        self.score = 0

        self.game_over = False

        # =========================
        # TIMER
        # =========================

        self.last_move_time = pygame.time.get_ticks()
        self.end_of_effect = 0
        self.current_time = pygame.time.get_ticks()
        self.tmp_move_delay = MOVE_DELAY

        # Food không nằm trên Snake
        self.food.spawn(self.snake.pos,self.effects.effect_pos,self.effects.gambling_pos)
        self.effects.spawn_effect(self.snake.pos,self.effects.gambling_pos,self.food.pos)
        self.effects.spawn_gambling(self.snake.pos,self.effects.effect_pos,self.food.pos)

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

    def get_effects(self,effect_name):
        if effect_name==["speed_up"]:
            self.end_of_effect=self.current_time+5000
            self.tmp_move_delay//=2
            print(self.tmp_move_delay)
        elif effect_name ==["slow_down"]:
            self.end_of_effect=self.current_time+5000
            self.tmp_move_delay*=2
            print(self.tmp_move_delay)
        elif effect_name ==["longer_tail_by_20"]:
            for i in range(20):
                self.snake.pos.insert(0,self.snake.pos[0])
        elif effect_name==["100_points"]:
            self.score+=100
        elif effect_name==["halve_points"]:
            self.score//=2
        elif effect_name==["die_instantly"]:
            self.game_over=True
        elif effect_name==["shorten_tail_50%"]:
            if len(self.snake.pos)!=1:
                self.snake.pos = self.snake.pos[:(len(self.snake.pos) // 2)]
        elif effect_name==["become_1_pixel"]:
            self.snake.pos=[self.snake.pos[0]]
        elif effect_name==["lost_all_points"]:
            self.score=0


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

        eating = False
        ate=""

        if new_head == self.food.pos:
            eating=True
            ate="apple"
        elif new_head == self.effects.effect_pos:
            eating=True
            ate=self.effects.random_effect()
        elif new_head == self.effects.gambling_pos:
            eating=True
            ate=self.effects.random_gambling()

        # =========================
        # MOVE
        # =========================

        self.snake.move(grow=eating,type=ate)

        # =========================
        # EAT
        # =========================

        if eating:
            if ate=="apple":
                self.score+=1
                self.food.spawn(self.snake.pos,self.effects.effect_pos,self.effects.gambling_pos)
            else:
                print(ate)
                self.get_effects(ate)
                if new_head == self.effects.effect_pos:
                    self.effects.spawn_effect(self.snake.pos, self.effects.gambling_pos, self.food.pos)
                else:
                    self.effects.spawn_gambling(self.snake.pos, self.effects.effect_pos, self.food.pos)

        if self.current_time>=self.end_of_effect:
            self.tmp_move_delay=MOVE_DELAY
            self.end_of_effect=0

        # =========================
        # COLLISION
        # =========================

        if self.snake.hit_wall():

             self.game_over = False

        elif self.snake.hit_body():

            self.game_over = True

        # =========================
        # UPDATE TIMER
        # =========================

        self.last_move_time = self.current_time

    # =========================
    # DRAW
    # =========================

    def draw(self):

        self.screen.fill(MAP_COLOR)

        # =========================
        # GRID
        # =========================

        # Uncomment nếu muốn hiện grid

        # for i in range(HEIGHT // SIZE + 1):
        #
        #     pygame.draw.line(
        #         self.screen,
        #         LINE_COLOR,
        #         (0, i * SIZE),
        #         (WIDTH, i * SIZE)
        #     )

        # for i in range(WIDTH // SIZE + 1):
        #
        #     pygame.draw.line(
        #         self.screen,
        #         LINE_COLOR,
        #         (i * SIZE, 0),
        #         (i * SIZE, HEIGHT)
        #     )

        # =========================
        # DRAW OBJECTS
        # =========================

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

        self.food.spawn(self.snake.pos,self.effects.effect_pos,self.effects.gambling_pos)

        self.last_move_time = pygame.time.get_ticks()

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