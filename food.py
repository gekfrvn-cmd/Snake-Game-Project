import math

from settings import SIZE
from utils import pick_free_cell, ease_out_back
import sprites


class Food:

    def __init__(self):
        self.pos = None
        self.age = 0.0

    def spawn(self, occupied):
        self.pos = list(pick_free_cell(occupied))
        self.age = 0.0

    def update(self, dt):
        self.age += dt

    def center(self):
        return self.pos[0] * SIZE + SIZE // 2, self.pos[1] * SIZE + SIZE // 2

    def light(self, t):
        if self.pos is None:
            return None
        cx, cy = self.center()
        return (cx, cy, 30, (255, 70, 70), 0.8 + 0.2 * math.sin(t * 4))

    def draw(self, screen, t=0.0):
        if self.pos is None:
            return
        cx, cy = self.center()
        pop = ease_out_back(self.age / 0.35)
        sprites.draw_apple(screen, cx, cy, SIZE, t, pop)
