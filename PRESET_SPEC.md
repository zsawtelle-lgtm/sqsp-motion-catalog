# Preset spec — how every preset in this catalog is built

Read this before adding or changing a preset. `presets/01-line-draw-preloader`
is the reference implementation: copy its structure, not its content.

## Folder contract

```
presets/NN-slug/
  INSTALL.md            Part 1 Basic install → Part 2 Styling → Part 3 For developers → Part 4 Support
  meta.json             feeds catalog.html (see 01 for the fields)
  snippets/*.html       exactly what gets pasted into Squarespace
  scene.py              video scene (DURATION, WIDTH=1280, HEIGHT=720, svg_at(t))
  checks.py             ≥5 timed frame assertions, one per beat (shared/check.py)
  browser.test.mjs      real-Chrome functional test (shared/harness)
  preview.mp4           1280×720, 30fps, 3–6s
  preview.gif           1280 wide, 20fps (same scene)
  poster.png            the strongest frame, 1280×720
```

Render: `python3 shared/render.py presets/NN-slug/scene.py --mp4 … --gif … --gif-width 1280 --gif-fps 20 --poster … --poster-t …`
Checks: `python3 presets/NN-slug/checks.py`
Browser: `node shared/harness/run.mjs x presets/NN-slug/browser.test.mjs` (Chrome is `/usr/bin/google-chrome`, Playwright at `/opt/npm-tools/node_modules/playwright`).

## Hard rules (every snippet)

**Squarespace 7.1, Fluid Engine only.** Never target Classic Editor markup.
Fluid Engine DOM:

```
section.page-section[data-section-id]
  .section-background
  .content-wrapper > .content > .fluid-engine        (CSS grid)
    .fe-block  (grid item; position via grid-area)
      .sqs-block.html-block  > .sqs-block-content > .sqs-html-content > h1,h2,h3,h4,p
      .sqs-block.image-block > .sqs-block-content > … img
      .sqs-block.button-block / .code-block / …
```

**Editor-safe.** The site must stay fully editable and resizable in the
Squarespace editor, not only on the published view.
- Do nothing when framed (`window.self !== window.top`) or when
  `body.sqs-edit-mode-active` / `body.sqs-is-page-editing` is present. Watch
  body classes with a MutationObserver: on edit, tear down (remove every class
  and inline style you added); on exit, re-init.
- Never set `height`, `min-height`, `max-height`, fixed `width`, or grid
  placement on Squarespace elements. Animate `transform`, `opacity`,
  `clip-path`, `filter` only.
- Hidden starting states come from a class the script adds to `<html>` only
  after it decides to run. If the script fails or is skipped, content shows.

**Activation.** Sitewide behavior → Code Injection (Header for preloaders,
Footer for in-page effects). Per-section targeting → a Code Block in that
section holding a marker like `<div data-swtl-xx hidden></div>`; the script uses
`closest('section.page-section')`. Optional `data-*` attributes on the marker
override settings. A config object `window.SwtlXxx = {…}` placed above the
snippet overrides defaults.

**Accessibility.** `prefers-reduced-motion: reduce` → final state, no motion.
Decorative duplicates (marquee copies, etc.) get `aria-hidden="true"`.
Never hide real text from screen readers.

**Namespace** every id, class, keyframe, CSS variable, data attribute and
storage key with the preset prefix (`swtl-xx-`). IIFE + `'use strict'`, ES5
syntax (`var`, `function`), no globals except the optional config object.

**Dependencies.** None preferred. GSAP (+ ScrollTrigger) from cdnjs is
allowed only if it clearly simplifies the effect; document it.

**Colors.** Shared variables with fallbacks — never hard-coded alone:
`var(--swtl-paper, #F4F1EA)` · `var(--swtl-ink, #1F1E1C)` · `var(--swtl-accent, #D4552B)`.
Preset-specific knobs are `--swtl-xx-*` variables.

**Arrows.** Never type `→`. Use the Heroicons v2 outline arrow (same set as
Will Myers' toolkit) at stroke-width 2:
`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg>`
sized slightly larger than default. Hover: `translateX(5px)` + color change.

**Weight budget.** Snippet ≤ 8 KB unminified (preloaders with inline logo
art may exceed; say why in meta.json). MP4 ≤ 400 KB, GIF ≤ 2.5 MB.

## Video scenes

- Use `shared/scene_kit.py`: palette, `seg()`/eases (match the CSS curves),
  outlined Inter text (`text_svg`, `text_paths` with real glyph lengths), mock
  7.1 page parts (`site_header`, `hero`, `image_tile`, `body_lines`, `button`),
  the Heroicons `arrow()`.
- The scene mirrors the snippet's timing beat-for-beat. Keep shared timing
  constants in one module both read (see 01's `mark.py`) or copy values verbatim.
- cairosvg ignores `pathLength` — use real lengths.
- Clip in local coordinates (clip-path on an inner group).
- In-page effects: show the effect in page context (simulate scroll by
  translating the page group). The last frame should be the resting state.

## Validation (before marking a preset done)

1. `checks.py` passes (≥5 beats, numeric pixel checks).
2. `browser.test.mjs` passes in real Chrome: effect applies, editor-frame
   guard, edit-mode class teardown (in-page presets), reduced motion, no page
   errors, no inline `height` written on any Squarespace element.
3. Contact sheet of 6+ frames reviewed by eye.
4. Two-strike rule: if a preset fails review twice, stop, log why in
   meta.json `notes`, set `status: "blocked"`, move on.
