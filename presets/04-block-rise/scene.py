"""Preset 04 — Staggered block rise, as a video scene.

Mirrors snippets/footer-injection.html: the page scrolls from the hero into
a 3-column services section. Each Fluid Engine block starts 28px low and
transparent; it is "observed" like the snippet's IntersectionObserver
(rootMargin bottom -8%, threshold 0, measured on the transformed box).
Blocks that cross in the same frame form a batch and are staggered in
reading order (top, then left), 0.08s apart. Each rise is 0.8s with
cubic-bezier(.22,1,.36,1) (~ease_out). Play once; last frame at rest.

    0.00-0.45s  hero holds
    0.45-2.05s  page scrolls 660px (sticky header stays)
    ~0.7s+      heading, then image row, text row, button rise as they enter
    ~2.9s+      section at rest, holds to the end
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 4.4
WIDTH, HEIGHT = k.W, k.H

# ---- timing: copied verbatim from the snippet's CONFIG -------------------
DISTANCE = 28.0
DUR = 0.8
STAGGER = 0.08
MAX_DELAY = 0.9
TRIGGER_Y = HEIGHT * (1 - 0.08)        # rootMargin '0px 0px -8% 0px'

SCROLL_START, SCROLL_END = 0.45, 2.05
SCROLL = 660.0
Y0 = 720.0                             # services section top (page coords)

HEADER_H = 76
COL_W, GUTTER, X0 = 362.0, 33.0, 64.0
IMG_Y, IMG_H = Y0 + 160, 210
TXT_Y = Y0 + 410
BTN_Y = Y0 + 520


def scroll(t):
    return SCROLL * k.seg(t, SCROLL_START, SCROLL_END, k.ease_in_out)


def _blocks():
    """(id, page_top, page_left, page_bottom, draw(dy) -> svg). DOM order is
    irrelevant; reveal order comes from position, like the snippet."""
    out = []

    def head(_):
        return (k.text_svg("SERVICES", X0, Y0 + 90, 12, k.ACCENT, "SemiBold", 0.14)
                + k.text_svg("What we do", X0 - 2, Y0 + 132, 44, k.INK, "SemiBold", -0.025))
    out.append(("head", Y0 + 70, X0, Y0 + 140, head))
    names = ["Architecture", "Planning", "Interiors"]
    for i in range(3):
        x = X0 + i * (COL_W + GUTTER)
        out.append((f"img{i + 1}", IMG_Y, x, IMG_Y + IMG_H,
                    lambda _, x=x, i=i: k.image_tile(x, IMG_Y, COL_W, IMG_H, idn=f"svc{i}",
                                                     accent=k.ACCENT if i == 1 else None)))
        out.append((f"txt{i + 1}", TXT_Y, x, TXT_Y + 90,
                    lambda _, x=x, n=names[i]: k.text_svg(n, x, TXT_Y + 22, 21, k.INK, "SemiBold", -0.01)
                    + k.body_lines(x, TXT_Y + 44, [COL_W - 30, COL_W - 70, COL_W - 150], 18, 8)))
    out.append(("btn", BTN_Y, X0, BTN_Y + 46, lambda _: k.button(X0, BTN_Y, "View all services")))
    return out


BLOCKS = _blocks()


def _schedule(fps=240):
    """Simulate the observer: start time per block id."""
    start, t = {}, 0.0
    while t <= DURATION and len(start) < len(BLOCKS):
        s = scroll(t)
        batch = [b for b in BLOCKS if b[0] not in start
                 and b[1] - s + DISTANCE < TRIGGER_Y and b[3] - s + DISTANCE > 0]
        batch.sort(key=lambda b: (round(b[1] / 8), b[2]))  # top (8px rows), then left
        for j, b in enumerate(batch):
            start[b[0]] = t + min(j * STAGGER, MAX_DELAY)
        t += 1 / fps
    return start


START = _schedule()
REST_AT = max(START.values()) + DUR


def progress(bid, t):
    return k.seg(t, START[bid], START[bid] + DUR, k.ease_out)


def svg_at(t):
    s = scroll(t)
    hero = k.hero()
    blocks = []
    for bid, top, left, bottom, draw in BLOCKS:
        p = progress(bid, t)
        if p <= 0:
            continue
        dy = DISTANCE * (1 - p)
        blocks.append(f'<g opacity="{p:.3f}" transform="translate(0,{dy:.2f})">{draw(dy)}</g>')
    page = (f'<g transform="translate(0,{-s:.2f})">{hero}'
            f'<rect x="0" y="{Y0:.0f}" width="{WIDTH}" height="1" fill="{k.LINE}"/>'
            f'{"".join(blocks)}</g>')
    return k.svg_doc(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>'
                     + page + k.site_header(active="Services"))


if __name__ == "__main__":
    for bid, st in sorted(START.items(), key=lambda kv: kv[1]):
        print(f"{bid:5s} {st:.3f}s")
    print("rest", round(REST_AT, 3))
