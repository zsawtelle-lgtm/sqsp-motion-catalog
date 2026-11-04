"""Placeholder lockup for the line-draw preloader, shared by the video scene
and the snippet generator so both draw the exact same geometry.

Lockup = rounded-square frame (stroke) + accent slash (stroke) + outlined
"Studio" wordmark (filled glyphs, Inter SemiBold, OFL). In a client build the
whole <svg> is replaced with the client's outlined logo.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "shared"))
import scene_kit as k  # noqa: E402

FRAME = dict(x=2, y=2, w=60, h=60, rx=14)            # stroke 3
SLASH = (17, 47, 47, 17)                              # x1 y1 x2 y2, stroke 5
WORD = "Studio"
WORD_SIZE = 52
WORD_X, WORD_BASE = 82, 50
VB_W = 0  # filled below
VB_H = 64

GLYPHS, WORD_W = k.text_paths(WORD, WORD_SIZE, "SemiBold", -0.02)
VB_W = round(WORD_X + WORD_W + 2)

# real lengths (cairosvg ignores pathLength — the browser snippet measures
# with getTotalLength(), this mirrors it for the video)
R = FRAME["rx"]
LEN_FRAME = 2 * (FRAME["w"] - 2 * R) + 2 * (FRAME["h"] - 2 * R) + 2 * 3.14159265 * R
LEN_SLASH = ((SLASH[2] - SLASH[0]) ** 2 + (SLASH[3] - SLASH[1]) ** 2) ** 0.5

# draw order = DOM order: frame, slash, then each glyph
# (kind, ...) kind: 'stroke' draws only; 'fill' traces then inks
ELEMENTS = [("stroke", "frame", LEN_FRAME), ("stroke", "slash", LEN_SLASH)] + [
    ("fill", ch, length) for ch, d, x, length in GLYPHS
]

# ---- timing: the snippet's JS computes the exact same numbers -------------
DELAY = 0.20            # s before the first stroke
STAGGER_MAX = 0.22      # s between element starts
STAGGER_SPAN = 1.80     # s cap for (n-1) * stagger
STROKE_DUR = 0.90       # stroke-only draw
TRACE_DUR = 0.50        # filled shapes: contour trace
INK_AT = 0.32           # ink starts this far into the trace
INK_DUR = 0.40
PULSE_PERIOD = 2.4


def stagger(n):
    return min(STAGGER_MAX, STAGGER_SPAN / max(1, n - 1))


def schedule():
    """[(kind, name, length, start)] plus intro end time."""
    st = stagger(len(ELEMENTS))
    out, end = [], 0.0
    for i, (kind, name, length) in enumerate(ELEMENTS):
        start = DELAY + i * st
        out.append((kind, name, length, start))
        end = max(end, start + (STROKE_DUR if kind == "stroke" else INK_AT + INK_DUR))
    return out, end


def svg_markup(ink="var(--swtl-ink, #1F1E1C)", accent="var(--swtl-accent, #D4552B)", for_web=True):
    """The lockup as inline SVG for the snippet. Colors via CSS classes."""
    f = FRAME
    glyphs = "".join(
        f'<path class="swtl-ld-fill" transform="translate({WORD_X},{WORD_BASE})" d="{d}"/>'
        for ch, d, x, _ in GLYPHS
    )
    return (
        f'<svg class="swtl-ld-mark" viewBox="0 0 {VB_W} {VB_H}" role="img" aria-label="Studio">'
        f'<rect class="swtl-ld-line" x="{f["x"]}" y="{f["y"]}" width="{f["w"]}" height="{f["h"]}" rx="{f["rx"]}" fill="none" stroke-width="3"/>'
        f'<line class="swtl-ld-line swtl-ld-accent" data-pulse x1="{SLASH[0]}" y1="{SLASH[1]}" x2="{SLASH[2]}" y2="{SLASH[3]}" fill="none" stroke-width="5" stroke-linecap="round"/>'
        f"{glyphs}</svg>"
    )
