// Real-Chrome functional test for the staggered block rise.
// Run: node shared/harness/run.mjs x presets/04-block-rise/browser.test.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

// Fluid Engine blocks. DOM order is deliberately scrambled; grid-area sets
// the visual position, like a section edited over time in Squarespace.
const fe = (id, area, inner) =>
  `<div class="fe-block fe-block-${id}" data-id="${id}" style="grid-area:${area}">${inner}</div>`;
const html = (tag, txt) =>
  `<div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><${tag}>${txt}</${tag}></div></div></div>`;
const img = `<div class="sqs-block image-block"><div class="sqs-block-content"><div class="img"></div></div></div>`;
const btn = `<div class="sqs-block button-block"><div class="sqs-block-content"><a class="sqs-block-button-element" href="#">View services <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/></svg></a></div></div>`;
const code = `<div class="sqs-block code-block"><div class="sqs-block-content">${marker}</div></div>`;

// visual reading order the script must produce
const VISUAL = ['head', 'img1', 'img2', 'img3', 'txt1', 'txt2', 'txt3', 'btn'];
const services = (withMarker) => `<section class="page-section" data-section-id="svc"><div class="section-background"></div>
 <div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${fe('txt3', '3/17/4/25', html('h4', 'Interiors'))}
  ${fe('btn', '4/1/5/9', btn)}
  ${fe('img2', '2/9/3/17', img)}
  ${withMarker ? fe('code', '4/22/5/25', code) : ''}
  ${fe('txt1', '3/1/4/9', html('h4', 'Architecture'))}
  ${fe('img3', '2/17/3/25', img)}
  ${fe('head', '1/1/2/17', html('h2', 'What we do'))}
  ${fe('img1', '2/1/3/9', img)}
  ${fe('txt2', '3/9/4/17', html('h4', 'Planning'))}
 </div></div></div></section>`;
const hero = `<section class="page-section" data-section-id="hero"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${fe('h1', '1/1/2/13', html('h1', 'Spaces built to be lived in.'))}
  ${fe('hp', '2/1/3/11', html('p', 'Architecture and interiors.'))}
  <div data-spacer style="grid-area:3/1/4/2;height:700px"></div>
 </div></div></div></section>`;

const pageMain = path.join(here, '.test-main.html');
fs.writeFileSync(pageMain, mock.replace('<!--HEAD-->', '').replace('<!--BODY-->',
  hero + services(true) + '<div data-spacer style="height:900px"></div>' + snippet));
const pageAll = path.join(here, '.test-all.html');
fs.writeFileSync(pageAll, mock.replace('<!--HEAD-->', '').replace('<!--BODY-->',
  hero + services(false) + '<script>window.SwtlBlockRise={allSections:true,skipFirst:false}</script>' + snippet));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pageMain}" width="1000" height="700"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

const state = () => [...document.querySelectorAll('section[data-section-id="svc"] .fe-block')].map(e => {
  const cs = getComputedStyle(e);
  return { id: e.dataset.id, op: +cs.opacity, tf: cs.transform, cls: e.className, style: e.getAttribute('style') };
});
// any inline height/width/min-/max- on the page (test spacers are marked data-spacer)
const sizeWrites = () => [...document.querySelectorAll('[style]:not([data-spacer])')]
  .filter(e => /(^|[;\s])(min-|max-)?(height|width)\s*:/.test(e.getAttribute('style'))).length;

export default async function (browser) {
  const errors = [];
  const shots = process.env.SHOTS;

  // 1. Marker section: hidden below the fold, staggered rise on scroll
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  let p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto('file://' + pageMain);
  await p.waitForTimeout(300);
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-br-on')), 'html.swtl-br-on added once a marked section is found');
  let s = await p.evaluate(state);
  const anim = s.filter(b => b.id !== 'code');
  assert(anim.every(b => b.op === 0 && b.tf !== 'none'), `blocks below the fold start hidden + offset (${anim.map(b => b.op).join(',')})`);
  assert(s.find(b => b.id === 'code').cls.indexOf('swtl-br') === -1, "marker's own code block is excluded");
  const heroTouched = await p.evaluate(() => document.querySelectorAll('section[data-section-id="hero"] .swtl-br-block').length);
  assert(heroTouched === 0, 'section without a marker is untouched');

  await p.evaluate(() => document.querySelector('section[data-section-id="svc"]').scrollIntoView({ block: 'start' }));
  await p.waitForTimeout(60);
  const delays = await p.evaluate(() => [...document.querySelectorAll('section[data-section-id="svc"] .fe-block.swtl-br-in')]
    .map(e => [e.dataset.id, parseFloat(e.style.getPropertyValue('--swtl-br-delay'))]));
  const order = delays.slice().sort((a, b) => a[1] - b[1]).map(d => d[0]);
  assert(JSON.stringify(order) === JSON.stringify(VISUAL), `stagger follows visual order, not DOM order (${order.join(' > ')})`);
  assert(Math.abs(delays.find(d => d[0] === 'img1')[1] - 0.08) < 1e-6, 'stagger step = 0.08s');
  // timeline: mid-animation the first blocks are ahead of the last
  await p.waitForTimeout(240);
  s = await p.evaluate(state);
  const op = id => s.find(b => b.id === id).op;
  assert(op('head') > op('img3') && op('img3') > op('btn'), `mid-rise opacity decreases along reading order (head ${op('head').toFixed(2)} > img3 ${op('img3').toFixed(2)} > btn ${op('btn').toFixed(2)})`);
  if (shots) await p.screenshot({ path: `${shots}/br-mid.png` });
  await p.waitForTimeout(1700);
  s = await p.evaluate(state);
  assert(s.every(b => b.op === 1 && b.tf === 'none'), 'all blocks end at opacity 1, no transform');
  assert(s.every(b => b.cls.indexOf('swtl-br') === -1 && !/--swtl-br/.test(b.style || '')), 'at rest: classes + inline vars handed back');
  assert(await p.evaluate(sizeWrites) === 0, 'no inline height/width written anywhere');
  // play once: scroll away and back
  await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(100);
  await p.evaluate(() => document.querySelector('section[data-section-id="svc"]').scrollIntoView()); await p.waitForTimeout(100);
  s = await p.evaluate(state);
  assert(s.every(b => b.op === 1), 'plays once (no re-hide on second pass)');
  await ctx.close();

  // 2. Editor class: teardown, then re-init on exit
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto('file://' + pageMain);
  await p.waitForTimeout(200);
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(80);
  const torn = await p.evaluate(() => ({
    html: document.documentElement.classList.contains('swtl-br-on'),
    cls: document.querySelectorAll('[class*="swtl-br"]').length,
    vars: [...document.querySelectorAll('[style]')].filter(e => /--swtl-br/.test(e.getAttribute('style'))).length,
  }));
  s = await p.evaluate(state);
  assert(!torn.html && torn.cls === 0 && torn.vars === 0, `edit mode: html class, block classes and inline vars removed (${JSON.stringify(torn)})`);
  assert(s.every(b => b.op === 1 && b.tf === 'none'), 'edit mode: every block visible and untransformed');
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(80);
  s = await p.evaluate(state);
  assert(s.filter(b => b.id !== 'code').every(b => b.op === 0), 'leaving edit mode re-initialises');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
  await p.waitForTimeout(80);
  assert(await p.evaluate(() => document.querySelectorAll('[class*="swtl-br"]').length) === 0, 'sqs-is-page-editing also tears down');
  await ctx.close();

  // 3. allSections: blocks already in view animate immediately
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto('file://' + pageAll);
  await p.waitForTimeout(80);
  const heroIn = await p.evaluate(() => [...document.querySelectorAll('section[data-section-id="hero"] .fe-block')].map(e => e.classList.contains('swtl-br-in')));
  assert(heroIn.length === 2 && heroIn.every(Boolean), 'allSections: in-view hero blocks start rising on load');
  await p.waitForTimeout(1500);
  const heroOp = await p.evaluate(() => [...document.querySelectorAll('section[data-section-id="hero"] .fe-block')].map(e => +getComputedStyle(e).opacity));
  assert(heroOp.every(o => o === 1), 'allSections: in-view blocks end visible');
  const svcHidden = (await p.evaluate(state)).every(b => b.op === 0);
  assert(svcHidden, 'allSections: unmarked section below the fold waits for scroll');
  await ctx.close();

  // 4. Inside a frame (the Squarespace editor) it never runs
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  const inner = p.frames()[1];
  assert(await inner.evaluate(() => !document.documentElement.classList.contains('swtl-br-on') && !document.querySelector('[class*="swtl-br"]')), 'skipped inside editor frame');
  await ctx.close();

  // 5. Reduced motion: visible immediately, nothing applied
  ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto('file://' + pageMain);
  await p.waitForTimeout(100);
  s = await p.evaluate(state);
  assert(s.every(b => b.op === 1 && b.tf === 'none') && !(await p.evaluate(() => document.documentElement.classList.contains('swtl-br-on'))), 'reduced motion: visible immediately, no classes');
  await ctx.close();

  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  for (const f of [pageMain, pageAll, frameHost]) fs.rmSync(f, { force: true });
}
