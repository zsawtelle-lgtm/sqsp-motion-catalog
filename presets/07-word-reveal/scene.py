"""Preset 07 — Word-by-word headline reveal, as a video scene.

Mirrors snippets/footer-injection.html beat-for-beat (values copied verbatim
from the snippet's CONFIG):
    hero h1      words rise from a per-word line mask, stagger 0.07s, 0.9s expo out
                 <em>built</em> picks up --swtl-accent
    +0.30s       after the last word starts: kicker then body fade up (0.10s apart, 0.7s)
    2.30–3.40s   page scrolls (simulated by translating the page group)
    2.75s        section 2 h2 crosses the 20% threshold → same reveal, then its text fades
    ~4.2s+       resting page
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 4.8
WIDTH, HEIGHT = k.W, k.H

# ---- timing: snippet CONFIG -------------------------------------------------
STAGGER = 0.07
WORD_DUR = 0.90          # cubic-bezier(.16,1,.3,1) ≈ expo out
FOLLOW = 0.30
FADE_STAGGER = 0.10
FADE_DUR = 0.70          # cubic-bezier(.22,1,.36,1)
RISE = 14                # --swtl-wr-rise
TRAVEL = 1.05            # translateY(105%) of the word box
LH = 1.05                # line-height of the mock headings

HERO_AT = 0.30           # IntersectionObserver fires on first paint
SCROLL_AT, SCROLL_END, SCROLL = 2.30, 3.40, 560
S2_AT = 2.75             # section-2 heading reaches the threshold mid-scroll

# ---- layout -----------------------------------------------------------------
TOP = 76
H1_SIZE, H1_TR, H1_X = 64, -0.025, 60
H1_LINES = [[("Spaces", 0), ("built", 1)], [("to", 0), ("be", 0), ("lived", 0), ("in.", 0)]]
H1_BASE = [TOP + 166, TOP + 236]
KICK_Y = TOP + 92

S2_TOP = 700
H2_SIZE, H2_TR, H2_X = 48, -0.02, 62
H2_LINES = [[("Rooms", 0), ("with", 0), ("room", 1), ("to", 0), ("breathe.", 0)]]
H2_BASE = [S2_TOP + 160]
S2_KICK_Y = S2_TOP + 92


def layout(lines, bases, x0, size, tr):
    """[(word, accent, x, baseline, width, index)] — accent words in italic."""
    out, i = [], 0
    space = k.text_paths(" ", size, "SemiBold", tr)[1]
    for line, base in zip(lines, bases):
        x = x0
        for word, acc in line:
            w = k.text_width(word, size, "SemiBoldItalic" if acc else "SemiBold", tr)
            out.append((word, acc, x, base, w, i))
            x += w + space + 2 * tr * size
            i += 1
    return out


H1 = layout(H1_LINES, H1_BASE, H1_X, H1_SIZE, H1_TR)
H2 = layout(H2_LINES, H2_BASE, H2_X, H2_SIZE, H2_TR)


def sched(start, n):
    """Mirror of reveal(): heading starts, then the section clock for fades."""
    return start, start + (n - 1) * STAGGER + FOLLOW


H1_START, H1_FADE = sched(HERO_AT, len(H1))
H2_START, H2_FADE = sched(S2_AT, len(H2))


def words(t, items, start, size, tr, idp):
    out = []
    for word, acc, x, base, w, i in items:
        p = k.seg(t, start + i * STAGGER, start + i * STAGGER + WORD_DUR, k.ease_out_expo)
        dy = (1 - p) * TRAVEL * LH * size
        weight = "SemiBoldItalic" if acc else "SemiBold"
        glyph = k.text_svg(word, 0, dy, size, k.ACCENT if acc else k.INK, weight, tr)
        # mask = the word box: inset(-0.4em -0.25em -0.1em -0.25em), local coords
        top, bot = -(0.80 + 0.40) * size, 0.27 * size
        out.append(
            f'<clipPath id="{idp}{i}"><rect x="{-0.25 * size:.1f}" y="{top:.1f}" '
            f'width="{w + 0.5 * size:.1f}" height="{bot - top:.1f}"/></clipPath>'
            f'<g transform="translate({x:.2f},{base})"><g clip-path="url(#{idp}{i})">{glyph}</g></g>')
    return "".join(out)


def fade(t, at, body):
    p = k.seg(t, at, at + FADE_DUR, k.ease_out)
    if p <= 0:
        return ""
    return f'<g opacity="{p:.3f}" transform="translate(0,{(1 - p) * RISE:.2f})">{body}</g>'


def hero(t):
    out = [image_hero, k.button(64, TOP + 378)]
    out.append(words(t, H1, H1_START, H1_SIZE, H1_TR, "w1-"))
    out.append(fade(t, H1_FADE, k.text_svg("ARCHITECTURE & INTERIORS", 64, KICK_Y, 12, k.ACCENT, "SemiBold", 0.14)))
    out.append(fade(t, H1_FADE + FADE_STAGGER, k.body_lines(64, TOP + 300, [430, 455, 300], 20, 9)))
    return "".join(out)


def section2(t):
    y = S2_TOP
    out = [f'<rect x="64" y="{y}" width="{WIDTH - 128}" height="1" fill="{k.LINE}"/>']
    out.append(words(t, H2, H2_START, H2_SIZE, H2_TR, "w2-"))
    out.append(fade(t, H2_FADE, k.text_svg("SELECTED WORK", 64, S2_KICK_Y, 12, k.ACCENT, "SemiBold", 0.14)))
    out.append(fade(t, H2_FADE + FADE_STAGGER, k.body_lines(64, y + 196, [520, 380], 20, 9)))
    tw = (WIDTH - 128 - 2 * 24) / 3
    for i in range(3):
        out.append(k.image_tile(64 + i * (tw + 24), y + 268, tw, 300, idn=f"s2-{i}"))
    return "".join(out)


image_hero = k.image_tile(700, TOP + 50, 516, 520, idn="hero")


def svg_at(t):
    off = SCROLL * k.seg(t, SCROLL_AT, SCROLL_END, k.ease_in_out)
    page = (f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>'
            f'<g transform="translate(0,{-off:.2f})">{hero(t)}{section2(t)}</g>')
    return k.svg_doc(page + k.site_header())
