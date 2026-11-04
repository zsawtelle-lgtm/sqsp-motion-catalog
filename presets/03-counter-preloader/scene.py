"""Preset 03 — Counter / progress-fill preloader, as a video scene.

Mirrors snippets/header-injection.html beat-for-beat (both read timing.py),
laid out exactly as the CSS resolves at 1280x720:
    0.00s    overlay mounted: wordmark top-left, "LOADING" top-right,
             counter 0 bottom-left, accent bar empty along the bottom edge
    0-2.6s   counter + bar crawl toward 90 (90 * (1 - e^(-t/0.9)))
    2.60s    simulated window load (later than minShow 1.8s, so the video
             shows the honest crawl parking in the high 80s)
    2.6-3.2  counter completes 85 -> 100 (power3.out), bar fills
    3.45s    hold done -> digits roll up out of their clip, chrome fades
    3.60s    overlay wipes up (0.75s); the bar is its leading edge
    4.35s+   loaded page holds
Numerals: Inter Medium tabular figures (.tf), outlined — the snippet uses
the site's own font with font-variant-numeric: tabular-nums.
"""
import functools
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402
import timing as T  # noqa: E402

DURATION = 5.4
WIDTH, HEIGHT = k.W, k.H

LOAD_AT = 2.6                                 # simulated window.load
READY_AT = max(LOAD_AT, T.MIN_SHOW)
DONE_AT = READY_AT + T.FINISH                 # counter shows 100
EXIT_AT = T.exit_at(READY_AT)                 # roll starts
WIPE_AT = EXIT_AT + T.WIPE_DELAY
WIPE_END = WIPE_AT + T.WIPE

# ---- layout (CSS resolved at 1280 wide) ----------------------------------
GUTTER = 64                     # clamp(20px, 5vw, 64px)
BAR_H = 4
SIZE = 0.17 * WIDTH             # clamp(96px, 17vw, 220px) -> 217.6
LINE_H = 0.74 * SIZE
BOX_BOTTOM = HEIGHT - GUTTER - BAR_H            # .swtl-ct-count bottom
BOX_TOP = BOX_BOTTOM - LINE_H
BASELINE = BOX_BOTTOM - 4                      # matches Chrome screenshot (half-leading)
TRACK = -0.045 * SIZE
PCT_SIZE = 0.2 * SIZE
CLIP_TOP = BOX_TOP - 0.05 * SIZE
ROLL_NUM = 1.10 * LINE_H        # translateY(-110%)
ROLL_PCT = 5.60 * PCT_SIZE      # translateY(-560%)
LABEL_FILL = "#8F8A82"          # ink @ .55 on paper

DIGIT = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


@functools.lru_cache(maxsize=16)
def _digit(i, size):
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    font = k._font("Medium")
    gs = font.getGlyphSet()
    s = size / font["head"].unitsPerEm
    name = DIGIT[i] + ".tf"
    pen = SVGPathPen(gs)
    gs[name].draw(TransformPen(pen, (s, 0, 0, -s, 0, 0)))
    return pen.getCommands(), font["hmtx"][name][0] * s


def number_svg(n, x, y, size, fill):
    out, cx = [], x
    for ch in str(n):
        d, adv = _digit(int(ch), size)
        out.append(f'<path transform="translate({cx:.2f},{y:.2f})" d="{d}" fill="{fill}"/>')
        cx += adv + TRACK
    return "".join(out), cx          # CSS letter-spacing trails the last digit too


def value_at(t):
    return T.value(t, READY_AT)


PAGE = k.page()


def overlay(t):
    v = value_at(t)
    n = 100 if v >= 99.999 else int(v)
    roll = k.seg(t, EXIT_AT, EXIT_AT + T.ROLL, k.ease_sweep)
    chrome = 1 - k.seg(t, EXIT_AT, EXIT_AT + T.ROLL, k.ease_out)

    digits, end_x = number_svg(n, GUTTER - 0.02 * SIZE, BASELINE - roll * ROLL_NUM, SIZE, k.INK)
    pct = k.text_svg("%", end_x + 0.25 * PCT_SIZE,
                     CLIP_TOP + 0.05 * SIZE + PCT_SIZE * 0.86 - roll * ROLL_PCT, PCT_SIZE, k.ACCENT, "Medium")
    clip = (f'<clipPath id="ct-clip"><rect x="0" y="{CLIP_TOP:.1f}" width="{WIDTH}" '
            f'height="{BOX_BOTTOM - CLIP_TOP + 40:.1f}"/></clipPath>')
    logo = (f'<rect x="{GUTTER}" y="26" width="24" height="24" rx="6" fill="none" stroke="{k.INK}" stroke-width="2"/>'
            f'<line x1="{GUTTER + 6}" y1="44" x2="{GUTTER + 18}" y2="32" stroke="{k.ACCENT}" stroke-width="2.4" stroke-linecap="round"/>'
            + k.text_svg("Studio", GUTTER + 34, 45, 19, k.INK, "SemiBold", -0.01))
    label = k.text_svg("LOADING", WIDTH - GUTTER, 42, 12, LABEL_FILL, "SemiBold", 0.14, anchor="end")
    bar = f'<rect x="0" y="{HEIGHT - BAR_H}" width="{WIDTH * v / 100:.2f}" height="{BAR_H}" fill="{k.ACCENT}"/>'
    return (f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>'
            f'<g opacity="{chrome:.3f}">{logo}{label}</g>'
            f'<defs>{clip}</defs><g clip-path="url(#ct-clip)">{digits}{pct}</g>{bar}')


def svg_at(t):
    wipe = k.seg(t, WIPE_AT, WIPE_END, k.ease_sweep)
    page = PAGE if wipe > 0 else ""
    ov = ""
    if wipe < 1:
        ov = f'<g transform="translate(0,{-wipe * HEIGHT:.2f})">{overlay(t)}</g>'
    return k.svg_doc(page + ov)
