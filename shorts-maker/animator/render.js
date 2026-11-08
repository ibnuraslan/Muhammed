#!/usr/bin/env node
// Renders animated shots from an episode file into MP4 clips.
//   node animator/render.js <episode.js> <jobs.json>
// jobs.json: [{ "id": "03", "frames": 54, "out": "/tmp/shot03.mp4" }, ...]
//   add "still": 0.5 to a job to write a single JPEG of that moment instead.
const http = require('http'), fs = require('fs'), path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const argv = process.argv.slice(2);
const sizeArg = argv.indexOf('--size');
const [VW, VH] = sizeArg >= 0 ? argv.splice(sizeArg, 2)[1].split('x').map(Number) : [1080, 1920];
const [episode, jobsFile] = argv;
if (!episode || !jobsFile) { console.error('usage: node render.js <episode.js> <jobs.json>'); process.exit(2); }
const jobs = JSON.parse(fs.readFileSync(jobsFile, 'utf8'));
const TYPES = { '.js': 'text/javascript', '.html': 'text/html', '.ttf': 'font/ttf', '.json': 'application/json' };

const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = url === '/episode.js' ? path.resolve(episode)
           : url === '/' ? path.join(__dirname, 'page.html') : path.join(ROOT, url);
  if (url !== '/episode.js' && !file.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(data);
  });
});

function encoder(out) {
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-',
    '-vf', 'eq=saturation=1.22:contrast=1.06,vignette=PI/6', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((ok, bad) => ff.on('close', c => c === 0 ? ok() : bad(new Error('ffmpeg exited ' + c))));
  return { ff, done };
}
const write = (s, buf) => new Promise(ok => s.write(buf) ? ok() : s.once('drain', ok));

(async () => {
  await new Promise(ok => server.listen(0, '127.0.0.1', ok));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--use-angle=swiftshader'] });
  const page = await browser.newPage({ viewport: { width: VW, height: VH } });
  page.on('console', m => { if (m.type() === 'error') console.error('  [page]', m.text()); });
  page.on('pageerror', e => console.error('  [page]', e.message));
  await page.goto(`http://127.0.0.1:${port}/?w=${VW}&h=${VH}`);
  await page.waitForFunction('window.ready === true', null, { timeout: 60000 });
  let failed = 0;
  for (const job of jobs) {
    const t0 = Date.now();
    try {
      const ok = await page.evaluate(([id, n]) => window.setupShot(id, n), [job.id, job.frames]);
      if (!ok) { console.log(`  shot ${job.id}: not in episode, skipped`); continue; }
      if (job.still !== undefined) {
        const i = Math.round(job.still * (job.frames - 1));
        const url = await page.evaluate(i => window.renderFrame(i), i);
        fs.writeFileSync(job.out, Buffer.from(url.split(',')[1], 'base64'));
      } else {
        const { ff, done } = encoder(job.out);
        for (let i = 0; i < job.frames; i++) {
          const url = await page.evaluate(i => window.renderFrame(i), i);
          await write(ff.stdin, Buffer.from(url.split(',')[1], 'base64'));
        }
        ff.stdin.end(); await done;
      }
      console.log(`  animated shot ${job.id}: ${job.frames} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
    } catch (e) { failed++; console.error(`  shot ${job.id} failed: ${e.message}`); }
  }
  await browser.close(); server.close();
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
