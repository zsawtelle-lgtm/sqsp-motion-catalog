"""Timed frame assertions for preset 18 (one per beat). Run: python checks.py"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker, hex_rgb  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
H, W = k.H, k.W
FT = s.FOOT_TOP                     # 420: top of the fixed footer


def arrow_top(f):
    """First footer row where the accent newsletter arrow shows (works faded:
    accent over ink stays red-dominant)."""
    col = f[FT:H, 330:380]
    rows = np.where(((col[:, :, 0] - col[:, :, 2]) > 40).any(axis=1))[0]
    return FT + int(rows[0]) if len(rows) else None


def hidden(f):
    ink = c.share(f, k.INK, (0, FT, 48, H), 12) + c.share(f, k.INK, (1232, FT, W, H), 12)
    return ink < 0.02, f"ink in footer zone {ink:.2f}"


c.expect("rest: footer hidden under the page", 0.30, hidden)


def entering(f):
    b = s.page_bottom(2.2)
    above = c.share(f, k.PAPER, (0, int(b) - 40, W, int(b) - 30), 6)
    below = c.share(f, k.INK, (0, int(b) + 34, W, H), 20)
    return 600 < b < 700 and above > 0.9 and below > 0.6, f"page bottom {b:.0f}, paper above {above:.2f}, ink below {below:.2f}"


c.expect("page bottom lifts off the charcoal footer", 2.20, entering)


def corners(f):
    b = int(s.page_bottom(2.7))
    corner = c.share(f, k.PAPER, (0, b - 4, 4, b), 10)          # rounded: footer shows at the corner
    edge = c.share(f, k.PAPER, (300, b - 4, 900, b - 1), 10)    # but paper along the edge
    return corner < 0.3 and edge > 0.95, f"corner {corner:.2f}, edge {edge:.2f}"


c.expect("page has rounded bottom corners", 2.70, corners)


def shadow(f):
    b = int(s.page_bottom(2.7))
    band = f[b + 1:b + 6, 300:900].mean()
    ink = hex_rgb(k.INK).mean()
    return band < ink - 6, f"band {band:.1f} vs ink {ink:.1f}"


c.expect("shadow darkens the footer just under the edge", 2.70, shadow)


def rising(f):
    dy, op = s.footer_state(2.7)
    rest = arrow_top(c.frame(s.DURATION))
    now = arrow_top(f)
    return now is not None and 15 < dy < 35 and abs((now - rest) - dy) < 3 and op < 0.9, \
        f"arrow top {now} vs rest {rest} (dy {dy:.1f}, opacity {op:.2f})"


c.expect("footer content mid-rise: offset + faded", 2.70, rising)


def revealed(f):
    b = s.page_bottom(4.2)
    ink = c.share(f, k.INK, (0, FT + 4, W, H), 20)
    links = c.share(f, s.LINK, (560, FT + 90, 1100, FT + 220), 30)
    return abs(b - FT) < 0.5 and ink > 0.75 and links > 0.01 and arrow_top(f) == arrow_top(c.frame(s.DURATION)), \
        f"bottom {b:.1f}, ink {ink:.2f}, link px {links:.3f}"


c.expect("footer fully revealed, content at rest", 4.20, revealed)
c.expect("header stays on top throughout", 2.70,
         lambda f: (c.share(f, k.PAPER, (300, 0, 700, 70), 10) > 0.9, ""))
c.expect("final frame == resting state", s.DURATION,
         lambda f: (c.diff(f, c.frame(4.0)) < 0.3, f"diff {c.diff(f, c.frame(4.0)):.2f}"))
c.run()
