import math
import random

import pygame

from settings import COLS, ROWS, SIZE
from utils import lerp_color, darken
import sprites

DIRS4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def inside(x, y):
    return 0 <= x < COLS and 0 <= y < ROWS


# =========================
# QUÁI VẬT
# =========================

class Enemy:
    """Đi lang thang, thấy rắn cùng hàng/cột thì báo hiệu rồi lao tới."""

    SPAWN_T = 1.0
    AIM_T = 0.7
    LOOK_RANGE = 14

    def __init__(self, cell):
        self.pos = list(cell)
        self.state = "spawning"       # spawning | wander | aim | charge | stunned
        self.t = 0.0
        self.age = 0.0
        self.dir = random.choice(DIRS4)
        self.move_timer = random.uniform(0.1, 0.4)
        self.cooldown = 2.0
        self.charge_dir = (1, 0)
        self.charge_left = 0
        self.step_timer = 0.0

    def stun(self, secs=1.4):
        self.state = "stunned"
        self.t = secs
        self.cooldown = 4.0

    def update(self, dt, world):
        self.age += dt
        self.cooldown = max(0.0, self.cooldown - dt)

        if self.state == "spawning":
            self.t += dt
            if self.t >= self.SPAWN_T:
                self.state, self.t = "wander", 0.0
            return
        if self.state == "stunned":
            self.t -= dt
            if self.t <= 0:
                self.state = "wander"
            return
        if self.state == "wander":
            self.move_timer -= dt
            if self.move_timer <= 0:
                self.move_timer = 0.34
                self._wander_step(world)
            if self.cooldown <= 0:
                self._look(world)
        elif self.state == "aim":
            self.t -= dt
            if self.t <= 0:
                self.state = "charge"
                self.charge_left = 18
                self.step_timer = 0.0
        elif self.state == "charge":
            self.step_timer -= dt
            while self.step_timer <= 0 and self.state == "charge":
                self.step_timer += 0.04
                self._charge_step(world)

    def _wander_step(self, world):
        if random.random() < 0.3:
            self.dir = random.choice(DIRS4)
        options = [self.dir] + [d for d in DIRS4 if d != self.dir]
        for d in options:
            nx, ny = self.pos[0] + d[0], self.pos[1] + d[1]
            if not world.enemy_blocked((nx, ny), self):
                self.dir = d
                self.pos = [nx, ny]
                return

    def _look(self, world):
        for d in DIRS4:
            for k in range(1, self.LOOK_RANGE + 1):
                c = (self.pos[0] + d[0] * k, self.pos[1] + d[1] * k)
                if not inside(*c) or world.enemy_solid(c):
                    break
                if world.snake_index(c) is not None:
                    self.charge_dir = d
                    self.state = "aim"
                    self.t = self.AIM_T
                    world.enemy_alert(self)
                    return

    def _charge_step(self, world):
        d = self.charge_dir
        nx, ny = self.pos[0] + d[0], self.pos[1] + d[1]
        if not inside(nx, ny) or world.enemy_solid((nx, ny)):
            self.stun(1.2)
            return
        self.pos = [nx, ny]
        idx = world.snake_index((nx, ny))
        if idx is not None:
            self.state = "wander"
            self.cooldown = 4.0
            world.enemy_hits_snake(self, idx)
            return
        self.charge_left -= 1
        if self.charge_left <= 0:
            self.state = "wander"
            self.cooldown = 3.0

    def aim_cells(self, world):
        """Các ô trên đường lao tới (để vẽ vạch cảnh báo)."""
        out = []
        for k in range(1, 18):
            c = (self.pos[0] + self.charge_dir[0] * k, self.pos[1] + self.charge_dir[1] * k)
            if not inside(*c) or world.enemy_solid(c):
                break
            out.append(c)
        return out


# =========================
# THÙNG GỖ (vật cản thêm theo cấp, có thể bị Lướt phá)
# =========================

BLOCK_SHAPES = [
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (1, 0), (0, 1), (1, 1)],
]


class Crates:

    def __init__(self):
        self.cells = {}      # (x, y) -> [block_id, age]
        self.next_id = 1

    def add_block(self, cells):
        bid = self.next_id
        self.next_id += 1
        for c in cells:
            self.cells[tuple(c)] = [bid, 0.0]
        return bid

    def update(self, dt):
        for v in self.cells.values():
            v[1] += dt

    def at(self, cell):
        return self.cells.get(tuple(cell))

    def break_block(self, cell):
        v = self.cells.get(tuple(cell))
        if not v:
            return []
        removed = [c for c, val in self.cells.items() if val[0] == v[0]]
        for c in removed:
            del self.cells[c]
        return removed

    def count_blocks(self):
        return len({v[0] for v in self.cells.values()})

    def draw(self, screen):
        S = SIZE
        for (x, y), (bid, age) in self.cells.items():
            sprites.draw_crate(screen, x * S, y * S, min(1.0, age / 0.3))

    def shadows(self, layer):
        S = SIZE
        for (x, y) in self.cells:
            layer.fill((0, 0, 0, 90), (x * S + 2, y * S + 3, S, S))


# =========================
# MẢNH VỠ (phần thân bị cắt, nguy hiểm nhưng biến mất nhanh)
# =========================

class Debris:

    LIFE = 5.0

    def __init__(self):
        self.cells = {}      # (x, y) -> [life, color]

    def add(self, cell, color, life=None):
        self.cells[tuple(cell)] = [life or self.LIFE, color]

    def update(self, dt):
        for c in list(self.cells):
            self.cells[c][0] -= dt
            if self.cells[c][0] <= 0:
                del self.cells[c]

    def draw(self, screen, t):
        S = SIZE
        for (x, y), (life, color) in self.cells.items():
            sprites.draw_debris(screen, x * S, y * S, color, life, t)
