---
name: swtl-motion-presets
description: Install, customize or build Squarespace 7.1 Fluid Engine motion presets (preloaders, scroll reveals, text effects, page transitions) from the SWTL motion catalog, with preview videos and automated checks. Use for any Squarespace animation, preloader or scroll effect.
---

# SWTL motion presets

This repo holds 18 paste-in animation presets for Squarespace 7.1 sites. Work in
the repo root. Rendering and checks run offline after setup.

## Setup (once)

```bash
pip install cairosvg svgpathtools numpy pillow fonttools --break-system-packages
ffmpeg -version          # must print a version
npm install playwright   # only for browser.test.mjs
```

## Pick the job

**A. Install an existing preset on a client site**
1. Open `catalog.html` or the table in `README.md` and pick the preset.
2. Read `presets/NN-slug/INSTALL.md`. Follow Part 1, then Part 2 for styling.
3. Set the three shared colors once in the site's Custom CSS:
   `--swtl-paper`, `--swtl-ink`, `--swtl-accent`. Use the client's brand values.
4. Give the user the exact snippet to paste and where it goes (Header
   injection, Footer injection, or a Code Block in the target section).
5. Remind the user to back up the current Custom CSS and Code Injection first.

**B. Customize a preset for one client**
1. Copy the snippet. Change only settings, `data-*` attributes, the
   `window.SwtlXxx = {…}` config, `--swtl-xx-*` variables or inline logo art.
2. For a client preview video, copy the preset's `scene.py`, swap colors/logo,
   then render:
   ```bash
   python3 shared/render.py path/to/scene.py --mp4 out.mp4 --gif out.gif \
     --gif-width 1280 --gif-fps 20 --poster out.png --poster-t 2.5
   ```

**C. Build a new preset**
Read `PRESET_SPEC.md` in full and copy the folder structure of
`presets/01-line-draw-preloader`. Then run all validation:
```bash
python3 presets/NN-slug/checks.py
node shared/harness/run.mjs x "$(pwd)/presets/NN-slug/browser.test.mjs"
python3 build_catalog.py
```
Review a contact sheet of 6+ frames by eye. Two-strike rule: if a preset fails
review twice, log why in `meta.json` notes, set `status: "blocked"`, move on.

## Hard rules (from PRESET_SPEC.md)

- Fluid Engine only. Never target Classic Editor markup.
- Editor-safe: do nothing inside the editor frame or in edit mode; tear down
  on edit and re-init on exit.
- Never set height, min-height, max-height, fixed width, grid placement, or
  section padding on Squarespace elements. Animate transform, opacity,
  clip-path and filter only.
- `prefers-reduced-motion` shows the final state.
- Namespace everything `swtl-xx-`. IIFE, `'use strict'`, ES5, no globals but
  the optional config object.
- No libraries by default. GSAP from cdnjs only when it clearly helps; document it.
- Arrows: Heroicons v2 outline SVG at stroke-width 2, slightly larger than
  default. Hover = `translateX(5px)` plus a color change. Never type `→`.
- Budgets: snippet ≤ 8 KB, MP4 ≤ 400 KB, GIF ≤ 2.5 MB.
