const CU = TIMELINE.cues, cs = k => CU[k].start, ce = k => CU[k].end;
const DUR = TIMELINE.duration + 0.2, FPS = 30;
const TEX = {};
const SCENES = [];
const scene = (start, trans, draw) => SCENES.push({ start, trans, draw });
function cam(c, z = 1, cx = W / 2, cy = H / 2, dx = 0, dy = 0) { c.translate(W / 2 + dx, H / 2 + dy); c.scale(z, z); c.translate(-cx, -cy); }
function bg(c, tex, m = 90) { c.drawImage(tex, -m, -m, W + m * 2, H + m * 2); }
function spot(c, x, y, r, a = .55) { c.fillStyle = radial(c, x, y, r * .15, r, [[0, 'rgba(0,0,0,0)'], [1, `rgba(12,6,2,${a})`]]); c.fillRect(-300, -300, W + 600, H + 600); }
function title(c, s, x, y, p, o = {}) { if (p <= 0) return; txt(c, s, x, y - (1 - E.out(p)) * 30, { fam: 'Cinzel', size: o.size || 54, color: o.color || INK, alpha: clamp(p * 2.5), ls: o.ls ?? 3, align: o.align || 'center', shadow: o.shadow, stroke: o.stroke, strokeW: o.strokeW }); }
function leader(c, x0, y0, x1, y1, p, label, o = {}) {
  if (p <= 0) return; c.save(); c.strokeStyle = o.col || INK; c.lineWidth = 1.6; c.setLineDash([5, 4]);
  c.beginPath(); c.moveTo(x0, y0); c.lineTo(lerp(x0, x1, E.out(clamp(p * 1.5))), lerp(y0, y1, E.out(clamp(p * 1.5)))); c.stroke(); c.setLineDash([]);
  c.fillStyle = o.col || INK; c.beginPath(); c.arc(x0, y0, 4, 0, 7); c.fill();
  txt(c, label, x1 + (x1 > x0 ? 8 : -8), y1 + 7, { fam: 'Special Elite', size: o.size || 24, color: o.col || INK, align: x1 > x0 ? 'left' : 'right', typed: clamp(p * 1.5 - .4) });
  c.restore();
}

// ======== 1. Map: 1206, the Tigris ========
const RIVER = p => { p.moveTo(-60, 60); p.bezierCurveTo(220, 90, 260, 300, 470, 330); p.bezierCurveTo(680, 360, 640, 520, 860, 560); p.bezierCurveTo(1040, 590, 1100, 700, 1360, 760); };
scene(0, 'none', (c, t) => {
  cam(c, lerp(1.18, 1.05, E.inOut(P(t, 0, 9))), lerp(560, 690, E.inOut(P(t, 0, 9))), 360);
  bg(c, TEX.paper, 160);
  c.strokeStyle = 'rgba(58,42,30,.18)'; c.lineWidth = 1; for (let k = 0; k < 14; k++) { c.beginPath(); c.moveTo(-200 + k * 120, -200); c.lineTo(-200 + k * 120, H + 200); c.stroke(); c.beginPath(); c.moveTo(-200, -200 + k * 90); c.lineTo(W + 200, -200 + k * 90); c.stroke(); }
  // mountains
  c.strokeStyle = 'rgba(58,42,30,.6)'; c.lineWidth = 2; const r = rng(3);
  for (let k = 0; k < 16; k++) { const mx = 860 + r() * 420, my = 60 + r() * 220, ms = 24 + r() * 26; c.beginPath(); c.moveTo(mx - ms, my); c.lineTo(mx, my - ms * 1.1); c.lineTo(mx + ms, my); c.stroke(); c.beginPath(); c.moveTo(mx, my - ms * 1.1); c.lineTo(mx + ms * .3, my); c.stroke(); }
  // river
  const dp = E.inOut(P(t, .2, 3.6));
  c.lineCap = 'round'; c.setLineDash([1900 * dp, 4000]);
  c.strokeStyle = 'rgba(31,61,122,.35)'; c.lineWidth = 26; c.beginPath(); RIVER(c); c.stroke();
  c.strokeStyle = '#2b5a8a'; c.lineWidth = 9; c.beginPath(); RIVER(c); c.stroke(); c.setLineDash([]);
  if (dp > .5) { c.save(); c.translate(300, 230); c.rotate(.55); txt(c, 'TIGRIS', 0, 0, { fam: 'Cinzel', size: 26, color: '#2b5a8a', ls: 10, alpha: P(t, 2.2, .6) }); c.restore(); }
  // city
  const pc = P(t, cs('a1') + 2.6, .5);
  if (pc > 0) {
    c.save(); c.translate(560, 290); c.scale(E.back(pc) * 1.5, E.back(pc) * 1.5);
    c.fillStyle = '#d9c08a'; c.strokeStyle = INK; c.lineWidth = 2;
    c.fillRect(-60, -30, 120, 40); c.strokeRect(-60, -30, 120, 40);
    [[-30, 26], [24, 34]].forEach(([dx, rr2]) => { c.fillStyle = LAPIS; c.beginPath(); c.ellipse(dx, -30, rr2 * .7, rr2, 0, Math.PI, 0); c.fill(); c.stroke(); });
    c.fillStyle = '#d9c08a'; c.fillRect(56, -90, 14, 100); c.strokeRect(56, -90, 14, 100); c.fillStyle = LAPIS; c.beginPath(); c.moveTo(52, -90); c.lineTo(63, -112); c.lineTo(74, -90); c.fill();
    c.restore();
    txt(c, 'AMID', 560, 372, { fam: 'Cinzel', size: 38, color: INK, ls: 6, alpha: pc });
    txt(c, '(today Diyarbakır)', 560, 404, { fam: 'Special Elite', size: 24, color: '#5a4636', alpha: pc });
  }
  // compass
  c.save(); c.translate(1120, 560); c.rotate(Math.sin(t * .5) * .05); c.fillStyle = VERM;
  for (let k = 0; k < 8; k++) { c.save(); c.rotate(k * Math.PI / 4); c.fillStyle = k % 2 ? GOLD : VERM; c.beginPath(); c.moveTo(0, -(k % 2 ? 40 : 70)); c.lineTo(10, 0); c.lineTo(-10, 0); c.closePath(); c.fill(); c.strokeStyle = INK; c.lineWidth = 1; c.stroke(); c.restore(); }
  c.strokeStyle = INK; c.beginPath(); c.arc(0, 0, 50, 0, 7); c.stroke(); txt(c, 'N', 0, -78, { fam: 'Cinzel', size: 22 }); c.restore();
  // 1206
  const p6 = P(t, cs('a1') + .25, .45);
  if (p6 > 0) txt(c, '1206', 250, 560, { fam: 'Playfair Display', size: 150, color: VERM, scale: lerp(1.8, 1, E.back(p6)), alpha: clamp(p6 * 3), shadow: 'rgba(0,0,0,.25)' });
  strip(c, 'a book that would outlive empires', 840, 660, { rot: -.02, p: P(t, cs('a2') + .2, .4), size: 32 });
});

// ======== 2. Portrait in arch ========
scene(cs('b1') - .25, 'left', (c, t) => {
  const s0 = cs('b1') - .25, lt = t - s0;
  cam(c, lerp(1.0, 1.06, E.inOut(P(lt, 0, 10))), W / 2, H / 2);
  const g = geoTile(W + 200, H + 200, 90, '#13284a', 'rgba(201,162,77,.55)', '#1b3766', '#16305a'); c.drawImage(g.c, -100, -100, g.w, g.h);
  c.fillStyle = 'rgba(10,8,5,.35)'; c.fillRect(-100, -100, W + 200, H + 200);
  archFrame(c, 340, 370, 420, 640, (c, ix, iy, iw, ih) => {
    c.drawImage(TEX.paper, ix, iy, iw, ih);
    c.fillStyle = radial(c, ix + iw / 2, iy + ih * .4, 20, ih * .8, [[0, 'rgba(255,235,190,.3)'], [1, 'rgba(90,60,25,.45)']]); c.fillRect(ix, iy, iw, ih);
    for (let k = 0; k < 3; k++) gear(c, ix + 40 + k * 140, iy + ih - 30, 34 - k * 4, 10, t * (k % 2 ? -1 : 1) * .8, 'rgba(201,162,77,.5)', 'rgba(58,42,30,.5)');
    drawScholar(c, ix + iw / 2, iy + ih + 6, 1.42, { holding: 'book' });
  });
  const pn = P(t, cs('b1') + .9, 1.0);
  txt(c, 'ISMAIL AL-JAZARI', 880, 230, { fam: 'Cinzel', size: 54, color: '#f2e6c8', ls: 4, typed: pn, shadow: 'rgba(0,0,0,.7)' });
  const pa = P(t, cs('b1') + 1.6, .8);
  if (pa > 0) txt(c, 'الجزري', 880, 360, { fam: 'Amiri', size: 120, color: GOLD, alpha: pa, scale: lerp(1.15, 1, E.out(pa)), shadow: 'rgba(0,0,0,.6)' });
  txt(c, '1136 – 1206', 880, 450, { fam: 'Courier Prime', size: 26, color: '#d9c9a4', ls: 4, alpha: P(t, cs('b1') + 2.2, .5) });
  stamp(c, stampCanvas(['25 YEARS'], { size: 44, color: '#e0574a' }), 780, 540, P(t, cs('b2') + .35, .35), -.08, 1, true);
  strip(c, 'engineer to the Artuqid kings', 940, 620, { rot: .02, p: P(t, cs('b2') + 1.8, .4), size: 26 });
});

// ======== 3. The book ========
scene(cs('c1') - .2, 'up', (c, t) => {
  const s0 = cs('c1') - .2, lt = t - s0;
  cam(c, lerp(1.1, 1.0, E.out(P(lt, 0, 4))), W / 2, 380);
  bg(c, TEX.woodDark);
  // candle
  const fl = .85 + Math.sin(t * 17) * .08 + Math.sin(t * 29) * .05;
  c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = radial(c, 1150, 170, 0, 420, [[0, `rgba(255,190,90,${.35 * fl})`], [1, 'rgba(0,0,0,0)']]); c.fillRect(600, -200, 1000, 900); c.restore();
  c.fillStyle = '#efe4c8'; c.fillRect(1130, 180, 40, 150); c.strokeStyle = 'rgba(0,0,0,.3)'; c.strokeRect(1130, 180, 40, 150);
  c.fillStyle = radial(c, 1150, 160, 1, 26, [[0, '#fffbe0'], [.5, `rgba(255,190,80,${fl})`], [1, 'rgba(255,120,20,0)']]); c.beginPath(); c.ellipse(1150 + Math.sin(t * 9) * 2, 158, 10, 24, 0, 0, 7); c.fill();
  // book
  const bx = 600, by = 390, pw = 420, ph = 520;
  c.save(); c.shadowColor = 'rgba(0,0,0,.7)'; c.shadowBlur = 30 * S; c.shadowOffsetY = 14 * S; c.fillStyle = '#5a1a12'; c.fillRect(bx - pw - 16, by - ph / 2 - 12, pw * 2 + 32, ph + 24); c.restore();
  [[-1, 101], [1, 102]].forEach(([sd, seed]) => { const pp = paper(pw, ph, seed, { rough: 1.5, step: 6, burnW: 30, burnBlur: 14 }); c.drawImage(pp.c, sd < 0 ? bx - pw - pp.pad : bx - pp.pad, by - ph / 2 - pp.pad, pw + pp.pad * 2, ph + pp.pad * 2); });
  c.fillStyle = shade(c, bx - 30, 0, bx + 30, 0, [[0, 'rgba(0,0,0,0)'], [.5, 'rgba(60,30,10,.4)'], [1, 'rgba(0,0,0,0)']]); c.fillRect(bx - 30, by - ph / 2, 60, ph);
  // left page: titles
  const L = bx - pw / 2;
  txt(c, 'كتاب في معرفة الحيل الهندسية', L, by - 170, { fam: 'Amiri', size: 34, color: VERM, alpha: P(t, cs('c1') + .3, .6) });
  c.strokeStyle = GOLD; c.lineWidth = 2; c.beginPath(); c.moveTo(L - 150, by - 145); c.lineTo(L + 150, by - 145); c.stroke();
  const tp = P(t, cs('c1') + 2.0, 3.2);
  ['The Book of Knowledge', 'of Ingenious', 'Mechanical Devices'].forEach((s, k) => txt(c, s, L, by - 80 + k * 52, { fam: 'Playfair Display', size: k === 0 ? 34 : 38, color: INK, typed: clamp(tp * 3 - k) }));
  txt(c, '— 1206 —', L, by + 110, { fam: 'Special Elite', size: 22, color: '#5a4636', alpha: P(t, cs('c1') + 4.8, .5) });
  // right page: diagram draws in
  const R0 = bx + pw / 2, dp = P(t, cs('c1') + .5, 3);
  c.save(); c.beginPath(); c.rect(bx + 10, by - ph / 2, pw * dp, ph); c.clip();
  gear(c, R0 - 70, by - 60, 60, 14, t * .6, 'rgba(201,162,77,.85)'); gear(c, R0 + 64, by - 60, 46, 11, -t * .78 + .2, 'rgba(184,57,43,.75)'); gear(c, R0 + 10, by + 70, 40, 10, t * .9, 'rgba(31,61,122,.6)');
  c.strokeStyle = INK; c.lineWidth = 1; c.setLineDash([4, 4]); c.strokeRect(R0 - 170, by - 200, 340, 380); c.setLineDash([]);
  txt(c, 'Fig. I', R0, by + 210, { fam: 'Old Standard TT', size: 20, color: INK });
  c.restore();
  // page flips during c2
  const fp = P(t, cs('c2') + .2, 2.6), nf = 7;
  if (fp > 0 && fp < 1) { const k = fp * nf, f = k - Math.floor(k), ang = f * Math.PI, wv = Math.cos(ang) * pw; c.save(); c.fillStyle = '#e6d6b0'; c.strokeStyle = 'rgba(90,60,25,.5)'; c.beginPath(); c.moveTo(bx, by - ph / 2); c.quadraticCurveTo(bx + wv * .6, by - ph / 2 - 30 * Math.sin(ang), bx + wv, by - ph / 2); c.lineTo(bx + wv, by + ph / 2); c.quadraticCurveTo(bx + wv * .6, by + ph / 2 - 20 * Math.sin(ang), bx, by + ph / 2); c.closePath(); c.fill(); c.stroke(); c.restore(); }
  const cnt = Math.round(lerp(1, 50, E.inOut(P(t, cs('c2') + .1, 2.4))));
  if (P(t, cs('c2'), .2) > 0) { c.save(); c.fillStyle = 'rgba(20,12,6,.75)'; rr(c, 450, 640, 380, 66, 10); c.fill(); c.restore(); txt(c, `${cnt} MACHINES`, 640, 686, { fam: 'Cinzel', size: 40, color: '#f2e6c8', ls: 4 }); }
  strip(c, 'each one drawn & explained', 640, 60, { rot: -.015, p: P(t, cs('c2') + 2.6, .4), size: 28 });
});

// ======== 4. Elephant clock ========
scene(cs('d1') - .2, 'right', (c, t) => {
  const s0 = cs('d1') - .2, lt = t - s0, dur = ce('d3') - s0;
  cam(c, lerp(1.0, 1.05, E.inOut(P(lt, 0, dur))), lerp(640, 660, E.inOut(P(lt, 0, dur))), 370);
  bg(c, TEX.paper, 140);
  c.strokeStyle = GOLD; c.lineWidth = 5; c.strokeRect(24, 24, W - 48, H - 48); c.strokeStyle = VERM; c.lineWidth = 1.5; c.strokeRect(34, 34, W - 68, H - 68);
  const tb = cs('d2') + .9, tball = cs('d2') + 2.9, tdrum = cs('d3') + 1.5;
  const bird = clamp(P(t, tb, .3)) * (1 - P(t, tb + 2.4, .4));
  const ball = t < tball ? -1 : (t - tball) / .9;
  const ds = t - tdrum, strike = ds > 0 && ds < 2.4 ? Math.max(0, Math.sin((ds % .6) / .6 * Math.PI)) : 0, ring = ds > 0 && ds < 2.6 ? 1 - (ds % .6) / .6 : 0;
  elephantClock(c, 770, 670, 1.0, t, { bird, ball, drum: strike, ring });
  title(c, 'The Elephant Clock', 330, 160, P(t, cs('d1') + 1.2, .6), { size: 40 });
  c.strokeStyle = GOLD; c.lineWidth = 2; const lp = E.out(P(t, cs('d1') + 1.5, .5)); c.beginPath(); c.moveTo(330 - 150 * lp, 190); c.lineTo(330 + 150 * lp, 190); c.stroke();
  strip(c, 'every half hour...', 330, 290, { rot: -.03, p: P(t, cs('d2') + .1, .4), size: 32 });
  leader(c, 780, 152, 960, 110, P(t, tb, .7), 'a bird sings');
  leader(c, 610, 372, 430, 430, P(t, tball + .2, .7), 'a ball drops', {});
  leader(c, 1028, 450, 1080, 560, P(t, tdrum - .2, .7), 'the drum', {});
});

// ======== 5. Musical boat ========
scene(cs('e1') - .2, 'up', (c, t) => {
  const s0 = cs('e1') - .2, lt = t - s0, zoom = E.inOut(P(t, cs('e3') - .2, 1.2));
  cam(c, lerp(1.0, 1.04, zoom), 640, lerp(360, 380, zoom));
  c.fillStyle = shade(c, 0, -100, 0, 420, [[0, '#a8b4b0'], [.6, '#e6d6b0'], [1, '#f0dfb8']]); c.fillRect(-200, -200, W + 400, 700);
  c.fillStyle = 'rgba(255,240,200,.6)'; c.beginPath(); c.arc(980, 150, 60, 0, 7); c.fill();
  // distant palace
  c.fillStyle = 'rgba(120,100,80,.45)'; c.fillRect(-100, 320, W + 200, 60);
  [[180, 40], [320, 55], [1080, 46], [1200, 36]].forEach(([dx, r]) => { c.beginPath(); c.ellipse(dx, 320, r * .8, r, 0, Math.PI, 0); c.fill(); c.fillRect(dx - r * .8, 320, r * 1.6, 60); });
  [[250, 150], [1140, 130]].forEach(([dx, h]) => { c.fillRect(dx - 8, 380 - h, 16, h); c.beginPath(); c.moveTo(dx - 12, 380 - h); c.lineTo(dx, 380 - h - 26); c.lineTo(dx + 12, 380 - h); c.fill(); });
  water(c, 400, t);
  musicBoat(c, 500, 480, 1.18, t, 1);
  water(c, 560, t * 1.1, ['rgba(36,67,79,.55)']);
  c.save(); c.globalAlpha = 1 - P(t, cs('e3'), .3); title(c, 'The Musical Boat', 270, 110, P(t, cs('e1') + .8, .6), { size: 44 }); c.restore();
  pegDrum(c, 1040, 290, 190, t, P(t, cs('e2') - .1, .5));
  stamp(c, stampCanvas(['PROGRAMMABLE'], { size: 46 }), 330, 105, P(t, cs('e3') + .2, .35), -.06);
  strip(c, '...800 years ago', 350, 185, { rot: .03, p: P(t, cs('e3') + 1.7, .4), size: 32 });
});

// ======== 6. Peacock fountain ========
scene(cs('f1') - .2, 'left', (c, t) => {
  const s0 = cs('f1') - .2, lt = t - s0;
  cam(c, lerp(1.06, 1.0, E.out(P(lt, 0, 8))), W / 2, H / 2);
  const g = geoTile(W + 200, H + 200, 80, '#1d4744', 'rgba(201,162,77,.5)', '#245a55', '#1f4f4b'); c.drawImage(g.c, -100, -100, g.w, g.h);
  c.fillStyle = 'rgba(10,8,5,.35)'; c.fillRect(-100, -100, W + 200, H + 200);
  archFrame(c, 840, 360, 600, 700, (c, ix, iy, iw, ih) => {
    c.drawImage(TEX.paper, ix, iy, iw, ih);
    const tw = cs('f2') + .15, tsv = cs('f2') + 2.3, ttw = cs('f2') + 4.4;
    const sv = t < tsv ? 0 : (t - tsv) / 1.0;
    peacockFountain(c, ix + iw / 2, iy + ih - 10, .92, t, { water: P(t, tw, .4), servant: sv, towel: t > ttw });
  });
  title(c, 'The Peacock', 280, 250, P(t, cs('f1') + .5, .6), { size: 50, color: '#f2e6c8', shadow: 'rgba(0,0,0,.7)' });
  title(c, 'Fountain', 280, 310, P(t, cs('f1') + .8, .6), { size: 50, color: '#f2e6c8', shadow: 'rgba(0,0,0,.7)' });
  strip(c, 'for washing hands', 280, 400, { rot: -.03, p: P(t, cs('f1') + 1.5, .4), size: 30 });
  strip(c, 'soap...', 230, 520, { rot: .04, p: P(t, cs('f2') + 2.7, .35), size: 34 });
  strip(c, '...then a towel', 330, 600, { rot: -.03, p: P(t, cs('f2') + 4.6, .35), size: 34, color: '#8e1d17' });
});

// ======== 7. Pump: cranks and pistons ========
scene(cs('g1') - .2, 'up', (c, t) => {
  const s0 = cs('g1') - .2, lt = t - s0, split = E.inOut(P(t, cs('g2') - .2, .9));
  cam(c, lerp(1.08, 1.0, E.out(P(lt, 0, 3))), lerp(560, 640, split), 380);
  bg(c, TEX.paper, 140);
  c.strokeStyle = 'rgba(58,42,30,.12)'; c.lineWidth = 1; for (let x = -100; x < W + 100; x += 40) { c.beginPath(); c.moveTo(x, -100); c.lineTo(x, H + 100); c.stroke(); } for (let y = -100; y < H + 100; y += 40) { c.beginPath(); c.moveTo(-100, y); c.lineTo(W + 100, y); c.stroke(); }
  pumpMachine(c, 560, 420, 1.0, t);
  title(c, 'Water-Raising Machine', 560, 70, P(t, cs('g1') + .4, .6), { size: 42 });
  leader(c, 514, 480, 400, 600, P(t, cs('g1') + 2.6, .7), 'crank');
  leader(c, 754, 370, 790, 250, P(t, cs('g1') + 3.6, .7), 'pistons');
  if (split > 0) {
    c.save(); c.translate((1 - split) * 600, 0);
    const pp = paper(300, 470, 141, { tint: '#e8e8e0' }); drawPaper(c, pp, 1090, 380, .03, { shadow: 20 });
    engineSketch(c, 1090, 420, 1.0, t);
    txt(c, 'TODAY', 1090, 210, { fam: 'Cinzel', size: 34, color: '#2a2a2a', ls: 6 });
    c.restore();
  }
  strip(c, 'ideas that still move machines today', 640, 660, { rot: -.015, p: P(t, cs('g2') + .3, .4), size: 30 });
});

// ======== 8. Empires fell, libraries burned ========
scene(cs('h1') - .3, 'flash', (c, t) => {
  const s0 = cs('h1') - .3, lt = t - s0;
  cam(c, lerp(1.0, 1.1, E.inOut(P(lt, 0, 7))), W / 2, 380);
  c.fillStyle = '#0d0907'; c.fillRect(-200, -200, W + 400, H + 400);
  const burn = E.inOut(P(t, cs('h1') + 1.4, 3.2));
  const pages = [[300, 'elephant', -.1, 151], [640, 'peacock', .04, 152], [980, 'pump', .12, 153]];
  pages.forEach(([x, kind, rot, seed], i) => {
    const pg = manuscriptPage(300, 420, seed, kind);
    c.save(); c.translate(x, 400); c.rotate(rot);
    c.drawImage(pg.c, -150 - pg.pad, -210 - pg.pad, 300 + pg.pad * 2, 420 + pg.pad * 2);
    // burn from bottom
    const lvl = 210 - burn * (480 + i * 40) + 60;
    c.fillStyle = '#0d0907'; c.beginPath(); c.moveTo(-170, 240);
    for (let x2 = -170; x2 <= 170; x2 += 10) c.lineTo(x2, lvl + Math.sin(x2 * .09 + i) * 16 + Math.sin(x2 * .23 + t * 3) * 6);
    c.lineTo(170, 240); c.closePath(); c.fill();
    c.strokeStyle = `rgba(255,140,40,${burn > 0 && burn < 1 ? .9 : 0})`; c.lineWidth = 3; c.shadowColor = '#ff8a20'; c.shadowBlur = 14 * S; c.stroke(); c.shadowColor = 'transparent';
    c.restore();
  });
  flames(c, 40, 1260, 720, t, 260 * (burn > 0 ? 1 : 0), clamp(burn * 3) * (1 - P(t, cs('h2') + .5, 1.5) * .7));
  embers(c, t, 5, clamp(burn * 3));
  c.fillStyle = 'rgba(60,20,5,.25)'; c.fillRect(-200, -200, W + 400, H + 400);
  title(c, 'EMPIRES FELL.', 640, 110, P(t, cs('h1') + .1, .4), { size: 56, color: '#f2e6c8', shadow: 'rgba(0,0,0,.8)', ls: 6 });
  title(c, 'LIBRARIES BURNED.', 640, 175, P(t, cs('h1') + 1.3, .4), { size: 40, color: '#e0a060', shadow: 'rgba(0,0,0,.8)', ls: 6 });
  const fp = P(t, cs('h2') + .3, 2.4);
  if (fp > 0) {
    txt(c, 'Al-Jazari', 640, 420, { fam: 'Playfair Display', size: 110, color: `rgba(242,230,200,${1 - fp})`, shadow: 'rgba(0,0,0,.8)' });
    const r = rng(9); c.fillStyle = 'rgba(242,230,200,.8)'; for (let k = 0; k < 160; k++) { const x0 = 420 + r() * 440, y0 = 340 + r() * 100, d = fp * (60 + r() * 220); c.globalAlpha = clamp(fp * 2) * (1 - fp); c.beginPath(); c.arc(x0 + d, y0 - d * .5 * r(), 1.5, 0, 7); c.fill(); } c.globalAlpha = 1;
  }
  strip(c, 'almost forgotten', 640, 620, { rot: -.02, p: P(t, cs('h2') + 2.0, .4), size: 34 });
});

// ======== 9. Museum + rebuilt machine ========
scene(cs('i1') - .3, 'up', (c, t) => {
  const s0 = cs('i1') - .3, lt = t - s0, pan = E.inOut(P(t, cs('i2') - .1, 1.2));
  cam(c, lerp(1.0, 1.05, pan), lerp(520, 900, pan), 370);
  c.fillStyle = shade(c, 0, 0, 0, H, [[0, '#2a1416'], [.75, '#3d1e1f'], [1, '#1a0c0c']]); c.fillRect(-300, -200, W + 900, H + 400);
  c.fillStyle = '#2a1e16'; c.fillRect(-300, 600, W + 900, 300); c.fillStyle = '#4a3020'; c.fillRect(-300, 596, W + 900, 8);
  const frames = [[200, 'elephant'], [520, 'boat'], [840, 'peacock']];
  frames.forEach(([x, kind], i) => {
    c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = radial(c, x, 120, 10, 320, [[0, 'rgba(255,220,160,.28)'], [1, 'rgba(0,0,0,0)']]); c.beginPath(); c.moveTo(x - 40, -40); c.lineTo(x + 40, -40); c.lineTo(x + 200, 600); c.lineTo(x - 200, 600); c.fill(); c.restore();
    const pp = P(t, cs('i1') + .2 + i * .5, .5);
    c.save(); c.globalAlpha = clamp(pp * 2);
    c.shadowColor = 'rgba(0,0,0,.7)'; c.shadowBlur = 20 * S; c.shadowOffsetY = 10 * S; c.fillStyle = shade(c, 0, 140, 0, 480, [[0, '#e0b860'], [1, '#8a6a20']]); c.fillRect(x - 130, 130, 260, 340); c.shadowColor = 'transparent';
    c.fillStyle = '#1a0c0c'; c.fillRect(x - 112, 148, 224, 304);
    const pg = manuscriptPage(200, 280, 160 + i, kind); c.drawImage(pg.c, x - 100 - pg.pad, 160 - pg.pad, 200 + pg.pad * 2, 280 + pg.pad * 2);
    c.fillStyle = '#c9b68e'; c.fillRect(x - 60, 500, 120, 26); txt(c, ['c. 1206', 'c. 1206', 'c. 1206'][i], x, 519, { fam: 'Courier Prime', size: 14, color: INK });
    c.restore();
  });
  // rebuilt clock on pedestal
  const rx = 1260;
  c.save(); c.globalCompositeOperation = 'lighter'; c.fillStyle = radial(c, rx, 200, 10, 420, [[0, 'rgba(255,230,180,.35)'], [1, 'rgba(0,0,0,0)']]); c.fillRect(rx - 420, -100, 840, 800); c.restore();
  c.fillStyle = shade(c, rx - 150, 0, rx + 150, 0, [[0, '#2a2420'], [.5, '#4a403a'], [1, '#2a2420']]); c.fillRect(rx - 150, 540, 300, 120);
  elephantClock(c, rx - 20, 540, .78, t, { bird: P(t, cs('i2') + 2.0, .3) * (Math.sin(t * 3) > 0 ? 1 : .4), drum: Math.max(0, Math.sin(t * 5)) * P(t, cs('i2') + 2.0, .3), ring: 0 });
  c.strokeStyle = 'rgba(220,235,240,.35)'; c.lineWidth = 2; c.strokeRect(rx - 260, 90, 520, 450); c.fillStyle = 'rgba(200,220,230,.06)'; c.fillRect(rx - 260, 90, 520, 450);
  c.fillStyle = 'rgba(255,255,255,.12)'; c.beginPath(); c.moveTo(rx - 240, 110); c.lineTo(rx - 190, 110); c.lineTo(rx - 250, 400); c.lineTo(rx - 255, 300); c.fill();
  strip(c, 'in museums around the world', 520, 70, { rot: -.02, p: P(t, cs('i1') + 1.4, .4), size: 28 });
  stamp(c, stampCanvas(['STILL WORKS'], { size: 44, color: '#e0574a' }), rx - 20, 630, P(t, cs('i2') + 2.4, .35), -.06, 1, true);
});

// ======== 10. Title medallion ========
scene(cs('j1') - .3, 'flash', (c, t) => {
  const s0 = cs('j1') - .3, lt = t - s0;
  cam(c, lerp(1.12, 1.0, E.out(P(lt, 0, 3.5))), W / 2, H / 2);
  const g = geoTile(W + 300, H + 300, 100, '#10213f', 'rgba(201,162,77,.6)', '#16305a', '#132a50'); c.drawImage(g.c, -150, -150, g.w, g.h);
  spot(c, W / 2, H / 2, 820, .75);
  gear(c, 150, 130, 80, 16, t * .3, 'rgba(201,162,77,.8)'); gear(c, 268, 210, 50, 11, -t * .48, 'rgba(184,57,43,.8)');
  gear(c, 1130, 590, 80, 16, -t * .3, 'rgba(201,162,77,.8)'); gear(c, 1012, 510, 50, 11, t * .48 + .2, 'rgba(31,61,122,.9)');
  const pm = P(lt, .1, .6);
  c.save(); c.translate(W / 2, 330); c.scale(E.back(pm), E.back(pm)); c.globalAlpha = clamp(pm * 3);
  c.shadowColor = 'rgba(0,0,0,.7)'; c.shadowBlur = 30 * S; c.fillStyle = GOLD; c.beginPath();
  for (let k = 0; k < 16; k++) { const a = k / 16 * Math.PI * 2 + Math.PI / 16, r2 = k % 2 ? 230 : 262; c.lineTo(Math.cos(a) * r2, Math.sin(a) * r2); } c.closePath(); c.fill(); c.shadowColor = 'transparent';
  c.fillStyle = '#efe2c2'; c.beginPath(); c.arc(0, 0, 215, 0, 7); c.fill();
  c.save(); c.beginPath(); c.arc(0, 0, 215, 0, 7); c.clip(); c.drawImage(TEX.paper, -215, -215, 430, 430); c.restore();
  c.strokeStyle = LAPIS; c.lineWidth = 5; c.beginPath(); c.arc(0, 0, 200, 0, 7); c.stroke(); c.strokeStyle = VERM; c.lineWidth = 1.5; c.beginPath(); c.arc(0, 0, 190, 0, 7); c.stroke();
  txt(c, 'الجزري', 0, -10, { fam: 'Amiri', size: 128, color: LAPIS, alpha: P(lt, .5, .6) });
  txt(c, 'AL-JAZARI', 0, 80, { fam: 'Cinzel', size: 50, color: INK, ls: 8, alpha: P(lt, .8, .6) });
  txt(c, '1136 – 1206', 0, 128, { fam: 'Courier Prime', size: 24, color: VERM, ls: 4, alpha: P(lt, 1.1, .6) });
  c.restore();
  ribbon(c, 'THE FATHER OF ROBOTICS', W / 2, 640, 620, P(t, cs('j2') + .05, .5), { size: 36 });
});

// ======== compositor (same as previous episode) ========
let main, mctx, bufA, bufB;
function sceneAt(t) { let i = 0; for (let k = 0; k < SCENES.length; k++) if (t >= SCENES[k].start) i = k; return i; }
function renderScene(buf, i, t) {
  const c = buf.getContext('2d'); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = '#000'; c.fillRect(0, 0, buf.width, buf.height);
  c.setTransform(S, 0, 0, S, 0, 0); c.save(); SCENES[i].draw(c, t); c.restore();
}
const TR = .4;
function renderFrame(f) {
  const t = f / FPS, c = mctx, PW = W * S, PH = H * S;
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over';
  const i = sceneAt(t + TR / 2), sc = SCENES[i];
  const inTr = i > 0 && t > sc.start - TR / 2 && t < sc.start + TR / 2;
  if (!inTr) { renderScene(bufA, sceneAt(t), t); c.drawImage(bufA, 0, 0); }
  else {
    const p = E.inOut((t - (sc.start - TR / 2)) / TR);
    renderScene(bufA, i - 1, t); renderScene(bufB, i, t);
    if (sc.trans === 'flash') { c.drawImage(p < .5 ? bufA : bufB, 0, 0); c.fillStyle = `rgba(255,246,225,${1 - Math.abs(p * 2 - 1)})`; c.fillRect(0, 0, PW, PH); }
    else {
      const dir = { up: [0, -1], left: [-1, 0], right: [1, 0] }[sc.trans] || [0, -1];
      const dx = dir[0] * PW, dy = dir[1] * PH, smear = Math.sin(p * Math.PI), N = 7;
      c.fillStyle = '#000'; c.fillRect(0, 0, PW, PH);
      for (const [buf, o] of [[bufA, 0], [bufB, 1]]) for (let k = 0; k < N; k++) { const q = p + (k / (N - 1) - .5) * .22 * smear; c.globalAlpha = k === 0 ? 1 : 1 / (k + 1); c.drawImage(buf, dx * (q - o), dy * (q - o)); }
      c.globalAlpha = 1;
    }
  }
  post(c, f, t); return main;
}
function post(c, f, t) {
  const PW = W * S, PH = H * S;
  c.globalCompositeOperation = 'multiply'; c.fillStyle = '#f5e2c0'; c.fillRect(0, 0, PW, PH);
  c.globalCompositeOperation = 'source-over';
  c.fillStyle = radial(c, PW / 2, PH / 2, PH * .45, PW * .62, [[0, 'rgba(0,0,0,0)'], [1, 'rgba(15,8,2,.6)']]); c.fillRect(0, 0, PW, PH);
  const r = rng(f * 7 + 3);
  c.fillStyle = `rgba(0,0,0,${r() * .045})`; c.fillRect(0, 0, PW, PH);
  c.globalCompositeOperation = 'overlay'; c.globalAlpha = .2; c.drawImage(TEX.grain[f % TEX.grain.length], 0, 0, PW, PH); c.globalAlpha = 1;
  c.globalCompositeOperation = 'source-over';
  for (let i = 0; i < 5; i++) { if (r() < .5) continue; c.fillStyle = r() < .5 ? 'rgba(20,12,6,.55)' : 'rgba(255,245,225,.45)'; c.beginPath(); c.ellipse(r() * PW, r() * PH, 1 + r() * 4, 1 + r() * 3, r() * 3, 0, 7); c.fill(); }
  if (r() < .1) { c.strokeStyle = 'rgba(255,245,225,.16)'; c.lineWidth = 1.5; const x = r() * PW; c.beginPath(); c.moveTo(x, 0); c.lineTo(x + (r() - .5) * 20, PH); c.stroke(); }
  const fin = P(t, 0, .5), fout = 1 - P(t, DUR - .9, .9), a = 1 - Math.min(fin, fout);
  if (a > 0) { c.fillStyle = `rgba(0,0,0,${a})`; c.fillRect(0, 0, PW, PH); }
}
async function init() {
  const fams = [['Special Elite', 'SpecialElite'], ['Courier Prime', 'CourierPrime'], ['Old Standard TT', 'OldStandard'], ['Cinzel', 'Cinzel'], ['Black Ops One', 'BlackOps'], ['Playfair Display', 'Playfair700'], ['Amiri', 'AmiriArabic'], ['Amiri', 'AmiriLatin']];
  for (const [fam, file] of fams) { const ff = new FontFace(fam, `url(fonts/${file}.woff2)`); await ff.load(); document.fonts.add(ff); }
  TEX.paper = makePaperTex(7);
  TEX.woodDark = makeWood(8, .38, 220);
  TEX.grain = [0, 1, 2, 3, 4, 5].map(i => makeGrain(i + 100));
  main = document.getElementById('c'); main.width = W * S; main.height = H * S; mctx = main.getContext('2d');
  bufA = mkCanvas(W * S, H * S); bufB = mkCanvas(W * S, H * S);
  return { frames: Math.ceil(DUR * FPS), dur: DUR };
}
window.READY = init();
window.frameData = f => { renderFrame(f); return main.toDataURL('image/jpeg', .93); };
