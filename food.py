import pygame
import random

from settings import ASSET_DIR, WIDTH, HEIGHT, SIZE


class Food:
    def __init__(self):
        self.pos = [0, 0]
        self.image = pygame.image.load(f"{ASSET_DIR}/apple.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (SIZE, SIZE))
        self.spawn(snake_pos=[], effect_pos=[], gambling_pos=[], terrain_pos=[])

    def spawn(self, snake_pos, effect_pos, gambling_pos, terrain_pos):
        while True:
            self.pos = [
                random.randint(0, WIDTH // SIZE - 1),
                random.randint(0, HEIGHT // SIZE - 1)
            ]
            if (self.pos not in snake_pos and self.pos not in effect_pos
                    and self.pos not in gambling_pos and self.pos not in terrain_pos):
                break

    def draw(self, screen):
        screen.blit(self.image, (self.pos[0] * SIZE, self.pos[1] * SIZE))
