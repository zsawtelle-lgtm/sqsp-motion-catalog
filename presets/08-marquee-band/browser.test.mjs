// Real-Chrome functional test for the marquee band.
// Run: node ../../shared/harness/run.mjs x "$(pwd)/browser.test.mjs"
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const SPEED = 60;
// Realistic Fluid Engine section: headline text block, phrase text block, code block with marker.
const section = (id, extra = '') => `
<section class="page-section" data-section-id="${id}">
 <div class="section-background"></div>
 <div class="content-wrapper"><div class="content"><div class="fluid-engine fe-${id}">
  <div class="fe-block fe-block-a" style="grid-area:1/1/2/25"><div class="sqs-block code-block sqs-block-code" data-block-type="23"><div class="sqs-block-content">${marker.replace('data-speed="100"', `data-speed="${SPEED}" data-source="2"${extra}`)}</div></div></div>
  <div class="fe-block fe-block-b" style="grid-area:2/1/3/13"><div class="sqs-block html-block sqs-block-html" data-block-type="2"><div class="sqs-block-content"><div class="sqs-html-content"><h2>What we do</h2></div></div></div></div>
  <div class="fe-block fe-block-c" style="grid-area:3/1/4/25"><div class="sqs-block html-block sqs-block-html" data-block-type="2"><div class="sqs-block-content"><div class="sqs-html-content"><p class="">Design — Build — Interiors — Landscape</p></div></div></div></div>
 </div></div></div>
</section>`;
const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--BODY-->',
  section('s1') + '<section class="page-section" style="padding:0"><div style="height:3000px"></div></section>' + section('s2'))
  .replace('</body>', snippet + '</body>'));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="800" height="600"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

const tx = (p, sel) => p.evaluate(s => new DOMMatrix(getComputedStyle(document.querySelector(s)).transform).m41, sel);

async function speedAt(browser, width) {
  const ctx = await browser.newContext({ viewport: { width, height: 800 } });
  const p = await ctx.newPage();
  await p.goto('file://' + pagePath);
  await p.waitForTimeout(600);
  const sel = '.fe-s1 .swtl-mq-row .swtl-mq-track';
  const period = await p.evaluate(s => parseFloat(document.querySelector(s).getAttribute('data-swtl-mq-period')), sel);
  const samples = await p.evaluate(async s => {
    const el = document.querySelector(s), out = [];
    for (let i = 0; i < 2; i++) {
      out.push([performance.now(), new DOMMatrix(getComputedStyle(el).transform).m41]);
      await new Promise(r => setTimeout(r, 1000));
    }
    return out;
  }, sel);
  let dx = samples[1][1] - samples[0][1];
  if (dx > 0) dx -= period;                      // wrapped once during the sample
  const v = -dx / ((samples[1][0] - samples[0][0]) / 1000);
  const fills = await p.evaluate(s => document.querySelector(s).getBoundingClientRect().width >= 2 * document.documentElement.clientWidth, sel);
  await ctx.close();
  return { v, fills };
}

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;

  // 1. Builds from the text block, moves, keeps SEO text in the DOM
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  let p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(500);
  const words = await p.evaluate(() => [...document.querySelector('.fe-s1 .swtl-mq-set').querySelectorAll('.swtl-mq-item')].map(e => e.textContent));
  assert(JSON.stringify(words) === JSON.stringify(['Design', 'Build', 'Interiors', 'Landscape']), 'track built from text block content: ' + words.join(','));
  assert(await p.evaluate(() => document.querySelectorAll('.fe-s1 .swtl-mq-row').length === 2), 'second band (opposite direction) built');
  assert(await p.evaluate(() => document.querySelector('.fe-s1 .swtl-mq-band').getAttribute('aria-hidden') === 'true'), 'band copies are aria-hidden');
  const src = await p.evaluate(() => { const c = document.querySelector('.fe-block-c .sqs-html-content'); const cs = getComputedStyle(c); return { inDom: c.textContent.includes('Interiors'), display: cs.display, clipped: c.classList.contains('swtl-mq-src') }; });
  assert(src.inDom && src.display !== 'none' && src.clipped, 'source text stays in DOM, clip-hidden (not display:none)');
  assert(await p.evaluate(() => document.querySelector('.fe-block-b h2').getBoundingClientRect().height > 0), 'other text blocks untouched');
  const a = await tx(p, '.fe-s1 .swtl-mq-left .swtl-mq-track');
  await p.waitForTimeout(400);
  const b = await tx(p, '.fe-s1 .swtl-mq-left .swtl-mq-track');
  assert(a !== b, `track moves over time (${a.toFixed(1)} → ${b.toFixed(1)})`);
  const r1 = await tx(p, '.fe-s1 .swtl-mq-right .swtl-mq-track');
  await p.waitForTimeout(300);
  const r2 = await tx(p, '.fe-s1 .swtl-mq-right .swtl-mq-track');
  assert(r2 > r1 || r2 < r1 - 100, 'second band runs to the right');
  const bandRect = await p.evaluate(() => { const r = document.querySelector('.fe-s1 .swtl-mq-band').getBoundingClientRect(); return [r.left, r.width, document.documentElement.clientWidth, document.documentElement.scrollWidth]; });
  assert(Math.abs(bandRect[0]) < 1 && Math.abs(bandRect[1] - bandRect[2]) < 1 && bandRect[3] <= bandRect[2], 'band bleeds edge to edge, no horizontal page scroll');
  if (shots) await p.screenshot({ path: `${shots}/mq-1280.png` });

  // 2. Offscreen: second section's band is paused, and stays put
  const off = await p.evaluate(() => document.querySelector('.fe-s2 .swtl-mq-band').classList.contains('swtl-mq-paused'));
  const o1 = await tx(p, '.fe-s2 .swtl-mq-left .swtl-mq-track');
  await p.waitForTimeout(400);
  const o2 = await tx(p, '.fe-s2 .swtl-mq-left .swtl-mq-track');
  assert(off && o1 === o2, 'pauses when off-screen (IntersectionObserver)');
  await p.evaluate(() => document.querySelector('.fe-s2').scrollIntoView());
  await p.waitForTimeout(300);
  assert(!(await p.evaluate(() => document.querySelector('.fe-s2 .swtl-mq-band').classList.contains('swtl-mq-paused'))), 'resumes when scrolled into view');
  await p.evaluate(() => window.scrollTo(0, 0));

  // 3. Hover pause
  await p.hover('.fe-s1 .swtl-mq-band');
  await p.waitForTimeout(100);
  const h1 = await tx(p, '.fe-s1 .swtl-mq-left .swtl-mq-track');
  await p.waitForTimeout(300);
  const h2 = await tx(p, '.fe-s1 .swtl-mq-left .swtl-mq-track');
  assert(h1 === h2, 'pauses on hover');
  await p.mouse.move(5, 5);

  // 4. Editor class → full teardown, text block visible and normal
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(150);
  const ed = await p.evaluate(() => ({
    bands: document.querySelectorAll('.swtl-mq-band').length,
    cls: document.querySelectorAll('[class*="swtl-mq-"]').length,
    h: document.querySelector('.fe-block-c .sqs-html-content').getBoundingClientRect().height,
    html: document.documentElement.className
  }));
  assert(ed.bands === 0 && ed.cls === 0 && ed.h > 10 && !/swtl-mq/.test(ed.html), `edit mode: torn down, text block visible (h=${ed.h.toFixed(0)})`);
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(200);
  assert(await p.evaluate(() => document.querySelectorAll('.swtl-mq-band').length === 2), 'exit edit mode: re-initialised');

  // 5. Resize rebuild (debounced)
  await p.setViewportSize({ width: 820, height: 800 });
  await p.waitForTimeout(500);
  const rs = await p.evaluate(() => { const r = document.querySelector('.fe-s1 .swtl-mq-band').getBoundingClientRect(); return [document.querySelectorAll('.swtl-mq-band').length, r.width, document.documentElement.clientWidth]; });
  assert(rs[0] === 2 && Math.abs(rs[1] - rs[2]) < 1, 'rebuilds on resize (band re-fits new width)');

  // 6. No inline height / min-height written on Squarespace elements
  const inline = await p.evaluate(() => [...document.querySelectorAll('.page-section, .content-wrapper, .content, .fluid-engine, .fe-block, .sqs-block, .sqs-block-content, .sqs-html-content')]
    .filter(e => /(^|;)\s*(min-|max-)?height\s*:/.test(e.getAttribute('style') || '')).length);
  assert(inline === 0, 'no inline height on Squarespace elements');
  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  await ctx.close();

  // 7. Speed in px/s at two viewport widths
  for (const w of [1280, 390]) {
    const { v, fills } = await speedAt(browser, w);
    assert(Math.abs(v - SPEED) / SPEED < 0.10, `speed at ${w}px: ${v.toFixed(1)} px/s (config ${SPEED})`);
    assert(fills, `track fills ≥ 2× viewport at ${w}px`);
  }

  // 8. Inside a frame (the Squarespace editor) it never runs
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(500);
  const inner = p.frames()[1];
  assert(await inner.$('.swtl-mq-band') === null, 'skipped inside editor frame');
  await ctx.close();

  // 9. Reduced motion: static band, no animation
  ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 800 } });
  p = await ctx.newPage();
  await p.goto(url);
  await p.waitForTimeout(400);
  const rm = await p.evaluate(() => { const t = document.querySelector('.fe-s1 .swtl-mq-track'); return { has: !!t, anim: t && getComputedStyle(t).animationName }; });
  const m1 = await tx(p, '.fe-s1 .swtl-mq-track');
  await p.waitForTimeout(300);
  const m2 = await tx(p, '.fe-s1 .swtl-mq-track');
  assert(rm.has && rm.anim === 'none' && m1 === m2, 'reduced motion: band shown static');
  await ctx.close();

  fs.unlinkSync(pagePath);
  fs.unlinkSync(frameHost);
}
