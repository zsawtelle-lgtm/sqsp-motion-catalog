"""Timed frame assertions for preset 08 (one per beat). Run: python checks.py"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
Y0, Y1 = int(s.BAND_Y), int(s.BAND_Y + s.BAND_H)
BAND = (0, Y0, k.W, Y1)
ROW1 = (0, int(s.ROW1_Y), k.W, int(s.ROW1_Y + s.LINE_H))
ROW2 = (0, int(s.ROW2_Y), k.W, int(s.ROW2_Y + s.LINE_H))
ABOVE = (0, 0, k.W, Y0 - 4)
BELOW = (0, Y1 + 4, k.W, k.H)
F0 = c.frame(0.0)


def ink_paper(f, box):
    return c.share(f, k.PAPER, box, 40)


def shift(a, b, box, max_px=400):
    """Horizontal shift (px) that best maps row a onto row b (b = a moved by dx)."""
    ra = a[box[1]:box[3]].mean(axis=2)
    rb = b[box[1]:box[3]].mean(axis=2)
    best, arg = 1e9, 0
    for dx in range(-max_px, max_px + 1):
        if dx >= 0:
            e = np.abs(ra[:, : k.W - dx] - rb[:, dx:]).mean()
        else:
            e = np.abs(ra[:, -dx:] - rb[:, : k.W + dx]).mean()
        if e < best:
            best, arg = e, dx
    return arg


DT = 0.5
EXPECT = s.SPEED * DT

c.expect("band painted full width in ink, page untouched around it", 0.0,
         lambda f: (c.share(f, k.INK, (0, Y0 + 1, k.W, Y0 + 10), 10) > 0.99
                    and c.share(f, k.INK, (0, Y1 - 10, k.W, Y1 - 1), 10) > 0.99
                    and c.diff(f, F0, ABOVE) == 0 and c.diff(f, F0, BELOW) == 0, ""))
c.expect("solid row: large paper words (>15% of row)", 0.0,
         lambda f: (ink_paper(f, ROW1) > 0.15, f"{ink_paper(f, ROW1):.3f}"))
c.expect("outlined row: thin strokes only (<9% of row), clearly lighter than row 1", 0.0,
         lambda f: (0.01 < ink_paper(f, ROW2) < 0.09 and ink_paper(f, ROW2) < ink_paper(f, ROW1) / 2,
                    f"{ink_paper(f, ROW2):.3f}"))
c.expect("accent star separators present in both rows", 1.0,
         lambda f: (c.share(f, k.ACCENT, ROW1, 40) > 0.004 and c.share(f, k.ACCENT, ROW2, 40) > 0.004,
                    f"{c.share(f, k.ACCENT, ROW1, 40):.4f}/{c.share(f, k.ACCENT, ROW2, 40):.4f}"))
c.expect(f"row 1 moves LEFT at config speed ({EXPECT:.0f}px per {DT}s, ±10%)", 2.0,
         lambda f: (abs(-shift(f, c.frame(2.0 + DT), ROW1) - EXPECT) <= EXPECT * 0.1,
                    f"{shift(f, c.frame(2.0 + DT), ROW1)}px"))
c.expect("row 2 moves RIGHT at the same speed", 2.0,
         lambda f: (abs(shift(f, c.frame(2.0 + DT), ROW2) - EXPECT) <= EXPECT * 0.1,
                    f"{shift(f, c.frame(2.0 + DT), ROW2)}px"))
c.expect("mid-loop frame differs from frame 0 (it is moving)", s.LOOP / 2,
         lambda f: (c.diff(f, F0, BAND) > 8, f"{c.diff(f, F0, BAND):.1f}"))
c.expect("seamless loop: frame after last (t=LOOP) == frame 0", s.LOOP,
         lambda f: (c.diff(f, F0) < 0.01, f"{c.diff(f, F0):.4f}"))
c.expect("last rendered frame is one step before frame 0 (no dup at the wrap)", s.DURATION,
         lambda f: (0 < shift(f, F0, ROW1, 40) * -1 <= s.SPEED / s.FPS + 1 and c.diff(f, F0, BAND) > 0.5,
                    f"{shift(f, F0, ROW1, 40)}px"))
c.run()
