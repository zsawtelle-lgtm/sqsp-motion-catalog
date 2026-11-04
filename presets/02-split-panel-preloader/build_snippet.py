"""Writes snippets/header-injection.html with the placeholder lockup and the
timing constants from mark.py inlined.
Run after changing mark.py:  python3 build_snippet.py
"""
import json
import pathlib

import mark as m

HERE = pathlib.Path(__file__).resolve().parent
TIMING = {k: getattr(m, k) for k in (
    "LOGO_IN_AT", "LOGO_IN_DUR", "LOGO_RISE", "LINE_AT", "LINE_DUR", "PULSE_PERIOD",
    "HOLD", "LOGO_OUT_DUR", "PART_LEAD", "PART_DUR", "PART_STAGGER")}
out = (HERE / "snippet.template.html").read_text()
out = (out.replace("__MARKUP__", m.svg_markup())
          .replace("__TIMING__", json.dumps(TIMING, separators=(", ", ": ")).replace('"', ""))
          .replace("__EASE_PART__", m.css(m.EASE_PART))
          .replace("__EASE_IN__", m.css(m.EASE_IN))
          .replace("__EASE_LINE__", m.css(m.EASE_LINE))
          .replace("__EASE_OUT__", m.css(m.EASE_OUT)))
dst = HERE / "snippets" / "header-injection.html"
dst.parent.mkdir(exist_ok=True)
dst.write_text(out)
print(f"wrote {dst} ({len(out.encode()) / 1024:.1f} KB)")
