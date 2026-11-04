// Real-Chrome functional test for the image scale-settle effect.
// Run: node ../../shared/harness/run.mjs x "$(pwd)/browser.test.mjs"
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/footer-injection.html'), 'utf8');
const marker = fs.readFileSync(path.join(here, 'snippets/code-block-marker.html'), 'utf8');

// --- tiny local PNGs (no network, no deps): striped gradient tiles
function png(w, h, seed) {
  const crcT = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crcT[n] = c >>> 0; }
  const crc = b => { let c = ~0; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (~c) >>> 0; };
  const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };
  const raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * 3 + 1)] = 0; for (let x = 0; x < w; x++) { const o = y * (w * 3 + 1) + 1 + x * 3; const s = ((x + y + seed * 7) >> 4) & 1; raw[o] = 120 + s * 80; raw[o + 1] = 90 + (y * 120 / h); raw[o + 2] = 70 + seed * 40; } }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}
const assets = fs.mkdtempSync(path.join(os.tmpdir(), 'swtl-ss-'));
const imgs = [0, 1, 2].map(i => { const f = path.join(assets, `img${i}.png`); fs.writeFileSync(f, png(480, 360, i)); return 'file://' + f; });

// Realistic Fluid Engine DOM: hero with .section-background img, a marked
// section with two image blocks (one with a clipping shape container like
// Squarespace's, one with no clipping wrapper), and an unmarked section.
const imageBlock = (id, src, clipWrap) => `
  <div class="fe-block fe-block-${id}" style="grid-area:1/${id === 'a' ? '1/2/12' : '13/2/25'}">
    <div class="sqs-block image-block sqs-block-image" data-block-type="5" id="block-${id}">
      <div class="sqs-block-content">
        <div class="image-block-outer-wrapper"><figure class="sqs-block-image-figure" style="margin:0">
          <div class="image-block-wrapper"${clipWrap ? ' style="overflow:hidden"' : ''}>
            <div class="sqs-image-shape-container-element"${clipWrap ? ' style="overflow:hidden"' : ''}>
              <img src="${src}" alt="Project ${id}" style="display:block;width:100%;aspect-ratio:4/3;object-fit:cover">
            </div></div></figure></div>
      </div></div></div>`;
const body = `
<section class="page-section" data-section-id="hero" style="min-height:640px">
  <div class="section-background" style="position:absolute;inset:0;overflow:hidden">
    <img src="${imgs[0]}" alt="" style="width:100%;height:100%;object-fit:cover;display:block">
  </div>
  <div class="content-wrapper"><div class="content"><div class="fluid-engine">
    <div class="fe-block" style="grid-area:1/1/2/24"><div class="sqs-block code-block"><div class="sqs-block-content">${marker}</div></div></div>
    <div class="fe-block" style="grid-area:2/1/3/16"><div class="sqs-block html-block"><div class="sqs-block-content"><div class="sqs-html-content"><h1>Spaces built to be lived in.</h1></div></div></div></div>
  </div></div></div>
</section>
<section class="page-section" data-section-id="spacer" style="height:900px"><div class="content-wrapper"><div class="content"><div class="fluid-engine"></div></div></div></section>
<section class="page-section" data-section-id="row">
  <div class="section-background"></div>
  <div class="content-wrapper"><div class="content"><div class="fluid-engine">
    ${imageBlock('a', imgs[1], true)}
    ${imageBlock('b', imgs[2], false)}
    <div class="fe-block" style="grid-area:2/1/3/4"><div class="sqs-block code-block"><div class="sqs-block-content">${marker}</div></div></div>
  </div></div></div>
</section>
<section class="page-section" data-section-id="unmarked"><div class="content-wrapper"><div class="content"><div class="fluid-engine">
  <div class="fe-block" style="grid-area:1/1/2/12"><div class="sqs-block image-block"><div class="sqs-block-content"><img id="plain" src="${imgs[1]}" alt="x" style="width:100%"></div></div></div>
</div></div></div></section>`;

const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--HEAD-->', '').replace('<!--BODY-->', body).replace('</body>', snippet + '\n</body>'));
const pageNoScript = path.join(here, '.test-page-plain.html');
fs.writeFileSync(pageNoScript, mock.replace('<!--HEAD-->', '').replace('<!--BODY-->', body));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="800" height="600"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }
const tf = (p, sel) => p.evaluate(s => getComputedStyle(document.querySelector(s)).transform, sel);
const scaleOf = m => { if (!m || m === 'none') return 1; const v = m.match(/matrix\(([^,]+)/); return v ? parseFloat(v[1]) : NaN; };
const boxes = p => p.evaluate(() => [...document.querySelectorAll('.fe-block, .sqs-block, .section-background')].map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10), Math.round(r.height * 10)].join('x'); }).join('|'));
const inlineDims = p => p.evaluate(() => [...document.querySelectorAll('*')].map((e, i) => [i, e.style.height, e.style.width, e.style.minHeight, e.style.maxHeight].join(',')).filter(s => !/^\d+,,,,$/.test(s)));

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;

  // baseline layout without the script
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  let p = await ctx.newPage();
  await p.goto('file://' + pageNoScript); await p.waitForTimeout(200);
  const base = await boxes(p);
  const baseInline = await inlineDims(p);
  await ctx.close();

  // 1. Effect applies; hero settles; row settles on scroll
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(40);
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-ss-on')), '<html> gets swtl-ss-on');
  const armed = await p.evaluate(() => document.querySelectorAll('.swtl-ss-img').length);
  assert(armed === 3, `3 images armed: hero bg + 2 row images (got ${armed})`);
  assert(await p.evaluate(() => !document.getElementById('plain').classList.contains('swtl-ss-img')), 'unmarked section untouched');
  const s0 = scaleOf(await tf(p, '#block-a img'));
  assert(Math.abs(s0 - 1.15) < 0.01, `row img starts at scale 1.15 (got ${s0})`);
  const f0 = await p.evaluate(() => getComputedStyle(document.querySelector('#block-a img')).filter);
  assert(/brightness/.test(f0), `row img starts dimmed (${f0})`);
  assert(await boxes(p) === base, 'block / background boxes identical to no-script layout (layout untouched)');
  const clipA = await p.evaluate(() => document.querySelector('#block-a .swtl-ss-clip') !== null);
  const clipB = await p.evaluate(() => document.querySelector('#block-b img').parentNode.classList.contains('swtl-ss-clip'));
  assert(!clipA && clipB, 'clip class only added where the image wrapper did not clip already');
  if (shots) await p.screenshot({ path: `${shots}/ss-0.png` });
  await p.waitForTimeout(600);
  const heroMid = scaleOf(await tf(p, '.section-background img'));
  assert(heroMid > 1 && heroMid < 1.1, `hero bg mid-settle (scale ${heroMid.toFixed(3)})`);
  await p.waitForTimeout(1200);
  assert(await tf(p, '.section-background img') === 'none', 'hero bg settles to transform: none');
  assert(scaleOf(await tf(p, '#block-a img')) > 1.14, 'row img still zoomed while off screen');
  await p.evaluate(() => document.querySelector('[data-section-id=row]').scrollIntoView());
  await p.waitForTimeout(500);
  const sa = scaleOf(await tf(p, '#block-a img')), sb = scaleOf(await tf(p, '#block-b img'));
  assert(sa < 1.15 && sb > sa, `row settles staggered (a ${sa.toFixed(3)} < b ${sb.toFixed(3)})`);
  if (shots) await p.screenshot({ path: `${shots}/ss-row.png` });
  await p.waitForTimeout(1600);
  const endA = await tf(p, '#block-a img'), endB = await tf(p, '#block-b img');
  assert(endA === 'none' && endB === 'none', `row images end at identity (${endA}, ${endB})`);
  assert(await p.evaluate(() => getComputedStyle(document.querySelector('#block-b img')).filter) === 'none', 'row images end at full color');
  assert(await boxes(p) === base, 'block boxes unchanged after settle');
  const dims = await inlineDims(p);
  assert(JSON.stringify(dims) === JSON.stringify(baseInline), 'no inline height/width written by the script');

  // 2. Edit mode → teardown, exit → re-init
  await p.evaluate(() => document.body.classList.add('sqs-edit-mode-active'));
  await p.waitForTimeout(50);
  const left = await p.evaluate(() => ({ on: document.documentElement.classList.contains('swtl-ss-on'), cls: document.querySelectorAll('[class*="swtl-ss-"]').length, htmlStyle: document.documentElement.getAttribute('style') }));
  assert(!left.on && left.cls === 0 && !left.htmlStyle, `edit mode: all classes + inline vars removed (${JSON.stringify(left)})`);
  assert(await tf(p, '#block-a img') === 'none', 'edit mode: images at natural size');
  await p.evaluate(() => document.body.classList.remove('sqs-edit-mode-active'));
  await p.waitForTimeout(50);
  assert(await p.evaluate(() => document.querySelectorAll('.swtl-ss-img').length) === 3, 'leaving edit mode re-inits');
  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));
  await ctx.close();

  // 3. Drift flag (off by default; on via config)
  ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.addInitScript(() => { window.SwtlScaleSettle = { drift: true }; });
  await p.goto(url); await p.waitForTimeout(100);
  await p.evaluate(() => window.scrollTo(0, 300)); await p.waitForTimeout(100);
  const ds = await p.evaluate(() => parseFloat(document.querySelector('.section-background img').style.scale));
  assert(ds > 1 && ds <= 1.04, `drift on: scroll-linked scale (${ds})`);
  await ctx.close();

  // 4. Inside a frame (the Squarespace editor) it never runs
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  const inner = p.frames()[1];
  assert(await inner.evaluate(() => !document.documentElement.classList.contains('swtl-ss-on') && !document.querySelector('.swtl-ss-img')), 'skipped inside editor frame');
  await ctx.close();

  // 5. Reduced motion: final state, no transform
  ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1280, height: 720 } });
  p = await ctx.newPage();
  await p.goto(url); await p.waitForTimeout(150);
  assert(await p.evaluate(() => !document.documentElement.classList.contains('swtl-ss-on')) && await tf(p, '#block-a img') === 'none', 'reduced motion: no zoom, images at rest');
  await ctx.close();

  fs.rmSync(assets, { recursive: true, force: true });
  for (const f of [pagePath, pageNoScript, frameHost]) fs.rmSync(f, { force: true });
}
