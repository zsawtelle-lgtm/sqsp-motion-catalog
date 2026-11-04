"""Shared helpers for every preset's video scene.

A scene file imports this module, defines DURATION / WIDTH / HEIGHT and
svg_at(t), and is rendered with shared/render.py (the website-animations
skill renderer: Python scene -> SVG per frame -> cairosvg -> ffmpeg).

What lives here:
    - timing helpers (seg, eases) — mirror the CSS cubic-beziers
    - the catalog's neutral placeholder palette (matches the CSS vars)
    - outlined text (fontTools) so glyphs can be traced and measured
    - a mock Squarespace 7.1 page so every preview shows the effect in context
    - the Heroicons v2 arrow (same set as Will Myers' toolkit), drawn heavier

Gotcha reminder (from references/video-export.md): cairosvg ignores
pathLength. Use real lengths — text_paths() returns them per glyph.
"""
import functools
import math

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# ------------------------------------------------------------------ palette
# Keep in sync with the CSS custom properties in every snippet.
PAPER = "#F4F1EA"    # --swtl-paper   (off-white background)
INK = "#1F1E1C"      # --swtl-ink     (charcoal text / lines)
ACCENT = "#D4552B"   # --swtl-accent  (single brand accent)
MUTED = "#8C877E"    # derived: ink at ~50% on paper (body copy, rules)
LINE = "#D9D3C7"     # derived: hairlines, skeleton bars
TILE = "#E6E0D4"     # derived: image placeholders
TILE_DARK = "#CFC7B8"

FONT_DIR = "/usr/share/fonts/opentype/inter/"
FONT_FAMILY = "Inter, sans-serif"

W, H = 1280, 720     # every preview: 1280x720, even dims for yuv420p

# ------------------------------------------------------------------ timing

def clamp01(x):
    return max(0.0, min(1.0, x))


def lerp(a, b, p):
    return a + (b - a) * p


def ease_in_out(p):            # ~ cubic-bezier(.65,0,.35,1)
    return 0.5 - 0.5 * math.cos(math.pi * p)


def ease_out(p):               # ~ cubic-bezier(.22,1,.36,1) / power3.out
    return 1 - (1 - p) ** 3


def ease_out_expo(p):          # ~ expo.out — fast start, long settle
    return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)


def ease_in(p):
    return p ** 3


def ease_sweep(p):             # ~ cubic-bezier(.7,0,.2,1) — easeInOutCubic
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_back(p, s=1.56):      # ~ cubic-bezier(.34,1.56,.64,1) overshoot
    c3 = s + 1
    return 1 + c3 * (p - 1) ** 3 + s * (p - 1) ** 2


def seg(t, start, end, ease=ease_in_out):
    """0..1 progress of one beat, eased."""
    if end <= start:
        return 1.0 if t >= end else 0.0
    return ease(clamp01((t - start) / (end - start)))


def pulse(t, start, period=2.4, lo=0.4):
    """Hold-state opacity pulse (CSS: 0%,100% {1} 50% {lo})."""
    if t < start:
        return 1.0
    return lo + (1 - lo) * (0.5 + 0.5 * math.cos(2 * math.pi * (t - start) / period))


# ------------------------------------------------------------------ outlined text

@functools.lru_cache(maxsize=8)
def _font(weight):
    return TTFont(f"{FONT_DIR}Inter-{weight}.otf")


@functools.lru_cache(maxsize=256)
def text_paths(text, size, weight="SemiBold", tracking=0.0):
    """Outline `text` with Inter. Returns (glyphs, width) where glyphs is a
    list of (char, d, x_offset, length). Coordinates: baseline at y=0,
    x from 0. Path data already scaled to `size` px and y-flipped.
    """
    from svgpathtools import parse_path

    font = _font(weight)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    k = size / upm
    hmtx = font["hmtx"]
    out, x = [], 0.0
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            continue
        adv = hmtx[name][0] * k
        if ch != " ":
            pen = SVGPathPen(gs)
            gs[name].draw(TransformPen(pen, (k, 0, 0, -k, x, 0)))
            d = pen.getCommands()
            if d:
                try:
                    length = parse_path(d).length()
                except Exception:
                    length = 0.0
                out.append((ch, d, x, length))
        x += adv + tracking * size
    return tuple(out), x - tracking * size


def text_svg(text, x, y, size, fill=INK, weight="SemiBold", tracking=0.0, anchor="start", extra=""):
    """Outlined text as one <path> group (font-independent rendering)."""
    glyphs, width = text_paths(text, size, weight, tracking)
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    d = " ".join(g[1] for g in glyphs)
    return f'<path transform="translate({x:.2f},{y:.2f})" d="{d}" fill="{fill}" {extra}/>'


def text_width(text, size, weight="SemiBold", tracking=0.0):
    return text_paths(text, size, weight, tracking)[1]


# ------------------------------------------------------------------ icons

# Heroicons v2 outline "arrow-right" (MIT) — the set Will Myers' toolkit
# ships. Drawn at stroke 2 instead of the default 1.5 (Zac's standard).
ARROW_D = "M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"


def arrow(x, y, size, color=INK, stroke=2.0):
    s = size / 24
    return (f'<path transform="translate({x:.2f},{y:.2f}) scale({s:.4f})" d="{ARROW_D}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


# ------------------------------------------------------------------ mock page

def image_tile(x, y, w, h, tone=TILE, accent=None, rx=0, idn="t"):
    """Placeholder image: flat tile with a soft 'mountain + sun' glyph so it
    reads as a photo without being one."""
    cx, cy = x + w * 0.5, y + h * 0.5
    m = min(w, h)
    sun = f'<circle cx="{x + w * 0.70:.1f}" cy="{y + h * 0.34:.1f}" r="{m * 0.075:.1f}" fill="{accent or TILE_DARK}" opacity="0.9"/>'
    hills = (f'<path d="M{x:.1f},{y + h:.1f} L{x + w * 0.32:.1f},{y + h * 0.58:.1f} '
             f'L{x + w * 0.52:.1f},{y + h * 0.78:.1f} L{x + w * 0.68:.1f},{y + h * 0.62:.1f} '
             f'L{x + w:.1f},{y + h * 0.9:.1f} L{x + w:.1f},{y + h:.1f} Z" fill="{TILE_DARK}" opacity="0.75"/>')
    clip = f'<clipPath id="clip-{idn}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}"/></clipPath>'
    return (f'<defs>{clip}</defs><g clip-path="url(#clip-{idn})">'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{tone}"/>{sun}{hills}</g>')


def bar(x, y, w, h=8, fill=LINE, rx=4):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"/>'


def body_lines(x, y, widths, gap=18, h=8, fill=LINE):
    return "".join(bar(x, y + i * gap, w, h, fill) for i, w in enumerate(widths))


def button(x, y, label="Get in touch", fill=INK, color=PAPER, size=15, arrow_dx=0.0):
    tw = text_width(label, size, "Medium")
    w = tw + 34 + 26 + 8
    h = 46
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="23" fill="{fill}"/>'
            + text_svg(label, x + 24, y + 28.5, size, color, "Medium")
            + arrow(x + 24 + tw + 10 + arrow_dx, y + 13, 20, color, 2.2))


def site_header(y=0, logo="Studio", active=None):
    """Squarespace 7.1-style header: wordmark left, nav right, hairline."""
    out = [f'<rect x="0" y="{y}" width="{W}" height="76" fill="{PAPER}"/>']
    out.append(f'<rect x="64" y="{y + 26}" width="24" height="24" rx="6" fill="none" stroke="{INK}" stroke-width="2"/>')
    out.append(f'<line x1="70" y1="{y + 44}" x2="82" y2="{y + 32}" stroke="{ACCENT}" stroke-width="2.4" stroke-linecap="round"/>')
    out.append(text_svg(logo, 98, y + 45, 19, INK, "SemiBold", -0.01))
    nav = ["Work", "Services", "About", "Journal"]
    x = 760
    for i, n in enumerate(nav):
        out.append(text_svg(n, x, y + 44, 14, INK if n != active else ACCENT, "Medium"))
        x += text_width(n, 14, "Medium") + 34
    out.append(f'<rect x="{x + 4:.1f}" y="{y + 22}" width="104" height="34" rx="17" fill="{INK}"/>')
    out.append(text_svg("Contact", x + 26, y + 44, 13.5, PAPER, "Medium"))
    out.append(f'<rect x="0" y="{y + 75}" width="{W}" height="1" fill="{LINE}"/>')
    return "".join(out)


def hero(y=76, headline=("Spaces built", "to be lived in."), kicker="ARCHITECTURE & INTERIORS"):
    """Two-column Fluid Engine hero: text left, image right."""
    out = [text_svg(kicker, 64, y + 92, 12, ACCENT, "SemiBold", 0.14)]
    for i, line in enumerate(headline):
        out.append(text_svg(line, 60, y + 166 + i * 70, 64, INK, "SemiBold", -0.025))
    out.append(body_lines(64, y + 300, [430, 455, 300], 20, 9))
    out.append(button(64, y + 378))
    out.append(image_tile(700, y + 50, 516, 520, idn="hero"))
    return "".join(out)


def page(headline=("Spaces built", "to be lived in."), active=None):
    """Full mock homepage (header + hero) on paper."""
    return f'<rect width="{W}" height="{H}" fill="{PAPER}"/>' + site_header(active=active) + hero(headline=headline)


def svg_doc(body, w=W, h=H, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<defs>{defs}</defs>{body}</svg>')
