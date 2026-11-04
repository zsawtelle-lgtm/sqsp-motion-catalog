"""Preset 06 — Image Scale-Settle, as a video scene.

Mirrors snippets/footer-injection.html beat-for-beat:
    0.00s    page loads; every armed image sits at scale 1.15, dimmed
    0.15s    hero background enters view -> settles over 1.4s, expo-out
             (CSS cubic-bezier(.16,1,.3,1)) to scale 1 / full color
    2.05s    visitor scrolls down (0.9s) to the two-image row
    2.85s    row enters view: image A settles, image B follows +0.12s
             (snippet stagger for images entering together)
    4.37s+   everything at rest; frames never changed size
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 5.0
WIDTH, HEIGHT = k.W, k.H

# ---- snippet values, copied verbatim ---------------------------------------
FROM = 1.15          # C.from
DIM = 0.82           # C.dim  (brightness)
SAT = 0.70           # C.saturate
DUR = 1.4            # C.duration
STAGGER = 0.12       # C.stagger

HERO_AT = 0.15                 # two rAFs + first paint
SCROLL_AT, SCROLL_DUR = 2.05, 0.9
SCROLL_PX = 644                # hero bottom meets the header
ROW_AT = 2.85                  # row crosses the 15% threshold mid-scroll
ROW_B_AT = ROW_AT + STAGGER
REST_AT = ROW_B_AT + DUR

HEADER_H = 76
HERO_Y, HERO_H = HEADER_H, HEIGHT - HEADER_H          # full-bleed hero
ROW_TOP = HERO_Y + HERO_H                              # next section (page y)
IMG_A = (64, ROW_TOP + 200, 560, 390)                  # x, y, w, h (page coords)
IMG_B = (656, ROW_TOP + 200, 560, 390)


def settle(t, start):
    return k.seg(t, start, start + DUR, k.ease_out_expo)


def scroll_y(t):
    return SCROLL_PX * k.seg(t, SCROLL_AT, SCROLL_AT + SCROLL_DUR, k.ease_in_out)


# ---- a richer placeholder photo: layered landscape + building so scale reads
def photo(w, h, scheme, house_x=0.18):
    sky, far, mid, near, sun = scheme
    out = [f'<rect width="{w}" height="{h}" fill="{sky}"/>',
           f'<circle cx="{w * 0.72:.1f}" cy="{h * 0.30:.1f}" r="{min(w, h) * 0.085:.1f}" fill="{sun}"/>',
           f'<path d="M0,{h * .62:.1f} L{w * .14:.1f},{h * .44:.1f} L{w * .30:.1f},{h * .58:.1f} L{w * .48:.1f},{h * .38:.1f} '
           f'L{w * .66:.1f},{h * .56:.1f} L{w * .84:.1f},{h * .42:.1f} L{w},{h * .55:.1f} L{w},{h} L0,{h} Z" fill="{far}"/>',
           f'<path d="M0,{h * .74:.1f} C{w * .25:.1f},{h * .64:.1f} {w * .45:.1f},{h * .80:.1f} {w * .7:.1f},{h * .70:.1f} '
           f'S{w},{h * .68:.1f} {w},{h * .68:.1f} L{w},{h} L0,{h} Z" fill="{mid}"/>']
    # a small pavilion (architecture cue) + window grid
    bx, by, bw, bh = w * house_x, h * 0.56, w * 0.30, h * 0.24
    out.append(f'<path d="M{bx - w * .02:.1f},{by:.1f} L{bx + bw + w * .02:.1f},{by:.1f} L{bx + bw:.1f},{by + h * .03:.1f} L{bx:.1f},{by + h * .03:.1f} Z" fill="{k.INK}"/>')
    out.append(f'<rect x="{bx:.1f}" y="{by + h * .03:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{k.PAPER}"/>')
    for i in range(5):
        out.append(f'<rect x="{bx + bw * (0.06 + i * 0.19):.1f}" y="{by + h * .07:.1f}" width="{bw * 0.13:.1f}" '
                   f'height="{bh * 0.62:.1f}" fill="{far}" opacity="0.85"/>')
    # trees
    trees = ((0.58, 1.0), (0.64, 0.75), (0.88, 1.1)) if house_x < 0.4 else ((0.86, 1.0), (0.91, 0.75), (0.96, 1.1))
    for tx, s in trees:
        x0, y0 = w * tx, h * 0.80
        out.append(f'<rect x="{x0 - 2:.1f}" y="{y0 - h * .05 * s:.1f}" width="4" height="{h * .05 * s:.1f}" fill="{k.INK}"/>')
        out.append(f'<ellipse cx="{x0:.1f}" cy="{y0 - h * .1 * s:.1f}" rx="{w * .028 * s:.1f}" ry="{h * .075 * s:.1f}" fill="{near}"/>')
    out.append(f'<path d="M0,{h * .86:.1f} C{w * .3:.1f},{h * .80:.1f} {w * .6:.1f},{h * .92:.1f} {w},{h * .84:.1f} L{w},{h} L0,{h} Z" fill="{near}"/>')
    return "".join(out)


HERO_SCHEME = ("#E9D9C4", "#B9A68C", "#8E8A6E", "#4E5B47", k.ACCENT)
A_SCHEME = ("#D8E0DD", "#A9B7B1", "#7F948B", "#3F5148", k.ACCENT)
B_SCHEME = ("#EDE1CF", "#C9AE8E", "#A2805E", "#5B4634", "#F2C14E")


def framed_photo(idn, x, y, w, h, scheme, p, house_x=0.18):
    """Fixed frame (clip) at x,y,w,h; the photo inside scales FROM -> 1."""
    s = FROM + (1 - FROM) * p
    cx, cy = x + w / 2, y + h / 2
    dim = (1 - DIM) * (1 - p)            # brightness -> black overlay
    gray = (1 - SAT) * 0.45 * (1 - p)    # desaturate -> neutral wash
    return (f'<defs><clipPath id="c-{idn}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs>'
            f'<g clip-path="url(#c-{idn})">'
            f'<g transform="translate({cx:.2f},{cy:.2f}) scale({s:.4f}) translate({-w / 2:.2f},{-h / 2:.2f})">{photo(w, h, scheme, house_x)}</g>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#9A958C" opacity="{gray:.3f}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" opacity="{dim:.3f}"/></g>')


def page(t):
    out = [f'<rect x="0" y="0" width="{WIDTH}" height="{ROW_TOP + 900}" fill="{k.PAPER}"/>']
    # hero: section background image + overlaid headline
    out.append(framed_photo("hero", 0, HERO_Y, WIDTH, HERO_H, HERO_SCHEME, settle(t, HERO_AT), 0.50))
    # flat text scrim (a gradient dithers badly in the GIF)
    out.append(f'<rect x="40" y="{HERO_Y + 296}" width="560" height="200" rx="4" fill="{k.INK}" opacity="0.28"/>')
    out.append(k.text_svg("ARCHITECTURE & INTERIORS", 64, HERO_Y + 330, 12, k.PAPER, "SemiBold", 0.14))
    out.append(k.text_svg("Spaces built", 60, HERO_Y + 404, 64, k.PAPER, "SemiBold", -0.025))
    out.append(k.text_svg("to be lived in.", 60, HERO_Y + 474, 64, k.PAPER, "SemiBold", -0.025))
    # second section: heading + two-image row
    out.append(k.text_svg("SELECTED WORK", 64, ROW_TOP + 96, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("Recent projects", 60, ROW_TOP + 156, 44, k.INK, "SemiBold", -0.02))
    out.append(k.body_lines(820, ROW_TOP + 118, [396, 360], 20, 9))
    out.append(framed_photo("a", *IMG_A, A_SCHEME, settle(t, ROW_AT)))
    out.append(framed_photo("b", *IMG_B, B_SCHEME, settle(t, ROW_B_AT)))
    out.append(k.text_svg("Hillside House", 64, IMG_A[1] + IMG_A[3] + 36, 18, k.INK, "Medium"))
    out.append(k.text_svg("Orchard Pavilion", 656, IMG_B[1] + IMG_B[3] + 36, 18, k.INK, "Medium"))
    return "".join(out)


def svg_at(t):
    body = f'<g transform="translate(0,{-scroll_y(t):.2f})">{page(t)}</g>' + k.site_header()
    return k.svg_doc(body)
