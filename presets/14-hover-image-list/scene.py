"""Preset 14 — Hover Image Reveal List, as a video scene.

Mirrors snippets/footer-injection.html (values copied verbatim):
    rows      font 64px (clamp(30px, 5vw, 64px) at 1280), weight 600, -0.02em,
              line-height 1.08, padding .3em top/bottom, 1px hairline borders
    arrow     Heroicons outline, stroke 2, .62em, margin-left:auto;
              hover: translateX(5px) + accent, .35s cubic-bezier(.22,1,.36,1)
    dim       other rows opacity .3, transition .35s ease
    float     340 x 255 (4/3), centered on the eased cursor
              per 60Hz frame: x += (tx - x) * 0.14; rot += (clamp(dx*0.35, ±8) - rot) * 0.15
              show: clip-path inset(100% 0 0 0) -> inset(0), scale .82 -> 1 (.55s
              cubic-bezier(.22,1,.36,1)), opacity 0 -> 1 (.3s ease)
    swap      img opacity .35s ease, scale 1.12 -> 1 over .7s cubic-bezier(.22,1,.36,1)
    snap      the float jumps to the cursor when it was hidden for > 600ms

The scene runs the same event logic as the snippet (mouseenter row -> show,
mousemove -> new target, leave list -> hide) on a 60Hz simulation, then
samples it per video frame. The cursor is drawn on top.
"""
import functools
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

WIDTH, HEIGHT = k.W, k.H
FPS = 30
DURATION = 5.8
SIM_HZ = 60

# ---- snippet values
EASE, TILT, MAX_TILT, ROT_EASE = 0.14, 0.35, 8.0, 0.15
FW, FH = 340.0, 255.0
SNAP_AFTER = 0.6
SIZE = 64.0
PAD = 0.3 * SIZE
LINE_H = 1.08 * SIZE
ROW_H = 2 * PAD + LINE_H + 1          # + 1px border-top
ARROW = 0.62 * SIZE
DIM = 0.3

# ---- layout
X0, X1 = 64, 1216
LIST_TOP = 150
ROWS = ["Harbor House", "Mill Street Lofts", "Orchard Pavilion", "Quarry Studio", "Fieldstone Barn"]
TONES = ["#C9B79C", "#9FB0A3", "#B89A8E", "#A7B4C2", "#D1BE86"]
SUNS = ["#E9DCC6", "#DCE5DD", "#E7D3C9", "#DDE4EC", "#F0E4BE"]
N = len(ROWS)
LIST_BOT = LIST_TOP + N * ROW_H


def row_top(i):
    return LIST_TOP + i * ROW_H


def row_cy(i):
    return row_top(i) + 1 + PAD + LINE_H / 2


# ---- cubic-bezier easing (same curves as the CSS)
def bezier(x1, y1, x2, y2):
    def f(p):
        if p <= 0:
            return 0.0
        if p >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(40):
            s = (lo + hi) / 2
            x = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
            lo, hi = (s, hi) if x < p else (lo, s)
        s = (lo + hi) / 2
        return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3
    return f


OUT = bezier(.22, 1, .36, 1)
EASE_CSS = bezier(.25, .1, .25, 1)


class Trans:
    """A CSS transition on one value: retargets from wherever it is now."""

    def __init__(self, v, dur, ease):
        self.dur, self.ease = dur, ease
        self.segs = [(-1.0, v, v)]          # (start, from, to)

    def at(self, t):
        t0, a, b = self.segs[0]
        for s in self.segs:
            if s[0] <= t:
                t0, a, b = s
        return a + (b - a) * self.ease(k.clamp01((t - t0) / self.dur))

    def set(self, t, v):
        if self.segs[-1][2] != v:
            self.segs.append((t, self.at(t), v))


# ---- cursor path: (time, x, y); eased moves between keys, holds where equal
KEYS = [
    (0.00, 1040, 108), (0.45, 1040, 108),
    (1.00, 700, row_cy(0)), (1.40, 740, row_cy(0) + 5),
    (1.80, 520, row_cy(1)), (2.20, 545, row_cy(1) + 5),
    (2.60, 820, row_cy(2)), (3.00, 840, row_cy(2) + 4),
    (3.40, 600, row_cy(3)), (3.80, 622, row_cy(3) + 5),
    (4.20, 880, row_cy(4)), (4.55, 900, row_cy(4) + 4),
    (5.00, 1252, 612), (DURATION, 1252, 612),
]


def cursor(t):
    for (ta, xa, ya), (tb, xb, yb) in zip(KEYS, KEYS[1:]):
        if t <= tb:
            p = k.ease_in_out(k.clamp01((t - ta) / (tb - ta))) if tb > ta else 1
            return xa + (xb - xa) * p, ya + (yb - ya) * p
    return KEYS[-1][1], KEYS[-1][2]


def hovered(mx, my):
    if not (X0 <= mx <= X1 and LIST_TOP <= my < LIST_BOT):
        return None
    return int((my - LIST_TOP) // ROW_H)


@functools.lru_cache(maxsize=1)
def simulate():
    """60Hz run of the snippet's event + rAF logic. Returns per-tick states and transitions."""
    reveal = Trans(0.0, .55, OUT)            # clip + scale
    fade = Trans(0.0, .30, EASE_CSS)         # frame opacity
    img_op = [Trans(0.0, .35, EASE_CSS) for _ in range(N)]
    img_sc = [Trans(1.12, .70, OUT) for _ in range(N)]
    row_op = [Trans(1.0, .35, EASE_CSS) for _ in range(N)]
    arr = [Trans(0.0, .35, OUT) for _ in range(N)]
    x = y = tx = ty = rot = 0.0
    shown, hid_at, cur = False, -1e9, None
    ticks = []
    steps = int(DURATION * SIM_HZ) + 2
    for n in range(steps):
        t = n / SIM_HZ
        mx, my = cursor(t)
        h = hovered(mx, my)
        if h is not None:
            tx, ty = mx, my                    # mousemove / mouseenter
            if h != cur:                       # mouseenter row -> show(i)
                if not shown and t - hid_at > SNAP_AFTER:
                    x, y, rot = tx, ty, 0.0
                shown, cur = True, h
                reveal.set(t, 1.0)
                fade.set(t, 1.0)
                for i in range(N):
                    img_op[i].set(t, 1.0 if i == h else 0.0)
                    img_sc[i].set(t, 1.0 if i == h else 1.12)
                    row_op[i].set(t, 1.0 if i == h else DIM)
                    arr[i].set(t, 1.0 if i == h else 0.0)
        elif shown:                            # mouseleave list -> hide()
            shown, hid_at, cur = False, t, None
            reveal.set(t, 0.0)
            fade.set(t, 0.0)
            for i in range(N):
                row_op[i].set(t, 1.0)
                arr[i].set(t, 0.0)
        # rAF tick
        dx, dy = (tx - x) * EASE, (ty - y) * EASE
        x += dx
        y += dy
        rot += (max(-MAX_TILT, min(MAX_TILT, dx * TILT)) - rot) * ROT_EASE
        ticks.append((x, y, rot, shown, cur))
    return ticks, dict(reveal=reveal, fade=fade, img_op=img_op, img_sc=img_sc, row_op=row_op, arr=arr)


def state(t):
    ticks, tr = simulate()
    i = min(len(ticks) - 1, int(round(t * SIM_HZ)))
    x, y, rot, shown, cur = ticks[i]
    return dict(x=x, y=y, rot=rot, shown=shown, cur=cur, tr=tr)


# ---- drawing
def mix(c1, c2, p):
    r1, g1, b1 = (int(c1[i:i + 2], 16) for i in (1, 3, 5))
    r2, g2, b2 = (int(c2[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % (round(r1 + (r2 - r1) * p), round(g1 + (g2 - g1) * p), round(b1 + (b2 - b1) * p))


def _page():
    out = [f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>', k.site_header(active="Work")]
    out.append(k.text_svg("SELECTED WORK", X0, 124, 12, k.ACCENT, "SemiBold", 0.14))
    out.append(k.text_svg("2019 — 2026", X1, 124, 12, k.MUTED, "Medium", 0.06, anchor="end"))
    for i in range(N + 1):
        out.append(f'<rect x="{X0}" y="{row_top(i):.2f}" width="{X1 - X0}" height="1" fill="{k.LINE}"/>')
    return "".join(out)


PAGE = _page()
BASE = 1 + PAD + (LINE_H - (1984 + 494) / 2048 * SIZE) / 2 + 1984 / 2048 * SIZE


def _rows(t, tr):
    out = []
    for i, name in enumerate(ROWS):
        top = row_top(i)
        op = tr["row_op"][i].at(t)
        a = tr["arr"][i].at(t)
        col = mix(k.INK, k.ACCENT, a)
        out.append(f'<g opacity="{op:.3f}">')
        out.append(k.text_svg(name, X0 - 2, top + BASE, SIZE, k.INK, "SemiBold", -0.02))
        out.append(k.arrow(X1 - ARROW + 5 * a, row_cy(i) - ARROW / 2, ARROW, col, 2.0))
        out.append("</g>")
    return "".join(out)


def _tile(i, w, h):
    """Placeholder photo, distinct per project (tone + sun position)."""
    sx = [0.70, 0.30, 0.62, 0.40, 0.76][i]
    sy = [0.34, 0.30, 0.26, 0.36, 0.30][i]
    m = min(w, h)
    return (f'<rect width="{w}" height="{h}" fill="{TONES[i]}"/>'
            f'<circle cx="{w * sx:.1f}" cy="{h * sy:.1f}" r="{m * 0.09:.1f}" fill="{SUNS[i]}"/>'
            f'<path d="M0,{h} L{w * 0.30:.1f},{h * 0.60:.1f} L{w * 0.50:.1f},{h * 0.80:.1f} '
            f'L{w * 0.70:.1f},{h * 0.58:.1f} L{w},{h * 0.86:.1f} L{w},{h} Z" fill="{k.INK}" opacity="0.18"/>')


def _float(t, s):
    tr = s["tr"]
    rv, op = tr["reveal"].at(t), tr["fade"].at(t)
    if op < 0.003:
        return "", ""
    sc = 0.82 + 0.18 * rv
    top = FH * (1 - rv)                   # clip-path inset(top 0 0 0)
    clip = f'<clipPath id="fclip"><rect x="0" y="{top:.2f}" width="{FW}" height="{FH - top:.2f}" rx="4"/></clipPath>'
    imgs = []
    for i in range(N):
        io = tr["img_op"][i].at(t)
        if io < 0.003:
            continue
        isc = tr["img_sc"][i].at(t)
        imgs.append(f'<g opacity="{io:.3f}" transform="translate({FW / 2},{FH / 2}) scale({isc:.4f}) '
                    f'translate({-FW / 2},{-FH / 2})">{_tile(i, FW, FH)}</g>')
    body = (f'<g transform="translate({s["x"]:.2f},{s["y"]:.2f}) rotate({s["rot"]:.3f}) scale({sc:.4f}) '
            f'translate({-FW / 2},{-FH / 2})" opacity="{op:.3f}">'
            f'<g clip-path="url(#fclip)"><rect width="{FW}" height="{FH}" fill="{k.INK}"/>{"".join(imgs)}</g></g>')
    return body, clip


CURSOR_D = "M0,0 L0,17 L4.6,12.9 L7.6,19.6 L10.3,18.4 L7.4,11.9 L13,11.9 Z"


def _cursor(t):
    x, y = cursor(t)
    return (f'<path transform="translate({x:.2f},{y:.2f}) scale(1.35)" d="{CURSOR_D}" '
            f'fill="{k.INK}" stroke="{k.PAPER}" stroke-width="1.2" stroke-linejoin="round"/>')


def svg_at(t):
    s = state(t)
    fl, clip = _float(t, s)
    return k.svg_doc(PAGE + _rows(t, s["tr"]) + fl + _cursor(t), defs=clip)
