"""Preset 09 — Sticky stacked-card scroll, as a video scene.

Mirrors snippets/footer-injection.html: three consecutive sections (paper,
ink, accent) under a fixed 76px header. Each pins at top = header height;
the next slides up over it with 24px rounded top corners; the covered card
scales 1 -> 0.94 (origin top-center) and dims to 0.35 ink as
p = (viewportH - nextTop) / (viewportH - stickyTop) goes 0 -> 1.

Beats (page scroll is simulated by moving the cards):
    0.00-0.50  rest on card 1
    0.50-2.40  scroll: card 2 slides over card 1 (card 1 shrinks + dims)
    2.40-2.90  hold, card 2 pinned
    2.90-4.80  scroll: card 3 slides over card 2
    4.80-5.60  rest (final frame = stack settled)
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 5.6
WIDTH, HEIGHT = k.W, k.H

# snippet defaults, copied verbatim
SCALE_MIN = 0.94
DIM = 0.35
RADIUS = 24
TOP = 76                      # headerOffset 'auto' -> fixed header height
CARD_H = HEIGHT - TOP         # 644: each section fills the space below the header

S1 = (0.50, 2.40)
S2 = (2.90, 4.80)

CARDS = [
    # bg, fg, muted bar, kicker color, number, heading, tile tone, tile sun
    dict(bg=k.PAPER, fg=k.INK, bar=k.LINE, kick=k.ACCENT, n="01", head="Strategy", tile=k.TILE, sun=k.ACCENT),
    dict(bg=k.INK, fg=k.PAPER, bar="#4A4843", kick=k.ACCENT, n="02", head="Design", tile="#3A3833", sun=k.ACCENT),
    dict(bg=k.ACCENT, fg=k.PAPER, bar="#E68A6B", kick=k.INK, n="03", head="Launch", tile="#E9A285", sun=k.PAPER),
]


def scroll(t):
    """Page scroll in px (one card = CARD_H)."""
    return CARD_H * (k.seg(t, *S1, k.ease_in_out) + k.seg(t, *S2, k.ease_in_out))


def layout(t):
    """[(top, progress)] per card, exactly as the snippet computes it."""
    s = scroll(t)
    tops = []
    for i in range(len(CARDS)):
        doc_top = TOP + i * CARD_H - s
        sticky = i < len(CARDS) - 1          # last card is not sticky
        tops.append(max(TOP, doc_top) if sticky else doc_top)
    out = []
    for i, top in enumerate(tops):
        p = 0.0
        if i < len(tops) - 1:
            p = k.clamp01((HEIGHT - tops[i + 1]) / (HEIGHT - TOP))
        out.append((top, p))
    return out


def card(i, c, top, p):
    sc = 1 - (1 - SCALE_MIN) * p
    rx = RADIUS if i > 0 else 0
    # rounded top corners only: rounded rect + square patch on the bottom
    shape = (f'<path d="M0,{rx} Q0,0 {rx},0 L{WIDTH - rx},0 Q{WIDTH},0 {WIDTH},{rx} '
             f'L{WIDTH},{CARD_H} L0,{CARD_H} Z"/>')
    body = [f'<g fill="{c["bg"]}">{shape}</g>']
    body.append(k.text_svg(f'{c["n"]} — SERVICE', 64, 108, 12, c["kick"], "SemiBold", 0.14))
    body.append(k.text_svg(c["head"], 58, 210, 96, c["fg"], "SemiBold", -0.03))
    body.append(k.body_lines(64, 262, [440, 470, 410, 300], 22, 9, c["bar"]))
    body.append(k.button(64, 372, "Learn more", c["fg"], c["bg"]))
    body.append(k.image_tile(700, 64, 516, 516, c["tile"], c["sun"], 16, idn=f"c{i}"))
    if p > 0:
        body.append(f'<rect width="{WIDTH}" height="{CARD_H}" fill="{k.INK}" opacity="{DIM * p:.3f}"/>')
    clip = f'<clipPath id="card{i}">{shape}</clipPath>'
    return (f'<defs>{clip}</defs>'
            f'<g transform="translate({WIDTH / 2:.1f},{top:.2f}) scale({sc:.4f}) translate({-WIDTH / 2:.1f},0)">'
            f'<g clip-path="url(#card{i})">{"".join(body)}</g></g>')


def svg_at(t):
    out = [f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>']
    for i, (top, p) in enumerate(layout(t)):
        if top < HEIGHT:
            out.append(card(i, CARDS[i], top, p))
    out.append(k.site_header())        # fixed header paints on top
    return k.svg_doc("".join(out))
