"""Preset 15 — Page transition wipe, as a video scene.

Mirrors snippets/header-injection.html beat-for-beat (same constants and the
same CSS cubic-beziers, evaluated exactly via timing.bezier):
    0.00s    page A (mock homepage) at rest, cursor drifts to the nav
    0.95s    click "Work": ink panel wipes up from the bottom (0.5s)
    1.10s    label ("Work", the link text) fades/rises in (0.35s)
    1.45s    page covered -> browser navigates (network gap shown as a hold)
    1.85s    page B DOMContentLoaded: panel replaces the first-paint cover
    1.93s    after HOLD, panel wipes up and off (0.6s), label fades (0.25s)
    2.53s    page B ("Selected work") revealed, holds to the end
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import timing as m  # noqa: E402
import scene_kit as k  # noqa: E402

DURATION = 4.2
WIDTH, HEIGHT = k.W, k.H

CLICK = 0.95                         # click on the nav item
COVERED = CLICK + m.IN_DUR           # panel fully up -> navigate
ARRIVE = COVERED + 0.40              # next page's DOMContentLoaded
OFF_AT = ARRIVE + m.HOLD             # wipe-off starts
REVEAL_END = OFF_AT + m.OUT_DUR

f_wipe = m.bezier(*m.EASE_WIPE)
f_label = m.bezier(*m.EASE_LABEL)

LABEL = "Work"
LABEL_SIZE = 33                      # clamp(22px, 2.6vw, 34px) at 1280 wide
LABEL_W = k.text_width(LABEL, LABEL_SIZE, "SemiBold", -0.01)

# nav item "Work" in k.site_header(): x=760, baseline y=44, 14px Medium
NAV_X, NAV_Y = 760 + k.text_width("Work", 14, "Medium") / 2, 39
CUR_FROM = (1010.0, 430.0)
CUR_TO = (NAV_X - 2, NAV_Y - 4)
CUR_MOVE = (0.15, 0.80)


def seg(t, a, dur, f):
    return f(k.clamp01((t - a) / dur)) if dur > 0 else float(t >= a)


# ---- pages -------------------------------------------------------------------
PAGE_A = k.page()
PAGE_A_HOVER = k.page(active="Work")


def _page_b():
    y = 76
    out = [f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>', k.site_header(active="Work")]
    out.append(k.text_svg("PORTFOLIO · 24 PROJECTS", 64, y + 86, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("Selected work", 60, y + 160, 64, k.INK, "SemiBold", -0.025))
    out.append(k.body_lines(812, y + 110, [404, 380, 250], 20, 9))
    tw, gap, ty = (WIDTH - 128 - 2 * 24) / 3, 24, y + 214
    tones = (k.TILE, "#DED7C9", k.TILE)
    for i in range(3):
        x = 64 + i * (tw + gap)
        out.append(k.image_tile(x, ty, tw, 400, tone=tones[i], accent=k.ACCENT if i == 1 else None, idn=f"b{i}"))
    return "".join(out)


PAGE_B = _page_b()


# ---- overlay -------------------------------------------------------------------
def panel_y(t):
    """Top edge of the ink panel (px), or None when it is off screen."""
    if t < CLICK:
        return None
    if t < ARRIVE:                    # wipe up over page A, then covered
        return HEIGHT * (1 - seg(t, CLICK, m.IN_DUR, f_wipe))
    p = seg(t, OFF_AT, m.OUT_DUR, f_wipe)
    return None if p >= 1 else -HEIGHT * p


def _label(t, top):
    if t < ARRIVE:
        p = seg(t, CLICK + m.LABEL_IN_AT, m.LABEL_IN_DUR, f_label)
        op, dy = p, (1 - p) * m.LABEL_RISE
    else:
        op, dy = 1 - k.clamp01((t - OFF_AT) / m.LABEL_OUT_DUR), 0.0
    if op <= 0.001:
        return ""
    base = top + HEIGHT / 2 + LABEL_SIZE * 0.36 + dy
    return k.text_svg(LABEL, WIDTH / 2, base, LABEL_SIZE, k.PAPER, "SemiBold", -0.01,
                      anchor="middle", extra=f'opacity="{op:.3f}"')


CURSOR_D = "M0,0 L0,17 L4.6,13 L7.6,20.2 L10.4,19 L7.5,12 L13,12 Z"


def _cursor(t):
    p = seg(t, CUR_MOVE[0], CUR_MOVE[1] - CUR_MOVE[0], k.ease_in_out)
    x = k.lerp(CUR_FROM[0], CUR_TO[0], p)
    y = k.lerp(CUR_FROM[1], CUR_TO[1], p)
    press = 0.86 if CLICK - 0.06 <= t < CLICK + 0.08 else 1.0
    s = 1.35 * press
    return (f'<path transform="translate({x:.2f},{y:.2f}) scale({s:.3f})" d="{CURSOR_D}" '
            f'fill="#FFFFFF" stroke="{k.INK}" stroke-width="1.1" stroke-linejoin="round"/>')


def svg_at(t):
    if t < ARRIVE:
        page = PAGE_A_HOVER if t >= CUR_MOVE[1] - 0.05 else PAGE_A
    else:
        page = PAGE_B
    top = panel_y(t)
    overlay = ""
    if top is not None:
        overlay = (f'<rect x="0" y="{top:.2f}" width="{WIDTH}" height="{HEIGHT}" fill="{k.INK}"/>'
                   + _label(t, top))
    return k.svg_doc(page + overlay + _cursor(t))
