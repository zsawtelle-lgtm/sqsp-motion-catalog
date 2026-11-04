// Real-Chrome functional test for the stat count-up.
// Run: node shared/harness/run.mjs x presets/11-stat-countup/browser.test.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const fe = (id, area, inner) =>
  `<div class="fe-block fe-block-${id}" data-id="${id}" style="grid-area:${area}">${inner}</div>`;
const text = (inner) =>
  `<div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content">${inner}</div></div></div>`;
const code = `<div class="sqs-block code-block"><div class="sqs-block-content">${marker}</div></div>`;

// the five formats, typed natively in Text blocks
const STATS = ['25+', '1,200', '98%', '$4.5M', '3.2x'];
const LABELS = ['Years in practice', 'Projects delivered', 'Client retention', 'Raised for partners', 'Average return'];
const stats = (id, withMarker) => `<section class="page-section" data-section-id="${id}"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${STATS.map((s, i) => fe('s' + i, `1/${i * 4 + 1}/2/${i * 4 + 5}`,
    text(`<h2 style="white-space:pre-wrap;text-align:center">${s}</h2><p class="" style="white-space:pre-wrap;">${LABELS[i]}</p>`))).join('\n  ')}
  ${fe('ctl', '2/1/3/25', text('<h3>Since 2009, <strong>open</strong> 24/7 — COVID-19 safe</h3><p>We answer 3 calls an hour for <strong>40</strong> partners.</p>'))}
  ${withMarker ? fe('code', '2/22/3/25', code) : ''}
 </div></div></div></section>`;
const hero = `<section class="page-section" data-section-id="hero"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  ${fe('h1', '1/1/2/13', text('<h1>Numbers since 2009</h1>'))}
  <div data-spacer style="grid-area:2/1/3/2;height:800px"></div>
 </div></div></div></section>`;

const write = (name, cfg, withMarker = true) => {
  const f = path.join(here, name);
  fs.writeFileSync(f, mock.replace('<!--HEAD-->', '').replace('<!--BODY-->',
    hero + stats('st', withMarker) + '<div data-spacer style="height:900px"></div>' + (cfg ? `<script>window.SwtlCountUp=${cfg}</script>` : '') + snippet));
  return f;
};
const pageMain = write('.test-main.html');
const pageNoLine = write('.test-noline.html', '{underline:false}');
const pageEm = write('.test-em.html', "{target:'emphasis'}");
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pageMain}" width="1000" height="700"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

const secHTML = () => document.querySelector('section[data-section-id="st"]').innerHTML;
const secText = () => document.querySelector('section[data-section-id="st"]').textContent;
const sizeWrites = () => [...document.querySelectorAll('[style]:not([data-spacer])')]
  .filter(e => /(^|[;\s])(min-|max-)?(height|width)\s*:/.test(e.getAttribute('style'))).length;
// page-side recorder: every frame, log the visible (overlay) text of each stat
const record = () => {
  window.__log = [];
  window.__w = [];
  const loop = () => {
    const runs = [...document.querySelectorAll('section[data-section-id="st"] h2')].map(h => {
      const r = h.querySelector('.swtl-cu-run');
      if (!r) return h.textContent;                       // finished: real text
      const st = h.querySelector('.swtl-cu-stat');
      return [...st.childNodes].map(n => n.nodeType === 3 ? n.data : n.querySelector('.swtl-cu-run').textContent).join('');
    });
    window.__log.push(runs);
    window.__w.push([...document.querySelectorAll('section[data-section-id="st"] h2')].map(h => { const st = h.querySelector('.swtl-cu-stat'); if (st) return st.getBoundingClientRect().width; const r = document.createRange(); r.selectNodeContents(h); return r.getBoundingClientRect().width; }));
    if (window.__log.length < 400) requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
};
const parse = (s) => parseFloat(s.replace(/[^\d.]/g, ''));
const shape = (s) => s.replace(/\d/g, '9').replace(/^(\D*)9(,?9)*/, '$1N');   // prefix N.dec suffix

export default async function (browser) {
  const errors = [];
  const shots = process.env.SHOTS;

  // 1. Default: headings in the marked section count up, end on exact text
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  let p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto('file://' + pageMain);
  // original markup, read before the script ran: rebuild it from the test source
  const origHTML = await (async () => {
    const q = await browser.newContext({ reducedMotion: 'reduce' }); const r = await q.newPage();
    await r.goto('file://' + pageMain); const h = await r.evaluate(secHTML); await q.close(); return h;
  })();
  const origText = await (async () => {
    const q = await browser.newContext({ reducedMotion: 'reduce' }); const r = await q.newPage();
    await r.goto('file://' + pageMain); const h = await r.evaluate(secText); await q.close(); return h;
  })();
  await p.waitForTimeout(200);
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-cu-on')), 'html.swtl-cu-on added once a marked section is found');
  assert(await p.evaluate(() => document.querySelectorAll('.swtl-cu-stat').length) === 5, `5 stats wrapped (headings only, years/24-7/COVID-19 skipped, paragraphs skipped)`);
  const sr = await p.evaluate(() => [...document.querySelectorAll('.swtl-cu-stat')].map(e => ({
    fin: e.querySelector('.swtl-cu-final').textContent, hid: e.querySelector('.swtl-cu-run').getAttribute('aria-hidden'),
    vis: getComputedStyle(e.querySelector('.swtl-cu-final')).visibility, disp: getComputedStyle(e.querySelector('.swtl-cu-final')).display })));
  assert(sr.every(s => s.hid === 'true' && s.vis === 'visible' && s.disp !== 'none'), 'real number stays in the a11y tree; counting copy is aria-hidden');
  const before = await p.evaluate(() => [...document.querySelectorAll('.swtl-cu-run')].map(e => e.textContent));
  assert(JSON.stringify(before) === JSON.stringify(['0', '0', '0', '0.0', '0.0']), `below the fold every number waits at 0 (${before.join(' ')})`);

  await p.evaluate(record);
  await p.evaluate(() => document.querySelector('section[data-section-id="st"]').scrollIntoView({ block: 'start' }));
  if (shots) { await p.waitForTimeout(700); await p.screenshot({ path: `${shots}/cu-mid.png` }); }
  await p.waitForTimeout(2900);
  const log = await p.evaluate(() => window.__log);
  const widths = await p.evaluate(() => window.__w);
  for (let i = 0; i < STATS.length; i++) {
    const seq = log.map(r => r[i]);
    const vals = seq.map(parse);
    const first = seq[0];
    const mono = vals.every((v, j) => j === 0 || v >= vals[j - 1] - 1e-9);
    const shapes = new Set(seq.filter(s => parse(s) >= 1000 || !/,/.test(STATS[i])).map(shape));
    const distinct = new Set(seq).size;
    assert(parse(first) === 0 && mono && seq[seq.length - 1] === STATS[i] && distinct > 8 &&
      [...shapes].every(sh => sh === shape(STATS[i])),
      `"${STATS[i]}" counts 0 → ${STATS[i]} (start ${first}, ${distinct} steps, monotonic ${mono}, format kept)`);
  }
  const mid = log[Math.floor(log.length * 0.12)];
  const v0 = parse(mid[0]) / 25, v4 = parse(mid[4]) / 3.2;
  assert(v0 > v4, `stagger: first stat ahead of the last mid-count (${mid.join(' | ')})`);
  const wJump = widths.reduce((m, r) => Math.max(m, ...r.map((w, i) => Math.abs(w - widths[0][i]))), 0);
  assert(wJump < 0.5, `no layout shift: the typed number keeps its width during the count (max Δ ${wJump.toFixed(2)}px)`);
  assert(await p.evaluate(secText) === origText, 'at rest: section textContent identical to the original');
  const rest = await p.evaluate(() => ({ run: document.querySelectorAll('.swtl-cu-run,.swtl-cu-box').length,
    line: [...document.querySelectorAll('.swtl-cu-stat')].map(e => getComputedStyle(e, '::after').transform) }));
  assert(rest.run === 0 && rest.line.length === 5 && rest.line.every(t => t === 'none'), 'at rest: overlay gone, underlines fully drawn');
  assert(await p.evaluate(sizeWrites) === 0, 'no inline height/width written anywhere');
  await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(100);
  await p.evaluate(() => document.querySelector('section[data-section-id="st"]').scrollIntoView()); await p.waitForTimeout(150);
  assert(await p.evaluate(() => document.querySelectorAll('.swtl-cu-run').length) === 0, 'plays once (no second count)');
  // editor after finishing → byte-identical markup
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active')); await p.waitForTimeout(60);
  assert(await p.evaluate(secHTML) === origHTML, 'edit mode after the count: innerHTML byte-identical');
  await ctx.close();

  // 2. underline:false → at rest the markup is byte-identical
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto('file://' + pageNoLine);
  await p.evaluate(() => document.querySelector('section[data-section-id="st"]').scrollIntoView({ block: 'start' }));
  await p.waitForTimeout(2900);
  assert(await p.evaluate(secHTML) === origHTML, 'underline:false: at rest innerHTML byte-identical');
  await ctx.close();

  // 3. Editor class mid-count: restore, then re-init on exit
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto('file://' + pageMain);
  await p.evaluate(() => document.querySelector('section[data-section-id="st"]').scrollIntoView({ block: 'start' }));
  await p.waitForTimeout(500);
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(80);
  const torn = await p.evaluate(() => ({ html: document.documentElement.classList.contains('swtl-cu-on'),
    cls: document.querySelectorAll('[class*="swtl-cu"]').length }));
  assert(!torn.html && torn.cls === 0 && await p.evaluate(secHTML) === origHTML, `edit mode mid-count: everything removed, innerHTML byte-identical (${JSON.stringify(torn)})`);
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(120);
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-cu-on') && document.querySelectorAll('.swtl-cu-stat').length === 5), 'leaving edit mode re-initialises');
  await p.waitForTimeout(2600);
  assert(await p.evaluate(secText) === origText, 're-init counts again and ends on the original text');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing')); await p.waitForTimeout(60);
  assert(await p.evaluate(() => document.querySelectorAll('[class*="swtl-cu"]').length) === 0 && await p.evaluate(secHTML) === origHTML, 'sqs-is-page-editing also tears down');
  await ctx.close();

  // 4. target: 'emphasis' → only bold/italic text counts
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  p.on('pageerror', e => errors.push(e.message));
  await p.goto('file://' + pageEm);
  await p.waitForTimeout(100);
  const em = await p.evaluate(() => [...document.querySelectorAll('.swtl-cu-stat')].map(e => e.parentNode.tagName + ':' + e.querySelector('.swtl-cu-final').textContent));
  assert(em.length === 1 && em[0] === 'STRONG:40', `target 'emphasis': only bold/italic numbers count (${em.join(',')})`);
  await ctx.close();

  // 5. Inside a frame (the Squarespace editor) it never runs
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  assert(await p.frames()[1].evaluate(() => !document.documentElement.classList.contains('swtl-cu-on') && !document.querySelector('[class*="swtl-cu"]')), 'skipped inside editor frame');
  await ctx.close();

  // 6. Reduced motion: final numbers at once, nothing touched
  ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto('file://' + pageMain);
  await p.evaluate(() => document.querySelector('section[data-section-id="st"]').scrollIntoView());
  await p.waitForTimeout(150);
  assert(!(await p.evaluate(() => document.documentElement.classList.contains('swtl-cu-on'))) &&
    await p.evaluate(() => [...document.querySelectorAll('section[data-section-id="st"] h2')].map(h => h.textContent).join('|')) === STATS.join('|'),
    'reduced motion: no count, final numbers shown');
  await ctx.close();

  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  for (const f of [pageMain, pageNoLine, pageEm, frameHost]) fs.rmSync(f, { force: true });
}
