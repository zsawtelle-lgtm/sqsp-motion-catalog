"""Timing + easing for the page-transition wipe, shared by the video scene and
the snippet generator so both use the exact same numbers.
Run build_snippet.py after changing anything here.
"""

# ---- timing (seconds): the snippet's JS uses the exact same numbers --------
IN_DUR = 0.50          # panel wipes up over the current page, then navigate
OUT_DUR = 0.60         # next page: panel wipes up and off
HOLD = 0.08            # beat on the covered next page before the wipe-off
LABEL_IN_AT = 0.15     # label (link text) fades/rises in, after the click
LABEL_IN_DUR = 0.35
LABEL_RISE = 12        # px
LABEL_OUT_DUR = 0.25   # label fades as the panel lifts off (linear)
NAV_GRACE = 0.08       # navigate at IN_DUR + this even if transitionend never fires

# ---- CSS easing curves, evaluated exactly (video == browser) ---------------
EASE_WIPE = (0.76, 0, 0.24, 1)     # panel, both directions: strong in-out
EASE_LABEL = (0.22, 1, 0.36, 1)    # label in: soft out


def bezier(x1, y1, x2, y2):
    """Return f(p) for CSS cubic-bezier(x1,y1,x2,y2) (bisection on x)."""
    def cx(s):
        return 3 * x1 * s * (1 - s) ** 2 + 3 * x2 * s * s * (1 - s) + s ** 3

    def cy(s):
        return 3 * y1 * s * (1 - s) ** 2 + 3 * y2 * s * s * (1 - s) + s ** 3

    def f(p):
        if p <= 0:
            return 0.0
        if p >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if cx(mid) < p:
                lo = mid
            else:
                hi = mid
        return cy((lo + hi) / 2)
    return f


def css(curve):
    return "cubic-bezier(%s)" % ",".join(f"{v:g}" for v in curve)
