"""Preset 01 — Line-draw logo preloader, as a video scene.

Mirrors snippets/header-injection.html beat-for-beat (same schedule() as
the snippet's JS):
    0.20s+   elements start in DOM order, staggered
             frame + slash: stroke draw (0.9s)
             glyphs: contour trace (0.5s), ink fades in from +0.32s (0.4s)
    ~2.5s    intro done -> accent slash hold-pulse (2.4s period)
    3.40s    overlay fades out (0.55s) revealing the page
    3.95s+   loaded page holds
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import mark as m  # noqa: E402
import scene_kit as k  # noqa: E402

DURATION = 5.6
WIDTH, HEIGHT = k.W, k.H

SCHED, INTRO_END = m.schedule()
DISMISS_AT = INTRO_END + 0.95   # = snippet minShow "auto" (intro + 950ms hold)
FADE = 0.55

SCALE = 1.55
MARK_W = m.VB_W * SCALE
OX = (WIDTH - MARK_W) / 2
OY = (HEIGHT - m.VB_H * SCALE) / 2

PAGE = k.page()


def _elements(t):
    out = []
    glyph_iter = iter(m.GLYPHS)
    for kind, name, length, start in SCHED:
        if kind == "stroke":
            p = k.seg(t, start, start + m.STROKE_DUR, k.ease_in_out)
            off = length * (1 - p)
            if name == "frame":
                f = m.FRAME
                out.append(
                    f'<rect x="{f["x"]}" y="{f["y"]}" width="{f["w"]}" height="{f["h"]}" rx="{f["rx"]}" '
                    f'fill="none" stroke="{k.INK}" stroke-width="3" '
                    f'stroke-dasharray="{length:.2f}" stroke-dashoffset="{off:.2f}"/>')
            else:
                op = k.pulse(t, INTRO_END, m.PULSE_PERIOD, 0.4)
                x1, y1, x2, y2 = m.SLASH
                out.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{k.ACCENT}" '
                    f'stroke-width="5" stroke-linecap="round" opacity="{op:.3f}" '
                    f'stroke-dasharray="{length:.2f}" stroke-dashoffset="{off:.2f}"/>')
        else:
            ch, d, x, _ = next(glyph_iter)
            tp = k.seg(t, start, start + m.TRACE_DUR, k.ease_in_out)
            ip = k.seg(t, start + m.INK_AT, start + m.INK_AT + m.INK_DUR, k.ease_out)
            out.append(
                f'<path transform="translate({m.WORD_X},{m.WORD_BASE})" d="{d}" '
                f'fill="{k.INK}" fill-opacity="{ip:.3f}" stroke="{k.INK}" stroke-width="0.9" '
                f'stroke-opacity="{1 - ip * 0.999:.3f}" '
                f'stroke-dasharray="{length:.2f}" stroke-dashoffset="{length * (1 - tp):.2f}"/>')
    return "".join(out)


def svg_at(t):
    fade = k.seg(t, DISMISS_AT, DISMISS_AT + FADE, k.ease_in_out)
    overlay = ""
    if fade < 1:
        overlay = (f'<g opacity="{1 - fade:.3f}"><rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>'
                   f'<g transform="translate({OX:.2f},{OY:.2f}) scale({SCALE})">{_elements(t)}</g></g>')
    page = PAGE if fade > 0 else ""
    return k.svg_doc(page + overlay)
