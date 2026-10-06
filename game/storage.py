"""Persistent save data (high score + sound settings) stored as JSON.

The file lives in %APPDATA%/FruitBox rather than next to the .exe, because a
--onefile build runs from a temporary folder that is deleted on exit.
"""

import json
import os


def _save_dir():
    root = os.getenv("APPDATA") or os.path.expanduser("~")
    return os.path.join(root, "FruitBox")


SAVE_FILE = os.path.join(_save_dir(), "save.json")


def _volume(data, key):
    try:
        return max(0.0, min(1.0, float(data.get(key, 1.0))))
    except (TypeError, ValueError):
        return 1.0


class SaveData:
    def __init__(self, high_score=0, sound=True, master=1.0, music=1.0, sfx=1.0):
        self.high_score = high_score
        self.sound = sound
        # Volume levels 0.0-1.0 set on the Settings screen
        self.master = master
        self.music = music
        self.sfx = sfx

    @classmethod
    def load(cls):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(int(data.get("high_score", 0)), bool(data.get("sound", True)),
                       _volume(data, "master"), _volume(data, "music"), _volume(data, "sfx"))
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self):
        try:
            os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump({"high_score": self.high_score, "sound": self.sound,
                           "master": self.master, "music": self.music, "sfx": self.sfx}, f)
        except OSError:
            pass  # saving is best-effort; never crash the game over it

    def submit_score(self, score):
        """Record a finished round. Returns True if it is a new high score."""
        if score > self.high_score:
            self.high_score = score
            self.save()
            return True
        return False
