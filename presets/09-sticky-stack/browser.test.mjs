// Real-Chrome functional test for the sticky stacked-card scroll.
// Run: node ../../shared/harness/run.mjs "$(pwd)/.test-page.html" "$(pwd)/browser.test.mjs"
// Builds a 7.1-shaped page (#siteWrapper > main#page > article.sections >
// section.page-section…) with a fixed header and an overflow-x:hidden
// wrapper (the case that breaks sticky), then removes its temp pages.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const tones = ['#F4F1EA', '#F4F1EA', '#1F1E1C', '#D4552B', '#F4F1EA', '#F4F1EA'];
function section(i, withMarker) {
  const code = withMarker
    ? `<div class="fe-block" style="grid-column:20/25"><div class="sqs-block code-block"><div class="sqs-block-content">${marker}</div></div></div>`
    : '';
  // block content sets the height (as the editor would) — never the section
  return `<section class="page-section" data-section-id="s${i}" id="s${i}">
  <div class="section-background" style="position:absolute;inset:0;background:${tones[i]}"></div>
  <div class="content-wrapper" style="position:relative"><div class="content"><div class="fluid-engine">
   <div class="fe-block" style="grid-column:1/13"><div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><h1>Section ${i}</h1></div></div></div></div>
   <div class="fe-block" style="grid-column:13/20"><div class="sqs-block image-block"><div class="sqs-block-content"><div class="img" style="aspect-ratio:auto;height:${i === 3 ? 340 : 400}px"></div></div></div></div>
   ${code}
  </div></div></div></section>`;
}
const body = `<article class="sections">${[0, 1, 2, 3, 4, 5].map(i => section(i, i === 1)).join('\n')}</article>`;
const extraCss = `<style>
 header#header{position:fixed;top:0;left:0;right:0;z-index:100;background:#F4F1EA;box-sizing:border-box}
 main#page{overflow-x:hidden;padding-top:76px}
 .page-section{padding:60px 0}
</style>`;
const build = withSnippet => mock
  .replace('<header>', '<div id="siteWrapper" class="site-wrapper"><header id="header" class="header">')
  .replace('</main>', '</main></div>')
  .replace('<!--HEAD-->', extraCss)
  .replace('<!--BODY-->', body)
  .replace('</body>', (withSnippet ? snippet : '') + '</body>');

const pagePath = path.join(here, '.test-page.html');
const barePath = path.join(here, '.test-bare.html');
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(pagePath, build(true));
fs.writeFileSync(barePath, build(false));
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="1280" height="720"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

const state = () => [...document.querySelectorAll('section.page-section')].map(s => ({
  id: s.id, card: s.classList.contains('swtl-sk-card'), round: s.classList.contains('swtl-sk-round'),
  after: s.classList.contains('swtl-sk-after'), style: s.getAttribute('style') || '', h: s.offsetHeight
}));
const anyAdded = () => document.querySelectorAll('[class*="swtl-sk-"]').length;

export default async function (browser) {
  const url = 'file://' + pagePath;
  const errors = [];
  const shots = process.env.SHOTS;

  try {
    // 0. reference heights from the same page without the snippet
    let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    let p = await ctx.newPage();
    await p.goto('file://' + barePath);
    const bare = await p.evaluate(state);
    await ctx.close();

    // 1. Desktop: count, heights, unclip, pin + scale
    ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(150);
    let st = await p.evaluate(state);
    assert(st.filter(s => s.card).map(s => s.id).join() === 's1,s2', `sticky class on exactly s1,s2 (got ${st.filter(s => s.card).map(s => s.id)})`);
    assert(st.filter(s => s.round).map(s => s.id).join() === 's2,s3', 'rounded incoming cards s2,s3');
    assert(!st[0].card && !st[0].round && !st[0].after && !st[4].card && !st[4].round, 'sections outside the count untouched (s0, s4)');
    assert(st.every((s, i) => s.h === bare[i].h), `section heights identical to no-snippet page (${st.map(s => s.h)} vs ${bare.map(s => s.h)})`);
    assert(st.every(s => !/(^|;)\s*(min-|max-)?height\s*:/.test(s.style)), 'no inline height/min-height on any section');
    assert(await p.evaluate(() => document.getElementById('page').classList.contains('swtl-sk-unclip')), 'overflow-x:hidden wrapper detected and switched to clip');
    const top = await p.evaluate(() => getComputedStyle(document.getElementById('s1')).top);
    assert(top === '76px', `headerOffset auto: sticky top = fixed header height (got ${top})`);

    const s1Start = await p.evaluate(() => document.getElementById('s1').getBoundingClientRect().top + scrollY);
    const tops = [], scales = [];
    for (const dy of [0, 150, 300, 420]) {
      await p.evaluate(y => scrollTo(0, y), s1Start - 76 + dy);
      await p.waitForTimeout(80);
      const r = await p.evaluate(() => {
        const s = document.getElementById('s1');
        return { top: s.getBoundingClientRect().top, t: s.style.transform, shade: parseFloat(s.style.getPropertyValue('--swtl-sk-shade') || 0) };
      });
      tops.push(r.top);
      scales.push(r);
    }
    // scaled from top-center origin, so the visual top stays at 76
    assert(tops.every(t => Math.abs(t - 76) < 1.5), `s1 pins at the sticky top while s2 slides over (${tops.map(t => t.toFixed(1))})`);
    const last = scales[scales.length - 1];
    const sc = parseFloat((last.t.match(/scale\(([\d.]+)/) || [])[1]);
    assert(sc < 1 && sc >= 0.94, `covered s1 scale < 1 (got ${last.t})`);
    assert(last.shade > 0.05, `covered s1 dims (shade ${last.shade})`);
    assert(scales[0].shade < scales[3].shade, 'dim grows as the next card covers');
    if (shots) await p.screenshot({ path: `${shots}/sk-desktop.png` });
    const z = await p.evaluate(() => {
      const s2 = document.getElementById('s2').getBoundingClientRect();
      const el = document.elementFromPoint(640, s2.top + 30);
      return el && el.closest('section') && el.closest('section').id;
    });
    assert(z === 's2', `incoming card paints above the pinned card (got ${z})`);

    // 2. Editor class → full teardown, then re-init on exit
    await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
    await p.waitForTimeout(80);
    const ed = await p.evaluate(() => ({ n: document.querySelectorAll('[class*="swtl-sk-"]').length,
      styles: [...document.querySelectorAll('section.page-section')].map(s => s.getAttribute('style')).filter(Boolean),
      pos: getComputedStyle(document.getElementById('s1')).position }));
    assert(ed.n === 0 && ed.styles.length === 0 && ed.pos !== 'sticky', `edit mode: no classes, no inline styles, no sticky (${JSON.stringify(ed)})`);
    await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
    await p.waitForTimeout(80);
    assert(await p.evaluate(() => document.getElementById('s1').classList.contains('swtl-sk-card')), 'leaving edit mode re-initialises');
    await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
    await p.waitForTimeout(80);
    assert(await p.evaluate(anyAdded) === 0, 'sqs-is-page-editing also tears down');

    // 3. Mobile breakpoint
    await p.evaluate(() => document.body.classList.remove('sqs-is-page-editing'));
    await p.setViewportSize({ width: 600, height: 800 });
    await p.waitForTimeout(150);
    assert(await p.evaluate(anyAdded) === 0, 'resize below 768px disables');
    await ctx.close();

    ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(120);
    assert(await p.evaluate(anyAdded) === 0, 'mobile (390px) load: no sticky, no classes');
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.waitForTimeout(150);
    assert(await p.evaluate(() => document.getElementById('s1').classList.contains('swtl-sk-card')), 'widening past breakpoint enables');
    await ctx.close();

    // 4. Editor frame guard
    ctx = await browser.newContext({ viewport: { width: 1400, height: 800 } });
    p = await ctx.newPage();
    await p.goto('file://' + frameHost);
    await p.waitForTimeout(400);
    assert(await p.frames()[1].evaluate(anyAdded) === 0, 'skipped inside editor frame');
    await ctx.close();

    // 5. Reduced motion: stacking stays, no scale / dim
    ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, reducedMotion: 'reduce' });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(120);
    await p.evaluate(() => scrollTo(0, document.getElementById('s1').getBoundingClientRect().top + scrollY - 76 + 400));
    await p.waitForTimeout(120);
    const rmS = await p.evaluate(() => { const s = document.getElementById('s1');
      return { card: s.classList.contains('swtl-sk-card'), t: s.style.transform, shade: s.style.getPropertyValue('--swtl-sk-shade'), top: s.getBoundingClientRect().top }; });
    assert(rmS.card && Math.abs(rmS.top - 76) < 1.5, 'reduced motion: sticky stacking kept');
    assert(!rmS.t && !rmS.shade, `reduced motion: no scale, no dim (${JSON.stringify(rmS)})`);
    await ctx.close();

    assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  } finally {
    for (const f of [pagePath, barePath, frameHost]) try { fs.unlinkSync(f); } catch (e) {}
  }
}
