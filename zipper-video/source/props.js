// ---------- characters ----------
const SKIN = '#c99a72', SKIN_D = '#8d6243', SKIN_L = '#e8c4a0';
function drawHead(c, o = {}) {
  const hair = o.hairCol || '#2a1c14';
  // ears
  c.fillStyle = SKIN_D; [-1, 1].forEach(s => { c.beginPath(); c.ellipse(s * 24, 3, 5.5, 9, 0, 0, 7); c.fill(); });
  // face
  c.fillStyle = radial(c, -7, -8, 4, 40, [[0, SKIN_L], [.55, SKIN], [1, SKIN_D]]);
  c.beginPath(); c.ellipse(0, 0, 24, 31, 0, 0, 7); c.fill();
  // jaw shadow
  c.fillStyle = 'rgba(80,45,25,.25)'; c.beginPath(); c.ellipse(0, 18, 18, 12, 0, 0, Math.PI); c.fill();
  // hair
  c.fillStyle = hair;
  if (o.hair === 'wavy') {
    c.beginPath(); c.moveTo(-26, 6); c.bezierCurveTo(-34, -16, -30, -34, -14, -38);
    c.bezierCurveTo(-4, -46, 12, -44, 20, -36); c.bezierCurveTo(32, -30, 34, -10, 27, 6);
    c.bezierCurveTo(24, -6, 22, -18, 14, -22); c.bezierCurveTo(4, -16, -8, -24, -14, -18);
    c.bezierCurveTo(-20, -14, -22, -4, -26, 6); c.fill();
    c.strokeStyle = 'rgba(255,230,200,.12)'; c.lineWidth = 1.5;
    for (let i = 0; i < 5; i++) { c.beginPath(); c.arc(-14 + i * 7, -30, 8, 3.6, 5.4); c.stroke(); }
  } else if (o.hair === 'bald') {
    c.fillStyle = 'rgba(255,240,220,.35)'; c.beginPath(); c.ellipse(-6, -20, 9, 6, -.4, 0, 7); c.fill();
    c.fillStyle = hair; [-1, 1].forEach(s => { c.beginPath(); c.ellipse(s * 22, -6, 7, 14, s * .2, 0, 7); c.fill(); });
  } else if (o.hair === 'short') {
    c.beginPath(); c.moveTo(-25, -2); c.bezierCurveTo(-27, -30, -12, -38, 4, -37); c.bezierCurveTo(22, -36, 28, -22, 25, -2);
    c.bezierCurveTo(22, -16, 16, -22, 4, -24); c.lineTo(-6, -21); c.bezierCurveTo(-16, -22, -22, -14, -25, -2); c.fill();
  }
  // brows + eyes
  c.strokeStyle = o.hair === 'bald' ? '#3a2a20' : hair; c.lineWidth = 3; c.lineCap = 'round';
  [-1, 1].forEach(s => { c.beginPath(); c.moveTo(s * 4, -10); c.quadraticCurveTo(s * 10, -14, s * 16, -10); c.stroke(); });
  c.fillStyle = '#1b120c'; [-1, 1].forEach(s => { c.beginPath(); c.ellipse(s * 10, -3, 3.2, 2.1, 0, 0, 7); c.fill(); });
  c.fillStyle = 'rgba(90,50,30,.35)'; [-1, 1].forEach(s => { c.beginPath(); c.ellipse(s * 10, 1, 5, 1.6, 0, 0, Math.PI); c.fill(); });
  // nose
  c.strokeStyle = 'rgba(95,55,32,.8)'; c.lineWidth = 1.8; c.beginPath(); c.moveTo(-1, -4); c.quadraticCurveTo(-4, 9, 0, 11); c.quadraticCurveTo(4, 12, 5, 9); c.stroke();
  if (o.beard === 'full') {
    c.fillStyle = o.beardCol || hair;
    c.beginPath(); c.moveTo(-24, 0); c.bezierCurveTo(-26, 30, -16, 52, 0, 62); c.bezierCurveTo(16, 52, 26, 30, 24, 0);
    c.bezierCurveTo(20, 14, 12, 15, 6, 13); c.lineTo(-6, 13); c.bezierCurveTo(-12, 15, -20, 14, -24, 0); c.fill();
    c.strokeStyle = 'rgba(255,230,200,.1)'; c.lineWidth = 1; for (let i = -3; i <= 3; i++) { c.beginPath(); c.moveTo(i * 5, 22); c.lineTo(i * 4, 50 - Math.abs(i) * 4); c.stroke(); }
  } else if (o.beard === 'chin') {
    c.fillStyle = o.beardCol || hair; c.beginPath(); c.moveTo(-18, 16); c.bezierCurveTo(-14, 40, 14, 40, 18, 16); c.bezierCurveTo(10, 30, -10, 30, -18, 16); c.fill();
  } else {
    c.strokeStyle = '#5a2e22'; c.lineWidth = 2; c.beginPath(); c.moveTo(-6, 20); c.quadraticCurveTo(0, 22, 6, 20); c.stroke();
  }
  if (o.beard === 'full' || o.mustache) {
    c.fillStyle = o.beardCol || hair; c.beginPath(); c.moveTo(0, 13); c.bezierCurveTo(-8, 10, -16, 14, -17, 20); c.bezierCurveTo(-10, 17, -4, 19, 0, 17);
    c.bezierCurveTo(4, 19, 10, 17, 17, 20); c.bezierCurveTo(16, 14, 8, 10, 0, 13); c.fill();
  }
  if (o.glasses) {
    c.strokeStyle = '#2a2018'; c.lineWidth = 1.6;
    [-1, 1].forEach(s => { c.beginPath(); c.arc(s * 10, -3, 7, 0, 7); c.stroke(); });
    c.beginPath(); c.moveTo(-3, -4); c.lineTo(3, -4); c.stroke();
    c.fillStyle = 'rgba(255,255,255,.18)'; [-1, 1].forEach(s => { c.beginPath(); c.arc(s * 10 - 2, -5, 3, 0, 7); c.fill(); });
  }
}
function drawMan(c, x, y, s, o = {}) {
  c.save(); c.translate(x, y); c.scale(s, s);
  const coat = o.coat || '#24201d', coatL = o.coatL || '#3b342e', trou = o.trousers || '#2e2b29';
  softShadow(c, 0, 0, 70, 12, .55);
  // shoes + legs
  c.fillStyle = '#120d0a'; [-1, 1].forEach(sd => { c.beginPath(); c.ellipse(sd * 19 + sd * 4, -5, 21, 8, 0, 0, 7); c.fill(); });
  c.fillStyle = shade(c, -30, 0, 30, 0, [[0, '#1c1a19'], [.5, trou], [1, '#1c1a19']]);
  c.beginPath(); c.moveTo(-32, -190); c.lineTo(-3, -190); c.lineTo(-6, -8); c.lineTo(-30, -8); c.closePath(); c.fill();
  c.beginPath(); c.moveTo(32, -190); c.lineTo(3, -190); c.lineTo(6, -8); c.lineTo(30, -8); c.closePath(); c.fill();
  // arms (behind coat edges)
  c.fillStyle = shade(c, -70, 0, 70, 0, [[0, '#14110f'], [.2, coatL], [.5, coat], [.8, coatL], [1, '#14110f']]);
  [-1, 1].forEach(sd => { c.beginPath(); c.moveTo(sd * 46, -292); c.quadraticCurveTo(sd * 72, -280, sd * 72, -230); c.lineTo(sd * 74, -150); c.lineTo(sd * 52, -148); c.lineTo(sd * 50, -240); c.closePath(); c.fill(); });
  c.fillStyle = SKIN; [-1, 1].forEach(sd => { c.beginPath(); c.ellipse(sd * 64, -138, 11, 15, sd * -.15, 0, 7); c.fill(); });
  c.fillStyle = '#ece4d4'; [-1, 1].forEach(sd => { c.fillRect(sd * 63 - 12, -154, 24, 6); });
  // coat body
  c.fillStyle = shade(c, -66, 0, 66, 0, [[0, '#15120f'], [.25, coatL], [.5, coat], [.8, coatL], [1, '#15120f']]);
  c.beginPath(); c.moveTo(-16, -304); c.quadraticCurveTo(-52, -298, -58, -282); c.lineTo(-60, -200); c.lineTo(-64, -100);
  c.lineTo(-14, -104); c.lineTo(0, -178); c.lineTo(14, -104); c.lineTo(64, -100); c.lineTo(60, -200); c.lineTo(58, -282); c.quadraticCurveTo(52, -298, 16, -304); c.closePath(); c.fill();
  // waistcoat
  c.fillStyle = o.vest || '#3a3029'; c.beginPath(); c.moveTo(-20, -292); c.lineTo(20, -292); c.lineTo(18, -182); c.lineTo(0, -170); c.lineTo(-18, -182); c.closePath(); c.fill();
  c.fillStyle = '#c9a85a'; for (let i = 0; i < 4; i++) { c.beginPath(); c.arc(0, -262 + i * 22, 2.2, 0, 7); c.fill(); }
  if (o.chain) { c.strokeStyle = '#d8b766'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(0, -218); c.quadraticCurveTo(-10, -205, -16, -214); c.stroke(); }
  // shirt + tie
  c.fillStyle = '#efe8da'; c.beginPath(); c.moveTo(-14, -306); c.lineTo(14, -306); c.lineTo(0, -262); c.closePath(); c.fill();
  c.fillStyle = '#100c0a'; c.beginPath(); c.moveTo(0, -296); c.lineTo(-13, -303); c.lineTo(-13, -289); c.closePath(); c.moveTo(0, -296); c.lineTo(13, -303); c.lineTo(13, -289); c.closePath(); c.fill();
  // lapels
  c.fillStyle = shade(c, -40, -300, 40, -200, [[0, '#4a423b'], [1, '#1d1a17']]);
  [-1, 1].forEach(sd => { c.beginPath(); c.moveTo(sd * 15, -306); c.lineTo(sd * 36, -270); c.lineTo(sd * 26, -262); c.lineTo(sd * 36, -246); c.lineTo(sd * 20, -190); c.lineTo(sd * 18, -270); c.closePath(); c.fill(); });
  // neck + head
  c.fillStyle = SKIN_D; c.fillRect(-9, -318, 18, 16);
  c.save(); c.translate(0, -346); drawHead(c, o); c.restore();
  c.restore();
}

// sepia photo card (cached)
function photoCard(o, w = 230, h = 290, caption = '') {
  const key = 'ph' + JSON.stringify([o, w, h, caption]); if (cache[key]) return cache[key];
  const pad = 10, c = mkCanvas((w + pad * 2) * S, (h + pad * 2) * S), x = c.getContext('2d'); x.scale(S, S); x.translate(pad, pad);
  x.fillStyle = '#efe6d2'; x.fillRect(0, 0, w, h);
  const iw = w - 24, ih = h - (caption ? 70 : 24);
  x.save(); x.beginPath(); x.rect(12, 12, iw, ih); x.clip();
  x.fillStyle = radial(x, 12 + iw / 2, 12 + ih * .35, 10, ih, [[0, '#cdb48f'], [.6, '#9a7f5e'], [1, '#4c3a28']]); x.fillRect(12, 12, iw, ih);
  const sc = iw / 118; drawMan(x, 12 + iw / 2, 12 + ih * .4 + 346 * sc, sc, o);
  x.globalCompositeOperation = 'color'; x.fillStyle = '#7a5a36'; x.fillRect(12, 12, iw, ih);
  x.globalCompositeOperation = 'source-over';
  x.fillStyle = radial(x, 12 + iw / 2, 12 + ih / 2, ih * .2, ih * .75, [[0, 'rgba(0,0,0,0)'], [1, 'rgba(40,25,10,.6)']]); x.fillRect(12, 12, iw, ih);
  const r = rng(w + h); x.fillStyle = 'rgba(255,245,220,.25)'; for (let i = 0; i < 60; i++) x.fillRect(12 + r() * iw, 12 + r() * ih, r() * 2, r() * 2);
  x.restore();
  x.strokeStyle = 'rgba(80,55,30,.4)'; x.lineWidth = 1; x.strokeRect(12, 12, iw, ih);
  if (caption) txt(x, caption, w / 2, h - 24, { fam: 'Special Elite', size: 17, color: '#3a2c20' });
  const g = x.createLinearGradient(0, 0, w, h); g.addColorStop(0, 'rgba(120,80,30,.15)'); g.addColorStop(1, 'rgba(120,80,30,.35)'); x.fillStyle = g; x.fillRect(0, 0, w, h);
  const res = { c, w, h, pad }; cache[key] = res; return res;
}

// ---------- props ----------
function sewingMachine(c, x, y, s) {
  c.save(); c.translate(x, y); c.scale(s, s);
  softShadow(c, 0, 2, 130, 14, .6);
  const blk = shade(c, 0, -170, 0, 0, [[0, '#3b3632'], [.4, '#141210'], [1, '#050404']]);
  c.fillStyle = shade(c, 0, -30, 0, 0, [[0, '#4a3020'], [1, '#22140c']]); rr(c, -125, -24, 250, 24, 4); c.fill();
  c.fillStyle = blk; rr(c, -112, -40, 224, 18, 6); c.fill();
  // pillar + arm + head
  c.beginPath(); c.moveTo(48, -40); c.bezierCurveTo(40, -90, 44, -140, 60, -165); c.lineTo(-92, -165); c.quadraticCurveTo(-104, -165, -104, -150);
  c.lineTo(-104, -70); c.lineTo(-74, -70); c.lineTo(-74, -130); c.lineTo(70, -130); c.bezierCurveTo(84, -100, 90, -70, 96, -40); c.closePath(); c.fill();
  c.fillStyle = 'rgba(255,255,255,.15)'; c.fillRect(-96, -162, 150, 4);
  // gold decals
  c.strokeStyle = '#c9a24d'; c.lineWidth = 1.6;
  c.beginPath(); c.moveTo(-60, -148); c.bezierCurveTo(-40, -158, -20, -138, 0, -148); c.bezierCurveTo(20, -158, 40, -138, 52, -148); c.stroke();
  c.beginPath(); c.arc(70, -80, 10, 0, 5); c.stroke(); c.beginPath(); c.moveTo(-100, -150); c.lineTo(-100, -78); c.stroke();
  // needle
  c.fillStyle = '#c8c4bc'; c.fillRect(-92, -70, 5, 28); c.fillStyle = '#e8e4dc'; c.fillRect(-90.5, -44, 1.6, 8);
  // hand wheel
  c.fillStyle = '#0d0b0a'; c.beginPath(); c.arc(104, -116, 32, 0, 7); c.fill();
  c.strokeStyle = '#c9a24d'; c.lineWidth = 2; c.beginPath(); c.arc(104, -116, 27, 0, 7); c.stroke();
  c.strokeStyle = '#2c2825'; c.lineWidth = 4; for (let i = 0; i < 5; i++) { const a = i * 1.256; c.beginPath(); c.moveTo(104, -116); c.lineTo(104 + Math.cos(a) * 26, -116 + Math.sin(a) * 26); c.stroke(); }
  // spool
  c.fillStyle = '#8a1c18'; rr(c, -8, -192, 18, 26, 3); c.fill(); c.fillStyle = '#d9c39a'; c.fillRect(-11, -194, 24, 4); c.fillRect(-11, -168, 24, 4);
  c.strokeStyle = 'rgba(200,40,30,.8)'; c.lineWidth = 1; c.beginPath(); c.moveTo(0, -180); c.quadraticCurveTo(-50, -190, -88, -70); c.stroke();
  c.restore();
}
function leatherBoot(c, x, y, s, o = {}) {
  c.save(); c.translate(x, y); c.scale(s, s);
  softShadow(c, 30, 0, 120, 16, .6);
  c.fillStyle = '#1a0f08'; c.beginPath(); c.moveTo(-60, -12); c.lineTo(130, -12); c.quadraticCurveTo(142, -8, 136, 0); c.lineTo(-62, 0); c.closePath(); c.fill();
  c.fillStyle = shade(c, -60, 0, 140, 0, [[0, '#3a2012'], [.35, '#7a4626'], [.6, '#5c331b'], [1, '#2a170c']]);
  c.beginPath(); c.moveTo(-58, -12); c.lineTo(-54, -280); c.quadraticCurveTo(-10, -290, 30, -282); c.lineTo(36, -120);
  c.bezierCurveTo(60, -95, 110, -80, 128, -50); c.quadraticCurveTo(140, -30, 128, -12); c.closePath(); c.fill();
  c.fillStyle = 'rgba(255,220,180,.12)'; c.beginPath(); c.ellipse(-30, -180, 8, 90, 0, 0, 7); c.fill();
  c.fillStyle = o.accent || '#7e1f19'; c.fillRect(24, -276, 8, 160);
  c.strokeStyle = '#d8c7a8'; c.lineWidth = 2.5;
  for (let i = 0; i < 9; i++) { const yy = -262 + i * 17; c.beginPath(); c.moveTo(14, yy); c.lineTo(36, yy + 12); c.moveTo(36, yy); c.lineTo(14, yy + 12); c.stroke(); }
  c.fillStyle = '#c9a24d'; for (let i = 0; i < 10; i++) { c.beginPath(); c.arc(14, -262 + i * 17, 2.2, 0, 7); c.arc(36, -262 + i * 17, 2.2, 0, 7); c.fill(); }
  c.strokeStyle = 'rgba(0,0,0,.35)'; c.setLineDash([4, 4]); c.lineWidth = 1.2; c.beginPath(); c.moveTo(-46, -30); c.bezierCurveTo(20, -36, 80, -40, 120, -20); c.stroke(); c.setLineDash([]);
  c.restore();
}
function rubberBoot(c, x, y, s, flip = 1) {
  c.save(); c.translate(x, y); c.scale(s * flip, s);
  softShadow(c, 20, 0, 110, 14, .7);
  c.fillStyle = '#0b0908'; c.beginPath(); c.moveTo(-58, -14); c.lineTo(118, -14); c.quadraticCurveTo(128, -6, 120, 2); c.lineTo(-60, 2); c.closePath(); c.fill();
  c.fillStyle = shade(c, -60, 0, 130, 0, [[0, '#0a0908'], [.25, '#3a3633'], [.38, '#1a1817'], [.75, '#0f0d0c'], [1, '#262220']]);
  c.beginPath(); c.moveTo(-56, -14); c.lineTo(-62, -330); c.quadraticCurveTo(-10, -344, 40, -332); c.lineTo(38, -110);
  c.bezierCurveTo(70, -90, 112, -78, 120, -44); c.quadraticCurveTo(124, -24, 116, -14); c.closePath(); c.fill();
  c.fillStyle = 'rgba(255,255,255,.22)'; c.beginPath(); c.ellipse(-36, -210, 5, 110, .02, 0, 7); c.fill();
  // brass zipper down front
  c.fillStyle = '#5b4220'; c.fillRect(18, -330, 12, 230);
  c.fillStyle = '#d7b15a'; for (let yy = -326; yy < -104; yy += 6) { c.fillRect(19 + ((yy / 6) & 1) * 3, yy, 7, 3.4); }
  c.fillStyle = '#e8c870'; rr(c, 14, -334, 20, 22, 4); c.fill(); c.fillStyle = '#a07a30'; c.fillRect(21, -318, 6, 16);
  c.fillStyle = '#c9a24d'; rr(c, -62, -340, 104, 10, 3); c.fill();
  c.restore();
}
function pocketWatch(c, x, y, r, t) {
  c.save(); c.translate(x, y);
  softShadow(c, 6, 10, r * 1.2, r * 1.1, .55);
  c.fillStyle = shade(c, -r, -r, r, r, [[0, '#f1d78a'], [.5, '#a77c2c'], [1, '#5a3f12']]); c.beginPath(); c.arc(0, 0, r, 0, 7); c.fill();
  c.fillStyle = '#c9a24d'; rr(c, -7, -r - 14, 14, 16, 4); c.fill(); c.strokeStyle = '#b58e3a'; c.lineWidth = 4; c.beginPath(); c.arc(0, -r - 20, 9, 0, 7); c.stroke();
  c.fillStyle = radial(c, -r * .3, -r * .3, 2, r, [[0, '#fbf3df'], [1, '#d8c8a4']]); c.beginPath(); c.arc(0, 0, r * .82, 0, 7); c.fill();
  c.fillStyle = '#2a2018'; for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; c.save(); c.rotate(a); c.fillRect(-1, -r * .76, 2, i % 3 ? 5 : 9); c.restore(); }
  const sec = t * 1.0, mn = t / 60 + 0.62;
  c.strokeStyle = '#1a120c'; c.lineCap = 'round';
  c.lineWidth = 3; c.beginPath(); c.moveTo(0, 0); c.lineTo(Math.sin(mn * 6.283) * r * .6, -Math.cos(mn * 6.283) * r * .6); c.stroke();
  c.lineWidth = 2.2; c.beginPath(); c.moveTo(0, 0); c.lineTo(Math.sin(1.9) * r * .42, -Math.cos(1.9) * r * .42); c.stroke();
  c.strokeStyle = '#8a1c18'; c.lineWidth = 1.2; const sa = Math.floor(sec) / 60 * 6.283; c.beginPath(); c.moveTo(0, 0); c.lineTo(Math.sin(sa) * r * .7, -Math.cos(sa) * r * .7); c.stroke();
  c.fillStyle = 'rgba(255,255,255,.2)'; c.beginPath(); c.ellipse(-r * .3, -r * .35, r * .35, r * .18, -.6, 0, 7); c.fill();
  c.restore();
}
function button(c, x, y, r, col = '#5a3a22') {
  c.save(); c.translate(x, y); softShadow(c, 2, 4, r * 1.1, r * 1.1, .5);
  c.fillStyle = radial(c, -r * .3, -r * .3, 1, r, [[0, 'rgba(255,255,255,.35)'], [.3, col], [1, '#1a0f08']]); c.beginPath(); c.arc(0, 0, r, 0, 7); c.fill();
  c.strokeStyle = 'rgba(0,0,0,.35)'; c.lineWidth = 1.5; c.beginPath(); c.arc(0, 0, r * .72, 0, 7); c.stroke();
  c.fillStyle = '#1a0f08'; [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([a, b]) => { c.beginPath(); c.arc(a * r * .22, b * r * .22, r * .1, 0, 7); c.fill(); });
  c.restore();
}
function spool(c, x, y, s, col = '#7e1f19', rot = 0) {
  c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); softShadow(c, 6, 8, 46, 34, .5);
  c.fillStyle = '#c9a77a'; c.beginPath(); c.ellipse(-30, 0, 10, 30, 0, 0, 7); c.fill();
  c.fillStyle = shade(c, 0, -26, 0, 26, [[0, '#2a0a08'], [.35, col], [.6, col], [1, '#2a0a08']]); c.fillRect(-30, -24, 60, 48);
  c.strokeStyle = 'rgba(0,0,0,.18)'; c.lineWidth = 1; for (let i = -28; i < 30; i += 3) { c.beginPath(); c.moveTo(i, -24); c.lineTo(i + 2, 24); c.stroke(); }
  c.fillStyle = '#d8b88a'; c.beginPath(); c.ellipse(30, 0, 10, 30, 0, 0, 7); c.fill(); c.fillStyle = '#6a4a2a'; c.beginPath(); c.ellipse(30, 0, 3, 8, 0, 0, 7); c.fill();
  c.restore();
}
function penHand(c, x, y, rot = 0) { // pen tip at x,y
  c.save(); c.translate(x, y); c.rotate(rot);
  softShadow(c, 60, 60, 120, 60, .35);
  c.fillStyle = '#1a1412'; c.beginPath(); c.moveTo(0, 0); c.lineTo(10, -4); c.lineTo(160, -150); c.lineTo(150, -160); c.lineTo(2, -10); c.closePath(); c.fill();
  c.fillStyle = '#c9a24d'; c.beginPath(); c.moveTo(0, 0); c.lineTo(14, -8); c.lineTo(4, -16); c.closePath(); c.fill();
  // hand
  c.fillStyle = shade(c, 30, -60, 140, 40, [[0, SKIN_L], [.6, SKIN], [1, SKIN_D]]);
  c.beginPath(); c.moveTo(22, -30); c.bezierCurveTo(10, -10, 30, 10, 60, 6); c.bezierCurveTo(110, 4, 150, 40, 180, 90); c.lineTo(260, 60);
  c.bezierCurveTo(220, 0, 160, -70, 110, -80); c.bezierCurveTo(80, -84, 50, -60, 40, -50); c.closePath(); c.fill();
  c.strokeStyle = 'rgba(90,50,30,.4)'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(60, 4); c.quadraticCurveTo(80, -14, 70, -36); c.stroke();
  // sleeve
  c.fillStyle = shade(c, 160, 40, 260, 120, [[0, '#3a3530'], [1, '#141210']]);
  c.beginPath(); c.moveTo(170, 80); c.lineTo(250, 40); c.lineTo(340, 200); c.lineTo(240, 260); c.closePath(); c.fill();
  c.fillStyle = '#e8e0cf'; c.beginPath(); c.moveTo(166, 82); c.lineTo(252, 38); c.lineTo(262, 54); c.lineTo(176, 98); c.closePath(); c.fill();
  c.restore();
}
function envelope(c, x, y, rot, s = 1) {
  c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s);
  c.shadowColor = 'rgba(0,0,0,.5)'; c.shadowBlur = 16 * S; c.shadowOffsetY = 6 * S;
  c.fillStyle = '#e9dfc8'; c.fillRect(-130, -80, 260, 160); c.shadowColor = 'transparent';
  c.strokeStyle = 'rgba(120,90,50,.35)'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(-130, -80); c.lineTo(0, 10); c.lineTo(130, -80); c.stroke();
  c.fillStyle = radial(c, -6, 4, 2, 30, [[0, '#d04236'], [.7, '#8e1b14'], [1, '#5e0f0b']]); c.beginPath();
  for (let i = 0; i < 14; i++) { const a = i / 14 * 6.283, rr2 = 26 + (i % 2) * 4; c.lineTo(Math.cos(a) * rr2, 10 + Math.sin(a) * rr2); } c.fill();
  c.strokeStyle = 'rgba(60,8,5,.6)'; c.lineWidth = 2; c.beginPath(); c.arc(0, 10, 15, 0, 7); c.stroke();
  txt(c, 'H', 0, 18, { fam: 'Old Standard TT', size: 20, color: 'rgba(60,8,5,.7)' });
  c.restore();
}
function lantern(c, x, y, s, flick) {
  c.save(); c.translate(x, y); c.scale(s, s);
  c.globalCompositeOperation = 'lighter';
  c.fillStyle = radial(c, 0, 10, 0, 260, [[0, `rgba(255,200,90,${.55 * flick})`], [.3, `rgba(255,150,40,${.22 * flick})`], [1, 'rgba(0,0,0,0)']]);
  c.beginPath(); c.arc(0, 10, 260, 0, 7); c.fill(); c.globalCompositeOperation = 'source-over';
  c.strokeStyle = '#1a1410'; c.lineWidth = 4; c.beginPath(); c.arc(0, -70, 14, Math.PI, 0); c.stroke();
  c.fillStyle = '#1e1813'; c.beginPath(); c.moveTo(-30, -52); c.lineTo(30, -52); c.lineTo(18, -70); c.lineTo(-18, -70); c.closePath(); c.fill();
  c.fillStyle = radial(c, 0, 10, 2, 40, [[0, '#fff6cf'], [.4, `rgba(255,214,110,${.9 * flick})`], [1, 'rgba(200,120,40,.7)']]);
  c.beginPath(); c.moveTo(-24, -52); c.quadraticCurveTo(-34, 10, -22, 50); c.lineTo(22, 50); c.quadraticCurveTo(34, 10, 24, -52); c.closePath(); c.fill();
  c.strokeStyle = '#1e1813'; c.lineWidth = 4; [-24, 0, 24].forEach(xx => { c.beginPath(); c.moveTo(xx, -52); c.lineTo(xx * 1.05, 50); c.stroke(); });
  c.fillStyle = '#1e1813'; rr(c, -32, 48, 64, 14, 3); c.fill();
  c.restore();
}
function helmet(c, x, y, s, rot = 0) {
  c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s);
  softShadow(c, 14, 70, 190, 50, .7);
  c.fillStyle = shade(c, -170, 0, 170, 0, [[0, '#2b2c1a'], [.4, '#5e6038'], [.7, '#4a4b2c'], [1, '#22231a']]);
  c.beginPath(); c.ellipse(0, 40, 180, 64, 0, 0, 7); c.fill();
  c.strokeStyle = '#1e1f14'; c.lineWidth = 6; c.stroke();
  c.fillStyle = shade(c, -110, -110, 110, 40, [[0, '#7a7c4c'], [.5, '#55573a'], [1, '#2a2b1c']]);
  c.beginPath(); c.ellipse(0, 30, 112, 116, 0, Math.PI, 0); c.bezierCurveTo(112, 52, -112, 52, -112, 30); c.fill();
  c.fillStyle = 'rgba(255,255,230,.18)'; c.beginPath(); c.ellipse(-40, -40, 34, 50, -.5, 0, 7); c.fill();
  const r = rng(77); c.fillStyle = 'rgba(30,25,10,.35)'; for (let i = 0; i < 120; i++) { const a = Math.PI + r() * Math.PI, d = r() * 105; c.fillRect(Math.cos(a) * d, 30 + Math.sin(a) * d, 2, 2); }
  c.strokeStyle = '#4a3420'; c.lineWidth = 10; c.beginPath(); c.moveTo(-100, 60); c.bezierCurveTo(-60, 150, 60, 150, 100, 60); c.stroke();
  c.fillStyle = '#b8a060'; c.fillRect(-106, 54, 12, 12); c.fillRect(94, 54, 12, 12);
  c.restore();
}
function dogTags(c, x, y, rot) {
  c.save(); c.translate(x, y); c.rotate(rot);
  c.strokeStyle = '#9a9890'; c.lineWidth = 2.5; c.setLineDash([3, 2]); c.beginPath(); c.moveTo(-30, -60); c.bezierCurveTo(-120, -20, -80, 120, 40, 100); c.stroke(); c.setLineDash([]);
  [[0, 0, .2], [26, 18, -.3]].forEach(([dx, dy, rt]) => {
    c.save(); c.translate(dx, dy); c.rotate(rt); c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 8 * S; c.shadowOffsetY = 4 * S;
    c.fillStyle = shade(c, -26, -40, 26, 40, [[0, '#d8d6cc'], [.5, '#8f8d84'], [1, '#c8c6bc']]); c.beginPath(); c.arc(0, 0, 30, 0, 7); c.fill();
    c.shadowColor = 'transparent'; c.fillStyle = 'rgba(40,40,35,.6)'; c.font = '9px "Courier Prime"'; c.textAlign = 'center'; c.fillText('U.S.A.', 0, -6); c.fillText('1918', 0, 6); c.fillText('NO. 2471', 0, 18);
    c.restore();
  });
  c.restore();
}

// ---------- zipper ----------
function zipGap(y, sliderY, dir, maxGap, rate) { // dir=-1 open above slider; dir=1 open below
  const d = dir < 0 ? sliderY - y : y - sliderY; return d <= 0 ? 0 : Math.min(maxGap, d * rate);
}
function zipper(c, cx, y0, y1, sliderY, o = {}) {
  const pitch = o.pitch || 13, tw = o.tw || 22, th = o.th || 8.5, dir = o.dir ?? -1, maxGap = o.maxGap ?? 120, rate = o.rate ?? .5;
  const bp = o.style === 'blueprint';
  const metal = bp ? null : shade(c, -tw, 0, tw, 0, [[0, '#6b4f1c'], [.4, '#f2d283'], [.6, '#c79a3e'], [1, '#6b4f1c']]);
  const tape = o.tape || '#3a3326';
  for (let k = 0, y = y0; y <= y1 + pitch; k++, y += pitch / 2) {
    if (y > y1) break;
    const left = k % 2 === 0, g = zipGap(y, sliderY, dir, maxGap, rate) / 2;
    const xx = left ? cx - g : cx + g;
    // tape
    if (!bp) { c.fillStyle = tape; c.fillRect(left ? xx - tw - 18 : xx + tw - 4, y - pitch / 2, 22, pitch / 2 + 1); }
    c.save(); c.translate(xx, y);
    if (bp) { c.strokeStyle = 'rgba(235,245,255,.9)'; c.lineWidth = 1.6; c.beginPath(); c.roundRect(left ? -tw + 6 : -6, -th / 2, tw, th, 3); c.stroke(); }
    else { c.fillStyle = metal; c.beginPath(); c.roundRect(left ? -tw + 6 : -6, -th / 2, tw, th, 3); c.fill(); c.fillStyle = 'rgba(0,0,0,.35)'; c.fillRect(left ? -tw + 6 : -6, th / 2 - 1.5, tw, 1.5); }
    c.restore();
  }
  // slider
  if (sliderY > y0 - 40 && sliderY < y1 + 40) {
    c.save(); c.translate(cx, sliderY);
    if (bp) { c.strokeStyle = '#fff'; c.lineWidth = 2; c.beginPath(); c.moveTo(-26, -14 * dir); c.lineTo(26, -14 * dir); c.lineTo(16, 30 * dir); c.lineTo(-16, 30 * dir); c.closePath(); c.stroke(); }
    else {
      c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 10 * S; c.shadowOffsetY = 4 * S;
      c.fillStyle = shade(c, -26, 0, 26, 0, [[0, '#7a5a20'], [.35, '#f8e09a'], [.7, '#b88a35'], [1, '#5a4014']]);
      c.beginPath(); c.moveTo(-28, -16 * dir); c.lineTo(28, -16 * dir); c.lineTo(18, 34 * dir); c.lineTo(-18, 34 * dir); c.closePath(); c.fill();
      c.shadowColor = 'transparent';
      c.fillStyle = shade(c, -10, 0, 10, 0, [[0, '#8a6828'], [.5, '#ffeaa8'], [1, '#8a6828']]);
      rr(c, -9, 10 * dir - (dir < 0 ? 60 : 0), 18, 60, 7); c.fill();
      c.fillStyle = '#2a1c08'; rr(c, -4, (dir < 0 ? -42 : 48), 8, 20, 4); c.fill();
    }
    c.restore();
  }
}

// lightbulb sketch, returns list of strokes in local coords
function bulbStrokes() {
  return [
    p => { p.moveTo(-40, 60); p.bezierCurveTo(-46, 20, -96, 0, -96, -64); p.bezierCurveTo(-96, -130, -46, -164, 0, -164); p.bezierCurveTo(46, -164, 96, -130, 96, -64); p.bezierCurveTo(96, 0, 46, 20, 40, 60); },
    p => { p.moveTo(-40, 60); p.lineTo(40, 60); p.moveTo(-38, 76); p.lineTo(38, 76); p.moveTo(-36, 92); p.lineTo(36, 92); p.moveTo(-30, 108); p.quadraticCurveTo(0, 128, 30, 108); },
    p => { p.moveTo(-16, 60); p.lineTo(-22, -40); p.moveTo(16, 60); p.lineTo(22, -40); p.moveTo(-22, -40); for (let i = 0; i <= 8; i++) p.lineTo(-22 + i * 5.5, -40 + (i % 2 ? -14 : 0)); },
    p => { for (let i = 0; i < 7; i++) { const a = Math.PI + .25 + i * (Math.PI - .5) / 6; p.moveTo(Math.cos(a) * 128, -64 + Math.sin(a) * 128); p.lineTo(Math.cos(a) * 165, -64 + Math.sin(a) * 165); } },
  ];
}

// clenched-hand sketch under bulb
function handSketch(p) {
  p.moveTo(-70, 130); p.bezierCurveTo(-90, 160, -96, 230, -70, 280); p.lineTo(-60, 380); p.moveTo(70, 130); p.bezierCurveTo(100, 170, 96, 240, 70, 290); p.lineTo(60, 380);
  for (let i = 0; i < 4; i++) { const x = -60 + i * 34; p.moveTo(x, 132); p.bezierCurveTo(x - 6, 150, x - 4, 190, x + 14, 196); p.bezierCurveTo(x + 30, 196, x + 32, 160, x + 26, 132); }
  p.moveTo(-70, 210); p.bezierCurveTo(-30, 220, 10, 214, 30, 196);
}

// World's fair gate
function fairGate(c, cx, by, s, t) {
  c.save(); c.translate(cx, by); c.scale(s, s);
  const stone = shade(c, 0, -420, 0, 0, [[0, '#d9c7a4'], [1, '#9c8461']]);
  c.fillStyle = stone;
  // towers
  [-1, 1].forEach(sd => {
    c.fillRect(sd * 250 - 55, -420, 110, 420);
    c.beginPath(); c.moveTo(sd * 250 - 62, -420); c.lineTo(sd * 250 + 62, -420); c.lineTo(sd * 250 + 50, -440); c.lineTo(sd * 250 - 50, -440); c.fill();
    c.beginPath(); c.ellipse(sd * 250, -440, 46, 60, 0, Math.PI, 0); c.fill();
    c.fillRect(sd * 250 - 3, -540, 6, 50);
    // windows
    c.fillStyle = '#5c4a35'; for (let i = 0; i < 4; i++) { rr(c, sd * 250 - 14, -390 + i * 80, 28, 46, [14, 14, 0, 0]); c.fill(); }
    c.fillStyle = stone;
    // flag
    const ph = t * 5 + sd;
    c.fillStyle = '#8f2a22'; c.beginPath(); c.moveTo(sd * 250 + 3, -540);
    for (let i = 0; i <= 10; i++) c.lineTo(sd * 250 + 3 + i * 6, -540 + Math.sin(ph + i * .6) * 4 * i / 10);
    for (let i = 10; i >= 0; i--) c.lineTo(sd * 250 + 3 + i * 6, -510 + Math.sin(ph + i * .6) * 4 * i / 10);
    c.fill(); c.fillStyle = '#e8dcc0'; c.fillRect(sd * 250 + 3, -540, 20, 14); c.fillStyle = stone;
  });
  // central block with arch
  c.fillStyle = stone; c.beginPath(); c.rect(-200, -380, 400, 380);
  c.moveTo(-120, 0); c.lineTo(-120, -190); c.arc(0, -190, 120, Math.PI, 0); c.lineTo(120, 0); c.closePath(); c.fill('evenodd');
  c.fillStyle = '#c4ad86'; c.fillRect(-210, -390, 420, 22); c.fillRect(-210, -280, 420, 10);
  c.strokeStyle = '#7d6648'; c.lineWidth = 3; c.beginPath(); c.arc(0, -190, 124, Math.PI, 0); c.stroke();
  c.beginPath(); c.arc(0, -190, 140, Math.PI, 0); c.stroke();
  // pillars
  c.fillStyle = '#b39b74'; [-180, -150, 150, 180].forEach(px => c.fillRect(px - 7, -270, 14, 270));
  // banner text
  c.save(); c.font = '20px "Old Standard TT"'; c.fillStyle = '#4a3622'; c.textAlign = 'center'; c.letterSpacing = '3px';
  const str = "WORLD'S COLUMBIAN EXPOSITION"; const R = 160, tot = .9;
  for (let i = 0; i < str.length; i++) { const a = -Math.PI / 2 - tot + (i / (str.length - 1)) * tot * 2; c.save(); c.translate(Math.cos(a) * R, -190 + Math.sin(a) * R); c.rotate(a + Math.PI / 2); c.fillText(str[i], 0, 0); c.restore(); }
  c.font = '18px "Old Standard TT"'; c.fillText('CHICAGO', 0, -300); c.restore();
  // statues on top
  c.fillStyle = '#8a7556'; [-120, 0, 120].forEach(px => { c.beginPath(); c.ellipse(px, -400, 10, 6, 0, 0, 7); c.fill(); c.fillRect(px - 6, -430, 12, 30); c.beginPath(); c.arc(px, -436, 7, 0, 7); c.fill(); });
  c.restore();
}
function crowdPerson(c, x, y, s, kind, col, t, seed) {
  c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = col;
  const step = Math.sin(t * 6 + seed) * 4;
  if (kind === 0) { // lady
    c.beginPath(); c.moveTo(-6, -100); c.lineTo(6, -100); c.quadraticCurveTo(10, -70, 14, -60); c.bezierCurveTo(40, -30, 36, 0, 30, 0); c.lineTo(-30, 0); c.bezierCurveTo(-36, 0, -40, -30, -14, -60); c.quadraticCurveTo(-10, -70, -6, -100); c.fill();
    c.beginPath(); c.arc(0, -110, 9, 0, 7); c.fill(); c.beginPath(); c.ellipse(0, -118, 18, 5, 0, 0, 7); c.fill(); c.fillRect(-7, -128, 14, 10);
    c.beginPath(); c.moveTo(-8, -100); c.quadraticCurveTo(-20, -96, -20, -86); c.lineTo(20, -86); c.quadraticCurveTo(20, -96, 8, -100); c.fill();
  } else { // gentleman
    c.fillRect(-9 + step * .5, -50, 7, 50); c.fillRect(2 - step * .5, -50, 7, 50);
    c.beginPath(); c.moveTo(-14, -100); c.lineTo(14, -100); c.lineTo(16, -42); c.lineTo(-16, -42); c.closePath(); c.fill();
    c.beginPath(); c.arc(0, -110, 9, 0, 7); c.fill();
    if (kind === 1) { c.fillRect(-8, -132, 16, 18); c.fillRect(-13, -116, 26, 3); } else { c.beginPath(); c.ellipse(0, -118, 11, 6, 0, Math.PI, 0); c.fill(); c.fillRect(-14, -118, 28, 3); }
  }
  c.restore();
}

// vintage newspaper clipping
function clipping(w, h, seed, head, sub, art) {
  const key = 'cl' + seed; if (cache[key]) return cache[key];
  const base = paper(w, h, seed, { rough: 2.5, step: 5, tint: '#f4ecd8', burnW: 16 });
  const c = mkCanvas(base.c.width, base.c.height), x = c.getContext('2d'); x.drawImage(base.c, 0, 0);
  x.scale(S, S); x.translate(base.pad, base.pad);
  txt(x, head, w / 2, 40, { fam: 'Old Standard TT', size: 26, color: '#1e1814' });
  x.fillStyle = '#1e1814'; x.fillRect(14, 50, w - 28, 2); x.fillRect(14, 54, w - 28, 1);
  if (sub) txt(x, sub, w / 2, 76, { fam: 'Courier Prime', size: 13, color: '#2a221c' });
  const r = rng(seed);
  x.save(); x.translate(w / 2, h * .52); art(x); x.restore();
  x.fillStyle = 'rgba(40,32,26,.55)';
  for (let col = 0; col < 2; col++) for (let i = 0; i < 6; i++) x.fillRect(16 + col * (w / 2 - 6), h - 96 + i * 13, (w / 2 - 30) * (.6 + r() * .4), 4);
  return (cache[key] = base && { c, w, h, pad: base.pad });
}
