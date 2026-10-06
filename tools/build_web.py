"""Build the browser version of Fruit Box with pygbag.

    pip install pygbag
    python tools/build_web.py           # -> build/web/  (static site)
    python tools/build_web.py --serve   # also serve it at http://localhost:8000

pygbag packs *everything* in the app folder, so we first copy only what the
game needs (main.py, game/, assets/) into a clean staging folder.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = os.path.join(ROOT, "build", "web-stage", "fruitbox")
OUT = os.path.join(ROOT, "build", "web")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.ico")


def stage():
    shutil.rmtree(os.path.dirname(STAGE), ignore_errors=True)
    os.makedirs(STAGE)
    shutil.copy2(os.path.join(ROOT, "main.py"), STAGE)
    for folder in ("game", "assets"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(STAGE, folder), ignore=IGNORE)
    make_favicon()


def make_favicon():
    """pygbag uses favicon.png from the app folder for the browser tab icon."""
    sys.path.insert(0, ROOT)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    from game import settings as S
    from game.graphics import render_apple

    pygame.init()
    pygame.image.save(render_apple(128, S.APPLE_NORMAL), os.path.join(STAGE, "favicon.png"))


def build():
    subprocess.run([sys.executable, "-m", "pygbag", "--build", "--title", "Fruit Box", STAGE],
                   check=True)
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(os.path.join(STAGE, "build", "web"), OUT)
    print(f"\nWeb build ready: {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    stage()
    build()
    if "--serve" in sys.argv:
        print("Serving at http://localhost:8000  (Ctrl+C to stop)")
        subprocess.run([sys.executable, "-m", "http.server", "8000", "--directory", OUT])
