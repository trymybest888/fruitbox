"""Fruit Box - entry point.

Run from source:   python main.py
Build the .exe:    build.bat   (see README.md)
"""

import sys


def enable_dpi_awareness():
    """Stop Windows from bitmap-stretching the window on high-DPI screens,
    which would make the game look blurry."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def main():
    enable_dpi_awareness()
    from game.core import Game
    Game().run()


if __name__ == "__main__":
    main()
