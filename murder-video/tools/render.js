#!/usr/bin/env node
// Step 2: renders every frame in headless Chromium and muxes with the soundtrack.
//   node tools/render.js crippen              -> build/crippen/crippen.mp4
//   node tools/render.js crippen --stills     -> one PNG per shot in build/crippen/stills (fast preview)
//   node tools/render.js crippen --from 30 --to 40   (seconds; partial render for testing)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const name = process.argv[2] || 'crippen';
const args = process.argv.slice(3);
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const BUILD = path.join(ROOT, 'build', name);
const timeline = JSON.parse(fs.readFileSync(path.join(BUILD, 'timeline.json')));

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.ttf': 'font/ttf', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(`http://localhost:${port}/engine/index.html`);
  const { frames } = await page.evaluate(tl => window.init(tl), timeline);
  const fps = timeline.fps;

  if (args.includes('--stills')) {
    const dir = path.join(BUILD, 'stills'); fs.mkdirSync(dir, { recursive: true });
    const at = opt('--at');
    const times = at ? at.split(',').map(Number) : timeline.shots.map(s => s.start + (s.end - s.start) * 0.6);
    for (const [i, t] of times.entries()) {
      const url = await page.evaluate(f => window.renderFrame(f, 0.85), Math.floor(t * fps));
      const file = path.join(dir, `shot${String(i).padStart(2, '0')}.jpg`);
      fs.writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
    }
    console.log('stills in', dir);
  } else {
    const from = Math.floor((Number(opt('--from')) || 0) * fps);
    const to = opt('--to') ? Math.floor(Number(opt('--to')) * fps) : frames;
    const partial = from > 0 || to < frames;
    const video = path.join(BUILD, partial ? `${name}_part.mp4` : `${name}.mp4`);
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-ss', String(from / fps), '-i', path.join(BUILD, 'audio.wav'),
      '-map', '0:v', '-map', '1:a', '-shortest',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
      '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', video], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let f = from; f < to; f++) {
      const url = await page.evaluate(i => window.renderFrame(i, 0.92), f);
      const buf = Buffer.from(url.split(',')[1], 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if ((f - from) % 150 === 0) console.log(`frame ${f}/${to}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('wrote', video);
  }
  await browser.close();
  server.close();
})();
