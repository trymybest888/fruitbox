"""Generate the game's sound effects, background music and window icon.

All audio is synthesised in Python (no external files or licences needed)
and saved as OGG via the `soundfile` package (pip install soundfile). Run from the project root:

    python tools/make_assets.py

Outputs:
    assets/sounds/clear.ogg, click.ogg, tick.ogg, timeup.ogg, go.ogg, bgm.ogg
    assets/icon.ico
"""

import io
import math
import os
import random
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUND_DIR = os.path.join(ROOT, "assets", "sounds")


# ---------------------------------------------------------------------------
# Tiny synthesiser
# ---------------------------------------------------------------------------
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def bell(freq, dur, sr, vol=1.0, decay=6.0, attack=0.004):
    """Bell / pluck: sine + soft harmonics with an exponential decay."""
    out = []
    for i in range(int(dur * sr)):
        t = i / sr
        env = min(1.0, t / attack) * math.exp(-decay * t)
        s = (math.sin(2 * math.pi * freq * t)
             + 0.35 * math.sin(2 * math.pi * freq * 2 * t)
             + 0.12 * math.sin(2 * math.pi * freq * 3.01 * t))
        out.append(s * env * vol)
    return out


def sweep(f0, f1, dur, sr, vol=1.0, decay=30.0):
    """Sine whose pitch glides from f0 to f1 (pops, blips)."""
    out, phase = [], 0.0
    n = int(dur * sr)
    for i in range(n):
        t = i / sr
        f = f0 + (f1 - f0) * (i / n)
        phase += 2 * math.pi * f / sr
        out.append(math.sin(phase) * math.exp(-decay * t) * vol)
    return out


def pad(freq, dur, sr, vol=1.0, attack=0.25, release=0.35):
    """Soft sustained tone for the background chords."""
    out = []
    n = int(dur * sr)
    for i in range(n):
        t = i / sr
        env = min(1.0, t / attack, (dur - t) / release)
        s = math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * freq * 2 * t)
        out.append(s * max(0.0, env) * vol)
    return out


def mix(dst, src, start, wrap=False):
    for i, s in enumerate(src):
        j = start + i
        if wrap:
            j %= len(dst)
        elif j >= len(dst):
            dst.extend([0.0] * (j - len(dst) + 1))
        dst[j] += s


def write_audio(name, samples, sr, peak=0.85):
    """Normalise and save as OGG Vorbis (small, and plays in browsers too)."""
    import numpy as np
    import soundfile as sf

    data = np.asarray(samples, dtype=np.float32)
    data *= peak / max(1e-9, float(np.abs(data).max()))
    path = os.path.join(SOUND_DIR, name)
    sf.write(path, data, sr, format="OGG", subtype="VORBIS")
    print(f"  wrote {os.path.relpath(path, ROOT)}  ({len(samples) / sr:.2f}s)")


# ---------------------------------------------------------------------------
# Sound effects
# ---------------------------------------------------------------------------
def make_sfx():
    sr = 44100

    # clear: a juicy pop followed by a sparkly rising arpeggio
    clear = sweep(260, 900, 0.07, sr, vol=0.9, decay=35)
    for k, n in enumerate([76, 79, 84, 88]):
        mix(clear, bell(midi(n), 0.55, sr, vol=0.45, decay=7), int((0.04 + k * 0.05) * sr))
    write_audio("clear.ogg", clear, sr)

    # click: short friendly blip for buttons
    write_audio("click.ogg", sweep(700, 1300, 0.07, sr, decay=45), sr, peak=0.7)

    # tick: woodblock-like tick for the final seconds
    tick = bell(midi(96), 0.08, sr, decay=60)
    mix(tick, bell(midi(84), 0.08, sr, vol=0.5, decay=70), 0)
    write_audio("tick.ogg", tick, sr, peak=0.6)

    # go: two quick rising notes
    go = bell(midi(72), 0.25, sr, decay=10)
    mix(go, bell(midi(79), 0.45, sr, decay=6), int(0.12 * sr))
    write_audio("go.ogg", go, sr, peak=0.7)

    # timeup: descending chime ending on a long low note
    up = []
    for k, n in enumerate([79, 76, 72]):
        mix(up, bell(midi(n), 0.4, sr, decay=8), int(k * 0.16 * sr))
    mix(up, bell(midi(67), 1.2, sr, decay=3), int(0.5 * sr))
    mix(up, bell(midi(55), 1.2, sr, vol=0.5, decay=3), int(0.5 * sr))
    write_audio("timeup.ogg", up, sr)


# ---------------------------------------------------------------------------
# Background music: gentle 8-bar loop (C - Am - F - G - C - Am - Dm - G)
# ---------------------------------------------------------------------------
def make_music():
    sr = 22050
    bpm = 96
    beat = 60 / bpm
    bar = beat * 4
    chords = [
        (48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [55, 59, 62]),
        (48, [60, 64, 67]), (45, [57, 60, 64]), (38, [57, 62, 65]), (43, [55, 59, 62]),
    ]
    total = int(bar * len(chords) * sr)
    out = [0.0] * total
    rnd = random.Random(11)
    pattern = [0, 1, 2, 3, 2, 1, 2, None]  # 8th-note arpeggio, last one rests

    for b, (root, triad) in enumerate(chords):
        t0 = b * bar
        # Soft pad chord
        for n in triad:
            mix(out, pad(midi(n), bar, sr, vol=0.05), int(t0 * sr), wrap=True)
        # Bass on beats 1 and 3
        for beat_i in (0, 2):
            mix(out, bell(midi(root), beat * 1.8, sr, vol=0.22, decay=2.5),
                int((t0 + beat_i * beat) * sr), wrap=True)
        # Plucked arpeggio an octave up
        tones = [n + 12 for n in triad] + [triad[0] + 24]
        for k, idx in enumerate(pattern):
            if idx is None:
                continue
            vol = 0.10 + rnd.uniform(-0.015, 0.015)
            mix(out, bell(midi(tones[idx]), 0.6, sr, vol=vol, decay=5.5),
                int((t0 + k * beat / 2) * sr), wrap=True)  # wrap -> seamless loop
    write_audio("bgm.ogg", out, sr, peak=0.7)


# ---------------------------------------------------------------------------
# Icon (.ico containing a 256x256 PNG of the apple sprite)
# ---------------------------------------------------------------------------
def make_icon():
    sys.path.insert(0, ROOT)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    from game import settings as S
    from game.graphics import render_apple

    pygame.init()
    surf = render_apple(256, S.APPLE_NORMAL)
    buf = io.BytesIO()
    pygame.image.save(surf, buf, "icon.png")
    png = buf.getvalue()
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 6 + 16)
    path = os.path.join(ROOT, "assets", "icon.ico")
    with open(path, "wb") as f:
        f.write(header + entry + png)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    os.makedirs(SOUND_DIR, exist_ok=True)
    print("Generating sound effects...")
    make_sfx()
    print("Generating background music (takes a few seconds)...")
    make_music()
    print("Generating icon...")
    make_icon()
    print("Done.")
