import pygame
import random

from settings import(
    WIDTH,
    HEIGHT,
    SIZE,
    EFFECT_COLOR,
    GAMBLING_COLOR
)

class Effects:

    def __init__(self):

        self.effect=["speed_up","slow_down"]

        self.gambling=["longer_tail_by_20","die_instantly","halve_points","100_points","shorten_tail_50%","become_1_pixel","lost_all_points"]

        self.effect_pos=[0, 0]

        self.gambling_pos=[0, 0]

        self.spawn_effect(snake_pos=[],gambling_pos=[],food_pos=[])

        self.spawn_gambling(snake_pos=[],effect_pos=[],food_pos=[])

    def random_effect(self):
        return random.choices(self.effect,weights=[1,1],k=1)

    def random_gambling(self):
        return random.choices(self.gambling,weights=[2,2.5,10,60,5.5,5,15],k=1)

    # =========================
    # SPAWN
    # =========================

    def spawn_effect(self,snake_pos,gambling_pos,food_pos):
        while True:

            self.effect_pos = [
                random.randint(0, WIDTH // SIZE - 1),
                random.randint(0, HEIGHT // SIZE - 1)
            ]

            # Nếu effect không nằm trên snake, gambling và food
            if self.effect_pos not in snake_pos and self.effect_pos not in gambling_pos and self.effect_pos not in food_pos:
                break

    def spawn_gambling(self,snake_pos,effect_pos,food_pos):
        while True:
            self.gambling_pos = [
                random.randint(0, WIDTH // SIZE - 1),
                random.randint(0, HEIGHT // SIZE - 1)
            ]

            # Nếu bling không nằm trên snake, effect và food
            if self.gambling_pos not in snake_pos and self.gambling_pos not in effect_pos and self.gambling_pos not in food_pos:
                break

    def draw_effect(self,screen):
        pygame.draw.rect(
            screen,
            EFFECT_COLOR,
            (
                self.effect_pos[0] * SIZE,
                self.effect_pos[1] * SIZE,
                SIZE,
                SIZE
            )
        )
    def draw_gambling(self,screen):
        pygame.draw.rect(
            screen,
            GAMBLING_COLOR,
            (
                self.gambling_pos[0] * SIZE,
                self.gambling_pos[1] * SIZE,
                SIZE,
                SIZE
            )
        )