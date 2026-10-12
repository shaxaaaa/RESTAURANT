// Renders scene.html frame by frame in headless Chromium (WebGL2 via SwiftShader).
// Usage: node render.js <outDir> [fps=30] [duration=15] [--times=t1,t2,...]
const path = require('path');
const fs = require('fs');
let playwright;
try { playwright = require('playwright'); } catch { playwright = require('/opt/node22/lib/node_modules/playwright'); }

(async () => {
  const outDir = process.argv[2] || 'frames';
  const fps = +(process.argv[3] || 30);
  const dur = +(process.argv[4] || 15);
  const timesArg = process.argv.find(a => a.startsWith('--times='));
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await playwright.chromium.launch({
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
           '--ignore-gpu-blocklist', '--disable-gpu-watchdog', '--disable-features=GpuWatchdog'],
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => { console.error('[page error]', e.message); process.exit(1); });
  await page.goto('file://' + path.resolve(__dirname, 'scene.html'));
  await page.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  if (process.env.NODOF) await page.evaluate(() => { window.NODOF = true; });

  const jobs = timesArg
    ? timesArg.slice(8).split(',').map((t, i) => [`test_${t}`, +t])
    : Array.from({ length: Math.round(fps * dur) }, (_, i) => [`f_${String(i).padStart(4, '0')}`, i / fps]);

  for (const [name, t] of jobs) {
    const file = path.join(outDir, name + '.jpg');
    if (!timesArg && fs.existsSync(file)) continue;
    const t0 = Date.now();
    const url = await page.evaluate(tt => window.renderFrame(tt), t);
    fs.writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
    console.log(`${name} t=${t.toFixed(3)} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  await browser.close();
})();
