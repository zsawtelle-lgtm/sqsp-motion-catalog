"""Timed frame assertions for preset 16 (one per beat). Run: python checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
tm = s.tm
SNIPPET = (HERE / "snippets" / "footer-injection.html").read_text()
X, Y, W, H = s.CMP


def band(t, x0, x1, y0=0.12, y1=0.24):
    """Screen box for a slice of the comparison block (fractions of w/h)."""
    top = Y - s.scroll_y(t)
    return (int(X + W * x0), int(top + H * y0), int(X + W * x1), int(top + H * y1))


def before(f, t, x0, x1):
    return c.share(f, s.BEFORE_BG, band(t, x0, x1), 10)


def after(f, t, x0, x1):
    return c.share(f, s.AFTER_WALL, band(t, x0, x1), 10)


def handle_box(t):
    hx = X + W * s.pos(t) / 100
    hy = Y - s.scroll_y(t) + H / 2
    return (int(hx - 14), int(hy - 10), int(hx + 14), int(hy + 10))


def cur_box(t):
    x0, y0, _, _ = handle_box(t)
    return (x0 + 20, y0 + 16, x0 + 44, y0 + 46)   # pointer sits just below-right of the handle centre


REST = c.frame(s.REST_AT + 0.1)

# 0. the video uses the snippet's numbers (timing.py <-> JS/CSS)
for needle in [f"HINT_DX = {tm.HINT_DX}", f"HINT_OUT = {int(tm.HINT_OUT * 1000)}",
               f"HINT_HOLD = {int(tm.HINT_HOLD * 1000)}", f"HINT_BACK = {int(tm.HINT_BACK * 1000)}",
               f"start: {tm.START}", f"step: {tm.STEP}", f"threshold: {tm.THRESHOLD}",
               "clip-path: inset(0 0 0 calc(var(--swtl-ba-pos, 50) * 1%))", 'stroke-width="2"',
               "0.5 - 0.5 * Math.cos(Math.PI * p)"]:
    c.expect(f"snippet matches timing.py / scene: {needle}", 0.0, lambda f, n=needle: (n in SNIPPET, ""))

T0 = s.T_HINT - 0.05
c.expect("scrolled in, before the hint: divider at 50% (gray left, warm right)", T0,
         lambda f: (before(f, T0, 0.40, 0.48) > 0.9 and after(f, T0, 0.52, 0.60) > 0.9,
                    f"B={before(f, T0, 0.40, 0.48):.2f} A={after(f, T0, 0.52, 0.60):.2f}"))
TH = s.T_HINT + tm.HINT_OUT + tm.HINT_HOLD / 2
c.expect("hint hold: divider eased to 35% (after shows from 35%)", TH,
         lambda f: (abs(s.pos(TH) - 35) < 1e-6 and after(f, TH, 0.45, 0.49) > 0.9 and before(f, TH, 0.24, 0.33) > 0.9,
                    f"A={after(f, TH, 0.45, 0.49):.2f} B={before(f, TH, 0.24, 0.33):.2f}"))
TM = s.T_HINT + tm.HINT_OUT / 2
c.expect("hint mid-ease: divider between 35% and 50%", TM,
         lambda f: (35 < s.pos(TM) < 50 and after(f, TM, s.pos(TM) / 100 + 0.02, 0.50) > 0.9,
                    f"pos={s.pos(TM):.1f}"))
TB = s.T_HINT + tm.HINT_TOTAL + 0.05
c.expect("hint done: back to the resting frame (no cursor yet)", TB,
         lambda f: (c.diff(f, REST, band(TB, 0, 1, 0, 1)) < 0.05, f"diff={c.diff(f, REST, band(TB, 0, 1, 0, 1)):.3f}"))
TC = s.CUR_AT + 0.03
c.expect("cursor on the handle, icon turns accent (hover state)", TC,
         lambda f: (c.share(f, k.ACCENT, handle_box(TC), 60) > 0.04 and c.share(REST, k.ACCENT, handle_box(TB), 60) < 0.01
                    and c.diff(f, REST, cur_box(TC)) > 20,
                    f"acc={c.share(f, k.ACCENT, handle_box(TC), 60):.3f} cursor diff={c.diff(f, REST, cur_box(TC)):.1f}"))
TD = s.DRAG2[0] - 0.03
c.expect("drag peak: divider at 80% (before shows across 62-76%)", TD,
         lambda f: (before(f, TD, 0.62, 0.76) > 0.85 and after(f, TD, 0.83, 0.95) > 0.9,
                    f"B={before(f, TD, 0.62, 0.76):.2f} A={after(f, TD, 0.83, 0.95):.2f}"))
TR = (s.DRAG2[0] + s.DRAG2[1]) / 2
c.expect("drag back: divider passing 65% on its way to 50%", TR,
         lambda f: (60 < s.pos(TR) < 70 and before(f, TR, 0.52, 0.58) > 0.9 and after(f, TR, 0.72, 0.80) > 0.9,
                    f"pos={s.pos(TR):.1f}"))
c.expect("labels: BEFORE pill top-left, AFTER pill top-right", TD,
         lambda f: (c.share(f, k.INK, band(TD, 0.025, 0.09, 0.04, 0.08), 30) > 0.4
                    and c.share(f, k.INK, band(TD, 0.92, 0.975, 0.04, 0.08), 30) > 0.4, ""))
c.expect("final frame == resting state (divider 50%, cursor gone)", s.DURATION,
         lambda f: (c.diff(f, REST) < 0.05 and before(f, s.DURATION, 0.40, 0.48) > 0.9
                    and after(f, s.DURATION, 0.52, 0.60) > 0.9, f"diff={c.diff(f, REST):.3f}"))
c.run()
