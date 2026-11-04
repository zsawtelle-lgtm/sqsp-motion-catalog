"""Builds catalog.html from presets/*/meta.json.

    python3 build_catalog.py

The page is self-contained (inline CSS/JS, data inlined); preview media are
referenced relatively (presets/NN-slug/preview.mp4), so it works from the
repo root, GitHub Pages, or a published artifact that carries the media.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>')
REPO = "https://github.com/zsawtelle-lgtm/sqsp-motion-catalog/blob/main/"


def card(m):
    slug = m["slug"]
    tags = "".join(f"<li>{html.escape(t)}</li>" for t in m.get("best_for", []))
    status = m.get("status", "beta")
    badge = "" if status == "stable" else f'<span class="badge badge--{status}">{status}</span>'
    return f'''
    <article class="card" data-cat="{html.escape(m["category"])}">
      <div class="media">
        <video src="presets/{slug}/preview.mp4" poster="presets/{slug}/poster.png"
               muted loop playsinline preload="none" aria-label="{html.escape(m["name"])} preview"></video>
        <span class="num">{html.escape(m["id"])}</span>{badge}
      </div>
      <div class="body">
        <p class="cat">{html.escape(m["category"])}</p>
        <h2>{html.escape(m["name"])}</h2>
        <p class="use">{html.escape(m["use"])}</p>
        <ul class="tags" aria-label="Best for">{tags}</ul>
        <div class="foot">
          <span class="install">{html.escape(m["install"])}</span>
          <a class="link" href="{REPO}presets/{slug}/INSTALL.md">Install guide {ARROW}</a>
        </div>
      </div>
    </article>'''


def main():
    metas = []
    for p in sorted(ROOT.glob("presets/*/meta.json")):
        m = json.loads(p.read_text())
        m["slug"] = p.parent.name
        metas.append(m)
    cats = []
    for m in metas:
        if m["category"] not in cats:
            cats.append(m["category"])
    chips = '<button class="chip is-on" data-filter="all">All</button>' + "".join(
        f'<button class="chip" data-filter="{html.escape(c)}">{html.escape(c)}</button>' for c in cats)
    page = (ROOT / "catalog.template.html").read_text()
    page = page.replace("__COUNT__", str(len(metas))).replace("__CHIPS__", chips).replace(
        "__CARDS__", "".join(card(m) for m in metas))
    # Repo / GitHub Pages copy: a full document.
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + page.replace("<div class=\"wrap\">", "</head>\n<body>\n<div class=\"wrap\">", 1)
            + "\n</body>\n</html>\n")
    (ROOT / "catalog.html").write_text(full)
    # Artifact copy: body content only (the host adds the document skeleton).
    (ROOT / ".artifact").mkdir(exist_ok=True)
    (ROOT / ".artifact" / "index.html").write_text(page)
    print(f"catalog.html: {len(metas)} presets, {len(full.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
