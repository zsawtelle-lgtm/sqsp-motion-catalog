"""Timed frame assertions for preset 09 (one per beat). Run: python checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
H = k.H

HEAD_BOX = (40, 216, 520, 290)        # heading zone of a card pinned at the top


def top_of(t, i):
    return s.layout(t)[i][0]


def rest1(f):
    ok = c.share(f, k.PAPER, (0, 80, k.W, H), 12) > 0.55 and c.share(f, k.INK, HEAD_BOX, 60) > 0.15
    return ok, f"paper {c.share(f, k.PAPER, (0, 80, k.W, H), 12):.2f}"


c.expect("rest: card 1 (paper) under header, untouched", 0.30, rest1)


def sliding(f):
    t2 = top_of(1.2, 1)
    ink_below = c.share(f, k.INK, (0, int(t2) + 30, 600, H), 20)
    return 200 < t2 < 600 and ink_below > 0.6, f"card2 top {t2:.0f}, ink below {ink_below:.2f}"


c.expect("card 2 (ink) slides up over card 1", 1.20, sliding)


def covered(f):
    top1, p1 = s.layout(1.9)[0]
    gutter = c.share(f, k.PAPER, (0, 100, 10, 160), 6)  # card 1 scaled in -> raw paper gutter
    dimmed = c.share(f, k.PAPER, (300, 90, 640, 110), 6)  # card 1's own paper is now dimmed
    return abs(top1 - s.TOP) < 0.5 and p1 > 0.5 and gutter > 0.9 and dimmed < 0.05, \
        f"top {top1:.1f}, p {p1:.2f}, gutter {gutter:.2f}, dimmed-paper {dimmed:.2f}"


c.expect("card 1 pinned at header, scaled < 1 and dimmed", 1.90, covered)


def rounded(f):
    t2 = int(top_of(1.2, 1))
    corner = c.share(f, k.INK, (0, t2, 5, t2 + 5), 30)        # rounded: not ink at the very corner
    edge = c.share(f, k.INK, (200, t2 + 2, 400, t2 + 8), 30)  # but ink along the top edge
    return corner < 0.3 and edge > 0.9, f"corner {corner:.2f}, edge {edge:.2f}"


c.expect("incoming card has rounded top corners", 1.20, rounded)


def pinned2(f):
    return c.share(f, k.PAPER, HEAD_BOX, 40) > 0.15 and c.share(f, k.INK, (0, 300, k.W, H), 20) > 0.6, \
        "Design heading pinned"


c.expect("hold: card 2 pinned, fully covering card 1", 2.60, pinned2)


def accent_in(f):
    t3 = top_of(4.0, 2)
    acc = c.share(f, k.ACCENT, (0, int(t3) + 20, 600, H), 30)
    return t3 < 400 and acc > 0.6, f"card3 top {t3:.0f}, accent {acc:.2f}"


c.expect("card 3 (accent) slides over card 2", 4.00, accent_in)
c.expect("header stays on top throughout", 3.60,
         lambda f: (c.share(f, k.PAPER, (300, 0, 700, 70), 10) > 0.9, ""))
c.expect("final frame == settled stack (resting state)", s.DURATION,
         lambda f: (c.diff(f, c.frame(4.9)) < 0.5 and c.share(f, k.ACCENT, (0, 90, 640, 720), 30) > 0.6, ""))
c.run()
