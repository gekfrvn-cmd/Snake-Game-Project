import pygame
import random

from settings import (
    WIDTH,
    HEIGHT,
    SIZE,
    FOOD_COLOR
)


class Food:

    def __init__(self):

        self.pos = [0, 0]

        self.spawn(snake_pos=[],effect_pos=[],gambling_pos=[],terrain_pos=[])

    # =========================
    # SPAWN
    # =========================

    def spawn(self,snake_pos,effect_pos,gambling_pos,terrain_pos):

        while True:

            self.pos = [
                random.randint(0, WIDTH // SIZE - 1),
                random.randint(0, HEIGHT // SIZE - 1)
            ]

            # Nếu food không nằm trên snake
            if self.pos not in snake_pos and self.pos not in effect_pos and self.pos not in gambling_pos and self.pos not in terrain_pos:
                break

    # =========================
    # DRAW
    # =========================

    def draw(self, screen):

        pygame.draw.rect(
            screen,
            FOOD_COLOR,
            (
                self.pos[0] * SIZE,
                self.pos[1] * SIZE,
                SIZE,
                SIZE
            )
        )