"""Timed frame assertions for preset 15 (one per beat). Run: python3 checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
m = s.m
TOP = (0, 90, k.W, 200)            # below the header: headline zone of both pages
BOTTOM = (0, k.H - 90, k.W, k.H)   # bottom band
HEADLINE = (60, 200, 660, 330)     # page A's two-line headline / page B's tiles start
LABEL = (int(k.W / 2 - s.LABEL_W / 2) - 4, int(k.H / 2 - 20), int(k.W / 2 + s.LABEL_W / 2) + 4, int(k.H / 2 + 20))


def ink(f, box):
    return c.share(f, k.INK, box, 6)


c.expect("page A at rest: no panel (bottom band is page, not ink)", 0.40,
         lambda f: (ink(f, BOTTOM) < 0.05 and c.share(f, k.INK, HEADLINE, 40) > 0.08,
                    f"bottom ink {ink(f, BOTTOM):.3f}"))
c.expect("nav item hovered before the click (accent 'Work')", s.CLICK - 0.05,
         lambda f: (c.share(f, k.ACCENT, (758, 30, 800, 48), 60) > 0.05,
                    f"{c.share(f, k.ACCENT, (758, 30, 800, 48), 60):.3f}"))
c.expect("panel wiping up: bottom ink, top still page A", s.CLICK + m.IN_DUR * 0.5,
         lambda f: (ink(f, BOTTOM) > 0.99 and ink(f, TOP) < 0.05,
                    f"bottom {ink(f, BOTTOM):.2f} top {ink(f, TOP):.2f}"))
c.expect("covered + label in: page gone, 'Work' in paper at center", s.COVERED + 0.05,
         lambda f: (c.share(f, k.INK, (0, 0, k.W, k.H), 6) > 0.97 and c.share(f, k.PAPER, LABEL, 40) > 0.12,
                    f"label paper {c.share(f, k.PAPER, LABEL, 40):.2f}"))
c.expect("navigation gap: still fully covered (first-paint cover)", s.ARRIVE + 0.04,
         lambda f: (c.share(f, k.INK, (0, 0, k.W, k.H), 6) > 0.97, ""))
c.expect("panel wiping off upward: page B shows at the bottom, top still ink", s.OFF_AT + m.OUT_DUR * 0.5,
         lambda f: (ink(f, BOTTOM) < 0.05 and ink(f, (0, 0, k.W, 60)) > 0.99,
                    f"bottom {ink(f, BOTTOM):.2f}"))
c.expect("page B revealed, differs from page A (new headline)", s.REVEAL_END + 0.05,
         lambda f: (ink(f, (0, 0, k.W, k.H)) < 0.06 and c.diff(f, c.frame(0.40), HEADLINE) > 8,
                    f"diff {c.diff(f, c.frame(0.40), HEADLINE):.1f}"))
c.expect("final frame == revealed page B (resting state)", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.REVEAL_END + 0.1)) < 0.5, ""))
c.run()
