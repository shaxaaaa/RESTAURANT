// Renders the still "plates" (3D shader scenes) used by the film.
// Usage: node render_plates.js <outDir> [scale=1] [name1,name2,...]
const path = require('path'), fs = require('fs');
let pw; try { pw = require('playwright'); } catch { pw = require('/opt/node22/lib/node_modules/playwright'); }

const PLATES = {
  dunes_sunrise: { scene: 'dunes', cam: [0, 14, 0], tgt: [30, 4, 120], sun: [0.85, 0.06, 0.55], fov: 45, var: 0, exposure: 0.9 },
  dunes_golden:  { scene: 'dunes', cam: [60, 12, 20], tgt: [80, 3, 140], sun: [-0.75, 0.16, 0.7], fov: 45, var: 1, exposure: 0.85 },
  valley_dawn:   { scene: 'valley', cam: [45, 42, -120], tgt: [0, 2, -5], sun: [0.9, 0.09, 0.35], fov: 38, var: 0, exposure: 0.9 },
  valley_close:  { scene: 'valley', cam: [26, 11, -62], tgt: [0, 2, -8], sun: [0.9, 0.10, 0.35], fov: 40, var: 0, exposure: 0.9 },
  valley_night:  { scene: 'valley', cam: [38, 30, -100], tgt: [0, 2, -5], sun: [0.9, -0.03, 0.35], fov: 40, var: 1, exposure: 1.3 },
  alley:         { scene: 'alley', cam: [0.25, 1.6, -2.0], tgt: [-0.1, 1.9, 14], sun: [0.55, 0.8, 0.25], fov: 55, exposure: 0.8 },
  cave_wide:     { scene: 'cave', cam: [0.5, 2.6, -4], tgt: [4, 22, 38], sun: [1.0, 0.07, 0.3], fov: 50, exposure: 1.1 },
  cave_close:    { scene: 'cave', cam: [1.5, 27.5, 27], tgt: [4, 25.8, 38], sun: [1.0, 0.07, 0.3], fov: 45, exposure: 1.1 },
  still_whole:   { scene: 'still', cam: [0.08, 0.62, 0.98], tgt: [0, 0.04, 0.06], sun: [-0.8, 0.55, 0.25], fov: 40, split: 0, focus: 1.05, aper: 0.012, exposure: 1.0 },
  belt_whole:    { scene: 'still', cam: [0.18, 0.21, 0.66], tgt: [-0.05, 0.0, 0.31], sun: [-0.8, 0.55, 0.25], fov: 34, split: 0, focus: 0.42, aper: 0.006, exposure: 1.0 },
  belt_split:    { scene: 'still', cam: [0.18, 0.21, 0.66], tgt: [-0.05, 0.0, 0.31], sun: [-0.8, 0.55, 0.25], fov: 34, split: 1, focus: 0.42, aper: 0.006, exposure: 1.0 },
  still_split:   { scene: 'still', cam: [0.08, 0.62, 0.98], tgt: [0, 0.04, 0.06], sun: [-0.8, 0.55, 0.25], fov: 40, split: 1, focus: 1.05, aper: 0.012, exposure: 1.0 },
  desk_wide:     { scene: 'desk', cam: [0.05, 0.62, 0.78], tgt: [0, 0.0, -0.02], sun: [0, 1, 0], fov: 42, var: 0, focus: 0.98, aper: 0.012, exposure: 1.1 },
  desk_macro:    { scene: 'desk', cam: [0.10, 0.17, 0.30], tgt: [0.0, 0.012, 0.0], sun: [0, 1, 0], fov: 40, var: 0, focus: 0.33, aper: 0.004, exposure: 1.1 },
  desk_books:    { scene: 'desk', cam: [-0.55, 0.42, 0.45], tgt: [-0.15, 0.02, -0.15], sun: [0, 1, 0], fov: 42, var: 1, focus: 0.75, aper: 0.010, exposure: 0.9 },
  hall:          { scene: 'hall', cam: [0.0, 1.5, -2.0], tgt: [0.0, 1.2, 8], sun: [0.35, 0.85, 0.4], fov: 55, exposure: 0.9 },
  hall_halqa:    { scene: 'hall', cam: [2.4, 2.3, 2.2], tgt: [0.0, 0.2, 5.5], sun: [0.35, 0.85, 0.4], fov: 48, exposure: 0.9 },
  arches:        { scene: 'arches', cam: [-0.5, 1.7, -4], tgt: [0.6, 2.4, 10], sun: [0.9, 0.32, 0.25], fov: 55, exposure: 0.85 },
};

(async () => {
  const out = process.argv[2] || 'plates';
  const scale = +(process.argv[3] || 1);
  const only = process.argv[4] ? process.argv[4].split(',') : Object.keys(PLATES);
  fs.mkdirSync(out, { recursive: true });
  const browser = await pw.chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage();
  page.on('pageerror', e => { console.error('[page error]', e.message); process.exit(1); });
  page.on('console', m => console.log('[page]', m.text()));
  await page.goto('file://' + path.resolve(__dirname, 'plates.html'));
  await page.waitForFunction(() => window.ready === true);
  for (const name of only) {
    const P = { ...PLATES[name], w: Math.round(2304 * scale), h: Math.round(1296 * scale) };
    const t0 = Date.now();
    let url;
    try { url = await page.evaluate(p => window.renderPlate(p), P); }
    catch (e) { console.error(name, e.message); continue; }
    fs.writeFileSync(path.join(out, name + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
    console.log(`${name} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  await browser.close();
})();
