// node cap3.js <sec> <outDir> <workers> [frames: all | a,b,c | step:N]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [sec, out, nw, which] = [process.argv[2], process.argv[3], +(process.argv[4] || 4), process.argv[5] || 'all'];
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const mk = async () => { const p = await b.newPage({ viewport: { width: 1920, height: 1080 } }); p.on('pageerror', e => console.log('PAGEERR', e.message)); p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); }); await p.goto('http://127.0.0.1:8765/film3.html?sec=' + sec); return [p, await p.evaluate(() => window.READY)]; };
  const [p0, info] = await mk(); let frames = [];
  if (which === 'all') for (let f = info.f0; f < info.f1; f++) frames.push(f);
  else if (which.startsWith('step:')) for (let f = info.f0; f < info.f1; f += +which.slice(5)) frames.push(f);
  else frames = which.split(',').map(Number);
  frames = frames.filter(f => !fs.existsSync(path.join(out, String(f).padStart(5, '0') + '.jpg')) || which !== 'all');
  console.log('sec', sec, info, 'todo', frames.length);
  const pages = [p0]; for (let i = 1; i < Math.min(nw, frames.length); i++) pages.push((await mk())[0]);
  let idx = 0, done = 0; const t0 = Date.now();
  await Promise.all(pages.map(async p => { while (idx < frames.length) { const f = frames[idx++]; const d = await p.evaluate(f => window.renderAt(f), f); fs.writeFileSync(path.join(out, String(f).padStart(5, '0') + '.jpg'), Buffer.from(d.split(',')[1], 'base64')); if (++done % 50 === 0) console.log(done, ((Date.now() - t0) / 1000).toFixed(0) + 's'); } }));
  console.log('done', frames.length, 'frames', ((Date.now() - t0) / 1000).toFixed(1) + 's'); await b.close();
})();
