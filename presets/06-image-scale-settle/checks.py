"""Timed frame assertions for preset 06 (one per beat). Run: python checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene

HERO = (0, 80, k.W, k.H)                       # hero on screen before scroll


def on_screen(box):                            # page box -> screen box at full scroll
    x, y, w, h = box
    return (x, int(y - s.SCROLL_PX), x + w, int(y - s.SCROLL_PX + h))


A, B = on_screen(s.IMG_A), on_screen(s.IMG_B)
HERO_REST = c.frame(s.SCROLL_AT - 0.05)
END = c.frame(s.DURATION)


def lum(f, box):
    return float(f[box[1]:box[3], box[0]:box[2]].mean())


c.expect("hero starts dimmed (<92% of resting brightness)", 0.0,
         lambda f: (lum(f, HERO) / lum(HERO_REST, HERO) < 0.92, f"{lum(f, HERO) / lum(HERO_REST, HERO):.3f}"))
D0 = c.diff(c.frame(0.0), HERO_REST, HERO)
c.expect("hero starts zoomed (large diff vs rest)", 0.0,
         lambda f: (D0 > 12, f"diff {D0:.1f}"))
c.expect("expo-out: hero mostly settled at +0.5s but not done", s.HERO_AT + 0.5,
         lambda f: (0.4 < c.diff(f, HERO_REST, HERO) < D0 * 0.35, f"diff {c.diff(f, HERO_REST, HERO):.2f}"))
c.expect("hero at rest before the scroll", s.HERO_AT + s.DUR + 0.2,
         lambda f: (c.diff(f, HERO_REST, HERO) < 0.3, f"diff {c.diff(f, HERO_REST, HERO):.2f}"))
c.expect("row images zoomed+dim on arrival", s.SCROLL_AT + s.SCROLL_DUR,
         lambda f: (c.diff(f, END, A) > 8 and lum(f, A) < lum(END, A) * 0.95,
                    f"diff {c.diff(f, END, A):.1f} lum {lum(f, A) / lum(END, A):.3f}"))
c.expect("stagger: image B trails image A", s.ROW_AT + 0.30,
         lambda f: (c.diff(f, END, B) > c.diff(f, END, A) * 1.15,
                    f"A {c.diff(f, END, A):.2f} B {c.diff(f, END, B):.2f}"))


def frame_fixed(f):
    # 6px paper gutter around each tile: the frame never grows while the photo scales
    ring = [(A[0] - 8, A[1] - 8, A[2] + 8, A[1] - 2), (A[2] + 2, A[1], A[2] + 8, A[3]),
            (B[0] - 8, B[1], B[0] - 2, B[3]), (B[0] - 8, B[1] - 8, B[2] + 8, B[1] - 2)]
    v = min(c.share(f, k.PAPER, r, 6) for r in ring)
    return v > 0.99, f"{v:.3f}"


c.expect("frames fixed: paper gutter intact mid-settle", s.ROW_AT + 0.15, frame_fixed)
c.expect("final frame == resting page", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.REST_AT + 0.3)) < 0.3, f"{c.diff(f, c.frame(s.REST_AT + 0.3)):.2f}"))
c.run()
