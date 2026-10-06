"""UI widgets: animated buttons, icon buttons, the HUD score card and time bar."""

import math

import pygame

from . import settings as S
from .graphics import (alpha_rect, blit_center, clamp, gradient_rounded_rect,
                       lerp, lerp_color, shade, shadow_text, soft_shadow)


class Button:
    """Rounded 'candy' button with a 3D base, hover zoom and press sink."""

    DEPTH = 6  # height of the darker base under the button face

    def __init__(self, text, center, font, theme="green", size=(300, 66), on_click=None):
        self.text = text
        self.center = center
        self.size = size
        self.on_click = on_click
        self.hover = 0.0     # 0..1 animated hover amount
        self.pressed = False
        self.is_hover = False
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        top, bottom, base = S.BUTTON_THEMES[theme]
        self.face = self._render_face(font, top, bottom)
        self.face_hover = self._render_face(font, shade(top, 0.15), shade(bottom, 0.12))
        self.base = gradient_rounded_rect(size, base, shade(base, -0.2), size[1] // 2)
        self.shadow = soft_shadow(size, size[1] // 2, alpha=70, spread=10)

    def _render_face(self, font, top, bottom):
        w, h = self.size
        face = gradient_rounded_rect(self.size, top, bottom, h // 2)
        # Glossy band on the top half
        alpha_rect(face, (255, 255, 255, 55), (8, 4, w - 16, h * 0.42), radius=h // 4)
        label = shadow_text(font, self.text, S.WHITE, shadow=(0, 0, 0), alpha=60, offset=(0, 2))
        face.blit(label, label.get_rect(center=(w / 2, h / 2)))
        return face

    def handle_event(self, event):
        """Returns True if this event was a completed click on the button."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was = self.pressed
            self.pressed = False
            if was and self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return False

    def update(self, dt):
        target = 1.0 if self.is_hover else 0.0
        self.hover += (target - self.hover) * min(1.0, dt * 14)

    def draw(self, surface):
        scale = 1.0 + 0.06 * self.hover
        sink = self.DEPTH - 2 if self.pressed else 0
        cx, cy = self.center
        blit_center(surface, self.shadow, (cx, cy + self.DEPTH + 6), scale)
        blit_center(surface, self.base, (cx, cy + self.DEPTH), scale)
        face = self.face_hover if self.hover > 0.5 else self.face
        blit_center(surface, face, (cx, cy + sink), scale)


class IconButton:
    """Round white button with a vector icon (sound on/off, home)."""

    def __init__(self, center, icon, radius=26, on_click=None):
        self.center = center
        self.icon = icon            # "sound", "mute", "home", "back", "gear"
        self.radius = radius
        self.on_click = on_click
        self.hover = 0.0
        self.is_hover = False

    def _inside(self, pos):
        return math.dist(pos, self.center) <= self.radius

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hover = self._inside(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._inside(event.pos):
            if self.on_click:
                self.on_click()
            return True
        return False

    def update(self, dt):
        target = 1.0 if self.is_hover else 0.0
        self.hover += (target - self.hover) * min(1.0, dt * 14)

    def draw(self, surface):
        r = self.radius * (1 + 0.1 * self.hover)
        size = int(r * 2 + 24)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size / 2
        pygame.draw.circle(surf, (0, 0, 0, 40), (c, c + 4), r)
        pygame.draw.circle(surf, (255, 255, 255, 235), (c, c), r)
        pygame.draw.circle(surf, (*S.INK_SOFT, 60), (c, c), r, 2)
        col = lerp_color(S.INK, (226, 40, 54), self.hover)
        self._draw_icon(surf, c, c, r * 0.5, col)
        surface.blit(surf, surf.get_rect(center=self.center))

    def _draw_icon(self, surf, x, y, s, col):
        if self.icon in ("sound", "mute"):
            # Speaker body
            pts = [(x - s * 0.95, y - s * 0.35), (x - s * 0.45, y - s * 0.35), (x + s * 0.1, y - s * 0.85),
                   (x + s * 0.1, y + s * 0.85), (x - s * 0.45, y + s * 0.35), (x - s * 0.95, y + s * 0.35)]
            pygame.draw.polygon(surf, col, pts)
            if self.icon == "sound":
                for i, rad in enumerate((s * 0.55, s * 0.95)):
                    rect = pygame.Rect(0, 0, rad * 2, rad * 2)
                    rect.center = (x + s * 0.1, y)
                    pygame.draw.arc(surf, col, rect, -0.85, 0.85, max(2, int(s * 0.18)))
            else:
                w = max(2, int(s * 0.2))
                pygame.draw.line(surf, col, (x + s * 0.4, y - s * 0.4), (x + s * 1.1, y + s * 0.4), w)
                pygame.draw.line(surf, col, (x + s * 0.4, y + s * 0.4), (x + s * 1.1, y - s * 0.4), w)
        elif self.icon == "home":
            pygame.draw.polygon(surf, col, [(x, y - s), (x + s, y - s * 0.05), (x - s, y - s * 0.05)])
            pygame.draw.rect(surf, col, (x - s * 0.65, y - s * 0.1, s * 1.3, s * 0.95))
            pygame.draw.rect(surf, (255, 255, 255), (x - s * 0.2, y + s * 0.3, s * 0.4, s * 0.55))
        elif self.icon == "gear":
            teeth = 8
            pts = []
            for i in range(teeth * 4):
                ang = 2 * math.pi * i / (teeth * 4)
                rad = s * (1.0 if (i % 4) in (0, 1) else 0.72)
                pts.append((x + math.cos(ang) * rad, y + math.sin(ang) * rad))
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.circle(surf, (255, 255, 255), (x, y), s * 0.32)
        elif self.icon == "back":
            w = max(3, int(s * 0.28))
            pygame.draw.line(surf, col, (x + s * 0.3, y - s * 0.7), (x - s * 0.4, y), w)
            pygame.draw.line(surf, col, (x - s * 0.4, y), (x + s * 0.3, y + s * 0.7), w)


class ScoreCard:
    """HUD panel showing the score with a count-up and bump animation."""

    def __init__(self, rect, assets):
        self.rect = pygame.Rect(rect)
        self.assets = assets
        self.shown = 0.0
        self.bump = 0.0
        self.panel = pygame.Surface((self.rect.w + 24, self.rect.h + 24), pygame.SRCALPHA)
        self.panel.blit(soft_shadow(self.rect.size, 18, alpha=60, spread=12), (0, 6))
        pygame.draw.rect(self.panel, (255, 255, 255, 235), (12, 12, *self.rect.size), border_radius=18)
        self.label = assets.fonts["label"].render("SCORE", True, S.INK_SOFT)

    def update(self, dt, score):
        if score > self.shown + 0.5:
            self.bump = 1.0
        self.shown += (score - self.shown) * min(1.0, dt * 10)
        if abs(score - self.shown) < 0.5:
            self.shown = score
        self.bump = max(0.0, self.bump - dt * 3)

    def draw(self, surface):
        surface.blit(self.panel, (self.rect.x - 12, self.rect.y - 12))
        blit_center(surface, self.assets.icon_apple, (self.rect.x + 30, self.rect.centery))
        surface.blit(self.label, (self.rect.x + 54, self.rect.y + 8))
        num = self.assets.fonts["hud"].render(str(int(round(self.shown))), True, S.INK)
        scale = 1 + 0.18 * math.sin(self.bump * math.pi) if self.bump > 0 else 1.0
        blit_center(surface, num, (self.rect.x + 54 + num.get_width() / 2,
                                   self.rect.y + 44), scale)


class TimeBar:
    """Horizontal countdown bar: green -> yellow -> red, pulsing when low."""

    def __init__(self, rect, assets):
        self.rect = pygame.Rect(rect)
        self.assets = assets
        self.panel = pygame.Surface((self.rect.w + 24, self.rect.h + 24), pygame.SRCALPHA)
        self.panel.blit(soft_shadow(self.rect.size, 18, alpha=60, spread=12), (0, 6))
        pygame.draw.rect(self.panel, (255, 255, 255, 235), (12, 12, *self.rect.size), border_radius=18)
        self.clock = 0.0

    def update(self, dt):
        self.clock += dt

    def draw(self, surface, remaining, total):
        """Draw the bar; `remaining=None` means free play (no time limit)."""
        surface.blit(self.panel, (self.rect.x - 12, self.rect.y - 12))
        if remaining is None:
            title = self.assets.fonts["button"].render("Free Play", True, (52, 120, 222))
            sub = self.assets.fonts["small"].render("no time limit", True, S.INK_SOFT)
            x = self.rect.x + 28
            surface.blit(title, title.get_rect(midleft=(x, self.rect.centery)))
            surface.blit(sub, sub.get_rect(midleft=(x + title.get_width() + 16, self.rect.centery + 3)))
            return
        frac = clamp(remaining / total)

        # Clock icon
        cx, cy = self.rect.x + 30, self.rect.centery
        pygame.draw.circle(surface, S.INK, (cx, cy), 15, 3)
        ang = -math.pi / 2 + 2 * math.pi * (1 - frac)
        pygame.draw.line(surface, S.INK, (cx, cy), (cx + math.cos(ang) * 10, cy + math.sin(ang) * 10), 3)
        pygame.draw.line(surface, S.INK, (cx, cy), (cx, cy - 7), 3)

        # Track
        track = pygame.Rect(self.rect.x + 56, self.rect.y + 22, self.rect.w - 140, self.rect.h - 44)
        pygame.draw.rect(surface, (220, 232, 210), track, border_radius=track.h // 2)

        # Fill colour depends on remaining time
        if frac > 0.5:
            col = lerp_color((255, 206, 72), (88, 196, 92), (frac - 0.5) * 2)
        else:
            col = lerp_color((240, 70, 70), (255, 206, 72), frac * 2)
        warn = remaining <= S.WARN_TIME and remaining > 0
        if warn:
            pulse = 0.5 + 0.5 * math.sin(self.clock * 10)
            col = lerp_color(col, (255, 150, 150), pulse * 0.5)
        fill_w = int(track.w * frac)
        if fill_w > track.h * 0.3:
            fill = gradient_rounded_rect((fill_w, track.h), shade(col, 0.2), shade(col, -0.1), track.h // 2)
            alpha_rect(fill, (255, 255, 255, 70), (4, 3, max(1, fill_w - 8), track.h * 0.35), radius=4)
            surface.blit(fill, track.topleft)

        # Seconds label
        secs = max(0, math.ceil(remaining))
        txt_col = (214, 52, 62) if warn else S.INK
        text = self.assets.fonts["hud"].render(f"{secs}", True, txt_col)
        scale = 1.0
        if warn:
            scale = 1 + 0.12 * max(0.0, math.sin((remaining % 1.0) * math.pi))
        blit_center(surface, text, (track.right + 42, self.rect.centery + 2), scale)


class Slider:
    """Horizontal 0-100% slider with a draggable knob.

    `on_change(value)` fires while dragging; `on_release(value)` once when
    the mouse button is let go (used to save settings and preview sounds).
    """

    def __init__(self, track_rect, value, font, on_change=None, on_release=None):
        self.track = pygame.Rect(track_rect)
        self.value = clamp(value)
        self.font = font
        self.on_change = on_change
        self.on_release = on_release
        self.dragging = False
        self.hover = 0.0
        self.is_hover = False

    def _hit_rect(self):
        return self.track.inflate(30, 30)

    def _set_from_x(self, x):
        value = clamp((x - self.track.x) / self.track.w)
        if abs(value - self.value) > 1e-4:
            self.value = value
            if self.on_change:
                self.on_change(value)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hit_rect().collidepoint(event.pos):
                self.dragging = True
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.is_hover = self._hit_rect().collidepoint(event.pos)
            if self.dragging:
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            if self.on_release:
                self.on_release(self.value)
            return True
        return False

    def update(self, dt):
        target = 1.0 if (self.is_hover or self.dragging) else 0.0
        self.hover += (target - self.hover) * min(1.0, dt * 14)

    def draw(self, surface):
        t = self.track
        pygame.draw.rect(surface, (220, 232, 210), t, border_radius=t.h // 2)
        fill_w = int(t.w * self.value)
        if fill_w >= t.h:
            fill = gradient_rounded_rect((fill_w, t.h), (120, 214, 110), (60, 160, 70), t.h // 2)
            surface.blit(fill, t.topleft)
        # Knob
        kx, ky = t.x + fill_w, t.centery
        r = 15 + 3 * self.hover
        alpha_rect(surface, (0, 0, 0, 50), (kx - r, ky - r + 4, r * 2, r * 2), radius=int(r))
        pygame.draw.circle(surface, S.WHITE, (kx, ky), r)
        pygame.draw.circle(surface, (60, 160, 70), (kx, ky), r, 3)
        pct = self.font.render(f"{round(self.value * 100)}%", True, S.INK)
        surface.blit(pct, pct.get_rect(midleft=(t.right + 28, t.centery)))


class Toggle:
    """On/off pill switch with a sliding knob."""

    def __init__(self, rect, get_value, on_click):
        self.rect = pygame.Rect(rect)
        self.get_value = get_value
        self.on_click = on_click
        self.pos = 1.0 if get_value() else 0.0  # animated knob position

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.inflate(16, 16).collidepoint(event.pos)):
            self.on_click()
            return True
        return False

    def update(self, dt):
        target = 1.0 if self.get_value() else 0.0
        self.pos += (target - self.pos) * min(1.0, dt * 16)

    def draw(self, surface):
        r = self.rect
        col = lerp_color((190, 200, 185), (60, 170, 80), self.pos)
        pygame.draw.rect(surface, col, r, border_radius=r.h // 2)
        kx = lerp(r.x + r.h / 2, r.right - r.h / 2, self.pos)
        pygame.draw.circle(surface, S.WHITE, (kx, r.centery), r.h / 2 - 4)
