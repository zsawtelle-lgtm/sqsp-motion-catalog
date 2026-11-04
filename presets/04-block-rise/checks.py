"""Timed frame assertions for preset 04 (one per beat). Run: python checks.py"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker, hex_rgb  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
B = {b[0]: b for b in s.BLOCKS}


def box(bid, t):
    """Screen box of a block at its resting place for the scroll at t."""
    _, top, left, bottom, _ = B[bid]
    w = s.COL_W if bid != "head" else 300
    y = s.scroll(t)
    y0, y1 = max(s.HEADER_H + 2, int(top - y)), min(k.H, int(bottom - y + s.DISTANCE))
    return (int(left), y0, int(left + w), y1)


def ink(f, bid, t):
    """Mean deviation from paper in the block's box (0 = blank)."""
    x0, y0, x1, y1 = box(bid, t)
    if y1 <= y0:
        return 0.0
    return float(np.abs(f[y0:y1, x0:x1] - hex_rgb(k.PAPER)).mean())


REST = c.frame(s.DURATION)
FULL = {b: ink(REST, b, s.DURATION) for b in B}


def rel(f, bid, t):
    return ink(f, bid, t) / FULL[bid]


def check_at(t, cond):
    return lambda f: cond(lambda b: rel(f, b, t))


t1 = s.START["img1"] - 0.02
c.expect("hero holds, nothing scrolled yet", 0.30,
         lambda f: (c.diff(f, c.frame(0.0)) < 0.2 and s.scroll(0.3) == 0, ""))
c.expect("heading rises first; image row still blank", t1,
         check_at(t1, lambda r: (0.15 < r("head") < 1.0 and r("img1") < 0.05 and r("img3") < 0.05,
                                 f"head {r('head'):.2f} img1 {r('img1'):.2f}")))
t2 = s.START["img1"] + 0.18
c.expect("image row staggered left to right (img1 > img2 > img3)", t2,
         check_at(t2, lambda r: (r("img1") > r("img2") > r("img3") and r("img3") < 0.6,
                                 f"{r('img1'):.2f} > {r('img2'):.2f} > {r('img3'):.2f}")))
t3 = s.START["txt1"] - 0.05
c.expect("text row waits for its own row (images up, text blank)", t3,
         check_at(t3, lambda r: (r("img1") > 0.8 and r("txt1") < 0.05 and r("txt3") < 0.05,
                                 f"img1 {r('img1'):.2f} txt1 {r('txt1'):.2f}")))
t4 = s.START["btn"] + 0.1
c.expect("button rises last; text row ahead of it", t4,
         check_at(t4, lambda r: (r("txt1") > r("btn") and 0.0 < r("btn") < 0.7,
                                 f"txt1 {r('txt1'):.2f} btn {r('btn'):.2f}")))
c.expect("rise is a lift: button still below its rest line mid-rise", t4,
         lambda f: (c.share(f, k.INK, (64, int(s.BTN_Y - s.scroll(t4)) - 2, 200,
                                       int(s.BTN_Y - s.scroll(t4)) + 3), 60) < 0.2, ""))
c.expect("every block at rest", s.REST_AT + 0.05,
         lambda f: (all(rel(f, b, s.REST_AT + 0.05) > 0.97 for b in B), ""))
c.expect("final frame == resting state", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.REST_AT + 0.1)) < 0.3, ""))
c.run()
