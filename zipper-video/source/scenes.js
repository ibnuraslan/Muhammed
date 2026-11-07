const CU = TIMELINE.cues, cs = k => CU[k].start, ce = k => CU[k].end;
const DUR = TIMELINE.duration + 0.35, FPS = 30;
const TEX = {};
const SCENES = [];
const scene = (start, trans, draw) => SCENES.push({ start, trans, draw });
function cam(c, z = 1, cx = W / 2, cy = H / 2, dx = 0, dy = 0, rot = 0) { c.translate(W / 2 + dx, H / 2 + dy); c.rotate(rot); c.scale(z, z); c.translate(-cx, -cy); }
function shake(t, t0, amp = 14, dur = .45) { const p = (t - t0) / dur; if (p < 0 || p > 1) return [0, 0]; const k = amp * (1 - p) * (1 - p); return [Math.sin(t * 93) * k, Math.cos(t * 71) * k]; }
function bg(c, tex, m = 90) { c.drawImage(tex, -m, -m, W + m * 2, H + m * 2); }
function spot(c, x, y, r, a = .55) { c.fillStyle = radial(c, x, y, r * .15, r, [[0, 'rgba(0,0,0,0)'], [1, `rgba(12,6,2,${a})`]]); c.fillRect(-200, -200, W + 400, H + 400); }

// ======== A: 1851, writing the patent ========
scene(0, 'none', (c, t) => {
  cam(c, lerp(1.16, 1.0, E.out(P(t, 0, 5.2))), W / 2, H / 2 + 30);
  bg(c, TEX.wood);
  drawPaper(c, paper(300, 400, 11, { lines: true }), 90, 1130, -.14);
  leatherBoot(c, 280, 560, 1.2);
  pocketWatch(c, 100, 610, 58, t);
  spool(c, 610, 290, 1.1, '#7e1f19', .5); spool(c, 640, 700, .9, '#2c4a6e', -.3);
  button(c, 560, 470, 18); button(c, 605, 515, 13, '#2a2a2a'); button(c, 640, 455, 15, '#6a4a2a'); button(c, 80, 260, 16, '#3a2a1e');
  const cx = 380, cy = 870, rot = -.04;
  drawPaper(c, paper(420, 230, 21), cx, cy, rot);
  c.save(); c.translate(cx, cy); c.rotate(rot);
  txt(c, 'UNITED STATES PATENT OFFICE', 0, -78, { fam: 'Courier Prime', size: 17, color: '#5a4636', typed: P(t, .15, .7), ls: 1 });
  c.strokeStyle = 'rgba(90,70,50,.5)'; c.lineWidth = 1; c.beginPath(); c.moveTo(-170, -66); c.lineTo(170, -66); c.stroke();
  const tw = measure(c, '1851', 'Caveat', 130), wp = E.inOut(P(t, .55, 1.7));
  c.save(); c.beginPath(); c.rect(-tw / 2 - 10, -80, (tw + 20) * wp, 160); c.clip();
  txt(c, '1851', 0, 40, { fam: 'Caveat', size: 130, color: '#1f2a44' }); c.restore();
  txt(c, 'No. 8,540', 0, 88, { fam: 'Special Elite', size: 24, color: '#4a3a2c', typed: P(t, 2.4, .6) });
  // pen
  const away = E.in(P(t, 2.3, .8)), wig = Math.sin(t * 38) * 9 * (wp > 0 && wp < 1 ? 1 : 0);
  const px = -tw / 2 + tw * wp + away * 260, py = 20 + wig + away * 380;
  if (t < 3.2) penHand(c, px, py - 30 * (1 - P(t, .2, .35)), .05);
  c.restore();
  strip(c, 'an invention...', 210, 300, { rot: -.06, p: P(t, cs('a1') + 1.9, .35), size: 30 });
  strip(c, 'that nobody wanted.', 380, 1110, { rot: .03, p: P(t, cs('a2'), .35), size: 38, fam: 'Courier Prime', color: '#8e1d17' });
});

// ======== B: Elias Howe ========
scene(cs('b1') - .2, 'up', (c, t) => {
  const s0 = cs('b1') - .2, lt = t - s0;
  cam(c, lerp(1.0, 1.1, E.inOut(P(lt, 0, 5.2))), W / 2, 620);
  c.fillStyle = shade(c, 0, 0, 0, H, [[0, '#3a2a1c'], [.7, '#24180f'], [1, '#120c08']]); c.fillRect(-100, -100, W + 200, H + 200);
  c.strokeStyle = 'rgba(0,0,0,.35)'; c.lineWidth = 3; for (let x = -80; x < W + 100; x += 90) { c.beginPath(); c.moveTo(x, -100); c.lineTo(x, 980); c.stroke(); }
  c.fillStyle = radial(c, 560, 260, 10, 420, [[0, 'rgba(255,214,150,.35)'], [1, 'rgba(0,0,0,0)']]); c.fillRect(-100, -100, W + 200, H);
  // shelves with books
  const r = rng(5);
  [[300, -40, 280], [430, 470, 760]].forEach(([y, x0, x1]) => {
    c.fillStyle = '#1a110a'; c.fillRect(x0, y, x1 - x0, 10);
    for (let x = x0 + 6; x < x1 - 20;) { const bw = 10 + r() * 14, bh = 50 + r() * 40; c.fillStyle = ['#4a2a1a', '#2e3a2a', '#5a4630', '#3a2020', '#6a5636'][Math.floor(r() * 5)]; c.fillRect(x, y - bh, bw, bh); x += bw + 2; }
  });
  c.drawImage(TEX.woodDark, -100, 960, W + 200, 500);
  drawMan(c, 360, 1010, 1.72, { hair: 'wavy', mustache: true, chain: true });
  // table
  c.fillStyle = shade(c, 0, 790, 0, 860, [[0, '#1d4c4a'], [1, '#123433']]);
  c.beginPath(); c.moveTo(60, 800); c.lineTo(660, 800); c.lineTo(700, 860); c.lineTo(20, 860); c.closePath(); c.fill();
  c.fillStyle = shade(c, 0, 860, 0, 1000, [[0, '#5a2e1a'], [1, '#2e160c']]); c.fillRect(20, 860, 680, 130);
  c.strokeStyle = 'rgba(0,0,0,.5)'; c.lineWidth = 3; [[50, 880, 190, 90], [265, 880, 190, 90], [480, 880, 190, 90]].forEach(a => c.strokeRect(...a));
  c.fillStyle = '#c9a24d'; [145, 360, 575].forEach(x => { c.beginPath(); c.arc(x, 925, 6, 0, 7); c.fill(); });
  c.fillStyle = '#26130a'; c.fillRect(30, 990, 30, 200); c.fillRect(660, 990, 30, 200);
  sewingMachine(c, 300, 845, 1.25);
  c.fillStyle = shade(c, 0, 780, 0, 840, [[0, '#efe4cc'], [1, '#bfae8c']]); rr(c, 470, 790, 170, 46, 22); c.fill();
  c.fillStyle = '#d8c9a8'; c.beginPath(); c.ellipse(640, 813, 12, 23, 0, 0, 7); c.fill();
  strip(c, 'Elias', 255, 600, { rot: -.05, p: P(t, cs('b1') + .05, .3), size: 42, fam: 'Courier Prime' });
  strip(c, 'Howe', 450, 612, { rot: .04, p: P(t, cs('b1') + .3, .3), size: 42, fam: 'Courier Prime' });
  strip(c, '"Automatic, Continuous Clothing Closure"', 360, 175, { rot: -.02, p: P(t, cs('b1') + 1.3, .35), size: 21, typed: P(t, cs('b1') + 1.4, 1.1) });
  strip(c, '...then ignored it.', 360, 760, { rot: -.1, p: P(t, cs('b2') + .1, .35), size: 46, fam: 'Special Elite', from: 2.2 });
});

// ======== C: years roll ========
scene(cs('c1') - .15, 'left', (c, t) => {
  const s0 = cs('c1') - .15, lt = t - s0;
  cam(c, lerp(1.0, 1.14, E.out(P(lt, 0, 2))), W / 2, 640);
  bg(c, TEX.felt);
  spool(c, 590, 170, 1.3, '#5a4a2a', .9); button(c, 120, 230, 20, '#6a4a2a'); button(c, 170, 1080, 16); button(c, 610, 1000, 22, '#2a2a2a');
  const ph = photoCard({ hair: 'short', beard: 'chin' }, 200, 250, ''); drawPaper(c, ph, 590, 1140, .2, { shadow: 14 });
  const ppr = paper(340, 250, 41);
  drawPaper(c, ppr, 360, 640, .02);
  c.save(); c.translate(360, 640); c.rotate(.02);
  const v = 1851 + 42 * E.inOut(P(lt, .1, 1.15)), n = Math.floor(v), frac = v - n, speed = 42 * 1.6 / 1.15 * (1 - Math.abs(P(lt, .1, 1.15) * 2 - 1));
  c.save(); c.beginPath(); c.rect(-160, -100, 320, 150); c.clip();
  const blur = clamp(speed / 30);
  for (let k = -1; k <= 1; k++) txt(c, String(n + k), 0, 30 - (k - frac) * 90 * blur, { fam: 'Courier Prime', size: 104, color: '#2a1e16', alpha: k === 0 ? 1 - blur * .4 : blur * .4 });
  c.restore();
  stamp(c, stampCanvas(['42 YEARS LATER'], { size: 30 }), 0, 85, P(lt, .9, .35), -.05);
  c.restore();
});

// ======== D: Whitcomb Judson ========
scene(cs('d1') - .15, 'up', (c, t) => {
  const s0 = cs('d1') - .15, lt = t - s0;
  cam(c, lerp(1.06, 1.0, E.out(P(lt, 0, 4.6))), W / 2, 680);
  bg(c, TEX.wood);
  envelope(c, 120, 150, -.22);
  drawPaper(c, paper(590, 820, 31), 380, 700, .05);
  const sy = lerp(1600, 680, E.out(P(lt, 0, .5)));
  drawPaper(c, paper(570, 800, 32), 360, sy, -.02);
  c.save(); c.translate(360, sy); c.rotate(-.02);
  // patent sketch
  c.save(); c.translate(185, -255); c.rotate(.08); drawPaper(c, paper(170, 230, 33), 0, 0, 0, { shadow: 8 });
  c.strokeStyle = 'rgba(60,40,25,.75)'; c.lineWidth = 1.4;
  for (let i = 0; i < 8; i++) { c.beginPath(); c.arc(-14, -80 + i * 20, 8, -1.2, 1.9); c.stroke(); c.beginPath(); c.arc(14, -70 + i * 20, 8, 1.9, 5.1); c.stroke(); }
  c.beginPath(); c.moveTo(-40, -95); c.lineTo(-40, 90); c.moveTo(40, -95); c.lineTo(40, 90); c.stroke();
  txt(c, 'Fig. 1', 0, 104, { fam: 'Old Standard TT', size: 14, color: '#4a3424' }); c.restore();
  txt(c, 'Another inventor', -245, -250, { fam: 'Special Elite', size: 36, align: 'left', typed: P(t, cs('d1') + .05, .9) });
  txt(c, 'improved it.', -175, -200, { fam: 'Special Elite', size: 40, align: 'left', color: '#a3221c', typed: P(t, ce('d1') - .8, .5) });
  const p93 = P(t, cs('d1') + .35, .4);
  if (p93 > 0) txt(c, '1893', 105, 50, { fam: 'Playfair Display', size: 128, color: '#a3221c', scale: lerp(1.8, 1, E.back(p93)), alpha: clamp(p93 * 3) });
  const pph = P(t, cs('d1') + 1.0, .45);
  if (pph > 0) { const ph = photoCard({ hair: 'bald', beard: 'full', beardCol: '#2e221a' }, 240, 300, 'Whitcomb Judson'); drawPaper(c, ph, -130 + (1 - E.out(pph)) * -400, 80, lerp(-.5, -.08, E.out(pph)), { shadow: 16 }); }
  stamp(c, stampCanvas(['CLASP LOCKER'], { size: 46 }), 110, 255, P(t, cs('d2') + .55, .35), -.12);
  txt(c, 'PAT. No. 504,038 - AUG. 29, 1893', -40, 345, { fam: 'Courier Prime', size: 18, color: '#4a3a2c', typed: P(t, cs('d2') + .9, .7) });
  c.restore();
});

// ======== E: World's Fair ========
const CROWD = (() => { const r = rng(42); return Array.from({ length: 34 }, (_, i) => { const d = r(); return { x: r() * 900 - 90, y: 830 + d * 230, s: .45 + d * .75, kind: Math.floor(r() * 3), v: (r() - .5) * 40, seed: r() * 10 }; }).sort((a, b) => a.y - b.y); })();
scene(cs('e1') - .15, 'right', (c, t) => {
  const s0 = cs('e1') - .15, lt = t - s0;
  cam(c, lerp(1.0, 1.12, E.inOut(P(lt, 0, 4.9))), W / 2, 560);
  c.fillStyle = shade(c, 0, -100, 0, 860, [[0, '#8f9aa0'], [.5, '#d8cdb3'], [1, '#e9dcc0']]); c.fillRect(-100, -100, W + 200, 1000);
  const r = rng(9); c.fillStyle = 'rgba(255,250,240,.45)';
  for (let i = 0; i < 9; i++) { const x = (r() * 900 + lt * 12 * (1 + r())) % 1000 - 140, y = 80 + r() * 260; for (let k = 0; k < 5; k++) { c.beginPath(); c.ellipse(x + k * 34, y + Math.sin(k) * 10, 50, 26, 0, 0, 7); c.fill(); } }
  c.fillStyle = shade(c, 0, 820, 0, H, [[0, '#a99271'], [1, '#6e5a42']]); c.fillRect(-100, 820, W + 200, 600);
  c.strokeStyle = 'rgba(60,40,20,.18)'; c.lineWidth = 2; for (let i = -10; i <= 10; i++) { c.beginPath(); c.moveTo(360 + i * 20, 830); c.lineTo(360 + i * 140, 1400); c.stroke(); }
  fairGate(c, 360, 860, .95, t);
  c.fillStyle = 'rgba(232,220,195,.25)'; c.fillRect(-100, 600, W + 200, 300);
  CROWD.forEach(p => { if (p.y < 1000) crowdPerson(c, ((p.x + p.v * lt) % 960 + 960) % 960 - 120, p.y, p.s, p.kind, `rgba(${40 + (1 - p.s) * 70},${30 + (1 - p.s) * 60},${22 + (1 - p.s) * 45},1)`, t, p.seed); });
  drawMan(c, 360, 1250, 1.55, { hair: 'bald', beard: 'full', beardCol: '#2e221a', chain: true });
  CROWD.forEach(p => { if (p.y >= 1000) crowdPerson(c, ((p.x + p.v * lt) % 960 + 960) % 960 - 120, p.y + 180, p.s * 1.5, p.kind, '#2a1e15', t, p.seed); });
  strip(c, 'Chicago, 1893', 165, 470, { rot: -.06, p: P(t, cs('e1') + .5, .35), size: 28 });
  // headline
  const f1 = 'Alfa Slab One', w1 = measure(c, 'Still ', f1, 74), w2 = measure(c, 'nobody', f1, 74), x0 = W / 2 - (w1 + w2) / 2;
  const pS = P(t, cs('e2'), .3), pN = P(t, cs('e3'), .3), pC = P(t, cs('e3') + .3, .35);
  const o = { fam: f1, size: 74, color: '#1f2f4a', align: 'left', stroke: '#f2e8d2', strokeW: 10, shadow: 'rgba(0,0,0,.5)' };
  if (pS > 0) txt(c, 'Still', x0, 230 - (1 - E.back(pS)) * 40, { ...o, alpha: clamp(pS * 3) });
  if (pN > 0) txt(c, 'nobody', x0 + w1, 230 - (1 - E.back(pN)) * 40, { ...o, alpha: clamp(pN * 3) });
  if (pC > 0) txt(c, 'cared.', W / 2, 318, { ...o, align: 'center', size: 84, color: '#a3221c', scale: lerp(2, 1, E.back(pC)), alpha: clamp(pC * 3) });
});

// ======== F: 1913 blueprint ========
scene(cs('f1') - .15, 'up', (c, t) => {
  const s0 = cs('f1') - .15, lt = t - s0;
  cam(c, lerp(1.0, 1.08, E.inOut(P(lt, 0, 4))), W / 2, 680);
  c.fillStyle = radial(c, W / 2, 600, 100, 900, [[0, '#2a5590'], [1, '#132b52']]); c.fillRect(-100, -100, W + 200, H + 200);
  c.globalAlpha = .18; c.globalCompositeOperation = 'overlay'; c.drawImage(TEX.paper, -100, -100, W + 200, H + 200); c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1;
  c.strokeStyle = 'rgba(200,225,255,.12)'; c.lineWidth = 1;
  for (let x = -100; x < W + 100; x += 30) { c.beginPath(); c.moveTo(x, -100); c.lineTo(x, H + 100); c.stroke(); }
  for (let y = -100; y < H + 100; y += 30) { c.beginPath(); c.moveTo(-100, y); c.lineTo(W + 100, y); c.stroke(); }
  c.strokeStyle = 'rgba(230,240,255,.7)'; c.lineWidth = 2; c.strokeRect(30, 30, W - 60, H - 60);
  const p13 = P(t, cs('f1') + .05, .4);
  if (p13 > 0) txt(c, '1913', W / 2, 250, { fam: 'Playfair Display', size: 150, color: 'rgba(0,0,0,0)', noFill: true, stroke: '#eef5ff', strokeW: 3, scale: lerp(1.6, 1, E.back(p13)), alpha: clamp(p13 * 3) });
  const sl = lerp(1080, 380, E.inOut(P(t, cs('f1') + .3, ce('f1') - cs('f1') + .2)));
  c.save(); c.translate(-10, 0);
  zipper(c, 300, 340, 1080, sl, { style: 'blueprint', pitch: 26, tw: 40, th: 15, maxGap: 120, rate: .35 });
  c.restore();
  // dimension/leader lines
  c.strokeStyle = 'rgba(235,245,255,.8)'; c.lineWidth = 1.3; c.setLineDash([6, 5]);
  const pl = P(t, cs('f1') + .9, .5);
  if (pl > 0) { c.beginPath(); c.moveTo(330, 760); c.lineTo(lerp(330, 470, pl), lerp(760, 560, pl)); c.stroke(); }
  c.setLineDash([]);
  txt(c, 'G. SUNDBACK', 480, 555, { fam: 'Courier Prime', size: 30, color: '#eef5ff', align: 'left', typed: P(t, cs('f1') + 1.2, .6) });
  txt(c, 'HOOKLESS FASTENER No. 2', W / 2, 1180, { fam: 'Courier Prime', size: 26, color: '#eef5ff', typed: P(t, cs('f1') + .6, 1.2), ls: 2 });
  const pp = P(t, cs('f1') + .7, .45);
  if (pp > 0) { const ph = photoCard({ hair: 'short', mustache: true, glasses: true, hairCol: '#4a3a2a' }, 190, 240, 'Gideon Sundback'); drawPaper(c, ph, 555, 400 + (1 - E.out(pp)) * -500, .07, { shadow: 16 }); c.fillStyle = '#b8241c'; c.beginPath(); c.arc(555, 290 + (1 - E.out(pp)) * -500, 7, 0, 7); c.fill(); }
  strip(c, 'interlocking teeth', 505, 860, { rot: .04, p: P(t, ce('f1') - 1.3, .35), size: 30, fam: 'Special Elite' });
  if (P(t, ce('f1') - 1.1, .3) > 0) { c.strokeStyle = '#eef5ff'; c.lineWidth = 2; c.beginPath(); c.moveTo(390, 860); c.lineTo(lerp(390, 335, P(t, ce('f1') - 1.1, .3)), 900); c.stroke(); }
});

// ======== G: World War I ========
scene(cs('g1') - .12, 'left', (c, t) => {
  const s0 = cs('g1') - .12, lt = t - s0;
  const [sx, sy] = shake(t, cs('g1') + .1, 16), [hx, hy] = shake(t, cs('g1') + .75, 12);
  cam(c, lerp(1.05, 1.0, P(lt, 0, 3.8)), W / 2, H / 2, sx + hx, sy + hy);
  bg(c, TEX.woodDark);
  drawPaper(c, paper(560, 640, 51, { tint: '#d8cfa8' }), 340, 820, .08, { alpha: .9 });
  c.save(); c.translate(340, 820); c.rotate(.08); c.strokeStyle = 'rgba(90,70,40,.35)'; c.lineWidth = 1.2;
  for (let k = 0; k < 9; k++) { c.beginPath(); for (let a = 0; a < 6.3; a += .2) { const rr2 = 30 + k * 26 + Math.sin(a * 3 + k) * 10; c.lineTo(-60 + Math.cos(a) * rr2, 40 + Math.sin(a) * rr2 * .7); } c.closePath(); c.stroke(); }
  c.strokeStyle = 'rgba(140,30,20,.6)'; c.lineWidth = 3; c.setLineDash([10, 8]); c.beginPath(); c.moveTo(-250, -200); c.bezierCurveTo(-60, -120, 40, 120, 240, 220); c.stroke(); c.setLineDash([]); c.restore();
  const st = stampCanvas(['WORLD', 'WAR I'], { fam: 'Black Ops One', size: 132, color: '#e9dcc0', ls: 4, noBorder: true });
  const pw = P(t, cs('g1') + .02, .22);
  if (pw > 0) { c.save(); c.translate(W / 2, 330); const s = lerp(2.4, 1, E.out(pw)); c.scale(s, s); c.globalAlpha = clamp(pw * 3) * .92; c.drawImage(st.c, -st.w / 2, -st.h / 2, st.w, st.h); c.restore(); }
  const ph = P(t, cs('g1') + .55, .22);
  if (ph > 0) helmet(c, 330, 800, lerp(1.7, 1, E.out(ph)), -.12);
  dogTags(c, 560, 1050, .2);
  strip(c, 'The military needed', 330, 1035, { rot: -.04, p: P(t, cs('g2'), .3), size: 34 });
  const pf = P(t, cs('g2') + 1.0, .35);
  if (pf > 0) txt(c, 'FASTER GEAR', W / 2, 1150, { fam: 'Alfa Slab One', size: 82, color: '#e0aa3e', stroke: '#1a120c', strokeW: 12, scale: lerp(2, 1, E.back(pf)), alpha: clamp(pf * 3), shadow: 'rgba(0,0,0,.6)' });
});

// ======== H: jacket zips up ========
scene(cs('h1') - .15, 'up', (c, t) => {
  const s0 = cs('h1') - .15, lt = t - s0, dur = ce('h3') - s0;
  cam(c, lerp(1.08, 1.0, E.out(P(lt, 0, dur))), W / 2, H / 2);
  c.fillStyle = '#16110d'; c.fillRect(-100, -100, W + 200, H + 200);
  const knit = c.createPattern(TEX.cloth2, 'repeat'); c.fillStyle = knit; c.save(); c.globalAlpha = .5; c.fillRect(-100, -100, W + 200, H + 200); c.restore();
  const sl = lerp(1260, 140, E.inOut(P(lt, .1, dur - .1))), maxG = 300, rate = .55, cx = 360;
  const cloth = c.createPattern(TEX.cloth, 'repeat');
  [-1, 1].forEach(sd => {
    c.beginPath(); c.moveTo(sd < 0 ? -120 : W + 120, -120);
    for (let y = -120; y <= H + 120; y += 10) c.lineTo(cx + sd * (zipGap(y, sl, -1, maxG, rate) / 2 + 30), y);
    c.lineTo(sd < 0 ? -120 : W + 120, H + 120); c.closePath();
    c.save(); c.fillStyle = cloth; c.shadowColor = 'rgba(0,0,0,.8)'; c.shadowBlur = 30 * S; c.fill(); c.restore();
    c.save(); c.clip(); c.fillStyle = shade(c, cx - 300 * sd, 0, cx + 20 * sd, 0, [[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,.35)']]); c.fillRect(-120, -120, W + 240, H + 240); c.restore();
    c.strokeStyle = 'rgba(220,200,150,.35)'; c.lineWidth = 1.6; c.setLineDash([7, 6]); c.beginPath();
    for (let y = -120; y <= H + 120; y += 10) c.lineTo(cx + sd * (zipGap(y, sl, -1, maxG, rate) / 2 + 44), y);
    c.stroke(); c.setLineDash([]);
  });
  // pocket flap
  c.save(); c.translate(160 - zipGap(780, sl, -1, maxG, rate) * .3, 780); c.fillStyle = 'rgba(0,0,0,.25)'; rr(c, -90, -30, 180, 70, 8); c.fill();
  c.strokeStyle = 'rgba(220,200,150,.35)'; c.setLineDash([6, 5]); c.lineWidth = 1.5; rr(c, -84, -24, 168, 58, 6); c.stroke(); c.setLineDash([]); button(c, 0, 20, 12, '#3a3020'); c.restore();
  zipper(c, cx, -40, H + 40, sl, { dir: -1, maxGap: maxG, rate, pitch: 22, tw: 30, th: 12, tape: '#2a2a1c' });
  const fl = .85 + Math.sin(t * 17) * .08 + Math.sin(t * 31) * .05;
  lantern(c, 100, 170, 1, fl); lantern(c, 620, 190, 1, fl * .95);
  strip(c, 'Flight suits.', 220, 420, { rot: -.06, p: P(t, cs('h1'), .3), size: 40 });
  strip(c, 'Money belts.', 500, 600, { rot: .05, p: P(t, cs('h2'), .3), size: 40 });
  strip(c, 'Jackets that closed', 360, 990, { rot: -.03, p: P(t, cs('h3'), .3), size: 40 });
  strip(c, 'in a second.', 400, 1065, { rot: .03, p: P(t, cs('h3') + .9, .3), size: 44, fam: 'Courier Prime', color: '#8e1d17' });
});

// ======== I: Suddenly people noticed ========
scene(cs('i1') - .15, 'right', (c, t) => {
  const s0 = cs('i1') - .15, lt = t - s0, pan = E.inOut(P(t, cs('i2') - .1, .8));
  cam(c, lerp(1.0, 1.12, pan), lerp(W / 2, 500, pan), lerp(H / 2, 700, pan));
  bg(c, TEX.paper, 120);
  c.strokeStyle = 'rgba(120,80,40,.25)'; c.lineWidth = 3; [[150, 1080, 90], [610, 260, 70]].forEach(([x, y, r]) => { c.beginPath(); c.arc(x, y, r, 0, 7); c.stroke(); });
  c.strokeStyle = '#3a2a1e'; c.lineWidth = 2; c.beginPath(); c.moveTo(30, 95); c.lineTo(690, 95); c.moveTo(30, 103); c.lineTo(690, 103); c.stroke();
  [90, 360, 630].forEach(x => txt(c, '✦', x, 108, { size: 22, fam: 'DejaVu Sans', color: '#3a2a1e' }));
  const word = 'Suddenly', f = 'Abril Fatface', sz = 118, tw = measure(c, word, f, sz); let x = W / 2 - tw / 2;
  for (let i = 0; i < word.length; i++) { const cw = measure(c, word[i], f, sz), p = P(t, cs('i1') + i * .045, .3); if (p > 0) txt(c, word[i], x + cw / 2, 300, { fam: f, size: sz, color: '#b8392b', scale: lerp(0, 1, E.back(p)), alpha: clamp(p * 3) }); x += cw; }
  txt(c, 'people noticed', W / 2, 375, { fam: 'Special Elite', size: 54, color: '#2a1e16', typed: P(t, cs('i1') + .65, .6) });
  // bulb + hand sketch
  const dp = E.out(P(t, cs('i1') + .1, 1.6));
  c.save(); c.translate(330, 680); c.scale(1.25, 1.25); c.strokeStyle = '#c8641e'; c.lineWidth = 3.4; c.lineCap = 'round'; c.lineJoin = 'round';
  c.setLineDash([1400 * dp, 2000]);
  bulbStrokes().forEach(fn => { c.beginPath(); fn(c); c.stroke(); });
  c.beginPath(); handSketch(c); c.stroke(); c.setLineDash([]);
  if (dp > .9) { c.globalCompositeOperation = 'multiply'; c.fillStyle = radial(c, 0, -64, 5, 140, [[0, 'rgba(240,170,60,.35)'], [1, 'rgba(240,170,60,0)']]); c.beginPath(); c.arc(0, -64, 140, 0, 7); c.fill(); }
  c.restore();
  const pc = P(t, cs('i2') - .05, .5);
  if (pc > 0) {
    c.save(); c.translate(lerp(1000, 520, E.out(pc)), 720); c.rotate(lerp(.8, .3, E.out(pc)));
    drawPaper(c, paper(330, 420, 61), 0, 0, 0, { shadow: 22 });
    txt(c, 'but the moment that', 0, -70, { size: 30, typed: P(t, cs('i2') + .2, .7) });
    txt(c, 'changed', 0, -10, { size: 26, typed: P(t, cs('i2') + .9, .3) });
    const pe = P(t, cs('i2') + 1.15, .35);
    if (pe > 0) txt(c, 'everything', 0, 70, { fam: 'Abril Fatface', size: 58, color: '#b8392b', scale: lerp(1.6, 1, E.back(pe)), alpha: clamp(pe * 3) });
    c.restore();
  }
  spot(c, lerp(W / 2, 500, pan), 600, 900, .5);
});

// ======== J: B.F. Goodrich 1923 ========
function badge(c, x, y, p) {
  if (p <= 0) return; c.save(); c.translate(x, y - (1 - E.back(p)) * 120); c.globalAlpha = clamp(p * 3);
  c.shadowColor = 'rgba(0,0,0,.55)'; c.shadowBlur = 18 * S; c.shadowOffsetY = 8 * S;
  const pth = s => { c.beginPath(); c.moveTo(-230 * s, -40 * s); c.lineTo(-200 * s, -72 * s); c.lineTo(200 * s, -72 * s); c.lineTo(230 * s, -40 * s); c.lineTo(230 * s, 40 * s); c.lineTo(200 * s, 72 * s); c.lineTo(-200 * s, 72 * s); c.lineTo(-230 * s, 40 * s); c.closePath(); };
  pth(1); c.fillStyle = shade(c, 0, -72, 0, 72, [[0, '#4a5258'], [.5, '#2b3136'], [1, '#1a1e21']]); c.fill(); c.shadowColor = 'transparent';
  c.strokeStyle = '#e8dcc0'; c.lineWidth = 3; pth(.94); c.stroke(); c.lineWidth = 1.2; pth(.9); c.stroke();
  txt(c, 'B.F. Goodrich', 0, 6, { fam: 'Old Standard TT', size: 58, color: '#f2e8d2' });
  txt(c, 'rubber company', 0, 46, { fam: 'Old Standard TT', size: 26, color: '#d8cbb0', ls: 2 });
  c.restore();
}
scene(cs('j1') - .15, 'up', (c, t) => {
  const s0 = cs('j1') - .15, lt = t - s0;
  cam(c, lerp(1.08, 1.0, E.out(P(lt, 0, 5.8))), W / 2, 640);
  bg(c, TEX.wall);
  const p23 = P(t, cs('j1') + .45, .35), mv = E.inOut(P(t, cs('j2') + .1, .5));
  stamp(c, stampCanvas(['1923'], { fam: 'Alfa Slab One', size: 96, color: '#8a1c18', oval: true, ls: 4 }), W / 2, lerp(640, 610, mv), p23, -.04, lerp(1.7, .95, mv));
  strip(c, 'a rubber boot company called', W / 2, 190, { rot: -.02, p: P(t, cs('j2') + .1, .35), size: 30 });
  badge(c, W / 2, 330, P(t, cs('j2') + 1.65, .45));
  strip(c, 'put them on their boots', W / 2, 475, { rot: .02, p: P(t, cs('j3'), .35), size: 32 });
  const pb = P(t, cs('j3') - .1, .55), pb2 = P(t, cs('j3') + .05, .55);
  c.fillStyle = shade(c, 0, 1080, 0, 1300, [[0, '#5a4430'], [1, '#3a2a1c']]); c.fillRect(-100, 1080, W + 200, 400); c.fillStyle = 'rgba(0,0,0,.35)'; c.fillRect(-100, 1080, W + 200, 4);
  if (pb > 0) rubberBoot(c, 240, lerp(1700, 1175, E.back(pb)), 1.0, -1);
  if (pb2 > 0) rubberBoot(c, 480, lerp(1700, 1190, E.back(pb2)), 1.0, 1);
  spot(c, W / 2, 640, 1000, .4);
});

// ======== K/L: named after the sound — ZIP! ========
scene(cs('k1') - .15, 'left', (c, t) => {
  const s0 = cs('k1') - .15, lt = t - s0, [sx, sy] = shake(t, cs('l1') + .04, 22, .5);
  cam(c, lerp(1.0, 1.06, P(lt, 0, 3.5)), W / 2, 680, sx, sy);
  bg(c, TEX.wood);
  const clips = [
    [clipping(260, 330, 71, 'GOODRICH', 'ZIPPER BOOTS - 1923', x => rubberBoot(x, -10, 70, .3, 1)), 210, 560, -.07, 0],
    [clipping(250, 310, 72, 'The Zipper', 'a new kind of fastener', x => zipper(x, 0, -60, 60, 10, { pitch: 12, tw: 18, th: 7, maxGap: 40, rate: .5 })), 505, 520, .07, .12],
    [clipping(270, 320, 73, 'MODERN!', 'Hookless Fastener Co.', x => { drawMan(x, 0, 80, .42, { hair: 'short', mustache: true }); }), 380, 960, .03, .24],
  ];
  clips.forEach(([cl, x, y, r, d]) => { const p = P(t, s0 + .1 + d, .35); if (p > 0) drawPaper(c, cl, x, y - (1 - E.out(p)) * 60, r, { scale: lerp(1.3, 1, E.out(p)), alpha: clamp(p * 3), shadow: 16 }); });
  // string + pins
  const pins = [[210, 410], [505, 378], [380, 815]];
  c.strokeStyle = '#a3221c'; c.lineWidth = 2.2; c.beginPath(); c.moveTo(-40, 470); c.quadraticCurveTo(120, 470, 210, 410); c.quadraticCurveTo(360, 450, 505, 378); c.quadraticCurveTo(500, 650, 380, 815); c.quadraticCurveTo(560, 860, 780, 820); c.stroke();
  pins.forEach(([x, y]) => { c.fillStyle = radial(c, x - 3, y - 3, 1, 11, [[0, '#ff6a5a'], [1, '#7a120c']]); c.beginPath(); c.arc(x, y, 10, 0, 7); c.fill(); });
  txt(c, 'and named it after the', W / 2, 150, { size: 40, color: '#eadfc6', shadow: 'rgba(0,0,0,.8)', typed: P(t, cs('k1') + .05, .8) });
  txt(c, 'sound it made.', W / 2, 220, { fam: 'Courier Prime', size: 58, color: '#eadfc6', shadow: 'rgba(0,0,0,.8)', typed: P(t, cs('k1') + .9, .6) });
  const pz = P(t, cs('l1') - .06, .2);
  if (pz > 0) {
    c.save(); c.translate(W / 2, 700); c.rotate(-.08); const s = lerp(3, 1, E.out(pz)); c.scale(s, s); c.globalAlpha = clamp(pz * 3);
    c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 24 * S; c.shadowOffsetY = 10 * S;
    c.fillStyle = '#e9dcc0'; rr(c, -200, -95, 400, 190, 26); c.fill(); c.shadowColor = 'transparent';
    c.fillStyle = '#a3221c'; rr(c, -186, -81, 372, 162, 18); c.fill();
    c.strokeStyle = '#e9dcc0'; c.lineWidth = 3; c.setLineDash([8, 6]); rr(c, -172, -67, 344, 134, 12); c.stroke(); c.setLineDash([]);
    txt(c, 'ZIP!', 0, 48, { fam: 'Rye', size: 140, color: '#f4ead4', shadow: 'rgba(60,0,0,.6)', shadowBlur: 4 });
    c.restore();
  }
});

// ======== M: title ========
scene(cs('l2') - .3, 'flash', (c, t) => {
  const s0 = cs('l2') - .3, lt = t - s0;
  cam(c, lerp(1.1, 1.0, E.out(P(lt, 0, 2.5))), W / 2, 640);
  bg(c, TEX.woodDark);
  drawPaper(c, paper(620, 760, 81), W / 2, 640, -.015, { shadow: 30 });
  c.save(); c.translate(W / 2, 640); c.rotate(-.015);
  txt(c, 'THE', 0, -150, { size: 50, ls: 12, alpha: P(lt, .1, .3) });
  const pz = P(lt, .25, .4);
  txt(c, 'ZIPPER', 0, -40, { fam: 'Alfa Slab One', size: 128, color: '#2b1d14', scale: lerp(1.5, 1, E.back(pz)), alpha: clamp(pz * 3) });
  c.save(); c.rotate(-Math.PI / 2); c.translate(-45, 0);
  const sl = lerp(-280, 300, E.inOut(P(lt, .3, 1.1)));
  zipper(c, 0, -270, 270, sl, { dir: 1, maxGap: 60, rate: .4, pitch: 20, tw: 28, th: 11, tape: '#3a2c20' });
  c.restore();
  txt(c, '1851  -  1923', 0, 120, { fam: 'Courier Prime', size: 38, color: '#8e1d17', typed: P(lt, 1.1, .5), ls: 3 });
  txt(c, 'Named after a sound.', 0, 185, { size: 32, color: '#3a2c20', typed: P(lt, 1.5, .8) });
  c.restore();
  spot(c, W / 2, 640, 900, .6);
});

// ======== compositor ========
let main, mctx, bufA, bufB;
function sceneAt(t) { let i = 0; for (let k = 0; k < SCENES.length; k++) if (t >= SCENES[k].start) i = k; return i; }
function renderScene(buf, i, t) {
  const c = buf.getContext('2d'); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = '#000'; c.fillRect(0, 0, buf.width, buf.height);
  c.setTransform(S, 0, 0, S, 0, 0); c.save(); SCENES[i].draw(c, t); c.restore();
}
const TR = .34;
function renderFrame(f) {
  const t = f / FPS, c = mctx;
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over';
  let i = sceneAt(t + TR / 2), sc = SCENES[i];
  const inTr = i > 0 && t > sc.start - TR / 2 && t < sc.start + TR / 2;
  const PW = W * S, PH = H * S;
  if (!inTr) { renderScene(bufA, sceneAt(t), t); c.drawImage(bufA, 0, 0); }
  else {
    const p = E.inOut((t - (sc.start - TR / 2)) / TR);
    renderScene(bufA, i - 1, t); renderScene(bufB, i, t);
    if (sc.trans === 'flash') {
      c.drawImage(p < .5 ? bufA : bufB, 0, 0);
      c.fillStyle = `rgba(255,246,225,${1 - Math.abs(p * 2 - 1)})`; c.fillRect(0, 0, PW, PH);
    } else {
      const dir = { up: [0, -1], left: [-1, 0], right: [1, 0] }[sc.trans] || [0, -1];
      const dx = dir[0] * PW, dy = dir[1] * PH, smear = Math.sin(p * Math.PI);
      const N = 7;
      c.fillStyle = '#000'; c.fillRect(0, 0, PW, PH);
      for (const [buf, o] of [[bufA, 0], [bufB, 1]]) {
        for (let k = 0; k < N; k++) {
          const q = p + (k / (N - 1) - .5) * .22 * smear;
          c.globalAlpha = k === 0 ? 1 : 1 / (k + 1);
          c.drawImage(buf, dx * (q - o), dy * (q - o));
        }
      }
      c.globalAlpha = 1;
    }
  }
  post(c, f, t);
  return main;
}
function post(c, f, t) {
  const PW = W * S, PH = H * S;
  c.globalCompositeOperation = 'multiply'; c.fillStyle = '#f5e2c0'; c.fillRect(0, 0, PW, PH);
  c.globalCompositeOperation = 'source-over';
  c.fillStyle = radial(c, PW / 2, PH * .48, PW * .3, PH * .72, [[0, 'rgba(0,0,0,0)'], [1, 'rgba(15,8,2,.62)']]); c.fillRect(0, 0, PW, PH);
  const r = rng(f * 7 + 3);
  c.fillStyle = `rgba(0,0,0,${r() * .05})`; c.fillRect(0, 0, PW, PH);
  c.globalCompositeOperation = 'overlay'; c.globalAlpha = .22; c.drawImage(TEX.grain[f % TEX.grain.length], 0, 0, PW, PH); c.globalAlpha = 1;
  c.globalCompositeOperation = 'source-over';
  for (let i = 0; i < 5; i++) { if (r() < .5) continue; c.fillStyle = r() < .5 ? 'rgba(20,12,6,.55)' : 'rgba(255,245,225,.45)'; c.beginPath(); c.ellipse(r() * PW, r() * PH, 1 + r() * 4, 1 + r() * 3, r() * 3, 0, 7); c.fill(); }
  if (r() < .12) { c.strokeStyle = 'rgba(255,245,225,.18)'; c.lineWidth = 1.5; const x = r() * PW; c.beginPath(); c.moveTo(x, 0); c.lineTo(x + (r() - .5) * 20, PH); c.stroke(); }
  if (r() < .06) { c.strokeStyle = 'rgba(20,12,6,.5)'; c.lineWidth = 1.2; const x = r() * PW, y = r() * PH; c.beginPath(); c.moveTo(x, y); c.bezierCurveTo(x + 20, y + 10, x - 10, y + 30, x + 15, y + 50); c.stroke(); }
  const fin = P(t, 0, .35), fout = 1 - P(t, DUR - .6, .6);
  const a = 1 - Math.min(fin, fout); if (a > 0) { c.fillStyle = `rgba(0,0,0,${a})`; c.fillRect(0, 0, PW, PH); }
}
async function init() {
  const fams = [['Special Elite', 'SpecialElite'], ['Rye', 'Rye'], ['Abril Fatface', 'AbrilFatface'], ['Alfa Slab One', 'AlfaSlab'], ['Black Ops One', 'BlackOps'], ['Courier Prime', 'CourierPrime'], ['Caveat', 'Caveat'], ['Old Standard TT', 'OldStandard']];
  for (const [fam, file] of fams) { const ff = new FontFace(fam, `url(fonts/${file}.woff2)`); await ff.load(); document.fonts.add(ff); }
  const pf = new FontFace('Playfair Display', 'url(fonts/PlayfairBI.woff2)', { style: 'normal', weight: '400' }); await pf.load(); document.fonts.add(pf);
  TEX.paper = makePaperTex(7);
  TEX.wood = makeWood(3, 0);
  TEX.woodDark = makeWood(8, .38, 300);
  TEX.felt = makeFelt(4);
  TEX.cloth = makeCanvasCloth(12, [96, 96, 56]);
  TEX.cloth2 = makeCanvasCloth(13, [40, 34, 28]);
  TEX.grain = [0, 1, 2, 3, 4, 5].map(i => makeGrain(i + 100));
  // wall: paper + block seams
  const wl = mkCanvas(W * S, H * S), wx = wl.getContext('2d'); wx.drawImage(TEX.paper, 0, 0, W * S, H * S); wx.scale(S, S);
  const r = rng(91); wx.strokeStyle = 'rgba(110,80,45,.22)'; wx.lineWidth = 2;
  for (let y = 0; y < H; y += 120) for (let x = ((y / 120) % 2) * 90 - 90; x < W; x += 180) { wx.strokeRect(x + r() * 4, y + r() * 4, 180, 120); wx.fillStyle = `rgba(90,60,30,${r() * .07})`; wx.fillRect(x, y, 180, 120); }
  TEX.wall = wl;
  main = document.getElementById('c'); main.width = W * S; main.height = H * S; mctx = main.getContext('2d');
  bufA = mkCanvas(W * S, H * S); bufB = mkCanvas(W * S, H * S);
  return { frames: Math.ceil(DUR * FPS), dur: DUR };
}
window.READY = init();
window.frameData = f => { renderFrame(f); return main.toDataURL('image/jpeg', .93); };
