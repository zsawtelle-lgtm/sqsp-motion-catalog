"""Timed frame assertions for preset 05 (one per beat). Run: python checks.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "shared"))
from check import Checker  # noqa: E402
import scene_kit as k  # noqa: E402

c = Checker(__file__)
s = c.scene
tm = s.tm
SNIPPET = (HERE / "snippets" / "footer-injection.html").read_text()


def box(b, t, x0=0.0, x1=1.0, pad=4):
    """Page-space image box -> screen pixel box at time t (after scroll),
    optionally a horizontal slice x0..x1 of the block width."""
    x, y, w, h = b
    y -= s.scroll_y(t)
    return (int(x + w * x0 + pad), int(y + pad), int(x + w * x1 - pad), int(min(k.H, y + h) - pad))


def acc(f, b, t, x0=0.0, x1=1.0):
    return c.share(f, k.ACCENT, box(b, t, x0, x1), 30)


REST = c.frame(s.DURATION)

# 0. the video uses the snippet's numbers (timing.py <-> CSS)
for needle in ["1.3s", "0.68s", "+ 0.62s", "1.2s", "scale(1.08)", "42.31%", "47.69%", "0.8s", "stagger: 0.28"]:
    c.expect(f"snippet timing matches timing.py: {needle}", 0.0,
             lambda f, n=needle: (n in SNIPPET, ""))
assert abs(tm.CURTAIN_IN / tm.CURTAIN_TOTAL - 0.4231) < 1e-3 and abs(tm.UNCOVER_AT / tm.CURTAIN_TOTAL - 0.4769) < 1e-3

T1, T2 = s.T1, s.T2
c.expect("before trigger: image area is blank paper (hidden state)", T1 - 0.05,
         lambda f: (c.share(f, k.PAPER, box(s.IMG1, T1 - 0.05), 6) > 0.98,
                    f"{c.share(f, k.PAPER, box(s.IMG1, T1 - 0.05), 6):.3f}"))
c.expect("curtain mid-sweep: accent on the left, paper on the right", T1 + 0.30,
         lambda f: (acc(f, s.IMG1, T1 + 0.30, 0, 0.3) > 0.95 and acc(f, s.IMG1, T1 + 0.30, 0.8, 1) < 0.02,
                    f"L={acc(f, s.IMG1, T1 + 0.30, 0, 0.3):.2f} R={acc(f, s.IMG1, T1 + 0.30, 0.8, 1):.2f}"))
c.expect("curtain hold: block fully covered", T1 + 0.58,
         lambda f: (acc(f, s.IMG1, T1 + 0.58) > 0.98, f"{acc(f, s.IMG1, T1 + 0.58):.3f}"))
TU = T1 + tm.UNCOVER_AT + tm.UNCOVER * 0.5
c.expect("uncover: photo on the left, curtain still on the right", TU,
         lambda f: (acc(f, s.IMG1, TU, 0, 0.3) < 0.01 and acc(f, s.IMG1, TU, 0.75, 1) > 0.95
                    and c.share(f, k.PAPER, box(s.IMG1, TU, 0, 0.3), 6) < 0.5,
                    f"L={acc(f, s.IMG1, TU, 0, 0.3):.2f} R={acc(f, s.IMG1, TU, 0.75, 1):.2f}"))
c.expect("uncovered photo is still scaled up (differs from rest)", TU,
         lambda f: (c.diff(f, REST, box(s.IMG1, TU, 0, 0.3)) > 0.3,
                    f"diff={c.diff(f, REST, box(s.IMG1, TU, 0, 0.3)):.2f}"))
TS = T1 + tm.CURTAIN_TOTAL + 0.05
c.expect("curtain gone, image nearly settled", TS,
         lambda f: (acc(f, s.IMG1, TS) < 0.005 and 0.02 < c.diff(f, REST, box(s.IMG1, TS)) < 1.0,
                    f"acc={acc(f, s.IMG1, TS):.3f} diff={c.diff(f, REST, box(s.IMG1, TS)):.2f}"))
T2M = T2 + 0.30
c.expect("second image: curtain sweeping after the first", T2M,
         lambda f: (acc(f, s.IMG2, T2M, 0, 0.3) > 0.95 and acc(f, s.IMG2, T2M, 0.8, 1) < 0.02,
                    f"L={acc(f, s.IMG2, T2M, 0, 0.3):.2f} R={acc(f, s.IMG2, T2M, 0.8, 1):.2f}"))
c.expect("second image still hidden while the first is covered", T2 - 0.05,
         lambda f: (c.share(f, k.PAPER, box(s.IMG2, T2 - 0.05), 6) > 0.98, ""))
c.expect("rest: both images uncovered, no curtain left", s.REST_AT + 0.05,
         lambda f: (acc(f, s.IMG1, s.DURATION) < 0.005 and acc(f, s.IMG2, s.DURATION) < 0.005
                    and c.diff(f, REST) < 0.3, f"diff={c.diff(f, REST):.2f}"))
c.expect("final frame == resting state (image 1 at scale 1)", s.DURATION,
         lambda f: (c.diff(f, c.frame(s.REST_AT + 0.6)) < 0.05, ""))
c.run()
