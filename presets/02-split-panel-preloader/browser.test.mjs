// Real-Chrome functional test for the split-panel preloader.
// Run: node ../../shared/harness/run.mjs x "$(pwd)/browser.test.mjs"
// Writes temp pages .test-*.html next to this file and deletes them at the end.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/header-injection.html'), 'utf8');
const BODY = '<section class="page-section"><div class="content-wrapper"><div class="fluid-engine"><div class="fe-block" style="grid-column:1/13"><div class="sqs-block"><div class="sqs-block-content"><h1>Spaces built to be lived in.</h1></div></div></div></div></div></section>';
const write = (name, head) => {
  const f = path.join(here, name);
  fs.writeFileSync(f, mock.replace('<!--HEAD-->', head).replace('<!--BODY-->', BODY));
  return f;
};
const pagePath = write('.test-page.html', snippet);
const horizPath = write('.test-horiz.html',
  '<script>window.SwtlSplitPanel = { panels: 3, direction: "horizontal", oncePerSession: false };</script>' + snippet);
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="800" height="600"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }
const panelX = p => p.evaluate(() => [...document.querySelectorAll('#swtl-sp-preloader .swtl-sp-panel')]
  .map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top)]; }));

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;
  try {
    // 1. Full sequence on a fresh session
    let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    let p = await ctx.newPage();
    const errors = [];
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url);
    await p.waitForTimeout(150);
    assert(await p.$('#swtl-sp-preloader') !== null, 'overlay mounts');
    assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-sp-lock')), 'scroll locked while showing');
    assert((await p.$$('#swtl-sp-preloader .swtl-sp-panel')).length === 2, 'two panels by default');
    assert(await p.$('#swtl-sp-preloader svg.swtl-sp-mark') !== null, 'logo cloned from <template>');
    const before = await panelX(p);
    assert(before[0][0] === 0 && before[1][0] === 640, `panels cover the screen at rest (${JSON.stringify(before)})`);
    if (shots) { await p.waitForTimeout(1000); await p.screenshot({ path: `${shots}/sp-hold.png` }); }
    await p.waitForTimeout(shots ? 1600 : 2600);   // ~2.8s: mid-part
    const mid = await panelX(p);
    if (shots) await p.screenshot({ path: `${shots}/sp-part.png` });
    assert(mid[0][0] < -40 && mid[1][0] > 680, `panels animate apart (${JSON.stringify(mid)})`);
    assert(-mid[0][0] > mid[1][0] - 640, 'left panel leads (stagger)');
    const done = await p.evaluate(() => document.getElementById('swtl-sp-preloader').classList.contains('swtl-sp-done'));
    assert(done, 'done class set (pointer-events off) during reveal');
    await p.waitForTimeout(1100);
    assert(await p.$('#swtl-sp-preloader') === null, 'overlay removed from DOM after dismiss');
    assert(!(await p.evaluate(() => document.documentElement.classList.contains('swtl-sp-lock'))), 'scroll unlocked');
    assert(!(await p.evaluate(() => document.documentElement.classList.contains('swtl-sp-init'))), 'init cover class removed');
    const heights = await p.evaluate(() => [...document.querySelectorAll('.page-section, .fe-block, .sqs-block')]
      .filter(e => /height/.test(e.getAttribute('style') || '')).length);
    assert(heights === 0, 'no inline height on Squarespace elements');
    assert(errors.length === 0, 'no page errors ' + errors.join(' | '));

    // 2. Once per session: second load renders instantly
    await p.reload();
    await p.waitForTimeout(100);
    assert(await p.$('#swtl-sp-preloader') === null, 'second page view skips preloader (once per session)');
    assert(!(await p.evaluate(() => document.documentElement.className.includes('swtl-sp'))), 'no classes left on <html> on repeat view');
    await ctx.close();

    // 3. ?nopreloader skips
    ctx = await browser.newContext();
    p = await ctx.newPage();
    await p.goto(url + '?nopreloader');
    await p.waitForTimeout(150);
    assert(await p.$('#swtl-sp-preloader') === null, '?nopreloader skips it');
    await ctx.close();

    // 4. Inside a frame (the Squarespace editor) it never runs
    ctx = await browser.newContext();
    p = await ctx.newPage();
    await p.goto('file://' + frameHost);
    await p.waitForTimeout(400);
    const inner = p.frames()[1];
    assert(await inner.$('#swtl-sp-preloader') === null, 'skipped inside editor frame');
    assert(!(await inner.evaluate(() => document.documentElement.className.includes('swtl-sp'))), 'no cover class inside editor frame');
    await ctx.close();

    // 5. Config: 3 horizontal panels part up/down
    ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    await p.goto('file://' + horizPath);
    await p.waitForTimeout(150);
    assert((await p.$$('#swtl-sp-preloader .swtl-sp-panel')).length === 3, 'config: panels: 3');
    await p.waitForTimeout(2700);
    const h = await panelX(p);
    assert(h[0][1] < -40 && h[2][1] > 480 + 20 && h[1][0] > 40, `horizontal: top up, bottom down, middle out sideways (${JSON.stringify(h)})`);
    await p.waitForTimeout(1200);
    assert(await p.$('#swtl-sp-preloader') === null, 'horizontal: removed after reveal');
    assert(errors.length === 0, 'no page errors (config run)');
    await ctx.close();

    // 6. Reduced motion: static logo, fast fade, no panel motion
    ctx = await browser.newContext({ reducedMotion: 'reduce' });
    p = await ctx.newPage();
    await p.goto(url);
    await p.waitForTimeout(150);
    const anim = await p.evaluate(() => {
      const c = document.querySelector('#swtl-sp-preloader .swtl-sp-center');
      return c ? getComputedStyle(c).animationName : 'missing';
    });
    assert(anim === 'none', `reduced motion: logo shown without intro animation (${anim})`);
    await p.waitForTimeout(300);
    const moved = await p.evaluate(() => [...document.querySelectorAll('#swtl-sp-preloader .swtl-sp-panel')].some(e => e.style.transform));
    assert(!moved, 'reduced motion: panels never slide');
    await p.waitForTimeout(500);
    assert(await p.$('#swtl-sp-preloader') === null, 'reduced motion: dismissed within ~1s');
    assert(!(await p.evaluate(() => document.documentElement.classList.contains('swtl-sp-lock'))), 'reduced motion: scroll unlocked');
    await ctx.close();
  } finally {
    for (const f of [pagePath, horizPath, frameHost]) fs.rmSync(f, { force: true });
  }
}
