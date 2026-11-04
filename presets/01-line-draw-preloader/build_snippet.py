"""Writes snippets/header-injection.html with the placeholder lockup inlined.
Run after changing mark.py:  python build_snippet.py
"""
import pathlib

import mark as m

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = (HERE / "snippet.template.html").read_text()
out = TEMPLATE.replace("__MARKUP__", m.svg_markup())
dst = HERE / "snippets" / "header-injection.html"
dst.parent.mkdir(exist_ok=True)
dst.write_text(out)
print(f"wrote {dst} ({len(out.encode()) / 1024:.1f} KB)")
