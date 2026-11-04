"""Timed frame assertions for preset 12 (one per beat). Run: python3 checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
DIM_RGB = s._mix(k.PAPER, k.INK, s.DIM)      # ink at 18% on paper


def wbox(word, t):
    """Screen box of one word's glyphs (cap height to baseline) at time t."""
    w = next(x for x in s.WORDS if x[0] == word)
    off = s.scroll(t)
    _, _, x, base, _, width = w
    return (int(x), int(base - 0.74 * s.SIZE - off), int(x + width), int(base + 0.05 * s.SIZE - off))


def block(t):
    off = s.scroll(t)
    return (40, int(s.TOP0 - off), 1180, min(s.HEIGHT, int(s.BLOCK_BOTTOM - off)))


def ink(f, box, color=k.INK):
    return c.share(f, color, box, 50)


REST = ink(c.frame(s.DURATION), block(s.DURATION))
T_A, T_B, T_C = 1.3, 1.9, 2.3
CALM = "calm"

c.expect("statement rests dim before the fill line", 0.0,
         lambda f: (ink(f, block(0.0)) < 0.001 and ink(f, block(0.0), DIM_RGB) > 0.05,
                    f"ink {ink(f, block(0.0)):.4f} dim {ink(f, block(0.0), DIM_RGB):.3f}"))
c.expect("first words filled, line end still dim", T_A,
         lambda f: (ink(f, wbox("We", T_A)) > 0.15 and ink(f, wbox("well,", T_A)) < 0.002,
                    f"We {ink(f, wbox('We', T_A)):.3f} well {ink(f, wbox('well,', T_A)):.4f}"))
c.expect("<em> word not yet accent while unfilled", T_B,
         lambda f: (ink(f, wbox(CALM, T_B), k.ACCENT) < 0.002, f"{ink(f, wbox(CALM, T_B), k.ACCENT):.4f}"))
c.expect("fill grows with scroll (reading order)", T_C,
         lambda f: (ink(c.frame(T_A), block(T_A)) < ink(c.frame(T_B), block(T_B)) < ink(f, block(T_C)) < REST,
                    f"{ink(c.frame(T_A), block(T_A)) / REST:.2f} → {ink(c.frame(T_B), block(T_B)) / REST:.2f} → {ink(f, block(T_C)) / REST:.2f}"))
c.expect("<em> word fills to the accent", 2.65,
         lambda f: (ink(f, wbox(CALM, 2.65), k.ACCENT) > 0.12, f"{ink(f, wbox(CALM, 2.65), k.ACCENT):.3f}"))
c.expect("block complete once its top passes 40%", 3.1,
         lambda f: (abs(ink(f, wbox("Tuesday.", 3.1)) - ink(c.frame(s.DURATION), wbox("Tuesday.", s.DURATION))) < 0.02
                    and s.progress(3.1) == 1.0, f"p {s.progress(3.1):.2f}"))
c.expect("final frame is the resting state, fully filled", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.DURATION - 0.4)) < 0.3 and c.share(f, DIM_RGB, block(s.DURATION), 12) < 0.01 and REST > 0.08,
                    f"diff {c.diff(f, c.frame(s.DURATION - 0.4)):.3f} rest {REST:.3f}"))
c.run()
