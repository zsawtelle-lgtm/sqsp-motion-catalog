"""Preset 13 — Horizontal scroll gallery, as a video scene.

Mirrors snippets/footer-injection.html: a carousel List Section (ink) under a
fixed 76px header. Its content-wrapper is sticky at top = header height; the
script's spacer adds DIST px of scroll room, DIST = trackW - viewW, so 1px of
page scroll moves the track 1px left:
    p = clamp((stickyTop + cwH - spacer.top) / DIST),  x = -DIST * p
The accent hairline under the cards fills with p. After the travel the
section unpins and scrolls away with the track at rest (-DIST).

Track geometry = the List Section defaults the snippet is tested on: holder
64..1216 (1152 wide), 3 columns, 24px gap -> 368px cards, 5 cards ->
trackW 1936, DIST 784.

Beats (page scroll is simulated by moving the page):
    0.00-0.40  rest on the intro section
    0.40-5.00  one continuous scroll (ease in-out):
               ~1.6s  work section rises to the header and pins
               ~1.6-3.6s pinned: cards slide left, hairline fills
               ~3.6-5.0s unpins, next section comes up
    5.00-5.60  rest (final frame = resting state)
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 5.6
WIDTH, HEIGHT = k.W, k.H

TOP = 76                        # headerOffset 'auto' -> fixed header height
INTRO_H = 430                   # intro section below the header
CW_H = HEIGHT - TOP             # 644: the work section's content-wrapper
HOLD_X, HOLD_W = 64, 1152       # .user-items-list-carousel__slideshow-holder
COLS, GAP = 3, 24
CARD_W = (HOLD_W - GAP * (COLS - 1)) / COLS     # 368
N = 5
TRACK_W = N * CARD_W + (N - 1) * GAP            # 1936
DIST = TRACK_W - HOLD_W                         # 784 = spacer height
AFTER = 380                     # scroll past the unpin
SCROLL = (0.40, 5.00)

CARD_Y = 190                    # card tiles, relative to the content-wrapper
TILE_H = 276                    # 4:3
BAR_Y = CARD_Y + TILE_H + 66 + 32               # holder bottom + barGap 32
BAR_BG = "#4A4843"
CARD_MUTED = "#8C877E"

WORKS = [
    ("Harbor House", "2025", "#3A3833", k.ACCENT),
    ("Mill Lofts", "2024", "#E6E0D4", k.ACCENT),
    ("Ridge Studio", "2024", "#5A554D", k.PAPER),
    ("Orchard Hall", "2023", "#E9A285", k.PAPER),
    ("North Pier", "2022", "#CFC7B8", k.INK),
]


def scroll(t):
    return (INTRO_H + DIST + AFTER) * k.seg(t, *SCROLL, k.ease_in_out)


def state(t):
    """(content-wrapper viewport top, progress p, track x) — the snippet's math."""
    s = scroll(t)
    sec_top = TOP + INTRO_H - s                  # section top in the viewport
    spacer_top = sec_top + CW_H                  # spacer follows the content-wrapper in flow
    p = k.clamp01((TOP + CW_H - spacer_top) / DIST)
    cw_top = min(max(TOP, sec_top), spacer_top + DIST - CW_H)   # sticky inside the section
    return cw_top, p, -DIST * p, sec_top


def intro(y):
    out = [f'<rect x="0" y="{y}" width="{WIDTH}" height="{INTRO_H}" fill="{k.PAPER}"/>']
    out.append(k.text_svg("ARCHITECTURE & INTERIORS", 64, y + 86, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("Spaces built", 60, y + 166, 64, k.INK, "SemiBold", -0.025))
    out.append(k.text_svg("to be lived in.", 60, y + 236, 64, k.INK, "SemiBold", -0.025))
    out.append(k.body_lines(700, y + 120, [430, 455, 400, 300], 20, 9))
    out.append(k.button(700, y + 220))
    return "".join(out)


def card(i, x):
    title, year, tone, sun = WORKS[i]
    out = [k.image_tile(x, CARD_Y, CARD_W, TILE_H, tone, sun, 10, idn=f"w{i}")]
    out.append(k.text_svg(title, x, CARD_Y + TILE_H + 38, 22, k.PAPER, "SemiBold", -0.01))
    out.append(k.text_svg(year, x + CARD_W, CARD_Y + TILE_H + 38, 15, CARD_MUTED, "Medium", 0.02, anchor="end"))
    out.append(k.text_svg(f"0{i + 1}", x, CARD_Y + TILE_H + 64, 12, CARD_MUTED, "SemiBold", 0.14))
    return "".join(out)


def work(cw_top, p, x, sec_top):
    sec_h = CW_H + DIST
    out = [f'<rect x="0" y="{sec_top:.2f}" width="{WIDTH}" height="{sec_h}" fill="{k.INK}"/>']
    inner = [k.text_svg("SELECTED WORK", 64, 72, 12, k.ACCENT, "SemiBold", 0.14),
             k.text_svg("Selected work", 60, 136, 52, k.PAPER, "SemiBold", -0.025),
             k.text_svg(f"{N} projects", 1216, 136, 15, CARD_MUTED, "Medium", 0.02, anchor="end")]
    cards = "".join(card(i, HOLD_X + i * (CARD_W + GAP)) for i in range(N))
    clip = (f'<clipPath id="hold"><rect x="{HOLD_X}" y="{CARD_Y - 4}" width="{HOLD_W}" '
            f'height="{TILE_H + 90}"/></clipPath>')
    inner.append(f'<defs>{clip}</defs><g clip-path="url(#hold)"><g transform="translate({x:.2f},0)">{cards}</g></g>')
    inner.append(f'<rect x="{HOLD_X}" y="{BAR_Y}" width="{HOLD_W}" height="2" fill="{BAR_BG}"/>')
    if p > 0:
        inner.append(f'<rect x="{HOLD_X}" y="{BAR_Y}" width="{HOLD_W * p:.2f}" height="2" fill="{k.ACCENT}"/>')
    out.append(f'<g transform="translate(0,{cw_top:.2f})">{"".join(inner)}</g>')
    return "".join(out)


def after(y):
    out = [f'<rect x="0" y="{y:.2f}" width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>']
    out.append(k.text_svg("STUDIO", 64, y + 92, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("Small team, long view.", 60, y + 160, 52, k.INK, "SemiBold", -0.025))
    out.append(k.body_lines(64, y + 206, [470, 500, 420, 280], 20, 9))
    out.append(k.image_tile(700, y + 60, 516, 300, k.TILE, k.ACCENT, 10, idn="after"))
    return "".join(out)


def svg_at(t):
    cw_top, p, x, sec_top = state(t)
    out = [f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>']
    if sec_top > TOP - INTRO_H:
        out.append(intro(sec_top - INTRO_H))
    out.append(work(cw_top, p, x, sec_top))
    nxt = sec_top + CW_H + DIST
    if nxt < HEIGHT:
        out.append(after(nxt))
    out.append(k.site_header(active="Work"))     # fixed header paints on top
    return k.svg_doc("".join(out))
