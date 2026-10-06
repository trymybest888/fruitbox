"""Sound effects and background music with volume levels and an on/off switch."""

import os

import pygame

from .resources import asset_path

# name -> (file, base volume). Final volume = base * master * sfx level.
SFX_FILES = {
    "clear": ("clear.wav", 0.55),
    "click": ("click.wav", 0.45),
    "tick": ("tick.wav", 0.5),
    "timeup": ("timeup.wav", 0.6),
    "go": ("go.wav", 0.5),
}
MUSIC_FILE = "bgm.wav"
MUSIC_VOLUME = 0.35  # base music volume; final = base * master * music level


class AudioManager:
    def __init__(self, enabled=True, master=1.0, music=1.0, sfx=1.0):
        self.enabled = enabled
        self.master, self.music, self.sfx = master, music, sfx
        self.available = pygame.mixer.get_init() is not None
        self.sounds = {}
        self.base_volume = {}
        self.music_loaded = False
        if not self.available:
            return
        for name, (filename, volume) in SFX_FILES.items():
            path = asset_path("sounds", filename)
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
                self.base_volume[name] = volume
        music_path = asset_path("sounds", MUSIC_FILE)
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            self.music_loaded = True
        self._apply_volumes()

    def _music_level(self):
        return MUSIC_VOLUME * self.master * self.music if self.enabled else 0.0

    def _apply_volumes(self):
        if not self.available:
            return
        for name, snd in self.sounds.items():
            snd.set_volume(self.base_volume[name] * self.master * self.sfx)
        if self.music_loaded:
            # Muting keeps the track running silently so it resumes in place.
            pygame.mixer.music.set_volume(self._music_level())

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def start_music(self):
        if not self.music_loaded:
            return
        pygame.mixer.music.set_volume(self._music_level())
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1, fade_ms=800)

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._apply_volumes()
        if not enabled and self.available:
            pygame.mixer.stop()

    def set_volume(self, channel, level):
        """Set 'master', 'music' or 'sfx' level (0.0 - 1.0)."""
        setattr(self, channel, max(0.0, min(1.0, level)))
        self._apply_volumes()
