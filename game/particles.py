"""Particle effects: juice bursts, shock rings, confetti and floating score text."""

import math
import random

import pygame

from .graphics import clamp, ease_out_back, ease_out_cubic

JUICE_COLORS = [(232, 36, 52), (255, 90, 90), (255, 150, 130), (200, 20, 40)]
LEAF_COLORS = [(80, 180, 70), (120, 210, 90)]
SPARK_COLOR = (255, 248, 200)
CONFETTI_COLORS = [(255, 90, 90), (255, 200, 60), (90, 200, 110), (90, 170, 255), (220, 120, 255)]

_dot_cache = {}


def _dot(color, radius):
    """Cached filled circle sprite (blitting is faster than drawing with alpha)."""
    key = (color, radius)
    surf = _dot_cache.get(key)
    if surf is None:
        surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (radius + 1, radius + 1), radius)
        _dot_cache[key] = surf
    return surf


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "color",
                 "gravity", "drag", "kind", "angle", "spin")

    def __init__(self, x, y, vx, vy, life, size, color, gravity=900.0,
                 drag=1.5, kind="dot"):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.size, self.color = size, color
        self.gravity, self.drag, self.kind = gravity, drag, kind
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-400, 400)

    def update(self, dt):
        self.life -= dt
        damp = math.exp(-self.drag * dt)
        self.vx *= damp
        self.vy = self.vy * damp + self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.spin * dt
        return self.life > 0

    def draw(self, surface):
        t = clamp(self.life / self.max_life)
        alpha = int(255 * min(1.0, t * 2.0))
        if self.kind == "confetti":
            w = max(2, int(self.size * abs(math.cos(math.radians(self.angle * 0.7)))))
            piece = pygame.Surface((w, int(self.size * 0.6) + 1), pygame.SRCALPHA)
            piece.fill(self.color)
            piece = pygame.transform.rotate(piece, self.angle)
            piece.set_alpha(alpha)
            surface.blit(piece, piece.get_rect(center=(int(self.x), int(self.y))))
            return
        radius = max(1, int(self.size * (0.4 + 0.6 * t)))
        dot = _dot(self.color, radius)
        dot.set_alpha(alpha)
        surface.blit(dot, (int(self.x) - radius - 1, int(self.y) - radius - 1))


class Ring:
    """Expanding circular shock-wave drawn when an apple pops."""

    def __init__(self, x, y, color, radius=34, life=0.35):
        self.x, self.y, self.color = x, y, color
        self.radius, self.life, self.max_life = radius, life, life

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        t = 1 - self.life / self.max_life
        r = int(8 + self.radius * ease_out_cubic(t))
        width = max(1, int(5 * (1 - t)) + 1)
        tmp = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(tmp, self.color, (r + 2, r + 2), r, width)
        tmp.set_alpha(int(200 * (1 - t)))
        surface.blit(tmp, (int(self.x) - r - 2, int(self.y) - r - 2))


class FloatingText:
    """'+N' text that pops in, rises and fades out."""

    def __init__(self, surf, x, y, life=1.0):
        self.surf, self.x, self.y = surf, x, y
        self.life = self.max_life = life

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        t = 1 - self.life / self.max_life
        scale = ease_out_back(clamp(t / 0.25)) if t < 0.25 else 1.0
        alpha = 255 if t < 0.6 else int(255 * (1 - (t - 0.6) / 0.4))
        y = self.y - 70 * ease_out_cubic(t)
        surf = self.surf
        if abs(scale - 1) > 0.01:
            w, h = surf.get_size()
            surf = pygame.transform.smoothscale(surf, (max(1, int(w * scale)), max(1, int(h * scale))))
        else:
            surf = surf.copy()
        surf.set_alpha(max(0, alpha))
        surface.blit(surf, surf.get_rect(center=(int(self.x), int(y))))


class ParticleSystem:
    def __init__(self):
        self.items = []

    def apple_burst(self, x, y):
        """Juice droplets, a few leaf bits, sparkles and a ring for one apple."""
        for _ in range(14):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(140, 420)
            self.items.append(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd - 160,
                                       random.uniform(0.45, 0.8), random.randint(3, 7),
                                       random.choice(JUICE_COLORS)))
        for _ in range(3):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(100, 260)
            self.items.append(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd - 200,
                                       random.uniform(0.6, 0.9), random.randint(3, 5),
                                       random.choice(LEAF_COLORS)))
        for _ in range(6):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(60, 220)
            self.items.append(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                                       random.uniform(0.3, 0.55), random.randint(2, 3),
                                       SPARK_COLOR, gravity=0, drag=3.0))
        self.items.append(Ring(x, y, (255, 255, 255)))

    def confetti(self, x, y, count=40, spread=260):
        for _ in range(count):
            ang = random.uniform(-math.pi * 0.9, -math.pi * 0.1)
            spd = random.uniform(spread * 0.5, spread * 1.6)
            self.items.append(Particle(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                                       random.uniform(1.4, 2.4), random.randint(8, 13),
                                       random.choice(CONFETTI_COLORS), gravity=420,
                                       drag=1.8, kind="confetti"))

    def add(self, item):
        self.items.append(item)

    def update(self, dt):
        self.items = [p for p in self.items if p.update(dt)]

    def draw(self, surface):
        for p in self.items:
            p.draw(surface)

    def clear(self):
        self.items.clear()
