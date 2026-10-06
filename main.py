"""Fruit Box - entry point.

Run from source:   python main.py
Build the .exe:    build.bat   (see README.md)
Web build:         python tools/build_web.py
"""

import asyncio
import sys

import pygame  # noqa: F401  (pygbag scans main.py's imports to know it must load pygame)


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


async def main():
    enable_dpi_awareness()
    from game.core import Game
    await Game().run()


# pygbag (web build) requires asyncio.run(main()) at the top level of main.py
asyncio.run(main())
