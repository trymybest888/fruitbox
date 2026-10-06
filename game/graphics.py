"""Drawing helpers and pre-rendered sprites.

Everything that is expensive to draw (apples, background, board crate) is
rendered once at start-up, supersampled for smooth anti-aliased edges, and
cached in the `Assets` object.
"""

import math
import random

import pygame

from . import settings as S
from .resources import load_font

SUPERSAMPLE = 4  # sprites are drawn at 4x size then smooth-scaled down


# ---------------------------------------------------------------------------
# Math / easing
# ---------------------------------------------------------------------------
def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_out_back(t, s=1.7):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2


def shade(color, amount):
    """Lighten (amount > 0) or darken (amount < 0) an RGB colour."""
    target = (255, 255, 255) if amount > 0 else (0, 0, 0)
    return lerp_color(color, target, abs(amount))


# ---------------------------------------------------------------------------
# Generic surface helpers
# ---------------------------------------------------------------------------
def vertical_gradient(size, top, bottom):
    w, h = size
    surf = pygame.Surface(size).convert()
    for y in range(h):
        pygame.draw.line(surf, lerp_color(top, bottom, y / max(1, h - 1)), (0, y), (w, y))
    return surf


def blur(surface, factor=6):
    """Cheap blur: downscale then upscale with smooth filtering.

    For SRCALPHA surfaces, fill the transparent area with the shape's own
    colour (alpha 0) first, otherwise the blur bleeds dark edges.
    """
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1, w // factor), max(1, h // factor)))
    return pygame.transform.smoothscale(small, (w, h))


def backdrop_blur(surface, radius=3):
    """Smooth, high-quality blur for full-screen backdrops (pause / game over).

    `blur()` above is fast but looks blocky at large factors, so here we only
    halve the size, apply a real Gaussian blur, and scale back up.
    """
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (w // 2, h // 2))
    if hasattr(pygame.transform, "gaussian_blur"):  # pygame-ce 2.2+
        small = pygame.transform.gaussian_blur(small, radius)
    else:
        small = blur(small, 2)
    return pygame.transform.smoothscale(small, (w, h))


def soft_shadow(size, radius, alpha=90, spread=12):
    """A blurred dark rounded rectangle used as a drop shadow."""
    w, h = size
    surf = pygame.Surface((w + spread * 2, h + spread * 2), pygame.SRCALPHA)
    pygame.draw.rect(surf, (0, 0, 0, alpha), (spread, spread, w, h), border_radius=radius)
    return blur(surf, 5)


def alpha_rect(target, rgba, rect, radius=0, width=0):
    """Draw a translucent rounded rect blended onto `target`."""
    rect = pygame.Rect(rect)
    tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(tmp, rgba, tmp.get_rect(), width, border_radius=radius)
    target.blit(tmp, rect.topleft)


def gradient_rounded_rect(size, top, bottom, radius):
    """Rounded rectangle filled with a vertical gradient."""
    w, h = size
    grad = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(h):
        pygame.draw.line(grad, lerp_color(top, bottom, y / max(1, h - 1)), (0, y), (w, y))
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return grad


def outlined_text(font, text, color, outline=(0, 0, 0), px=2):
    """Render text with a solid outline for crisp, high-contrast labels."""
    base = font.render(text, True, color)
    edge = font.render(text, True, outline)
    w, h = base.get_width() + px * 2, base.get_height() + px * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = max(8, px * 8)
    for i in range(steps):
        a = 2 * math.pi * i / steps
        surf.blit(edge, (px + round(math.cos(a) * px), px + round(math.sin(a) * px)))
    surf.blit(base, (px, px))
    return surf


def shadow_text(font, text, color, shadow=(0, 0, 0), alpha=70, offset=(0, 3)):
    """Render text with a soft drop shadow underneath."""
    base = font.render(text, True, color)
    sh = font.render(text, True, shadow)
    sh.set_alpha(alpha)
    ox, oy = offset
    surf = pygame.Surface((base.get_width() + abs(ox), base.get_height() + abs(oy)), pygame.SRCALPHA)
    surf.blit(sh, (max(0, ox), max(0, oy)))
    surf.blit(base, (max(0, -ox), max(0, -oy)))
    return surf


def blit_center(target, surf, center, scale=1.0, alpha=255):
    """Blit `surf` centred on `center`, optionally scaled and faded."""
    scaled = abs(scale - 1.0) > 0.005
    if scaled:
        w, h = surf.get_size()
        size = (max(1, int(w * scale)), max(1, int(h * scale)))
        surf = pygame.transform.smoothscale(surf, size)
    if alpha < 255:
        if not scaled:
            surf = surf.copy()  # don't modify the cached sprite
        surf.set_alpha(max(0, int(alpha)))
    target.blit(surf, surf.get_rect(center=(int(center[0]), int(center[1]))))


# ---------------------------------------------------------------------------
# Apple sprite
# ---------------------------------------------------------------------------
def render_apple(size, palette):
    """Draw a shaded apple (no number) of `size` x `size` pixels.

    Layers: soft ground shadow -> dark outline -> radial-gradient body ->
    glossy highlight -> stem -> leaf. Drawn at SUPERSAMPLE x for smoothness.
    """
    dark, mid, light, outline = palette
    k = SUPERSAMPLE
    sz = size * k
    surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy, r = sz * 0.5, sz * 0.57, sz * 0.36

    def silhouette(target, color, grow=0.0):
        # Two upper lobes + one lower circle give the classic apple outline.
        rr = r * 0.80 + grow
        pygame.draw.circle(target, color, (cx - r * 0.30, cy - r * 0.08), rr)
        pygame.draw.circle(target, color, (cx + r * 0.30, cy - r * 0.08), rr)
        pygame.draw.circle(target, color, (cx, cy + r * 0.14), r * 0.86 + grow)

    # Ground shadow
    shadow = pygame.Surface((sz, sz), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 80),
                        (cx - r * 0.85, cy + r * 0.78, r * 1.7, r * 0.36))
    surf.blit(blur(shadow, 6), (0, 0))

    # Thin dark outline (silhouette drawn slightly larger)
    silhouette(surf, outline, grow=k * 1.3)

    # Body: radial gradient from a light spot (upper-left) to the dark edge
    body = pygame.Surface((sz, sz), pygame.SRCALPHA)
    body.fill(dark)
    hx, hy = cx - r * 0.32, cy - r * 0.38
    steps = 48
    for i in range(steps):
        t = i / (steps - 1)
        rad = lerp(r * 1.9, r * 0.12, t)
        col = lerp_color(dark, mid, t / 0.55) if t < 0.55 else lerp_color(mid, light, (t - 0.55) / 0.45)
        pygame.draw.circle(body, col, (hx, hy), rad)
    mask = pygame.Surface((sz, sz), pygame.SRCALPHA)
    silhouette(mask, (255, 255, 255, 255))
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(body, (0, 0))

    # Glossy highlight (blurred ellipse clipped to the body) + tiny sparkle
    gloss = pygame.Surface((sz, sz), pygame.SRCALPHA)
    gloss.fill((255, 255, 255, 0))  # transparent *white* so the blur has no dark fringe
    ell = pygame.Surface((int(r * 0.62), int(r * 0.34)), pygame.SRCALPHA)
    pygame.draw.ellipse(ell, (255, 255, 255, 170), ell.get_rect())
    ell = pygame.transform.rotate(ell, 32)
    gloss.blit(ell, ell.get_rect(center=(cx - r * 0.45, cy - r * 0.42)))
    gloss = blur(gloss, 3)
    pygame.draw.circle(gloss, (255, 255, 255, 220), (cx - r * 0.18, cy - r * 0.62), r * 0.07)
    gloss.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(gloss, (0, 0))

    # Stem: a short curved brown stroke
    stem_w = max(2, int(r * 0.13))
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((cx + r * 0.16 * t * t, cy - r * 0.72 - r * 0.45 * t))
    pygame.draw.lines(surf, (98, 60, 30), False, pts, stem_w)
    for p in (pts[0], pts[-1]):
        pygame.draw.circle(surf, (98, 60, 30), p, stem_w / 2)

    # Leaf: two-tone ellipse with a vein, rotated to point up-right
    lw, lh = int(r * 0.95), int(r * 0.46)
    leaf = pygame.Surface((lw, lh), pygame.SRCALPHA)
    pygame.draw.ellipse(leaf, (46, 140, 52), leaf.get_rect())
    pygame.draw.ellipse(leaf, (98, 196, 82), (lw * 0.06, lh * 0.08, lw * 0.82, lh * 0.55))
    pygame.draw.line(leaf, (36, 112, 44), (lw * 0.05, lh * 0.55), (lw * 0.95, lh * 0.45), max(1, k))
    leaf = pygame.transform.rotate(leaf, 28)
    surf.blit(leaf, leaf.get_rect(center=(cx + r * 0.50, cy - r * 1.02)))

    return pygame.transform.smoothscale(surf, (size, size))


def render_glow(size, color, alpha=170):
    """Soft round glow drawn behind selected apples."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((*color, 0))  # transparent pixels share the glow colour -> clean blur
    pygame.draw.circle(surf, (*color, alpha), (size / 2, size / 2), size * 0.36)
    return blur(surf, 4)


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------
def render_background():
    """Bright lawn: soft gradient, mowed stripes, light glow, grass and flowers."""
    w, h = S.SCREEN_W, S.SCREEN_H
    bg = vertical_gradient((w, h), S.GRASS_TOP, S.GRASS_BOTTOM)
    rnd = random.Random(7)  # fixed seed -> same lawn every launch

    # Diagonal mowed-lawn stripes
    stripes = pygame.Surface((w, h), pygame.SRCALPHA)
    band = 90
    for i in range(-h // band - 2, w // band + 2):
        x = i * band * 2
        pygame.draw.polygon(stripes, (255, 255, 255, 16),
                            [(x, 0), (x + band, 0), (x + band - h * 0.4, h), (x - h * 0.4, h)])
    bg.blit(stripes, (0, 0))

    # Warm sunlight glow from the top-left
    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    glow.fill((255, 255, 220, 0))
    pygame.draw.circle(glow, (255, 255, 210, 70), (w * 0.15, -h * 0.05), h * 0.75)
    pygame.draw.circle(glow, (255, 255, 230, 40), (w * 0.85, h * 0.1), h * 0.45)
    bg.blit(blur(glow, 10), (0, 0))

    # Grass tufts and little flowers scattered around
    deco = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(140):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        col = (*shade(S.GRASS_DARK, rnd.uniform(-0.1, 0.15)), rnd.randint(50, 100))
        for blade in range(3):
            dx = (blade - 1) * 4
            pygame.draw.line(deco, col, (x + dx, y), (x + dx * 2 + rnd.uniform(-2, 2), y - rnd.uniform(7, 13)), 2)
    flower_cols = [(255, 255, 255), (255, 236, 120), (255, 196, 220)]
    for _ in range(46):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        col = rnd.choice(flower_cols)
        for a in range(5):
            ang = a * 2 * math.pi / 5
            pygame.draw.circle(deco, (*col, 170), (x + math.cos(ang) * 3.2, y + math.sin(ang) * 3.2), 2.6)
        pygame.draw.circle(deco, (255, 200, 60, 200), (x, y), 2)
    bg.blit(deco, (0, 0))
    return bg


def render_crate(size):
    """Wooden 'fruit box' frame with a cream inner tray for the board."""
    w, h = size
    surf = pygame.Surface((w + 40, h + 40), pygame.SRCALPHA)
    surf.blit(soft_shadow((w, h), 22, alpha=110, spread=20), (0, 8))
    frame = gradient_rounded_rect((w, h), S.CRATE_LIGHT, S.CRATE, 22)
    surf.blit(frame, (20, 20))
    # Wood grain lines
    grain = pygame.Surface((w, h), pygame.SRCALPHA)
    rnd = random.Random(3)
    for _ in range(26):
        y = rnd.uniform(4, h - 4)
        pygame.draw.line(grain, (*S.CRATE_DARK, 40), (8, y), (w - 8, y + rnd.uniform(-3, 3)), 2)
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=22)
    grain.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(grain, (20, 20))
    # Inner tray with an inset shadow
    inset = 10
    inner = pygame.Rect(20 + inset, 20 + inset, w - inset * 2, h - inset * 2)
    pygame.draw.rect(surf, S.CRATE_DARK, inner.inflate(4, 4), border_radius=16)
    tray = gradient_rounded_rect(inner.size, S.BOARD_BG, shade(S.BOARD_BG, -0.06), 14)
    surf.blit(tray, inner.topleft)
    top_shadow = pygame.Surface(inner.size, pygame.SRCALPHA)
    for i in range(10):
        pygame.draw.line(top_shadow, (0, 0, 0, 34 - i * 3), (0, i), (inner.w, i))
    tmask = pygame.Surface(inner.size, pygame.SRCALPHA)
    pygame.draw.rect(tmask, (255, 255, 255, 255), tmask.get_rect(), border_radius=14)
    top_shadow.blit(tmask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(top_shadow, inner.topleft)
    # Highlight along the top edge of the wood
    pygame.draw.rect(surf, (255, 230, 190, 120), (24, 22, w - 8, h - 4), 2, border_radius=22)
    return surf


# ---------------------------------------------------------------------------
# Asset cache
# ---------------------------------------------------------------------------
class Assets:
    """All pre-rendered surfaces and fonts, built once after the window opens."""

    def __init__(self):
        self.fonts = {
            "title": load_font("display", 110),
            "h1": load_font("display", 64),
            "h2": load_font("display", 42),
            "button": load_font("display", 32),
            "hud": load_font("display", 40),
            "digit": load_font("display", int(S.CELL * 0.50)),
            "label": load_font("body", 18),
            "body": load_font("body", 25),
            "small": load_font("body", 20),
        }
        self.background = render_background()
        crate_size = (S.BOARD_W + S.BOARD_PAD * 2, S.BOARD_H + S.BOARD_PAD * 2)
        self.crate = render_crate(crate_size).convert_alpha()
        self.glow = render_glow(int(S.CELL * 1.5), S.GLOW).convert_alpha()

        # One composited sprite per (value, selected) so drawing is a single blit.
        base_normal = render_apple(S.CELL, S.APPLE_NORMAL)
        base_selected = render_apple(S.CELL, S.APPLE_SELECTED)
        self.apples = {}
        self._scaled = {}
        self.cache = {}  # scene surfaces built on first use (see PlayScene)
        for value in range(1, 10):
            for selected, base, edge in ((False, base_normal, S.APPLE_NORMAL[3]),
                                         (True, base_selected, S.APPLE_SELECTED[3])):
                sprite = base.copy()
                num = outlined_text(self.fonts["digit"], str(value), S.WHITE, edge, 2)
                sprite.blit(num, num.get_rect(center=(S.CELL * 0.5, S.CELL * 0.60)))
                self.apples[(value, selected)] = sprite.convert_alpha()

        # Pre-scale the sizes the round-start drop-in animation passes through
        # (0 -> ~110% overshoot) so the first round doesn't hitch.
        for value in range(1, 10):
            for step in range(1, 23):
                self.apple_scaled(value, False, step / 20)

        # Small plain apple for the HUD score card
        self.icon_apple = render_apple(28, S.APPLE_NORMAL).convert_alpha()

    def apple(self, value, selected=False):
        return self.apples[(value, selected)]

    def apple_scaled(self, value, selected, scale):
        """Apple sprite at `scale`, rounded to 5% steps and cached, so the
        drop-in / select / pop animations don't smooth-scale every frame."""
        step = max(1, round(scale * 20))
        if step == 20:
            return self.apples[(value, selected)]
        key = (value, selected, step)
        sprite = self._scaled.get(key)
        if sprite is None:
            size = max(1, round(S.CELL * step / 20))
            sprite = pygame.transform.smoothscale(self.apples[(value, selected)], (size, size))
            self._scaled[key] = sprite
        return sprite
