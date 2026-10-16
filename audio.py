import array
import math
import random

import pygame


class Audio:
    """Âm thanh tổng hợp bằng code (không cần file .wav/.mp3)."""

    def __init__(self, config):
        self.config = config
        self.sounds = {}
        self.ok = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            freq, size, channels = pygame.mixer.get_init()
            if size != -16:
                return
            self.rate, self.channels = freq, channels
            self._build()
            self.ok = True
        except Exception:
            self.ok = False

    # ---------- tổng hợp ----------
    def _render(self, f0, f1, dur, vol=0.4, kind="sine"):
        n = max(1, int(self.rate * dur))
        buf = array.array("h")
        phase = 0.0
        attack = max(1, int(self.rate * 0.004))
        for i in range(n):
            p = i / n
            f = f0 + (f1 - f0) * p
            phase += 2 * math.pi * f / self.rate
            if kind == "square":
                v = 0.5 if math.sin(phase) >= 0 else -0.5
            elif kind == "noise":
                v = random.uniform(-1, 1)
            else:
                v = math.sin(phase)
            env = min(1.0, i / attack) * (1 - p) ** 1.5
            s = int(v * env * vol * 32767)
            for _ in range(self.channels):
                buf.append(s)
        return buf

    def _make(self, *parts):
        buf = array.array("h")
        for p in parts:
            buf.extend(p)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _build(self):
        r = self._render
        notes = lambda fs, d, v=0.35, k="sine": [r(f, f, d, v, k) for f in fs]
        self.sounds = {
            "move": self._make(r(700, 700, 0.03, 0.18)),
            "select": self._make(r(520, 820, 0.09, 0.28, "square")),
            "back": self._make(r(620, 380, 0.09, 0.28, "square")),
            "eat": self._make(r(520, 980, 0.09, 0.35)),
            "effect": self._make(r(380, 1300, 0.2, 0.32)),
            "good": self._make(*notes([523, 659, 784, 1046], 0.08)),
            "bad": self._make(r(320, 110, 0.35, 0.3, "square")),
            "die": self._make(r(420, 60, 0.55, 0.35, "square"), r(0, 0, 0.0, 0), r(200, 200, 0.25, 0.25, "noise")),
            "record": self._make(*notes([523, 659, 784, 1046, 1318], 0.1, 0.35)),
            "count": self._make(r(700, 700, 0.12, 0.3)),
            "go": self._make(r(1000, 1250, 0.28, 0.35)),
            "pause": self._make(r(520, 400, 0.08, 0.25)),
            "levelup": self._make(*notes([392, 523, 659, 784, 1046], 0.09, 0.35)),
            "dash": self._make(r(300, 1400, 0.14, 0.3, "square"), r(0, 0, 0.0, 0), r(900, 200, 0.12, 0.18, "noise")),
            "teleport": self._make(r(1500, 250, 0.18, 0.3), r(250, 1500, 0.14, 0.3)),
            "shield": self._make(r(500, 1100, 0.22, 0.3)),
            "shield_break": self._make(r(900, 200, 0.22, 0.3, "noise"), r(600, 150, 0.15, 0.25, "square")),
            "cut": self._make(r(700, 100, 0.2, 0.3, "noise"), r(300, 80, 0.25, 0.3, "square")),
            "alert": self._make(r(950, 950, 0.07, 0.25, "square"), r(0, 0, 0.04, 0), r(950, 950, 0.07, 0.25, "square")),
            "crate": self._make(r(500, 120, 0.12, 0.3, "noise")),
            "kill": self._make(r(900, 300, 0.1, 0.3, "square"), r(300, 80, 0.15, 0.3, "noise")),
        }
        self._build_music()
        self.apply_music_volume()

    # ---------- nhạc nền (sinh bằng code, lặp vô hạn) ----------
    def _build_music(self):
        self.music = None
        try:
            rate = self.rate
            step, steps = 0.3, 32
            N = int(rate * step * steps)
            mix = [0.0] * N
            twopi = 2 * math.pi

            def add_note(start, f, dur, vol, kind="sine"):
                s0 = int(start * rate)
                n = int(dur * rate)
                w = twopi * f / rate
                atk = max(1, int(rate * 0.010))
                for i in range(n):
                    env = min(1.0, i / atk) * math.exp(-3.0 * i / n)
                    ph = math.sin(w * i)
                    if kind == "sq":
                        ph = 0.6 if ph >= 0 else -0.6
                    elif kind == "tri":
                        ph = 2 / math.pi * math.asin(ph)
                    mix[(s0 + i) % N] += ph * env * vol

            def add_hat(start, vol):
                s0 = int(start * rate)
                n = int(0.035 * rate)
                for i in range(n):
                    mix[(s0 + i) % N] += random.uniform(-1, 1) * (1 - i / n) ** 2 * vol

            chords = [
                (55.0, [220.0, 261.63, 329.63]),
                (43.65, [174.61, 220.0, 261.63]),
                (65.41, [261.63, 329.63, 392.0]),
                (49.0, [196.0, 246.94, 293.66]),
            ]
            pattern = [0, 1, 2, 1, 0, 2, 1, 2]
            for c, (bass, notes) in enumerate(chords):
                t0 = c * 8 * step
                for b in range(4):
                    add_note(t0 + b * 2 * step, bass * 2, 2 * step * 0.9, 0.17, "sq")
                for k in range(8):
                    add_note(t0 + k * step, notes[pattern[k]] * 2, 0.5, 0.10, "tri")
                    add_hat(t0 + k * step + step / 2, 0.035)
                    if k % 4 == 0:
                        add_note(t0 + k * step, 70.0, 0.18, 0.28)
            peak = max(abs(x) for x in mix) or 1.0
            scale = 0.55 * 32767 / peak
            buf = array.array("h")
            for x in mix:
                s = int(x * scale)
                for _ in range(self.channels):
                    buf.append(s)
            self.music = pygame.mixer.Sound(buffer=buf.tobytes())
            self.music.play(loops=-1)
        except Exception:
            self.music = None

    def apply_music_volume(self):
        if self.music is not None:
            try:
                self.music.set_volume(self.config.music / 10.0 * 0.6)
            except Exception:
                pass

    # ---------- phát ----------
    def play(self, name):
        if not self.ok:
            return
        s = self.sounds.get(name)
        if s is None:
            return
        try:
            s.set_volume(self.config.volume / 10.0)
            s.play()
        except Exception:
            pass
