"""Preset 02 — Split-panel wipe preloader, as a video scene.

Mirrors snippets/header-injection.html beat-for-beat (same constants and the
same CSS cubic-beziers, evaluated exactly via mark.bezier):
    0.00s    ink cover (two vertical panels, seam invisible)
    0.15s    logo + hairline track fade/rise in (0.6s, 14px)
    0.55s    accent hairline runs left -> right (1.5s)
    2.15s    dismiss (= 'auto' minShow): logo fades up and out (0.3s)
    2.30s    left panel slides off left (0.9s, strong in-out)
    2.38s    right panel slides off right (0.9s)
    3.28s    page fully revealed, holds to the end
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import mark as m  # noqa: E402
import scene_kit as k  # noqa: E402

DURATION = 5.0
WIDTH, HEIGHT = k.W, k.H
N_PANELS = 2

DISMISS_AT = m.MIN_SHOW
REVEAL_END = m.reveal_end(N_PANELS, DISMISS_AT)

f_part = m.bezier(*m.EASE_PART)
f_in = m.bezier(*m.EASE_IN)
f_line = m.bezier(*m.EASE_LINE)
f_out = m.bezier(*m.EASE_OUT)

LOGO_W = 240.0                       # --swtl-sp-size at 1280 wide
SCALE = LOGO_W / m.VB_W
LOGO_H = m.VB_H * SCALE
TRACK_H = 2
BLOCK_H = LOGO_H + m.GAP + TRACK_H
LX = (WIDTH - LOGO_W) / 2
LY = (HEIGHT - BLOCK_H) / 2
TRACK_Y = LY + LOGO_H + m.GAP

PAGE = k.page()


def seg(t, a, dur, f):
    return f(k.clamp01((t - a) / dur)) if dur > 0 else float(t >= a)


def panel_dx(i, t):
    """Pixel offset of panel i at time t (vertical halves part left/right)."""
    start = DISMISS_AT + m.PART_LEAD + i * m.PART_STAGGER
    p = seg(t, start, m.PART_DUR, f_part)
    w = WIDTH / N_PANELS + 1          # CSS: calc(100%/n + 1px), translate(±100%)
    mid = (N_PANELS - 1) / 2
    d = -(i + 1) if i < mid else (N_PANELS - i)
    return d * w * p


def _logo():
    f = m.FRAME
    glyphs = "".join(f'<path transform="translate({m.WORD_X},{m.WORD_BASE})" d="{d}" fill="{k.PAPER}"/>'
                     for ch, d, x, _ in m.GLYPHS)
    x1, y1, x2, y2 = m.SLASH
    return (f'<rect x="{f["x"]}" y="{f["y"]}" width="{f["w"]}" height="{f["h"]}" rx="{f["rx"]}" '
            f'fill="none" stroke="{k.PAPER}" stroke-width="3"/>'
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{k.ACCENT}" stroke-width="5" stroke-linecap="round"/>'
            + glyphs)


LOGO = _logo()


def _center(t):
    pin = seg(t, m.LOGO_IN_AT, m.LOGO_IN_DUR, f_in)
    pout = seg(t, DISMISS_AT, m.LOGO_OUT_DUR, f_out) if t >= DISMISS_AT else 0.0
    op = pin * (1 - pout)
    if op <= 0.001:
        return ""
    dy = (1 - pin) * m.LOGO_RISE - pout * m.LOGO_OUT_RISE
    run = seg(t, m.LINE_AT, m.LINE_DUR, f_line)
    bar_op = k.pulse(t, m.LINE_AT + m.LINE_DUR + m.HOLD, m.PULSE_PERIOD, 0.4)
    bar = (f'<rect x="{LX:.2f}" y="{TRACK_Y:.2f}" width="{LOGO_W * run:.2f}" height="{TRACK_H}" '
           f'fill="{k.ACCENT}" opacity="{bar_op:.3f}"/>') if run > 0 else ""
    return (f'<g opacity="{op:.3f}" transform="translate(0,{dy:.2f})">'
            f'<g transform="translate({LX:.2f},{LY:.2f}) scale({SCALE:.5f})">{LOGO}</g>'
            f'<rect x="{LX:.2f}" y="{TRACK_Y:.2f}" width="{LOGO_W}" height="{TRACK_H}" fill="{k.PAPER}" opacity="0.16"/>'
            f'{bar}</g>')


def svg_at(t):
    w = WIDTH / N_PANELS
    panels = []
    for i in range(N_PANELS):
        dx = panel_dx(i, t)
        x = i * w + dx
        if x + w + 1 > 0 and x < WIDTH:
            panels.append(f'<rect x="{x:.2f}" y="0" width="{w + 1:.2f}" height="{HEIGHT}" fill="{k.INK}"/>')
    overlay = "".join(panels) + _center(t)
    page = PAGE if t >= DISMISS_AT + m.PART_LEAD else ""
    return k.svg_doc(page + overlay)
