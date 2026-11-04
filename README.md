# SWTL Motion Presets

Reusable animation presets for Squarespace 7.1 (Fluid Engine) client sites.
Each preset is a paste-in snippet with an install guide, a video preview, and
automated checks.

Open [`catalog.html`](catalog.html) to browse all presets with hover-to-play
previews.

## Presets

| # | Preset | Category | Install |
|---|---|---|---|
| 01 | [Line-Draw Preloader](presets/01-line-draw-preloader/INSTALL.md) | Preloader | Header injection |
| 02 | [Split-Panel Preloader](presets/02-split-panel-preloader/INSTALL.md) | Preloader | Header injection |
| 03 | [Counter Preloader](presets/03-counter-preloader/INSTALL.md) | Preloader | Header injection |
| 04 | [Block Rise](presets/04-block-rise/INSTALL.md) | Section reveal | Footer + Code Block |
| 05 | [Mask Wipe](presets/05-mask-wipe/INSTALL.md) | Section reveal | Footer + Code Block |
| 06 | [Image Scale-Settle](presets/06-image-scale-settle/INSTALL.md) | Section reveal | Footer + Code Block |
| 07 | [Word Reveal](presets/07-word-reveal/INSTALL.md) | Text | Footer + Code Block |
| 08 | [Marquee Band](presets/08-marquee-band/INSTALL.md) | Text | Footer + Code Block |
| 09 | [Sticky Stack](presets/09-sticky-stack/INSTALL.md) | Scroll | Footer + Code Block |
| 10 | [Parallax Depth](presets/10-parallax-depth/INSTALL.md) | Scroll | Footer + Code Block |

## Shared rules

- Fluid Engine only. Everything stays editable and resizable in the Squarespace
  editor: no fixed heights, effects switch off while editing.
- `prefers-reduced-motion` shows the finished state.
- No libraries by default. Every class, id and keyframe is namespaced `swtl-`.
- Colors come from three variables. Set them once in Custom CSS:

```css
:root {
  --swtl-paper: #F4F1EA;
  --swtl-ink: #1F1E1C;
  --swtl-accent: #D4552B;
}
```

## Repo layout

```
presets/NN-slug/     snippet, INSTALL.md, preview.mp4/.gif, poster.png, tests
shared/              video renderer, scene kit, frame checker, Chrome harness
PRESET_SPEC.md       the build contract for new presets
build_catalog.py     regenerates catalog.html from presets/*/meta.json
```

## Working on a preset

```bash
pip install cairosvg svgpathtools numpy pillow fonttools --break-system-packages
python3 shared/render.py presets/01-line-draw-preloader/scene.py \
  --mp4 preview.mp4 --gif preview.gif --gif-width 1280 --poster poster.png
python3 presets/01-line-draw-preloader/checks.py        # timed frame checks
node shared/harness/run.mjs x "$(pwd)/presets/01-line-draw-preloader/browser.test.mjs"
python3 build_catalog.py
```

Video previews are rendered from Python scenes (SVG per frame → cairosvg →
ffmpeg) that mirror each snippet's timing, per the `website-animations` skill.
