// Real-Chrome functional test for the marker highlight & underline draw.
// Run: node shared/harness/run.mjs x presets/17-marker-highlight/browser.test.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');

const marker = (attrs) => `<div data-swtl-marker ${attrs} hidden></div>`;
const block = (col, inner) => `<div class="fe-block" style="grid-area:1/${col}"><div class="sqs-block html-block sqs-block-html" data-block-type="2"><div class="sqs-block-content"><div class="sqs-html-content" data-sqsp-text-block-content>${inner}</div></div></div></div>`;
const code = (m) => `<div class="fe-block" style="grid-area:2/1/3/3"><div class="sqs-block code-block sqs-block-code" data-block-type="23"><div class="sqs-block-content">${m}</div></div></div>`;
const section = (id, inner) => `<section class="page-section" data-section-id="${id}"><div class="section-background"></div><div class="content-wrapper"><div class="content"><div class="fluid-engine fe-${id}">${inner}</div></div></div></section>`;
const spacer = (id) => section(id, '<div class="fe-block" style="grid-area:1/1/2/25"><div data-spacer style="height:1200px"></div></div>');

// s1 highlight on <em>; <strong> must stay untouched
const S1 = `<h1 style="white-space:pre-wrap;">Design that <em>works</em> as hard as <strong>you</strong> do.</h1><p>A <em>long highlighted phrase that wraps onto a second line</em> in a narrow block.</p>`;
// s3 underline on em (one phrase wraps to two lines), circle on strong
const S3 = `<h2>Every launch, <em>planned around the people who use it every day</em>, and <strong>tested</strong>.</h2><p>Plain words, then a <em>short</em> one.</p>`;
const body =
  section('s1', block('1/2/9', S1) + code(marker('data-style="highlight"'))) +
  spacer('sp1') +
  section('s3', block('1/2/12', S3) + code(marker('data-target="em, strong" data-style="underline, circle"'))) +
  spacer('sp2') +
  section('s5', block('1/2/13', '<h2>Unmarked <em>section</em> stays put.</h2>'));
const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--HEAD-->', '').replace('<!--BODY-->', body).replace('</body>', snippet + '</body>'));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="1000" height="700"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

const snap = () => ({
  html: [...document.querySelectorAll('.sqs-html-content')].map(e => e.innerHTML),
  blocks: [...document.querySelectorAll('.sqs-block')].map(e => e.outerHTML),
  text: [...document.querySelectorAll('.sqs-html-content')].map(e => e.textContent)
});
const bgw = (sel) => { const e = document.querySelector(sel); return parseFloat(getComputedStyle(e).backgroundSize) || 0; };
const offs = (sel) => [...document.querySelectorAll(sel)].map(p => parseFloat(getComputedStyle(p).strokeDashoffset));

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;

  // Reference markup with no script
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, javaScriptEnabled: false });
  let p = await ctx.newPage();
  await p.goto(url);
  const orig = await p.evaluate(snap);
  await ctx.close();

  // 1. Targets, styles, hidden start
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(40);
  const a = await p.evaluate(() => ({
    on: document.documentElement.classList.contains('swtl-mh-on'),
    hl: [...document.querySelectorAll('.swtl-mh-hl')].map(e => e.tagName + ':' + e.textContent.slice(0, 8)),
    strong1: document.querySelector('.fe-s1 strong').getAttribute('class'),
    svg1: document.querySelectorAll('.fe-s1 .swtl-mh-svg').length,
    svg3: document.querySelectorAll('.fe-s3 .swtl-mh-svg').length,
    svgHidden: [...document.querySelectorAll('.swtl-mh-svg')].every(s => s.getAttribute('aria-hidden') === 'true'),
    svgInText: document.querySelectorAll('.sqs-html-content svg').length,
    paths3: document.querySelectorAll('.fe-s3 .swtl-mh-path').length,
    s3cls: [...document.querySelectorAll('.fe-s3 em, .fe-s3 strong')].map(e => e.getAttribute('class')),
    unmarked: document.querySelectorAll('.fe-s5 [class*="swtl-mh"], .fe-s5 .swtl-mh-svg').length,
    hlStart: parseFloat(getComputedStyle(document.querySelector('.fe-s1 h1 em')).backgroundSize),
    italic: getComputedStyle(document.querySelector('.fe-s1 h1 em')).fontStyle
  }));
  assert(a.on, 'html.swtl-mh-on added by the script');
  assert(JSON.stringify(a.hl) === JSON.stringify(['EM:works', 'EM:long hig']), `highlight applies to <em> only in its section (${a.hl.join(', ')})`);
  assert(a.strong1 === null, '<strong> in a highlight-only section untouched');
  assert(a.svg1 === 0 && a.svg3 === 1 && a.svgHidden && a.svgInText === 0, 'one aria-hidden overlay per underline/circle block, outside the text markup');
  assert(a.s3cls.every(c => c === null), 'underline/circle add no classes to the words');
  assert(a.unmarked === 0, 'unmarked section untouched');
  assert(a.hlStart === 0, `highlight starts undrawn (${a.hlStart}%)`);
  assert(a.italic === 'italic', 'em keeps italic by default');
  const s3hidden = await p.evaluate(offs, '.fe-s3 .swtl-mh-path');
  assert(s3hidden.every(o => o > 5), `below-fold strokes start undrawn (${s3hidden.map(o => o.toFixed(0)).join(',')})`);
  const tx = await p.evaluate(snap);
  assert(tx.text.every((t, i) => t === orig.text[i]), 'textContent of every text block unchanged');

  // highlight draws in on load (hero in view)
  await p.waitForTimeout(500);
  const mid = await p.evaluate(bgw, '.fe-s1 h1 em');
  if (shots) await p.screenshot({ path: `${shots}/mh-hero-mid.png` });
  await p.waitForTimeout(1200);
  const end = await p.evaluate(bgw, '.fe-s1 h1 em');
  assert(mid > 0 && mid < 100 && end === 100, `highlight draws left→right (${mid.toFixed(0)}% → ${end}%)`);
  const wrapHl = await p.evaluate(() => {
    const e = document.querySelector('.fe-s1 p em'), rs = [...e.getClientRects()].filter(r => r.width > 1);
    return { lines: rs.length, clone: getComputedStyle(e).boxDecorationBreak || getComputedStyle(e).webkitBoxDecorationBreak, style: e.getAttribute('style') };
  });
  assert(wrapHl.lines >= 2 && wrapHl.clone === 'clone', `wrapped highlight: ${wrapHl.lines} lines, box-decoration-break clone (each line gets a band)`);
  assert(wrapHl.style === null, 'highlight at rest: inline animation style removed');

  // 2. Scroll → underline + circle draw in
  await p.evaluate(() => document.querySelector('.fe-s3').scrollIntoView({ block: 'center' }));
  await p.waitForTimeout(450);
  const drawing = await p.evaluate(offs, '.fe-s3 .swtl-mh-path');
  if (shots) await p.screenshot({ path: `${shots}/mh-scroll-mid.png` });
  await p.waitForTimeout(2200);
  const drawn = await p.evaluate(offs, '.fe-s3 .swtl-mh-path');
  if (shots) await p.screenshot({ path: `${shots}/mh-scroll-rest.png` });
  assert(drawing.some((o, i) => o < s3hidden[i] - 1), `strokes drawing after scroll (${drawing.map(o => o.toFixed(0)).join(',')})`);
  assert(drawn.every(o => Math.abs(o) < 0.5), 'all strokes fully drawn at rest');

  // geometry: wrapped underline phrase → one stroke per line; circle around "tested"
  const geo = await p.evaluate(() => {
    const em = document.querySelector('.fe-s3 h2 em');
    const lines = [...em.getClientRects()].filter(r => r.width > 1);
    const paths = [...document.querySelectorAll('.fe-s3 .swtl-mh-path')].map(x => x.getBoundingClientRect());
    const st = document.querySelector('.fe-s3 h2 strong').getBoundingClientRect();
    const em2 = document.querySelector('.fe-s3 p em').getBoundingClientRect();
    return { lines: lines.map(r => [r.left, r.top, r.right, r.bottom]), paths: paths.map(r => [r.left, r.top, r.right, r.bottom]), st: [st.left, st.top, st.right, st.bottom], em2: [em2.left, em2.top, em2.right, em2.bottom] };
  });
  const under = (pr, r) => pr[1] > r[1] + (r[3] - r[1]) * 0.6 && pr[3] < r[3] + (r[3] - r[1]) * 0.4 && Math.abs(pr[0] - r[0]) < 14 && Math.abs(pr[2] - r[2]) < 14;
  const around = (pr, r) => pr[0] < r[0] && pr[2] > r[2] && pr[1] < r[1] + 6 && pr[3] > r[3] - 6;
  assert(geo.lines.length === 2, `underline phrase wraps to 2 lines (${geo.lines.length})`);
  assert(geo.paths.length === 4, `4 strokes: 2 underline lines + circle + short underline (${geo.paths.length})`);
  assert(under(geo.paths[0], geo.lines[0]) && under(geo.paths[1], geo.lines[1]), 'each wrapped line gets its own underline under it');
  const circ = geo.paths.find(pr => around(pr, geo.st));
  assert(!!circ, 'circle stroke encloses the <strong> word');
  assert(geo.paths.some(pr => under(pr, geo.em2)), 'second <em> in the section gets its own underline');

  // 3. Resize → geometry recomputed
  const d0 = await p.evaluate(() => [...document.querySelectorAll('.fe-s3 .swtl-mh-path')].map(x => x.getAttribute('d')));
  await p.setViewportSize({ width: 900, height: 720 });
  await p.waitForTimeout(400);
  const rs = await p.evaluate(() => {
    const em = document.querySelector('.fe-s3 h2 em');
    const lines = [...em.getClientRects()].filter(r => r.width > 1).map(r => [r.left, r.top, r.right, r.bottom]);
    const ps = [...document.querySelectorAll('.fe-s3 .swtl-mh-path')];
    return { lines, d: ps.map(x => x.getAttribute('d')), boxes: ps.map(x => { const r = x.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }),
      off: ps.map(x => parseFloat(getComputedStyle(x).strokeDashoffset)) };
  });
  assert(rs.d.join() !== d0.join(), 'resize rebuilds the stroke paths');
  assert(rs.lines.every((r, i) => rs.boxes[i] && under(rs.boxes[i], r)), `after resize strokes sit under the reflowed lines (${rs.lines.length} lines)`);
  assert(rs.off.every(o => Math.abs(o) < 0.5), 'already-drawn marks stay drawn after resize');
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.waitForTimeout(300);

  const inlineH = await p.evaluate(() => [...document.querySelectorAll('[style]:not([data-spacer])')].filter(e => /(^|;|\s)(min-|max-)?height\s*:/.test(e.getAttribute('style'))).length);
  assert(inlineH === 0, 'no inline height written on any element');
  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));

  // 4. Edit mode → byte-identical restore, overlays removed, re-init on exit
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(30);
  const ed = await p.evaluate(() => ({
    html: [...document.querySelectorAll('.sqs-html-content')].map(e => e.innerHTML),
    blocks: [...document.querySelectorAll('.sqs-block')].map(e => e.outerHTML),
    on: document.documentElement.classList.contains('swtl-mh-on'),
    svgs: document.querySelectorAll('svg.swtl-mh-svg, .swtl-mh-path').length,
    leftover: document.querySelectorAll('[class*="swtl-mh-"]').length
  }));
  assert(ed.html.every((h, i) => h === orig.html[i]), 'edit mode: every text block innerHTML byte-identical to original');
  assert(ed.blocks.every((h, i) => h === orig.blocks[i]), 'edit mode: every .sqs-block outerHTML byte-identical (overlays gone)');
  assert(!ed.on && ed.svgs === 0 && ed.leftover === 0, 'edit mode: html class, SVGs and all swtl-mh classes removed');
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(60);
  const re = await p.evaluate(() => ({ hl: document.querySelectorAll('.swtl-mh-hl').length, svg: document.querySelectorAll('.swtl-mh-svg').length, on: document.documentElement.classList.contains('swtl-mh-on') }));
  assert(re.hl === 2 && re.svg === 1 && re.on, 'leaving edit mode re-initializes');
  await p.waitForTimeout(1500);
  assert((await p.evaluate(offs, '.fe-s3 .swtl-mh-path')).every(o => Math.abs(o) < 0.5), 're-init: in-view marks draw again');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
  await p.waitForTimeout(30);
  assert(JSON.stringify(await p.evaluate(snap)) === JSON.stringify(orig), 'sqs-is-page-editing also restores byte-identical');
  await ctx.close();

  // 5. keepItalic:false
  const plainPath = path.join(here, '.test-plain.html');
  fs.writeFileSync(plainPath, mock.replace('<!--HEAD-->', '').replace('<!--BODY-->', body).replace('</body>', '<script>window.SwtlMarker={keepItalic:false}</script>' + snippet + '</body>'));
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto('file://' + plainPath);
  await p.waitForTimeout(60);
  assert(await p.evaluate(() => getComputedStyle(document.querySelector('.fe-s1 h1 em')).fontStyle === 'normal' && document.querySelector('.fe-s1 h1 em').tagName === 'EM'), 'keepItalic:false resets italic, <em> element kept');
  await ctx.close();

  // 6. Editor frame guard
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  const inner = p.frames()[1];
  assert(await inner.evaluate(() => !document.documentElement.classList.contains('swtl-mh-on') && !document.querySelector('[class*="swtl-mh"]')), 'skipped inside editor frame');
  await ctx.close();

  // 7. Reduced motion: marks shown static, no hidden state
  ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto(url);
  await p.waitForTimeout(60);
  const rm = await p.evaluate(() => ({
    on: document.documentElement.classList.contains('swtl-mh-on'),
    bg: parseFloat(getComputedStyle(document.querySelector('.fe-s1 h1 em')).backgroundSize),
    anim: [...document.querySelectorAll('.swtl-mh-hl, .swtl-mh-path')].map(e => getComputedStyle(e).animationName),
    off: [...document.querySelectorAll('.swtl-mh-path')].map(x => parseFloat(getComputedStyle(x).strokeDashoffset))
  }));
  assert(!rm.on && rm.bg === 100 && rm.off.length === 4 && rm.off.every(o => o === 0) && rm.anim.every(n => n === 'none'),
    `reduced motion: highlight full, all ${rm.off.length} strokes drawn, no animation`);
  if (shots) { await p.evaluate(() => document.querySelector('.fe-s3').scrollIntoView({ block: 'center' })); await p.screenshot({ path: `${shots}/mh-reduced.png` }); }
  await ctx.close();
}
