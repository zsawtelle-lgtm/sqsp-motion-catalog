"""Timed frame assertions for preset 01 (one per beat). Run: python checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
S, OX, OY = s.SCALE, s.OX, s.OY


def box(x0, y0, x1, y1):  # mark-space -> pixel box
    return (int(OX + x0 * S), int(OY + y0 * S), int(OX + x1 * S), int(OY + y1 * S))


FRAME_BOX = box(-2, -2, 66, 66)
SLASH_BOX = box(20, 20, 44, 44)
WORD_BOX = box(82, 8, s.m.VB_W, 52)
S_BOX = box(82, 8, 112, 52)


def word_ink(f):
    return c.share(f, k.INK, WORD_BOX, 60)


c.expect("blank cover before the first beat", 0.15,
         lambda f: (c.share(f, k.PAPER, (0, 0, k.W, k.H), 6) > 0.995, ""))
FULL_FRAME = c.share(c.frame(1.2), k.INK, FRAME_BOX, 60)
c.expect("frame outline partly drawn (20-90% of final)", 0.70,
         lambda f: (0.2 < c.share(f, k.INK, FRAME_BOX, 60) / FULL_FRAME < 0.9,
                    f"{c.share(f, k.INK, FRAME_BOX, 60) / FULL_FRAME:.2f}"))
c.expect("accent slash drawn", 1.40,
         lambda f: (c.share(f, k.ACCENT, SLASH_BOX, 50) > 0.08, f"{c.share(f, k.ACCENT, SLASH_BOX, 50):.3f}"))
c.expect("'S' traced but not yet inked", 0.78,
         lambda f: (c.share(f, k.INK, S_BOX, 60) < 0.05, f"{c.share(f, k.INK, S_BOX, 60):.3f}"))
c.expect("wordmark fully inked", 2.55,
         lambda f: (word_ink(f) > 0.25, f"{word_ink(f):.3f}"))
c.expect("hold pulse dims the slash", s.INTRO_END + 1.2,
         lambda f: (c.share(f, k.ACCENT, SLASH_BOX, 30) < 0.03, f"{c.share(f, k.ACCENT, SLASH_BOX, 30):.3f}"))
c.expect("page revealed after dismiss", s.DISMISS_AT + 0.6,
         lambda f: (c.share(f, k.ACCENT, (60, 150, 300, 175), 60) > 0.05, "kicker visible"))
c.expect("final frame == loaded page (resting state)", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.DISMISS_AT + 0.7)) < 0.5, ""))
c.run()
