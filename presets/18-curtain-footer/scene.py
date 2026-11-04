"""Preset 18 — Curtain footer reveal, as a video scene.

Mirrors snippets/footer-injection.html: the charcoal footer (300px) sits
fixed at the bottom of the viewport behind the page. The page scrolls up
and its bottom edge (24px rounded corners, soft shadow) lifts off the
footer like a curtain. While the footer is revealed its content rises
from +60px to 0 and fades from 0.35 to 1, driven by the same progress
the script uses:  p = clamp((viewportH - spacerTop) / footerH).

Beats (page scroll is simulated by translating the page group):
    0.00-0.40  rest near the end of the page, footer hidden
    0.40-3.70  scroll: last section rises, page bottom enters (~1.6s),
               lifts off the footer, content rises + fades in
    3.70-5.00  rest: footer fully revealed (final frame = resting state)
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 5.0
WIDTH, HEIGHT = k.W, k.H

# snippet defaults, copied verbatim
RADIUS = 24
PARALLAX = 60
FADE = 0.35

FH = 300                      # footer height (measured -> spacer height)
EXTRA = 260                   # page left below the fold at t=0
SCROLL = (0.40, 3.70)

FOOT_TOP = HEIGHT - FH        # fixed: bottom 0


def scroll(t):
    return (EXTRA + FH) * k.seg(t, *SCROLL, k.ease_in_out)


def page_bottom(t):
    """Viewport y of the page's bottom edge (= spacer top)."""
    return HEIGHT + EXTRA - scroll(t)


def progress(t):
    return k.clamp01((HEIGHT - page_bottom(t)) / FH)


def footer_state(t):
    p = progress(t)
    return (1 - p) * PARALLAX, FADE + (1 - FADE) * p


# ------------------------------------------------------------------ page
PB = HEIGHT + EXTRA           # page bottom in page coordinates (t=0)
LAST_TOP = PB - 560           # last section: 560px tall


def page_body():
    out = []
    # section above: three project tiles on a tile-toned band
    out.append(f'<rect x="0" y="0" width="{WIDTH}" height="{LAST_TOP}" fill="{k.TILE}"/>')
    for i in range(3):
        x = 64 + i * 392
        out.append(k.image_tile(x, 100, 368, 260, k.PAPER, k.ACCENT if i == 1 else None, 12, idn=f"p{i}"))
        out.append(k.bar(x, 380, 180, 9, k.TILE_DARK))
    # last section: closing call to action on paper
    y = LAST_TOP
    out.append(f'<rect x="0" y="{y}" width="{WIDTH}" height="{PB - y}" fill="{k.PAPER}"/>')
    out.append(k.text_svg("NEXT PROJECT", 64, y + 104, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("Let’s build", 60, y + 186, 72, k.INK, "SemiBold", -0.03))
    out.append(k.text_svg("something good.", 60, y + 266, 72, k.INK, "SemiBold", -0.03))
    out.append(k.body_lines(64, y + 316, [430, 380], 20, 9))
    out.append(k.button(64, y + 384, "Start a project"))
    out.append(k.image_tile(760, y + 80, 456, 400, k.TILE, None, 16, idn="last"))
    return "".join(out)


def page(t):
    s = scroll(t)
    b = PB
    r = RADIUS
    shape = (f'M0,-200 L{WIDTH},-200 L{WIDTH},{b - r} Q{WIDTH},{b} {WIDTH - r},{b} '
             f'L{r},{b} Q0,{b} 0,{b - r} Z')
    # box-shadow stand-in (cairosvg has no blur)
    # stacked soft rounded rects = blurred, inset shadow (like spread -18px)
    shadow = "".join(
        f'<rect x="{36 - i * 4}" y="{b - 60}" width="{WIDTH - 72 + i * 8}" height="{60 + 3 + i * 4}" '
        f'rx="{RADIUS + i * 3}" fill="#000" opacity="0.055"/>' for i in range(8))
    return (f'<g transform="translate(0,{-s:.2f})">{shadow}'
            f'<clipPath id="cf-page"><path d="{shape}"/></clipPath>'
            f'<g clip-path="url(#cf-page)">{page_body()}</g></g>')


# ------------------------------------------------------------------ footer
LINK = "#C9C3B8"


def footer_content():
    y0 = FOOT_TOP
    out = []
    # brand
    out.append(f'<rect x="64" y="{y0 + 58}" width="26" height="26" rx="7" fill="none" stroke="{k.PAPER}" stroke-width="2"/>')
    out.append(f'<line x1="70.5" y1="{y0 + 77}" x2="83.5" y2="{y0 + 64}" stroke="{k.ACCENT}" stroke-width="2.4" stroke-linecap="round"/>')
    out.append(k.text_svg("Studio", 102, y0 + 79, 22, k.PAPER, "SemiBold", -0.01))
    out.append(k.body_lines(64, y0 + 112, [250, 210], 18, 8, "#3A3833"))
    # newsletter line with the Heroicons arrow
    out.append(k.text_svg("Get the newsletter", 64, y0 + 196, 16, k.PAPER, "Medium"))
    out.append(f'<rect x="64" y="{y0 + 214}" width="300" height="1.5" fill="#5A5750"/>')
    out.append(k.arrow(340, y0 + 180, 24, k.ACCENT, 2.2))
    # three link columns
    cols = [("STUDIO", ["About", "Team", "Careers", "Journal"]),
            ("SERVICES", ["Strategy", "Design", "Build", "Launch"]),
            ("FOLLOW", ["Instagram", "LinkedIn", "Dribbble", "Email"])]
    for i, (head, links) in enumerate(cols):
        x = 560 + i * 230
        out.append(k.text_svg(head, x, y0 + 72, 11.5, k.MUTED, "SemiBold", 0.14))
        for j, l in enumerate(links):
            out.append(k.text_svg(l, x, y0 + 110 + j * 34, 16, LINK, "Medium"))
    out.append(f'<rect x="64" y="{y0 + 244}" width="{WIDTH - 128}" height="1" fill="#3A3833"/>')
    out.append(k.text_svg("© 2026 Studio", 64, y0 + 274, 12, k.MUTED, "Medium"))
    out.append(k.text_svg("Privacy · Terms", WIDTH - 64, y0 + 274, 12, k.MUTED, "Medium", anchor="end"))
    return "".join(out)


def footer(t):
    dy, op = footer_state(t)
    bg = f'<rect x="0" y="{FOOT_TOP}" width="{WIDTH}" height="{FH}" fill="{k.INK}"/>'
    return bg + f'<g transform="translate(0,{dy:.2f})" opacity="{op:.3f}">{footer_content()}</g>'


def svg_at(t):
    out = [f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.INK}"/>']
    out.append(footer(t))              # fixed, z-index under the page
    out.append(page(t))                # the curtain
    out.append(k.site_header())        # header paints on top
    return k.svg_doc("".join(out))
