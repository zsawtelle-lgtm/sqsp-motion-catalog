"""Frame-level assertions for preset scenes (validation standard from the
website-animations skill: one numeric check per beat, not eyeballing).

Usage inside a preset's checks.py:

    from check import Checker
    c = Checker(__file__)               # loads ./scene.py
    c.expect("frame drawing", 0.5, lambda f: c.share(f, ACCENT, box) > 0.1)
    c.run()                             # prints PASS/FAIL, exits 1 on any fail
"""
import importlib.util
import io
import pathlib
import sys

import cairosvg
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


class Checker:
    def __init__(self, checks_file):
        scene_path = pathlib.Path(checks_file).parent / "scene.py"
        spec = importlib.util.spec_from_file_location("scene", scene_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.scene = mod
        self.cases = []

    def frame(self, t):
        png = cairosvg.svg2png(bytestring=self.scene.svg_at(t).encode(),
                               output_width=self.scene.WIDTH, output_height=self.scene.HEIGHT)
        return np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(float)

    @staticmethod
    def share(frame, color, box=None, tol=40):
        """Fraction of pixels in box (x0, y0, x1, y1) within tol of color."""
        f = frame if box is None else frame[box[1]:box[3], box[0]:box[2]]
        d = np.sqrt(((f - hex_rgb(color)) ** 2).sum(axis=2))
        return float((d < tol).mean())

    @staticmethod
    def diff(a, b, box=None):
        """Mean absolute per-channel difference between two frames (0..255)."""
        if box is not None:
            a = a[box[1]:box[3], box[0]:box[2]]
            b = b[box[1]:box[3], box[0]:box[2]]
        return float(np.abs(a - b).mean())

    def expect(self, name, t, fn):
        self.cases.append((name, t, fn))

    def run(self):
        fails = 0
        cache = {}
        for name, t, fn in self.cases:
            if t not in cache:
                cache[t] = self.frame(t)
            try:
                ok, detail = fn(cache[t]), ""
                if isinstance(ok, tuple):
                    ok, detail = ok
            except Exception as e:  # noqa: BLE001
                ok, detail = False, repr(e)
            fails += not ok
            print(f"{'PASS' if ok else 'FAIL'}  t={t:>5.2f}s  {name} {detail}")
        print(f"\n{len(self.cases) - fails}/{len(self.cases)} checks passed")
        sys.exit(1 if fails else 0)
