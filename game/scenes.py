"""Game screens: main menu, how-to-play, gameplay and game over."""

import math
import random

import pygame

from . import settings as S
from .board import Apple, Board
from .graphics import (alpha_rect, backdrop_blur, blit_center, blur, clamp, ease_out_back,
                       ease_out_cubic, outlined_text, shadow_text, soft_shadow)
from .particles import FloatingText, ParticleSystem
from .ui import Button, IconButton, ScoreCard, Slider, TimeBar, Toggle

TIME_UP = "Time's Up!"


class Scene:
    """Base class. The Game calls handle_event / update / draw every frame."""

    def __init__(self, game):
        self.game = game
        self.assets = game.assets
        self.sound_btn = IconButton((S.SCREEN_W - 52, 52), "sound", on_click=game.toggle_sound)

    def handle_event(self, event):
        pass

    def update(self, dt):
        self.sound_btn.icon = "sound" if self.game.audio.enabled else "mute"
        self.sound_btn.update(dt)

    def draw(self, surface):
        pass


def _title_text(font, text, color=S.WHITE, outline=(200, 30, 45), px=5):
    """Big outlined title with a soft shadow, rendered once."""
    txt = outlined_text(font, text, color, outline, px)
    surf = pygame.Surface((txt.get_width() + 8, txt.get_height() + 12), pygame.SRCALPHA)
    shadow = txt.copy()
    shadow.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MIN)
    shadow.set_alpha(60)
    surf.blit(shadow, (4, 10))
    surf.blit(txt, (0, 0))
    return surf


def _panel(size, radius=28, color=(255, 255, 255, 240)):
    """White rounded panel with a soft drop shadow (returned with margins)."""
    w, h = size
    surf = pygame.Surface((w + 48, h + 48), pygame.SRCALPHA)
    surf.blit(soft_shadow((w, h), radius, alpha=90, spread=24), (0, 10))
    pygame.draw.rect(surf, color, (24, 24, w, h), border_radius=radius)
    return surf


# ===========================================================================
# Main menu
# ===========================================================================
class MenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        f = self.assets.fonts
        cx = S.SCREEN_W // 2
        items = [("Play", "green", self._play), ("How to Play", "yellow", self._howto),
                 ("Settings", "blue", self._settings)]
        if not S.IS_WEB:  # a browser tab can't quit itself
            items.append(("Quit", "red", game.quit))
        y0 = 342 + (4 - len(items)) * 39  # keep the column centred
        self.buttons = [Button(text, (cx, y0 + i * 78), f["button"], theme, on_click=cb)
                        for i, (text, theme, cb) in enumerate(items)]
        self.title = _title_text(f["title"], "Fruit Box")
        self.subtitle = shadow_text(f["body"], "Drag a box  •  Make 10  •  Pop the apples!",
                                    S.WHITE, alpha=80, offset=(0, 2))
        self.t = 0.0
        # Decorative apples floating on both sides of the screen
        rnd = random.Random()
        spots = [(110, 150), (230, 330), (120, 520), (260, 640), (1170, 160),
                 (1050, 320), (1180, 500), (1020, 640), (360, 120), (920, 110)]
        self.floaters = [(x, y, rnd.randint(1, 9), rnd.uniform(1.1, 1.6),
                          rnd.uniform(0, math.tau), rnd.uniform(-12, 12)) for x, y in spots]
        game.audio.start_music()

    def _play(self):
        self.game.audio.play("click")
        self.game.change_scene(lambda: PlayScene(self.game))

    def _howto(self):
        self.game.audio.play("click")
        self.game.change_scene(lambda: HowToScene(self.game))

    def _settings(self):
        self.game.audio.play("click")
        self.game.change_scene(lambda: SettingsScene(self.game, lambda: MenuScene(self.game)))

    def handle_event(self, event):
        if self.sound_btn.handle_event(event):
            return
        for b in self.buttons:
            if b.handle_event(event):
                return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._play()

    def update(self, dt):
        super().update(dt)
        self.t += dt
        for b in self.buttons:
            b.update(dt)

    def draw(self, surface):
        surface.blit(self.assets.background, (0, 0))
        for i, (x, y, v, sc, ph, rot) in enumerate(self.floaters):
            bob = math.sin(self.t * 1.6 + ph) * 8
            ang = rot + math.sin(self.t * 1.1 + ph) * 6
            spr = pygame.transform.rotozoom(self.assets.apple(v), ang, sc)
            surface.blit(spr, spr.get_rect(center=(x, y + bob)))

        intro = ease_out_back(clamp(self.t / 0.7))
        bob = math.sin(self.t * 2.0) * 6
        blit_center(surface, self.title, (S.SCREEN_W / 2, 158 + bob), scale=max(0.01, intro))
        blit_center(surface, self.subtitle, (S.SCREEN_W / 2, 256), alpha=255 * clamp((self.t - 0.3) / 0.4))

        for b in self.buttons:
            b.draw(surface)

        best = self.game.save.high_score
        pill = self.assets.fonts["small"].render(f"Best score:  {best}", True, S.INK)
        rect = pill.get_rect(center=(S.SCREEN_W / 2, 664)).inflate(36, 16)
        alpha_rect(surface, (255, 255, 255, 200), rect, radius=rect.h // 2)
        surface.blit(pill, pill.get_rect(center=rect.center))

        self.sound_btn.draw(surface)


# ===========================================================================
# How to play
# ===========================================================================
class HowToScene(Scene):
    STEPS = [
        "Hold the left mouse button and drag to draw a box.",
        "Apples inside the box light up, and their sum is shown.",
        "If the sum is exactly 10, the apples pop!",
        "Each apple popped = 1 point. You have 120 seconds.",
    ]
    DEMO_VALUES = [4, 3, 7, 8, 2]
    DEMO_CYCLE = 3.4

    def __init__(self, game):
        super().__init__(game)
        f = self.assets.fonts
        self.title = _title_text(f["h1"], "How to Play", px=4)
        self.panel = _panel((900, 450))
        self.lines = [f["body"].render(s, True, S.INK) for s in self.STEPS]
        keys = "ESC  back to menu      M  sound on/off"
        if not S.IS_WEB:
            keys += "      F11  fullscreen"
        self.keys = f["small"].render(keys,
                                      True, S.INK_SOFT)
        self.buttons = [
            Button("Back", (S.SCREEN_W // 2 - 160, 650), f["button"], "yellow", (260, 62), self._back),
            Button("Play", (S.SCREEN_W // 2 + 160, 650), f["button"], "green", (260, 62), self._play),
        ]
        self.particles = ParticleSystem()
        self.demo_t = 0.0
        self.demo_cleared = False
        self._reset_demo()

    def _reset_demo(self):
        spacing = 74
        x0 = S.SCREEN_W / 2 - spacing * 2
        self.demo = [Apple(i, 0, v, (x0 + i * spacing, 222), i * 0.05)
                     for i, v in enumerate(self.DEMO_VALUES)]
        self.demo_cleared = False

    def _back(self):
        self.game.audio.play("click")
        self.game.change_scene(lambda: MenuScene(self.game))

    def _play(self):
        self.game.audio.play("click")
        self.game.change_scene(lambda: PlayScene(self.game))

    def handle_event(self, event):
        if self.sound_btn.handle_event(event):
            return
        for b in self.buttons:
            if b.handle_event(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()

    def _demo_rect(self):
        """Animated selection box sweeping over the '3' and '7' apples."""
        t = self.demo_t
        if t < 0.5 or self.demo_cleared:
            return None
        a, b = self.demo[1].center, self.demo[2].center
        start = (a[0] - 34, a[1] - 34)
        grow = ease_out_cubic(clamp((t - 0.5) / 0.9))
        end = (start[0] + (b[0] + 34 - start[0]) * grow, start[1] + 68 * min(1.0, grow * 2))
        return pygame.Rect(start, (max(1, end[0] - start[0]), max(1, end[1] - start[1])))

    def update(self, dt):
        super().update(dt)
        for b in self.buttons:
            b.update(dt)
        self.demo_t += dt
        rect = self._demo_rect()
        sel = [a for a in self.demo if a.alive and rect and rect.collidepoint(a.center)]
        for a in self.demo:
            a.selected = a in sel
        if not self.demo_cleared and self.demo_t >= 1.9:
            for a in self.demo[1:3]:
                a.pop()
                self.particles.apple_burst(*a.center)
            self.demo_cleared = True
        for a in self.demo:
            a.update(dt)
        self.demo = [a for a in self.demo if not a.finished]
        self.particles.update(dt)
        if self.demo_t >= self.DEMO_CYCLE:
            self.demo_t = 0.0
            self._reset_demo()

    def draw(self, surface):
        surface.blit(self.assets.background, (0, 0))
        blit_center(surface, self.title, (S.SCREEN_W / 2, 66))
        panel_rect = self.panel.get_rect(center=(S.SCREEN_W / 2, 350))
        surface.blit(self.panel, panel_rect)

        # Demo strip
        strip = pygame.Rect(0, 0, 420, 96)
        strip.center = (S.SCREEN_W / 2, 222)
        alpha_rect(surface, (*S.BOARD_BG, 255), strip, radius=18)
        pygame.draw.rect(surface, (*S.CRATE, ), strip, 3, border_radius=18)
        rect = self._demo_rect()
        sel_sum = sum(a.value for a in self.demo if a.selected)
        if rect:
            _draw_selection(surface, rect, sel_sum, self.assets, "fill")
        for a in self.demo:
            a.draw(surface, self.assets)
        if rect:
            _draw_selection(surface, rect, sel_sum, self.assets, "top")
        self.particles.draw(surface)

        # Numbered steps
        y = 312
        x = S.SCREEN_W / 2 - 400
        for i, line in enumerate(self.lines):
            pygame.draw.circle(surface, (226, 40, 54), (x + 18, y + 14), 18)
            n = self.assets.fonts["button"].render(str(i + 1), True, S.WHITE)
            surface.blit(n, n.get_rect(center=(x + 18, y + 15)))
            surface.blit(line, (x + 54, y))
            y += 54
        surface.blit(self.keys, self.keys.get_rect(center=(S.SCREEN_W / 2, 548)))

        for b in self.buttons:
            b.draw(surface)
        self.sound_btn.draw(surface)


# ===========================================================================
# Settings
# ===========================================================================
class SettingsScene(Scene):
    """Volume sliders + sound on/off. `back` is a factory for the scene to
    return to (a new MenuScene, or the paused PlayScene instance)."""

    CHANNELS = [("master", "Master volume"), ("music", "Music"), ("sfx", "Sound effects")]

    def __init__(self, game, back, backdrop=None):
        super().__init__(game)
        self.back = back
        self.backdrop = backdrop
        f = self.assets.fonts
        self.title = _title_text(f["h1"], "Settings", outline=(52, 120, 222), px=4)
        self.panel = _panel((760, 420), color=(255, 255, 255, 255))
        self.rows_y = [208, 292, 376]
        self.labels = [f["body"].render(text, True, S.INK) for _, text in self.CHANNELS]
        self.sliders = []
        for (channel, _), y in zip(self.CHANNELS, self.rows_y):
            self.sliders.append(Slider(
                (560, y - 9, 330, 18), getattr(game.audio, channel), f["body"],
                on_change=lambda v, ch=channel: game.set_volume(ch, v),
                on_release=lambda v, ch=channel: self._released(ch, v)))
        self.toggle_y = 460
        self.sound_label = f["body"].render("Sound", True, S.INK)
        self.toggle = Toggle((560, self.toggle_y - 18, 76, 36),
                             lambda: game.audio.enabled, game.toggle_sound)
        self.on_txt = f["body"].render("On", True, (52, 150, 62))
        self.off_txt = f["body"].render("Off", True, S.INK_SOFT)
        self.hint = f["small"].render("Tip: press M at any time to mute / unmute", True, S.INK_SOFT)
        self.back_btn = Button("Back", (S.SCREEN_W // 2, 652), f["button"], "yellow", (260, 62), self._back)

    def _released(self, channel, value):
        self.game.set_volume(channel, value, persist=True)
        if channel != "music":
            self.game.audio.play("clear")  # preview the new effects level

    def _back(self):
        self.game.audio.play("click")
        self.game.change_scene(self.back)

    def handle_event(self, event):
        if self.sound_btn.handle_event(event) or self.toggle.handle_event(event):
            return
        for sl in self.sliders:
            if sl.handle_event(event):
                return
        if self.back_btn.handle_event(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()

    def update(self, dt):
        super().update(dt)
        for sl in self.sliders:
            sl.update(dt)
        self.toggle.update(dt)
        self.back_btn.update(dt)

    def draw(self, surface):
        surface.blit(self.backdrop or self.assets.background, (0, 0))
        blit_center(surface, self.title, (S.SCREEN_W / 2, 66))
        surface.blit(self.panel, self.panel.get_rect(center=(S.SCREEN_W / 2, 350)))
        for label, y, sl in zip(self.labels, self.rows_y, self.sliders):
            surface.blit(label, label.get_rect(midleft=(310, y)))
            sl.draw(surface)
        surface.blit(self.sound_label, self.sound_label.get_rect(midleft=(310, self.toggle_y)))
        self.toggle.draw(surface)
        state = self.on_txt if self.game.audio.enabled else self.off_txt
        surface.blit(state, state.get_rect(midleft=(656, self.toggle_y)))
        surface.blit(self.hint, self.hint.get_rect(center=(S.SCREEN_W / 2, 528)))
        self.back_btn.draw(surface)
        self.sound_btn.draw(surface)


# ===========================================================================
# Gameplay
# ===========================================================================
def _draw_selection(surface, rect, total, assets, layer, pos=None):
    """Translucent selection box; green when the sum is exactly 10.

    Drawn in two layers so the apples stay bright: the fill goes *under*
    the apples ("fill"), the outline and sum badge go *over* them ("top").
    """
    col = S.SELECT_OK if total == S.TARGET_SUM else S.SELECT_NORMAL
    if layer == "fill":
        alpha_rect(surface, (*col, 70), rect, radius=8)
        return
    alpha_rect(surface, (*col, 230), rect, radius=8, width=3)
    if pos is not None:
        label = assets.fonts["button"].render(str(total), True, S.WHITE)
        pill = label.get_rect().inflate(26, 6)
        pill.midleft = (pos[0] + 18, pos[1] + 22)
        pill.clamp_ip(pygame.Rect(0, 0, S.SCREEN_W, S.SCREEN_H))
        alpha_rect(surface, (*col, 235), pill, radius=pill.h // 2)
        surface.blit(label, label.get_rect(center=pill.center))


class PlayScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.board = Board()
        self.board.new_round()
        self.particles = ParticleSystem()
        self.score = 0
        self.remaining = S.GAME_TIME
        self.state = "ready"          # ready -> playing -> ended (-> playing again in free play)
        self.free_play = False        # True after "Continue": no timer
        self.timed_score = 0          # score at the end of the timed round (counts for Best)
        self.state_t = 0.0
        self.end_reason = ""
        self.new_record = False
        self.drag_start = None
        self.drag_pos = None
        self.selection = []
        self.leaving = False
        self._end_txt = None

        self.score_card = ScoreCard((150, 26, 220, 72), self.assets)
        self.time_bar = TimeBar((394, 26, 540, 72), self.assets)
        self.gear_btn = IconButton((980, 62), "gear", on_click=self._open_settings)
        self.sound_btn.center = (1042, 62)
        self.home_btn = IconButton((1104, 62), "home", on_click=self._to_menu)
        self.finish_btn = Button("Finish", (854, 59), self.assets.fonts["button"], "red",
                                 (130, 46), on_click=self._finish)

        f = self.assets.fonts
        self.txt_ready = _title_text(f["h1"], "Ready?", outline=(52, 120, 222), px=4)
        self.txt_go = _title_text(f["title"], "GO!", outline=(34, 140, 50), px=5)
        self.crate_pos = (S.BOARD_X - S.BOARD_PAD - 20, S.BOARD_Y - S.BOARD_PAD - 20)

    # -- helpers ------------------------------------------------------------
    def _to_menu(self):
        self.game.audio.play("click")
        self.game.change_scene(lambda: MenuScene(self.game))

    def _open_settings(self):
        """Pause by switching to Settings; it returns to this same instance."""
        if self.state == "ended":
            return
        self.game.audio.play("click")
        self._cancel_drag()
        backdrop = backdrop_blur(self.game.screen.copy())
        dim = pygame.Surface(backdrop.get_size(), pygame.SRCALPHA)
        dim.fill((20, 50, 25, 90))
        backdrop.blit(dim, (0, 0))
        self.game.change_scene(lambda: SettingsScene(self.game, lambda: self, backdrop))

    def _finish(self):
        if self.state == "playing" and self.free_play:
            self._end("Finished!")

    def resume_free_play(self):
        """Called from the Game Over screen's Continue button."""
        self.free_play = True
        self.state = "playing"
        self.state_t = 0.0            # replays the "GO!" animation
        self.leaving = False
        self._end_txt = None
        self.finish_btn.pressed = self.finish_btn.is_hover = False

    def _selection_rect(self):
        if self.drag_start is None:
            return None
        x1, y1 = self.drag_start
        x2, y2 = self.drag_pos
        return pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

    def _cancel_drag(self):
        self.drag_start = self.drag_pos = None
        self.selection = []
        self.board.set_selection([])

    def _release(self):
        """Mouse released: clear the selection if it sums to 10."""
        cleared = self.board.try_clear(self.selection)
        self._cancel_drag()
        if not cleared:
            return
        n = len(cleared)
        self.score += n
        self.game.audio.play("clear")
        for a in cleared:
            self.particles.apple_burst(*a.center)
        cx = sum(a.center[0] for a in cleared) / n
        cy = sum(a.center[1] for a in cleared) / n
        label = outlined_text(self.assets.fonts["h2"], f"+{n}", (255, 236, 90), (150, 66, 8), 3)
        self.particles.add(FloatingText(label, cx, cy))
        if not self.board.has_valid_move():
            self._end("No More Moves!")

    def _end(self, reason):
        self.state = "ended"
        self.state_t = 0.0
        self.end_reason = reason
        self._cancel_drag()
        self.game.audio.play("timeup")
        if self.free_play:
            # Extra apples from free play don't count towards the high score.
            self.new_record = False
        else:
            self.timed_score = self.score
            self.new_record = self.game.save.submit_score(self.score)

    # -- scene API ----------------------------------------------------------
    def handle_event(self, event):
        if (self.sound_btn.handle_event(event) or self.home_btn.handle_event(event)
                or self.gear_btn.handle_event(event)):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._to_menu()
            return
        if self.state != "playing":
            return
        if self.free_play and self.drag_start is None:
            if self.finish_btn.handle_event(event):
                return
            if event.type == pygame.MOUSEBUTTONDOWN and self.finish_btn.rect.collidepoint(event.pos):
                return  # press on the Finish button, not the start of a drag
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drag_start = self.drag_pos = event.pos
        elif event.type == pygame.MOUSEMOTION and self.drag_start is not None:
            self.drag_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag_start is not None:
            self.drag_pos = event.pos
            self.selection = self.board.apples_in_rect(self._selection_rect())
            self._release()
        elif event.type == pygame.WINDOWFOCUSLOST:
            self._cancel_drag()

    def update(self, dt):
        super().update(dt)
        self.home_btn.update(dt)
        self.gear_btn.update(dt)
        self.finish_btn.update(dt)
        self.state_t += dt

        if self.state == "ready":
            if self.board.intro_done and self.state_t >= S.READY_TIME:
                self.state = "playing"
                self.state_t = 0.0
                self.game.audio.play("go")
        elif self.state == "playing" and not self.free_play and self.game.fade_phase is None:
            # (the clock is frozen during scene fades, e.g. while opening Settings)
            before = math.ceil(self.remaining)
            self.remaining = max(0.0, self.remaining - dt)
            after = math.ceil(self.remaining)
            if after < before and 0 < after <= S.TICK_TIME:
                self.game.audio.play("tick")
            if self.remaining <= 0:
                self._end(TIME_UP)
        elif self.state == "ended" and self.state_t >= 1.9 and not self.leaving:
            self.leaving = True
            snapshot = self.game.screen.copy()
            self.game.change_scene(lambda: GameOverScene(self.game, self, snapshot))

        # Live selection highlight while dragging
        rect = self._selection_rect()
        if rect is not None:
            self.selection = self.board.apples_in_rect(rect)
            self.board.set_selection(self.selection)

        self.board.update(dt)
        self.particles.update(dt)
        self.score_card.update(dt, self.score)
        self.time_bar.update(dt)

    def draw(self, surface):
        surface.blit(self.assets.background, (0, 0))
        self.score_card.draw(surface)
        self.time_bar.draw(surface, None if self.free_play else self.remaining, S.GAME_TIME)
        if self.free_play and self.state == "playing":
            self.finish_btn.draw(surface)
        self.gear_btn.draw(surface)
        self.sound_btn.draw(surface)
        self.home_btn.draw(surface)

        surface.blit(self.assets.crate, self.crate_pos)
        rect = self._selection_rect()
        show = rect is not None and (rect.w > 2 or rect.h > 2)
        total = sum(a.value for a in self.selection)
        if show:
            _draw_selection(surface, rect, total, self.assets, "fill")
        self.board.draw(surface, self.assets)
        if show:
            _draw_selection(surface, rect, total, self.assets, "top", pos=self.drag_pos)

        self.particles.draw(surface)
        self._draw_overlay_text(surface)

    def _draw_overlay_text(self, surface):
        center = self.board.rect.center
        if self.state == "ready":
            t = clamp((self.state_t - 0.2) / 0.4)
            blit_center(surface, self.txt_ready, center, scale=max(0.01, ease_out_back(t)))
        elif self.state == "playing" and self.state_t < 0.7:
            t = self.state_t / 0.7
            blit_center(surface, self.txt_go, center, scale=0.6 + 0.8 * ease_out_cubic(t),
                        alpha=255 * (1 - t) ** 1.5)
        elif self.state == "ended":
            t = clamp(self.state_t / 0.35)
            band = pygame.Rect(0, 0, S.SCREEN_W, int(150 * ease_out_cubic(t)))
            band.center = center
            alpha_rect(surface, (30, 50, 30, 150), band)
            if self._end_txt is None:
                self._end_txt = _title_text(self.assets.fonts["title"], self.end_reason, px=5)
            blit_center(surface, self._end_txt, center, scale=max(0.01, ease_out_back(t)))


# ===========================================================================
# Game over
# ===========================================================================
class GameOverScene(Scene):
    def __init__(self, game, play, snapshot):
        """`play` is the finished PlayScene (kept so Continue can resume it)."""
        super().__init__(game)
        self.play = play
        self.score, self.new_record = play.score, play.new_record
        best = game.save.high_score
        # Continue is offered only when the timer ran out and moves remain.
        self.can_continue = (not play.free_play and play.end_reason == TIME_UP
                             and play.board.has_valid_move())
        f = self.assets.fonts
        # Blurred, darkened picture of the final board as the backdrop
        self.backdrop = backdrop_blur(snapshot)
        shade_layer = pygame.Surface(self.backdrop.get_size(), pygame.SRCALPHA)
        shade_layer.fill((20, 50, 25, 120))
        self.backdrop.blit(shade_layer, (0, 0))

        self.panel_w = 760 if self.can_continue else 640
        self.panel = _panel((self.panel_w, 470), color=(255, 255, 255, 255))
        self.title = _title_text(f["h1"], play.end_reason, px=4)
        self.label = f["small"].render("FINAL SCORE", True, S.INK_SOFT)
        if play.free_play:
            info = f"In {int(S.GAME_TIME)} s:  {play.timed_score}        Best score:  {best}"
        else:
            info = f"Best score:  {best}"
        self.best_txt = f["body"].render(info, True, S.INK)
        self.hint = None
        if self.can_continue:
            self.hint = f["small"].render(
                "Continue: keep playing this board, no time limit (Best = 120 s score)",
                True, S.INK_SOFT)
        self.badge = outlined_text(f["h2"], "NEW BEST!", (255, 230, 80), (200, 30, 45), 4)

        cx, y = S.SCREEN_W // 2, 540
        self.buttons = []
        if self.can_continue:
            self.buttons.append(Button("Continue", (0, y), f["button"], "blue", (190, 62), self._continue))
        self.buttons += [
            Button("Play Again", (0, y), f["button"], "green", (210, 62), self._again),
            Button("Menu", (0, y), f["button"], "yellow", (140, 62), self._menu),
        ]
        if not S.IS_WEB:
            self.buttons.append(Button("Quit", (0, y), f["button"], "red", (110, 62), game.quit))
        # Centre the row of buttons
        widths = [b.size[0] for b in self.buttons]
        x = cx - (sum(widths) + 20 * (len(widths) - 1)) / 2
        for b, w in zip(self.buttons, widths):
            b.center = (int(x + w / 2), y)
            b.rect.center = b.center
            x += w + 20

        self.particles = ParticleSystem()
        self.t = 0.0
        self.next_confetti = 0.6
        self._num_value, self._num_surf = None, None

    def _continue(self):
        self.game.audio.play("go")
        play = self.play

        def resume():
            play.resume_free_play()
            return play
        self.game.change_scene(resume)

    def _again(self):
        self.game.audio.play("click")
        self.game.change_scene(lambda: PlayScene(self.game))

    def _menu(self):
        self.game.audio.play("click")
        self.game.change_scene(lambda: MenuScene(self.game))

    def handle_event(self, event):
        if self.sound_btn.handle_event(event):
            return
        if self.t > 0.5:
            for b in self.buttons:
                if b.handle_event(event):
                    return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._menu()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._again()
            elif event.key == pygame.K_c and self.can_continue:
                self._continue()

    def update(self, dt):
        super().update(dt)
        self.t += dt
        for b in self.buttons:
            b.update(dt)
        if self.new_record and self.t >= self.next_confetti:
            self.next_confetti += 1.4
            self.particles.confetti(S.SCREEN_W * 0.3, S.SCREEN_H * 0.62, 45)
            self.particles.confetti(S.SCREEN_W * 0.7, S.SCREEN_H * 0.62, 45)
        self.particles.update(dt)

    def draw(self, surface):
        surface.blit(self.backdrop, (0, 0))
        intro = ease_out_back(clamp(self.t / 0.5))
        cx, cy = S.SCREEN_W / 2, S.SCREEN_H / 2 + 10

        # Panel + content scale in together
        content = self.panel.copy()
        pw = content.get_width()
        content.blit(self.title, self.title.get_rect(center=(pw / 2, 92)))
        content.blit(self.label, self.label.get_rect(center=(pw / 2, 166)))
        shown = int(round(self.score * ease_out_cubic(clamp((self.t - 0.3) / 1.2))))
        if shown != self._num_value:
            self._num_value = shown
            self._num_surf = outlined_text(self.assets.fonts["title"], str(shown), (226, 40, 54), S.WHITE, 3)
        num = self._num_surf
        content.blit(num, num.get_rect(center=(pw / 2, 240)))
        content.blit(self.best_txt, self.best_txt.get_rect(center=(pw / 2, 322)))
        if self.hint:
            content.blit(self.hint, self.hint.get_rect(center=(pw / 2, 362)))
        blit_center(surface, content, (cx, cy), scale=max(0.01, intro))

        if self.new_record and self.t > 1.5:
            pulse = 1 + 0.06 * math.sin(self.t * 6)
            pop = ease_out_back(clamp((self.t - 1.5) / 0.4))
            badge = pygame.transform.rotozoom(self.badge, 10, pulse * pop)
            surface.blit(badge, badge.get_rect(center=(cx + self.panel_w / 2 - 90, cy - 100)))

        self.particles.draw(surface)
        if self.t > 0.4:
            for b in self.buttons:
                b.draw(surface)
        self.sound_btn.draw(surface)
