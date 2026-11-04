"""Timed frame assertions for preset 02 (one per beat). Run: python3 checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
m = s.m
FULL = (0, 0, k.W, k.H)
LOGO_BOX = (int(s.LX), int(s.LY - 20), int(s.LX + s.LOGO_W), int(s.LY + s.LOGO_H + 20))
TRACK = (int(s.LX), int(s.TRACK_Y - 1), int(s.LX + s.LOGO_W), int(s.TRACK_Y + 4))
LEFT_EDGE = (0, 0, 40, k.H)        # left panel leaves first
RIGHT_EDGE = (k.W - 40, 0, k.W, k.H)
SEAM = (k.W // 2 - 30, 100, k.W // 2 + 30, 300)
KICKER = (60, 150, 300, 175)


def paper(f, box):
    return c.share(f, k.PAPER, box, 30)


c.expect("solid ink cover at first paint (no logo yet)", 0.10,
         lambda f: (c.share(f, k.INK, FULL, 6) > 0.999, f"{c.share(f, k.INK, FULL, 6):.4f}"))
def lum(f, box):  # mean brightness above the ink floor
    return float(f[box[1]:box[3], box[0]:box[2]].mean()) - 31


c.expect("logo mid fade-in (25-75% of settled brightness)", 0.22,
         lambda f: (0.25 < lum(f, LOGO_BOX) / lum(c.frame(1.0), LOGO_BOX) < 0.75,
                    f"{lum(f, LOGO_BOX) / lum(c.frame(1.0), LOGO_BOX):.2f}"))
c.expect("hairline part-way (accent covers 15-85% of track)", 1.30,
         lambda f: (0.15 < c.share(f, k.ACCENT, TRACK, 60) / c.share(c.frame(2.10), k.ACCENT, TRACK, 60) < 0.85,
                    f"{c.share(f, k.ACCENT, TRACK, 60) / c.share(c.frame(2.10), k.ACCENT, TRACK, 60):.2f}"))
c.expect("hairline complete before dismiss", 2.10,
         lambda f: (c.share(f, k.ACCENT, TRACK, 60) > 0.30, f"{c.share(f, k.ACCENT, TRACK, 60):.3f}"))
c.expect("logo gone, panels opening at the seam, edges still ink", s.DISMISS_AT + 0.45,
         lambda f: (paper(f, LOGO_BOX) < 0.6 and paper(f, SEAM) > 0.5
                    and c.share(f, k.INK, LEFT_EDGE, 6) > 0.99 and c.share(f, k.INK, RIGHT_EDGE, 6) > 0.99,
                    f"seam {paper(f, SEAM):.2f}"))
LEFT_HALF, RIGHT_HALF = (0, 0, k.W // 2, k.H), (k.W // 2, 0, k.W, k.H)
c.expect("stagger: left panel further out than the right mid-part", s.DISMISS_AT + 0.60,
         lambda f: (c.share(f, k.INK, LEFT_HALF, 6) + 0.15 < c.share(f, k.INK, RIGHT_HALF, 6),
                    f"L {c.share(f, k.INK, LEFT_HALF, 6):.2f} R {c.share(f, k.INK, RIGHT_HALF, 6):.2f}"))
c.expect("page fully revealed (kicker visible, no ink panel left)", s.REVEAL_END + 0.05,
         lambda f: (c.share(f, k.ACCENT, KICKER, 60) > 0.05 and c.share(f, k.INK, LEFT_EDGE, 6) < 0.02
                    and c.share(f, k.INK, RIGHT_EDGE, 6) < 0.02, ""))
c.expect("final frame == loaded page (resting state)", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.REVEAL_END + 0.1)) < 0.5, ""))
c.run()
