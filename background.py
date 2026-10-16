import math
import random

import pygame

import ui
import sprites
from settings import *
from terrain import brick_surface, make_floor
from utils import lerp_color, darken


class Background:
    """Nền ngục tối dùng cho menu / cài đặt / hướng dẫn: tường gạch, cột đá, đuốc,
    xích đung đưa, sương mù trôi và tàn lửa bay lên. Có ánh sáng động."""

    GROUND_Y = 318

    def __init__(self, w=WIDTH, h=HEIGHT):
        self.w, self.h = w, h
        self.time = 0.0
        rnd = random.Random(11)
        self.far = brick_surface(w, h, 7, (46, 42, 70), (20, 17, 34), (66, 60, 96), var=7, moss=0.04)
        # cột đá lớp giữa
        self.mid = pygame.Surface((w, h), pygame.SRCALPHA)
        self.pillar_x = [16, 168, 340, 476]
        for i, px in enumerate(self.pillar_x):
            pw = 22
            body = brick_surface(pw, self.GROUND_Y, 50 + i, (64, 58, 92), (24, 20, 38), (88, 82, 120), var=8, moss=0.06)
            self.mid.blit(body, (px, 0))
            ui.rect(self.mid, INK, px - 1, 0, 1, self.GROUND_Y)
            ui.rect(self.mid, INK, px + pw, 0, 1, self.GROUND_Y)
            ui.rect(self.mid, (92, 86, 122), px, 0, 1, self.GROUND_Y)
            ui.rect(self.mid, (24, 20, 38), px + pw - 1, 0, 1, self.GROUND_Y)
            # đầu cột
            ui.rect(self.mid, INK, px - 4, 30, pw + 8, 10)
            ui.rect(self.mid, (70, 64, 98), px - 3, 31, pw + 6, 3)
            ui.rect(self.mid, (46, 42, 68), px - 3, 34, pw + 6, 5)
        # xà ngang
        ui.rect(self.mid, INK, 0, 34, w, 1)
        self.ground = make_floor()
        self.ground_rect = pygame.Rect(0, self.GROUND_Y, w, h - self.GROUND_Y)
        self.torch_pos = [(78, 120), (432, 120), (254, 52 + 200)]
        self.torch_pos = [(78, 126), (432, 126), (27, 262), (487, 262)]
        xs = [28, 60, 100, 128, 380, 410, 450, 486]
        self.chains = [(x, rnd.randint(60, 190), rnd.random() * 6) for x in xs]
        self.fog = pygame.Surface((w * 2, 28), pygame.SRCALPHA)
        for _ in range(46):
            ui.rect(self.fog, (150, 150, 200, rnd.randint(10, 24)), rnd.randint(0, w * 2 - 90), rnd.randint(2, 20),
                    rnd.randint(30, 100), rnd.randint(3, 9))
        self.embers = []
        self.lightmap = pygame.Surface((w, h))
        self.ambient = (104, 102, 146)

    def update(self, dt):
        self.time += dt
        for (x, y) in self.torch_pos:
            if random.random() < dt * 5:
                self.embers.append([x + random.uniform(-3, 3), y - 8, random.uniform(-6, 6), random.uniform(-26, -12),
                                    random.uniform(1.2, 2.6), random.random() * 6])
        for e in self.embers:
            e[0] += (e[2] + math.sin(self.time * 2 + e[5]) * 6) * dt
            e[1] += e[3] * dt
            e[4] -= dt
        self.embers = [e for e in self.embers if e[4] > 0 and e[1] > 0]

    def draw(self, screen, glow=True, ground=True):
        t = self.time
        screen.blit(self.far, (0, 0))
        screen.blit(self.mid, (0, 0))
        if ground:
            screen.blit(self.ground, self.ground_rect.topleft, self.ground_rect)
            ui.rect(screen, INK, 0, self.GROUND_Y - 1, self.w, 1)
        # ánh sáng
        lm = self.lightmap
        lm.fill(self.ambient)
        for i, (x, y) in enumerate(self.torch_pos):
            k = 0.9 + 0.1 * math.sin(t * 9 + i * 2) + 0.05 * math.sin(t * 21 + i)
            ui.add_light(lm, x, y, 120, (255, 160, 80), k)
        if glow:
            ui.add_light(lm, self.w // 2, 62, 150, (130, 90, 70), 0.9 + 0.1 * math.sin(t * 2), power=2.2)
        screen.blit(lm, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        # xích
        for (x, ln, ph) in self.chains:
            sway = int(round(math.sin(t * 0.9 + ph) * 2))
            for y in range(0, ln):
                xx = x + (sway * y) // max(1, ln)
                c = (110, 104, 130) if (y // 2) % 2 == 0 else (60, 56, 80)
                ui.rect(screen, INK, xx - 2, y, 4, 1)
                ui.rect(screen, c, xx - 1, y, 2, 1)
            ui.ring(screen, (130, 124, 150), x + sway, ln + 3, 3)
        # đuốc + lửa
        for i, (x, y) in enumerate(self.torch_pos):
            sprites.draw_torch(screen, x, y, t, seed=i)
            ui.add_light(screen, x, y - 6, 22, (180, 90, 30), 0.55)
        # tàn lửa
        for x, y, vx, vy, life, ph in self.embers:
            c = (255, 190, 80) if int(t * 14 + ph) % 3 else (255, 120, 40)
            if life < 0.6:
                c = darken(c, life / 0.6)
            screen.fill(c, (int(x), int(y), 1, 1))
        # sương
        for i, (yy, spd, a) in enumerate(((250, 9, 0.9), (292, 14, 0.7), (150, 6, 0.5))):
            off = int((t * spd) % self.w)
            self.fog.set_alpha(int(255 * a))
            screen.blit(self.fog, (-off, yy))
            screen.blit(self.fog, (self.w * 2 - off - 1, yy)) if off > self.w else None
        screen.blit(ui.get_vignette(self.w, self.h, 200, 0.5), (0, 0))
