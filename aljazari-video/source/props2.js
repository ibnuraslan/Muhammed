// ===== Islamic-manuscript style props for the Al-Jazari episode =====
const INK = '#3a2a1e', GOLD = '#c9a24d', LAPIS = '#1f3d7a', VERM = '#b8392b', TEAL = '#2f6a66', CREAM = '#efe6d2';

function outline(c, w = 2) { c.strokeStyle = INK; c.lineWidth = w; c.lineJoin = 'round'; c.stroke(); }

// 8-point star tessellation (cached canvas)
function geoTile(w, h, size, bgc, line, fill1, fill2) {
  const key = 'geo' + [w, h, size, bgc, line, fill1, fill2].join(); if (cache[key]) return cache[key];
  const cv = mkCanvas(w * S, h * S), c = cv.getContext('2d'); c.scale(S, S);
  c.fillStyle = bgc; c.fillRect(0, 0, w, h);
  const star = (x, y, r) => { c.beginPath(); for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2 + Math.PI / 8, rr2 = i % 2 ? r * .62 : r; c.lineTo(x + Math.cos(a) * rr2, y + Math.sin(a) * rr2); } c.closePath(); };
  for (let j = -1; j <= h / size + 1; j++) for (let i = -1; i <= w / size + 1; i++) {
    const x = i * size, y = j * size;
    star(x, y, size * .46); c.fillStyle = (i + j) % 2 ? fill1 : fill2; c.fill(); c.strokeStyle = line; c.lineWidth = 2; c.stroke();
    c.save(); c.translate(x + size / 2, y + size / 2); c.rotate(Math.PI / 4); c.beginPath(); c.rect(-size * .17, -size * .17, size * .34, size * .34); c.fillStyle = fill2; c.fill(); c.stroke(); c.restore();
    c.beginPath(); c.moveTo(x + size * .46, y); c.lineTo(x + size * .54, y); c.moveTo(x, y + size * .46); c.lineTo(x, y + size * .54); c.stroke();
  }
  const res = { c: cv, w, h }; cache[key] = res; return res;
}
function pointedArch(c, x, y, w, h) { // x,y top-left of bounding box; apex at top
  c.moveTo(x, y + h); c.lineTo(x, y + w * .55);
  c.bezierCurveTo(x, y + w * .12, x + w * .32, y + w * .04, x + w / 2, y);
  c.bezierCurveTo(x + w * .68, y + w * .04, x + w, y + w * .12, x + w, y + w * .55);
  c.lineTo(x + w, y + h); c.closePath();
}
function archFrame(c, cx, cy, w, h, inner) { // decorative frame with pointed arch window; inner(c) draws content clipped
  const x = cx - w / 2, y = cy - h / 2;
  c.save(); c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 24 * S; c.shadowOffsetY = 10 * S;
  c.fillStyle = shade(c, 0, y, 0, y + h, [[0, '#d9c08a'], [1, '#a8874e']]); c.fillRect(x, y, w, h); c.restore();
  c.strokeStyle = GOLD; c.lineWidth = 4; c.strokeRect(x + 8, y + 8, w - 16, h - 16); c.lineWidth = 1.5; c.strokeRect(x + 16, y + 16, w - 32, h - 32);
  const ix = x + 34, iy = y + 34, iw = w - 68, ih = h - 68;
  c.save(); c.beginPath(); pointedArch(c, ix, iy, iw, ih); c.clip(); inner(c, ix, iy, iw, ih); c.restore();
  c.beginPath(); pointedArch(c, ix, iy, iw, ih); c.strokeStyle = LAPIS; c.lineWidth = 6; c.stroke(); c.strokeStyle = GOLD; c.lineWidth = 2; c.stroke();
  // corner arabesques
  c.fillStyle = LAPIS; [[ix + 10, iy + 10], [ix + iw - 10, iy + 10]].forEach(([px, py]) => { c.beginPath(); c.arc(px, py, 7, 0, 7); c.fill(); });
}
function gear(c, x, y, r, teeth, ang, col = GOLD, line = INK) {
  c.save(); c.translate(x, y); c.rotate(ang); c.beginPath();
  for (let i = 0; i < teeth * 2; i++) { const a0 = i / (teeth * 2) * Math.PI * 2, a1 = (i + 1) / (teeth * 2) * Math.PI * 2, rr2 = i % 2 ? r : r * 1.16; c.arc(0, 0, rr2, a0, a1); }
  c.closePath(); c.fillStyle = col; c.fill(); c.strokeStyle = line; c.lineWidth = 1.6; c.stroke();
  c.beginPath(); c.arc(0, 0, r * .55, 0, 7); c.stroke(); c.beginPath(); c.arc(0, 0, r * .15, 0, 7); c.fillStyle = line; c.fill();
  for (let i = 0; i < 4; i++) { c.beginPath(); c.moveTo(Math.cos(i * 1.57) * r * .15, Math.sin(i * 1.57) * r * .15); c.lineTo(Math.cos(i * 1.57) * r * .55, Math.sin(i * 1.57) * r * .55); c.stroke(); }
  c.restore();
}
function turban(c, col = '#f2ead8') {
  c.fillStyle = shade(c, -34, -70, 34, -20, [[0, '#ffffff'], [.6, col], [1, '#b9ad94']]);
  c.beginPath(); c.ellipse(0, -30, 34, 25, 0, Math.PI * .9, Math.PI * 2.1); c.bezierCurveTo(30, -14, -30, -14, -33, -22); c.fill();
  c.beginPath(); c.ellipse(0, -40, 31, 24, 0, 0, 7); c.fill();
  c.strokeStyle = 'rgba(120,100,70,.55)'; c.lineWidth = 1.6;
  for (let i = 0; i < 4; i++) { c.beginPath(); c.ellipse(0, -46 + i * 7, 30 - i * 2, 12, -.25 + i * .05, Math.PI * 1.05, Math.PI * 1.95); c.stroke(); }
  c.fillStyle = VERM; c.beginPath(); c.ellipse(0, -60, 12, 8, 0, Math.PI, 0); c.fill();
}
function drawScholar(c, x, y, s, o = {}) {
  c.save(); c.translate(x, y); c.scale(s, s);
  softShadow(c, 0, 0, 80, 12, .5);
  const robe = o.robe || '#24476b', robeD = '#14283e';
  // outer robe
  c.fillStyle = shade(c, -80, 0, 80, 0, [[0, robeD], [.3, robe], [.7, robe], [1, robeD]]);
  c.beginPath(); c.moveTo(-40, -300); c.quadraticCurveTo(-62, -290, -66, -260); c.lineTo(-84, 0); c.lineTo(84, 0); c.lineTo(66, -260); c.quadraticCurveTo(62, -290, 40, -300); c.closePath(); c.fill();
  // inner robe
  c.fillStyle = shade(c, -20, 0, 20, 0, [[0, '#c8b48a'], [.5, '#e8dcc0'], [1, '#c8b48a']]);
  c.beginPath(); c.moveTo(-14, -300); c.lineTo(14, -300); c.lineTo(26, 0); c.lineTo(-26, 0); c.closePath(); c.fill();
  c.strokeStyle = GOLD; c.lineWidth = 4; [-1, 1].forEach(sd => { c.beginPath(); c.moveTo(sd * 16, -300); c.lineTo(sd * 28, 0); c.stroke(); });
  c.lineWidth = 5; c.beginPath(); c.moveTo(-84, -6); c.lineTo(84, -6); c.stroke();
  // sash
  c.fillStyle = VERM; c.fillRect(-56, -196, 112, 16); c.fillStyle = GOLD; c.fillRect(-56, -188, 112, 2);
  // sleeves + hands
  c.fillStyle = shade(c, -90, 0, 90, 0, [[0, robeD], [.5, robe], [1, robeD]]);
  [-1, 1].forEach(sd => { c.beginPath(); c.moveTo(sd * 50, -292); c.quadraticCurveTo(sd * 84, -270, sd * 80, -200); c.lineTo(sd * 70, -150); c.lineTo(sd * 30, -160); c.lineTo(sd * 46, -230); c.closePath(); c.fill(); });
  c.fillStyle = SKIN; [-1, 1].forEach(sd => { c.beginPath(); c.ellipse(sd * 30, -160, 13, 11, 0, 0, 7); c.fill(); });
  if (o.holding === 'book') { c.fillStyle = '#7a2a1e'; c.save(); c.translate(0, -172); c.rotate(-.08); rr(c, -38, -26, 76, 44, 3); c.fill(); c.fillStyle = GOLD; c.fillRect(-30, -18, 60, 2); c.fillRect(-30, 8, 60, 2); c.beginPath(); c.arc(0, -4, 7, 0, 7); c.fill(); c.restore(); }
  c.fillStyle = SKIN_D; c.fillRect(-9, -318, 18, 18);
  c.save(); c.translate(0, -346); drawHead(c, { hair: 'bald', beard: 'full', beardCol: o.beardCol || '#4a3a2c', hairCol: '#3a2c20' }); turban(c); c.restore();
  c.restore();
}
function seatedFigure(c, x, y, s, o = {}) { // small musician/driver, torso up, origin at seat
  c.save(); c.translate(x, y); c.scale(s, s);
  c.fillStyle = o.robe || '#7a2a1e'; c.beginPath(); c.moveTo(-24, 0); c.lineTo(-18, -50); c.quadraticCurveTo(0, -60, 18, -50); c.lineTo(24, 0); c.closePath(); c.fill(); outline(c, 1.4);
  c.fillStyle = SKIN; c.beginPath(); c.arc(0, -66, 12, 0, 7); c.fill(); outline(c, 1.2);
  c.fillStyle = '#f2ead8'; c.beginPath(); c.ellipse(0, -76, 13, 8, 0, 0, 7); c.fill(); outline(c, 1);
  c.fillStyle = INK; c.beginPath(); c.arc(4, -66, 1.6, 0, 7); c.fill();
  // arm
  const a = o.arm ?? 0; c.strokeStyle = o.robe || '#7a2a1e'; c.lineWidth = 7; c.lineCap = 'round';
  c.beginPath(); c.moveTo(10, -44); const ex = 10 + Math.cos(-.4 - a) * 26, ey = -44 + Math.sin(-.4 - a) * 26; c.lineTo(ex, ey); c.stroke();
  if (o.stick) { c.strokeStyle = INK; c.lineWidth = 2.5; c.beginPath(); c.moveTo(ex, ey); c.lineTo(ex + Math.cos(-.9 - a * 1.4) * 26, ey + Math.sin(-.9 - a * 1.4) * 26 + 26); c.stroke(); }
  c.restore(); return [x + ex * s, y + ey * s];
}

// ===== Elephant clock =====
function elephantClock(c, x, y, s, t, o = {}) {
  c.save(); c.translate(x, y); c.scale(s, s);
  softShadow(c, 20, 0, 240, 22, .45);
  const grey = shade(c, -180, -260, 180, 0, [[0, '#a7b2bd'], [.6, '#7d8a99'], [1, '#56616e']]);
  // far legs
  c.fillStyle = '#5c6774'; [[-110, 0], [100, 0]].forEach(([lx]) => { c.beginPath(); c.rect(lx + 18, -110, 46, 106); c.fill(); outline(c); });
  // tail
  c.strokeStyle = '#56616e'; c.lineWidth = 6; c.beginPath(); c.moveTo(-178, -150); c.quadraticCurveTo(-200, -100, -190, -60); c.stroke();
  // body
  c.fillStyle = grey; c.beginPath(); c.ellipse(-10, -160, 178, 100, 0, 0, 7); c.fill(); outline(c);
  // near legs
  c.fillStyle = grey; [[-140, 0], [70, 0]].forEach(([lx]) => { c.beginPath(); c.moveTo(lx, -120); c.lineTo(lx + 56, -120); c.lineTo(lx + 54, -4); c.lineTo(lx + 2, -4); c.closePath(); c.fill(); outline(c); c.fillStyle = '#e8e0cc'; for (let k = 0; k < 3; k++) { c.beginPath(); c.arc(lx + 12 + k * 15, -6, 5, Math.PI, 0); c.fill(); } c.fillStyle = grey; });
  // head + trunk + ear
  c.beginPath(); c.arc(180, -180, 72, 0, 7); c.fill(); outline(c);
  c.lineCap = 'round'; c.strokeStyle = INK; c.lineWidth = 42; c.beginPath(); c.moveTo(225, -150); c.bezierCurveTo(262, -100, 262, -40, 240, -10); c.quadraticCurveTo(228, 6, 214, -6); c.stroke();
  c.strokeStyle = '#7d8a99'; c.lineWidth = 38; c.stroke();
  c.strokeStyle = 'rgba(58,42,30,.4)'; c.lineWidth = 1.5; for (let k = 0; k < 6; k++) { c.beginPath(); c.arc(248, -120 + k * 18, 14, .2, 2.6); c.stroke(); }
  c.fillStyle = '#f4efe0'; c.beginPath(); c.moveTo(220, -132); c.quadraticCurveTo(268, -110, 286, -138); c.quadraticCurveTo(262, -118, 226, -124); c.closePath(); c.fill(); outline(c, 1.5);
  c.fillStyle = '#6d7988'; c.beginPath(); c.ellipse(140, -178, 46, 62, -.15, 0, 7); c.fill(); outline(c);
  c.fillStyle = INK; c.beginPath(); c.arc(206, -196, 5, 0, 7); c.fill();
  // saddle cloth
  c.fillStyle = VERM; c.beginPath(); c.moveTo(-130, -236); c.lineTo(100, -236); c.lineTo(110, -120); c.lineTo(-140, -120); c.closePath(); c.fill(); outline(c);
  c.strokeStyle = GOLD; c.lineWidth = 4; c.beginPath(); c.moveTo(-134, -132); c.lineTo(106, -132); c.stroke();
  c.fillStyle = GOLD; for (let k = 0; k < 9; k++) { c.beginPath(); c.arc(-118 + k * 27, -190, 5, 0, 7); c.fill(); }
  for (let k = 0; k < 12; k++) { c.beginPath(); c.moveTo(-138 + k * 21, -120); c.lineTo(-128 + k * 21, -104); c.lineTo(-118 + k * 21, -120); c.fill(); }
  // tower
  c.fillStyle = shade(c, -100, 0, 80, 0, [[0, '#d6c49c'], [.5, '#f1e6c8'], [1, '#c9b68e']]);
  c.fillRect(-100, -430, 170, 194); c.strokeStyle = INK; c.lineWidth = 2; c.strokeRect(-100, -430, 170, 194);
  c.fillStyle = LAPIS; for (let k = 0; k < 3; k++) { c.beginPath(); pointedArch(c, -86 + k * 52, -400, 38, 64); c.fill(); }
  c.fillStyle = GOLD; c.fillRect(-104, -300, 178, 10); c.fillRect(-104, -440, 178, 12);
  // clock dial (half-hour disk)
  c.fillStyle = CREAM; c.beginPath(); c.arc(-15, -268, 22, 0, 7); c.fill(); outline(c, 1.5);
  c.strokeStyle = INK; c.lineWidth = 2; c.beginPath(); c.moveTo(-15, -268); c.lineTo(-15 + Math.cos(t * .8) * 16, -268 + Math.sin(t * .8) * 16); c.stroke();
  // dome + bird
  c.fillStyle = shade(c, -80, -520, 50, -430, [[0, '#4f74b8'], [1, '#1a356b']]); c.beginPath(); c.ellipse(-15, -430, 76, 82, 0, Math.PI, 0); c.fill(); outline(c);
  c.strokeStyle = GOLD; c.lineWidth = 2; for (let k = -2; k <= 2; k++) { c.beginPath(); c.ellipse(-15, -430, Math.abs(k) * 15 + 3, 80, 0, Math.PI, 0); c.stroke(); }
  const sing = o.bird ?? 0, bob = Math.sin(t * 14) * 4 * sing;
  c.save(); c.translate(-15, -520 + bob);
  c.fillStyle = '#2f6a66'; c.beginPath(); c.ellipse(0, 0, 22, 14, -.2, 0, 7); c.fill(); outline(c, 1.5);
  c.beginPath(); c.moveTo(-18, 2); c.lineTo(-42, -10); c.lineTo(-38, 8); c.closePath(); c.fill(); outline(c, 1.5);
  c.beginPath(); c.arc(18, -12, 9, 0, 7); c.fill(); outline(c, 1.5);
  c.fillStyle = GOLD; c.beginPath(); c.moveTo(26, -14); c.lineTo(38, -12 - sing * 4); c.lineTo(26, -9); c.fill(); if (sing) { c.beginPath(); c.moveTo(26, -10); c.lineTo(37, -4 + sing * 2); c.lineTo(26, -8); c.fill(); }
  c.restore();
  if (sing > 0) { for (let k = 0; k < 3; k++) { const ph = ((t * 1.2 + k / 3) % 1); txt(c, '♪', 30 + ph * 60 + k * 10, -540 - ph * 70, { fam: 'DejaVu Sans', size: 26, color: INK, alpha: (1 - ph) * sing }); } }
  // dragons on both sides of tower
  [-1, 1].forEach(sd => {
    const bx = sd < 0 ? -100 : 70;
    c.strokeStyle = TEAL; c.lineWidth = 12; c.lineCap = 'round'; c.beginPath(); c.moveTo(bx, -400); c.bezierCurveTo(bx + sd * 60, -390, bx + sd * 10, -330, bx + sd * 56, -300); c.stroke();
    c.strokeStyle = INK; c.lineWidth = 1.5; c.stroke();
    c.save(); c.translate(bx + sd * 56, -300); c.scale(sd, 1); c.fillStyle = TEAL; c.beginPath(); c.moveTo(0, -10); c.lineTo(26, -14); c.lineTo(14, 0); c.lineTo(28, 10); c.lineTo(0, 10); c.closePath(); c.fill(); outline(c, 1.5); c.fillStyle = VERM; c.beginPath(); c.moveTo(14, 0); c.lineTo(28, -6); c.lineTo(28, 6); c.fill(); c.restore();
  });
  // ball path: from dome falcon down into left dragon mouth
  const bp = o.ball ?? -1;
  if (bp >= 0 && bp <= 1.15) { const q = clamp(bp), bx = lerp(-40, -166, q), by = lerp(-470, -300, E.in(q)); c.fillStyle = radial(c, bx - 2, by - 2, 1, 9, [[0, '#fff0b0'], [1, '#a07a20']]); c.beginPath(); c.arc(bx, by, 8, 0, 7); c.fill(); }
  // driver + drum
  const st = o.drum ?? 0;
  c.fillStyle = '#8a1c18'; rr(c, 240, -272, 36, 50, 6); c.fill(); outline(c, 1.5); c.fillStyle = CREAM; c.beginPath(); c.ellipse(258, -272, 18, 6, 0, 0, 7); c.fill(); outline(c, 1); c.strokeStyle = GOLD; c.lineWidth = 1.5; c.beginPath(); c.moveTo(242, -266); c.lineTo(274, -230); c.moveTo(274, -266); c.lineTo(242, -230); c.stroke();
  seatedFigure(c, 205, -235, 1.05, { robe: '#2f6a66', arm: -st * 1.2 + .3, stick: true });
  if (o.ring > 0) { c.strokeStyle = `rgba(58,42,30,${o.ring})`; c.lineWidth = 2; for (let k = 1; k <= 3; k++) { c.beginPath(); c.arc(258, -246, 20 + k * 14 * (1.4 - o.ring), -1, 1); c.stroke(); } }
  c.restore();
}

// ===== Musical boat + peg drum =====
function musicBoat(c, x, y, s, t, play = 1) {
  c.save(); c.translate(x, y + Math.sin(t * 1.6) * 5); c.rotate(Math.sin(t * 1.3) * .02); c.scale(s, s);
  // canopy
  c.strokeStyle = INK; c.lineWidth = 4; [-210, -70, 70, 210].forEach(px => { c.beginPath(); c.moveTo(px, -40); c.lineTo(px, -190); c.stroke(); });
  c.fillStyle = VERM; c.beginPath(); c.moveTo(-230, -190); for (let k = 0; k <= 8; k++) c.quadraticCurveTo(-230 + k * 57.5 - 28, -168, -230 + k * 57.5, -190); c.lineTo(230, -215); c.quadraticCurveTo(0, -260, -230, -215); c.closePath(); c.fill(); outline(c);
  c.fillStyle = GOLD; for (let k = 0; k < 8; k++) { c.beginPath(); c.arc(-200 + k * 57, -200, 4, 0, 7); c.fill(); }
  // musicians
  const inst = ['drum', 'harp', 'flute', 'cymbal'], cols = ['#2f6a66', '#7a2a1e', '#24476b', '#6a4a1a'];
  [-165, -55, 55, 165].forEach((px, i) => {
    const arm = Math.sin(t * (i === 0 ? 9 : 5) + i) * .5 * play;
    const [hx, hy] = seatedFigure(c, px, -42, 1.25, { robe: cols[i], arm, stick: i === 0 });
    c.strokeStyle = INK; c.lineWidth = 2;
    if (i === 0) { c.fillStyle = '#8a1c18'; c.beginPath(); c.ellipse(px + 40, -60, 16, 20, 0, 0, 7); c.fill(); c.stroke(); }
    if (i === 1) { c.fillStyle = 'rgba(0,0,0,0)'; c.beginPath(); c.moveTo(px + 22, -40); c.lineTo(px + 50, -110); c.lineTo(px + 56, -40); c.closePath(); c.strokeStyle = GOLD; c.lineWidth = 4; c.stroke(); c.strokeStyle = INK; c.lineWidth = .8; for (let k = 1; k < 5; k++) { c.beginPath(); c.moveTo(px + 22 + k * 6, -40); c.lineTo(px + 22 + k * 6 + (5 - k) * 3, -40 - k * 13); c.stroke(); } }
    if (i === 2) { c.strokeStyle = '#8a6a3a'; c.lineWidth = 4; c.beginPath(); c.moveTo(px + 6, -84); c.lineTo(px + 50, -70); c.stroke(); }
    if (i === 3) { c.fillStyle = GOLD; const sp = 6 + Math.abs(Math.sin(t * 6)) * 10 * play; [-1, 1].forEach(sd => { c.beginPath(); c.ellipse(px + 40, -70 + sd * sp, 16, 4, 0, 0, 7); c.fill(); c.strokeStyle = INK; c.lineWidth = 1; c.stroke(); }); }
  });
  // hull
  c.fillStyle = shade(c, 0, -50, 0, 50, [[0, '#8a5a2a'], [1, '#4a2a12']]);
  c.beginPath(); c.moveTo(-320, -90); c.quadraticCurveTo(-300, -40, -250, -40); c.lineTo(250, -40); c.quadraticCurveTo(300, -40, 320, -90); c.quadraticCurveTo(310, 30, 220, 44); c.lineTo(-220, 44); c.quadraticCurveTo(-310, 30, -320, -90); c.closePath(); c.fill(); outline(c);
  c.strokeStyle = GOLD; c.lineWidth = 4; c.beginPath(); c.moveTo(-280, -20); c.lineTo(280, -20); c.stroke();
  c.fillStyle = GOLD; for (let k = 0; k < 10; k++) { c.beginPath(); c.arc(-225 + k * 50, 12, 6, 0, 7); c.fill(); }
  // prow bird heads
  [-1, 1].forEach(sd => { c.save(); c.translate(sd * 322, -92); c.scale(sd, 1); c.fillStyle = GOLD; c.beginPath(); c.arc(0, -12, 12, 0, 7); c.fill(); outline(c, 1.5); c.beginPath(); c.moveTo(10, -14); c.lineTo(26, -8); c.lineTo(10, -6); c.fill(); outline(c, 1.2); c.restore(); });
  c.restore();
}
function water(c, y0, t, cols = ['#3d6b78', '#2e5562', '#24434f']) {
  cols.forEach((col, k) => {
    c.fillStyle = col; c.beginPath(); c.moveTo(-200, H + 200);
    for (let x = -200; x <= W + 200; x += 20) c.lineTo(x, y0 + k * 40 + Math.sin(x * .02 + t * (1.5 + k * .4) + k) * 6);
    c.lineTo(W + 200, H + 200); c.closePath(); c.fill();
    c.strokeStyle = 'rgba(230,240,230,.35)'; c.lineWidth = 1.5;
    for (let x = -200 + (k * 37) % 80; x <= W + 200; x += 80) { const yy = y0 + k * 40 + Math.sin(x * .02 + t * (1.5 + k * .4) + k) * 6 + 10; c.beginPath(); c.moveTo(x, yy); c.quadraticCurveTo(x + 15, yy - 5, x + 30, yy); c.stroke(); }
  });
}
function pegDrum(c, cx, cy, r, t, p) { // circular inset with rotating peg cylinder
  if (p <= 0) return;
  c.save(); c.translate(cx, cy); c.scale(E.back(p), E.back(p));
  c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 20 * S; c.shadowOffsetY = 8 * S;
  c.fillStyle = '#efe2c2'; c.beginPath(); c.arc(0, 0, r, 0, 7); c.fill(); c.shadowColor = 'transparent';
  c.save(); c.beginPath(); c.arc(0, 0, r - 8, 0, 7); c.clip();
  c.drawImage(TEX.paper, -r, -r, r * 2, r * 2);
  // cylinder
  const cw = r * 1.3, ch = r * .62, rows = 5;
  c.fillStyle = shade(c, 0, 0, 0, ch, [[0, '#a07a42'], [.5, '#e8c88a'], [1, '#8a6232']]); c.fillRect(-cw / 2, 0, cw, ch); c.strokeStyle = INK; c.lineWidth = 2; c.strokeRect(-cw / 2, 0, cw, ch);
  const cols = 4, rot = t * .9, PEGS = [[0, .1], [1, .35], [2, .6], [3, .85], [0, .5], [2, .2], [1, .75], [3, .4]];
  const lift = Array(cols).fill(0);
  PEGS.forEach(([col, ph]) => {
    const a = ((ph + rot) % 1) * Math.PI * 2, yy = ch / 2 - Math.cos(a) * ch / 2, vis = Math.sin(a) > 0;
    if (!vis) return; const px = -cw / 2 + (col + .5) * cw / cols;
    c.fillStyle = VERM; c.fillRect(px - 7, yy - 7, 14, 14); c.strokeStyle = INK; c.lineWidth = 1.2; c.strokeRect(px - 7, yy - 7, 14, 14);
    if (yy < ch * .12) lift[col] = Math.max(lift[col], 1 - yy / (ch * .12));
  });
  // levers
  for (let k = 0; k < cols; k++) {
    const px = -cw / 2 + (k + .5) * cw / cols, ang = -lift[k] * .5;
    c.save(); c.translate(px - 30, -40); c.rotate(ang); c.strokeStyle = INK; c.lineWidth = 5; c.beginPath(); c.moveTo(0, 0); c.lineTo(34, 36); c.stroke(); c.restore();
    c.fillStyle = INK; c.beginPath(); c.arc(px - 30, -40, 4, 0, 7); c.fill();
    if (lift[k] > .5) txt(c, '♪', px - 40, -70, { fam: 'DejaVu Sans', size: 24, color: VERM });
  }
  txt(c, 'pegs on a turning drum', 0, -r * .66, { fam: 'Special Elite', size: 17, color: INK });
  c.restore();
  c.strokeStyle = GOLD; c.lineWidth = 8; c.beginPath(); c.arc(0, 0, r - 4, 0, 7); c.stroke(); c.strokeStyle = INK; c.lineWidth = 1.5; c.stroke();
  c.restore();
}

// ===== Peacock fountain =====
function peacockFountain(c, x, y, s, t, o = {}) {
  c.save(); c.translate(x, y); c.scale(s, s);
  softShadow(c, 0, 0, 220, 20, .45);
  // basin
  c.fillStyle = shade(c, 0, -110, 0, 0, [[0, '#d9c08a'], [1, '#8a6a3a']]);
  c.beginPath(); c.moveTo(-230, -110); c.quadraticCurveTo(-210, -10, -60, -10); c.lineTo(60, -10); c.quadraticCurveTo(210, -10, 230, -110); c.closePath(); c.fill(); outline(c);
  c.fillStyle = '#3d6b78'; c.beginPath(); c.ellipse(0, -110, 230, 22, 0, 0, 7); c.fill(); outline(c);
  c.strokeStyle = GOLD; c.lineWidth = 3; c.beginPath(); c.moveTo(-200, -70); c.quadraticCurveTo(0, -40, 200, -70); c.stroke();
  // cabinet/column
  c.fillStyle = shade(c, -70, 0, 70, 0, [[0, '#c9b68e'], [.5, '#efe3c4'], [1, '#c9b68e']]); c.fillRect(-70, -380, 140, 260); c.strokeStyle = INK; c.lineWidth = 2; c.strokeRect(-70, -380, 140, 260);
  c.fillStyle = LAPIS; c.fillRect(-70, -392, 140, 14); c.fillStyle = GOLD; c.fillRect(-70, -396, 140, 4);
  // door
  const sv = o.servant ?? 0, open = clamp(sv * 3);
  c.fillStyle = '#20140c'; c.beginPath(); pointedArch(c, -40, -320, 80, 170); c.fill();
  if (sv > 0) {
    const out = E.out(clamp(sv * 2)); c.save(); c.beginPath(); pointedArch(c, -40, -320, 80, 170); c.rect(-300, -170, 600, 170); c.clip();
    seatedFigure(c, 0, -150 + (1 - out) * 10, 1.5, { robe: '#7a2a1e', arm: -.9 });
    c.restore();
    const hx = 26, hy = -228;
    if (o.towel) { c.fillStyle = '#f4f0e4'; rr(c, hx - 4, hy - 6, 46, 30, 3); c.fill(); outline(c, 1.2); c.fillStyle = VERM; c.fillRect(hx, hy + 14, 38, 4); }
    else { c.fillStyle = '#f2ead0'; rr(c, hx, hy, 26, 16, 5); c.fill(); outline(c, 1.2); }
  }
  if (open < 1) { c.save(); c.beginPath(); pointedArch(c, -40, -320, 80, 170); c.clip(); c.fillStyle = shade(c, -40, 0, 40, 0, [[0, '#8a5a2a'], [1, '#5a3a1a']]); c.fillRect(-40, -320, 80 * (1 - open), 170); c.restore(); }
  c.beginPath(); pointedArch(c, -40, -320, 80, 170); outline(c, 2);
  // peacock: tail fan
  c.save(); c.translate(0, -420);
  for (let k = 0; k < 15; k++) {
    const a = Math.PI + .15 + k * (Math.PI - .3) / 14, L = 170 + Math.sin(k * 1.3) * 8;
    const ex = Math.cos(a) * L, ey = Math.sin(a) * L;
    c.strokeStyle = '#2f6a46'; c.lineWidth = 16; c.lineCap = 'round'; c.beginPath(); c.moveTo(0, 0); c.lineTo(ex, ey); c.stroke();
    c.strokeStyle = '#4e8f5a'; c.lineWidth = 8; c.stroke();
    c.fillStyle = GOLD; c.beginPath(); c.ellipse(ex * .92, ey * .92, 12, 16, a + Math.PI / 2, 0, 7); c.fill();
    c.fillStyle = LAPIS; c.beginPath(); c.ellipse(ex * .92, ey * .92, 6, 8, a + Math.PI / 2, 0, 7); c.fill();
  }
  // body + neck + head
  c.fillStyle = shade(c, -30, -40, 30, 40, [[0, '#4f74b8'], [1, '#1a356b']]);
  c.beginPath(); c.ellipse(0, 10, 34, 44, 0, 0, 7); c.fill(); outline(c);
  c.beginPath(); c.moveTo(-10, -24); c.bezierCurveTo(-14, -70, 10, -90, 30, -96); c.lineTo(40, -84); c.bezierCurveTo(22, -76, 10, -60, 14, -20); c.closePath(); c.fill(); outline(c);
  c.beginPath(); c.arc(38, -94, 12, 0, 7); c.fill(); outline(c, 1.5);
  c.fillStyle = GOLD; c.beginPath(); c.moveTo(48, -96); c.lineTo(64, -86); c.lineTo(48, -88); c.fill();
  c.strokeStyle = INK; c.lineWidth = 1.2; for (let k = -1; k <= 1; k++) { c.beginPath(); c.moveTo(36, -104); c.lineTo(36 + k * 8, -122); c.stroke(); c.fillStyle = LAPIS; c.beginPath(); c.arc(36 + k * 8, -124, 3, 0, 7); c.fill(); }
  c.fillStyle = '#fff'; c.beginPath(); c.arc(41, -96, 2.5, 0, 7); c.fill();
  c.restore();
  // water stream from beak
  const wv = o.water ?? 0;
  if (wv > 0) {
    const bx = 62, by = -506, ex = 150, ey = -120;
    c.strokeStyle = 'rgba(170,210,220,.85)'; c.lineWidth = 7 * wv; c.lineCap = 'round';
    c.beginPath(); c.moveTo(bx, by); c.quadraticCurveTo(140, by - 10, ex, ey); c.stroke();
    c.fillStyle = 'rgba(200,230,240,.9)'; for (let k = 0; k < 8; k++) { const ph = (t * 1.8 + k / 8) % 1; const q = ph, xx = (1 - q) * (1 - q) * bx + 2 * (1 - q) * q * 140 + q * q * ex, yy = (1 - q) * (1 - q) * by + 2 * (1 - q) * q * (by - 10) + q * q * ey; c.beginPath(); c.arc(xx + 4, yy, 3, 0, 7); c.fill(); }
    c.strokeStyle = 'rgba(220,240,245,.7)'; c.lineWidth = 1.5; for (let k = 0; k < 3; k++) { const ph = (t * 1.5 + k / 3) % 1; c.beginPath(); c.ellipse(ex, ey + 6, 10 + ph * 40, 3 + ph * 8, 0, 0, 7); c.stroke(); }
  }
  c.restore();
}

// ===== Water-raising pump (crank + pistons) =====
function pumpMachine(c, x, y, s, t) {
  c.save(); c.translate(x, y); c.scale(s, s);
  const a = t * 2.2;
  c.strokeStyle = INK; c.lineWidth = 2.2; c.lineJoin = 'round';
  // water channel + paddle wheel
  c.fillStyle = 'rgba(61,107,120,.55)'; c.fillRect(-420, 120, 300, 50); c.strokeRect(-420, 120, 300, 50);
  c.save(); c.translate(-270, 60); c.rotate(a);
  c.beginPath(); c.arc(0, 0, 100, 0, 7); c.stroke(); c.beginPath(); c.arc(0, 0, 14, 0, 7); c.fillStyle = INK; c.fill();
  for (let k = 0; k < 10; k++) { c.save(); c.rotate(k / 10 * Math.PI * 2); c.beginPath(); c.moveTo(0, 0); c.lineTo(100, 0); c.stroke(); c.fillStyle = '#b08a52'; c.fillRect(92, -8, 34, 16); c.strokeRect(92, -8, 34, 16); c.restore(); }
  c.restore();
  // gears
  gear(c, -150, 60, 46, 12, a * 2.17, '#d9c08a'); gear(c, -46, 60, 46, 12, -a * 2.17 + .26, '#d9c08a');
  // crank disc
  const cx = -46, cy = 60, R = 34, px = cx + Math.cos(-a * 2.17) * R, py = cy + Math.sin(-a * 2.17) * R;
  c.fillStyle = VERM; c.beginPath(); c.arc(px, py, 7, 0, 7); c.fill(); c.stroke();
  // slotted rod to two pistons (moves horizontally)
  const dx = Math.cos(-a * 2.17) * R;
  c.strokeStyle = '#6a4a2a'; c.lineWidth = 8; c.beginPath(); c.moveTo(px, py); c.lineTo(px, -40); c.stroke();
  c.lineWidth = 10; c.beginPath(); c.moveTo(-46 + dx - 180, -40); c.lineTo(-46 + dx + 180, -40); c.stroke();
  c.strokeStyle = INK; c.lineWidth = 2.2;
  // cylinders
  [-1, 1].forEach(sd => {
    const cxl = -46 + sd * 250; c.fillStyle = 'rgba(217,192,138,.9)'; c.fillRect(cxl - 70, -70, 140, 60); c.strokeRect(cxl - 70, -70, 140, 60);
    const pist = cxl + dx - sd * 0; c.fillStyle = '#8a6a3a'; c.fillRect(pist - sd * 40 - 8, -66, 16, 52); c.strokeRect(pist - sd * 40 - 8, -66, 16, 52);
    // pipe up
    c.save(); c.beginPath(); c.moveTo(cxl + sd * 70, -40); c.lineTo(cxl + sd * 90, -40); c.lineTo(cxl + sd * 90, -265); c.lineTo(sd * 80 - 46, -265);
    c.strokeStyle = INK; c.lineWidth = 14; c.stroke(); c.strokeStyle = '#b08a52'; c.lineWidth = 9; c.stroke(); c.strokeStyle = 'rgba(80,140,170,.9)'; c.lineWidth = 4; c.setLineDash([10, 12]); c.lineDashOffset = -t * 60; c.stroke(); c.restore();
  });
  // tank + water out
  c.fillStyle = 'rgba(61,107,120,.6)'; c.fillRect(-126, -300, 160, 70); c.strokeRect(-126, -300, 160, 70);
  const flow = (Math.sin(a * 2.17) + 1) / 2;
  c.strokeStyle = 'rgba(120,170,190,.9)'; c.lineWidth = 6 + flow * 4; c.beginPath(); c.moveTo(34, -270); c.quadraticCurveTo(110, -280, 130, -200); c.stroke();
  c.restore();
}
function engineSketch(c, x, y, s, t) {
  c.save(); c.translate(x, y); c.scale(s, s); c.strokeStyle = '#2a2a2a'; c.lineWidth = 2.4;
  const a = t * 5, R = 40, cy = 80, px = Math.cos(a) * R, py = cy + Math.sin(a) * R;
  const L = 130, pistY = py - Math.sqrt(L * L - px * px);
  c.fillStyle = 'rgba(200,200,195,.6)'; c.fillRect(-60, -170, 120, 190); c.strokeRect(-60, -170, 120, 190);
  c.fillStyle = '#8a8a86'; c.fillRect(-56, pistY - 50, 112, 50); c.strokeRect(-56, pistY - 50, 112, 50);
  c.lineWidth = 8; c.beginPath(); c.moveTo(0, pistY - 20); c.lineTo(px, py); c.stroke(); c.lineWidth = 2.4;
  c.beginPath(); c.arc(0, cy, R + 14, 0, 7); c.stroke(); c.fillStyle = '#2a2a2a'; c.beginPath(); c.arc(px, py, 7, 0, 7); c.fill(); c.beginPath(); c.arc(0, cy, 8, 0, 7); c.fill();
  c.restore();
}
// ===== fire / embers =====
function flames(c, x0, x1, yb, t, h, a = 1) {
  c.save(); c.globalCompositeOperation = 'lighter';
  const n = noiseFactory(21);
  for (let x = x0; x < x1; x += 22) {
    const hh = h * (.5 + n(x * .02, t * 2.5)) * a;
    c.fillStyle = radial(c, x, yb, 4, hh, [[0, `rgba(255,230,140,${.9 * a})`], [.4, `rgba(255,140,40,${.6 * a})`], [1, 'rgba(120,20,0,0)']]);
    c.beginPath(); c.moveTo(x - 26, yb); c.quadraticCurveTo(x - 20, yb - hh * .5, x + Math.sin(t * 7 + x) * 10, yb - hh); c.quadraticCurveTo(x + 20, yb - hh * .5, x + 26, yb); c.closePath(); c.fill();
  }
  c.restore();
}
function embers(c, t, n0, a = 1) {
  const r = rng(n0); c.save(); c.globalCompositeOperation = 'lighter';
  for (let k = 0; k < 70; k++) { const sp = 40 + r() * 80, x0 = r() * W, ph = (t * sp / H + r()) % 1; const x = x0 + Math.sin(t * 2 + k) * 30, y = H + 20 - ph * (H + 60);
    c.fillStyle = `rgba(255,${140 + r() * 80},60,${(1 - ph) * a * .9})`; c.beginPath(); c.arc(x, y, 1.2 + r() * 2.5, 0, 7); c.fill(); }
  c.restore();
}
// manuscript page with mini illustration (cached)
function manuscriptPage(w, h, seed, kind) {
  const key = 'ms' + [w, h, seed, kind]; if (cache[key]) return cache[key];
  const base = paper(w, h, seed, { rough: 2.5, step: 6, burnW: 18 });
  const cv = mkCanvas(base.c.width, base.c.height), c = cv.getContext('2d'); c.drawImage(base.c, 0, 0); c.scale(S, S); c.translate(base.pad, base.pad);
  c.strokeStyle = GOLD; c.lineWidth = 3; c.strokeRect(14, 14, w - 28, h - 28); c.strokeStyle = VERM; c.lineWidth = 1; c.strokeRect(20, 20, w - 40, h - 40);
  c.save(); c.beginPath(); c.rect(24, 60, w - 48, h * .62); c.clip();
  if (kind === 'elephant') elephantClock(c, w / 2 - 10, 60 + h * .6, w / 800, 0, {});
  else if (kind === 'peacock') peacockFountain(c, w / 2, 60 + h * .6, w / 620, 0, {});
  else if (kind === 'pump') pumpMachine(c, w / 2 + 20, 60 + h * .38, w / 1000, 0);
  else if (kind === 'boat') { musicBoat(c, w / 2, 60 + h * .45, w / 760, 0, 0); }
  c.restore();
  c.fillStyle = 'rgba(58,42,30,.7)'; c.font = `${Math.round(w / 14)}px Amiri`; c.textAlign = 'right'; c.direction = 'rtl';
  const lines = ['في معرفة الحيل الهندسية', 'كتاب الجزري', 'الآلات والساعات'];
  for (let k = 0; k < 3; k++) c.fillText(lines[(k + seed) % 3], w - 36, 60 + h * .62 + 34 + k * (w / 11));
  const res = { c: cv, w, h, pad: base.pad }; cache[key] = res; return res;
}
function ribbon(c, s, x, y, w, p, o = {}) {
  if (p <= 0) return; c.save(); c.translate(x, y); c.scale(lerp(.3, 1, E.back(p)), 1); c.globalAlpha = clamp(p * 3);
  const h = o.h || 70; c.shadowColor = 'rgba(0,0,0,.5)'; c.shadowBlur = 14 * S; c.shadowOffsetY = 6 * S;
  c.fillStyle = '#7a1612'; [-1, 1].forEach(sd => { c.beginPath(); c.moveTo(sd * w / 2, -h / 2 + 14); c.lineTo(sd * (w / 2 + 60), -h / 2 + 14); c.lineTo(sd * (w / 2 + 36), 14); c.lineTo(sd * (w / 2 + 60), h / 2 + 14); c.lineTo(sd * w / 2, h / 2 + 14); c.closePath(); c.fill(); });
  c.fillStyle = shade(c, 0, -h / 2, 0, h / 2, [[0, '#c8463a'], [1, '#8e1d17']]); c.fillRect(-w / 2, -h / 2, w, h); c.shadowColor = 'transparent';
  c.strokeStyle = GOLD; c.lineWidth = 2; c.strokeRect(-w / 2 + 6, -h / 2 + 6, w - 12, h - 12);
  txt(c, s, 0, h * .18, { fam: o.fam || 'Cinzel', size: o.size || 38, color: '#f6ecd4', ls: 3 });
  c.restore();
}
