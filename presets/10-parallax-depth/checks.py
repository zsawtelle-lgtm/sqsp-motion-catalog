"""Timed frame assertions for preset 10 (one per beat). Run: python checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker, hex_rgb  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene


def sun_y(f):
    """Screen y (row centroid) of the accent sun on the front tile."""
    import numpy as np
    d = np.sqrt(((f - hex_rgb(k.ACCENT)) ** 2).sum(axis=2))
    ys = np.nonzero(d < 50)[0]
    return float(ys.mean()) if len(ys) > 200 else None


def expected_sun(t):
    f = s.FRONT
    return s.screen_y(f["y"] + f["h"] * 0.34, t, "front")


def headline_y(t):
    return s.screen_y(s.HEAD_Y, t)


# 1. start: layers offset in opposite directions (back up, front down)
c.expect("start: back sinks (-), front floats (+), both clamped", 0.0,
         lambda f: (s.offset("back", 0) < -40 and s.offset("front", 0) > 40
                    and abs(s.offset("back", 0)) <= s.MAX and abs(s.offset("front", 0)) <= s.MAX,
                    f'back {s.offset("back", 0):.0f} front {s.offset("front", 0):.0f}'))
# 2. headline (speed 0) tracks the page exactly: ink present at its expected row
c.expect("text layer moves 1:1 with the page", 2.4,
         lambda f: (c.share(f, k.INK, (60, int(headline_y(2.4)) - 40, 260, int(headline_y(2.4)) + 4), 60) > 0.12,
                    f"y={headline_y(2.4):.0f}"))
# 3. near centre the layers converge on the editor layout
T_MID = min((i / 30 for i in range(int(s.DURATION * 30))), key=lambda t: abs(s.dist_at(t)))
c.expect("layers converge near section centre (|offset| < 8px)", T_MID,
         lambda f: (abs(s.offset("back", T_MID)) < 8 and abs(s.offset("front", T_MID)) < 8,
                    f"t={T_MID:.2f}"))
# 4. front tile sun sits where the formula says (rendered pixels, not maths only)
c.expect("front tile rendered at its parallax offset", 3.2,
         lambda f: (sun_y(f) is not None and abs(sun_y(f) - expected_sun(3.2)) < 6,
                    f"sun {sun_y(f)} vs {expected_sun(3.2):.1f}"))
# 5. layers separate after centre: front leads the page, back lags it
c.expect("layers separated after centre (gap > 60px)", s.SCROLL_T1,
         lambda f: (s.offset("back", s.SCROLL_T1) - s.offset("front", s.SCROLL_T1) > 60,
                    f'{s.offset("back", s.SCROLL_T1) - s.offset("front", s.SCROLL_T1):.0f}px'))
# 6. background never shows its edge: offset within the scale room
SEC_TOP0 = int(s.SEC_Y - s.scroll_at(0))
c.expect("background fills the section top edge (no gap from the 1.12 scale)", 0.0,
         lambda f: (all(abs(s.bg_offset(i / 10)) <= s.SEC_H * 0.06 + 1e-6 for i in range(53))
                    and c.share(f, k.PAPER, (900, SEC_TOP0 + 1, 1280, SEC_TOP0 + 6), 8) < 0.02,
                    f"paper share at top edge {c.share(f, k.PAPER, (900, SEC_TOP0 + 1, 1280, SEC_TOP0 + 6), 8):.3f}"))
# 7. motion visible mid-scroll
c.expect("frames change during the scroll", 2.0,
         lambda f: (c.diff(f, c.frame(2.4)) > 2, f"{c.diff(f, c.frame(2.4)):.1f}"))
# 8. ends at rest
c.expect("final frame == rest (no motion after scroll ends)", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.SCROLL_T1 + 0.05)) < 0.3, ""))
c.run()
