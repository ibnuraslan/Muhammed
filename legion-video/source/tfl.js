const { chromium } = require('playwright'); const fs = require('fs');
(async () => { const [sec, out, ...fr] = process.argv.slice(2); const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } }); p.on('pageerror', e => console.log('ERR', e.message)); await p.goto(`http://127.0.0.1:8765/film3.html?sec=${sec}&tl=tl6.json`); await p.evaluate(() => window.READY);
  for (const f of fr) { const d = await p.evaluate(f => window.renderAt(f), +f); fs.writeFileSync(`${out}/t${f}.jpg`, Buffer.from(d.split(',')[1], 'base64')); } await b.close(); })();
