"""Preset 12 — Scroll text fill, as a video scene.

Mirrors snippets/footer-injection.html (values copied verbatim from CONFIG):
    words rest at opacity DIM (0.18) and fill to full ink in reading order
    progress p = (START*vh - top) / ((START - END)*vh), clamped 0..1,
        where top is the statement's line-box top on screen
    word i fill  f = clamp((p*(n + SOFT) - i) / SOFT)
    opacity = DIM + (1 - DIM)*f;  the <em> word blends ink → --swtl-accent with f
Scroll-linked, not time-based: the page scrolls slowly (simulated by
translating the page group) and the fill follows the scroll position.

    0.00–0.25s   page at rest, statement dim near the bottom of the view
    0.25–4.00s   slow scroll; top crosses 85% → fill starts, 40% → complete
    4.00–4.90s   resting page, statement fully filled
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 4.9
WIDTH, HEIGHT = k.W, k.H

# ---- snippet CONFIG -------------------------------------------------------
START, END, SOFT, DIM = 0.85, 0.40, 2, 0.18

# ---- scroll -----------------------------------------------------------------
SCROLL_AT, SCROLL_END = 0.25, 4.00
TOP0 = 0.88 * HEIGHT          # statement top on screen at t=0 (page coords)
SCROLL = TOP0 - 0.30 * HEIGHT  # ends with the top at 30% of the view

# ---- layout -----------------------------------------------------------------
SIZE, TR, LH, X0, MAXW = 68, -0.03, 1.08, 61, 1000
TEXT = "We design homes that age well, cost less to run, and feel calm on a Tuesday."
ACCENT_WORDS = {"calm"}
KICK_Y = TOP0 - 30


def _layout():
    """Greedy wrap like the browser: [(word, accent, x, baseline, index)]."""
    space = k.text_width(" ", SIZE, "SemiBold", TR) + TR * SIZE
    out, x, line = [], X0, 0
    for i, word in enumerate(TEXT.split(" ")):
        acc = word in ACCENT_WORDS
        w = k.text_width(word, SIZE, "SemiBoldItalic" if acc else "SemiBold", TR)
        if x > X0 and x + w > X0 + MAXW:
            x, line = X0, line + 1
        out.append((word, acc, x, TOP0 + line * LH * SIZE + 0.915 * SIZE, i, w))
        x += w + space + TR * SIZE
    return out, line + 1


WORDS, LINES = _layout()
N = len(WORDS)
BLOCK_BOTTOM = TOP0 + LINES * LH * SIZE


def scroll(t):
    return SCROLL * k.seg(t, SCROLL_AT, SCROLL_END, k.ease_in_out)


def progress(t):
    top = TOP0 - scroll(t)
    return k.clamp01((START * HEIGHT - top) / ((START - END) * HEIGHT))


def word_fill(t, i):
    return k.clamp01((progress(t) * (N + SOFT) - i) / SOFT)


def _mix(a, b, p):
    ca = [int(a[j:j + 2], 16) for j in (1, 3, 5)]
    cb = [int(b[j:j + 2], 16) for j in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * p):02X}" for x, y in zip(ca, cb))


def statement(t):
    out = []
    for word, acc, x, base, i, _ in WORDS:
        f = word_fill(t, i)
        color = _mix(k.INK, k.ACCENT, f) if acc else k.INK
        op = DIM + (1 - DIM) * f
        out.append(k.text_svg(word, x, base, SIZE, color, "SemiBoldItalic" if acc else "SemiBold", TR,
                              extra=f'opacity="{op:.3f}"'))
    return "".join(out)


def page(t):
    out = []
    # tail of the section above: two image tiles and a rule
    tw = (WIDTH - 128 - 24) / 2
    out.append(k.image_tile(64, 96, tw, 340, idn="a"))
    out.append(k.image_tile(64 + tw + 24, 96, tw, 340, tone=k.TILE, idn="b"))
    out.append(k.body_lines(64, 462, [300, 220], 18, 8))
    out.append(f'<rect x="64" y="{KICK_Y - 52:.0f}" width="{WIDTH - 128}" height="1" fill="{k.LINE}"/>')
    # statement section
    out.append(k.text_svg("OUR APPROACH", 64, KICK_Y, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(statement(t))
    y = BLOCK_BOTTOM + 34
    out.append(k.body_lines(64, y, [420, 380], 20, 9))
    out.append(k.button(64, y + 64, "Our process"))
    tw3 = (WIDTH - 128 - 48) / 3
    for i in range(3):
        out.append(k.image_tile(64 + i * (tw3 + 24), y + 150, tw3, 260, idn=f"c{i}"))
    return "".join(out)


def svg_at(t):
    body = (f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>'
            f'<g transform="translate(0,{-scroll(t):.2f})">{page(t)}</g>')
    return k.svg_doc(body + k.site_header())
