// Real-Chrome functional test for the scroll text fill.
// Run: node ../../shared/harness/run.mjs "$(pwd)/.test-page.html" "$(pwd)/browser.test.mjs"
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const H2 = 'We design homes that age well, cost less to run,<br>and feel <em>calm</em> on a <a href="#tue">Tuesday&nbsp;night</a>.';
const P = 'Every project starts with <strong>how you live</strong>, not how it photographs.';
const block = (col, inner) => `<div class="fe-block" style="grid-area:1/${col}"><div class="sqs-block html-block sqs-block-html" data-block-type="2"><div class="sqs-block-content"><div class="sqs-html-content" data-sqsp-text-block-content>${inner}</div></div></div></div>`;
const code = `<div class="fe-block" style="grid-area:2/1/3/3"><div class="sqs-block code-block sqs-block-code" data-block-type="23"><div class="sqs-block-content">${marker}</div></div></div>`;
const section = (id, inner) => `<section class="page-section" data-section-id="${id}"><div class="section-background"></div><div class="content-wrapper"><div class="content"><div class="fluid-engine fe-${id}">${inner}</div></div></div></section>`;
const spacer = id => section(id, '<div class="fe-block" style="grid-area:1/1/2/25"><div class="swtl-test-spacer" style="height:1600px"></div></div>');
const body =
  spacer('s1') +
  section('s2', block('1/2/20', `<h2 class="sqsrte-large" style="white-space:pre-wrap;">${H2}</h2><p>${P}</p>`) + code) +
  spacer('s3') +
  section('s4', block('1/2/13', '<h2>Unmarked section stays put.</h2>'));
const head = '<style>.sqs-block-content h2{font-size:56px;line-height:1.1;margin:0 0 24px;letter-spacing:-0.02em}</style>';
const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--HEAD-->', head).replace('<!--BODY-->', body).replace('</body>', snippet + '</body>'));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="1000" height="700"></iframe>`);

// Chrome serializes color-mix() results as color(srgb r g b): normalize to rgb()
const rgb = c => { const m = c.match(/color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)/); return m ? `rgb(${m.slice(1).map(v => Math.round(v * 255)).join(', ')})` : c; };

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

// Count rAF callbacks the page schedules (installed before any page script)
const countRaf = () => {
  const raf = window.requestAnimationFrame.bind(window);
  window.__rafs = 0;
  window.requestAnimationFrame = cb => { window.__rafs++; return raf(cb); };
};

// Put the h2's top at a given share of the viewport height
async function placeTop(p, share) {
  await p.evaluate(s => {
    const h = document.querySelector('.fe-s2 h2');
    window.scrollTo(0, window.scrollY + h.getBoundingClientRect().top - s * innerHeight);
  }, share);
  await p.waitForTimeout(80);
}
const fill = p => p.evaluate(() => {
  const ws = [...document.querySelectorAll('.fe-s2 h2 .swtl-tf-w')];
  return ws.reduce((a, w) => a + (parseFloat(w.style.getPropertyValue('--swtl-tf-f')) || 0), 0) / ws.length;
});

export default async function (browser) {
  const url = 'file://' + pagePath;

  // Reference: the editor's original markup, as the browser serializes it
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, javaScriptEnabled: false });
  let p = await ctx.newPage();
  await p.goto(url);
  const orig = await p.evaluate(() => [...document.querySelectorAll('.sqs-html-content')].map(e => e.innerHTML));
  const origText = await p.evaluate(() => [...document.querySelectorAll('.fe-s2 h2, .fe-s2 p')].map(e => e.textContent));
  const origOuter = await p.evaluate(() => document.querySelector('.fe-s2 .sqs-html-content').outerHTML);
  await ctx.close();

  // 1. Split + scroll-linked fill
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  await ctx.addInitScript(countRaf);
  p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(100);
  const s = await p.evaluate(() => {
    const h = document.querySelector('.fe-s2 h2'), para = document.querySelector('.fe-s2 p');
    const first = h.querySelector('.swtl-tf-w');
    return {
      on: document.documentElement.classList.contains('swtl-tf-on'),
      words: h.querySelectorAll('.swtl-tf-w').length, pWords: para.querySelectorAll('.swtl-tf-w').length,
      hHidden: [...h.querySelectorAll('.swtl-tf-w')].every(w => w.getAttribute('aria-hidden') === 'true'),
      pExposed: [...para.querySelectorAll('.swtl-tf-w')].every(w => !w.hasAttribute('aria-hidden')) && !para.hasAttribute('aria-label'),
      label: h.getAttribute('aria-label'), aLabel: h.querySelector('a').getAttribute('aria-label'),
      em: !!h.querySelector('em > .swtl-tf-w.swtl-tf-acc'), a: !!h.querySelector('a[href="#tue"] > .swtl-tf-w'),
      strong: para.querySelectorAll('strong > .swtl-tf-acc').length, br: h.querySelectorAll('br').length,
      nbsp: [...h.querySelectorAll('.swtl-tf-w')].some(w => w.textContent === 'Tuesday\u00a0night'),
      text: [h.textContent, para.textContent],
      op: parseFloat(getComputedStyle(first).opacity),
      display: getComputedStyle(first).display,
      unmarked: document.querySelectorAll('.fe-s4 .swtl-tf-w').length
    };
  });
  assert(s.on, 'html.swtl-tf-on added by the script');
  assert(s.words === 17, `h2 split into 17 words (got ${s.words})`);
  assert(s.pWords === 12, `paragraph split into 12 words (got ${s.pWords})`);
  assert(s.em && s.a && s.br === 1 && s.strong === 3, 'inline markup kept: words inside <em>, <a>, <strong>; <br> intact');
  assert(s.nbsp, '&nbsp; keeps "Tuesday night" as one word');
  assert(s.text[0] === origText[0] && s.text[1] === origText[1], 'textContent unchanged by the split');
  assert(s.hHidden && s.label === 'We design homes that age well, cost less to run, and feel calm on a Tuesday\u00a0night.', `heading: aria-label holds original text, words aria-hidden (${JSON.stringify(s.label)})`);
  assert(s.aLabel === 'Tuesday\u00a0night', 'link keeps an accessible name');
  assert(s.pExposed, 'paragraph words stay exposed to screen readers (no aria-label on <p>)');
  assert(Math.abs(s.op - 0.18) < 0.01, `below the fold: words rest dim (opacity ${s.op})`);
  assert(s.display === 'inline', 'word spans stay inline (no layout change)');
  assert(s.unmarked === 0, 'unmarked section is untouched');

  // 2. rAF idle while the block is offscreen
  let r0 = await p.evaluate(() => window.__rafs);
  await p.waitForTimeout(500);
  let r1 = await p.evaluate(() => window.__rafs);
  assert(r1 - r0 === 0, `rAF idle while offscreen (${r1 - r0} callbacks in 500 ms)`);

  // 3. Fill follows scroll position, both ways
  await placeTop(p, 0.90); const f0 = await fill(p);
  await placeTop(p, 0.70); const f1 = await fill(p);
  await placeTop(p, 0.55); const f2 = await fill(p);
  await placeTop(p, 0.38); const f3 = await fill(p);
  assert(f0 === 0 && f1 > 0 && f2 > f1 && f3 === 1, `fill rises with scroll: ${[f0, f1, f2, f3].map(v => v.toFixed(2)).join(' → ')}`);
  r0 = await p.evaluate(() => window.__rafs);
  await p.waitForTimeout(300);
  r1 = await p.evaluate(() => window.__rafs);
  assert(r1 - r0 > 5, `rAF runs while in view (${r1 - r0} callbacks in 300 ms)`);
  const lit = await p.evaluate(() => ({
    op: getComputedStyle(document.querySelector('.fe-s2 h2 .swtl-tf-w')).opacity,
    acc: getComputedStyle(document.querySelector('.fe-s2 em .swtl-tf-w')).color,
    plain: getComputedStyle(document.querySelector('.fe-s2 h2 .swtl-tf-w')).color
  }));
  assert(lit.op === '1', `filled words reach full ink (opacity ${lit.op})`);
  assert(rgb(lit.acc) === 'rgb(212, 85, 43)', `<em> word fills to --swtl-accent (${rgb(lit.acc)})`);
  assert(lit.plain === 'rgb(31, 30, 28)', `plain words keep the text color (${lit.plain})`);
  await placeTop(p, 0.62); const b1 = await fill(p);
  await placeTop(p, 0.80); const b2 = await fill(p);
  const dimAcc = await p.evaluate(() => getComputedStyle(document.querySelector('.fe-s2 em .swtl-tf-w')).color);
  assert(b1 < 1 && b2 < b1, `fill reverses scrolling back up: 1.00 → ${b1.toFixed(2)} → ${b2.toFixed(2)}`);
  assert(rgb(dimAcc) === 'rgb(31, 30, 28)', `unfilled <em> word is not yet accent (${rgb(dimAcc)})`);

  // 4. Resize: inline spans reflow, no re-split, fill still tracks
  const before = await p.evaluate(() => document.querySelectorAll('.swtl-tf-w').length);
  await p.setViewportSize({ width: 760, height: 720 });
  await placeTop(p, 0.55);
  const rz = await p.evaluate(() => {
    const h = document.querySelector('.fe-s2 h2'), ws = [...h.querySelectorAll('.swtl-tf-w')];
    return { n: document.querySelectorAll('.swtl-tf-w').length, lines: new Set(ws.map(w => Math.round(w.getBoundingClientRect().top))).size,
             over: h.scrollWidth > h.clientWidth + 1 };
  });
  const fr = await fill(p);
  assert(rz.n === before && rz.lines >= 4 && !rz.over && fr > 0 && fr < 1, `narrow viewport reflows (${rz.lines} lines, same ${rz.n} spans, fill ${fr.toFixed(2)})`);
  await p.setViewportSize({ width: 1280, height: 720 });

  // 5. Leaving the viewport upward settles at full; rAF stops
  await p.evaluate(() => window.scrollTo(0, scrollY + document.querySelector('.fe-s4').getBoundingClientRect().top));
  await p.waitForTimeout(150);
  assert(await fill(p) === 1, 'scrolled past: block settles fully filled');
  r0 = await p.evaluate(() => window.__rafs);
  await p.waitForTimeout(400);
  r1 = await p.evaluate(() => window.__rafs);
  assert(r1 - r0 === 0, `rAF stops once the block leaves view (${r1 - r0})`);

  const inlineH = await p.evaluate(() => [...document.querySelectorAll('[style]')].filter(e => /(^|;|\s)(min-|max-)?height\s*:/.test(e.getAttribute('style')) && !e.classList.contains('swtl-test-spacer')).length);
  assert(inlineH === 0, 'no inline height written on any element');
  const foreign = await p.evaluate(() => [...document.querySelectorAll('[style*="--swtl-tf"]')].every(e => e.classList.contains('swtl-tf-w')));
  assert(foreign, 'inline styles only on the script\'s own word spans');
  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  await ctx.close();

  // 6. Edit mode mid-fill → byte-identical restore, then re-init on exit
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto(url);
  await placeTop(p, 0.6);
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(30);
  const ed = await p.evaluate(() => ({
    html: [...document.querySelectorAll('.sqs-html-content')].map(e => e.innerHTML),
    outer: document.querySelector('.fe-s2 .sqs-html-content').outerHTML,
    on: document.documentElement.classList.contains('swtl-tf-on'),
    leftover: document.querySelectorAll('[class*="swtl-tf-"], [aria-label]').length
  }));
  assert(ed.html.every((h, i) => h === orig[i]), 'edit mode: every text block innerHTML byte-identical to original');
  assert(ed.outer === origOuter, 'edit mode: heading and paragraph attributes restored (outerHTML identical)');
  assert(!ed.on && ed.leftover === 0, 'edit mode: html class, aria-labels and all swtl-tf classes removed');
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(80);
  const re = await p.evaluate(() => document.querySelectorAll('.fe-s2 h2 .swtl-tf-w').length);
  assert(re === 17 && (await fill(p)) > 0, 'leaving edit mode re-initializes at the current scroll position');
  await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
  await p.waitForTimeout(30);
  assert(await p.evaluate(() => document.querySelector('.fe-s2 .sqs-html-content').outerHTML) === origOuter, 'sqs-is-page-editing also restores');
  await ctx.close();

  // 7. Editor frame guard
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  const inner = p.frames()[1];
  assert(await inner.evaluate(() => !document.documentElement.classList.contains('swtl-tf-on') && !document.querySelector('.swtl-tf-w')), 'skipped inside editor frame');
  await ctx.close();

  // 8. Reduced motion: fully filled, no split, accent kept
  ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto(url);
  await p.waitForTimeout(100);
  const rm = await p.evaluate(() => ({
    spans: document.querySelectorAll('.swtl-tf-w').length,
    on: document.documentElement.classList.contains('swtl-tf-on'),
    op: getComputedStyle(document.querySelector('.fe-s2 h2')).opacity,
    acc: getComputedStyle(document.querySelector('.fe-s2 em')).color,
    text: document.querySelector('.fe-s2 h2').textContent
  }));
  assert(rm.spans === 0 && !rm.on && rm.op === '1' && rm.text === origText[0], 'reduced motion: no split, text at full ink');
  assert(rm.acc === 'rgb(212, 85, 43)', `reduced motion: <em> shows the accent (${rm.acc})`);
  await ctx.close();
}
