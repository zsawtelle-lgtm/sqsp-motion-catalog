"""Timed frame assertions for preset 03 (one per beat). Run: python3 checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
W, H = k.W, k.H
BAR = (0, H - s.BAR_H, W, H)
COUNT = (s.GUTTER - 10, int(s.CLIP_TOP), 620, int(s.BOX_BOTTOM))
LOGO = (s.GUTTER, 24, s.GUTTER + 100, 52)
KICKER = (60, 150, 300, 175)         # page hero kicker (accent)


def bar_fill(f):
    """Fraction of the bottom bar row that is accent (= progress)."""
    return c.share(f, k.ACCENT, BAR, 60)


def digit_ink(f):
    return c.share(f, k.INK, COUNT, 60)


c.expect("overlay up at mount: paper, wordmark, '0', empty bar", 0.0,
         lambda f: (bar_fill(f) < 0.01 and c.share(f, k.INK, LOGO, 60) > 0.05 and digit_ink(f) > 0.02,
                    f"bar={bar_fill(f):.3f} logo={c.share(f, k.INK, LOGO, 60):.3f}"))
c.expect("crawl: bar ~ counter value at 1.0s (60-72%)", 1.0,
         lambda f: (abs(bar_fill(f) * 100 - s.value_at(1.0)) < 3 and 55 < s.value_at(1.0) < 72,
                    f"bar={bar_fill(f) * 100:.1f}% v={s.value_at(1.0):.1f}"))
c.expect("honest wait: parks below 90 just before load", s.LOAD_AT - 0.02,
         lambda f: (0.80 < bar_fill(f) < 0.90, f"bar={bar_fill(f) * 100:.1f}%"))
c.expect("load fired: counter completes, bar full", s.DONE_AT + 0.05,
         lambda f: (bar_fill(f) > 0.995 and digit_ink(f) > 0.08,
                    f"bar={bar_fill(f) * 100:.1f}% ink={digit_ink(f):.3f}"))
c.expect("three digits wider than two (100 rendered)", s.DONE_AT + 0.05,
         lambda f: (digit_ink(f) > 1.25 * digit_ink(c.frame(s.LOAD_AT - 0.3)), f"{digit_ink(f):.3f}"))
c.expect("roll-out: digits rolled up out of the clip, logo faded", s.EXIT_AT + 0.3,
         lambda f: (digit_ink(f) < 0.5 * digit_ink(c.frame(s.DONE_AT + 0.05)) and c.share(f, k.INK, LOGO, 60) < 0.03,
                    f"ink={digit_ink(f):.3f}"))
c.expect("mid-wipe: bar is the leading edge, page under it", s.WIPE_AT + 0.4,
         lambda f: (c.share(f, k.ACCENT, (0, 0, W, H), 60) > 0.003 and c.share(f, k.TILE, (720, 420, 1200, 460), 20) > 0.5,
                    "edge + hero tile"))
c.expect("page revealed after the wipe", s.WIPE_END + 0.05,
         lambda f: (c.share(f, k.ACCENT, KICKER, 60) > 0.05 and bar_fill(f) < 0.01, "kicker visible, bar gone"))
c.expect("final frame == loaded page (resting state)", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.WIPE_END + 0.1)) < 0.5, ""))
c.run()
