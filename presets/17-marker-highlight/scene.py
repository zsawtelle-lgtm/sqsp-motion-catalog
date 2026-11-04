"""Preset 17 — Marker highlight & underline draw, as a video scene.

Mirrors snippets/footer-injection.html beat-for-beat (values copied verbatim
from the snippet's CONFIG and geometry functions):
    hero h1       <em>works</em> → highlight band (35% tall, at 88%) grows
                  left→right: observer at first paint + delay 0.15s, 0.8s
                  cubic-bezier(.7,0,.2,1) (= scene_kit.ease_sweep)
    1.70–2.80s    page scrolls (simulated by translating the page group)
    section 2     paragraph: <em> phrase wraps to two lines → one underline
                  stroke per line (drawn in sequence, time split by length,
                  the last line ends in a return swoosh); <strong>tested</strong>
                  → rough circle, 0.25s stagger, 0.8 × 1.15s
    ~4.0s+        resting page
Stroke lengths are real (svgpathtools), since cairosvg ignores pathLength.
"""
import math
import pathlib
import sys

from svgpathtools import parse_path

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 4.8
WIDTH, HEIGHT = k.W, k.H

# ---- timing: snippet CONFIG -------------------------------------------------
DUR = 0.80
STAGGER = 0.25
DELAY = 0.15
CIRCLE_X = 1.15
WEIGHT = 0.08
BAND_H, BAND_POS, BAND_PAD = 0.35, 0.88, 0.06
ROOT_MARGIN = 0.15            # rootMargin bottom -15%
ASC, LINE_H = 0.969, 1.21     # Inter hhea: content-area box of an inline element
ease = k.ease_sweep           # cubic-bezier(.7,0,.2,1)

HERO_IO = 0.30                # observer fires on first paint
SCROLL_AT, SCROLL_END, SCROLL = 1.70, 2.80, 560
BAND = "#E5A58C"              # accent at 38% over paper (color-mix in the snippet)

# ---- layout -----------------------------------------------------------------
TOP = 76
H1_SIZE, H1_TR, H1_X = 64, -0.025, 60
H1_BASE = [TOP + 166, TOP + 236]
KICK_Y = TOP + 92

S2_TOP = 720
P_SIZE, P_X = 34, 64
P_BASE = [S2_TOP + 150, S2_TOP + 196]
P_LINES = [
    [("We plan every launch around ", "Medium"), ("the people who", "MediumItalic")],
    [("use it every day", "MediumItalic"), (", and every page is ", "Medium"), ("tested", "Bold"), (".", "Medium")],
]


def runs(lines, bases, x0, size, tr=0.0):
    """[(text, weight, x, baseline, width)] laid out like inline text."""
    out = []
    for line, base in zip(lines, bases):
        x = x0
        for text, weight in line:
            w = k.text_width(text, size, weight, tr)
            out.append((text, weight, x, base, w))
            x += w
    return out


H1 = runs([[("Design that ", "SemiBold"), ("works", "SemiBoldItalic")],
           [("as hard as you do.", "SemiBold")]], H1_BASE, H1_X, H1_SIZE, H1_TR)
WORKS = H1[1]
P = runs(P_LINES, P_BASE, P_X, P_SIZE)
EM_RUNS = [P[1], P[2]]        # the wrapped <em> phrase, one run per line
TESTED = P[4]


def rect(run):
    """getClientRects() box of an inline run: content area, not line box."""
    _, _, x, base, w = run
    size = P_SIZE if run in P else H1_SIZE
    return dict(x=x, y=base - ASC * size, w=w, h=LINE_H * size)


# ---- geometry: verbatim ports of the snippet's functions --------------------
def f(p):
    return f"{p[0]:.1f},{p[1]:.1f}"


def smooth(p):
    d = "M" + f(p[0])
    for i in range(len(p) - 1):
        a = p[i - 1] if i > 0 else p[i]
        b, c = p[i], p[i + 1]
        e = p[i + 2] if i + 2 < len(p) else c
        d += ("C" + f((b[0] + (c[0] - a[0]) / 6, b[1] + (c[1] - a[1]) / 6)) + " "
              + f((c[0] - (e[0] - b[0]) / 6, c[1] - (e[1] - b[1]) / 6)) + " " + f(c))
    return d


def underline(r, last):
    x, w, h = r["x"], r["w"], r["h"]
    y = r["y"] + h * 0.9
    p = [(x - h * .08, y + h * .03), (x + w * .35, y - h * .02), (x + w * .7, y + h * .02), (x + w + h * .12, y - h * .04)]
    if last:
        p += [(x + w * .62, y + h * .09), (x + w * .2, y + h * .13)]
    return smooth(p)


def circle(r):
    cx, cy = r["x"] + r["w"] / 2, r["y"] + r["h"] * .52
    rx, ry = r["w"] / 2 + r["h"] * .32, r["h"] * .62
    n, tilt = 26, -0.07
    ct, st = math.cos(tilt), math.sin(tilt)
    p = []
    for i in range(n + 1):
        t = i / n
        a = -2.5 + math.pi * 2 * 1.12 * t
        kk = 0.97 + 0.07 * t + 0.03 * math.sin(t * 9)
        dx, dy = math.cos(a) * rx * kk, math.sin(a) * ry * kk
        p.append((cx + dx * ct - dy * st, cy + dx * st + dy * ct))
    return smooth(p)


UL = [underline(rect(r), i == len(EM_RUNS) - 1) for i, r in enumerate(EM_RUNS)]
UL_LEN = [parse_path(d).length() + 2 for d in UL]
CIRC = circle(rect(TESTED))
CIRC_LEN = parse_path(CIRC).length() + 2
STROKE = max(2, P_SIZE * WEIGHT)


def scroll_off(t):
    return SCROLL * k.seg(t, SCROLL_AT, SCROLL_END, k.ease_in_out)


def crossing(run):
    """First time the run's top passes the observer line (85% of viewport)."""
    top = rect(run)["y"]
    t = 0.0
    while t < DURATION:
        if top - scroll_off(t) < HEIGHT * (1 - ROOT_MARGIN):
            return t
        t += 1 / 120
    return DURATION


# reveal(): start = max(now + delay, section clock); clock = start + stagger
WORKS_AT = HERO_IO + DELAY
UL_AT = crossing(EM_RUNS[0]) + DELAY
CIRC_AT = max(crossing(TESTED) + DELAY, UL_AT + STAGGER)
UL_SPLIT = [DUR * L / sum(UL_LEN) for L in UL_LEN]
UL_STARTS = [UL_AT, UL_AT + UL_SPLIT[0]]
CIRC_DUR = DUR * CIRCLE_X


def stroke(d, length, p, color=k.ACCENT):
    if p <= 0:
        return ""
    off = length * (1 - p)
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{STROKE:.1f}" stroke-linecap="round" '
            f'stroke-linejoin="round" stroke-dasharray="{length:.1f} {length:.1f}" stroke-dashoffset="{off:.2f}"/>')


def band(t):
    p = k.seg(t, WORKS_AT, WORKS_AT + DUR, ease)
    r = rect(WORKS)
    pad = BAND_PAD * H1_SIZE
    bw, bh = (r["w"] + 2 * pad) * p, r["h"] * BAND_H
    by = r["y"] + (r["h"] - bh) * BAND_POS
    return f'<rect x="{r["x"] - pad:.2f}" y="{by:.2f}" width="{bw:.2f}" height="{bh:.2f}" fill="{BAND}"/>' if p > 0 else ""


def text_runs(items, size, tr=0.0):
    return "".join(k.text_svg(txt, x, base, size, k.INK, wt, tr) for txt, wt, x, base, w in items)


def hero(t):
    out = [image_hero, k.text_svg("BRAND & WEB STUDIO", 64, KICK_Y, 12, k.ACCENT, "SemiBold", 0.14)]
    out.append(band(t))                      # background of the <em>: behind its text
    out.append(text_runs(H1, H1_SIZE, H1_TR))
    out.append(k.body_lines(64, TOP + 300, [430, 455, 300], 20, 9))
    out.append(k.button(64, TOP + 378))
    return "".join(out)


def section2(t):
    y = S2_TOP
    out = [f'<rect x="64" y="{y}" width="{WIDTH - 128}" height="1" fill="{k.LINE}"/>',
           k.text_svg("HOW WE WORK", 64, y + 76, 12, k.ACCENT, "SemiBold", 0.14),
           text_runs(P, P_SIZE),
           k.body_lines(64, y + 250, [560, 600, 420], 20, 9),
           k.image_tile(64, y + 340, 540, 300, idn="s2a"), k.image_tile(628, y + 340, 588, 300, idn="s2b")]
    # overlay SVG paints after the text block (z-index 1)
    for i, (d, L) in enumerate(zip(UL, UL_LEN)):
        out.append(stroke(d, L, k.seg(t, UL_STARTS[i], UL_STARTS[i] + UL_SPLIT[i], ease)))
    out.append(stroke(CIRC, CIRC_LEN, k.seg(t, CIRC_AT, CIRC_AT + CIRC_DUR, ease)))
    return "".join(out)


image_hero = k.image_tile(700, TOP + 50, 516, 520, idn="hero")


def svg_at(t):
    off = scroll_off(t)
    page = (f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>'
            f'<g transform="translate(0,{-off:.2f})">{hero(t)}{section2(t)}</g>')
    return k.svg_doc(page + k.site_header())
