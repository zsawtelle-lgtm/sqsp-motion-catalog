"""Timing model for the counter preloader, shared by the video scene and the
snippet builder (build_snippet.py writes these numbers into the JS), so the
browser and the video run the same curve.

Counter value v(t), t = seconds since the overlay mounted:
    waiting:   v = CRAWL * (1 - exp(-t / TAU))          eases toward ~90, never past
    ready:     ready = max(window load, MIN_SHOW)  (or MAX_WAIT fail-safe)
               v eases from v(ready) to 100 over FINISH (power3.out)
    exit:      HOLD after 100 -> counter rolls up (ROLL)
               WIPE_DELAY later -> overlay wipes up (WIPE) -> node removed
"""
CRAWL = 90          # % the counter crawls toward while waiting
TAU = 0.9           # s, crawl time constant
MIN_SHOW = 1.8      # s, earliest the counter may complete
MAX_WAIT = 8.0      # s, fail-safe: force completion
FINISH = 0.6        # s, v(ready) -> 100
HOLD = 0.25         # s, rest on 100
ROLL = 0.5          # s, counter + wordmark leave
WIPE_DELAY = 0.15   # s after the roll starts
WIPE = 0.75         # s, overlay translateY(-100%)

EASE_FINISH = "power3.out"                 # 1-(1-p)^3, done in JS
EASE_ROLL = "cubic-bezier(.7,0,.2,1)"      # scene_kit.ease_sweep
EASE_WIPE = "cubic-bezier(.7,0,.2,1)"


def crawl(t):
    import math
    return CRAWL * (1 - math.exp(-max(0.0, t) / TAU))


def value(t, ready_at):
    """Counter value at t for a given ready time (s since mount)."""
    if t < ready_at:
        return crawl(t)
    v0 = crawl(ready_at)
    p = min(1.0, (t - ready_at) / FINISH)
    return v0 + (100 - v0) * (1 - (1 - p) ** 3)


def exit_at(ready_at):
    return ready_at + FINISH + HOLD
