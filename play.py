import math
import random

import pygame

import ui
import sprites
from settings import *
from utils import *
from ui import (ParticleSystem, FloatingText, MenuList, text, text_w, rect, px, panel, fill_a)
from snake import Snake, DIR_VEC
from food import Food
from effects import Effects, EFFECT_INFO, GAMBLING_INFO
from terrain import Terrain, make_floor
from enemies import Enemy, Crates, Debris, BLOCK_SHAPES, inside
from skills import SKILLS, ORDER, SKILL_MAX, SkillState, MAX_LEVEL, xp_needed, describe

DIRS = {
    pygame.K_w: "up", pygame.K_UP: "up",
    pygame.K_s: "down", pygame.K_DOWN: "down",
    pygame.K_a: "left", pygame.K_LEFT: "left",
    pygame.K_d: "right", pygame.K_RIGHT: "right",
}

PITCH = 58                  # khoảng cách giữa các thẻ vòng quay
CARD_W, CARD_H = 52, 70
GAMBLE_SHORT = {
    "longer_tail_by_20": "+20", "die_instantly": "X", "halve_points": "1/2",
    "100_points": "+100", "shorten_tail_50%": "-50%", "become_1_pixel": "1", "lost_all_points": "0",
}
GAMBLE_LABEL = {
    "longer_tail_by_20": ("DÀI", "ĐUÔI"), "die_instantly": ("XUI", "QUÁ"), "halve_points": ("CHIA", "ĐÔI"),
    "100_points": ("TRÚNG", "LỚN"), "shorten_tail_50%": ("MẤT NỬA", "ĐUÔI"), "become_1_pixel": ("THU", "NHỎ"),
    "lost_all_points": ("MẤT", "SẠCH"),
}
FIRE7 = ((255, 250, 214), (255, 228, 134), (255, 194, 84), (255, 154, 58), (236, 104, 42), (190, 58, 42), (132, 34, 46))
GOLD7 = ((255, 246, 200), (255, 232, 150), (246, 208, 110), (232, 180, 84), (204, 146, 66), (160, 106, 52), (110, 70, 44))
RED7 = ((255, 190, 170), (255, 130, 120), (240, 84, 84), (214, 52, 66), (170, 34, 52), (120, 24, 44), (80, 16, 36))
GREEN7 = ((230, 255, 220), (170, 255, 170), (112, 240, 150), (84, 210, 130), (56, 170, 110), (40, 130, 90), (28, 90, 70))


def make_grid():
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for x in range(0, WIDTH + 1, SIZE):
        s.fill((255, 255, 255, 14), (x, 0, 1, HEIGHT))
    for y in range(0, HEIGHT + 1, SIZE):
        s.fill((255, 255, 255, 14), (0, y, WIDTH, 1))
    return s


def make_scanlines():
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 2):
        s.fill((0, 0, 0, 46), (0, y, WIDTH, 1))
    return s


class PlayScene:

    def __init__(self, app):
        self.app = app
        cfg = app.config
        self.skin = SKINS[cfg.skin % len(SKINS)]

        # --- thế giới ---
        self.snake = Snake()
        self.food = Food()
        self.effects = Effects()
        self.terrain = Terrain()
        self.crates = Crates()
        self.debris = Debris()
        self.enemies = []
        self.enemy_pending = []          # đồng hồ chờ sinh quái
        self.snake_map = {}

        # --- tiến trình ---
        self.score = 0
        self.apples = 0
        self.kills = 0
        self.level = 1
        self.xp = 0
        self.xp_disp = 0.0
        self._disp_level = 1
        self.pending_levelups = 0
        self.skills = SkillState()
        self.high_score = cfg.high_score
        self.new_record = False
        self.death_reason = ""

        # --- trạng thái kỹ năng ---
        self.shield_time = 0.0
        self.shield_hits = 0
        self.invuln = 0.0
        self.dash_left = 0
        self.dash_timer = 0.0
        self.mouse_cell = None

        # --- trạng thái game ---
        self.time = 0.0
        self.state = "countdown"   # countdown|playing|paused|dead|roulette|levelup
        self.resume_state = "countdown"
        self.countdown = 3.0
        self._last_count = 4
        self.go_timer = 0.0
        self.dead_time = 0.0
        self.rl = None
        self.lu = None

        self.base_delay = DIFFICULTY_DELAY[cfg.difficulty % len(DIFFICULTY_DELAY)]
        self.move_acc = 0.0
        self.effect_kind = None
        self.effect_left = 0.0
        self.enemy_check = 0.0

        # --- hiệu ứng ---
        self.particles = ParticleSystem()
        self.particles.enabled = cfg.particles
        self.texts = []
        self.rings = []
        self.banner = None
        self.shake = 0.0
        self.flash = 0.0
        self.lvl_flash = 0.0
        self.score_bump = 0.0

        self.floor = make_floor()
        self.grid = make_grid()
        self.scanlines = make_scanlines()
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.lightmap = pygame.Surface((WIDTH, HEIGHT))

        # --- khu vực, ánh sáng, bụi ---
        self.biome = biome_for_level(1)
        self.ambient = BIOMES[self.biome]["ambient"]
        self.flashes = []          # ánh sáng chớp nhoáng [x, y, màu, bán kính, sống, tổng]
        self.motes = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT), random.uniform(-3, 3),
                       random.uniform(-5, -1), random.random() * 6] for _ in range(34)]
        self.hitstop = 0.0
        self.white_flash = 0.0

        cx = WIDTH // 2
        self.pause_group = MenuList(
            [("Tiếp tục", "play", GOLD), ("Chơi lại", "retry", INFO), ("Về menu", "menu", WARN)],
            cx, 150, w=190, row_h=30, s=2)
        self.over_group = MenuList(
            [("Chơi lại", "retry", GOLD), ("Về menu", "menu", WARN)],
            cx, 286, w=190, row_h=29, s=2)

        self.rebuild_snake_map()
        self.food.spawn(self.occupied())
        self.effects.spawn_effect(self.occupied())
        self.effects.spawn_gambling(self.occupied())
        app.audio.play("count")

    # ======================================================
    # TIỆN ÍCH
    # ======================================================

    def rebuild_snake_map(self):
        self.snake_map = {tuple(p): i for i, p in enumerate(self.snake.pos)}

    def snake_index(self, cell):
        return self.snake_map.get(tuple(cell))

    def solid_cells(self):
        s = set(self.terrain.cells)
        s |= set(self.crates.cells)
        s |= set(self.debris.cells)
        s |= {tuple(e.pos) for e in self.enemies}
        return s

    def occupied(self, radius=3):
        occ = {tuple(p) for p in self.snake.pos}
        occ |= self.solid_cells()
        for pos in (self.food.pos, self.effects.effect_pos, self.effects.gambling_pos):
            if pos:
                occ.add(tuple(pos))
        hx, hy = self.snake.pos[-1]
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                occ.add(((hx + dx) % COLS, (hy + dy) % ROWS))
        return occ

    def cell_center(self, cell):
        return cell[0] * SIZE + SIZE // 2, cell[1] * SIZE + SIZE // 2

    def head_center(self):
        return self.cell_center(self.snake.pos[-1])

    def current_delay(self):
        base = self.base_delay * max(0.75, 1 - 0.02 * (self.level - 1))   # cấp càng cao càng nhanh
        mult = 1.0
        if self.effect_kind == "speed_up":
            mult = 0.5
        elif self.effect_kind == "slow_down":
            mult = 2.0
        return max(45.0, base * mult)

    def show_banner(self, title, sub, color):
        self.banner = {"title": title, "sub": sub, "color": color, "t": 0.0, "life": 2.0}

    def add_ring(self, x, y, color, maxr=46):
        self.rings.append([x, y, 0.0, 0.5, color, maxr * 0.5])
        self.flashes.append([x, y, color, max(24, maxr * 0.8), 0.35, 0.35])

    def float_text(self, text, x, y, color, size=22):
        self.texts.append(FloatingText(text, x, y, color, size))

    def body_color(self):
        return (255, 255, 255) if self.skin.get("rainbow") else self.skin["body"]

    # ======================================================
    # XP / CẤP ĐỘ
    # ======================================================

    def gain_xp(self, n):
        if n <= 0 or self.level >= MAX_LEVEL:
            return
        self.xp += n
        while self.level < MAX_LEVEL and self.xp >= xp_needed(self.level):
            self.xp -= xp_needed(self.level)
            self.level += 1
            self.pending_levelups += 1
        if self.level >= MAX_LEVEL:
            self.xp = 0

    def check_levelup(self):
        if self.pending_levelups > 0 and self.state == "playing":
            self.begin_levelup()

    def begin_levelup(self):
        self.pending_levelups -= 1
        opts = self.skills.upgradable()
        hx, hy = self.head_center()
        self.lvl_flash = 1.0
        self.add_ring(hx, hy, ACCENT, 120)
        self.particles.burst(hx, hy, ACCENT, n=30, speed=260)
        if not opts:
            self.score += 50
            self.score_bump = 1.0
            self.app.audio.play("levelup")
            self.show_banner(f"LÊN CẤP {self.level}!", "Đã tối đa kỹ năng: +50 điểm", GOOD)
            self.on_new_level()
            return
        self.lu = {"opts": opts, "t": 0.0, "sel": 0}
        self.state = "levelup"
        self.app.audio.play("levelup")

    def card_rects(self):
        n = len(self.lu["opts"])
        w, h, gap = 122, 176, 14
        total = n * w + (n - 1) * gap
        x0 = WIDTH // 2 - total // 2
        return [pygame.Rect(x0 + i * (w + gap), 92, w, h) for i in range(n)]

    def pick_skill(self, i):
        name = self.lu["opts"][i]
        self.skills.upgrade(name)
        lvl = self.skills.level[name]
        info = SKILLS[name]
        hx, hy = self.head_center()
        self.particles.burst(hx, hy, info["color"], n=26, speed=240)
        self.add_ring(hx, hy, info["color"], 90)
        self.app.audio.play("good")
        self.show_banner(f"{info['name'].upper()} - CẤP {lvl}", describe(name, lvl)[0], info["color"])
        self.lu = None
        self.state = "playing"
        self.on_new_level()

    def on_new_level(self):
        nb = biome_for_level(self.level)
        if nb != self.biome:
            self.biome = nb
            hx, hy = self.head_center()
            self.show_banner("KHU VỰC MỚI", BIOMES[nb]["name"], BIOMES[nb]["torch"])
            self.white_flash = 0.8
            if self.app.config.shake:
                self.shake = max(self.shake, 8.0)
        cap = min(self.level - 1, 8)
        guard = 0
        while self.crates.count_blocks() < cap and guard < 8:
            guard += 1
            self.spawn_crate_block()

    def enemy_target(self):
        return 0 if self.level < 3 else min(4, 1 + (self.level - 3) // 3)

    # ======================================================
    # SINH VẬT CẢN / QUÁI
    # ======================================================

    def spawn_crate_block(self):
        occ = self.occupied(radius=6)
        for _ in range(60):
            shape = random.choice(BLOCK_SHAPES)
            ox, oy = random.randrange(COLS - 3), random.randrange(ROWS - 3)
            cells = [(ox + dx, oy + dy) for dx, dy in shape]
            if all(c not in occ for c in cells):
                self.crates.add_block(cells)
                return True
        return False

    def spawn_enemy(self):
        occ = self.occupied(radius=3)
        hx, hy = self.snake.pos[-1]
        for _ in range(80):
            c = (random.randrange(1, COLS - 1), random.randrange(1, ROWS - 1))
            if c in occ or abs(c[0] - hx) + abs(c[1] - hy) < 14:
                continue
            self.enemies.append(Enemy(c))
            return True
        return False

    # --- giao diện cho Enemy ---
    def enemy_solid(self, cell):
        return tuple(cell) in self.terrain.cells or tuple(cell) in self.crates.cells

    def enemy_blocked(self, cell, me):
        cell = tuple(cell)
        if not inside(*cell) or self.enemy_solid(cell):
            return True
        if cell in self.debris.cells or cell in self.snake_map:
            return True
        return any(e is not me and tuple(e.pos) == cell for e in self.enemies)

    def enemy_alert(self, enemy):
        self.app.audio.play("alert")
        x, y = self.cell_center(enemy.pos)
        self.float_text("!", x, y - 22, (255, 90, 90), 30)

    def enemy_hits_snake(self, enemy, idx):
        head_idx = len(self.snake.pos) - 1
        if self.try_absorb():
            enemy.stun(1.6)
            return
        if idx >= head_idx:
            self.die("Bị quái vật húc trúng")
        else:
            self.cut_snake(idx)

    def kill_enemy(self, enemy, xp=2):
        if enemy not in self.enemies:
            return
        self.enemies.remove(enemy)
        self.kills += 1
        x, y = self.cell_center(enemy.pos)
        self.particles.burst(x, y, (255, 90, 120), n=22, speed=240)
        self.particles.burst(x, y, (170, 80, 220), n=10, speed=160)
        self.add_ring(x, y, (255, 120, 150), 60)
        self.float_text(f"+{xp} XP", x, y - 14, ACCENT)
        self.app.audio.play("kill")
        self.hitstop = max(self.hitstop, 0.07)
        self.enemy_pending.append(8.0)
        self.gain_xp(xp)

    def break_crate(self, cell):
        for c in self.crates.break_block(cell):
            x, y = self.cell_center(c)
            self.particles.burst(x, y, (190, 140, 80), n=6, speed=180, size=(2, 4.5))
        self.app.audio.play("crate")
        if self.shake < 4 and self.app.config.shake:
            self.shake = 4.0

    def break_debris(self, cell):
        cell = tuple(cell)
        if cell in self.debris.cells:
            x, y = self.cell_center(cell)
            self.particles.burst(x, y, (230, 90, 90), n=5, speed=140, size=(2, 3.5))
            del self.debris.cells[cell]

    def cut_snake(self, idx):
        snake = self.snake
        cut = snake.pos[:idx + 1]
        snake.pos = snake.pos[idx + 1:]
        col = self.body_color()
        for c in cut:
            self.debris.add(c, col)
            x, y = self.cell_center(c)
            self.particles.burst(x, y, col, n=2, speed=120, size=(2, 4))
        cx, cy = self.cell_center(cut[-1])
        self.add_ring(cx, cy, (255, 90, 90), 70)
        if self.app.config.shake:
            self.shake = max(self.shake, 9.0)
        self.flash = max(self.flash, 0.5)
        self.hitstop = max(self.hitstop, 0.12)
        self.snake.snap()
        self.app.audio.play("cut")
        hx, hy = self.head_center()
        self.float_text(f"BỊ CẮT -{len(cut)}", hx, hy - 24, (255, 110, 110), 24)
        self.rebuild_snake_map()

    # ======================================================
    # VA CHẠM / KHIÊN
    # ======================================================

    def try_absorb(self):
        """Trả về True nếu đòn đánh bị chặn (bất tử hoặc khiên)."""
        if self.invuln > 0:
            return True
        if self.shield_hits > 0:
            self.shield_hits -= 1
            self.invuln = 1.2
            if self.shield_hits <= 0:
                self.shield_time = 0.0
            hx, hy = self.head_center()
            self.particles.burst(hx, hy, (140, 210, 255), n=22, speed=240)
            self.add_ring(hx, hy, (140, 210, 255), 70)
            self.float_text("CHẶN!", hx, hy - 24, (150, 220, 255), 26)
            self.app.audio.play("shield_break")
            return True
        return False

    def hit(self, kind, cell, reason):
        """Trả về 'die' | 'block' | 'pass'."""
        if not self.try_absorb():
            self.die(reason)
            return "die"
        if kind == "wall":
            return "block"
        if kind == "crate":
            self.break_crate(cell)
        elif kind == "debris":
            self.break_debris(cell)
        elif kind == "enemy":
            for e in list(self.enemies):
                if tuple(e.pos) == tuple(cell):
                    self.kill_enemy(e, xp=1)
        return "pass"

    def enemy_at(self, cell):
        for e in self.enemies:
            if tuple(e.pos) == tuple(cell):
                return e
        return None

    def check_cell(self, nh):
        """Kiểm tra ô sắp đi vào. True = được đi."""
        c = tuple(nh)
        checks = []
        if c in self.terrain.cells:
            checks.append(("wall", "Đâm vào tường"))
        if c in self.crates.cells:
            checks.append(("crate", "Đâm vào thùng gỗ"))
        if c in self.debris.cells:
            checks.append(("debris", "Chạm vào mảnh vỡ"))
        e = self.enemy_at(c)
        if e is not None and e.state != "spawning":
            checks.append(("enemy", "Đụng phải quái vật"))
        for kind, reason in checks:
            if self.hit(kind, c, reason) != "pass":
                return False
        return True

    # ======================================================
    # DI CHUYỂN / ĂN
    # ======================================================

    def advance(self, nh):
        snake = self.snake
        eaten = None
        if nh == self.food.pos:
            eaten = "apple"
            snake.grow(1)
        elif nh == self.effects.effect_pos:
            eaten = "effect"
        elif nh == self.effects.gambling_pos:
            eaten = "gamble"

        snake.move(nh)
        self.rebuild_snake_map()
        px, py = self.cell_center(nh)

        if eaten == "apple":
            self.score += 1
            self.apples += 1
            self.score_bump = 1.0
            self.app.audio.play("eat")
            self.particles.burst(px, py, (255, 80, 90), n=14)
            self.particles.burst(px, py, (255, 255, 255), n=5, speed=120, size=(1.5, 3))
            self.add_ring(px, py, (255, 120, 130))
            self.float_text("+1", px, py - 14, (255, 220, 220))
            self.food.spawn(self.occupied())
            self.gain_xp(1)
        elif eaten == "effect":
            kind = self.effects.random_effect()
            title, sub, color = EFFECT_INFO[kind]
            self.effect_kind = kind
            self.effect_left = 5.0
            self.app.audio.play("effect")
            self.show_banner(title, sub, color)
            self.particles.burst(px, py, color, n=22, speed=220)
            self.add_ring(px, py, color, 60)
            self.effects.spawn_effect(self.occupied())
            self.gain_xp(1)
        elif eaten == "gamble":
            self.start_roulette()

    def step(self):
        snake = self.snake
        snake.apply_queued_direction()
        nh = snake.get_new_head()
        if not self.check_cell(nh):
            return
        self.advance(nh)
        if self.state != "playing":
            return
        if snake.hit_body():
            if self.hit("body", None, "Cắn vào thân mình") == "die":
                return

    # ======================================================
    # KỸ NĂNG
    # ======================================================

    def use_dash(self):
        if not self.skills.ready("dash") or self.dash_left > 0:
            return
        cells = int(self.skills.param("dash", "cells"))
        self.skills.start_cd("dash")
        self.dash_left = cells
        self.dash_timer = 0.0
        self.invuln = max(self.invuln, cells * 0.03 + 0.5)
        self.app.audio.play("dash")
        hx, hy = self.head_center()
        self.add_ring(hx, hy, SKILLS["dash"]["color"], 50)

    def dash_step(self):
        snake = self.snake
        nh = snake.get_new_head()
        c = tuple(nh)
        if c in self.terrain.cells:
            self.dash_left = 0
            hx, hy = self.head_center()
            self.particles.burst(hx, hy, (255, 220, 120), n=10, speed=160)
            if self.app.config.shake:
                self.shake = max(self.shake, 4.0)
            return
        if c in self.crates.cells:
            self.break_crate(c)
        if c in self.debris.cells:
            self.break_debris(c)
        e = self.enemy_at(c)
        if e is not None:
            self.kill_enemy(e)
        self.advance(nh)
        self.dash_left -= 1
        px, py = self.cell_center(nh)
        self.particles.burst(px, py, SKILLS["dash"]["color"], n=4, speed=90, size=(2, 4), life=(0.2, 0.45), gravity=0)
        if self.state != "playing":
            self.dash_left = 0

    def teleport_target(self):
        lvl = self.skills.level["teleport"]
        if lvl == 0:
            return None
        rng = self.skills.param("teleport", "range")
        hx, hy = self.snake.pos[-1]
        if self.mouse_cell is not None:
            tx, ty = self.mouse_cell
        else:
            d = DIR_VEC[self.snake.direction]
            tx, ty = hx + d[0] * rng, hy + d[1] * rng
        dx, dy = tx - hx, ty - hy
        dist = math.hypot(dx, dy)
        if dist < 1.5:
            return None
        if dist > rng:
            k = rng / dist
            tx, ty = hx + dx * k, hy + dy * k
        cell = (int(clamp(round(tx), 0, COLS - 1)), int(clamp(round(ty), 0, ROWS - 1)))
        blocked = self.solid_cells() | set(self.snake_map)
        for r in range(0, 3):
            cands = []
            for ddx in range(-r, r + 1):
                for ddy in range(-r, r + 1):
                    if max(abs(ddx), abs(ddy)) != r:
                        continue
                    c = (cell[0] + ddx, cell[1] + ddy)
                    if inside(*c) and c not in blocked:
                        cands.append((abs(ddx) + abs(ddy), c))
            if cands:
                cands.sort()
                return cands[0][1]
        return None

    def use_teleport(self):
        if self.skills.level["teleport"] == 0 or not self.skills.ready("teleport"):
            return
        t = self.teleport_target()
        hx, hy = self.head_center()
        if t is None:
            self.float_text("Không thể dịch chuyển!", hx, hy - 24, (255, 150, 150), 20)
            return
        self.skills.start_cd("teleport")
        col = SKILLS["teleport"]["color"]
        self.particles.burst(hx, hy, col, n=20, speed=220)
        self.add_ring(hx, hy, col, 60)
        self.app.audio.play("teleport")
        self.invuln = max(self.invuln, 0.5)
        self.advance(list(t))
        nx, ny = self.head_center()
        self.particles.burst(nx, ny, col, n=24, speed=240)
        self.add_ring(nx, ny, col, 70)

    def use_shield(self):
        if not self.skills.ready("shield"):
            return
        self.skills.start_cd("shield")
        self.shield_time = float(self.skills.param("shield", "dur"))
        self.shield_hits = int(self.skills.param("shield", "hits"))
        hx, hy = self.head_center()
        col = SKILLS["shield"]["color"]
        self.particles.burst(hx, hy, col, n=18, speed=180)
        self.add_ring(hx, hy, col, 60)
        self.app.audio.play("shield")

    # ======================================================
    # VÒNG QUAY MAY RỦI
    # ======================================================

    def start_roulette(self):
        kinds = self.effects.gambling
        result = self.effects.random_gambling()
        n, target = 48, 40
        cards = random.choices(kinds, weights=[3, 2, 4, 6, 3, 2, 5], k=n)
        cards[target] = result
        self.rl = {
            "cards": cards, "target": target, "result": result,
            "t": 0.0, "T": 4.2, "final": target * PITCH + random.uniform(-50, 50),
            "pos": 0.0, "last_tick": 0, "done": False, "hold": 0.0,
        }
        self.state = "roulette"
        self.app.audio.play("effect")
        self.effects.spawn_gambling(self.occupied())

    def update_roulette(self, dt):
        rl = self.rl
        if not rl["done"]:
            rl["t"] += dt
            p = min(1.0, rl["t"] / rl["T"])
            rl["pos"] = rl["final"] * (1 - (1 - p) ** 4)
            idx = int((rl["pos"] + PITCH / 2) // PITCH)
            if idx != rl["last_tick"]:
                rl["last_tick"] = idx
                self.app.audio.play("move")
            if p >= 1.0:
                rl["done"] = True
                good = GAMBLING_INFO[rl["result"]][3]
                self.app.audio.play("good" if good else "bad")
        else:
            rl["hold"] += dt
            if rl["hold"] >= 1.2:
                self.finish_roulette()

    def finish_roulette(self):
        kind = self.rl["result"]
        self.rl = None
        self.state = "playing"
        title, sub, color, good = GAMBLING_INFO[kind]
        self.show_banner(title, sub, color)
        hx, hy = self.head_center()
        for i in range(3):
            self.particles.burst(hx, hy, hsv_color(i / 3.0, 0.8, 1.0), n=10, speed=240)
        self.add_ring(hx, hy, color, 70)
        if not good and self.app.config.shake:
            self.shake = max(self.shake, 6.0)
        self.apply_gamble(kind)

    def apply_gamble(self, kind):
        snake = self.snake
        hx, hy = self.head_center()
        if kind == "longer_tail_by_20":
            snake.grow(20)
        elif kind == "100_points":
            self.score += 100
            self.score_bump = 1.0
            self.gain_xp(10)
            self.float_text("+10 XP", hx, hy - 24, ACCENT)
        elif kind == "halve_points":
            self.score //= 2
            self.score_bump = 1.0
        elif kind == "lost_all_points":
            self.score = 0
            self.score_bump = 1.0
        elif kind == "shorten_tail_50%":
            if len(snake.pos) > 1:
                snake.pos = snake.pos[len(snake.pos) // 2:]
            snake.growth = 0
            snake.snap()
            self.rebuild_snake_map()
        elif kind == "become_1_pixel":
            snake.pos = [snake.pos[-1]]
            snake.growth = 0
            snake.snap()
            self.rebuild_snake_map()
        elif kind == "die_instantly":
            self.die("Vận may không mỉm cười")

    # ======================================================
    # CHẾT
    # ======================================================

    def die(self, reason):
        if self.state == "dead":
            return
        self.state = "dead"
        self.death_reason = reason
        self.dead_time = 0.0
        self.dash_left = 0
        cfg = self.app.config
        hx, hy = self.head_center()
        self.particles.burst(hx, hy, self.body_color(), n=40, speed=300, size=(3, 7), life=(0.5, 1.2))
        self.particles.burst(hx, hy, (255, 90, 90), n=20, speed=200)
        self.add_ring(hx, hy, (255, 90, 90), 90)
        if cfg.shake:
            self.shake = 14.0
        self.flash = 1.0
        if self.level > cfg.best_level:
            cfg.set("best_level", self.level)
        if self.score > cfg.high_score:
            self.new_record = True
            cfg.set("high_score", self.score)
            self.high_score = self.score
            self.app.audio.play("record")
        else:
            self.app.audio.play("die")
        cfg.save()

    # ======================================================
    # INPUT
    # ======================================================

    def pause(self):
        self.resume_state = self.state
        self.state = "paused"
        self.pause_group.selected = 0
        self.app.audio.play("pause")

    def resume(self):
        self.state = self.resume_state
        self.app.audio.play("pause")

    def handle_event(self, e):
        audio = self.app.audio
        focus_lost = getattr(pygame, "WINDOWFOCUSLOST", None)
        if focus_lost is not None and e.type == focus_lost and self.state in ("countdown", "playing"):
            self.pause()
            return

        if e.type == pygame.MOUSEMOTION:
            self.mouse_cell = (int(clamp(e.pos[0] // SIZE, 0, COLS - 1)), int(clamp(e.pos[1] // SIZE, 0, ROWS - 1)))

        if self.state in ("countdown", "playing"):
            if e.type == pygame.KEYDOWN:
                if e.key in DIRS:
                    self.snake.change_direction(DIRS[e.key])
                elif e.key in (pygame.K_p, pygame.K_ESCAPE):
                    self.pause()
                elif self.state == "playing":
                    if e.key == pygame.K_SPACE:
                        self.use_dash()
                    elif e.key == pygame.K_e:
                        self.use_teleport()
                    elif e.key == pygame.K_q:
                        self.use_shield()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3 and self.state == "playing":
                self.mouse_cell = (int(clamp(e.pos[0] // SIZE, 0, COLS - 1)), int(clamp(e.pos[1] // SIZE, 0, ROWS - 1)))
                self.use_teleport()

        elif self.state == "roulette":
            skip = (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)) \
                or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)
            if skip and not self.rl["done"] and self.rl["t"] > 0.4:
                self.rl["t"] = self.rl["T"]

        elif self.state == "levelup":
            lu = self.lu
            if lu["t"] < 0.6:
                return
            n = len(lu["opts"])
            rects = self.card_rects()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    lu["sel"] = (lu["sel"] - 1) % n
                    audio.play("move")
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    lu["sel"] = (lu["sel"] + 1) % n
                    audio.play("move")
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self.pick_skill(lu["sel"])
                elif pygame.K_1 <= e.key <= pygame.K_3 and e.key - pygame.K_1 < n:
                    self.pick_skill(e.key - pygame.K_1)
            elif e.type == pygame.MOUSEMOTION:
                for i, r in enumerate(rects):
                    if r.collidepoint(e.pos) and lu["sel"] != i:
                        lu["sel"] = i
                        audio.play("move")
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(e.pos):
                        self.pick_skill(i)
                        break

        elif self.state == "paused":
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.resume()
                return
            idx = self.pause_group.handle_event(e, audio)
            if idx == 0:
                self.resume()
            elif idx == 1:
                audio.play("select")
                self.app.change_scene("play")
            elif idx == 2:
                audio.play("back")
                self.app.change_scene("menu")

        elif self.state == "dead":
            if self.dead_time < 0.7:
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                audio.play("back")
                self.app.change_scene("menu")
                return
            idx = self.over_group.handle_event(e, audio)
            if idx == 0:
                audio.play("select")
                self.app.change_scene("play")
            elif idx == 1:
                audio.play("back")
                self.app.change_scene("menu")

    # ======================================================
    # UPDATE
    # ======================================================

    def update(self, dt):
        self.time += dt
        self.particles.update(dt)
        self.texts = [t for t in self.texts if t.update(dt)]
        alive = []
        for r in self.rings:
            r[2] += dt
            if r[2] < r[3]:
                alive.append(r)
        self.rings = alive
        if self.banner:
            self.banner["t"] += dt
            if self.banner["t"] > self.banner["life"]:
                self.banner = None
        self.shake = max(0.0, self.shake - dt * 28)
        self.flash = max(0.0, self.flash - dt * 1.6)
        self.lvl_flash = max(0.0, self.lvl_flash - dt * 1.8)
        self.score_bump = max(0.0, self.score_bump - dt * 4)
        self.go_timer = max(0.0, self.go_timer - dt)
        self.food.update(dt)
        self.effects.update(dt)
        self.crates.update(dt)
        self.white_flash = max(0.0, self.white_flash - dt * 2.5)
        for f in self.flashes:
            f[4] -= dt
        self.flashes = [f for f in self.flashes if f[4] > 0]
        for m in self.motes:
            m[0] = (m[0] + (m[2] + math.sin(self.time + m[4]) * 2) * dt) % WIDTH
            m[1] = (m[1] + m[3] * dt) % HEIGHT
        tgt = BIOMES[self.biome]["ambient"]
        self.ambient = lerp_color(self.ambient, tgt, min(1.0, dt * 1.5))
        if self.skin.get("ember") and self.state in ("playing", "countdown") and random.random() < dt * 40:
            hx, hy = self.head_center()
            self.particles.burst(hx + random.uniform(-3, 3), hy - 4, (255, 150, 50), n=1, speed=40, size=(2, 3.5),
                                 life=(0.4, 0.9), gravity=-160)

        if self._disp_level != self.level:
            self._disp_level = self.level
            self.xp_disp = 0.0
        need = xp_needed(self.level)
        target = (self.xp / need) if need > 0 else 1.0
        self.xp_disp += (target - self.xp_disp) * min(1.0, dt * 8)

        if self.state == "countdown":
            self.countdown -= dt
            c = math.ceil(self.countdown)
            if 0 < c < self._last_count:
                self._last_count = c
                if c < 3:
                    self.app.audio.play("count")
            if self.countdown <= 0:
                self.state = "playing"
                self.go_timer = 0.7
                self.app.audio.play("go")
        elif self.state == "playing":
            self.update_playing(dt)
        elif self.state == "roulette":
            self.update_roulette(dt)
        elif self.state == "levelup":
            self.lu["t"] += dt
        elif self.state == "paused":
            self.pause_group.update(dt)
        elif self.state == "dead":
            self.dead_time += dt
            self.over_group.update(dt)

    def update_playing(self, dt):
        if self.hitstop > 0:
            self.hitstop -= dt
            return
        if self.effect_left > 0:
            self.effect_left -= dt
            if self.effect_left <= 0:
                self.effect_left = 0.0
                self.effect_kind = None

        self.skills.update(dt)
        self.invuln = max(0.0, self.invuln - dt)
        if self.shield_time > 0:
            self.shield_time -= dt
            if self.shield_time <= 0:
                self.shield_time = 0.0
                self.shield_hits = 0
        self.debris.update(dt)

        # --- quái vật ---
        self.rebuild_snake_map()
        for en in list(self.enemies):
            en.update(dt, self)
            if self.state != "playing":
                return
        self.enemy_check -= dt
        if self.enemy_check <= 0:
            self.enemy_check = 1.0
            if len(self.enemies) + len(self.enemy_pending) < self.enemy_target():
                self.enemy_pending.append(3.0)
        still = []
        for t in self.enemy_pending:
            t -= dt
            if t <= 0:
                if len(self.enemies) < self.enemy_target():
                    self.spawn_enemy()
            else:
                still.append(t)
        self.enemy_pending = still

        # --- di chuyển ---
        if self.dash_left > 0:
            self.dash_timer -= dt
            while self.dash_timer <= 0 and self.dash_left > 0 and self.state == "playing":
                self.dash_timer += 0.03
                self.dash_step()
        else:
            self.move_acc += dt * 1000.0
            delay = self.current_delay()
            if self.move_acc >= delay:
                self.move_acc = min(self.move_acc - delay, delay)
                self.step()
        self.check_levelup()

    # ======================================================
    # DRAW - THẾ GIỚI
    # ======================================================

    def frac(self):
        """Tiến độ trượt của rắn giữa 2 ô (làm mượt chuyển động, vẫn bám lưới pixel)."""
        if self.state != "playing" or self.dash_left > 0:
            return 1.0
        d = self.current_delay()
        return ease_out_cubic(min(1.0, (self.move_acc / d) / 0.6))

    def flame_pal(self):
        col = BIOMES[self.biome]["torch"]
        return (darken(col, 0.55), col, lighten(col, 0.45), lighten(col, 0.85))

    def draw_shadows(self, c, frac):
        L = self.shadow
        L.fill((0, 0, 0, 0))
        for (x, y) in self.snake.visual_positions(frac):
            L.fill((0, 0, 0, 84), (x + 2, y + 3, SIZE, SIZE))
        self.crates.shadows(L)
        for en in self.enemies:
            cx, cy = self.cell_center(en.pos)
            L.fill((0, 0, 0, 90), (cx - 6, cy + 4, 13, 6))
        for pos in (self.food.pos, self.effects.effect_pos, self.effects.gambling_pos):
            if pos:
                cx, cy = self.cell_center(pos)
                L.fill((0, 0, 0, 90), (cx - 3, cy + 4, 7, 2))
        c.blit(L, (0, 0))

    def apply_lighting(self, c, frac):
        t = self.time
        lm = self.lightmap
        amb = self.ambient
        if self.state == "dead":
            amb = mul_color(amb, 1.0 - 0.4 * min(1.0, self.dead_time * 2))
        lm.fill(amb)
        hx, hy = self.snake.head_pixel(frac)
        glow = hsv_color(t * 0.3, 0.55, 1.0) if self.skin.get("rainbow") else self.skin["glow"]
        flick = 0.78 + 0.05 * math.sin(t * 7) + (0.06 * math.sin(t * 23) if self.skin.get("ember") else 0)
        ui.add_light(lm, hx, hy, 58, glow, flick)
        vp = self.snake.visual_positions(frac)
        for i in range(len(vp) - 6, 0, -6):
            ui.add_light(lm, vp[i][0] + 5, vp[i][1] + 5, 18, darken(glow, 0.55), 0.45)
        fl = self.food.light(t)
        if fl:
            ui.add_light(lm, *fl[:4], fl[4])
        for l in self.effects.lights(t):
            ui.add_light(lm, *l[:4], l[4])
        for l in self.terrain.lights(t, BIOMES[self.biome]["torch"]):
            ui.add_light(lm, *l[:4], l[4], power=1.5)
        for en in self.enemies:
            if en.state == "spawning":
                continue
            cx, cy = self.cell_center(en.pos)
            if en.state == "charge":
                ui.add_light(lm, cx, cy, 38, (255, 50, 60), 1.0)
            elif en.state == "aim":
                ui.add_light(lm, cx, cy, 34, (255, 200, 80), 0.6 + 0.4 * (int(t * 14) % 2))
            else:
                ui.add_light(lm, cx, cy, 28, (150, 40, 150), 0.7)
        if self.shield_hits > 0 and self.shield_time > 0:
            ui.add_light(lm, hx, hy, 42, SKILLS["shield"]["color"], 0.8)
        for x, y, col, rad, life, mx in self.flashes:
            ui.add_light(lm, x, y, rad, col, life / mx)
        c.blit(lm, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def draw(self, screen):
        c = self.canvas
        cfg = self.app.config
        t = self.time
        frac = self.frac()
        c.blit(self.floor, (0, 0))
        if cfg.grid:
            c.blit(self.grid, (0, 0))
        self.terrain.draw(c)
        self.draw_shadows(c, frac)
        self.crates.draw(c)
        self.debris.draw(c, t)
        self.snake.draw(c, t, self.skin, dead=(self.state == "dead"), frac=frac)
        if cfg.lighting:
            self.apply_lighting(c, frac)
        self.terrain.draw_torches(c, t, self.flame_pal())
        self.draw_telegraphs(c)
        self.food.draw(c, t)
        self.effects.draw_effect(c, t)
        self.effects.draw_gambling(c, t)
        for pos, col in ((self.food.pos, (255, 90, 80)), (self.effects.effect_pos, (255, 60, 150)),
                         (self.effects.gambling_pos, hsv_color(t * 0.6, 0.7, 1.0))):
            if pos:
                cx, cy = self.cell_center(pos)
                ui.add_light(c, cx, cy, 14, col, 0.45)
        self.draw_enemies(c)
        self.draw_shield(c, frac)
        self.draw_reticle(c, frac)
        for x, y, age, life, color, maxr in self.rings:
            p = age / life
            ui.ring(c, lerp_color(color, (30, 30, 50), p * 0.7), x, y, max(1, int(maxr * ease_out_cubic(p))))
        for m in self.motes:
            tw = 0.5 + 0.5 * math.sin(t * 2 + m[4])
            c.fill(darken(BIOMES[self.biome]["dust"], 0.35 + 0.4 * tw), (int(m[0]), int(m[1]), 1, 1))
        self.particles.draw(c)
        for ft in self.texts:
            ft.draw(c)

        ox = oy = 0
        if self.shake > 0.5:
            m = max(1, int(self.shake * 0.5))
            ox, oy = random.randint(-m, m), random.randint(-m, m)
            screen.fill((6, 4, 12))
        screen.blit(c, (ox, oy))
        screen.blit(ui.get_vignette(WIDTH, HEIGHT, 200, 0.6), (0, 0))
        if self.flash > 0:
            ui.tint(screen, (255, 40, 40), int(110 * self.flash))
        if self.lvl_flash > 0:
            ui.tint(screen, (160, 255, 220), int(70 * self.lvl_flash))
        if self.white_flash > 0:
            ui.tint(screen, (255, 255, 255), int(120 * self.white_flash))

        self.draw_hud(screen)
        self.draw_banner(screen)

        if self.state == "countdown":
            self.draw_countdown(screen)
        elif self.go_timer > 0 and self.state == "playing":
            p = 1 - self.go_timer / 0.7
            text(screen, "GO!", 10 + int(4 * p), GREEN7, (WIDTH // 2, HEIGHT // 2 - 30), "center",
                 outline=INK, alpha=int(255 * (1 - p)))
        elif self.state == "roulette":
            self.draw_roulette(screen)
        elif self.state == "levelup":
            self.draw_levelup(screen)
        elif self.state == "paused":
            self.draw_pause(screen)
        elif self.state == "dead":
            self.draw_over(screen)
        if cfg.crt:
            screen.blit(self.scanlines, (0, 0))

    def draw_telegraphs(self, c):
        for en in self.enemies:
            if en.state != "aim":
                continue
            on = int(self.time * 16) % 2 == 0
            for i, cell in enumerate(en.aim_cells(self)):
                x, y = cell[0] * SIZE, cell[1] * SIZE
                fill_a(c, x + 1, y + 1, SIZE - 2, SIZE - 2, (255, 50, 60, 70 if on else 40))
                if (i + int(self.time * 20)) % 2 == 0:
                    rect(c, (255, 120, 120), x + 4, y + 4, 2, 2)
            ex, ey = self.cell_center(en.pos)
            text(c, "!", 2, (255, 230, 90), (ex, ey - 16 - (1 if on else 0)), "center")

    def draw_enemies(self, c):
        for en in self.enemies:
            cx, cy = self.cell_center(en.pos)
            prog = clamp(en.t / en.SPAWN_T, 0.0, 1.0) if en.state == "spawning" else 0.0
            sprites.draw_enemy(c, cx, cy, 12, self.time + en.age, en.state, prog)

    def draw_shield(self, c, frac):
        hx, hy = self.snake.head_pixel(frac)
        t = self.time
        if self.shield_hits > 0 and self.shield_time > 0:
            if self.shield_time > 2 or int(t * 8) % 2 == 0:
                col = SKILLS["shield"]["color"]
                for i in range(self.shield_hits):
                    ui.dashed_ring(c, lighten(col, 0.3 * i), hx, hy, 10 + i * 2, t * (0.6 if i == 0 else -0.8), 10, 0.62)
                ui.ring(c, darken(col, 0.45), hx, hy, 9)
        elif self.invuln > 0 and int(t * 12) % 2 == 0:
            ui.dashed_ring(c, (255, 255, 255), hx, hy, 9, t, 8, 0.5)

    def draw_reticle(self, c, frac):
        if self.state != "playing" or self.skills.level["teleport"] == 0:
            return
        tg = self.teleport_target()
        if tg is None:
            return
        ready = self.skills.ready("teleport")
        col = SKILLS["teleport"]["color"] if ready else (90, 84, 110)
        cx, cy = self.cell_center(tg)
        hx, hy = self.snake.head_pixel(frac)
        n = max(2, int(math.hypot(cx - hx, cy - hy) / 5))
        for i in range(1, n):
            if (i + int(self.time * 10)) % 2 == 0:
                px(c, col, hx + (cx - hx) * i / n, hy + (cy - hy) * i / n)
        r = int(5 + math.sin(self.time * 8))
        ui.ring(c, col, cx, cy, r)
        rect(c, col, cx - 1, cy - 1, 3, 3)

    # ======================================================
    # DRAW - HUD
    # ======================================================

    def draw_hud(self, screen):
        ui.stat_pill(screen, 6, 6, 84, 33, "ĐIỂM", self.score, ACCENT, self.score_bump)
        ui.stat_pill(screen, 94, 6, 70, 33, "ĐỘ DÀI", len(self.snake.pos), INFO)
        ui.stat_pill(screen, WIDTH - 90, 6, 84, 33, "KỶ LỤC", max(self.high_score, self.score), WARN)

        if self.effect_kind and self.effect_left > 0:
            title, sub, color = EFFECT_INFO[self.effect_kind]
            w, h = 120, 33
            x, y = WIDTH // 2 - w // 2, 6
            panel(screen, (x, y, w, h), accent=None, border=darken(color, 0.6), alpha=225, shadow=False, studs=False)
            ui.draw_icon(screen, "bolt" if self.effect_kind == "speed_up" else "hourglass", x + 13, y + 16, color, 1)
            text(screen, title, 1, color, (x + 26, y + 11))
            ui.bar(screen, x + 26, y + 22, w - 34, 4, self.effect_left / 5.0, color)

        self.draw_xp_bar(screen)
        self.draw_skill_slots(screen)

    def draw_xp_bar(self, screen):
        w, h = 200, 7
        x, y = WIDTH // 2 - w // 2 + 12, HEIGHT - 17
        frac = clamp(self.xp_disp, 0.0, 1.0)
        ui.bar(screen, x, y, w, h, frac, TEAL, segments=0, glow=self.lvl_flash)
        label = "MAX" if self.level >= MAX_LEVEL else f"{self.xp}/{xp_needed(self.level)} XP"
        text(screen, label, 1, TEXT, (x + w // 2, y - 6), "center")
        bx, by = x - 16, y + h // 2
        rect(screen, INK, bx - 11, by - 11, 22, 22)
        rect(screen, GOLD, bx - 10, by - 10, 20, 20)
        rect(screen, (24, 20, 40), bx - 8, by - 8, 16, 16)
        rect(screen, lighten(GOLD, 0.4), bx - 10, by - 10, 20, 1)
        text(screen, str(self.level), 1, (255, 255, 255), (bx, by), "center", outline=None)
        text(screen, "CẤP", 1, GOLD, (bx, by - 15), "center")
        if self.lvl_flash > 0:
            ui.add_light(screen, bx, by, 30, TEAL, self.lvl_flash)

    def draw_skill_slots(self, screen):
        for i, name in enumerate(ORDER):
            info = SKILLS[name]
            lvl = self.skills.level[name]
            x, y, s = 8 + i * 33, HEIGHT - 36, 28
            col = info["color"]
            ready = self.skills.ready(name)
            fl = self.skills.flash[name]
            border = lerp_color(STONE_3, col, 1.0 if ready else 0.35) if lvl > 0 else STONE_2
            rect(screen, INK, x - 1, y - 1, s + 2, s + 2)
            rect(screen, border, x, y, s, s)
            rect(screen, (16, 13, 28), x + 1, y + 1, s - 2, s - 2)
            if lvl == 0:
                ui.draw_icon(screen, "lock", x + s // 2, y + s // 2, (80, 74, 104), 1)
            else:
                ic = col if ready else lerp_color(col, (60, 56, 80), 0.65)
                ui.draw_icon(screen, info["icon"], x + s // 2, y + s // 2 - 1, ic, 2)
                cd, tot = self.skills.cd[name], self.skills.cd_total[name]
                if cd > 0:
                    oh = int((s - 2) * clamp(cd / tot, 0, 1))
                    fill_a(screen, x + 1, y + 1, s - 2, max(1, oh), (0, 0, 0, 165))
                    rect(screen, border, x + 1, y + 1 + oh, s - 2, 1) if oh < s - 2 else None
                    text(screen, str(int(math.ceil(cd))), 2, (255, 255, 255), (x + s // 2, y + s // 2), "center")
                if fl > 0:
                    ui.add_light(screen, x + s // 2, y + s // 2, 22, col, fl / 0.6)
                for k in range(lvl):
                    rect(screen, col, x + 3 + k * 4, y + 3, 3, 2)
            ui.key_cap(screen, info["key"].upper(), x + s // 2, y - 7, active=lvl > 0)
            if name == "shield" and self.shield_time > 0 and lvl > 0:
                dur = max(1.0, float(self.skills.param("shield", "dur")))
                ui.bar(screen, x + 3, y + s - 6, s - 6, 3, self.shield_time / dur, col)

    def draw_banner(self, screen):
        b = self.banner
        if not b:
            return
        t, life = b["t"], b["life"]
        appear = ease_out_cubic(min(1.0, t / 0.3))
        fade = 1.0 if t < life - 0.4 else max(0.0, (life - t) / 0.4)
        col = b["color"]
        y = 46
        h = int(52 * appear)
        fill_a(screen, 0, y, WIDTH, h, (0, 0, 0, int(150 * fade)))
        if h > 4:
            rect(screen, darken(col, 0.6), 0, y, WIDTH, 1)
            rect(screen, darken(col, 0.6), 0, y + h - 1, WIDTH, 1)
        if appear > 0.8:
            pal = tuple(lerp_color(lighten(col, 0.75), darken(col, 0.45), i / 6.0) for i in range(7))
            text(screen, b["title"], 3, pal, (WIDTH // 2, y + 8), "midtop", shadow=2, alpha=int(255 * fade))
            text(screen, b["sub"], 1, TEXT, (WIDTH // 2, y + 36), "midtop", alpha=int(230 * fade))

    def draw_countdown(self, screen):
        ui.dim(screen, 70)
        c = max(1, math.ceil(self.countdown))
        p = clamp(1 - (self.countdown - (c - 1)), 0.0, 1.0)
        s = 10 + int(6 * (1 - ease_out_cubic(p)))
        alpha = 255 if p < 0.7 else int(255 * (1 - (p - 0.7) / 0.3))
        text(screen, str(c), s, FIRE7, (WIDTH // 2, HEIGHT // 2 - 40), "center", alpha=max(0, alpha))
        text(screen, "SẴN SÀNG!", 2, GREEN7, (WIDTH // 2, HEIGHT // 2 + 38), "center", shadow=1)
        text(screen, "W A S D HOẶC PHÍM MŨI TÊN ĐỂ ĐIỀU KHIỂN", 1, TEXT, (WIDTH // 2, HEIGHT // 2 + 62), "center")

    # ======================================================
    # DRAW - OVERLAY
    # ======================================================

    def draw_roulette(self, screen):
        rl = self.rl
        ui.dim(screen, 175)
        cy = HEIGHT // 2
        band = pygame.Rect(0, cy - 48, WIDTH, 96)
        rect(screen, INK, 0, band.y - 2, WIDTH, band.h + 4)
        rect(screen, (14, 11, 26), 0, band.y, WIDTH, band.h)
        rect(screen, STONE_3, 0, band.y, WIDTH, 1)
        rect(screen, STONE_3, 0, band.bottom - 1, WIDTH, 1)
        text(screen, "VÒNG QUAY MAY RỦI", 3, GOLD7, (WIDTH // 2, cy - 96), "midtop", shadow=2)

        screen.set_clip(band.inflate(0, -4))
        for i, kind in enumerate(rl["cards"]):
            x = WIDTH // 2 + i * PITCH - rl["pos"]
            if x < -CARD_W or x > WIDTH + CARD_W:
                continue
            title, sub, color, good = GAMBLING_INFO[kind]
            r = pygame.Rect(0, 0, CARD_W, CARD_H)
            r.center = (int(x), cy)
            win = rl["done"] and i == rl["target"]
            dimmed = rl["done"] and not win
            bg = darken(color, 0.22 if not dimmed else 0.1)
            rect(screen, INK, r.x - 1, r.y - 1, r.w + 2, r.h + 2)
            rect(screen, bg, r.x, r.y, r.w, r.h)
            rect(screen, color if not dimmed else darken(color, 0.4), r.x, r.y, r.w, 3)
            frame_c = color if not dimmed else darken(color, 0.35)
            ui.frame(screen, frame_c, r.x + 1, r.y + 1, r.w - 2, r.h - 2)
            if kind == "die_instantly":
                ui.draw_icon(screen, "skull", r.centerx, r.y + 26, (255, 255, 255) if not dimmed else TEXT_DIM, 2)
            else:
                text(screen, GAMBLE_SHORT[kind], 2, (255, 255, 255) if not dimmed else TEXT_DIM, (r.centerx, r.y + 26), "center")
            l1, l2 = GAMBLE_LABEL[kind]
            text(screen, l1, 1, color if not dimmed else TEXT_DIM, (r.centerx, r.y + 46), "center", outline=None)
            text(screen, l2, 1, color if not dimmed else TEXT_DIM, (r.centerx, r.y + 56), "center", outline=None)
            if win:
                ui.add_light(screen, r.centerx, r.centery, 50, color, 0.5 + 0.3 * math.sin(self.time * 10))
        screen.set_clip(None)

        mx = WIDTH // 2
        rect(screen, (255, 215, 90), mx, cy - 46, 1, 92)
        ui.draw_arrow(screen, mx, cy - 58, "d", (255, 215, 90), 6)
        ui.draw_arrow(screen, mx, cy + 58, "u", (255, 215, 90), 6)

        if rl["done"]:
            title, sub, color, good = GAMBLING_INFO[rl["result"]]
            pal = tuple(lerp_color(lighten(color, 0.7), darken(color, 0.45), i / 6.0) for i in range(7))
            text(screen, title, 3, pal, (WIDTH // 2, cy + 74), "midtop", shadow=2)
        else:
            text(screen, "SPACE / ENTER: BỎ QUA", 1, TEXT_DIM, (WIDTH // 2, cy + 74), "midtop")

    def draw_levelup(self, screen):
        lu = self.lu
        ui.dim(screen, 185)
        t = lu["t"]
        a = int(255 * clamp(t / 0.3, 0, 1))
        s = 4 + (1 if int(self.time * 4) % 2 else 0)
        text(screen, f"LÊN CẤP {self.level}!", 4, GOLD7, (WIDTH // 2, 26), "midtop", shadow=2, alpha=a)
        text(screen, "CHỌN MỘT KỸ NĂNG ĐỂ NÂNG CẤP", 1, TEXT, (WIDTH // 2, 66), "midtop", alpha=a)

        for i, (name, r) in enumerate(zip(lu["opts"], self.card_rects())):
            e = ease_out_back(clamp((t - 0.12 * i) / 0.4, 0, 1))
            ca = clamp((t - 0.12 * i) / 0.25, 0, 1)
            if ca < 0.08:
                continue
            sel = lu["sel"] == i
            info = SKILLS[name]
            col = info["color"]
            cur = self.skills.level[name]
            rr = r.move(0, int((1 - e) * 60) - (4 if sel else 0))
            if sel:
                ui.add_light(screen, rr.centerx, rr.centery, 110, col, 0.35 + 0.1 * math.sin(self.time * 6))
            panel(screen, rr, accent=col if sel else None, fill=lerp_color((14, 12, 26), darken(col, 0.3), 0.55 if sel else 0.15),
                  alpha=int(245 * ca), border=col if sel else darken(col, 0.5), shadow=True)
            ui.draw_icon(screen, info["icon"], rr.centerx, rr.y + 34, col, 3, alpha=int(255 * ca))
            ns = 2 if text_w(info["name"], 2) <= rr.w - 8 else 1
            text(screen, info["name"].upper(), ns, (255, 255, 255), (rr.centerx, rr.y + 66), "center", alpha=int(255 * ca))
            tag = "MỚI!" if cur == 0 else f"CẤP {cur} → {cur + 1}"
            text(screen, tag, 1, col, (rr.centerx, rr.y + 84), "center", alpha=int(255 * ca))
            for k in range(SKILL_MAX):
                pc = col if k < cur + 1 else STONE_2
                rect(screen, INK, rr.centerx + (k - 1) * 12 - 4, rr.y + 96, 8, 6)
                rect(screen, pc, rr.centerx + (k - 1) * 12 - 3, rr.y + 97, 6, 4)
                if k == cur:
                    ui.frame(screen, (255, 255, 255), rr.centerx + (k - 1) * 12 - 5, rr.y + 95, 10, 8)
            yy = rr.y + 112
            for ln in describe(name, cur + 1):
                yy = ui.text_wrapped(screen, ln, 1, TEXT, rr.x + 8, yy, rr.w - 16, line_h=10, anchor="center",
                                     alpha=int(255 * ca))
                yy += 3
            ui.key_cap(screen, str(i + 1), rr.centerx, rr.bottom - 13)
        if t > 0.6:
            text(screen, "PHÍM 1 / 2 / 3, MŨI TÊN + ENTER HOẶC BẤM CHUỘT", 1, TEXT_DIM, (WIDTH // 2, 330), "midtop")

    def draw_pause(self, screen):
        ui.dim(screen, 150)
        panel(screen, (WIDTH // 2 - 110, 84, 220, 210), accent=GOLD)
        text(screen, "TẠM DỪNG", 3, GOLD7, (WIDTH // 2, 100), "midtop", shadow=2)
        self.pause_group.draw(screen)
        text(screen, "P HOẶC ESC ĐỂ TIẾP TỤC", 1, TEXT_DIM, (WIDTH // 2, 272), "midtop")

    def draw_over(self, screen):
        e = ease_out_cubic(self.dead_time / 0.45)
        ui.dim(screen, int(170 * e))
        off = int((1 - e) * 24)
        px0, py0, pw, ph = WIDTH // 2 - 150, 30 + off, 300, 322
        panel(screen, (px0, py0, pw, ph), accent=BAD, alpha=int(240 * e))
        if e < 0.6:
            return
        a = int(255 * clamp((e - 0.6) / 0.4, 0, 1))
        cx = WIDTH // 2
        text(screen, "BẠN ĐÃ CHẾT", 4, RED7, (cx, py0 + 20), "midtop", shadow=3, alpha=a)
        text(screen, self.death_reason.upper(), 1, TEXT_DIM, (cx, py0 + 56), "midtop", alpha=a)
        rect(screen, STONE_2, px0 + 24, py0 + 68, pw - 48, 1)
        text(screen, "ĐIỂM", 1, TEXT_DIM, (cx, py0 + 76), "midtop", alpha=a)
        text(screen, str(self.score), 5, (255, 255, 255), (cx, py0 + 88), "midtop", shadow=2, alpha=a)
        ui.draw_icon(screen, "crown", cx - text_w(f"KỶ LỤC: {self.high_score}", 1) // 2 - 12, py0 + 135, WARN, 1)
        text(screen, f"KỶ LỤC: {self.high_score}", 1, WARN, (cx, py0 + 131), "midtop", alpha=a)
        if self.new_record:
            s = 1 + (1 if int(self.time * 5) % 2 else 0)
            text(screen, "KỶ LỤC MỚI!", 2, GREEN7, (cx, py0 + 146), "midtop", shadow=1, alpha=a)
        stats = [("apple", self.apples, "TÁO"), ("skull", self.kills, "QUÁI HẠ"),
                 ("dash", len(self.snake.pos), "ĐỘ DÀI"), ("star", self.level, "CẤP")]
        for i, (ic, val, lab) in enumerate(stats):
            sx = px0 + 24 + int((pw - 48) * (i + 0.5) / 4)
            ui.draw_icon(screen, ic, sx, py0 + 184, TEXT, 1, alpha=a)
            text(screen, str(val), 2, (255, 255, 255), (sx, py0 + 198), "midtop", alpha=a)
            text(screen, lab, 1, TEXT_DIM, (sx, py0 + 218), "midtop", alpha=a)
        text(screen, f"CẤP CAO NHẤT: {self.app.config.best_level}", 1, TEXT_DIM, (cx, py0 + 236), "midtop", alpha=a)
        if self.dead_time > 0.7:
            self.over_group.draw(screen)
