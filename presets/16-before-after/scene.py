"""Preset 16 — Before / after slider, as a video scene.

Mirrors snippets/footer-injection.html (timing.py holds the numbers both
use). The mock page scrolls from a hero into an "Our work" section with one
comparison block on the right:
    scroll in -> intro hint 50 -> 35 -> 50 (once, as the block is on screen)
    a cursor arrives, presses the handle, drags right to 80%, back to 50%,
    releases and leaves. Last frame = resting state (divider at 50%).
Before (left of the divider) = muted gray room with clutter; after (right
of the divider) = clean styled room. Same geometry as the snippet: the
after layer is clipped with inset(0 0 0 pos%).
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402
import timing as tm  # noqa: E402

DURATION = 5.6
WIDTH, HEIGHT = k.W, k.H

# ---- scroll ------------------------------------------------------------
SCROLL_START, SCROLL_END = 0.15, 1.05
SCROLL = 640

# ---- section geometry (page coordinates) -------------------------------
SEC_Y = 720 + 40
CMP = (560, SEC_Y + 60, 656, 440)      # x, y, w, h of the before/after block
TEXT_X, TEXT_Y = 64, SEC_Y + 110

# ---- beats -------------------------------------------------------------
T_HINT = 1.15                          # block crosses the 50% threshold
CUR_IN, CUR_AT = 2.70, 3.15            # cursor glides to the handle
PRESS = 3.22
DRAG1 = (3.25, 3.95)                   # 50 -> 80
DRAG_TO = 80
DRAG2 = (4.05, 4.75)                   # 80 -> 50
RELEASE = 4.80
CUR_OUT = (4.85, 5.25)                 # cursor leaves
REST_AT = CUR_OUT[1]

BEFORE_BG = "#A6A29B"                  # muted gray wall
BEFORE_FLOOR = "#8A867F"
AFTER_WALL = "#E2D2B8"                 # warm sand wall
AFTER_FLOOR = "#B88C60"
SOFA = "#3F4C45"


def scroll_y(t):
    return SCROLL * k.seg(t, SCROLL_START, SCROLL_END, k.ease_in_out)


def pos(t):
    """Divider position in % (the snippet's --swtl-ba-pos)."""
    s, to = tm.START, tm.START + tm.HINT_DX
    lt = t - T_HINT
    if 0 <= lt < tm.HINT_OUT:
        return s + (to - s) * k.ease_in_out(lt / tm.HINT_OUT)
    if tm.HINT_OUT <= lt < tm.HINT_OUT + tm.HINT_HOLD:
        return to
    if tm.HINT_OUT + tm.HINT_HOLD <= lt < tm.HINT_TOTAL:
        return to + (s - to) * k.ease_in_out((lt - tm.HINT_OUT - tm.HINT_HOLD) / tm.HINT_BACK)
    if DRAG1[0] <= t < DRAG2[0]:
        return s + (DRAG_TO - s) * k.seg(t, *DRAG1, k.ease_in_out)
    if DRAG2[0] <= t < DRAG2[1]:
        return DRAG_TO + (s - DRAG_TO) * k.seg(t, *DRAG2, k.ease_in_out)
    return s


# ---- the two "photos", in LOCAL coords (0,0)-(w,h) ----------------------

def before_room(w, h):
    fy = h * 0.70
    o = [f'<rect width="{w}" height="{h}" fill="{BEFORE_BG}"/>',
         f'<rect y="{fy:.1f}" width="{w}" height="{h - fy:.1f}" fill="{BEFORE_FLOOR}"/>',
         # water stains + a crooked frame + loose wire
         f'<ellipse cx="{w * 0.18:.1f}" cy="{h * 0.40:.1f}" rx="{w * 0.07:.1f}" ry="{h * 0.06:.1f}" fill="#99958E"/>',
         f'<ellipse cx="{w * 0.83:.1f}" cy="{h * 0.36:.1f}" rx="{w * 0.05:.1f}" ry="{h * 0.08:.1f}" fill="#9B978F"/>',
         f'<g transform="rotate(-9 {w * 0.47:.1f} {h * 0.40:.1f})"><rect x="{w * 0.39:.1f}" y="{h * 0.31:.1f}" '
         f'width="{w * 0.16:.1f}" height="{h * 0.17:.1f}" fill="none" stroke="#6E6A63" stroke-width="5"/></g>',
         f'<path d="M{w * 0.66:.1f},0 C{w * 0.64:.1f},{h * 0.2:.1f} {w * 0.72:.1f},{h * 0.3:.1f} {w * 0.68:.1f},{h * 0.46:.1f}" '
         f'fill="none" stroke="#5F5B55" stroke-width="3"/>']
    # stacked boxes, tilted crates, scattered junk on the floor
    boxes = [(0.06, 0.52, 0.16, 0.20, -4, "#7C786F"), (0.09, 0.40, 0.11, 0.13, 6, "#B7B2A8"),
             (0.27, 0.58, 0.13, 0.14, 12, "#6F6B64"), (0.55, 0.60, 0.19, 0.12, -7, "#BCB7AE"),
             (0.74, 0.50, 0.12, 0.22, 3, "#77736C"), (0.86, 0.64, 0.10, 0.10, -15, "#B0ABA2"),
             (0.40, 0.76, 0.09, 0.07, 20, "#6A665F"), (0.64, 0.80, 0.07, 0.06, -25, "#C2BDB4"),
             (0.15, 0.82, 0.08, 0.05, 8, "#75716A")]
    for x, y, bw, bh, rot, c in boxes:
        cx, cy = w * (x + bw / 2), h * (y + bh / 2)
        o.append(f'<rect x="{w * x:.1f}" y="{h * y:.1f}" width="{w * bw:.1f}" height="{h * bh:.1f}" fill="{c}" '
                 f'transform="rotate({rot} {cx:.1f} {cy:.1f})"/>')
    o.append(f'<path d="M{w * 0.30:.1f},{h * 0.94:.1f} q{w * 0.08:.1f},-{h * 0.05:.1f} {w * 0.16:.1f},0 '
             f't{w * 0.16:.1f},0" fill="none" stroke="#5F5B55" stroke-width="3"/>')
    return "".join(o)


def after_room(w, h):
    fy = h * 0.72
    sx, sy, sw, sh = w * 0.50, h * 0.54, w * 0.34, h * 0.20
    o = [f'<rect width="{w}" height="{h}" fill="{AFTER_WALL}"/>',
         f'<rect y="{fy:.1f}" width="{w}" height="{h - fy:.1f}" fill="{AFTER_FLOOR}"/>',
         f'<rect y="{fy - 6:.1f}" width="{w}" height="6" fill="{k.PAPER}"/>',
         # framed art (accent stripe) over the sofa
         f'<rect x="{w * 0.56:.1f}" y="{h * 0.26:.1f}" width="{w * 0.22:.1f}" height="{h * 0.19:.1f}" fill="{k.PAPER}" '
         f'stroke="{k.INK}" stroke-width="4"/>',
         f'<rect x="{w * 0.59:.1f}" y="{h * 0.34:.1f}" width="{w * 0.16:.1f}" height="{h * 0.05:.1f}" fill="{k.ACCENT}"/>',
         # sofa
         f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" rx="14" fill="{SOFA}"/>',
         f'<rect x="{sx - 14:.1f}" y="{sy + sh * 0.35:.1f}" width="28" height="{sh * 0.65:.1f}" rx="10" fill="#35413A"/>',
         f'<rect x="{sx + sw - 14:.1f}" y="{sy + sh * 0.35:.1f}" width="28" height="{sh * 0.65:.1f}" rx="10" fill="#35413A"/>',
         f'<rect x="{sx + 24:.1f}" y="{sy - 14:.1f}" width="{sw * 0.22:.1f}" height="{sh * 0.55:.1f}" rx="10" fill="#E9C9A6"/>',
         f'<rect x="{sx + sw * 0.60:.1f}" y="{sy - 14:.1f}" width="{sw * 0.22:.1f}" height="{sh * 0.55:.1f}" rx="10" fill="#D9B48C"/>',
         f'<rect x="{sx + 18:.1f}" y="{sy + sh:.1f}" width="8" height="16" fill="#2B2A27"/>',
         f'<rect x="{sx + sw - 26:.1f}" y="{sy + sh:.1f}" width="8" height="16" fill="#2B2A27"/>',
         # rug
         f'<ellipse cx="{w * 0.66:.1f}" cy="{h * 0.88:.1f}" rx="{w * 0.26:.1f}" ry="{h * 0.06:.1f}" fill="#EFE3CF"/>',
         # plant in an accent pot
         f'<path d="M{w * 0.875:.1f},{h * 0.76:.1f} l{w * 0.012:.1f},-{h * 0.11:.1f} h{w * 0.07:.1f} l{w * 0.012:.1f},{h * 0.11:.1f} Z" fill="{k.ACCENT}"/>']
    for ang, ln in ((-60, 0.20), (-85, 0.26), (-110, 0.21), (-35, 0.15), (-140, 0.15)):
        a = math.radians(ang)
        bx, by = w * 0.922, h * 0.65
        ex, ey = bx + math.cos(a) * h * ln, by + math.sin(a) * h * ln
        o.append(f'<path d="M{bx:.1f},{by:.1f} Q{(bx + ex) / 2 + 14:.1f},{(by + ey) / 2:.1f} {ex:.1f},{ey:.1f}" '
                 f'fill="none" stroke="#5E7A5E" stroke-width="9" stroke-linecap="round"/>')
    # pendant lamp
    o.append(f'<rect x="{w * 0.40 - 1:.1f}" y="0" width="2" height="{h * 0.18:.1f}" fill="{k.INK}"/>')
    o.append(f'<path d="M{w * 0.40 - 26:.1f},{h * 0.24:.1f} a26,22 0 0 1 52,0 Z" fill="{k.INK}"/>')
    return "".join(o)


CHEVRONS = "M9 7.5 4.5 12 9 16.5M15 7.5l4.5 4.5-4.5 4.5"


def pill(text, x, y, align, alpha):
    if alpha <= 0.001:
        return ""
    tw = k.text_width(text, 11, "SemiBold", 0.12)
    w, h = tw + 22, 25
    if align == "end":
        x -= w
    return (f'<g opacity="{alpha:.3f}"><rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="12.5" fill="{k.INK}"/>'
            + k.text_svg(text, x + 11, y + 16.6, 11, k.PAPER, "SemiBold", 0.12) + '</g>')


def hovering(t):
    return CUR_AT <= t < RELEASE + 0.05


def comparison(t):
    x, y, w, h = CMP
    p = pos(t)
    dx = w * p / 100
    o = [f'<g transform="translate({x},{y})">',
         f'<defs><clipPath id="ba-box"><rect width="{w}" height="{h}"/></clipPath>'
         f'<clipPath id="ba-after"><rect x="{dx:.2f}" width="{w - dx + 1:.2f}" height="{h}"/></clipPath></defs>',
         f'<g clip-path="url(#ba-box)">{before_room(w, h)}'
         f'<g clip-path="url(#ba-after)">{after_room(w, h)}</g>']
    # labels (fade near the edges, like .swtl-ba-off)
    o.append(pill("BEFORE", 14, 14, "start", k.clamp01((p - 16) / 4)))
    o.append(pill("AFTER", w - 14, 14, "end", k.clamp01((84 - p) / 4)))
    # divider line + handle
    o.append(f'<rect x="{dx - 4:.2f}" width="8" height="{h}" fill="#000" opacity="0.06"/>')
    o.append(f'<rect x="{dx - 1:.2f}" width="2" height="{h}" fill="{k.PAPER}"/>')
    o.append('</g>')
    sc = 1.0 + 0.08 * (k.seg(t, CUR_AT - 0.15, CUR_AT, k.ease_out) - k.seg(t, RELEASE, RELEASE + 0.2, k.ease_out))
    icon = k.ACCENT if hovering(t) else k.INK
    cy = h / 2
    o.append(f'<g transform="translate({dx:.2f},{cy:.1f}) scale({sc:.4f})">'
             f'<circle cy="3" r="27" fill="#000" opacity="0.12"/>'
             f'<circle r="26" fill="{k.PAPER}"/>'
             f'<path transform="translate(-15,-15) scale(1.25)" d="{CHEVRONS}" fill="none" stroke="{icon}" '
             f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></g>')
    o.append('</g>')
    return "".join(o)


CURSOR_D = "M0,0 L0,22 L5.6,16.8 L9.4,25.6 L13,24 L9.3,15.4 L17,15.4 Z"


def cursor(t, scr):
    """Mouse pointer in SCREEN coords (drawn above the page)."""
    if t < CUR_IN or t > CUR_OUT[1]:
        return ""
    x, y, w, h = CMP
    hx = x + w * pos(t) / 100 + 6
    hy = y - scr + h / 2 + 8
    if t < CUR_AT:
        a = k.seg(t, CUR_IN, CUR_AT, k.ease_out)
        cx, cy = k.lerp(1060, hx, a), k.lerp(690, hy, a)
        alpha = k.seg(t, CUR_IN, CUR_IN + 0.15, k.ease_out)
    elif t < CUR_OUT[0]:
        cx, cy, alpha = hx, hy, 1.0
    else:
        a = k.seg(t, *CUR_OUT, k.ease_in_out)
        cx, cy = k.lerp(hx, hx + 150, a), k.lerp(hy, hy + 170, a)
        alpha = 1 - k.seg(t, CUR_OUT[0] + 0.15, CUR_OUT[1], k.ease_out)
    pressed = PRESS <= t < RELEASE
    s = 0.92 if pressed else 1.0
    ring = (f'<circle cx="2" cy="2" r="16" fill="{k.ACCENT}" opacity="0.18"/>' if pressed else "")
    return (f'<g opacity="{alpha:.3f}" transform="translate({cx:.1f},{cy:.1f}) scale({s * 1.25:.3f})">{ring}'
            f'<path d="{CURSOR_D}" fill="{k.INK}" stroke="{k.PAPER}" stroke-width="1.6" stroke-linejoin="round"/></g>')


def section(t):
    o = [f'<rect x="64" y="{SEC_Y}" width="{k.W - 128}" height="1" fill="{k.LINE}"/>',
         k.text_svg("OUR WORK", TEXT_X, TEXT_Y, 12, k.ACCENT, "SemiBold", 0.14),
         k.text_svg("Same room,", TEXT_X - 3, TEXT_Y + 62, 50, k.INK, "SemiBold", -0.025),
         k.text_svg("eight weeks on.", TEXT_X - 3, TEXT_Y + 118, 50, k.INK, "SemiBold", -0.025),
         k.body_lines(TEXT_X, TEXT_Y + 156, [390, 410, 260], 20, 8),
         k.text_svg("Living room renovation · 2026", TEXT_X, TEXT_Y + 248, 13, k.MUTED, "Medium"),
         k.button(TEXT_X, TEXT_Y + 280, "See all projects"),
         comparison(t)]
    return "".join(o)


HEADER = k.site_header(active="Work")
HERO = k.hero(headline=("Built right,", "start to finish."), kicker="DESIGN-BUILD & RENOVATION")


def svg_at(t):
    y = scroll_y(t)
    page = (f'<g transform="translate(0,{-y:.2f})">'
            f'<rect width="{WIDTH}" height="{HEIGHT + SCROLL + 200}" fill="{k.PAPER}"/>'
            f'{HERO}{section(t)}</g>')
    return k.svg_doc(page + HEADER + cursor(t, y))
