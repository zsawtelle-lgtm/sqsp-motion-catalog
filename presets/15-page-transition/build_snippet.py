"""Writes snippets/header-injection.html with the timing constants and easing
curves from timing.py inlined.
Run after changing timing.py:  python3 build_snippet.py
"""
import json
import pathlib

import timing as m

HERE = pathlib.Path(__file__).resolve().parent
TIMING = {k: getattr(m, k) for k in (
    "IN_DUR", "OUT_DUR", "HOLD", "LABEL_IN_AT", "LABEL_IN_DUR", "LABEL_RISE",
    "LABEL_OUT_DUR", "NAV_GRACE")}
out = (HERE / "snippet.template.html").read_text()
out = (out.replace("__TIMING__", json.dumps(TIMING, separators=(", ", ": ")).replace('"', ""))
          .replace("__EASE_WIPE__", m.css(m.EASE_WIPE))
          .replace("__EASE_LABEL__", m.css(m.EASE_LABEL)))
dst = HERE / "snippets" / "header-injection.html"
dst.parent.mkdir(exist_ok=True)
dst.write_text(out)
print(f"wrote {dst} ({len(out.encode()) / 1024:.1f} KB)")
