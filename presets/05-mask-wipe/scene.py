"""Preset 05 — Mask / clip wipe reveal, as a video scene.

Mirrors snippets/footer-injection.html beat-for-beat (timing.py holds the
numbers both use). The mock page scrolls from a hero down into an editorial
section (big image left, text right, second image lower right). Each image:
    +0.00  accent curtain grows left -> right across the block   (0.55s)
    +0.62  curtain exits to the right, image uncovered behind it (0.68s)
    +0.62  image settles scale 1.08 -> 1                         (1.20s)
Image 2 enters the viewport later in the scroll -> starts STAGGER+ after 1.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402
import timing as tm  # noqa: E402

DURATION = 5.2
WIDTH, HEIGHT = k.W, k.H

# ---- scroll: page group translates up by SCROLL px ---------------------
SCROLL_START, SCROLL_END = 0.25, 1.35
SCROLL = 640

# ---- editorial section geometry (page coordinates) ---------------------
SEC_Y = 720 + 40                      # section starts below the hero
IMG1 = (64, SEC_Y + 70, 610, 470)     # x, y, w, h  (big image left)
IMG2 = (782, SEC_Y + 318, 434, 268)   # second image lower right
TEXT_X, TEXT_Y = 742, SEC_Y + 96

# trigger times (when each block crosses the snippet's threshold line)
T1 = 0.95
T2 = T1 + tm.STAGGER + 0.42           # enters later in the scroll
REST_AT = T2 + tm.BLOCK_TOTAL         # every block at rest


def scroll_y(t):
    return SCROLL * k.seg(t, SCROLL_START, SCROLL_END, k.ease_in_out)


def wipe_state(t, start):
    """(curtain_x0, curtain_x1, image_reveal, scale) in 0..1 of block width."""
    lt = t - start
    if lt <= 0:
        return 0.0, 0.0, 0.0, tm.SCALE_FROM
    grow = k.seg(lt, 0, tm.CURTAIN_IN, k.ease_in_out)
    leave = k.seg(lt, tm.UNCOVER_AT, tm.CURTAIN_TOTAL, k.ease_in_out)
    settle = k.seg(lt, tm.UNCOVER_AT, tm.BLOCK_TOTAL, k.ease_out)
    scale = tm.SCALE_FROM + (1 - tm.SCALE_FROM) * settle
    if lt < tm.UNCOVER_AT:
        return 0.0, grow, 0.0, scale
    return leave, 1.0, leave, scale


def photo(w, h, variant, idn):
    """Editorial placeholder photo in LOCAL coords (0,0)-(w,h)."""
    if variant == 1:
        sky, mid, ground = "#D9CDB8", "#B9A88E", "#7E6E58"
    else:
        sky, mid, ground = "#C9D2C6", "#93A493", "#566A5B"
    return (f'<rect width="{w}" height="{h}" fill="{sky}"/>'
            f'<circle cx="{w * 0.72:.1f}" cy="{h * 0.30:.1f}" r="{min(w, h) * 0.085:.1f}" fill="{k.PAPER}" opacity="0.9"/>'
            f'<path d="M0,{h * 0.72:.1f} L{w * 0.28:.1f},{h * 0.46:.1f} L{w * 0.47:.1f},{h * 0.64:.1f} '
            f'L{w * 0.66:.1f},{h * 0.50:.1f} L{w},{h * 0.70:.1f} L{w},{h} L0,{h} Z" fill="{mid}"/>'
            f'<path d="M0,{h * 0.86:.1f} L{w * 0.4:.1f},{h * 0.74:.1f} L{w},{h * 0.88:.1f} L{w},{h} L0,{h} Z" fill="{ground}"/>')


def wiped_image(t, box, start, variant, idn):
    x, y, w, h = box
    c0, c1, rev, s = wipe_state(t, start)
    # all clipping happens in the block's LOCAL coordinates (inner group)
    cx, cy = w / 2, h / 2
    img = (f'<g transform="translate({cx:.2f},{cy:.2f}) scale({s:.4f}) translate({-cx:.2f},{-cy:.2f})">'
           f'{photo(w, h, variant, idn)}</g>')
    out = [f'<g transform="translate({x},{y})">',
           f'<defs><clipPath id="mw-box-{idn}"><rect width="{w}" height="{h}"/></clipPath>'
           f'<clipPath id="mw-img-{idn}"><rect width="{w * rev:.2f}" height="{h}"/></clipPath></defs>']
    if rev > 0:
        out.append(f'<g clip-path="url(#mw-box-{idn})"><g clip-path="url(#mw-img-{idn})">{img}</g></g>')
    if c1 - c0 > 0.0005:
        out.append(f'<rect x="{w * c0:.2f}" width="{w * (c1 - c0):.2f}" height="{h}" fill="{k.ACCENT}"/>')
    out.append('</g>')
    return "".join(out)


def editorial(t):
    out = [f'<rect x="64" y="{SEC_Y}" width="{k.W - 128}" height="1" fill="{k.LINE}"/>']
    out.append(wiped_image(t, IMG1, T1, 1, "a"))
    out.append(k.text_svg("FIELD NOTES · 04", TEXT_X, TEXT_Y, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("Light, timber", TEXT_X - 3, TEXT_Y + 60, 46, k.INK, "SemiBold", -0.025))
    out.append(k.text_svg("and long rooms.", TEXT_X - 3, TEXT_Y + 112, 46, k.INK, "SemiBold", -0.025))
    out.append(k.body_lines(TEXT_X, TEXT_Y + 148, [400, 380, 250], 20, 8))
    out.append(wiped_image(t, IMG2, T2, 2, "b"))
    return "".join(out)


HEADER = k.site_header()
HERO = k.hero()


def svg_at(t):
    y = scroll_y(t)
    page = (f'<g transform="translate(0,{-y:.2f})">'
            f'<rect width="{WIDTH}" height="{HEIGHT + SCROLL + 200}" fill="{k.PAPER}"/>'
            f'{HERO}{editorial(t)}</g>')
    return k.svg_doc(page + HEADER)   # sticky header stays on top
