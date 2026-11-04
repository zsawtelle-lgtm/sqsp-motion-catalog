"""Preset 10 — Parallax Depth Layers, as a video scene.

Mirrors snippets/footer-injection.html: each layer's offset is
    y = clamp(speed * dist, ±MAX)      dist = section centre - viewport centre
and the section background is translated (clamped to the room a 1.12 scale
leaves) and scaled 1.12. Speeds below are the snippet defaults, plus a
data-blocks override that pushes the front photo forward (+0.12).

Beats:
    0.00-0.40s  hold: section low in the viewport, layers offset
    0.40-4.40s  page scrolls (eased); layers converge at centre then separate
    4.40-5.20s  rest
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 5.2
WIDTH, HEIGHT = k.W, k.H

# --- snippet values (verbatim) ---------------------------------------------
MAX = 80
BG_SPEED, BG_SCALE = -0.2, 1.12
SPEED = {"text": 0.0, "back": -0.15, "front": 0.12, "button": 0.08}

# --- page geometry (page coordinates) --------------------------------------
SEC_Y, SEC_H = 520, 760
SCROLL_A, SCROLL_B = 120, 840          # dist +420 -> -300
SCROLL_T0, SCROLL_T1 = 0.40, 4.40

BACK = dict(x=610, y=100, w=390, h=470)     # section-relative
FRONT = dict(x=880, y=330, w=320, h=330)
FRAME_PAD = 10
HEAD_Y = 250                                 # first headline baseline
BTN_Y = 470


def scroll_at(t):
    return k.lerp(SCROLL_A, SCROLL_B, k.seg(t, SCROLL_T0, SCROLL_T1, k.ease_in_out))


def dist_at(t):
    return SEC_Y + SEC_H / 2 - scroll_at(t) - HEIGHT / 2


def offset(name, t):
    return max(-MAX, min(MAX, SPEED[name] * dist_at(t)))


def bg_offset(t):
    room = SEC_H * (BG_SCALE - 1) / 2
    return max(-room, min(room, BG_SPEED * dist_at(t)))


def screen_y(sec_rel_y, t, layer=None):
    """Screen y of a section-relative y for a layer (None = scrolls normally)."""
    return SEC_Y + sec_rel_y - scroll_at(t) + (offset(layer, t) if layer else 0)


def _intro():
    out = [k.site_header()]
    out.append(k.text_svg("SELECTED WORK", 64, 200, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("A studio for calm, built rooms.", 60, 268, 46, k.INK, "SemiBold", -0.02))
    out.append(k.body_lines(64, 320, [520, 560, 380], 20, 9))
    out.append(k.body_lines(700, 320, [500, 470, 520, 300], 20, 9))
    return "".join(out)


def _outro():
    y = SEC_Y + SEC_H
    out = [k.text_svg("Process", 64, y + 110, 34, k.INK, "SemiBold", -0.02)]
    out.append(k.body_lines(64, y + 150, [480, 520, 300], 20, 9))
    out.append(k.body_lines(700, y + 110, [500, 470, 520, 300], 20, 9))
    return "".join(out)


def _bg_tile():
    # big background photo placeholder, drawn darker so the tiles read on it
    w, h = WIDTH, SEC_H
    return (f'<rect width="{w}" height="{h}" fill="{k.TILE_DARK}"/>'
            f'<circle cx="{w * 0.18:.0f}" cy="{h * 0.26:.0f}" r="70" fill="{k.TILE}" opacity="0.55"/>'
            f'<path d="M0,{h} L0,{h * 0.62:.0f} L{w * 0.22:.0f},{h * 0.42:.0f} L{w * 0.42:.0f},{h * 0.66:.0f} '
            f'L{w * 0.63:.0f},{h * 0.48:.0f} L{w},{h * 0.72:.0f} L{w},{h} Z" fill="#B9B09F"/>')


def _section(t):
    by = bg_offset(t)
    cx, cy = WIDTH / 2, SEC_H / 2
    bg = (f'<g transform="translate({cx},{cy + by:.2f}) scale({BG_SCALE}) translate({-cx},{-cy})">'
          f'{_bg_tile()}</g>')
    clip = f'<clipPath id="sec"><rect width="{WIDTH}" height="{SEC_H}"/></clipPath>'

    b, f = BACK, FRONT
    back = (f'<g transform="translate(0,{offset("back", t):.2f})">'
            + k.image_tile(b["x"], b["y"], b["w"], b["h"], tone=k.TILE, idn="back") + '</g>')
    p = FRAME_PAD
    front = (f'<g transform="translate(0,{offset("front", t):.2f})">'
             f'<rect x="{f["x"] - p + 10}" y="{f["y"] - p + 18}" width="{f["w"] + 2 * p}" height="{f["h"] + 2 * p}" fill="{k.INK}" opacity="0.10"/>'
             f'<rect x="{f["x"] - p}" y="{f["y"] - p}" width="{f["w"] + 2 * p}" height="{f["h"] + 2 * p}" fill="{k.PAPER}"/>'
             + k.image_tile(f["x"], f["y"], f["w"], f["h"], tone=k.TILE, accent=k.ACCENT, idn="front") + '</g>')
    text = (k.text_svg("DEPTH LAYERS", 64, HEAD_Y - 78, 12, k.PAPER, "SemiBold", 0.14)
            + k.text_svg("Depth,", 60, HEAD_Y, 64, k.INK, "SemiBold", -0.025)
            + k.text_svg("quietly.", 60, HEAD_Y + 70, 64, k.INK, "SemiBold", -0.025)
            + k.body_lines(64, HEAD_Y + 112, [380, 330], 20, 9, k.PAPER))
    btn = f'<g transform="translate(0,{offset("button", t):.2f})">' + k.button(64, BTN_Y) + '</g>'
    return (f'<g transform="translate(0,{SEC_Y})"><defs>{clip}</defs>'
            f'<g clip-path="url(#sec)">{bg}</g>{back}{front}{text}{btn}</g>')


def svg_at(t):
    s = scroll_at(t)
    page = _intro() + _section(t) + _outro()
    return k.svg_doc(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>'
                     f'<g transform="translate(0,{-s:.2f})">{page}</g>')
