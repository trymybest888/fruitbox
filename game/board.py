"""Apple and Board: the grid of numbered apples and the 'sum to 10' rule."""

import random

import pygame

from . import settings as S
from .graphics import blit_center, clamp, ease_out_back, ease_out_cubic


class Apple:
    INTRO_TIME = 0.35   # drop-in scale animation at the start of a round
    POP_TIME = 0.26     # pop animation when cleared

    def __init__(self, col, row, value, center, intro_delay=0.0):
        self.col, self.row = col, row
        self.value = value
        self.center = center
        self.alive = True          # False once cleared (no longer counts)
        self.popping = False
        self.pop_t = 0.0
        self.selected = False
        self.intro_t = -intro_delay
        self.sel_scale = 1.0       # smoothed hover/selection scale

    @property
    def finished(self):
        """True when the pop animation is over and the apple can be removed."""
        return self.popping and self.pop_t >= self.POP_TIME

    @property
    def intro_done(self):
        return self.intro_t >= self.INTRO_TIME

    def pop(self):
        self.alive = False
        self.popping = True
        self.selected = False

    def update(self, dt):
        self.intro_t += dt
        target = 1.12 if self.selected else 1.0
        self.sel_scale += (target - self.sel_scale) * min(1.0, dt * 18)
        if self.popping:
            self.pop_t += dt

    def draw(self, surface, assets):
        if self.popping:
            # Swell up quickly while fading out = "pop"
            t = clamp(self.pop_t / self.POP_TIME)
            blit_center(surface, assets.apple(self.value, True), self.center,
                        scale=1.0 + 0.5 * ease_out_cubic(t), alpha=255 * (1 - t) ** 1.4)
            return
        if self.intro_t <= 0:
            return
        intro = ease_out_back(clamp(self.intro_t / self.INTRO_TIME))
        if self.selected:
            blit_center(surface, assets.glow, self.center)
        blit_center(surface, assets.apple(self.value, self.selected), self.center,
                    scale=intro * self.sel_scale)


class Board:
    def __init__(self, x=S.BOARD_X, y=S.BOARD_Y):
        self.rect = pygame.Rect(x, y, S.BOARD_W, S.BOARD_H)
        self.apples = []

    # -- setup --------------------------------------------------------------
    def new_round(self):
        """Fill the grid with random 1-9 apples that drop in diagonally."""
        self.apples = []
        for row in range(S.ROWS):
            for col in range(S.COLS):
                delay = (col + row) * 0.022
                self.apples.append(Apple(col, row, random.randint(1, 9),
                                         self.cell_center(col, row), delay))

    def cell_center(self, col, row):
        return (self.rect.x + col * S.CELL + S.CELL // 2,
                self.rect.y + row * S.CELL + S.CELL // 2)

    # -- queries ------------------------------------------------------------
    def alive_apples(self):
        return [a for a in self.apples if a.alive]

    def apples_in_rect(self, rect):
        """Apples whose centre lies inside the (normalised) selection rect."""
        return [a for a in self.apples if a.alive and rect.collidepoint(a.center)]

    @property
    def intro_done(self):
        return all(a.intro_done for a in self.apples)

    def has_valid_move(self):
        """Is there any rectangle on the grid whose apples sum to exactly 10?

        Uses a 2D prefix-sum table so every rectangle is checked in O(1);
        the whole search (~8k rectangles) is instant.
        """
        grid = [[0] * S.COLS for _ in range(S.ROWS)]
        for a in self.apples:
            if a.alive:
                grid[a.row][a.col] = a.value
        pre = [[0] * (S.COLS + 1) for _ in range(S.ROWS + 1)]
        for r in range(S.ROWS):
            for c in range(S.COLS):
                pre[r + 1][c + 1] = grid[r][c] + pre[r][c + 1] + pre[r + 1][c] - pre[r][c]
        for r1 in range(S.ROWS):
            for r2 in range(r1 + 1, S.ROWS + 1):
                for c1 in range(S.COLS):
                    for c2 in range(c1 + 1, S.COLS + 1):
                        total = pre[r2][c2] - pre[r1][c2] - pre[r2][c1] + pre[r1][c1]
                        if total == S.TARGET_SUM:
                            return True
                        if total > S.TARGET_SUM:
                            break  # widening only adds more
        return False

    # -- actions ------------------------------------------------------------
    def set_selection(self, selected):
        chosen = set(id(a) for a in selected)
        for a in self.apples:
            a.selected = a.alive and id(a) in chosen

    def try_clear(self, selected):
        """Pop the selected apples if they sum to 10. Returns apples cleared."""
        if selected and sum(a.value for a in selected) == S.TARGET_SUM:
            for a in selected:
                a.pop()
            return list(selected)
        return []

    def update(self, dt):
        for a in self.apples:
            a.update(dt)
        self.apples = [a for a in self.apples if not a.finished]

    def draw(self, surface, assets):
        # Draw order: idle apples, then selected (on top, enlarged), then pops.
        for a in self.apples:
            if a.alive and not a.selected:
                a.draw(surface, assets)
        for a in self.apples:
            if a.alive and a.selected:
                a.draw(surface, assets)
        for a in self.apples:
            if a.popping:
                a.draw(surface, assets)
