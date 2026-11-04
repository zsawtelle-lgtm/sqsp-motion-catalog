"""Timed frame assertions for preset 11 (one per beat). Run: python checks.py"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker, hex_rgb  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
N = len(s.STATS)
FINAL_T = s.DURATION


def col_x(i):
    return int(s.X0 + i * s.COL_W)


def total_w(i):
    return s.k.text_width(s.word(i), s.NUM_SIZE, "SemiBold", -0.02)


def line_frac(f, i, t):
    """How much of stat i's underline is drawn (0..1), from accent pixels."""
    y = int(round(s.LINE_Y - s.scroll(t)))
    x0, w = col_x(i), total_w(i)
    strip = f[y:y + 3, x0 - 4:int(x0 + w + 6)]
    hit = (np.sqrt(((strip - hex_rgb(k.ACCENT)) ** 2).sum(axis=2)) < 60).any(axis=0)
    return hit.sum() / w


def num_box(i, t, left=0.0, right=1.0):
    y = s.scroll(t)
    x0, w = col_x(i), total_w(i)
    return (int(x0 + w * left), int(s.NUM_BASE - 0.76 * s.NUM_SIZE - y), int(x0 + w * right), int(s.NUM_BASE + 2 - y))


def ink(f, box):
    x0, y0, x1, y1 = box
    return float((np.abs(f[y0:y1, x0:x1] - hex_rgb(k.PAPER)).sum(axis=2) > 120).mean())


REST = c.frame(FINAL_T)
t0 = s.START[0] - 0.03
c.expect("hero holds, nothing scrolled yet", 0.30,
         lambda f: (c.diff(f, c.frame(0.0)) < 0.2 and s.scroll(0.3) == 0, ""))
c.expect("stats on screen, waiting at 0: no underline, ink far below rest", t0,
         lambda f: (all(line_frac(f, i, t0) < 0.02 for i in range(N))
                    and ink(f, num_box(1, t0)) < 0.5 * ink(REST, num_box(1, FINAL_T)),
                    f"col1 ink {ink(f, num_box(1, t0)):.3f} vs {ink(REST, num_box(1, FINAL_T)):.3f}"))
t1 = s.START[3] - 0.02
c.expect("stagger left to right: underline col0 > col1 > col2 > col3 ~ 0", t1,
         lambda f: ((lambda L: (L[0] > L[1] > L[2] > L[3] and L[3] < 0.03, " ".join(f"{v:.2f}" for v in L)))
                    ([line_frac(f, i, t1) for i in range(N)])))
t2 = s.START[1] + 0.25
c.expect("count is right-aligned: '1,200' grows leftward (left 20% blank, right inked)", t2,
         lambda f: (ink(f, num_box(1, t2, 0, 0.2)) < 0.01 < ink(f, num_box(1, t2, 0.6, 1.0)),
                    f"left {ink(f, num_box(1, t2, 0, 0.2)):.3f} right {ink(f, num_box(1, t2, 0.6, 1.0)):.3f}"))
t3 = 2.3
c.expect("mid count: every number differs from its typed value, lines part-drawn", t3,
         lambda f: (all(c.diff(f, REST, num_box(i, t3)) > 0.5 and 0.5 < line_frac(f, i, t3) < 1.0 for i in range(N)),
                    " ".join(f"{line_frac(f, i, t3):.2f}" for i in range(N))))
t4 = s.REST_AT + 0.05
c.expect("count done: numbers == typed text, underlines full width", t4,
         lambda f: (all(c.diff(f, REST, num_box(i, t4)) < 0.3 and line_frac(f, i, t4) > 0.97 for i in range(N)), ""))
c.expect("final frame == resting state (holds still)", FINAL_T,
         lambda f: (c.diff(f, c.frame(s.REST_AT + 0.4)) < 0.2, ""))
c.run()
