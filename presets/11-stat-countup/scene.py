"""Preset 11 — Stat count-up, as a video scene.

Mirrors snippets/footer-injection.html: the page scrolls from the hero into
a 4-column stats row. Each number is "observed" like the snippet's
IntersectionObserver (rootMargin bottom -10%, threshold 0). Numbers that
cross in the same frame form a batch, staggered left to right 0.12s apart.
Each counts 0 -> typed value in 1.6s, ease-out cubic, keeping its prefix,
suffix, commas and decimals; the running copy is right-aligned in the box
the typed number reserves (no layout shift). A 3px accent line grows under
each number with the same eased progress. Plays once; last frame at rest.

    0.00-0.40s  hero holds
    0.40-1.80s  page scrolls 540px (sticky header stays)
    ~1.0s+      the four numbers start counting, left to right
    ~3.0s+      every number on its typed value, holds to the end
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
import scene_kit as k  # noqa: E402

DURATION = 4.6
WIDTH, HEIGHT = k.W, k.H

# ---- timing: copied verbatim from the snippet's CONFIG -------------------
DUR = 1.6
STAGGER = 0.12
MAX_DELAY = 0.8
TRIGGER_Y = HEIGHT * (1 - 0.10)        # rootMargin '0px 0px -10% 0px'

SCROLL_START, SCROLL_END = 0.40, 1.80
SCROLL = 540.0
Y0 = 720.0                             # stats section top (page coords)
HEADER_H = 76

X0, COL_W = 64.0, (1280 - 128) / 4
NUM_SIZE = 76
NUM_BASE = Y0 + 300                    # number baseline (page coords)
LABEL_BASE = NUM_BASE + 62
LINE_Y = NUM_BASE + 0.24 * NUM_SIZE    # CSS: bottom -0.06em of the inline box
LINE_H = max(2.0, 0.045 * NUM_SIZE)

# (prefix, number, decimals, commas, suffix, label) — typed text, parsed like the snippet
STATS = [
    ("", 25, 0, False, "+", "Years in practice"),
    ("", 1200, 0, True, "", "Projects delivered"),
    ("", 98, 0, False, "%", "Client retention"),
    ("$", 4.5, 1, False, "M", "Raised for partners"),
]


def fmt(v, dec, commas):
    f = 10 ** dec
    s = f"{math.floor(v * f + 1e-6) / f:.{dec}f}"
    if commas:
        i, _, d = s.partition(".")
        s = f"{int(i):,}" + (("." + d) if d else "")
    return s


def word(i):
    pre, n, dec, com, suf, _ = STATS[i]
    return pre + fmt(n, dec, com) + suf


def tabular(text, right, y):
    """Running copy with tabular figures (CSS font-variant-numeric):
    every digit gets the same cell, right-aligned at `right`."""
    track = -0.02 * NUM_SIZE
    cell = 1325 / 2048 * NUM_SIZE + track       # Inter "zero.tf" advance
    widths = [cell if c.isdigit() else k.text_width(c, NUM_SIZE, "SemiBold") + track for c in text]
    x, out = right - sum(widths), []
    for c, w in zip(text, widths):
        cw = k.text_width(c, NUM_SIZE, "SemiBold")
        out.append(k.text_svg(c, x + (w - cw - track) / 2 if c.isdigit() else x, y, NUM_SIZE, k.INK, "SemiBold"))
        x += w
    return "".join(out)


def scroll(t):
    return SCROLL * k.seg(t, SCROLL_START, SCROLL_END, k.ease_in_out)


def _schedule(fps=240):
    """Simulate the observer: start time per stat index."""
    start, t = {}, 0.0
    top, bottom = NUM_BASE - 0.75 * NUM_SIZE, NUM_BASE + 0.25 * NUM_SIZE
    while t <= DURATION and len(start) < len(STATS):
        s = scroll(t)
        batch = [i for i in range(len(STATS)) if i not in start
                 and top - s < TRIGGER_Y and bottom - s > 0]
        for j, i in enumerate(batch):            # same row → left to right
            start[i] = t + min(j * STAGGER, MAX_DELAY)
        t += 1 / fps
    return start


START = _schedule()
REST_AT = max(START.values()) + DUR


def progress(i, t):
    return k.seg(t, START[i], START[i] + DUR, k.ease_out)   # 1-(1-p)^3


def stat_svg(i, t):
    pre, n, dec, com, suf, label = STATS[i]
    x = X0 + i * COL_W
    e = progress(i, t)
    final = fmt(n, dec, com)
    pw = k.text_width(pre, NUM_SIZE, "SemiBold", -0.02) if pre else 0.0
    fw = k.text_width(final, NUM_SIZE, "SemiBold", -0.02)
    total = k.text_width(pre + final + suf, NUM_SIZE, "SemiBold", -0.02)
    run = final if e >= 1 else fmt(n * e, dec, com)
    out = []
    if pre:
        out.append(k.text_svg(pre, x, NUM_BASE, NUM_SIZE, k.INK, "SemiBold", -0.02))
    if e >= 1:                                   # at rest: the typed text itself
        out.append(k.text_svg(final, x + pw, NUM_BASE, NUM_SIZE, k.INK, "SemiBold", -0.02))
    else:
        out.append(tabular(run, x + pw + fw, NUM_BASE))
    if suf:
        out.append(k.text_svg(suf, x + pw + fw + (total - pw - fw - k.text_width(suf, NUM_SIZE, "SemiBold", -0.02)),
                              NUM_BASE, NUM_SIZE, k.INK, "SemiBold", -0.02))
    if e > 0:
        out.append(f'<rect x="{x:.1f}" y="{LINE_Y:.1f}" width="{total * e:.2f}" height="{LINE_H:.1f}" fill="{k.ACCENT}"/>')
    out.append(k.text_svg(label, x, LABEL_BASE, 16, k.MUTED, "Medium"))
    return "".join(out)


def section():
    out = [f'<rect x="0" y="{Y0:.0f}" width="{WIDTH}" height="1" fill="{k.LINE}"/>',
           k.text_svg("BY THE NUMBERS", X0, Y0 + 92, 12, k.ACCENT, "SemiBold", 0.14),
           k.text_svg("Ten years of work, measured.", X0 - 2, Y0 + 140, 42, k.INK, "SemiBold", -0.025),
           k.body_lines(X0, Y0 + 168, [420, 300], 18, 8),
           f'<rect x="{X0:.0f}" y="{LABEL_BASE + 56:.0f}" width="{WIDTH - 2 * X0:.0f}" height="1" fill="{k.LINE}"/>',
           k.button(X0, LABEL_BASE + 92, "Read our story")]
    return "".join(out)


def svg_at(t):
    s = scroll(t)
    stats = "".join(stat_svg(i, t) for i in range(len(STATS)))
    page = f'<g transform="translate(0,{-s:.2f})">{k.hero()}{section()}{stats}</g>'
    return k.svg_doc(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{k.PAPER}"/>'
                     + page + k.site_header(active="About"))


if __name__ == "__main__":
    for i, st in sorted(START.items()):
        print(word(i), f"{st:.3f}s")
    print("rest", round(REST_AT, 3))
