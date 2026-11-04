// Real-Chrome functional test for 10 · Parallax Depth Layers.
// Run: node ../../shared/harness/run.mjs "$(pwd)/.test-page.html" "$(pwd)/browser.test.mjs"
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const PX = 'data:image/svg+xml;utf8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900"><rect width="1600" height="900" fill="#CFC7B8"/></svg>');
const STYLE = `<style>
 .section-background{position:absolute;inset:0;z-index:0}
 .section-background img{width:100%;height:100%;object-fit:cover;display:block}
 .page-section .content-wrapper{position:relative;z-index:1}
 .spacer{height:1400px}
 .img{width:100%}
 .sqs-block-button-element{display:inline-block;padding:14px 24px;background:#1F1E1C;color:#F4F1EA;border-radius:23px}
</style>`;

// Realistic Fluid Engine section: bg image, two images, headline, button, marker code block.
function section(markerHtml) {
  return `<div class="spacer"></div>
<section class="page-section" data-section-id="px1" id="px">
 <div class="section-background"><img src="${PX}" alt=""></div>
 <div class="content-wrapper"><div class="content"><div class="fluid-engine">
  <div class="fe-block fe-a" style="grid-area:1/1/9/11"><div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><h1>Depth, quietly.</h1><p>Body copy.</p></div></div></div></div>
  <div class="fe-block fe-b" style="grid-area:1/13/12/25"><div class="sqs-block image-block"><div class="sqs-block-content"><div class="img"></div></div></div></div>
  <div class="fe-block fe-c" style="grid-area:9/1/12/7"><div class="sqs-block button-block"><div class="sqs-block-content"><a class="sqs-block-button-element" href="#">Get in touch</a></div></div></div>
  <div class="fe-block fe-d" style="grid-area:12/5/20/13"><div class="sqs-block image-block"><div class="sqs-block-content"><div class="img"></div></div></div></div>
  <div class="fe-block fe-m" style="grid-area:20/1/21/2"><div class="sqs-block code-block"><div class="sqs-block-content">${markerHtml}</div></div></div>
 </div></div></div>
</section>
<div class="spacer"></div>`;
}

function build(name, markerHtml, withSnippet = true) {
  const p = path.join(here, name);
  fs.writeFileSync(p, mock.replace('<!--HEAD-->', STYLE).replace('<!--BODY-->', section(markerHtml) + (withSnippet ? snippet : '')));
  return 'file://' + p;
}
const urlMain = build('.test-page.html', marker);
const urlClamp = build('.test-clamp.html', '<div data-swtl-parallax data-images="-2" data-max="80" hidden></div>');
const urlOverride = build('.test-override.html', '<div data-swtl-parallax data-blocks="1:0.3,4:0" hidden></div>');
const urlPlain = build('.test-plain.html', marker, false);
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="${urlMain}" width="1280" height="720"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }
const ty = (p, sel) => p.evaluate(s => {
  const el = document.querySelector(s); const m = getComputedStyle(el).transform;
  return m === 'none' ? 0 : new DOMMatrix(m).m42;
}, sel);
const IMG_B = '.fe-b .sqs-block', IMG_D = '.fe-d .sqs-block', TXT = '.fe-a .sqs-block', BTN = '.fe-c .sqs-block';
const scrollTo = async (p, y) => { await p.evaluate(y => window.scrollTo(0, y), y); await p.waitForTimeout(120); };
const centerY = p => p.evaluate(() => { const r = document.getElementById('px').getBoundingClientRect(); return r.top + scrollY + r.height / 2 - innerHeight / 2; });
const sizes = p => p.evaluate(() => [...document.querySelectorAll('#px .fe-block, #px .sqs-block')].map(e => e.offsetWidth + 'x' + e.offsetHeight).join(','));
const inlineHeights = p => p.evaluate(() => [...document.querySelectorAll('#px *')].filter(e => /height/.test(e.getAttribute('style') || '') && !e.classList.contains('fe-block')).length);
const anyTransforms = p => p.evaluate(() => [...document.querySelectorAll('#px *')].filter(e => e.style.transform).length);

export default async function (browser) {
  const errors = [];
  const ctxOpts = { viewport: { width: 1280, height: 720 } };

  // 1. Main behavior
  let ctx = await browser.newContext(ctxOpts);
  let p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.addInitScript(() => {
    window.__raf = 0; const r = window.requestAnimationFrame.bind(window);
    window.requestAnimationFrame = cb => r(t => { window.__raf++; cb(t); });
  });
  await p.goto(urlMain);
  await p.waitForTimeout(150);
  const c = await centerY(p);
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-px-on')), 'html.swtl-px-on added when it runs');
  await scrollTo(p, c - 300);
  const a1 = await ty(p, IMG_B), t1 = await ty(p, TXT), b1 = await ty(p, BTN);
  await scrollTo(p, c + 300);
  const a2 = await ty(p, IMG_B), t2 = await ty(p, TXT), b2 = await ty(p, BTN);
  assert(Math.abs(a1 - a2) > 40, `image block translateY changes with scroll (${a1.toFixed(1)} → ${a2.toFixed(1)})`);
  assert(a1 < 0 && a2 > 0, 'image drifts against scroll (slower than page)');
  assert(t1 === 0 && t2 === 0, `text block stays at 0 (${t1}, ${t2})`);
  assert(b1 > 0 && b2 < 0, `button floats faster than page (${b1.toFixed(1)}, ${b2.toFixed(1)})`);
  await scrollTo(p, c);
  assert(Math.abs(await ty(p, IMG_B)) < 3, 'section centered → image at its editor position (≈0)');
  const bgT = await p.evaluate(() => document.querySelector('#px .section-background img').style.transform);
  assert(/scale\(1\.12\)/.test(bgT), 'background img uses scale(1.12): ' + bgT);
  assert(await p.evaluate(() => getComputedStyle(document.querySelector('#px .section-background')).overflow === 'hidden'), 'background wrapper clips the oversize image');

  // sizes unchanged vs a page without the snippet
  const sz = await sizes(p);
  const pp = await ctx.newPage();
  await pp.goto(urlPlain);
  const szRef = await sizes(pp);
  await pp.close();
  assert(sz === szRef, 'block sizes identical to page without the snippet');
  assert(await inlineHeights(p) === 0, 'no inline height written on any Squarespace element');

  // rAF stops offscreen
  await p.evaluate(() => window.scrollBy(0, 40));
  await p.waitForTimeout(50);
  const rOn0 = await p.evaluate(() => window.__raf);
  for (let i = 0; i < 5; i++) { await p.evaluate(() => window.scrollBy(0, 30)); await p.waitForTimeout(40); }
  const rOn = (await p.evaluate(() => window.__raf)) - rOn0;
  assert(rOn > 3, `rAF runs while scrolling near the section (${rOn} frames)`);
  await scrollTo(p, 0);
  await p.waitForTimeout(600);
  const tr0 = await p.evaluate(() => document.querySelector('.fe-b .sqs-block').style.transform);
  const r0 = await p.evaluate(() => window.__raf);
  for (let i = 0; i < 5; i++) { await p.evaluate(i => window.scrollTo(0, 10 + i * 20), i); await p.waitForTimeout(60); }
  await p.waitForTimeout(300);
  const rOff = (await p.evaluate(() => window.__raf)) - r0;
  const tr1 = await p.evaluate(() => document.querySelector('.fe-b .sqs-block').style.transform);
  assert(rOff === 0, `rAF stopped while section is offscreen (${rOff} frames during scroll)`);
  assert(tr0 === tr1, 'transforms stable offscreen');
  await scrollTo(p, c);
  await p.waitForTimeout(800);
  const rIdle0 = await p.evaluate(() => window.__raf);
  await p.waitForTimeout(400);
  assert((await p.evaluate(() => window.__raf)) - rIdle0 === 0, 'rAF sleeps when on screen but idle');

  // editor class → full teardown, then re-init
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(100);
  const left = await p.evaluate(() => ({
    t: [...document.querySelectorAll('#px *')].filter(e => e.style.transform).length,
    c: document.querySelectorAll('[class*="swtl-px-"]').length,
    h: document.documentElement.classList.contains('swtl-px-on')
  }));
  assert(left.t === 0 && left.c === 0 && !left.h, `edit mode: no transforms / classes left (${JSON.stringify(left)})`);
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await scrollTo(p, c - 300);
  await p.waitForTimeout(100);
  assert((await ty(p, IMG_B)) < -10, 'exit edit mode → re-initialised');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
  await p.waitForTimeout(100);
  assert(await anyTransforms(p) === 0, 'sqs-is-page-editing also tears down');
  await ctx.close();

  // 2. Clamp
  ctx = await browser.newContext(ctxOpts);
  p = await ctx.newPage(); p.on('pageerror', e => errors.push(e.message));
  await p.goto(urlClamp); await p.waitForTimeout(100);
  const cc = await centerY(p);
  await scrollTo(p, cc - 400);
  const k1 = await ty(p, IMG_B);
  await scrollTo(p, cc + 400);
  const k2 = await ty(p, IMG_D);
  assert(Math.abs(Math.abs(k1) - 80) < 0.5 && Math.abs(Math.abs(k2) - 80) < 0.5, `offsets clamped to ±80px with speed -2 (${k1}, ${k2})`);
  await ctx.close();

  // 3. Per-block override (visual order: 1 = text (top-left), 2 = image B, 3 = button, 4 = image D)
  ctx = await browser.newContext(ctxOpts);
  p = await ctx.newPage(); p.on('pageerror', e => errors.push(e.message));
  await p.goto(urlOverride); await p.waitForTimeout(100);
  const co = await centerY(p);
  await scrollTo(p, co - 200);
  const oT = await ty(p, TXT), oB = await ty(p, IMG_B), oD = await ty(p, IMG_D);
  assert(oT > 50, `override 1:0.3 moves the text block (${oT.toFixed(1)})`);
  assert(oB < 0, `non-overridden image keeps default speed (${oB.toFixed(1)})`);
  assert(oD === 0, `override 4:0 pins image D (${oD})`);
  await ctx.close();

  // 4. Mobile disable
  ctx = await browser.newContext({ viewport: { width: 600, height: 900 } });
  p = await ctx.newPage(); p.on('pageerror', e => errors.push(e.message));
  await p.goto(urlMain); await p.waitForTimeout(100);
  await scrollTo(p, 1200);
  assert(await anyTransforms(p) === 0 && !(await p.evaluate(() => document.documentElement.classList.contains('swtl-px-on'))), 'below 768px: no transforms');
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.waitForTimeout(400);
  await scrollTo(p, (await centerY(p)) - 300);
  assert((await ty(p, IMG_B)) < -10, 'resize to desktop → enabled');
  await p.setViewportSize({ width: 700, height: 720 });
  await p.waitForTimeout(400);
  assert(await anyTransforms(p) === 0, 'resize back to mobile → torn down');
  await ctx.close();

  // 5. Editor iframe guard
  ctx = await browser.newContext(ctxOpts);
  p = await ctx.newPage();
  await p.goto('file://' + frameHost); await p.waitForTimeout(300);
  const inner = p.frames()[1];
  await inner.evaluate(() => window.scrollTo(0, 1300)); await p.waitForTimeout(150);
  assert(await inner.evaluate(() => [...document.querySelectorAll('#px *')].filter(e => e.style.transform).length === 0 && !document.documentElement.classList.contains('swtl-px-on')), 'skipped inside editor frame');
  await ctx.close();

  // 6. Reduced motion
  ctx = await browser.newContext({ ...ctxOpts, reducedMotion: 'reduce' });
  p = await ctx.newPage(); p.on('pageerror', e => errors.push(e.message));
  await p.goto(urlMain); await p.waitForTimeout(100);
  await scrollTo(p, 1000); await scrollTo(p, 1600);
  assert(await anyTransforms(p) === 0, 'reduced motion: no transforms');
  await ctx.close();

  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
}
