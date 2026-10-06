"""Game: window setup, main loop at 60 FPS and fade transitions between scenes."""

import asyncio
import importlib
import os

import pygame

from . import settings as S
from .audio import AudioManager
from .graphics import Assets, render_apple
from .storage import SaveData


class Game:
    def __init__(self):
        # The browser build doesn't load pygame.mixer automatically, so import
        # it explicitly; any audio failure just means the game runs silently.
        try:
            importlib.import_module("pygame.mixer")
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except (ImportError, AttributeError, pygame.error):
            pass
        pygame.init()
        try:
            importlib.import_module("pygame.mixer")
            pygame.mixer.init()
        except (ImportError, AttributeError, pygame.error):
            pass

        # SCALED keeps the 1280x720 layout and lets F11 go fullscreen cleanly.
        # pygame defaults SCALED to nearest-neighbour upscaling, which looks
        # jagged at non-integer ratios (e.g. 1.5x on a 1080p screen); ask SDL
        # for linear filtering instead. The env var outranks pygame's default.
        os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "linear")
        # In the browser pygbag scales the canvas itself, so no SCALED flag there.
        flags = 0 if S.IS_WEB else pygame.SCALED
        self.screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H), flags)
        pygame.display.set_caption(S.TITLE)
        pygame.display.set_icon(render_apple(64, S.APPLE_NORMAL))
        if S.IS_WEB:
            # pygbag sized the page canvas before we picked 1280x720; ask its
            # page script to re-fit the canvas so it isn't squashed.
            try:
                __import__("platform").window.window_resize()
            except Exception:
                pass

        self.clock = pygame.time.Clock()
        self.save = SaveData.load()
        self.audio = AudioManager(self.save.sound, self.save.master,
                                  self.save.music, self.save.sfx)
        self.assets = Assets()
        self.running = True

        # Transition state: fade 'out' to a colour, swap scene, fade 'in'.
        self.fade = 0.0
        self.fade_phase = None
        self.pending_scene = None
        self.fade_layer = pygame.Surface((S.SCREEN_W, S.SCREEN_H))
        self.fade_layer.fill((26, 60, 34))

        from .scenes import MenuScene  # local import avoids a circular import
        self.scene = MenuScene(self)

    # -- scene management ---------------------------------------------------
    def change_scene(self, factory):
        """Start a fade transition; `factory()` builds the next scene mid-fade."""
        if self.fade_phase is None:
            self.pending_scene = factory
            self.fade_phase = "out"

    def _update_transition(self, dt):
        step = dt / S.TRANSITION_TIME
        if self.fade_phase == "out":
            self.fade = min(1.0, self.fade + step)
            if self.fade >= 1.0:
                self.scene = self.pending_scene()
                self.pending_scene = None
                self.fade_phase = "in"
        elif self.fade_phase == "in":
            self.fade = max(0.0, self.fade - step)
            if self.fade <= 0.0:
                self.fade_phase = None

    # -- global actions -----------------------------------------------------
    def toggle_sound(self):
        self.audio.set_enabled(not self.audio.enabled)
        self.save.sound = self.audio.enabled
        self.save.save()
        self.audio.play("click")

    def set_volume(self, channel, level, persist=False):
        """Change a volume level ('master' / 'music' / 'sfx').

        Sliders call this on every drag step with persist=False and once
        more with persist=True on release, so the file is written only once.
        """
        self.audio.set_volume(channel, level)
        setattr(self.save, channel, getattr(self.audio, channel))
        if persist:
            self.save.save()

    def quit(self):
        self.running = False

    # -- main loop ----------------------------------------------------------
    async def run(self):
        """Main loop. It is async so the same code runs in the browser:
        `await asyncio.sleep(0)` hands control back to the page each frame."""
        while self.running:
            # Clamp dt so a dragged/paused window doesn't cause huge jumps.
            dt = min(self.clock.tick(S.FPS) / 1000.0, 1 / 20)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11 and not S.IS_WEB:
                    pygame.display.toggle_fullscreen()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    self.toggle_sound()
                elif self.fade_phase is None:  # ignore input mid-transition
                    self.scene.handle_event(event)

            self._update_transition(dt)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            if self.fade > 0:
                self.fade_layer.set_alpha(int(255 * self.fade))
                self.screen.blit(self.fade_layer, (0, 0))
            pygame.display.flip()
            await asyncio.sleep(0)
        pygame.quit()
