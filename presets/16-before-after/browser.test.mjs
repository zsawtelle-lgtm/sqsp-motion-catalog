// Real-Chrome functional test for the before / after slider.
// Run: node ../../shared/harness/run.mjs x "$(pwd)/browser.test.mjs"
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

// local generated PNGs (a gray "before" and a warm "after" photo stand-in)
const png = (name, rgb) => {
  const p = path.join(here, `.test-${name}.png`);
  execFileSync('python3', ['-c', `from PIL import Image, ImageDraw
im = Image.new('RGB', (900, 600), tuple(${JSON.stringify(rgb)}))
d = ImageDraw.Draw(im); d.rectangle([80, 380, 420, 560], fill=(60, 60, 60)); im.save(${JSON.stringify(p)})`]);
  return p;
};
const IMGS = { b1: png('b1', [150, 148, 144]), a1: png('a1', [233, 223, 205]),
               b2: png('b2', [90, 110, 130]),  a2: png('a2', [212, 85, 43]) };

// Fluid Engine image block, as Squarespace 7.1 renders it (crop = container aspect + object-fit)
const img = (area, file, id, alt, ratio = '3/2') => `<div class="fe-block fe-block-${id}" style="grid-area:${area}">
  <div class="sqs-block image-block sqs-block-image" id="block-${id}"><div class="sqs-block-content">
   <div class="fluid-image-component-root"><div class="fluid-image-animation-wrapper"><div class="fluid-image-container sqs-image-content" style="overflow:hidden;position:relative;aspect-ratio:${ratio}">
    <div class="content-fill"><img src="file://${file}" alt="${alt}" style="display:block;width:100%;height:100%;object-fit:cover;object-position:50% 50%"></div>
   </div></div></div></div></div></div>`;
const txt = (area, id, h) => `<div class="fe-block fe-block-${id}" style="grid-area:${area}">
  <div class="sqs-block html-block sqs-block-html" id="block-${id}"><div class="sqs-block-content"><div class="sqs-html-content"><h2>${h}</h2><p>Body copy.</p></div></div></div></div>`;
const code = (area, m) => `<div class="fe-block" style="grid-area:${area}"><div class="sqs-block code-block sqs-block-code"><div class="sqs-block-content">${m}</div></div></div>`;

// s1: default pairing (marker tucked bottom-left; after block in DOM BEFORE the before block,
//     but placed lower on the grid -> reading order must win). s2: explicit data-pair, alt labels.
const BODY = (withMarkers) => `
<section class="page-section" data-section-id="s0"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${txt('1/1/2/24', 'h0', 'Intro section (no marker)')}
  ${img('2/1/4/12', IMGS.b2, 'i0', 'unmarked')}
</div></div></div></section>
<div class="test-spacer" style="height:1200px"></div>
<section class="page-section" data-section-id="s1"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${txt('1/1/2/10', 't1', 'Our work')}
  ${img('6/14/9/25', IMGS.a1, 'i2', 'Kitchen after')}
  ${img('1/12/6/25', IMGS.b1, 'i1', 'Kitchen before')}
  ${withMarkers ? code('9/1/10/3', marker) : ''}
</div></div></div></section>
<div class="test-spacer" style="height:1200px"></div>
<section class="page-section" data-section-id="s2"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${img('1/1/4/12', IMGS.b2, 'i3', 'Yard before', '4/3')}
  ${img('1/13/4/25', IMGS.a2, 'i4', 'Yard after', '1/1')}
  ${img('4/1/6/12', IMGS.a1, 'i5', 'extra')}
  ${withMarkers ? code('6/1/7/3', '<div data-swtl-beforeafter data-pair="block-i3, #block-i4" data-labels="alt" data-hint="false" data-start="30" hidden></div>') : ''}
</div></div></div></section>
<div class="test-spacer" style="height:900px"></div>`;

const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--BODY-->', BODY(true)).replace('</body>', snippet + '\n</body>'));
const plainPath = path.join(here, '.test-plain.html');
fs.writeFileSync(plainPath, mock.replace('<!--BODY-->', BODY(true)));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="1000" height="700"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

const st = (s => {
  const b = document.querySelector(s); const ui = b.querySelector('.swtl-ba-ui');
  const h = b.querySelector('.swtl-ba-handle'); const af = b.querySelector('.swtl-ba-after');
  return { ui: !!ui, now: h ? +h.getAttribute('aria-valuenow') : null,
    clip: af ? getComputedStyle(af).clipPath : null,
    hr: h ? h.getBoundingClientRect().toJSON() : null,
    ur: ui ? ui.getBoundingClientRect().toJSON() : null };
});
const clipPct = (c) => { const m = /inset\(0px 0px 0px ([\d.]+)%\)/.exec(c || ''); return m ? parseFloat(m[1]) : NaN; };
const scrollTo = (p, id) => p.evaluate(i => {
  const r = document.getElementById(i).getBoundingClientRect();
  window.scrollTo(0, window.scrollY + r.top - 100);
}, id);
const rects = (p) => p.evaluate(() => ['i1', 'i2', 'i3', 'i4'].map(i => {
  const r = document.getElementById('block-' + i).getBoundingClientRect(); return [r.width, r.height]; }));
const inlineSizes = (p) => p.evaluate(() => [...document.querySelectorAll('.page-section, .fe-block, .sqs-block, .sqs-block-content, .sqs-block-content *')]
  .filter(e => /(^|;|\s)(min-|max-)?(height|width)\s*:/.test(e.getAttribute('style') || '') && !e.matches('img, .test-spacer'))
  .map(e => e.className));
// sample aria-valuenow over a period (rAF-paced)
const sample = (p, sel, ms) => p.evaluate(([s, ms]) => new Promise(res => {
  const h = document.querySelector(s + ' .swtl-ba-handle'), out = [], t0 = performance.now();
  (function f() { out.push(+h.getAttribute('aria-valuenow')); if (performance.now() - t0 < ms) requestAnimationFrame(f); else res(out); })();
}), [sel, ms]);

export default async function (browser) {
  const url = 'file://' + pagePath;
  const errors = [];

  // 0. Reference sizes without the script
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  let p = await ctx.newPage();
  await p.goto('file://' + plainPath);
  await p.waitForTimeout(150);
  const plain = await rects(p);
  await ctx.close();

  // 1. Pairing, structure, hint
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(150);
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-ba-on')), 'html.swtl-ba-on added');
  const pair = await p.evaluate(() => ({
    uis: document.querySelectorAll('.swtl-ba-ui').length,
    i1: !!document.querySelector('#block-i1 .swtl-ba-ui'), i2ui: !!document.querySelector('#block-i2 .swtl-ba-ui'),
    i2vis: getComputedStyle(document.getElementById('block-i2')).visibility,
    clone: (document.querySelector('#block-i1 .swtl-ba-after img') || {}).src || '',
    cloneAlt: (document.querySelector('#block-i1 .swtl-ba-after img') || {}).alt,
    i0: !!document.querySelector('#block-i0 [class*="swtl-ba"]'),
    i5: getComputedStyle(document.getElementById('block-i5')).visibility,
    labels: [...document.querySelectorAll('#block-i1 .swtl-ba-label')].map(l => l.textContent),
    alt: [...document.querySelectorAll('#block-i3 .swtl-ba-label')].map(l => l.textContent),
    role: document.querySelector('#block-i1 .swtl-ba-handle').getAttribute('role'),
    tab: document.querySelector('#block-i1 .swtl-ba-handle').tabIndex,
    icon: document.querySelector('#block-i1 .swtl-ba-handle svg').getAttribute('stroke-width')
  }));
  assert(pair.uis === 2, `two sliders built (got ${pair.uis})`);
  assert(pair.i1 && !pair.i2ui, 'reading order: the upper block (i1) is "before", even though i2 comes first in the DOM');
  assert(pair.i2vis === 'hidden', 'after block visually hidden while active');
  assert(/\.test-a1\.png$/.test(pair.clone) && pair.cloneAlt === 'Kitchen after', 'after image layered into the before block (alt kept)');
  assert(!pair.i0, 'unmarked section untouched');
  assert(pair.i5 === 'visible', 'third image block in a data-pair section left alone');
  assert(pair.labels.join('|') === 'Before|After', 'labels from marker data attributes: ' + pair.labels.join('|'));
  assert(pair.alt.join('|') === 'Yard before|Yard after', 'data-labels="alt" uses alt text: ' + pair.alt.join('|'));
  assert(pair.role === 'slider' && pair.tab === 0 && pair.icon === '2', 'handle is a focusable role="slider" with a stroke-2 icon');
  const s3 = await p.evaluate(st, '#block-i3');
  assert(s3.now === 30 && Math.abs(clipPct(s3.clip) - 30) < 0.1, 'data-pair + data-start="30" applied: ' + s3.clip);
  const withScript = await rects(p);
  assert(JSON.stringify(withScript) === JSON.stringify(plain),
    'block sizes unchanged vs no script ' + JSON.stringify(withScript) + ' vs ' + JSON.stringify(plain));
  const ui1 = await p.evaluate(st, '#block-i1');
  const host = await p.evaluate(() => document.querySelector('#block-i1 .fluid-image-container').getBoundingClientRect().toJSON());
  assert(Math.abs(ui1.ur.width - host.width) < 0.5 && Math.abs(ui1.ur.height - host.height) < 0.5, 'overlay fills the image crop exactly');
  assert(ui1.now === 50 && Math.abs(clipPct(ui1.clip) - 50) < 0.1, 'starts at 50%: ' + ui1.clip);

  // hint: plays once on scroll-in
  await scrollTo(p, 'block-i1');
  const hint = await sample(p, '#block-i1', 1700);
  const lo = Math.min(...hint);
  assert(lo >= 34 && lo <= 36, `hint eases to 35% (min ${lo})`);
  assert(hint[hint.length - 1] === 50, 'hint returns to 50%');
  assert(hint.indexOf(lo) > 3 && hint.slice(0, 3).every(v => v >= 48), 'hint starts from 50%');
  const s3b = await p.evaluate(st, '#block-i3');
  assert(s3b.now === 30, 'data-hint="false" section did not move');

  // 2. Mouse drag
  const r = (await p.evaluate(st, '#block-i1')).ur;
  const cy = r.y + r.height / 2;
  await p.mouse.move(r.x + r.width * 0.5, cy);
  await p.mouse.down();
  await p.mouse.move(r.x + r.width * 0.65, cy, { steps: 4 });
  await p.mouse.move(r.x + r.width * 0.8, cy, { steps: 4 });
  const m1 = await p.evaluate(st, '#block-i1');
  assert(Math.abs(m1.now - 80) <= 1 && Math.abs(clipPct(m1.clip) - 80) < 1, `mouse drag to 80%: aria ${m1.now}, ${m1.clip}`);
  assert(Math.abs(m1.hr.x + m1.hr.width / 2 - (r.x + r.width * 0.8)) < 2, 'handle follows the pointer');
  assert(await p.evaluate(() => document.querySelector('#block-i1 .swtl-ba-ui').classList.contains('swtl-ba-drag')), 'drag class while pressed');
  await p.mouse.move(r.x - 40, cy, { steps: 3 });           // beyond the edge -> clamps
  const m2 = await p.evaluate(st, '#block-i1');
  assert(m2.now === 0, 'drag past the edge clamps to 0 (pointer capture)');
  await p.mouse.up();
  await p.mouse.move(r.x + r.width * 0.9, cy);
  const m3 = await p.evaluate(st, '#block-i1');
  assert(m3.now === 0, 'moving without a press does nothing');
  const lbOff = await p.evaluate(() => document.querySelector('#block-i1 .swtl-ba-lb').classList.contains('swtl-ba-off'));
  assert(lbOff, '"Before" label fades when the before side is nearly closed');
  await p.mouse.click(r.x + r.width * 0.25, cy);
  assert((await p.evaluate(st, '#block-i1')).now === 25, 'click jumps the divider');

  // 3. Keyboard
  await p.focus('#block-i1 .swtl-ba-handle');
  await p.keyboard.press('ArrowRight');
  let kv = (await p.evaluate(st, '#block-i1')).now;
  assert(kv === 30, 'ArrowRight +5 (' + kv + ')');
  await p.keyboard.press('ArrowLeft'); await p.keyboard.press('ArrowLeft');
  kv = (await p.evaluate(st, '#block-i1')).now;
  assert(kv === 20, 'ArrowLeft -5 (' + kv + ')');
  await p.keyboard.press('End');
  kv = await p.evaluate(st, '#block-i1');
  assert(kv.now === 100 && clipPct(kv.clip) === 100, 'End = 100');
  await p.keyboard.press('Home');
  assert((await p.evaluate(st, '#block-i1')).now === 0, 'Home = 0');
  await p.keyboard.press('ArrowLeft');
  assert((await p.evaluate(st, '#block-i1')).now === 0, 'keyboard clamps at 0');
  const vt = await p.evaluate(() => document.querySelector('#block-i1 .swtl-ba-handle').getAttribute('aria-valuetext'));
  assert(vt === '0% before', 'aria-valuetext updated: ' + vt);

  const sizes = await inlineSizes(p);
  assert(sizes.length === 0, 'no inline height/width written on Squarespace elements ' + sizes.join(','));
  const after = await rects(p);
  assert(JSON.stringify(after) === JSON.stringify(plain), 'block sizes unchanged after interaction');
  await ctx.close();

  // 4. Touch drag (hasTouch context, real touch events via CDP)
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, hasTouch: true, isMobile: false });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(150);
  await scrollTo(p, 'block-i1');
  await p.waitForTimeout(1700);                             // let the hint finish
  const tr = (await p.evaluate(st, '#block-i1')).ur;
  const cdp = await ctx.newCDPSession(p);
  const touch = (type, x) => cdp.send('Input.dispatchTouchEvent', { type,
    touchPoints: type === 'touchEnd' ? [] : [{ x, y: tr.y + tr.height / 2 }] });
  await touch('touchStart', tr.x + tr.width * 0.5);
  for (let i = 1; i <= 8; i++) { await touch('touchMove', tr.x + tr.width * (0.5 - 0.04 * i)); }
  await touch('touchEnd');
  await p.waitForTimeout(50);
  const t1 = await p.evaluate(st, '#block-i1');
  assert(Math.abs(t1.now - 18) <= 1 && Math.abs(clipPct(t1.clip) - 18) < 1, `touch drag to 18%: aria ${t1.now}, ${t1.clip}`);
  await ctx.close();

  // 5. Edit mode: full teardown, both images visible; re-init on exit
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(150);
  await scrollTo(p, 'block-i1');
  await p.waitForTimeout(300);                              // mid-hint on purpose
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(80);
  const ed = await p.evaluate(() => ({
    on: document.documentElement.classList.contains('swtl-ba-on'),
    ui: document.querySelectorAll('.swtl-ba-ui').length,
    cls: document.querySelectorAll('[class*="swtl-ba"]').length,
    vis: ['i1', 'i2', 'i3', 'i4'].map(i => getComputedStyle(document.getElementById('block-' + i)).visibility),
    styles: [...document.querySelectorAll('.sqs-block, .fluid-image-container')].filter(e => /--swtl/.test(e.getAttribute('style') || '')).length
  }));
  assert(!ed.on && ed.ui === 0 && ed.cls === 0, 'edit mode: slider UI, classes and html class removed');
  assert(ed.vis.every(v => v === 'visible'), 'edit mode: both images of each pair visible ' + ed.vis.join(','));
  assert(ed.styles === 0, 'edit mode: no inline variables left on Squarespace elements');
  assert(JSON.stringify(await rects(p)) === JSON.stringify(plain), 'edit mode: sizes identical to no-script page');
  const hold = await sample(p, '#block-i1 .fluid-image-container', 0).catch(() => 'gone');
  assert(hold === 'gone', 'edit mode: hint animation stopped (no handle left)');
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(100);
  assert(await p.evaluate(() => document.querySelectorAll('.swtl-ba-ui').length === 2 &&
    getComputedStyle(document.getElementById('block-i2')).visibility === 'hidden'), 'leaving edit mode re-initialises');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
  await p.waitForTimeout(80);
  assert(await p.evaluate(() => !document.querySelector('.swtl-ba-ui')), 'sqs-is-page-editing also tears down');
  await ctx.close();

  // 6. Inside a frame (the Squarespace editor) it never runs
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  const inner = p.frames()[1];
  assert(await inner.evaluate(() => !document.documentElement.classList.contains('swtl-ba-on') &&
    !document.querySelector('.swtl-ba-ui') && getComputedStyle(document.getElementById('block-i2')).visibility === 'visible'),
    'skipped inside editor frame (both images visible)');
  await ctx.close();

  // 7. Reduced motion: no hint, slider still works
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, reducedMotion: 'reduce' });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(150);
  await scrollTo(p, 'block-i1');
  const rm = await sample(p, '#block-i1', 1500);
  assert(rm.every(v => v === 50), 'reduced motion: no hint animation (stays 50)');
  await p.focus('#block-i1 .swtl-ba-handle');
  await p.keyboard.press('ArrowLeft');
  assert((await p.evaluate(st, '#block-i1')).now === 45, 'reduced motion: keyboard still works');
  const rr = (await p.evaluate(st, '#block-i1')).ur;
  await p.mouse.move(rr.x + rr.width * 0.5, rr.y + rr.height / 2);
  await p.mouse.down();
  await p.mouse.move(rr.x + rr.width * 0.7, rr.y + rr.height / 2, { steps: 4 });
  await p.mouse.up();
  assert((await p.evaluate(st, '#block-i1')).now === 70, 'reduced motion: drag still works');
  await ctx.close();

  assert(errors.length === 0, 'no page errors (all runs) ' + errors.join(' | '));
}
