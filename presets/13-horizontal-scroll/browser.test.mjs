// Real-Chrome functional test for the horizontal scroll gallery.
// Run: node ../../shared/harness/run.mjs "$(pwd)/.test-page.html" "$(pwd)/browser.test.mjs"
// Builds a 7.1-shaped page (#siteWrapper > main#page > article.sections >
// section.page-section…) with a fixed header, an overflow-x:hidden wrapper,
// flex sections (as 7.1 lays them out) and a carousel List Section whose
// slides carry the inline transform the native carousel writes. Removes its
// temp pages after.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

const fe = (i, h, withMarker) => `<section class="page-section" data-section-id="s${i}" id="s${i}">
  <div class="section-background" style="position:absolute;inset:0;background:#F4F1EA"></div>
  <div class="content-wrapper"><div class="content"><div class="fluid-engine">
   <div class="fe-block" style="grid-column:1/13"><div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><h1>${h}</h1></div></div></div></div>
   <div class="fe-block" style="grid-column:13/25"><div class="sqs-block image-block"><div class="sqs-block-content"><div class="img"></div></div></div></div>
   ${withMarker ? `<div class="fe-block" style="grid-column:23/25"><div class="sqs-block code-block"><div class="sqs-block-content">${marker}</div></div></div>` : ''}
  </div></div></div></section>`;
const works = ['Harbor House', 'Mill Lofts', 'Ridge Studio', 'Orchard Hall', 'North Pier'];
const list = `<section class="page-section user-items-list-section" data-section-id="work" id="work">
  <div class="section-background" style="position:absolute;inset:0;background:#1F1E1C"></div>
  <div class="content-wrapper"><div class="user-items-list"><div class="user-items-list-carousel">
   <div class="list-section-title"><p>Selected work</p></div>
   <div class="user-items-list-carousel__gutter">
    <div class="user-items-list-carousel__slideshow-holder">
     <ul class="user-items-list-carousel__slides" style="transform: translateX(0px);">
      ${works.map((w, i) => `<li class="list-item user-items-list-carousel__slide"><div class="list-item-media"><div class="list-item-media-inner"></div></div>
        <div class="list-item-content"><h2 class="list-item-content__title">${w}</h2><div class="list-item-content__description"><p>${2020 + i}</p></div></div></li>`).join('')}
     </ul>
    </div>
    <div class="desktop-arrows"><button class="user-items-list-carousel__arrow-button">prev</button><button class="user-items-list-carousel__arrow-button">next</button></div>
   </div>
  </div></div></div></section>`;
const body = `<article class="sections">${fe(0, 'Studio intro', true)}${list}${fe(2, 'About')}${fe(3, 'Contact')}</article>`;
const extraCss = `<style>
 header#header{position:fixed;top:0;left:0;right:0;z-index:100;background:#F4F1EA;box-sizing:border-box}
 main#page{overflow-x:hidden;padding-top:76px}
 .page-section{display:flex;align-items:center;padding:60px 0;overflow:hidden}
 .content-wrapper{position:relative;width:100%;box-sizing:border-box}
 .img{height:auto;aspect-ratio:4/3}
 .user-items-list-section{color:#F4F1EA}
 .list-section-title p{font-size:32px;margin:0 0 32px}
 .user-items-list-carousel__slideshow-holder{overflow:hidden}
 .user-items-list-carousel__slides{display:grid;grid-auto-flow:column;grid-auto-columns:calc((100% - 48px) / 3);gap:24px;margin:0;padding:0;list-style:none;transition:transform .5s}
 .list-item-media-inner{aspect-ratio:4/3;background:#3A3833}
 .list-item-content__title{font-size:22px;margin:16px 0 4px}
 .list-item-content__description p{margin:0;color:#8C877E}
 .desktop-arrows{display:flex;gap:8px;margin-top:24px}
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

// every inline style that mentions height, on anything that is not the script's own spacer
const sqsHeights = () => [...document.querySelectorAll('[style]')]
  .filter(el => !el.classList.contains('swtl-hs-spacer') && /(^|;)\s*(min-|max-)?height\s*:/.test(el.getAttribute('style')))
  .map(el => el.className || el.tagName);
const added = () => document.querySelectorAll('[class*="swtl-hs-"]').length;
const read = () => {
  const cw = document.querySelector('#work .content-wrapper');
  const tr = document.querySelector('#work .user-items-list-carousel__slides');
  const ho = tr.parentElement;
  const m = new DOMMatrix(getComputedStyle(tr).transform);
  return { top: cw.getBoundingClientRect().top, x: m.m41, trackW: tr.scrollWidth, viewW: ho.clientWidth,
    p: parseFloat(document.querySelector('.swtl-hs-bar')?.style.getPropertyValue('--swtl-hs-p') || 0),
    sticky: getComputedStyle(cw).position === 'sticky' };
};

export default async function (browser) {
  const url = 'file://' + pagePath;
  const errors = [];
  const shots = process.env.SHOTS;

  try {
    // 0. reference layout without the snippet
    let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    let p = await ctx.newPage();
    await p.goto('file://' + barePath);
    // the script hides the native arrows, so compare against that same layout
    const bare = await p.evaluate(() => (document.querySelector('.desktop-arrows').style.display = 'none', {
      sec: document.getElementById('work').offsetHeight,
      cw: document.querySelector('#work .content-wrapper').offsetHeight,
      style: document.querySelector('#work .user-items-list-carousel__slides').getAttribute('style') }));
    const bareSec = await p.evaluate(() => (document.querySelector('.desktop-arrows').style.display = '', document.getElementById('work').offsetHeight));
    await ctx.close();

    // 1. Desktop
    ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(200);
    const lay = await p.evaluate(() => {
      const sp = document.querySelectorAll('.swtl-hs-spacer');
      return { n: sp.length, aria: sp[0] && sp[0].getAttribute('aria-hidden'), parent: sp[0] && sp[0].parentElement.id,
        h: sp[0] ? sp[0].offsetHeight : 0, sec: document.getElementById('work').offsetHeight,
        cw: document.querySelector('#work .content-wrapper').offsetHeight,
        others: ['s0', 's2', 's3'].filter(id => document.getElementById(id).className.includes('swtl-hs')),
        unclip: document.getElementById('page').classList.contains('swtl-hs-unclip') &&
                document.getElementById('work').classList.contains('swtl-hs-unclip'),
        stickTop: getComputedStyle(document.querySelector('#work .content-wrapper')).top };
    });
    const r0 = await p.evaluate(read);
    const dist = r0.trackW - r0.viewW;
    assert(lay.n === 1 && lay.parent === 'work' && lay.aria === 'true', `one aria-hidden spacer, inside the marked-next List Section (${JSON.stringify(lay)})`);
    assert(dist > 300 && Math.abs(lay.h - dist) < 1, `spacer height = trackW - viewW (${lay.h} vs ${dist})`);
    assert(lay.sec === bare.sec + lay.h && lay.cw === bare.cw, `section grows only by the spacer; content-wrapper height unchanged (${lay.sec} = ${bare.sec}+${lay.h}, cw ${lay.cw}/${bare.cw})`);
    assert(lay.others.length === 0, 'marker section and following sections untouched');
    assert(lay.unclip, 'overflow:hidden ancestors (main#page, section) switched to clip');
    assert(lay.stickTop === '76px', `headerOffset auto: sticky top = fixed header (${lay.stickTop})`);
    assert((await p.evaluate(sqsHeights)).length === 0, 'no inline height on any Squarespace element (spacer is the script\'s own)');
    assert(await p.evaluate(() => getComputedStyle(document.querySelector('.desktop-arrows')).display === 'none'), 'native carousel arrows hidden while driven');

    const start = await p.evaluate(() => document.querySelector('#work .content-wrapper').getBoundingClientRect().top + scrollY - 76);
    const samples = [];
    for (const dy of [-200, 0, 0.25, 0.5, 0.75, 1, 1.0001]) {
      const y = dy <= 0 ? start + dy : start + dist * dy;
      await p.evaluate(v => scrollTo(0, v), y);
      await p.waitForTimeout(60);
      samples.push(await p.evaluate(read));
    }
    const pin = samples.slice(1, 6);
    assert(samples[0].x === 0 && samples[0].top > 76, `before pin: track at 0, section below header (top ${samples[0].top.toFixed(1)})`);
    assert(pin.every(s => Math.abs(s.top - 76) < 1.5), `pins under the header across the whole travel (${pin.map(s => s.top.toFixed(1))})`);
    const xs = samples.map(s => s.x);
    assert(xs.every((x, i) => i === 0 || x <= xs[i - 1] + 0.01), `translateX monotonic (${xs.map(x => x.toFixed(0))})`);
    assert(Math.abs(pin[2].x + dist * 0.5) < 2, `mid-travel x = -dist/2 (${pin[2].x.toFixed(1)} vs ${-dist / 2})`);
    assert(Math.abs(pin[4].x + dist) < 1, `end of travel x = -(trackW - viewW) (${pin[4].x.toFixed(1)} vs ${-dist})`);
    assert(Math.abs(pin[2].p - 0.5) < 0.01 && pin[4].p > 0.999, `progress hairline tracks (${pin.map(s => s.p.toFixed(2))})`);
    if (shots) await p.screenshot({ path: `${shots}/hs-desktop.png` });

    await p.evaluate(() => { document.querySelector('.user-items-list-carousel__slides').style.transform = 'translateX(-500px)'; });
    assert(Math.abs((await p.evaluate(read)).x + dist) < 1, 'native carousel inline transform cannot fight the scroll-driven one');
    await p.evaluate(() => { document.querySelector('.user-items-list-carousel__slides').style.transform = 'translateX(0px)'; });

    await p.evaluate(v => scrollTo(0, v), start + dist + 300);
    await p.waitForTimeout(80);
    const after = await p.evaluate(read);
    assert(after.top < 76 - 250 && Math.abs(after.x + dist) < 1, `unpins after the travel and scrolls away at rest (top ${after.top.toFixed(1)}, x ${after.x.toFixed(1)})`);

    // rAF only while the section is on screen
    await p.evaluate(() => scrollTo(0, 0));
    await p.waitForTimeout(150);
    const rafs = await p.evaluate(async () => {
      let n = 0; const o = requestAnimationFrame;
      window.requestAnimationFrame = f => { n++; return o(f); };
      for (let i = 0; i < 5; i++) { scrollTo(0, i * 4); await new Promise(r => setTimeout(r, 30)); }
      window.requestAnimationFrame = o;
      return n;
    });
    assert(rafs === 0, `no rAF while the gallery is off screen (${rafs})`);

    // 2. Editor class → teardown, re-init on exit
    await p.evaluate(v => scrollTo(0, v), start + dist * 0.5);
    await p.waitForTimeout(60);
    await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
    await p.waitForTimeout(700);   // the carousel's own .5s transition eases the track home
    const ed = await p.evaluate(() => ({ n: document.querySelectorAll('[class*="swtl-hs-"]').length,
      spacer: document.querySelectorAll('.swtl-hs-spacer, .swtl-hs-bar').length,
      style: document.querySelector('#work .user-items-list-carousel__slides').getAttribute('style'),
      cw: document.querySelector('#work .content-wrapper').getAttribute('style'),
      h: document.getElementById('work').offsetHeight,
      x: new DOMMatrix(getComputedStyle(document.querySelector('#work .user-items-list-carousel__slides')).transform).m41 }));
    assert(ed.n === 0 && ed.spacer === 0, `edit mode: spacer + bar removed, no classes (${JSON.stringify(ed)})`);
    assert(ed.style === bare.style && ed.cw === null && ed.x === 0 && ed.h === bareSec, 'edit mode: transforms cleared, section back to the editor layout');
    await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
    await p.waitForTimeout(100);
    const re = await p.evaluate(read);
    assert(re.sticky && Math.abs(re.x + dist * 0.5) < 2, `leaving edit mode re-inits at the current scroll (x ${re.x.toFixed(1)})`);
    await p.evaluate(() => document.body.classList.add('sqs-is-page-editing'));
    await p.waitForTimeout(80);
    assert(await p.evaluate(added) === 0, 'sqs-is-page-editing also tears down');
    await p.evaluate(() => document.body.classList.remove('sqs-is-page-editing'));
    await ctx.close();

    // 3. Mobile: native swipe row with scroll-snap, no pin
    const swipeCheck = async (pg, label) => {
      const m = await pg.evaluate(() => {
        const tr = document.querySelector('#work .user-items-list-carousel__slides'), ho = tr.parentElement;
        const cs = getComputedStyle(ho);
        ho.scrollLeft = tr.children[1].offsetLeft - 10;
        return { spacer: document.querySelectorAll('.swtl-hs-spacer').length, sticky: getComputedStyle(tr.closest('.content-wrapper')).position === 'sticky',
          ox: cs.overflowX, snap: cs.scrollSnapType, align: getComputedStyle(tr.children[0]).scrollSnapAlign,
          t: getComputedStyle(tr).transform, sw: ho.scrollWidth > ho.clientWidth };
      });
      await pg.waitForTimeout(400);
      const sl = await pg.evaluate(() => document.querySelector('#work .user-items-list-carousel__slideshow-holder').scrollLeft);
      assert(m.spacer === 0 && !m.sticky, `${label}: no spacer, no pin`);
      assert(m.ox === 'auto' && /x mandatory/.test(m.snap) && m.align.includes('start') && m.t === 'none' && m.sw && sl > 0,
        `${label}: track is a native scroll-snap row (${JSON.stringify(m)}, scrollLeft ${sl})`);
    };
    ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(150);
    await swipeCheck(p, 'mobile 390px');
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.waitForTimeout(200);
    assert((await p.evaluate(read)).sticky && await p.evaluate(() => document.querySelectorAll('.swtl-hs-spacer, .swtl-hs-swipe').length === 1),
      'widening past the breakpoint switches to pin mode');
    await p.setViewportSize({ width: 600, height: 800 });
    await p.waitForTimeout(200);
    await swipeCheck(p, 'narrowing below 768px');
    await ctx.close();

    // 4. Editor frame guard
    ctx = await browser.newContext({ viewport: { width: 1400, height: 800 } });
    p = await ctx.newPage();
    await p.goto('file://' + frameHost);
    await p.waitForTimeout(400);
    assert(await p.frames()[1].evaluate(added) === 0, 'skipped inside editor frame');
    await ctx.close();

    // 5. Reduced motion: native swipe row, no pin
    ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, reducedMotion: 'reduce' });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(150);
    await swipeCheck(p, 'reduced motion');
    await ctx.close();

    assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  } finally {
    for (const f of [pagePath, barePath, frameHost]) try { fs.unlinkSync(f); } catch (e) {}
  }
}
