// Generic harness: node run.mjs <page.html> <testscript.mjs>
// Serves nothing — loads file:// directly in real Chrome.
import { chromium } from '/opt/npm-tools/node_modules/playwright/index.mjs';
const [,, page, test] = process.argv;
const mod = await import(test);
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
try { await mod.default(browser, 'file://' + page); console.log('HARNESS DONE'); }
catch (e) { console.error('HARNESS FAIL', e); process.exitCode = 1; }
finally { await browser.close(); }
