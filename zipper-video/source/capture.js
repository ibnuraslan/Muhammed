// usage: node capture.js outDir [frameList comma|all] [workers]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const out = process.argv[2], which = process.argv[3] || 'all', nw = +(process.argv[4] || 4);
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const url = 'file://' + path.resolve(__dirname, 'index.html');
  const mk = async () => { const p = await browser.newPage(); p.on('pageerror', e => console.error('PAGEERR', e.message)); p.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); }); await p.goto(url); return [p, await p.evaluate(() => window.READY)]; };
  const [p0, info] = await mk();
  let frames = which === 'all' ? [...Array(info.frames).keys()] : which.split(',').map(Number);
  console.log('frames', frames.length, 'dur', info.dur);
  const pages = [p0]; for (let i = 1; i < Math.min(nw, frames.length); i++) pages.push((await mk())[0]);
  let idx = 0, done = 0; const t0 = Date.now();
  await Promise.all(pages.map(async p => { while (idx < frames.length) { const f = frames[idx++]; const d = await p.evaluate(f => window.frameData(f), f); fs.writeFileSync(path.join(out, String(f).padStart(5, '0') + '.jpg'), Buffer.from(d.split(',')[1], 'base64')); if (++done % 100 === 0) console.log(done, ((Date.now() - t0) / 1000).toFixed(0) + 's'); } }));
  await browser.close(); console.log('done', ((Date.now() - t0) / 1000).toFixed(1) + 's');
})();
