"""Timed frame assertions for preset 07 (one per beat). Run: python3 checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene


def wbox(item, size, off=0.0):
    """Pixel box of one word's resting glyphs (cap height to baseline)."""
    word, acc, x, base, w, i = item
    return (int(x), int(base - 0.74 * size - off), int(x + w), int(base + 0.2 * size - off))


def ink(f, box, color=k.INK):
    return c.share(f, color, box, 60)


L1 = (40, s.H1_BASE[0] - 60, 640, s.H1_BASE[0] + 14)
L2 = (40, s.H1_BASE[1] - 60, 640, s.H1_BASE[1] + 14)
GAP = (40, s.H1_BASE[0] + 18, 640, s.H1_BASE[1] - 50)   # between the two line masks
BUILT = wbox(s.H1[1], s.H1_SIZE)
KICK = (60, s.KICK_Y - 12, 280, s.KICK_Y + 2)
BODY = (60, s.TOP + 298, 520, s.TOP + 350)
REST_L1 = ink(c.frame(2.0), L1)
OFF_END = s.SCROLL
H2_BOX = (40, s.H2_BASE[0] - 46 - OFF_END, 760, s.H2_BASE[0] + 12 - OFF_END)
H2_REST = ink(c.frame(s.DURATION), H2_BOX)
FIRST_LAST = wbox(s.H1[-1], s.H1_SIZE)


c.expect("headline hidden before the observer fires", 0.25,
         lambda f: (ink(f, L1) + ink(f, L2) < 0.002 and ink(f, KICK, k.ACCENT) < 0.002, f"{ink(f, L1):.4f}"))
c.expect("line 1 rising while the last word is still masked", 0.40,
         lambda f: (0.05 < ink(f, L1) / REST_L1 < 0.95 and ink(f, FIRST_LAST) < 0.01,
                    f"L1 {ink(f, L1) / REST_L1:.2f} last {ink(f, FIRST_LAST):.3f}"))
c.expect("mask clips: nothing leaks between lines mid-rise", 0.55,
         lambda f: (ink(f, GAP) < 0.002, f"{ink(f, GAP):.4f}"))
c.expect("<em> word arrives in the accent color", 0.85,
         lambda f: (ink(f, BUILT, k.ACCENT) > 0.12, f"{ink(f, BUILT, k.ACCENT):.3f}"))
c.expect("kicker + body wait for the headline", s.H1_FADE - 0.02,
         lambda f: (ink(f, KICK, k.ACCENT) < 0.002 and c.share(f, k.LINE, BODY, 12) < 0.01, ""))
c.expect("kicker + body faded in", 1.90,
         lambda f: (ink(f, KICK, k.ACCENT) > 0.04 and c.share(f, k.LINE, BODY, 12) > 0.08,
                    f"kick {ink(f, KICK, k.ACCENT):.3f} body {c.share(f, k.LINE, BODY, 12):.3f}"))
T_MID = 3.10
OFF_MID = s.SCROLL * k.seg(T_MID, s.SCROLL_AT, s.SCROLL_END, k.ease_in_out)
H2_MID = (40, int(s.H2_BASE[0] - 46 - OFF_MID), 760, int(s.H2_BASE[0] + 12 - OFF_MID))
c.expect("section 2 heading mid-reveal during scroll", T_MID,
         lambda f: (0.1 < ink(f, H2_MID) / H2_REST < 0.95, f"{ink(f, H2_MID) / H2_REST:.2f}"))
c.expect("section 2 heading fully set at rest", s.DURATION,
         lambda f: (H2_REST > 0.08 and ink(f, H2_BOX, k.ACCENT) > 0.01, f"{H2_REST:.3f}"))
c.expect("final frame is the resting state", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.DURATION - 0.4)) < 0.3, f"{c.diff(f, c.frame(s.DURATION - 0.4)):.3f}"))
c.run()
