"""Writes snippets/header-injection.html with the timing from timing.py
inlined, so the snippet and the video run the same numbers.
Run after changing timing.py or the template:  python3 build_snippet.py
"""
import pathlib

import timing as T

HERE = pathlib.Path(__file__).resolve().parent
out = (HERE / "snippet.template.html").read_text()
subs = {
    "__MIN_SHOW_MS__": str(round(T.MIN_SHOW * 1000)),
    "__MAX_WAIT_MS__": str(round(T.MAX_WAIT * 1000)),
    "__CRAWL__": str(T.CRAWL),
    "__TAU__": str(T.TAU), "__FINISH__": str(T.FINISH), "__HOLD__": str(T.HOLD),
    "__ROLL__": str(T.ROLL), "__WIPE_DELAY__": str(T.WIPE_DELAY), "__WIPE__": str(T.WIPE),
    "__EASE_ROLL__": T.EASE_ROLL, "__EASE_WIPE__": T.EASE_WIPE,
}
for a, b in subs.items():
    out = out.replace(a, b)
assert "__" not in out.split("<script>")[1].replace("__proto__", ""), "unfilled placeholder"
dst = HERE / "snippets" / "header-injection.html"
dst.parent.mkdir(exist_ok=True)
dst.write_text(out)
print(f"wrote {dst} ({len(out.encode()) / 1024:.1f} KB)")
