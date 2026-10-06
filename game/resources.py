"""Locating bundled assets (works both from source and from a PyInstaller .exe)."""

import os
import sys

import pygame

# Font files looked up in assets/fonts, in order of preference per role.
FONT_FILES = {
    "display": ["LilitaOne-Regular.ttf"],   # titles, numbers, buttons
    "body": ["VarelaRound-Regular.ttf"],    # longer readable text
}

_font_cache = {}


def base_path():
    """Folder that contains the `assets` directory.

    PyInstaller --onefile unpacks bundled data into a temp folder exposed as
    sys._MEIPASS; when running from source we use the project root instead.
    """
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_path(*parts):
    return os.path.join(base_path(), "assets", *parts)


def load_font(role, size):
    """Return a cached pygame Font for a role ('display' / 'body').

    Falls back to pygame's built-in font if the TTF file is missing so the
    game still runs without the assets folder.
    """
    key = (role, size)
    if key in _font_cache:
        return _font_cache[key]
    font = None
    for name in FONT_FILES.get(role, []):
        path = asset_path("fonts", name)
        if os.path.exists(path):
            font = pygame.font.Font(path, size)
            break
    if font is None:
        font = pygame.font.Font(None, int(size * 1.3))
        font.set_bold(role == "display")
    _font_cache[key] = font
    return font
