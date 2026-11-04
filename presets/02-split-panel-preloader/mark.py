"""Placeholder lockup + timing for the split-panel preloader, shared by the
video scene and the snippet generator so both use the exact same numbers.

Lockup geometry is the same "Studio" mark as preset 01 (rounded-square frame,
accent slash, outlined Inter SemiBold wordmark), drawn in paper on ink. It is
copied here, not imported, so presets stay independent. In a client build the
whole <svg> is replaced with the client's logo.
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
VB_H = 64
GLYPHS, WORD_W = k.text_paths(WORD, WORD_SIZE, "SemiBold", -0.02)
VB_W = round(WORD_X + WORD_W + 2)

# ---- timing (seconds): the snippet's JS uses the exact same numbers --------
LOGO_IN_AT, LOGO_IN_DUR, LOGO_RISE = 0.15, 0.60, 14   # fade + rise (px)
LINE_AT, LINE_DUR = 0.55, 1.50                        # accent hairline run
PULSE_PERIOD = 2.4                                    # hold pulse after run
HOLD = 0.10                                           # beat after the line lands
LOGO_OUT_DUR, LOGO_OUT_RISE = 0.30, 10                # logo fades up and out
PART_LEAD = 0.15                                      # panels start after logo-out begins
PART_DUR = 0.90                                       # panel slide
PART_STAGGER = 0.08                                   # between panels
GAP = 28                                              # px, logo -> hairline

MIN_SHOW = LINE_AT + LINE_DUR + HOLD                  # 'auto' minShow = 2.15s


def reveal_end(n=2, start=MIN_SHOW):
    return start + PART_LEAD + (n - 1) * PART_STAGGER + PART_DUR


def svg_markup():
    """The lockup as inline SVG for the snippet. Colors via CSS classes."""
    f = FRAME
    glyphs = "".join(
        f'<path class="swtl-sp-fill" transform="translate({WORD_X},{WORD_BASE})" d="{d}"/>'
        for ch, d, x, _ in GLYPHS
    )
    return (
        f'<svg class="swtl-sp-mark" viewBox="0 0 {VB_W} {VB_H}" role="img" aria-label="Studio">'
        f'<rect class="swtl-sp-line" x="{f["x"]}" y="{f["y"]}" width="{f["w"]}" height="{f["h"]}" rx="{f["rx"]}" fill="none" stroke-width="3"/>'
        f'<line class="swtl-sp-accent" x1="{SLASH[0]}" y1="{SLASH[1]}" x2="{SLASH[2]}" y2="{SLASH[3]}" stroke-width="5" stroke-linecap="round"/>'
        f"{glyphs}</svg>"
    )


# ---- CSS easing curves, evaluated exactly (video == browser) ---------------
EASE_PART = (0.77, 0, 0.18, 1)     # panels: strong in-out (quart-like)
EASE_IN = (0.22, 1, 0.36, 1)       # logo in: soft out
EASE_LINE = (0.65, 0, 0.35, 1)     # hairline run
EASE_OUT = (0.55, 0, 1, 0.45)      # logo out: quick in


def bezier(x1, y1, x2, y2):
    """Return f(p) for CSS cubic-bezier(x1,y1,x2,y2) (Newton + bisection)."""
    def cx(s):
        return 3 * x1 * s * (1 - s) ** 2 + 3 * x2 * s * s * (1 - s) + s ** 3

    def cy(s):
        return 3 * y1 * s * (1 - s) ** 2 + 3 * y2 * s * s * (1 - s) + s ** 3

    def f(p):
        if p <= 0:
            return 0.0
        if p >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if cx(mid) < p:
                lo = mid
            else:
                hi = mid
        return cy((lo + hi) / 2)
    return f


def css(curve):
    return "cubic-bezier(%s)" % ",".join(f"{v:g}" for v in curve)
