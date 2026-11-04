// Real-Chrome functional test for the word-by-word headline reveal.
// Run: node ../../shared/harness/run.mjs "$(pwd)/.test-page.html" "$(pwd)/browser.test.mjs"
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const H1 = 'Spaces <em>built</em> to be<br>lived in, <a href="#work">see&nbsp;the work</a>.';
const H2 = 'Rooms with <strong>room</strong> to breathe.';
const block = (col, inner) => `<div class="fe-block" style="grid-area:1/${col}"><div class="sqs-block html-block sqs-block-html" data-block-type="2"><div class="sqs-block-content"><div class="sqs-html-content" data-sqsp-text-block-content>${inner}</div></div></div></div>`;
const code = `<div class="fe-block" style="grid-area:2/1/3/3"><div class="sqs-block code-block sqs-block-code" data-block-type="23"><div class="sqs-block-content">${marker}</div></div></div>`;
const section = (id, inner, extra = '') => `<section class="page-section" data-section-id="${id}"${extra}><div class="section-background"></div><div class="content-wrapper"><div class="content"><div class="fluid-engine fe-${id}">${inner}</div></div></div></section>`;
const body =
  section('s1', block('1/2/13', `<p class="sqsrte-small">ARCHITECTURE &amp; INTERIORS</p><h1 style="white-space:pre-wrap;">${H1}</h1><p>We design homes and workplaces around how people actually use them.</p>`) + code) +
  section('s2', '<div class="fe-block" style="grid-area:1/1/2/25"><div style="height:1400px"></div></div>') +   /* spacer (test-only) */
  section('s3', block('1/2/13', `<h2>${H2}</h2><p>Light, air and long sightlines.</p>`) + code) +
  section('s4', block('1/2/13', '<h2>Unmarked section stays put.</h2>'));
const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--HEAD-->', '').replace('<!--BODY-->', body).replace('</body>', snippet + '</body>'));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="1000" height="700"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;

  // Reference: the editor's original markup, as the browser serializes it
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, javaScriptEnabled: false });
  let p = await ctx.newPage();
  await p.goto(url);
  const orig = await p.evaluate(() => [...document.querySelectorAll('.sqs-html-content')].map(e => e.innerHTML));
  const origText = await p.evaluate(() => [...document.querySelectorAll('h1, h2')].map(e => e.textContent));
  await ctx.close();

  // 1. Split + reveal
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(60);
  const s = await p.evaluate(() => {
    const h = document.querySelector('h1');
    return {
      on: document.documentElement.classList.contains('swtl-wr-on'),
      words: h.querySelectorAll('.swtl-wr-w').length,
      hidden: [...h.querySelectorAll('.swtl-wr-w')].every(w => w.getAttribute('aria-hidden') === 'true'),
      em: !!h.querySelector('em > .swtl-wr-w'), a: !!h.querySelector('a[href="#work"] > .swtl-wr-w'),
      br: h.querySelectorAll('br').length, aLabel: h.querySelector('a').getAttribute('aria-label'),
      label: h.getAttribute('aria-label'), text: h.textContent,
      nbsp: [...h.querySelectorAll('.swtl-wr-in')].some(i => i.textContent === 'see the'),
      firstT: getComputedStyle(h.querySelector('.swtl-wr-in')).transform,
      kicker: getComputedStyle(document.querySelector('.sqsrte-small')).opacity,
      h2split: document.querySelectorAll('.fe-s3 h2 .swtl-wr-w').length,
      unmarked: document.querySelectorAll('.fe-s4 .swtl-wr-w').length,
      accent: getComputedStyle(h.querySelector('em')).color
    };
  });
  assert(s.on, 'html.swtl-wr-on added by the script');
  assert(s.words === 9, `h1 split into 9 word masks (got ${s.words})`);
  assert(s.hidden, 'every split word is aria-hidden');
  assert(s.em && s.a && s.br === 1, 'inline markup kept: words inside <em> and <a>, <br> intact');
  assert(s.nbsp, '&nbsp; keeps "see the" as one word');
  assert(s.text === origText[0], 'heading textContent unchanged by the split');
  assert(s.label === 'Spaces built to be lived in, see the work.', `aria-label holds original text (${JSON.stringify(s.label)})`);
  assert(s.aLabel === 'see the work', 'link keeps an accessible name');
  assert(s.firstT !== 'none', 'words start translated (in motion)');
  assert(s.kicker !== '1', `kicker waits for the headline (opacity ${s.kicker})`);
  assert(s.accent === 'rgb(212, 85, 43)', `<em> picks up --swtl-accent (${s.accent})`);
  assert(s.h2split > 0, 'second marked section is split');
  assert(s.unmarked === 0, 'unmarked section is untouched');
  if (shots) { await p.waitForTimeout(250); await p.screenshot({ path: `${shots}/wr-mid.png` }); }

  // Resize mid-state: masks are per word, so lines reflow without re-splitting
  await p.setViewportSize({ width: 760, height: 720 });
  await p.waitForTimeout(50);
  const r = await p.evaluate(() => {
    const ws = [...document.querySelectorAll('h1 .swtl-wr-w')];
    const h = document.querySelector('h1');
    return { lines: new Set(ws.map(w => Math.round(w.getBoundingClientRect().top))).size, over: h.scrollWidth > h.clientWidth + 1, n: ws.length };
  });
  assert(r.lines >= 3 && !r.over && r.n === 9, `narrow viewport reflows (${r.lines} lines, no overflow, still 9 masks)`);
  await p.setViewportSize({ width: 1280, height: 720 });

  await p.waitForTimeout(2200);
  const rest = await p.evaluate(() => ({
    html: document.querySelector('.fe-s1 .sqs-html-content').innerHTML,
    spans: document.querySelectorAll('.fe-s1 .swtl-wr-w').length,
    kicker: getComputedStyle(document.querySelector('.sqsrte-small')).opacity,
    accent: document.querySelector('h1').classList.contains('swtl-wr-accent')
  }));
  assert(rest.spans === 0, 'at rest: words unwrapped, no transforms left');
  assert(rest.kicker === '1', 'kicker and body faded in');
  assert(rest.html.replace(/ class="swtl-wr-accent"/, '') === orig[0], 'at rest: hero markup equals the original (plus accent class)');
  assert(rest.accent, 'accent class kept at rest');

  // 2. Scroll: second section reveals on entry
  const before = await p.evaluate(() => getComputedStyle(document.querySelector('.fe-s3 h2 .swtl-wr-in')).transform);
  assert(before !== 'none', 'below-fold heading still hidden before scroll');
  await p.evaluate(() => document.querySelector('.fe-s3').scrollIntoView({ block: 'center' }));
  await p.waitForTimeout(250);
  if (shots) await p.screenshot({ path: `${shots}/wr-scroll.png` });
  await p.waitForTimeout(1800);
  assert(await p.evaluate(() => document.querySelectorAll('.fe-s3 .swtl-wr-w').length) === 0, 'second heading revealed and unwrapped');

  // 3. Inline heights: never written on any element
  const inlineH = await p.evaluate(() => [...document.querySelectorAll('[style]')].filter(e => /(^|;|\s)(min-|max-)?height\s*:/.test(e.getAttribute('style')) && !(e.parentElement && e.parentElement.closest('.fe-s2'))).length);
  assert(inlineH === 0, 'no inline height written on any element');
  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  await ctx.close();

  // 4. Edit mode mid-animation → byte-identical restore, then re-init on exit
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto(url);
  await p.waitForTimeout(200);
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(30);
  const ed = await p.evaluate(() => ({
    html: [...document.querySelectorAll('.sqs-html-content')].map(e => e.innerHTML),
    on: document.documentElement.classList.contains('swtl-wr-on'),
    label: document.querySelector('h1').hasAttribute('aria-label'),
    leftover: document.querySelectorAll('[class*="swtl-wr-"]').length
  }));
  assert(ed.html.every((h, i) => h === orig[i]), 'edit mode: every text block innerHTML byte-identical to original');
  assert(!ed.on && !ed.label && ed.leftover === 0, 'edit mode: html class, aria-label and all swtl-wr classes removed');
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(60);
  assert(await p.evaluate(() => document.querySelectorAll('h1 .swtl-wr-w').length) === 9, 'leaving edit mode re-initializes');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
  await p.waitForTimeout(30);
  assert(await p.evaluate(() => document.querySelector('.fe-s1 .sqs-html-content').innerHTML) === orig[0], 'sqs-is-page-editing also restores');
  await ctx.close();

  // 5. Editor frame guard
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  const inner = p.frames()[1];
  assert(await inner.evaluate(() => !document.documentElement.classList.contains('swtl-wr-on') && !document.querySelector('.swtl-wr-w')), 'skipped inside editor frame');
  await ctx.close();

  // 6. Reduced motion: no split, content visible
  ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto(url);
  await p.waitForTimeout(100);
  const rm = await p.evaluate(() => ({
    spans: document.querySelectorAll('.swtl-wr-w').length,
    on: document.documentElement.classList.contains('swtl-wr-on'),
    op: getComputedStyle(document.querySelector('.sqsrte-small')).opacity
  }));
  assert(rm.spans === 0 && !rm.on && rm.op === '1', 'reduced motion: no split, no hidden state');
  await ctx.close();
}
