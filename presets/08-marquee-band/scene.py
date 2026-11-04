"""Preset 08 — Marquee / Ticker Band, as a video scene.

Mirrors snippets/footer-injection.html (CSS metrics copied verbatim):
    font-size --swtl-mq-size        80px here (Inter SemiBold, -0.02em)
    line-height 1.15 · band padding .22em · row gap .08em
    item padding .42em each side · star glyph .42em, accent
    row 1: solid paper words, moves left   (keyframe 0 -> -period)
    row 2: outlined words (1.5px stroke), phrases reversed, moves right
    duration = period / speed  -> one loop period per LOOP seconds

Seamless loop: the band travels exactly one set width (period) in LOOP
seconds, so state(LOOP) == state(0). The period is rounded up to whole
STEP-px frames (see FRAMES) so LOOP is an exact frame count at 30 and 20fps.
The preview runs at PERIOD/LOOP = 270 px/s so one full period fits in ~6s;
the snippet default is 100 px/s. The renderer also draws a frame at
t=DURATION, so DURATION = LOOP - 1 frame: the frame after the last one is
t=LOOP, which equals frame 0. No duplicated frame at the wrap.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

import os
FPS = 30
STEP = int(os.environ.get("MQ_STEP", 9))
# MQ_CRISP=1: aliased band edges, used for the GIF pass only. Antialiased
# moving text dithers into a ~4.5 MB GIF; crisp edges keep it under 2.5 MB.
CRISP = os.environ.get("MQ_CRISP") == "1"   # px the band moves per 30fps frame (whole px = crisp, small files)
WIDTH, HEIGHT = k.W, k.H

WORDS = ["Design", "Build", "Interiors", "Landscape"]
SIZE = float(os.environ.get("MQ_SIZE", 80))
TRACK = -0.02
PAD = 0.42 * SIZE          # .swtl-mq-item padding (each side)
GLYPH = 0.42 * SIZE        # .swtl-mq-sep svg
LINE_H = 1.15 * SIZE
BAND_PAD = 0.22 * SIZE
ROW_GAP = 0.08 * SIZE
STROKE = 1.5
# baseline inside a 1.15 line box (Inter: ascent 1984, descent 494 / 2048)
ASC, DESC = 1984 / 2048 * SIZE, 494 / 2048 * SIZE
BASE = (LINE_H - (ASC + DESC)) / 2 + ASC

STAR_D = ("M12 1.5c.7 5.6 4.9 9.8 10.5 10.5-5.6.7-9.8 4.9-10.5 10.5"
          "C11.3 16.9 7.1 12.7 1.5 12 7.1 11.3 11.3 7.1 12 1.5z")


def _layout(words):
    """[(kind, x, payload)] for one set, plus the set width (= loop period)."""
    items, x = [], 0.0
    for w in words:
        x += PAD
        items.append(("word", x, w))
        x += k.text_width(w, SIZE, "SemiBold", TRACK) + PAD
        items.append(("star", x, None))
        x += GLYPH
    return items, x


SET1, RAW = _layout(WORDS)
SET2, _ = _layout(WORDS[::-1])
# Round the loop period up to a whole multiple of STEP (adds <STEP px to the
# last star's trailing gap; invisible) so every frame lands on a whole pixel
# and t=LOOP is exactly frame 0 (in the 30fps MP4 and the 20fps GIF).
FRAMES = int(RAW // STEP) + 1
FRAMES += -FRAMES % 3      # multiple of 3 -> the 20fps GIF also wraps on an exact frame
PERIOD = PERIOD2 = FRAMES * STEP
LOOP = FRAMES / FPS
DURATION = LOOP - 1 / FPS
SPEED = PERIOD / LOOP      # px/s shown in the video (= config `speed`)

BAND_Y = 268
ROW1_Y = BAND_Y + BAND_PAD
ROW2_Y = ROW1_Y + LINE_H + ROW_GAP
BAND_H = 2 * BAND_PAD + 2 * LINE_H + ROW_GAP


def _set_svg(items, ox, oy, outline):
    out = []
    for kind, x, w in items:
        if kind == "word":
            if outline:
                paint = f'fill="none" stroke="{k.PAPER}" stroke-width="{STROKE}" stroke-linejoin="round"'
            else:
                paint = ""
            fill = "none" if outline else k.PAPER
            out.append(k.text_svg(w, ox + x, oy + BASE, SIZE, fill, "SemiBold", TRACK,
                                  extra=paint.replace('fill="none" ', "")))
        else:
            s = GLYPH / 24
            gy = oy + (LINE_H - GLYPH) / 2
            out.append(f'<path transform="translate({ox + x:.2f},{gy:.2f}) scale({s:.4f})" '
                       f'd="{STAR_D}" fill="{k.ACCENT}"/>')
    return "".join(out)


def _row(items, period, y, offset, outline):
    """offset = current translateX of the track (0 .. -period)."""
    n = int(WIDTH // period) + 2
    return "".join(_set_svg(items, offset + i * period, y, outline) for i in range(n))


def row_offsets(t):
    p = (t % LOOP) / LOOP
    left = -round(p * PERIOD)               # keyframe 0 -> -period
    right = -PERIOD2 + round(p * PERIOD2)   # same keyframe, reversed
    return left, right


def _page():
    out = [f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>', k.site_header(active="Services")]
    out.append(k.text_svg("WHAT WE DO", 64, 156, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("One studio, start to finish.", 60, 214, 40, k.INK, "SemiBold", -0.02))
    out.append(k.body_lines(820, 176, [396, 360, 250], 20, 9))
    y = BAND_Y + BAND_H + 52
    for i, x in enumerate((64, 448, 832)):
        out.append(k.image_tile(x, y, 372, 220, idn=f"t{i}"))
    return "".join(out)


PAGE = _page()


def svg_at(t):
    left, right = row_offsets(t)
    band = (f'<rect x="0" y="{BAND_Y}" width="{WIDTH}" height="{BAND_H:.2f}" fill="{k.INK}"/>'
            + _row(SET1, PERIOD, ROW1_Y, left, False)
            + _row(SET2, PERIOD2, ROW2_Y, right, True))
    clip = (f'<clipPath id="band"><rect x="0" y="{BAND_Y}" width="{WIDTH}" height="{BAND_H:.2f}"/></clipPath>')
    return k.svg_doc(PAGE + f'<g clip-path="url(#band)"{' shape-rendering="crispEdges"' if CRISP else ''}>{band}</g>', defs=clip)
