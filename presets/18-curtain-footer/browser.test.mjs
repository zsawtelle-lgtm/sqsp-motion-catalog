// Real-Chrome functional test for the curtain footer reveal.
// Run: node ../../shared/harness/run.mjs x "$(pwd)/browser.test.mjs"
// Builds a 7.1-shaped page (#siteWrapper > header#header + main#page >
// article.sections + footer#footer-sections.sections > section.page-section)
// with a fixed header, then removes its temp pages.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');

const tones = ['#F4F1EA', '#E6E0D4', '#F4F1EA', '#D4552B'];
function section(i) {
  return `<section class="page-section" data-section-id="s${i}" id="s${i}">
  <div class="section-background" style="position:absolute;inset:0;background:${tones[i]}"></div>
  <div class="content-wrapper" style="position:relative"><div class="content"><div class="fluid-engine">
   <div class="fe-block" style="grid-column:1/13"><div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><h1>Section ${i}</h1></div></div></div></div>
   <div class="fe-block" style="grid-column:13/25"><div class="sqs-block image-block"><div class="sqs-block-content"><div class="img" style="aspect-ratio:auto;height:420px"></div></div></div></div>
  </div></div></div></section>`;
}
// footer content height comes from its blocks (as the editor would), never the section
function footer(extra) {
  const col = n => `<div class="fe-block" style="grid-column:${n * 6 + 1}/${n * 6 + 7}"><div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content">
     <p><a href="#l${n}a" id="l${n}a" style="color:#F4F1EA">Link ${n}a</a></p><p><a href="#l${n}b" style="color:#F4F1EA">Link ${n}b</a></p></div></div></div></div>`;
  return `<footer class="sections" id="footer-sections" data-footer-sections>
  <section class="page-section" data-section-id="f1" id="f1" style="color:#F4F1EA">
   <div class="section-background" style="position:absolute;inset:0;background:#1F1E1C"></div>
   <div class="content-wrapper" style="position:relative"><div class="content"><div class="fluid-engine" id="ffe">
    <div class="fe-block" style="grid-column:1/7"><div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><h3 style="margin:0">Studio</h3></div></div></div></div>
    ${col(1)}${col(2)}${col(3)}
    ${extra || ''}
   </div></div></div></section></footer>`;
}
const tall = '<div class="fe-block" id="tallblock" style="grid-column:1/25"><div class="sqs-block code-block"><div class="sqs-block-content"><div style="height:640px"></div></div></div></div>';
const extraCss = `<style>
 header#header{position:fixed;top:0;left:0;right:0;z-index:100;background:#F4F1EA;box-sizing:border-box}
 main#page{padding-top:76px}
 .page-section{padding:60px 0}
 #footer-sections .page-section{padding:56px 0}
</style>`;
const build = (withSnippet, extra) => mock
  .replace('<header>', '<div id="siteWrapper" class="site-wrapper"><header id="header" class="header">')
  .replace('</main>', '</main>' + footer(extra) + '</div>')
  .replace('<!--HEAD-->', extraCss)
  .replace('<!--BODY-->', `<article class="sections" id="sections">${[0, 1, 2, 3].map(section).join('\n')}</article>`)
  .replace('</body>', (withSnippet ? snippet : '') + '</body>');

const pagePath = path.join(here, '.test-page.html');
const barePath = path.join(here, '.test-bare.html');
const tallPath = path.join(here, '.test-tall.html');
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(pagePath, build(true));
fs.writeFileSync(barePath, build(false));
fs.writeFileSync(tallPath, build(true, tall));
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="1280" height="720"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

const heights = () => [...document.querySelectorAll('#siteWrapper, #page, #footer-sections, section.page-section')]
  .map(e => e.offsetHeight);
const anyAdded = () => document.querySelectorAll('[class*="swtl-cf-"]').length +
  (document.documentElement.getAttribute('style') ? 1 : 0);
const probe = () => {
  const f = document.getElementById('footer-sections'), sp = document.querySelector('.swtl-cf-spacer');
  const at = (x, y) => { const e = document.elementFromPoint(x, y); return e ? (e.closest('#page') ? 'page' : e.closest('#footer-sections') ? 'footer' : e.className || e.tagName) : null; };
  const fr = f.getBoundingClientRect();
  return {
    pos: getComputedStyle(f).position, fz: getComputedStyle(f).zIndex,
    pz: getComputedStyle(document.getElementById('page')).zIndex,
    fh: f.offsetHeight, ftop: fr.top, fbottom: fr.bottom, ih: innerHeight,
    sp: sp ? { h: sp.offsetHeight, top: sp.getBoundingClientRect().top, aria: sp.getAttribute('aria-hidden'),
      afterPage: sp.previousElementSibling && sp.previousElementSibling.id === 'page', style: sp.getAttribute('style') } : null,
    y: f.style.getPropertyValue('--swtl-cf-y'), o: f.style.getPropertyValue('--swtl-cf-o'),
    cwT: getComputedStyle(f.querySelector('.content-wrapper')).transform,
    hitBottom: at(640, innerHeight - 20), hitMid: at(640, innerHeight / 2)
  };
};
// inline height/margin on any Squarespace-owned element (the spacer is ours)
const SQS = 'html, body, #siteWrapper, #header, #page, .sections, #footer-sections, section.page-section, .section-background, .content-wrapper, .content, .fluid-engine, .fe-block, .sqs-block';
const inlineLayout = sel => [...document.querySelectorAll(sel)]
  .map(e => e.getAttribute('style') || '').filter(s => /(^|;)\s*((min-|max-)?height|margin[a-z-]*)\s*:/.test(s));

export default async function (browser) {
  const url = 'file://' + pagePath;
  const errors = [];
  const shots = process.env.SHOTS;
  const ctxOpts = { viewport: { width: 1280, height: 720 } };

  try {
    // 0. reference heights from the same page without the snippet
    let ctx = await browser.newContext(ctxOpts);
    let p = await ctx.newPage();
    await p.goto('file://' + barePath);
    const bare = await p.evaluate(heights);
    await ctx.close();

    // 1. Desktop: fixed footer behind the page, spacer sized to it
    ctx = await browser.newContext(ctxOpts);
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(200);
    let r = await p.evaluate(probe);
    assert(r.pos === 'fixed' && Math.abs(r.fbottom - r.ih) < 1, `footer fixed to the viewport bottom (${r.pos}, bottom ${r.fbottom})`);
    assert(+r.fz < +r.pz, `footer z-index under page (${r.fz} < ${r.pz})`);
    assert(r.sp && r.sp.afterPage && r.sp.aria === 'true', 'spacer inserted right after main#page, aria-hidden');
    assert(r.sp && r.sp.h === r.fh, `spacer height == footer height (${r.sp && r.sp.h} / ${r.fh})`);
    assert(r.hitBottom === 'page' && r.hitMid === 'page', `at top: footer hidden under the page (hit ${r.hitBottom})`);
    const bg = await p.evaluate(() => [document.documentElement.style.getPropertyValue('--swtl-cf-bg'), getComputedStyle(document.body).backgroundColor,
      getComputedStyle(document.getElementById('page')).backgroundColor]);
    assert(bg[0] === bg[1] && bg[2] === bg[1], `page background = site background (${bg.join(' / ')})`);
    const st = await p.evaluate(heights);
    assert(st.join() === bare.join(), `Squarespace element heights unchanged (${st} vs ${bare})`);
    assert((await p.evaluate(inlineLayout, SQS)).length === 0, 'no inline height/margin on Squarespace elements');
    const radius = await p.evaluate(() => [getComputedStyle(document.getElementById('page')).borderBottomLeftRadius, getComputedStyle(document.getElementById('page')).overflow, getComputedStyle(document.getElementById('page')).boxShadow]);
    assert(radius[0] === '24px' && radius[1] === 'clip' && radius[2] !== 'none', `rounded bottom corners + shadow (${radius.join(' | ')})`);

    // 2. Mid-reveal parallax, then page bottom: fully visible, clickable
    const max = await p.evaluate(() => document.documentElement.scrollHeight - innerHeight);
    await p.evaluate(y => scrollTo(0, y), max - Math.round(r.fh / 2));
    await p.waitForTimeout(120);
    const mid = await p.evaluate(probe);
    assert(parseFloat(mid.y) > 20 && parseFloat(mid.y) < 40 && parseFloat(mid.o) < 1, `half revealed: content mid-rise (y ${mid.y}, o ${mid.o})`);
    assert(mid.hitBottom === 'footer' && mid.hitMid === 'page', `half revealed: page bottom covers top of footer (${mid.hitBottom}/${mid.hitMid})`);
    await p.evaluate(() => scrollTo(0, document.documentElement.scrollHeight));
    await p.waitForTimeout(120);
    r = await p.evaluate(probe);
    assert(Math.abs(r.sp.top - r.ftop) < 1 && Math.abs(r.ftop - (r.ih - r.fh)) < 1, `at bottom: spacer sits exactly over the footer (spacer ${r.sp.top}, footer ${r.ftop})`);
    assert(parseFloat(r.y) === 0 && parseFloat(r.o) === 1, `at bottom: content at rest (y ${r.y}, o ${r.o})`);
    const link = await p.evaluate(() => {
      const a = document.getElementById('l2a'), b = a.getBoundingClientRect();
      const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
      return { same: hit === a, top: b.top };
    });
    assert(link.same && link.top > 0, `footer link is the top element at its point (elementFromPoint)`);
    await p.click('#l2a');
    assert((await p.evaluate(() => location.hash)) === '#l2a', 'footer link click lands');
    if (shots) await p.screenshot({ path: `${shots}/cf-bottom.png` });

    // 3. Footer resizes → spacer follows (ResizeObserver)
    await p.evaluate(() => {
      const d = document.createElement('div');
      d.className = 'fe-block'; d.id = 'grow'; d.style.gridColumn = '1/25';
      d.innerHTML = '<div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><p>new line</p><p>another</p><p>and one more</p></div></div></div>';
      document.getElementById('ffe').appendChild(d);
    });
    await p.waitForTimeout(150);
    const grown = await p.evaluate(probe);
    assert(grown.fh > r.fh && grown.sp.h === grown.fh, `footer grows ${r.fh}→${grown.fh}: spacer follows (${grown.sp.h})`);
    await p.evaluate(() => document.getElementById('grow').remove());
    await p.waitForTimeout(150);
    assert((await p.evaluate(probe)).sp.h === r.fh, 'footer shrinks back: spacer follows');

    // 4. Editor class → full teardown, then re-init on exit
    await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
    await p.waitForTimeout(100);
    const ed = await p.evaluate(() => {
      const f = document.getElementById('footer-sections'), m = document.getElementById('page');
      return { n: document.querySelectorAll('[class*="swtl-cf-"]').length, sp: !!document.querySelector('.swtl-cf-spacer'),
        html: document.documentElement.getAttribute('style'), fstyle: f.getAttribute('style'), pos: getComputedStyle(f).position,
        flow: Math.abs(f.getBoundingClientRect().top - m.getBoundingClientRect().bottom) < 1 };
    });
    assert(ed.n === 0 && !ed.sp && !ed.html && !ed.fstyle && ed.pos === 'static' && ed.flow,
      `edit mode: footer back in normal flow, no classes/spacer/styles (${JSON.stringify(ed)})`);
    assert((await p.evaluate(heights)).join() === bare.join(), 'edit mode: layout identical to no-snippet page');
    await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
    await p.waitForTimeout(100);
    r = await p.evaluate(probe);
    assert(r.pos === 'fixed' && r.sp && r.sp.h === r.fh, 'leaving edit mode re-initialises');
    await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
    await p.waitForTimeout(100);
    assert(await p.evaluate(anyAdded) === 0, 'sqs-is-page-editing also tears down');

    // 5. Header guard: a positioned header with no z-index is lifted above the page
    await p.evaluate(() => { document.getElementById('header').style.zIndex = 'auto'; document.body.classList.remove('sqs-is-page-editing'); });
    await p.waitForTimeout(100);
    await p.evaluate(() => scrollTo(0, 400));
    const hd = await p.evaluate(() => ({ c: document.getElementById('header').classList.contains('swtl-cf-header'),
      hit: !!document.elementFromPoint(900, 38).closest('#header') }));
    assert(hd.c && hd.hit, 'fixed header without z-index stays above the page');
    await ctx.close();

    // 6. Tall footer: skipped, then enabled when it shrinks to fit
    ctx = await browser.newContext(ctxOpts);
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto('file://' + tallPath);
    await p.waitForTimeout(200);
    const t1 = await p.evaluate(() => ({ n: document.querySelectorAll('[class*="swtl-cf-"]').length, pos: getComputedStyle(document.getElementById('footer-sections')).position, fh: document.getElementById('footer-sections').offsetHeight }));
    assert(t1.n === 0 && t1.pos === 'static' && t1.fh > 720 * 0.85, `footer ${t1.fh}px > 85% of 720: skipped, scrolls normally`);
    await p.evaluate(() => document.getElementById('tallblock').remove());
    await p.waitForTimeout(150);
    r = await p.evaluate(probe);
    assert(r.pos === 'fixed' && r.sp && r.sp.h === r.fh, `footer shrinks to ${r.fh}px: curtain turns on`);
    await ctx.close();

    // 7. Editor frame guard
    ctx = await browser.newContext({ viewport: { width: 1400, height: 800 } });
    p = await ctx.newPage();
    await p.goto('file://' + frameHost);
    await p.waitForTimeout(400);
    assert(await p.frames()[1].evaluate(anyAdded) === 0, 'skipped inside editor frame');
    await ctx.close();

    // 8. Reduced motion: curtain stays, no parallax / fade
    ctx = await browser.newContext({ ...ctxOpts, reducedMotion: 'reduce' });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(150);
    const fhR = (await p.evaluate(probe)).fh;
    await p.evaluate(y => scrollTo(0, document.documentElement.scrollHeight - innerHeight - y), Math.round(fhR / 2));
    await p.waitForTimeout(120);
    r = await p.evaluate(probe);
    assert(r.pos === 'fixed' && r.sp, 'reduced motion: curtain kept');
    assert(!r.y && !r.o && (r.cwT === 'none' || r.cwT === 'matrix(1, 0, 0, 1, 0, 0)'), `reduced motion: no parallax (${JSON.stringify([r.y, r.o, r.cwT])})`);
    await ctx.close();

    assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  } finally {
    for (const f of [pagePath, barePath, tallPath, frameHost]) try { fs.unlinkSync(f); } catch (e) {}
  }
}
