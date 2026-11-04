// Real-Chrome functional test for the page-transition wipe.
// Run: node ../../shared/harness/run.mjs x "$(pwd)/browser.test.mjs"
// Starts a tiny local http server (same-origin navigation, bfcache, a slow
// script for the fail-safe, a 204 for the stuck guard) and stops it at the end.
// Nothing is written to disk.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '/opt/npm-tools/node_modules/playwright/index.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/header-injection.html'), 'utf8');

// Probe: records (in sessionStorage, which survives the navigation) whether a
// panel ever appeared on a page, and whether the page started covered.
const PROBE = `<script>
window.__cover = document.documentElement.classList.contains('swtl-pt-cover');
window.__coverText = getComputedStyle(document.documentElement, '::before').content;
window.__persisted = false;
addEventListener('pageshow', function (e) { if (e.persisted) window.__persisted = true; });
new MutationObserver(function () {
  if (!window.__seen && document.getElementById('swtl-pt-panel')) {
    window.__seen = true;
    try { sessionStorage.setItem('probePanel', (sessionStorage.getItem('probePanel') || '') + location.pathname + ';'); } catch (e) {}
  }
}).observe(document.documentElement, { childList: true, subtree: true });
</script>`;

let PORT = 0;
const links = () => `
<nav id="links">
  <a id="go-work" href="/b.html">Work</a>
  <a id="go-slow" href="/slow.html">Slow</a>
  <a id="go-204" href="/nav204">Nowhere</a>
  <a id="go-blank" href="/b.html" target="_blank">Blank</a>
  <a id="go-download" href="/file.txt" download>Download</a>
  <a id="go-hash" href="#sec">Hash</a>
  <a id="go-hash-full" href="/a.html#sec">Hash full</a>
  <a id="go-mailto" href="mailto:hi@example.com">Mail</a>
  <a id="go-tel" href="tel:+15555550100">Tel</a>
  <a id="go-external" href="http://localhost:${PORT}/b.html">External</a>
  <a id="go-cart" href="/cart">Cart</a>
  <a id="go-account" href="/account/orders">Account</a>
  <a id="go-image" href="/photo.jpg">Image</a>
  <div class="gallery-grid"><a id="go-gallery" href="/b.html">Gallery item</a></div>
  <a id="go-off" href="/b.html" data-swtl-pt="off">Opt-out</a>
</nav>`;
const section = h => `<section class="page-section" id="sec"><div class="content-wrapper"><div class="fluid-engine"><div class="fe-block" style="grid-column:1/13"><div class="sqs-block"><div class="sqs-block-content"><h1>${h}</h1></div></div></div></div></div></section>`;
const page = ({ head = '', body = '', bodyClass = '' } = {}) =>
  mock.replace('<!--HEAD-->', head + snippet + PROBE).replace('<!--BODY-->', body).replace('class=""', `class="${bodyClass}"`);

const routes = {
  '/a.html': () => page({ body: links() + section('Spaces built to be lived in.') }),
  '/a-notrans.html': () => page({ head: '<style>#swtl-pt-panel{transition:none!important}</style>', body: links() + section('A') }),
  '/a-stuck.html': () => page({ head: '<script>window.SwtlPageTransition={stuckAfter:700}</script>', body: links() + section('A') }),
  '/a-edit.html': () => page({ body: links() + section('A'), bodyClass: 'sqs-edit-mode-active' }),
  '/a-fixed.html': () => page({ head: '<script>window.SwtlPageTransition={label:"Studio"}</script>', body: links() + section('A') }),
  '/b.html': () => page({ body: section('Selected work') }),
  '/slow.html': () => page({ body: section('Slow page') + '<script src="/slow.js"></script><p>after</p>' }),
  '/frame.html': () => '<!doctype html><iframe src="/a.html" width="900" height="600"></iframe>',
};

const server = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x');
  if (u.pathname === '/slow.js') { setTimeout(() => { res.writeHead(200, { 'content-type': 'text/javascript' }); res.end('window.__slow=1'); }, 4000); return; }
  if (u.pathname === '/nav204') { res.writeHead(204); res.end(); return; }
  if (u.pathname === '/file.txt') { res.writeHead(200, { 'content-type': 'text/plain' }); res.end('file'); return; }
  const r = routes[u.pathname];
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(r ? r() : page({ body: section('Page ' + u.pathname) }));
});

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }
const wait = ms => new Promise(r => setTimeout(r, ms));
const panelTop = p => p.evaluate(() => { const e = document.getElementById('swtl-pt-panel'); return e ? Math.round(e.getBoundingClientRect().top) : null; });
const coverState = p => p.evaluate(() => ({
  panel: !!document.getElementById('swtl-pt-panel'),
  cls: document.documentElement.className.includes('swtl-pt'),
  style: document.documentElement.getAttribute('style') || '',
  ready: document.readyState,
}));
const probe = p => p.evaluate(() => sessionStorage.getItem('probePanel') || '');

export default async function (browser) {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  PORT = server.address().port;
  const base = `http://127.0.0.1:${PORT}`;
  const errors = [];
  const fresh = async (opts = {}) => {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, ...opts });
    const p = await ctx.newPage();
    p.on('pageerror', e => errors.push(e.message));
    return { ctx, p };
  };
  const shots = process.env.SHOTS;

  try {
    // 1. Internal click: panel wipes up, navigation, next page covered then revealed
    let { ctx, p } = await fresh();
    await p.goto(base + '/a.html');
    assert(!(await coverState(p)).cls && !(await coverState(p)).panel, 'first load: no cover (only covers navigations it started)');
    const t0 = Date.now();
    await p.click('#go-work');
    await wait(150);
    const midTop = await panelTop(p);
    if (shots) await p.screenshot({ path: `${shots}/pt-in.png` });
    assert(midTop !== null && midTop > 0 && midTop < 700, `panel wiping up over page A (top ${midTop}px)`);
    assert(p.url().endsWith('/a.html'), 'still on page A while the panel wipes');
    assert(await p.evaluate(() => document.querySelector('#swtl-pt-panel .swtl-pt-label')?.textContent) === 'Work', 'label = clicked link text');
    await p.waitForURL('**/b.html', { waitUntil: 'commit' });
    const navAt = Date.now() - t0;
    assert(navAt >= 450 && navAt < 1400, `navigates after the wipe (${navAt}ms)`);
    await p.waitForLoadState('domcontentloaded');
    assert(await p.evaluate(() => window.__cover), 'page B: covered from first paint (html.swtl-pt-cover in <head>)');
    assert(/Work/.test(await p.evaluate(() => window.__coverText)), 'page B: first-paint cover carries the label');
    await wait(260);
    const outTop = await panelTop(p);
    if (shots) await p.screenshot({ path: `${shots}/pt-out.png` });
    assert(outTop !== null && outTop < -20 && outTop > -720, `page B: panel wiping up and off (top ${outTop}px)`);
    await wait(700);
    let st = await coverState(p);
    assert(!st.panel && !st.cls && st.style === '', 'page B: panel removed, no class or inline style left on <html>');
    assert(await p.evaluate(() => sessionStorage.getItem('swtlPtCover')) === null, 'page B: session flag consumed');
    const heights = await p.evaluate(() => [...document.querySelectorAll('.page-section, .fe-block, .sqs-block')]
      .filter(e => /height/.test(e.getAttribute('style') || '')).length);
    assert(heights === 0, 'no inline height on Squarespace elements');

    // 2. Back button: page A must not come back covered. Playwright launches
    // Chrome with --disable-back-forward-cache, so a second Chrome without that
    // flag is used to exercise a real bfcache restore.
    await p.goBack();
    await wait(150);
    st = await coverState(p);
    assert(!st.panel && !st.cls, 'back to A (normal reload): no stuck cover');
    const bf = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'], ignoreDefaultArgs: ['--disable-back-forward-cache'] });
    try {
      const bctx = await bf.newContext({ viewport: { width: 1280, height: 720 } });
      const bp = await bctx.newPage();
      bp.on('pageerror', e => errors.push(e.message));
      await bp.goto(base + '/a.html');
      await bp.click('#go-work');
      await bp.waitForURL('**/b.html');
      await wait(1000);
      await bp.goBack({ waitUntil: 'commit' });
      await wait(200);
      const persisted = await bp.evaluate(() => window.__persisted);
      st = await coverState(bp);
      assert(persisted, 'bfcache: Back restored page A from the bfcache (pageshow persisted=true)');
      assert(!st.panel && !st.cls, 'bfcache: restored page A shows no stuck cover');
      await bp.click('#go-work');
      await bp.waitForURL('**/b.html', { timeout: 2000 });
      assert(true, 'bfcache: links work again after the restore');
      await bctx.close();
    } finally { await bf.close(); }
    // and the handler itself, on a page that is covered right now (204 = no navigation)
    await p.goto(base + '/a.html');
    await p.click('#go-204');
    await wait(700);
    assert(await panelTop(p) === 0, '204 response: page A stays covered (no navigation happened)');
    await p.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })));
    st = await coverState(p);
    assert(!st.panel && !st.cls, 'pageshow persisted=true removes the cover');
    await ctx.close();

    // 3. Skip cases: plain navigation (or none), never a panel
    const skips = [
      ['#go-blank', 'target=_blank', false],
      ['#go-download', 'download attribute', false],
      ['#go-hash', 'hash-only link (#sec)', false],
      ['#go-hash-full', 'same-page link with hash (/a.html#sec)', false],
      ['#go-mailto', 'mailto:', false],
      ['#go-tel', 'tel:', false],
      ['#go-external', 'external origin', '**/b.html'],
      ['#go-cart', '/cart path', '**/cart'],
      ['#go-account', '/account path', '**/account/orders'],
      ['#go-image', 'link to an image file (lightbox)', '**/photo.jpg'],
      ['#go-gallery', 'link inside a gallery/lightbox', '**/b.html'],
      ['#go-off', 'data-swtl-pt="off" opt-out', '**/b.html'],
    ];
    for (const [sel, name, nav] of skips) {
      ({ ctx, p } = await fresh());
      await p.goto(base + '/a.html');
      await p.click(sel);
      if (nav) {
        await p.waitForURL(nav, { timeout: 3000 });
        await p.waitForLoadState('domcontentloaded');
        const covered = await p.evaluate(() => !!window.__cover).catch(() => false);
        const seen = await probe(p).catch(() => '');
        assert(!covered && seen === '', `skip: ${name} → plain navigation, no panel`);
      } else {
        await wait(300);
        st = await coverState(p);
        assert(!st.panel && !st.cls && (await probe(p)) === '' && p.url().includes('/a.html'), `skip: ${name} → no panel`);
      }
      await ctx.close();
    }
    // modifier and middle clicks (new tab / background tab)
    for (const [opts, name] of [[{ modifiers: ['Control'] }, 'Ctrl+click'], [{ modifiers: ['Meta'] }, 'Cmd+click'],
      [{ modifiers: ['Shift'] }, 'Shift+click'], [{ button: 'middle' }, 'middle click']]) {
      ({ ctx, p } = await fresh());
      await p.goto(base + '/a.html');
      await p.click('#go-work', opts);
      await wait(300);   // Linux Chrome treats Meta+click as a plain click: navigation is fine, a panel is not
      st = await coverState(p);
      const cov = await p.evaluate(() => !!window.__cover);
      assert(!st.panel && !cov && (await probe(p)) === '', `skip: ${name} → no panel (${p.url().endsWith('/a.html') ? 'page A untouched' : 'plain navigation'})`);
      await ctx.close();
    }

    // 4. Fail-safe: next page's HTML stalls on a slow script → reveal at maxWait anyway
    ({ ctx, p } = await fresh());
    await p.goto(base + '/a.html');
    await p.click('#go-slow');
    await p.waitForURL('**/slow.html', { waitUntil: 'commit' });
    await wait(1200);
    st = await coverState(p);
    assert((st.cls || st.panel) && st.ready === 'loading', `slow page: still covered while HTML parses (${st.ready})`);
    await wait(2300);
    st = await coverState(p);
    assert(!st.panel && !st.cls && st.ready === 'loading', 'fail-safe: revealed by maxWait (2.5s) before DOMContentLoaded');
    await ctx.close();

    // 5. Never block navigation
    ({ ctx, p } = await fresh());
    await p.goto(base + '/a-notrans.html');
    await p.click('#go-work');
    await p.waitForURL('**/b.html', { timeout: 1500 });
    assert(true, 'transitionend never fires → navigates on the timeout');
    await ctx.close();
    ({ ctx, p } = await fresh());
    await p.addInitScript(() => { Storage.prototype.setItem = function () { throw new Error('quota'); }; });
    await p.goto(base + '/a.html');
    await p.click('#go-work');
    await p.waitForURL('**/b.html', { timeout: 1500 });
    await p.waitForLoadState('domcontentloaded');
    st = await coverState(p);
    assert(!st.cls && !st.panel, 'sessionStorage throws → still navigates, next page simply uncovered');
    await ctx.close();
    ({ ctx, p } = await fresh());
    await p.goto(base + '/a-stuck.html');
    await p.click('#go-204');
    await wait(1500);
    st = await coverState(p);
    assert(!st.panel && !st.cls, 'no navigation (204) → panel dropped after stuckAfter');
    await p.click('#go-work');
    await p.waitForURL('**/b.html', { timeout: 1500 });
    assert(true, 'links still work after a stuck attempt');
    await ctx.close();

    // 6. Fixed label config
    ({ ctx, p } = await fresh());
    await p.goto(base + '/a-fixed.html');
    await p.click('#go-work');
    await wait(100);
    assert(await p.evaluate(() => document.querySelector('#swtl-pt-panel .swtl-pt-label')?.textContent) === 'Studio', 'config label: fixed wordmark');
    await p.waitForURL('**/b.html');
    await ctx.close();

    // 7. Editor: inside a frame, and with edit-mode body classes
    ({ ctx, p } = await fresh());
    await p.goto(base + '/frame.html');
    await wait(300);
    let inner = p.frames()[1];
    await inner.click('#go-work');
    await wait(150);
    inner = p.frames()[1];
    const innerPanel = await inner.evaluate(() => !!document.getElementById('swtl-pt-panel')).catch(() => false);
    assert(!innerPanel, 'framed (editor): click navigates without a panel');
    await wait(400);
    assert((p.frames()[1].url() || '').endsWith('/b.html'), 'framed: link still navigates');
    await ctx.close();
    ({ ctx, p } = await fresh());
    await p.goto(base + '/a-edit.html');
    await p.click('#go-work');
    await p.waitForURL('**/b.html', { timeout: 1500 });
    await p.waitForLoadState('domcontentloaded');
    assert((await probe(p)) === '' && !(await p.evaluate(() => window.__cover)), 'edit-mode body class: plain navigation');
    await ctx.close();

    // 8. Reduced motion: plain navigation, no cover
    ({ ctx, p } = await fresh({ reducedMotion: 'reduce' }));
    await p.goto(base + '/a.html');
    let r0 = Date.now();
    await p.click('#go-off');                         // baseline: a link the script never touches
    await p.waitForURL('**/b.html', { waitUntil: 'commit', timeout: 1500 });
    const baseAt = Date.now() - r0;
    await p.goto(base + '/a.html');
    await p.evaluate(() => sessionStorage.clear());
    r0 = Date.now();
    await p.click('#go-work');
    await p.waitForURL('**/b.html', { waitUntil: 'commit', timeout: 1500 });
    const rAt = Date.now() - r0;
    await p.waitForLoadState('domcontentloaded');
    assert((await probe(p)) === '' && !(await p.evaluate(() => window.__cover)) && rAt < baseAt + 200, `reduced motion: immediate plain navigation (${rAt}ms vs ${baseAt}ms untouched link), no panel`);
    await ctx.close();

    assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  } finally {
    server.close();
  }
}
