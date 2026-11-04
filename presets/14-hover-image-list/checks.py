"""Timed frame assertions for preset 14 (one per beat). Run: python checks.py"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker, hex_rgb  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
F0 = c.frame(0.0)
LIST = (s.X0, int(s.LIST_TOP), s.X1 + 8, int(s.LIST_BOT))
ARROWS = (int(s.X1 - s.ARROW - 4), int(s.LIST_TOP), s.X1 + 10, int(s.LIST_BOT))
TONE_TOL = 12


def row_box(i, x0=s.X0, x1=s.X1 - 60):
    return (x0, int(s.row_top(i)) + 4, x1, int(s.row_top(i) + s.ROW_H) - 4)


def arrow_box(i):
    return (ARROWS[0], int(s.row_top(i)) + 4, ARROWS[2], int(s.row_top(i) + s.ROW_H) - 4)


def mask(f, color, box=None, tol=TONE_TOL):
    m = np.sqrt(((f - hex_rgb(color)) ** 2).sum(axis=2)) < tol
    if box:
        z = np.zeros_like(m)
        z[box[1]:box[3], box[0]:box[2]] = m[box[1]:box[3], box[0]:box[2]]
        m = z
    return m


def centroid(m):
    ys, xs = np.nonzero(m)
    return (xs.mean(), ys.mean()) if len(xs) else (None, None)


def tones(f):
    return [int(mask(f, t).sum()) for t in s.TONES]


def image_beat(i, t):
    """image i is the one showing, and it sits on the (eased) float position near the cursor."""
    def fn(f):
        n = tones(f)
        st = s.state(t)
        cx, cy = centroid(mask(f, s.TONES[i]))
        mx, my = s.cursor(t)
        ok = (st["cur"] == i and n[i] > 20000 and all(n[j] < 0.02 * n[i] for j in range(s.N) if j != i)
              and cx is not None and np.hypot(cx - mx, cy - my) < 70)
        return ok, f"tone px {n} centroid→cursor {np.hypot(cx - mx, cy - my) if cx else -1:.0f}px"
    return fn


def tilt(f, color):
    """slope (deg) of the image's top edge, from the topmost tone pixel per column."""
    m = mask(f, color)
    cols = np.nonzero(m.any(axis=0))[0]
    cols = cols[int(len(cols) * .2): int(len(cols) * .8)]
    tops = np.array([np.nonzero(m[:, x])[0][0] for x in cols])
    return np.degrees(np.arctan(np.polyfit(cols, tops, 1)[0]))


def dims(f, hot):
    """ink share of each row's text area (rows dimmed to .3 have none at full ink)."""
    return [c.share(f, k.INK, row_box(i, s.X0, s.X0 + 300), 30) for i in range(s.N)]


c.expect("rest: list at full ink, no image, no accent arrows", 0.0,
         lambda f: (sum(tones(f)) == 0 and min(dims(f, None)) > 0.04 and c.share(f, k.ACCENT, ARROWS, 60) == 0,
                    f"ink {[round(d, 3) for d in dims(f, None)]}"))
SETTLED = tones(c.frame(1.45))[0]
c.expect("enter row 1: image mid-reveal (clipped from below, scaled down)", 0.95,
         lambda f: (0 < tones(f)[0] < 0.8 * SETTLED, f"{tones(f)[0]} px vs settled {SETTLED}"))
c.expect("row 1 hovered: image 1 on the cursor", 1.45, image_beat(0, 1.45))
c.expect("row 1 hovered: other rows dim to .3, row 1 stays full ink", 1.45,
         lambda f: (dims(f, 0)[0] > 0.04 and max(dims(f, 0)[1:]) < 0.002, f"{[round(d, 3) for d in dims(f, 0)]}"))
c.expect("row 1 arrow: accent + nudged 5px right; other arrows stay ink", 1.45,
         lambda f: ((lambda a, b: abs(a - b - 5) < 1.2)(centroid(mask(f, k.ACCENT, arrow_box(0), 60))[0],
                                                       centroid(mask(F0, k.INK, arrow_box(0), 60))[0])
                    and all(c.share(f, k.ACCENT, arrow_box(i), 60) == 0 for i in range(1, s.N)),
                    f"dx {centroid(mask(f, k.ACCENT, arrow_box(0), 60))[0] - centroid(mask(F0, k.INK, arrow_box(0), 60))[0]:.2f}px"))
c.expect("moving to row 2: float lags the cursor (lerp) and tilts with speed", 1.62,
         lambda f: ((lambda st, mx: abs(st["x"] - mx[0]) > 40 and abs(tilt(f, s.TONES[0])) > 1.5)(s.state(1.62), s.cursor(1.62)),
                    f"lag {abs(s.state(1.62)['x'] - s.cursor(1.62)[0]):.0f}px tilt {tilt(f, s.TONES[0]):.2f}°"))
c.expect("row 2 hovered: swaps to image 2", 2.3, image_beat(1, 2.3))
c.expect("row 3 hovered: image 3", 3.1, image_beat(2, 3.1))
c.expect("row 4 hovered: image 4", 3.9, image_beat(3, 3.9))
c.expect("row 5 hovered: image 5, settled upright", 4.6,
         lambda f: (image_beat(4, 4.6)(f)[0] and abs(tilt(f, s.TONES[4])) < 1.0, f"tilt {tilt(f, s.TONES[4]):.2f}°"))
ROW1_TXT = row_box(0, s.X0, s.X0 + 300)
LUM_DIM = c.frame(4.6)[ROW1_TXT[1]:ROW1_TXT[3], ROW1_TXT[0]:ROW1_TXT[2]].mean()
LUM_REST = F0[ROW1_TXT[1]:ROW1_TXT[3], ROW1_TXT[0]:ROW1_TXT[2]].mean()
c.expect("cursor leaves: image fading out while rows un-dim (mid-transition)", 5.0,
         lambda f: ((lambda lum: LUM_REST < lum < LUM_DIM and c.diff(f, F0, LIST) > 1 and not s.state(5.0)["shown"])
                    (f[ROW1_TXT[1]:ROW1_TXT[3], ROW1_TXT[0]:ROW1_TXT[2]].mean()),
                    f"row-1 lum {f[ROW1_TXT[1]:ROW1_TXT[3], ROW1_TXT[0]:ROW1_TXT[2]].mean():.1f} (rest {LUM_REST:.1f}, dim {LUM_DIM:.1f}) list diff {c.diff(f, F0, LIST):.1f}"))
c.expect("end at rest: list identical to frame 0, no image", s.DURATION,
         lambda f: (sum(tones(f)) == 0 and c.diff(f, F0, LIST) < 0.05, f"diff {c.diff(f, F0, LIST):.3f}"))
c.run()
