// Real-Chrome functional test for the hover image reveal list.
// Run: node shared/harness/run.mjs x presets/14-hover-image-list/browser.test.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const NAMES = ['Harbor House', 'Mill Street Lofts', 'Orchard Pavilion', 'Quarry Studio', 'Fieldstone Barn'];
const HREF = ['/work/harbor', '/work/mill', '/work/orchard', '/work/quarry', '/work/fieldstone'];
const COLORS = ['#C9B79C', '#9FB0A3', '#B89A8E', '#A7B4C2', '#D1BE86'];
const svg = c => 'data:image/svg+xml,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect width="400" height="300" fill="${c}"/></svg>`);
// image 5 is lazy like Squarespace: placeholder src, real file in data-src
const lazyFile = path.join(here, '.test-img5.svg');
fs.writeFileSync(lazyFile, `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect width="400" height="300" fill="${COLORS[4]}"/></svg>`);
const IMG_URL = [0, 1, 2, 3].map(i => svg(COLORS[i])).concat('file://' + lazyFile + '?format=1000w');

const fe = (id, area, inner) => `<div class="fe-block fe-block-${id}" style="grid-area:${area}">${inner}</div>`;
const imgBlock = (i, link) => {
  const img = i === 4
    ? `<img data-src="file://${lazyFile}" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="${NAMES[i]}">`
    : `<img src="${IMG_URL[i]}" alt="${NAMES[i]}">`;
  const inner = link ? `<a href="${link}">${img}</a>` : img;
  return `<div class="sqs-block image-block sqs-block-image" data-block-type="5"><div class="sqs-block-content"><div class="image-block-outer-wrapper"><figure class="sqs-block-image-figure">${inner}</figure></div></div></div>`;
};
// DOM order of the image blocks is scrambled on purpose: image 3 carries
// a click-through link to row 3, so it pairs by link; the rest pair in order.
const imgs = fe('i3', '2/18/5/25', imgBlock(2, HREF[2])) + [0, 1, 3, 4].map(i => fe('i' + i, '2/18/5/25', imgBlock(i))).join('');
const rows = NAMES.map((n, i) => `<p class=""><a href="${HREF[i]}">${n}</a></p>`).join('');
const section = `
<section class="page-section" data-section-id="work">
 <div class="section-background"></div>
 <div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${fe('code', '1/22/2/25', `<div class="sqs-block code-block sqs-block-code" data-block-type="23"><div class="sqs-block-content">${marker}</div></div>`)}
  ${fe('head', '1/1/2/13', '<div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><h4>Selected work</h4></div></div></div>')}
  ${fe('list', '2/1/5/17', `<div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content">${rows}</div></div></div>`)}
  ${imgs}
 </div></div></div>
</section>`;
const pagePath = path.join(here, '.test-page.html');
// mobile: Fluid Engine stacks blocks in its own mobile layout; mimic it with one column
const MOBILE = '<style>@media (max-width:767px){html .content-wrapper{padding:0 16px}html .fluid-engine{grid-template-columns:minmax(0,1fr)}html .fe-block{grid-area:auto!important}}</style>';
fs.writeFileSync(pagePath, mock.replace('<!--HEAD-->', MOBILE).replace('<!--BODY-->', section + '<div style="height:900px"></div>')
  .replace('</body>', '<script>window.SwtlHoverList={source:2}</script>' + snippet + '</body>'));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="1200" height="700"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }
const wait = (p, ms) => p.waitForTimeout(ms);

const rowBox = (p, i) => p.evaluate(i => { const r = document.querySelectorAll('.swtl-hl-row')[i].getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, cx: r.left + r.width / 2, cy: r.top + r.height / 2 }; }, i);
const floatState = p => p.evaluate(() => {
  const f = document.querySelector('.swtl-hl-float');
  if (!f) return null;
  const r = f.getBoundingClientRect(), m = new DOMMatrix(getComputedStyle(f).transform);
  const cur = f.querySelector('img.swtl-hl-cur');
  return {
    show: f.classList.contains('swtl-hl-show'), cx: r.left + r.width / 2, cy: r.top + r.height / 2,
    rot: Math.atan2(m.b, m.a) * 180 / Math.PI, tf: f.style.transform,
    src: cur ? cur.getAttribute('src') : null, op: +getComputedStyle(f.querySelector('.swtl-hl-frame')).opacity
  };
});
const rowOps = p => p.evaluate(() => [...document.querySelectorAll('.swtl-hl-row')].map(r => +(+getComputedStyle(r).opacity).toFixed(2)));
const inlineHeights = p => p.evaluate(() => [...document.querySelectorAll('.page-section, .content-wrapper, .content, .fluid-engine, .fe-block, .sqs-block, .sqs-block-content, .sqs-html-content, .sqs-html-content *')]
  .filter(e => /(^|;)\s*(min-|max-)?height\s*:/.test(e.getAttribute('style') || '')).length);

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;
  const errors = [];

  // 1. Desktop: rows built, pairing in order (link match first), image blocks hidden but in layout
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  let p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await wait(p, 300);
  const built = await p.evaluate(() => ({
    rows: document.querySelectorAll('.swtl-hl-row').length,
    arrows: [...document.querySelectorAll('.swtl-hl-arrow svg')].filter(s => s.getAttribute('stroke-width') === '2' && s.getAttribute('aria-hidden') === 'true').length,
    on: document.documentElement.classList.contains('swtl-hl-on'),
    head: !!document.querySelector('.fe-block-head .swtl-hl-row, .fe-block-head .swtl-hl-list'),
    srcs: [...document.querySelectorAll('.swtl-hl-frame img')].map(i => i.getAttribute('src')),
    hidden: [...document.querySelectorAll('.sqs-block.image-block')].map(b => { const f = b.closest('.fe-block'), cs = getComputedStyle(f); return f.classList.contains('swtl-hl-img') && cs.visibility === 'hidden' && cs.display !== 'none' && f.getBoundingClientRect().height > 0; }),
    floatAria: document.querySelector('.swtl-hl-float').getAttribute('aria-hidden'),
    text: [...document.querySelectorAll('.swtl-hl-link')].map(a => a.textContent)
  }));
  assert(built.on && built.rows === 5 && built.arrows === 5, `5 rows with Heroicons arrows (stroke 2, aria-hidden) built (${built.rows}/${built.arrows})`);
  assert(!built.head, 'data-source="2": the heading Text Block is left alone');
  assert(JSON.stringify(built.srcs) === JSON.stringify(IMG_URL), 'row ↔ image pairing in order (click-through link match first, lazy data-src resolved)');
  assert(built.hidden.every(Boolean), 'image blocks visibility:hidden, still in layout (not display:none)');
  assert(built.floatAria === 'true' && JSON.stringify(built.text) === JSON.stringify(NAMES), 'float is aria-hidden; link text unchanged for screen readers');

  // 2. Hover row 2: correct image, near the cursor, other rows dim
  let r = await rowBox(p, 1);
  await p.mouse.move(r.x + 300, r.cy, { steps: 6 });
  await wait(p, 900);
  let f = await floatState(p);
  assert(f.show && f.src === IMG_URL[1], 'hover row 2 → image 2 shown');
  assert(Math.hypot(f.cx - (r.x + 300), f.cy - r.cy) < 12, `image settles on the cursor (off by ${Math.hypot(f.cx - (r.x + 300), f.cy - r.cy).toFixed(1)}px)`);
  const ops = await rowOps(p);
  assert(ops[1] === 1 && [0, 2, 3, 4].every(i => ops[i] < 0.4), `non-hovered rows dim (${ops.join(',')})`);
  const arrow = await p.evaluate(() => { const a = document.querySelectorAll('.swtl-hl-arrow')[1], b = document.querySelectorAll('.swtl-hl-arrow')[0]; return { tx: new DOMMatrix(getComputedStyle(a).transform).m41, c: getComputedStyle(a).color, tx0: new DOMMatrix(getComputedStyle(b).transform).m41 }; });
  assert(Math.abs(arrow.tx - 5) < 0.01 && arrow.c === 'rgb(212, 85, 43)' && arrow.tx0 === 0, `hovered arrow: translateX(5px) + accent (${arrow.tx}px, ${arrow.c}); others at rest`);
  if (shots) await p.screenshot({ path: `${shots}/hl-hover.png` });

  // 3. Lerped follow + velocity tilt, then swap to row 4
  const r4 = await rowBox(p, 3);
  await p.mouse.move(r.x + 700, r4.cy, { steps: 2 });
  await wait(p, 60);
  f = await floatState(p);
  const lag = Math.hypot(f.cx - (r.x + 700), f.cy - r4.cy);
  assert(lag > 40 && Math.abs(f.rot) > 0.5, `follows with easing (lag ${lag.toFixed(0)}px) and tilts from speed (${f.rot.toFixed(2)}°)`);
  await wait(p, 1200);
  f = await floatState(p);
  assert(f.src === IMG_URL[3] && Math.hypot(f.cx - (r.x + 700), f.cy - r4.cy) < 12 && Math.abs(f.rot) < 0.3, `swaps to image 4, settles upright (rot ${f.rot.toFixed(2)}°)`);

  // 4. Leave hides it
  await p.mouse.move(5, 5, { steps: 3 });
  await wait(p, 700);
  f = await floatState(p);
  const ops2 = await rowOps(p);
  assert(!f.show && f.op === 0 && ops2.every(o => o === 1), 'leaving the list hides the image and un-dims rows');

  // 5. Keyboard focus shows the image (pinned beside the row)
  await p.evaluate(() => document.querySelectorAll('.swtl-hl-link')[2].focus());
  await wait(p, 700);
  f = await floatState(p);
  r = await rowBox(p, 2);
  assert(f.show && f.src === IMG_URL[2] && Math.abs(f.cy - r.cy) < 4 && f.cx > r.x + r.w * 0.5, 'keyboard focus → image 3 shown beside its row');
  await p.keyboard.press('Tab');
  await wait(p, 400);
  f = await floatState(p);
  assert(f.show && f.src === IMG_URL[3], 'Tab to next link → image 4');
  await p.evaluate(() => document.activeElement.blur());
  await wait(p, 300);
  assert(!(await floatState(p)).show, 'blur hides it');

  // 6. Editor class → full teardown, image blocks visible and editable
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await wait(p, 150);
  const ed = await p.evaluate(() => ({
    cls: document.querySelectorAll('[class*="swtl-hl"]').length, html: document.documentElement.className,
    added: document.querySelectorAll('.swtl-hl-float, .swtl-hl-arrow, .swtl-hl-thumb').length,
    vis: [...document.querySelectorAll('.sqs-block.image-block')].every(b => getComputedStyle(b.closest('.fe-block')).visibility === 'visible'),
    rows: document.querySelector('.fe-block-list .sqs-html-content').innerHTML
  }));
  assert(ed.cls === 0 && ed.added === 0 && !/swtl-hl/.test(ed.html), 'edit mode: every class and added element removed');
  assert(ed.vis, 'edit mode: image blocks visible');
  assert(ed.rows === rows, 'edit mode: Text Block markup restored byte for byte');
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await wait(p, 150);
  assert(await p.evaluate(() => document.querySelectorAll('.swtl-hl-row').length === 5 && document.querySelectorAll('.swtl-hl-float').length === 1), 'exit edit mode: re-initialised (one float, no duplicates)');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
  await wait(p, 100);
  assert(await p.evaluate(() => document.querySelectorAll('[class*="swtl-hl"]').length === 0), 'sqs-is-page-editing also tears down');
  await p.evaluate(() => document.body.classList.remove('sqs-is-page-editing'));
  await wait(p, 100);
  assert(await inlineHeights(p) === 0, 'no inline height on Squarespace elements');
  await ctx.close();

  // 7. Touch / no-hover → inline thumbnails, no float
  for (const [w, label] of [[1024, 'touch tablet 1024px'], [390, 'touch phone 390px']]) {
    ctx = await browser.newContext({ viewport: { width: w, height: 800 }, hasTouch: true, isMobile: w < 500 });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await wait(p, 300);
    const t = await p.evaluate(() => ({
      hover: matchMedia('(hover: hover)').matches,
      float: document.querySelectorAll('.swtl-hl-float').length,
      thumbs: [...document.querySelectorAll('.swtl-hl-row .swtl-hl-thumb img')].map(i => i.getAttribute('src')),
      seen: [...document.querySelectorAll('.swtl-hl-thumb')].every(e => e.getBoundingClientRect().width > 20),
      fit: [...document.querySelectorAll('.swtl-hl-row')].every(r => r.scrollWidth <= r.clientWidth + 1 && r.getBoundingClientRect().right <= document.querySelector('.fe-block-list').getBoundingClientRect().right + 1)
    }));
    assert(!t.hover && t.float === 0 && JSON.stringify(t.thumbs) === JSON.stringify(IMG_URL) && t.seen && t.fit, `${label}: no float, each row shows its own thumbnail, rows fit the block (fit ${t.fit})`);
    if (shots) await p.screenshot({ path: `${shots}/hl-touch-${w}.png` });
    await ctx.close();
  }
  // narrow desktop window (mouse, < 768px) → thumbnails too
  ctx = await browser.newContext({ viewport: { width: 700, height: 800 } });
  p = await ctx.newPage();
  await p.goto(url);
  await wait(p, 200);
  assert(await p.evaluate(() => !document.querySelector('.swtl-hl-float') && document.querySelectorAll('.swtl-hl-thumb').length === 5), 'mouse below 768px: thumbnail fallback');
  await p.setViewportSize({ width: 1280, height: 800 });
  await wait(p, 200);
  assert(await p.evaluate(() => document.querySelectorAll('.swtl-hl-float').length === 1 && !document.querySelector('.swtl-hl-thumb')), 'resize past 768px: switches to the floating image');
  await ctx.close();

  // 8. Inside a frame (the Squarespace editor) it never runs
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await wait(p, 500);
  assert(await p.frames()[1].evaluate(() => !document.querySelector('[class*="swtl-hl"]')), 'skipped inside editor frame');
  await ctx.close();

  // 9. Reduced motion: image fades in at a fixed spot, no follow, no tilt
  ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 800 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await wait(p, 200);
  r = await rowBox(p, 1);
  await p.mouse.move(r.x + 120, r.cy, { steps: 4 });
  await wait(p, 400);
  const a1 = await floatState(p);
  await p.mouse.move(r.x + 520, r.cy + 10, { steps: 4 });
  await wait(p, 400);
  const a2 = await floatState(p);
  const fr = await p.evaluate(() => { const cs = getComputedStyle(document.querySelector('.swtl-hl-frame')); return cs.transform + '|' + cs.clipPath; });
  assert(a1.show && a1.src === IMG_URL[1] && a1.tf === a2.tf && a1.rot === 0, 'reduced motion: image shown, does not follow the cursor, no tilt');
  assert(/^none\|(none|inset\(0)/.test(fr) && Math.abs(a1.cy - r.cy) < 4, `reduced motion: no scale/clip reveal, pinned to its row (${fr}, cy ${a1.cy} vs ${r.cy})`);
  await ctx.close();

  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  if (!process.env.KEEP) for (const x of [pagePath, frameHost, lazyFile]) fs.rmSync(x, { force: true });
}
