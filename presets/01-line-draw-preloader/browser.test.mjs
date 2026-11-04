// Real-Chrome functional test for the line-draw preloader.
// Run: node ../../shared/harness/run.mjs "$(pwd)/.test-page.html" "$(pwd)/browser.test.mjs"
// (npm run test-01 from the repo root builds the page first.)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mock = fs.readFileSync(path.join(here, '../../shared/harness/mockpage.html'), 'utf8');
const snippet = fs.readFileSync(path.join(here, 'snippets/header-injection.html'), 'utf8');
const pagePath = path.join(here, '.test-page.html');
fs.writeFileSync(pagePath, mock.replace('<!--HEAD-->', snippet).replace('<!--BODY-->',
  '<section class="page-section"><div class="content-wrapper"><div class="fluid-engine"><div class="fe-block" style="grid-column:1/13"><div class="sqs-block"><div class="sqs-block-content"><h1>Spaces built to be lived in.</h1></div></div></div></div></div></section>'));
const frameHost = path.join(here, '.test-frame.html');
fs.writeFileSync(frameHost, `<iframe src="file://${pagePath}" width="800" height="600"></iframe>`);

function assert(ok, msg) { console.log((ok ? 'PASS  ' : 'FAIL  ') + msg); if (!ok) process.exitCode = 1; }

export default async function (browser) {
  const url = 'file://' + pagePath;
  const shots = process.env.SHOTS;

  // 1. Full sequence on a fresh session
  let ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  let p = await ctx.newPage();
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(url);
  await p.waitForTimeout(150);
  assert(await p.$('#swtl-ld-preloader') !== null, 'overlay mounts');
  assert(await p.evaluate(() => document.documentElement.classList.contains('swtl-ld-lock')), 'scroll locked while showing');
  const n = await p.evaluate(() => document.querySelectorAll('#swtl-ld-preloader svg [style*="animation"]').length);
  assert(n === 8, `all 8 shapes choreographed (got ${n})`);
  const lens = await p.evaluate(() => [...document.querySelectorAll('#swtl-ld-preloader svg [style*="animation"]')].map(e => parseFloat(e.style.strokeDasharray)));
  assert(lens.every(l => l > 1), 'every shape has a measured dash length');
  if (shots) for (const t of [600, 1300, 2600]) { await p.waitForTimeout(t === 600 ? 450 : 700 + (t === 2600 ? 600 : 0)); await p.screenshot({ path: `${shots}/ld-${t}.png` }); }
  await p.waitForTimeout(4200);
  assert(await p.$('#swtl-ld-preloader') === null, 'overlay removed from DOM after dismiss');
  assert(!(await p.evaluate(() => document.documentElement.classList.contains('swtl-ld-lock'))), 'scroll unlocked');
  assert(errors.length === 0, 'no page errors ' + errors.join(' | '));

  // 2. Once per session: second load renders instantly
  await p.reload();
  await p.waitForTimeout(100);
  assert(await p.$('#swtl-ld-preloader') === null, 'second page view skips preloader (once per session)');
  await ctx.close();

  // 3. Inside a frame (the Squarespace editor) it never runs
  ctx = await browser.newContext();
  p = await ctx.newPage();
  await p.goto('file://' + frameHost);
  await p.waitForTimeout(400);
  const inner = p.frames()[1];
  assert(await inner.$('#swtl-ld-preloader') === null, 'skipped inside editor frame');
  await ctx.close();

  // 4. Reduced motion: finished mark, fast exit
  ctx = await browser.newContext({ reducedMotion: 'reduce' });
  p = await ctx.newPage();
  await p.goto(url);
  await p.waitForTimeout(150);
  const animated = await p.evaluate(() => document.querySelectorAll('#swtl-ld-preloader svg [style*="animation"]').length);
  assert(animated === 0, 'reduced motion: no draw animation applied (static finished mark)');
  await p.waitForTimeout(1200);
  assert(await p.$('#swtl-ld-preloader') === null, 'reduced motion: dismissed within ~1s');
  await ctx.close();
}
