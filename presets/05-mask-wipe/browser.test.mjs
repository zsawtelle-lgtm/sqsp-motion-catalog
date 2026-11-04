// Real-Chrome functional test for the mask / clip wipe reveal.
// Run: node ../../shared/harness/run.mjs x "$(pwd)/browser.test.mjs"
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const svg = (c) => 'data:image/svg+xml,' + encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="450"><rect width="600" height="450" fill="${c}"/><circle cx="420" cy="150" r="40" fill="#F4F1EA"/></svg>`);
// Fluid Engine image block, as Squarespace 7.1 renders it
const img = (area, c, id) => `<div class="fe-block fe-block-${id}" style="grid-area:${area}">
  <div class="sqs-block image-block sqs-block-image" id="block-${id}"><div class="sqs-block-content">
   <div class="fluid-image-component-root"><div class="fluid-image-animation-wrapper"><div class="fluid-image-container sqs-image-content" style="overflow:hidden;position:relative">
    <div class="content-fill"><img src="${svg(c)}" alt="" style="display:block;width:100%;height:auto"></div>
   </div></div></div></div></div></div>`;
const txt = (area, id, h) => `<div class="fe-block fe-block-${id}" style="grid-area:${area}">
  <div class="sqs-block html-block sqs-block-html" id="block-${id}"><div class="sqs-block-content"><div class="sqs-html-content"><h2>${h}</h2><p>Body copy for the editorial column.</p></div></div></div></div>`;
const code = (area, m) => `<div class="fe-block" style="grid-area:${area}"><div class="sqs-block code-block sqs-block-code"><div class="sqs-block-content">${m}</div></div></div>`;

const BODY = `
<section class="page-section" data-section-id="s0"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${txt('1/1/2/24', 'h0', 'Intro section (no marker)')}
</div></div></div></section>
<div class="test-spacer" style="height:1400px"></div>
<section class="page-section" data-section-id="s1"><div class="section-background"></div><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${img('1/1/6/13', '#D4552B', 'i1')}
  ${txt('1/14/3/25', 't1', 'Editorial heading')}
  ${img('3/16/6/25', '#4C6A5B', 'i2')}
  ${code('6/1/7/3', marker)}
</div></div></div></section>
<div class="test-spacer" style="height:1400px"></div>
<section class="page-section" data-section-id="s2"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${img('1/1/4/12', '#1F1E1C', 'i3')}
  ${txt('1/13/3/25', 't2', 'Text wipes too')}
  ${code('4/1/5/3', '<div data-swtl-wipe data-direction="down" data-curtain="ink" data-text="true" hidden></div>')}
</div></div></div></section>
<div class="test-spacer" style="height:900px"></div>`;

const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--BODY-->', BODY).replace('</body>', snippet + '\n</body>'));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="1000" height="700"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

// helpers evaluated in page
const state = (s => {
  const b = document.querySelector(s); const c = b.querySelector('.sqs-block-content');
  const kid = c.firstElementChild; const cur = c.querySelector('.swtl-mw-curtain');
  const im = b.querySelector('img');
  return {
    cls: b.className, kidClip: getComputedStyle(kid).clipPath,
    cur: cur ? getComputedStyle(cur).clipPath : null,
    curRect: cur ? cur.getBoundingClientRect().toJSON() : null,
    contentRect: c.getBoundingClientRect().toJSON(),
    imgTf: im ? getComputedStyle(im).transform : null
  };
});
const scrollTo = (p, id) => p.evaluate(i => {
  const r = document.getElementById(i).getBoundingClientRect();
  window.scrollTo(0, window.scrollY + r.top - 120);
}, id);
const inlineSizes = (p) => p.evaluate(() => [...document.querySelectorAll('.page-section, .fe-block, .sqs-block, .sqs-block-content, .sqs-block-content *')]
  .filter(e => /(^|;|\s)(min-|max-)?(height|width)\s*:/.test(e.getAttribute('style') || '') && !e.matches('img, .test-spacer'))
  .map(e => e.className));

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;

  // 1. Hidden, then fully revealed after scroll
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  let p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(200);
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-mw-on')), 'html.swtl-mw-on added when a marker exists');
  const curtains = await p.evaluate(() => document.querySelectorAll('.swtl-mw-curtain').length);
  assert(curtains === 3, `one curtain per image block in marked sections (got ${curtains})`);
  assert(await p.evaluate(() => !document.querySelector('[data-section-id="s0"] .swtl-mw-item')), 'unmarked section untouched');
  const before = await p.evaluate(state, '#block-i1');
  assert(/inset\(0px 100% 0px 0px\)/.test(before.kidClip), 'image hidden before scroll: ' + before.kidClip);
  assert(before.curRect.width === before.contentRect.width && before.curRect.height === before.contentRect.height,
    'curtain fills the block content box exactly');
  assert(await p.evaluate(() => getComputedStyle(document.querySelector('#block-t1 .sqs-html-content')).clipPath === 'none'),
    'text blocks untouched by default (data-text off)');
  const sizeBefore = await p.evaluate(() => document.getElementById('block-i1').getBoundingClientRect().height);

  await scrollTo(p, 'block-i1');
  await p.waitForTimeout(420);
  const mid = await p.evaluate(state, '#block-i1');
  assert(/swtl-mw-go/.test(mid.cls), 'block triggered on scroll');
  assert(mid.cur && /inset\(0px [\d.]+% 0px 0px\)/.test(mid.cur), 'curtain mid-sweep (growing from the left): ' + mid.cur);
  if (shots) await p.screenshot({ path: `${shots}/mw-420.png` });
  await p.waitForTimeout(500);
  const mid2 = await p.evaluate(state, '#block-i1');
  assert(/inset\(0px 0px 0px [\d.]+%\)/.test(mid2.cur || ''), 'curtain exiting to the right: ' + mid2.cur);
  assert(mid2.imgTf && mid2.imgTf !== 'none' && parseFloat(mid2.imgTf.slice(7)) > 1.0, 'image scaled >1 while uncovering: ' + mid2.imgTf);
  const stag = await p.evaluate(() => [document.getElementById('block-i1').style.getPropertyValue('--swtl-mw-delay'),
    document.getElementById('block-i2').style.getPropertyValue('--swtl-mw-delay')]);
  assert(parseFloat(stag[1]) > parseFloat(stag[0] || 0), 'second image staggered after the first: ' + stag.join(' / '));
  if (shots) await p.screenshot({ path: `${shots}/mw-920.png` });
  await p.waitForTimeout(2200);
  const done = await p.evaluate(state, '#block-i1');
  const done2 = await p.evaluate(state, '#block-i2');
  assert(done.kidClip === 'none' && done2.kidClip === 'none', 'clip-path cleared after reveal');
  assert(done.cur === null && done2.cur === null, 'curtain nodes removed after reveal');
  assert(done.imgTf === 'none', 'image transform back to none');
  assert(!/swtl-mw/.test(done.cls + done2.cls), 'block classes cleaned: ' + done.cls);
  const sizeAfter = await p.evaluate(() => document.getElementById('block-i1').getBoundingClientRect().height);
  assert(Math.abs(sizeAfter - sizeBefore) < 0.5, `block keeps its own size (${sizeBefore} -> ${sizeAfter})`);

  // 2. Direction attribute + ink curtain + text wipe
  assert(await p.evaluate(() => /swtl-mw-down/.test(document.getElementById('block-i3').className) &&
    /swtl-mw-ink/.test(document.getElementById('block-i3').className)), 'data-direction="down" + data-curtain="ink" applied');
  assert(await p.evaluate(() => /swtl-mw-text/.test(document.getElementById('block-t2').className)), 'data-text="true" opts text blocks in');
  await scrollTo(p, 'block-i3');
  await p.waitForTimeout(380);
  const d = await p.evaluate(state, '#block-i3');
  assert(/inset\(0px 0px [\d.]+%( 0px)?\)/.test(d.cur || ''), 'down: curtain grows from the top: ' + d.cur);
  const curBg = await p.evaluate(() => getComputedStyle(document.querySelector('#block-i3 .swtl-mw-curtain')).backgroundColor);
  assert(curBg === 'rgb(31, 30, 28)', 'ink curtain color: ' + curBg);
  const tclip = await p.evaluate(() => getComputedStyle(document.querySelector('#block-t2 .sqs-html-content')).clipPath);
  assert(/inset\(0px 0px [\d.]+%( 0px)?\)/.test(tclip), 'text block plain clip wipe running: ' + tclip);
  await p.waitForTimeout(2400);
  assert(await p.evaluate(() => !document.querySelector('.swtl-mw-curtain, .swtl-mw-item')), 'all blocks cleaned after every reveal');
  const sizes = await inlineSizes(p);
  assert(sizes.length === 0, 'no inline height/width written on Squarespace elements ' + sizes.join(','));
  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  await ctx.close();

  // 3. Edit mode: teardown, everything visible, curtains removed; re-init on exit
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(200);
  await scrollTo(p, 'block-i1');
  await p.waitForTimeout(300);                        // mid-animation on purpose
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(80);
  const ed = await p.evaluate(() => ({
    on: document.documentElement.classList.contains('swtl-mw-on'),
    curtains: document.querySelectorAll('.swtl-mw-curtain').length,
    items: document.querySelectorAll('[class*="swtl-mw"]').length,
    clips: [...document.querySelectorAll('.sqs-block-content > *')].map(e => getComputedStyle(e).clipPath).filter(c => c !== 'none').length,
    anims: [...document.querySelectorAll('.sqs-block-content *')].filter(e => getComputedStyle(e).animationName !== 'none').length,
    styles: [...document.querySelectorAll('.sqs-block')].filter(e => e.hasAttribute('style')).length
  }));
  assert(!ed.on, 'edit mode: html class removed');
  assert(ed.curtains === 0, 'edit mode: injected curtain nodes removed');
  assert(ed.items === 0, 'edit mode: every swtl-mw class removed');
  assert(ed.clips === 0 && ed.anims === 0, 'edit mode: everything visible (no clip, no animation)');
  assert(ed.styles === 0, 'edit mode: no inline style left on blocks');
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(100);
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-mw-on') &&
    document.querySelectorAll('.swtl-mw-curtain').length === 3), 'leaving edit mode re-initialises');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
  await p.waitForTimeout(80);
  assert(await p.evaluate(() => !document.querySelector('.swtl-mw-curtain')), 'sqs-is-page-editing also tears down');
  await ctx.close();

  // 4. Inside a frame (the Squarespace editor) it never runs
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  const inner = p.frames()[1];
  assert(await inner.evaluate(() => !document.documentElement.classList.contains('swtl-mw-on') &&
    !document.querySelector('.swtl-mw-curtain')), 'skipped inside editor frame');
  await ctx.close();

  // 5. Reduced motion: content visible, nothing injected
  ctx = await browser.newContext({ reducedMotion: 'reduce' });
  p = await ctx.newPage();
  await p.goto(url);
  await p.waitForTimeout(200);
  const rm = await p.evaluate(state, '#block-i1');
  const rmHtml = await p.evaluate(() => document.documentElement.className);
  assert(rm.kidClip === 'none' && rm.cur === null && !/swtl/.test(rmHtml),
    'reduced motion: images visible, no curtain');
  await ctx.close();
  assert(errors.length === 0, 'no page errors (all runs)');
}
