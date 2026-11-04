"""Timed frame assertions for preset 13 (one per beat). Run: python checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
H = k.H
BAR = s.TOP + s.BAR_Y            # hairline row while pinned (viewport y)
TILE_MID = s.TOP + s.CARD_Y + 60  # a row through the tiles' sky while pinned


def bar_fill(f):
    """Accent share along the hairline (0..1 of the holder width)."""
    return c.share(f, k.ACCENT, (s.HOLD_X, BAR, s.HOLD_X + s.HOLD_W, BAR + 2), 40)


def rest(f):
    sec = s.state(0.3)[3]
    ok = c.share(f, k.PAPER, (40, 100, 640, 420), 12) > 0.8 and c.share(f, k.INK, (0, int(sec) + 10, k.W, H), 12) > 0.5
    return ok, f"work section top {sec:.0f}"


c.expect("rest: intro on paper, ink work section below", 0.30, rest)


def rising(f):
    top, p, x, _ = s.state(1.2)
    harbor = c.share(f, "#3A3833", (70, int(top) + s.CARD_Y + 10, 300, int(top) + s.CARD_Y + 60), 8)
    return top > s.TOP + 100 and p == 0 and x == 0 and harbor > 0.8, f"top {top:.0f}, harbor {harbor:.2f}"


c.expect("scrolling in: section rises, track still at 0", 1.20, rising)


def pinned(f):
    top, p, x, sec = s.state(2.4)
    head = c.share(f, k.PAPER, (60, s.TOP + 96, 400, s.TOP + 140), 40)
    fill = bar_fill(f)
    return abs(top - s.TOP) < 0.01 and sec < s.TOP and 0.2 < p < 0.5 and abs(fill - p) < 0.03 and head > 0.1, \
        f"top {top:.1f}, section top {sec:.0f}, p {p:.2f}, bar {fill:.2f}"


c.expect("pinned under the header, hairline = progress", 2.40, pinned)


def sliding(f):
    a, b = s.state(2.4), s.state(3.0)
    left_edge = c.share(f, k.INK, (s.HOLD_X - 40, TILE_MID, s.HOLD_X - 4, TILE_MID + 60), 10)
    return b[0] == s.TOP and b[2] < a[2] - 200 and bar_fill(f) > 0.6 and left_edge > 0.95, \
        f"x {a[2]:.0f} -> {b[2]:.0f}, bar {bar_fill(f):.2f}, clip edge ink {left_edge:.2f}"


c.expect("still pinned: cards slide left, clipped at the holder edge", 3.00, sliding)


def end_of_travel(f):
    top, p, x, _ = s.state(3.50)
    pier = c.share(f, "#CFC7B8", (1170, int(top) + s.CARD_Y + 10, 1212, int(top) + s.CARD_Y + 60), 8)
    return top == s.TOP and p > 0.99 and abs(x + s.DIST) < 0.01 * s.DIST and pier > 0.9 and bar_fill(f) > 0.97, \
        f"p {p:.2f}, x {x:.0f}, last card flush right {pier:.2f}"


c.expect("end of travel: x = -(trackW - viewW), last card flush right", 3.50, end_of_travel)


def unpinned(f):
    top, p, x, sec = s.state(4.3)
    nxt = int(sec + s.CW_H + s.DIST)
    return top < s.TOP - 150 and x == -s.DIST and c.share(f, k.PAPER, (0, nxt + 10, k.W, H), 30) > 0.5, \
        f"cw top {top:.0f}, next section at {nxt}"


c.expect("unpins and scrolls away, next section comes up", 4.30, unpinned)
c.expect("header stays on top throughout", 2.80,
         lambda f: (c.share(f, k.PAPER, (300, 0, 700, 70), 10) > 0.9, ""))
c.expect("final frame == resting state", s.DURATION,
         lambda f: (c.diff(f, c.frame(5.05)) < 0.3 and s.state(s.DURATION)[2] == -s.DIST, ""))
c.run()
