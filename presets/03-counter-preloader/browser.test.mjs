// Real-Chrome functional test for the counter preloader.
// Run: node ../../shared/harness/run.mjs x "$(pwd)/browser.test.mjs"
// Builds its own temp pages (.test-*.html) and deletes them at the end.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/header-injection.html'), 'utf8');
const BODY = '<section class="page-section"><div class="content-wrapper"><div class="fluid-engine"><div class="fe-block" style="grid-column:1/13"><div class="sqs-block"><div class="sqs-block-content"><h1>Spaces built to be lived in.</h1></div></div></div></div></div></section>' +
  '<div style="height:2000px"></div>';
const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--HEAD-->', snippet).replace('<!--BODY-->', BODY));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="800" height="600"></iframe>`);
// slow page: load is held open by a script that never finishes until 4s (file:// can't throttle)
const slowPath = path.join(here, '.test-slow.html');
fs.writeFileSync(slowPath, mock.replace('<!--HEAD-->', snippet).replace('<!--BODY-->', BODY +
  '<iframe id="hold" style="display:none"></iframe><script>(function(){var f=document.getElementById("hold");var d=f.contentDocument;d.open();window.__release=function(){d.close();};setTimeout(window.__release,4000);})();</script>'));

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }
const num = p => p.evaluate(() => { const n = document.querySelector('#swtl-ct-preloader .swtl-ct-num'); return n ? parseInt(n.textContent, 10) : null; });

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;
  try {
    // 1. Full sequence on a fresh session
    let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    let p = await ctx.newPage();
    const errors = [];
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(url, { waitUntil: 'commit' });
    await p.waitForSelector('#swtl-ct-preloader', { timeout: 2000 });
    assert(true, 'overlay mounts');
    assert(await p.evaluate(() => document.getElementById('swtl-ct-preloader').getAttribute('aria-hidden') === 'true'), 'overlay is aria-hidden');
    assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-ct-lock')), 'scroll locked while showing');
    await p.waitForTimeout(700);
    const mid = await num(p);
    assert(mid > 5 && mid < 90, `counter climbing while waiting (got ${mid})`);
    if (shots) await p.screenshot({ path: `${shots}/ct-0700.png` });
    await p.waitForTimeout(700);
    const late = await num(p);
    assert(late > mid && late < 90, `counter keeps climbing but holds under 90 before minShow (got ${late})`);
    // capture 100 before exit
    const hit100 = await p.waitForFunction(() => {
      const n = document.querySelector('#swtl-ct-preloader .swtl-ct-num'); return n && n.textContent === '100';
    }, null, { timeout: 3000, polling: 'raf' }).then(() => true, () => false);
    assert(hit100, 'counter text reaches 100');
    const barScale = await p.evaluate(() => getComputedStyle(document.querySelector('#swtl-ct-preloader .swtl-ct-bar')).transform);
    assert(barScale === 'matrix(1, 0, 0, 1, 0, 0)' || barScale === 'none', `bar full width at 100 (${barScale})`);
    if (shots) await p.screenshot({ path: `${shots}/ct-100.png` });
    await p.waitForTimeout(550);
    if (shots) await p.screenshot({ path: `${shots}/ct-wipe.png` });
    await p.waitForTimeout(1200);
    assert(await p.$('#swtl-ct-preloader') === null, 'overlay removed from DOM after dismiss');
    assert(!(await p.evaluate(() => document.documentElement.classList.contains('swtl-ct-lock'))), 'scroll unlocked');
    await p.mouse.wheel(0, 400); await p.waitForTimeout(200);
    assert(await p.evaluate(() => window.scrollY) > 0, 'page actually scrolls');
    const inlineH = await p.evaluate(() => [...document.querySelectorAll('.page-section, .fe-block, .sqs-block, .fluid-engine')].some(e => /height/.test(e.getAttribute('style') || '')));
    assert(!inlineH, 'no inline height written on Squarespace elements');
    assert(errors.length === 0, 'no page errors ' + errors.join(' | '));

    // 2. Once per session
    await p.reload();
    await p.waitForTimeout(100);
    assert(await p.$('#swtl-ct-preloader') === null, 'second page view skips preloader (once per session)');
    await ctx.close();

    // 3. Honest counter on a slow page: holds under 90 until load, then completes
    ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    p = await ctx.newPage();
    await p.goto('file://' + slowPath, { waitUntil: 'commit' });
    await p.waitForSelector('#swtl-ct-preloader');
    await p.waitForTimeout(3500);
    const held = await num(p);
    assert(held >= 80 && held < 90, `slow load: counter parks below 90 while waiting (got ${held})`);
    if (shots) await p.screenshot({ path: `${shots}/ct-slow.png` });
    await p.waitForFunction(() => { const n = document.querySelector('#swtl-ct-preloader .swtl-ct-num'); return n && n.textContent === '100'; }, null, { timeout: 3000, polling: 'raf' });
    assert(true, 'slow load: completes to 100 after load fires');
    await p.waitForTimeout(1500);
    assert(await p.$('#swtl-ct-preloader') === null, 'slow load: overlay removed');
    await ctx.close();

    // 4. ?nopreloader
    ctx = await browser.newContext();
    p = await ctx.newPage();
    await p.goto(url + '?nopreloader');
    assert(await p.$('#swtl-ct-preloader') === null, '?nopreloader skips it');
    await ctx.close();

    // 5. Inside a frame (the Squarespace editor) it never runs
    ctx = await browser.newContext();
    p = await ctx.newPage();
    await p.goto('file://' + frameHost);
    await p.waitForTimeout(400);
    const inner = p.frames()[1];
    assert(await inner.$('#swtl-ct-preloader') === null, 'skipped inside editor frame');
    assert(!(await inner.evaluate(() => document.documentElement.className.includes('swtl-ct'))), 'no classes added inside editor frame');
    await ctx.close();

    // 6. Reduced motion: no counting, fast fade exit
    ctx = await browser.newContext({ reducedMotion: 'reduce' });
    p = await ctx.newPage();
    const rmErrors = [];
    p.on('pageerror', e => rmErrors.push(e.message));
    await p.goto(url, { waitUntil: 'commit' });
    await p.waitForSelector('#swtl-ct-preloader');
    await p.waitForTimeout(150);
    const rv = await num(p);
    assert(rv === 0 || rv === 100, `reduced motion: no counting animation (got ${rv})`);
    await p.waitForTimeout(1200);
    assert(await p.$('#swtl-ct-preloader') === null, 'reduced motion: dismissed within ~1.3s');
    assert(!(await p.evaluate(() => document.documentElement.classList.contains('swtl-ct-lock'))), 'reduced motion: scroll unlocked');
    assert(rmErrors.length === 0, 'reduced motion: no page errors');
    await ctx.close();

    // 7. Config object
    ctx = await browser.newContext();
    p = await ctx.newPage();
    await p.addInitScript(() => { window.SwtlCounter = { oncePerSession: false, minShow: 600 }; });
    await p.goto(url);
    await p.waitForTimeout(2900);
    assert(await p.$('#swtl-ct-preloader') === null, 'window.SwtlCounter minShow override shortens the run');
    await p.reload(); await p.waitForTimeout(100);
    assert(await p.$('#swtl-ct-preloader') !== null, 'window.SwtlCounter oncePerSession:false replays');
    await ctx.close();
  } finally {
    for (const f of [pagePath, frameHost, slowPath]) try { fs.unlinkSync(f); } catch (e) {}
  }
}
