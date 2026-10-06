"""Persistent save data (high score + sound settings) stored as JSON.

The file lives in %APPDATA%/FruitBox rather than next to the .exe, because a
--onefile build runs from a temporary folder that is deleted on exit.
"""

import json
import os
import sys

IS_WEB = sys.platform == "emscripten"
STORAGE_KEY = "fruitbox-save"


def _read_raw():
    """Return the saved JSON text, or None. In the browser this lives in
    localStorage, since pygbag's in-memory file system is wiped on reload."""
    if IS_WEB:
        import platform  # pygbag's platform module exposes the JS window
        return platform.window.localStorage.getItem(STORAGE_KEY)
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _write_raw(text):
    if IS_WEB:
        import platform
        platform.window.localStorage.setItem(STORAGE_KEY, text)
        return
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        f.write(text)


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
            raw = _read_raw()
            if not raw:
                return cls()
            data = json.loads(raw)
            return cls(int(data.get("high_score", 0)), bool(data.get("sound", True)),
                       _volume(data, "master"), _volume(data, "music"), _volume(data, "sfx"))
        except Exception:  # missing/corrupt save (or no localStorage): start fresh
            return cls()

    def save(self):
        try:
            _write_raw(json.dumps({"high_score": self.high_score, "sound": self.sound,
                                   "master": self.master, "music": self.music, "sfx": self.sfx}))
        except Exception:
            pass  # saving is best-effort; never crash the game over it

    def submit_score(self, score):
        """Record a finished round. Returns True if it is a new high score."""
        if score > self.high_score:
            self.high_score = score
            self.save()
            return True
        return False
