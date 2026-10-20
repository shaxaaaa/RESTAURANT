// Renders the film frame by frame.
// Usage: node render_film.js <platesDir> <outDir> [fps=25] [--times=t1,t2]  (or [from] [to] seconds)
const path = require('path'), fs = require('fs');
let pw; try { pw = require('playwright'); } catch { pw = require('/opt/node22/lib/node_modules/playwright'); }
(async () => {
  const [plates, out] = [path.resolve(process.argv[2]), process.argv[3]];
  const fps = +(process.argv[4] || 25);
  const timesArg = process.argv.find(a => a.startsWith('--times='));
  const from = +(process.argv[5] || 0), to = +(process.argv[6] || 180);
  fs.mkdirSync(out, { recursive: true });
  const narration = JSON.parse(fs.readFileSync(path.join(__dirname, 'narration.json'), 'utf8'));
  const browser = await pw.chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => { console.error('[page error]', e.message); process.exit(1); });
  await page.addInitScript(n => { window.NARRATION = n; }, narration);
  await page.goto('file://' + path.join(__dirname, 'film.html') + '?plates=' + encodeURIComponent('file://' + plates));
  await page.waitForFunction(() => window.ready === true || window.loadError, null, { timeout: 60000 });
  const err = await page.evaluate(() => window.loadError); if (err) { console.error(err); process.exit(1); }
  const jobs = timesArg ? timesArg.slice(8).split(',').map(t => [`test_${t}`, +t])
    : Array.from({ length: Math.round((to - from) * fps) }, (_, i) => { const n = Math.round(from * fps) + i; return [`f_${String(n).padStart(5, '0')}`, n / fps]; });
  const t0 = Date.now();
  for (const [name, t] of jobs) {
    const file = path.join(out, name + '.jpg');
    if (!timesArg && fs.existsSync(file)) continue;
    const url = await page.evaluate(tt => window.renderFrame(tt), t);
    fs.writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
    if (timesArg || name.endsWith('00')) console.log(name, t.toFixed(2), ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  await browser.close();
})();
