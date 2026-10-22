import pygame
import random

from settings import ASSET_DIR, WIDTH, HEIGHT, SIZE


class Effects:
    def __init__(self):
        self.effect = ["speed_up", "slow_down"]
        self.gambling = ["longer_tail_by_20", "die_instantly", "halve_points", "100_points", "shorten_tail_50%", "become_1_pixel", "lost_all_points"]
        self.effect_pos = [0, 0]
        self.gambling_pos = [0, 0]
        self.effect_image = pygame.image.load(f"{ASSET_DIR}/flash.png").convert_alpha()
        self.effect_image = pygame.transform.scale(self.effect_image, (SIZE, SIZE))
        self.gambling_image = pygame.image.load(f"{ASSET_DIR}/mystery.png").convert_alpha()
        self.gambling_image = pygame.transform.scale(self.gambling_image, (SIZE, SIZE))
        self.spawn_effect(snake_pos=[], gambling_pos=[], food_pos=[], terrain_pos=[])
        self.spawn_gambling(snake_pos=[], effect_pos=[], food_pos=[], terrain_pos=[])

    def random_effect(self):
        return random.choices(self.effect, weights=[1, 1], k=1)

    def random_gambling(self):
        return random.choices(self.gambling, weights=[5, 1, 11, 60, 2, 1, 20], k=1)

    def spawn_effect(self, snake_pos, gambling_pos, food_pos, terrain_pos):
        while True:
            self.effect_pos = [
                random.randint(0, WIDTH // SIZE - 1),
                random.randint(0, HEIGHT // SIZE - 1)
            ]
            if (self.effect_pos not in snake_pos and self.effect_pos not in gambling_pos
                    and self.effect_pos not in food_pos and self.effect_pos not in terrain_pos):
                break

    def spawn_gambling(self, snake_pos, effect_pos, food_pos, terrain_pos):
        while True:
            self.gambling_pos = [
                random.randint(0, WIDTH // SIZE - 1),
                random.randint(0, HEIGHT // SIZE - 1)
            ]
            if (self.gambling_pos not in snake_pos and self.gambling_pos != effect_pos
                    and self.gambling_pos not in food_pos and self.gambling_pos not in terrain_pos):
                break

    def draw_effect(self, screen):
        screen.blit(self.effect_image, (self.effect_pos[0] * SIZE, self.effect_pos[1] * SIZE))

    def draw_gambling(self, screen):
        screen.blit(self.gambling_image, (self.gambling_pos[0] * SIZE, self.gambling_pos[1] * SIZE))


