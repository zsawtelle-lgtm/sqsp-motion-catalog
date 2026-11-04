"""Timed frame assertions for preset 17 (one per beat). Run: python3 checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene


def box(r, off=0.0, pad=(0, 0, 0, 0)):
    return (int(r["x"] - pad[0]), int(r["y"] - off - pad[1]), int(r["x"] + r["w"] + pad[2]), int(r["y"] + r["h"] - off + pad[3]))


def half(b, right=False):
    mx = (b[0] + b[2]) // 2
    return (mx, b[1], b[2], b[3]) if right else (b[0], b[1], mx, b[3])


def band(f, b):
    return c.share(f, s.BAND, b, 22)


def acc(f, b):
    return c.share(f, k.ACCENT, b, 70)


WORKS = box(s.rect(s.WORKS), pad=(6, 0, 6, 0))
END = s.scroll_off(s.DURATION)
# underline strip under each wrapped line, and the circle's bounding area
UL1 = box(s.rect(s.EM_RUNS[0]), END, (8, -int(0.7 * s.P_SIZE * s.LINE_H), 12, 8))
UL2 = box(s.rect(s.EM_RUNS[1]), END, (8, -int(0.7 * s.P_SIZE * s.LINE_H), 12, 14))
CIRC = box(s.rect(s.TESTED), END, (24, 14, 24, 14))
WORD = box(s.rect(s.TESTED), END, (-6, -6, -6, -14))      # inside the circle: the word itself
PARA = (40, int(s.P_BASE[0] - 40 - END), 900, int(s.P_BASE[1] + 30 - END))


def para_at(t):
    o = s.scroll_off(t)
    return (40, int(s.P_BASE[0] - 40 - o), 900, int(s.P_BASE[1] + 30 - o))


c.expect("hero: no band before the observer + delay", 0.40,
         lambda f: (band(f, WORKS) < 0.005, f"{band(f, WORKS):.4f}"))
c.expect("band grows left→right (left half filled, right half not yet)", s.WORKS_AT + 0.42,
         lambda f: (band(f, half(WORKS)) > 0.12 and band(f, half(WORKS, True)) < 0.6 * band(f, half(WORKS)),
                    f"L {band(f, half(WORKS)):.3f} R {band(f, half(WORKS, True)):.3f}"))
c.expect("band complete, behind the text (ink still on top)", 1.50,
         lambda f: (band(f, half(WORKS, True)) > 0.15 and c.share(f, k.INK, WORKS, 60) > 0.15,
                    f"band R {band(f, half(WORKS, True)):.3f} ink {c.share(f, k.INK, WORKS, 60):.3f}"))
c.expect("paragraph scrolled in, no strokes before its observer fires", s.UL_AT - 0.05,
         lambda f: (acc(f, para_at(s.UL_AT - 0.05)) < 0.001, f"{acc(f, para_at(s.UL_AT - 0.05)):.4f}"))
T_L1 = s.UL_STARTS[1] - 0.02


def mid_l1(f):
    o = s.scroll_off(T_L1) - END
    l1 = (UL1[0], int(UL1[1] - o), UL1[2], int(UL1[3] - o))
    l2 = (UL2[0], int(UL2[1] - o), UL2[2], int(UL2[3] - o))
    return acc(f, l1) > 0.02 and acc(f, l2) < 0.002, f"L1 {acc(f, l1):.3f} L2 {acc(f, l2):.4f}"


c.expect("line 1 underline drawn before line 2 starts (sequenced by length)", T_L1, mid_l1)
T_C = s.CIRC_AT + s.CIRC_DUR * 0.45


def mid_circ(f):
    o = s.scroll_off(T_C) - END
    cb = (CIRC[0], int(CIRC[1] - o), CIRC[2], int(CIRC[3] - o))
    return 0.005 < acc(f, cb) < 0.75 * REST_CIRC, f"{acc(f, cb):.3f} of {REST_CIRC:.3f}"


REST = c.frame(s.DURATION)
REST_CIRC = acc(REST, CIRC)
c.expect("circle mid-draw, overlapping the underline (0.25s stagger)", T_C, mid_circ)
c.expect("at rest: underline under both wrapped lines + circle", s.DURATION,
         lambda f: (acc(f, UL1) > 0.02 and acc(f, UL2) > 0.02 and REST_CIRC > 0.03,
                    f"L1 {acc(f, UL1):.3f} L2 {acc(f, UL2):.3f} circ {REST_CIRC:.3f}"))
c.expect("circled word stays readable ink (marks sit around, not over)", s.DURATION,
         lambda f: (c.share(f, k.INK, WORD, 60) > 0.2 and acc(f, WORD) < 0.02,
                    f"ink {c.share(f, k.INK, WORD, 60):.3f} acc {acc(f, WORD):.3f}"))
c.expect("final frame is the resting state", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.DURATION - 0.6)) < 0.3, f"{c.diff(f, c.frame(s.DURATION - 0.6)):.3f}"))
c.run()
