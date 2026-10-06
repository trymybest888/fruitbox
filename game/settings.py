"""Global constants: window, board layout, timing and colour palette."""

import sys

# True when running in the browser via pygbag (Python compiled to WebAssembly)
IS_WEB = sys.platform == "emscripten"

# --- Window -----------------------------------------------------------------
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
TITLE = "Fruit Box"

# --- Board ------------------------------------------------------------------
COLS, ROWS = 17, 10
CELL = 56                      # pixel size of one grid cell
TARGET_SUM = 10                # selected apples must add up to exactly this
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
BOARD_X = (SCREEN_W - BOARD_W) // 2
BOARD_Y = 128
BOARD_PAD = 14                 # padding between the crate frame and apples

# --- Timing -----------------------------------------------------------------
GAME_TIME = 120.0              # seconds per round
WARN_TIME = 10.0               # time bar turns red below this
TICK_TIME = 5                  # play a tick sound each second below this
READY_TIME = 1.4               # "Ready... Go!" intro before the clock starts
TRANSITION_TIME = 0.28         # fade-out / fade-in duration between scenes

# --- Colours ----------------------------------------------------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
INK = (44, 62, 38)             # main dark text colour (deep green-brown)
INK_SOFT = (92, 112, 80)

GRASS_TOP = (178, 230, 128)
GRASS_BOTTOM = (96, 176, 78)
GRASS_DARK = (70, 140, 60)

CRATE = (190, 128, 74)         # wooden frame around the board
CRATE_DARK = (140, 88, 48)
CRATE_LIGHT = (222, 168, 110)
BOARD_BG = (250, 252, 236)

# Apple palettes: (shadow, mid, light, outline)
APPLE_NORMAL = ((160, 16, 34), (226, 40, 54), (255, 128, 120), (112, 10, 26))
APPLE_SELECTED = ((214, 104, 18), (255, 160, 40), (255, 230, 140), (150, 66, 8))

SELECT_OK = (60, 200, 110)     # selection box when the sum is exactly 10
SELECT_NORMAL = (70, 150, 255) # selection box otherwise
GLOW = (255, 238, 120)

BUTTON_THEMES = {
    "green": ((88, 196, 92), (52, 150, 62), (34, 110, 44)),
    "yellow": ((255, 206, 72), (240, 164, 32), (176, 112, 16)),
    "red": ((250, 96, 96), (214, 52, 62), (150, 30, 40)),
    "blue": ((92, 170, 255), (52, 120, 222), (30, 80, 160)),
}
