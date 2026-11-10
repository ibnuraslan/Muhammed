// flat/bust.js - big close-up heads / busts in the flat cel style (thick ink, one shadow tone).
// Local units: head centre at (0,0), skull top ≈ -208, chin ≈ 192, shoulders ≈ 380, waist ≈ 1100.
// Caller: g.save(); g.translate(x,y); g.scale(k,k); bust(g, look, pose, 6/k); g.restore();
import { INK } from './flat.js';
import { rng } from '../engine.js';

const clampv = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export function shadeOf(hex, k = 0.74) {
  const n = parseInt(hex.slice(1), 16), r = n >> 16, g = (n >> 8) & 255, b = n & 255;
  const f = (v, cool) => Math.round(clampv(v * k + cool, 0, 255)).toString(16).padStart(2, '0');
  return '#' + f(r, -4) + f(g, 0) + f(b, 10);
}
export const LOOKS = {
  li: { skin: '#cdb59b', hair: 'flat', hairColor: '#17171a', shirt: '#b7babd', collar: '#a6a9ad', eyes: '#3b2c22', lines: 1, stubble: 0.5, jaw: 1.08 },
  tim: { skin: '#e0b88f', hair: 'crew', hairColor: '#e2c25c', shirt: '#4f9a45', collar: '#93b27c', eyes: '#4a6a8a', lines: 0.2, jaw: 1.0 },
};

function strokeFill(g, fill, lw, ink = INK) { if (fill) { g.fillStyle = fill; g.fill(); } if (lw) { g.strokeStyle = ink; g.lineWidth = lw; g.lineJoin = 'round'; g.lineCap = 'round'; g.stroke(); } }
function pathPts(g, pts, close = true) { g.beginPath(); pts.forEach((p, i) => (i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]))); if (close) g.closePath(); }
function curve(g, pts, lw, color = INK) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); if (pts.length === 3) g.quadraticCurveTo(pts[1][0], pts[1][1], pts[2][0], pts[2][1]); else if (pts.length === 4) g.bezierCurveTo(pts[1][0], pts[1][1], pts[2][0], pts[2][1], pts[3][0], pts[3][1]); else g.lineTo(pts[1][0], pts[1][1]); g.strokeStyle = color; g.lineWidth = lw; g.lineCap = 'round'; g.stroke(); }

function headPath(g, tn, jaw = 1) {
  const n = 1 + 0.1 * tn, f = 1 - 0.1 * tn, j = jaw;
  g.beginPath(); g.moveTo(0, -208);
  g.bezierCurveTo(95 * n, -210, 150 * n, -172, 152 * n, -95);
  g.bezierCurveTo(157 * n, -30, 153 * n * j, 30, 142 * n * j, 96);
  g.bezierCurveTo(130 * n * j, 142, 96 * n * j, 176, 46 * n, 190);
  g.quadraticCurveTo(0, 199, -46 * f, 190);
  g.bezierCurveTo(-96 * f * j, 176, -130 * f * j, 142, -142 * f * j, 96);
  g.bezierCurveTo(-153 * f * j, 30, -157 * f, -30, -152 * f, -95);
  g.bezierCurveTo(-150 * f, -172, -95 * f, -210, 0, -208);
  g.closePath();
}

// one arm: shoulder -> elbow -> hand, sleeve over the upper arm, fist or open hand
export function arm(g, a, look, lw, front) {
  const { sh, el, hd } = a, skin = look.skin, sk2 = shadeOf(skin);
  const seg = (p, q, w1, w2) => { const dx = q[0] - p[0], dy = q[1] - p[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L;
    return [[p[0] + nx * w1, p[1] + ny * w1], [q[0] + nx * w2, q[1] + ny * w2], [q[0] - nx * w2, q[1] - ny * w2], [p[0] - nx * w1, p[1] - ny * w1]]; };
  const up = seg(sh, el, 60, 50), fo = seg(el, hd, 50, 38);
  // outline pass then fill pass (hides the seams)
  for (const pass of [0, 1]) {
    for (const [pts, r] of [[up, 0], [fo, 0]]) { pathPts(g, pts); if (pass) { g.fillStyle = skin; g.fill(); } else { g.strokeStyle = INK; g.lineWidth = lw * 2; g.stroke(); } }
    g.beginPath(); g.arc(el[0], el[1], 50, 0, 7); if (pass) { g.fillStyle = skin; g.fill(); } else { g.lineWidth = lw * 2; g.stroke(); }
  }
  // forearm shadow strip
  const fs = seg(el, hd, 50, 38); pathPts(g, [fs[2], fs[3], lerp2(fs[3], fs[0], 0.35), lerp2(fs[2], fs[1], 0.35)]); g.fillStyle = sk2; g.fill();
  // sleeve
  const m = [sh[0] + (el[0] - sh[0]) * 0.45, sh[1] + (el[1] - sh[1]) * 0.45];
  const sl = seg(sh, m, 70, 76), sc = look.shirt;
  for (const pass of [0, 1]) {
    pathPts(g, sl); if (pass) { g.fillStyle = sc; g.fill(); } else { g.strokeStyle = INK; g.lineWidth = lw * 2; g.stroke(); }
    if (!a.noCap) { g.beginPath(); g.arc(sh[0], sh[1], 72, 0, 7); if (pass) { g.fillStyle = sc; g.fill(); } else { g.lineWidth = lw * 2; g.stroke(); } }
  }
  pathPts(g, [sl[2], sl[3], lerp2(sl[3], sl[0], 0.3), lerp2(sl[2], sl[1], 0.3)]); g.fillStyle = shadeOf(sc); g.fill();
  curve(g, [sl[1], sl[2]], lw);                       // hem
  if (a.blood) splat(g, (sh[0] + m[0]) / 2, (sh[1] + m[1]) / 2, 60, a.blood, 3);
  // hand
  if (a.fist !== false) fist(g, hd, Math.atan2(hd[1] - el[1], hd[0] - el[0]), skin, lw, a.flip);
  return front;
}
const lerp2 = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];

export function fist(g, [x, y], ang, skin, lw, flip = false) {
  g.save(); g.translate(x, y); g.rotate(ang - Math.PI / 2); if (flip) g.scale(-1, 1);
  // +y now points from the wrist to the knuckles
  const sk2 = shadeOf(skin);
  g.beginPath(); g.moveTo(-36, -20); g.bezierCurveTo(-48, 20, -44, 62, -20, 72); g.lineTo(30, 70); g.bezierCurveTo(50, 60, 50, 18, 38, -22); g.closePath(); strokeFill(g, skin, lw);
  // curled fingers (knuckle bumps) + creases
  for (let i = 0; i < 4; i++) { const fx = -30 + i * 18; g.beginPath(); g.moveTo(fx, 40); g.quadraticCurveTo(fx + 9, 80, fx + 18, 42); strokeFill(g, skin, lw * 0.9); }
  g.beginPath(); g.moveTo(-34, 40); g.lineTo(38, 40); g.strokeStyle = INK; g.lineWidth = lw * 0.8; g.stroke();
  // thumb across the front
  g.beginPath(); g.moveTo(-38, 0); g.bezierCurveTo(-20, 8, 10, 22, 22, 30); g.quadraticCurveTo(28, 38, 18, 40); g.bezierCurveTo(0, 36, -28, 26, -40, 22); strokeFill(g, skin, lw * 0.9);
  g.beginPath(); g.moveTo(-36, -18); g.quadraticCurveTo(-30, -2, -38, 10); g.strokeStyle = sk2; g.lineWidth = lw * 2; g.stroke();
  g.restore();
}

function hair(g, look, tn, lw, front) {
  const c = look.hairColor, c2 = shadeOf(c, 0.7), hl = look.hair === 'spiky' ? '#f3dc8a' : '#3b3b42';
  const n = 1 + 0.07 * tn, f = 1 - 0.07 * tn, hx = tn * 26;
  const hp = new Path2D();
  if (look.hair === 'flat') {
    hp.moveTo(-160 * f, -30); hp.lineTo(-150 * f, -60); hp.bezierCurveTo(-170 * f, -150, -150 * f, -230, -60, -240);
    hp.lineTo(60, -242); hp.bezierCurveTo(150 * n, -232, 172 * n, -150, 150 * n, -60); hp.lineTo(160 * n, -30);
    hp.lineTo(138 * n, -32); hp.lineTo(132 * n, -100);
    const hl0 = [[100, -124], [70, -132], [hx + 34, -128], [hx + 6, -138], [hx - 24, -126], [-70, -134], [-102, -122]];
    for (const [px, py] of hl0) hp.quadraticCurveTo(px + 14, py + 10, px, py);
    hp.lineTo(-132 * f, -100); hp.lineTo(-138 * f, -32);
  } else if (look.hair === 'crew') {   // short crew cut: rounded top, slightly ragged edge
    hp.moveTo(-152 * f, -50); hp.bezierCurveTo(-176 * f, -150, -130 * f, -246, -10, -250);
    const top = [[30, -256], [60, -248], [96, -238], [126, -214], [150 * n, -178]];
    for (const [px, py] of top) hp.lineTo(px, py + ((px * 7) % 9) - 4);
    hp.bezierCurveTo(170 * n, -140, 160 * n, -90, 150 * n, -50); hp.lineTo(136 * n, -70); hp.lineTo(130 * n, -108);
    const fr = [[96, -126], [hx + 50, -136], [hx + 10, -130], [hx - 30, -138], [-80, -128], [-120, -118]];
    for (const [px, py] of fr) hp.quadraticCurveTo(px + 18, py - 8, px, py);
    hp.lineTo(-136 * f, -96);
  } else if (look.hair === 'messy') {   // tousled clumps, fringe over the forehead
    hp.moveTo(-158 * f, -30);
    const cl = [[-178, -128], [-150, -220], [-88, -268], [-18, -286], [52, -276], [116, -248], [162, -192], [176 * n, -112], [160 * n, -30]];
    let px0 = -158 * f, py0 = -30;
    for (const [px, py] of cl) { hp.quadraticCurveTo((px0 + px) / 2 * 1.12, (py0 + py) / 2 * 1.12, px, py); px0 = px; py0 = py; }
    const fr = [[134, -78], [100, -122], [hx + 70, -84], [hx + 34, -132], [hx - 6, -92], [hx - 46, -138], [-92, -98], [-126, -122], [-150 * f, -60]];
    for (const [px, py] of fr) hp.lineTo(px, py);
  } else if (look.hair === 'bun') {     // pulled back, swept fringe, bun on top (ends above the jaw)
    hp.moveTo(-156 * f, 10); hp.bezierCurveTo(-176 * f, -120, -120, -236, 0, -238); hp.bezierCurveTo(120, -236, 176 * n, -120, 156 * n, 10);
    hp.lineTo(140 * n, 0); hp.bezierCurveTo(140 * n, -70, 120, -112, 60, -134); hp.bezierCurveTo(10, -150, -60, -120, -110, -70); hp.lineTo(-140 * f, 0);
  } else if (look.hair === 'long') {
    hp.moveTo(-170 * f, 40); hp.bezierCurveTo(-190 * f, -140, -120, -246, 0, -246); hp.bezierCurveTo(120, -246, 190 * n, -140, 170 * n, 40);
    hp.lineTo(140 * n, 30); hp.bezierCurveTo(140, -80, 90, -130, 0, -132); hp.bezierCurveTo(-90, -130, -140, -80, -140 * f, 30);
  } else {      // spiky
    hp.moveTo(-158 * f, -60); hp.lineTo(-170 * f, -120);
    const spikes = [[-150, -205], [-140, -185], [-110, -250], [-90, -222], [-50, -270], [-25, -238], [15, -278], [35, -240], [75, -268], [92, -225], [128, -248], [132, -200], [165, -205], [160 * n, -150], [175 * n, -120]];
    for (const [px, py] of spikes) hp.lineTo(px, py);
    hp.lineTo(156 * n, -60); hp.lineTo(140 * n, -70); hp.lineTo(136 * n, -112);
    const fringe = [[110, -128], [80, -112], [hx + 60, -138], [hx + 30, -118], [hx + 4, -142], [hx - 30, -116], [-60, -138], [-92, -114], [-118, -130]];
    for (const [px, py] of fringe) hp.lineTo(px, py);
    hp.lineTo(-136 * f, -112); hp.lineTo(-140 * f, -70);
  }
  hp.closePath();
  if (look.hair === 'bun') { g.beginPath(); g.arc(18, -262, 62, 0, 7); strokeFill(g, c, lw); curve(g, [[-10, -280], [18, -250], [50, -282]], lw * 0.7, shadeOf(c, 0.7)); }
  g.fillStyle = c; g.fill(hp);
  // shadow side + strand marks
  g.save(); g.clip(hp); g.fillStyle = c2; g.beginPath(); g.ellipse(-150 * f, -110, 60, 170, 0.2, 0, 7); g.fill();
  g.strokeStyle = hl; g.lineWidth = lw * 0.9;
  const ticks = look.hair !== 'flat' ? [[-60, -215], [10, -228], [70, -210], [110, -190]] : [[-80, -205], [20, -215], [95, -190]];
  for (const [tx, ty] of ticks) { g.beginPath(); g.moveTo(tx, ty); g.lineTo(tx + 10, ty + 14); g.lineTo(tx + 2, ty + 18); g.lineTo(tx + 12, ty + 32); g.stroke(); }
  g.restore();
  g.strokeStyle = INK; g.lineWidth = lw; g.lineJoin = 'round'; g.stroke(hp);
  if (look.hat === 'cap') {      // police cap
    g.beginPath(); g.moveTo(-168 * f, -96); g.bezierCurveTo(-200 * f, -200, -140, -272, 0, -276); g.bezierCurveTo(140, -272, 200 * n, -200, 168 * n, -96); g.closePath();
    strokeFill(g, '#1b2234', lw);
    g.beginPath(); g.moveTo(-170 * f, -110); g.quadraticCurveTo(hx, -130, 170 * n, -110); g.lineTo(166 * n, -88); g.quadraticCurveTo(hx, -104, -166 * f, -88); g.closePath(); strokeFill(g, '#0e1220', lw);
    g.beginPath(); g.moveTo(-150 * f, -96); g.quadraticCurveTo(hx, -70, 150 * n, -96); g.quadraticCurveTo(hx + 10, -40, -150 * f, -96); strokeFill(g, '#0a0d16', lw);
    g.beginPath(); g.arc(hx, -170, 22, 0, 7); strokeFill(g, '#c9a640', lw * 0.8);
  }
}

function headphones(g, tn, lw) {
  g.strokeStyle = INK; g.lineWidth = 24; g.beginPath(); g.arc(0, -40, 176, Math.PI * 1.08, Math.PI * 1.92); g.stroke();
  g.strokeStyle = '#2b2c33'; g.lineWidth = 24 - lw * 2; g.stroke();
  for (const s of [-1, 1]) { if (tn * s < -0.55) continue; const x = s * 160 - tn * 14;
    g.beginPath(); g.ellipse(x, -10, 30, 52, 0, 0, 7); strokeFill(g, '#2b2c33', lw);
    g.beginPath(); g.ellipse(x + s * 6, -10, 14, 30, 0, 0, 7); strokeFill(g, '#b5342b', lw * 0.7); }
}

// the face features on top of the skin
function face(g, look, p, lw) {
  const tn = p.tn || 0, fx = tn * 60, skin = look.skin, sk2 = shadeOf(skin, 0.78);
  const EW = s => clampv(1 + 0.32 * tn * s, 0.62, 1.3);     // near eye bigger, far eye smaller
  const ey = -28, eo = clampv(p.eye ?? 1), mode = p.eyeMode || (eo < 0.12 ? 'closed' : 'open');
  // forehead / age lines
  if ((look.lines || 0) > 0.5 || p.strain) for (let i = 0; i < 2; i++) curve(g, [[fx - 70, -102 - i * 16], [fx, -110 - i * 16 - 6], [fx + 70, -102 - i * 16]], lw * 0.7);
  if ((p.browUp || 0) > 0.6) for (let i = 0; i < 2; i++) curve(g, [[fx - 50, -112 - i * 15], [fx, -104 - i * 15], [fx + 50, -112 - i * 15]], lw * 0.55);
  // deep eye sockets (creepy)
  const so = clampv(p.socket || 0);
  // brows
  const bIn = p.brow || 0, bUp = p.browUp || 0;
  if (so < 0.8) for (const s of [-1, 1]) {
    const w = s * EW(s);
    const pin = [fx + s * 18, -66 + bIn * 14 - bUp * 10], pout = [fx + w * 118, -82 - bIn * 6 - bUp * 4];
    g.beginPath(); g.moveTo(pin[0], pin[1] + 8); g.quadraticCurveTo(fx + w * 70, -96 + bIn * 4 - bUp * 12, pout[0], pout[1]); g.quadraticCurveTo(fx + w * 72, -84 + bIn * 6 - bUp * 10, pin[0], pin[1] - 6); g.closePath();
    strokeFill(g, look.hairColor === '#e2c25c' ? '#b8913a' : '#1c1a1c', lw * 0.6);
  }
  if (so > 0) {
    g.save(); g.globalAlpha = so * 0.92;
    for (const s of [-1, 1]) {
      const w = s * EW(s);    // the reference's dark bandit-mask sockets: slanted top, rounded bottom, no outline
      g.beginPath(); g.moveTo(fx + s * 8, -40 + bIn * 8); g.quadraticCurveTo(fx + w * 60, -74, fx + w * 132, -88);
      g.quadraticCurveTo(fx + w * 146, -44, fx + w * 122, -6); g.quadraticCurveTo(fx + w * 72, 12, fx + s * 26, 2);
      g.quadraticCurveTo(fx + s * 8, -14, fx + s * 8, -40 + bIn * 8); g.closePath();
      g.fillStyle = '#2e2b2e'; g.fill();
    }
    g.restore();
    for (let i = 0; i < 3; i++) curve(g, [[fx - 40 + i * 6, -112 - i * 14], [fx, -122 - i * 14 + (i === 1 ? 6 : 0)], [fx + 40 - i * 6, -112 - i * 14]], lw * 0.6);
  }
  // eyes
  for (const s of [-1, 1]) {
    const w = EW(s), ex = fx + s * 62 * w, R = 40 * w;
    if (so > 0.85) {   // eyes lost in the sockets: only a faint wet glint
      const gl = p.glint || 0; if (gl > 0) { g.fillStyle = `rgba(235,228,210,${gl})`; g.beginPath(); g.arc(ex + (p.look || 0) * 10 + s * 4, ey + 2, 5, 0, 7); g.fill(); }
      continue;
    }
    if (mode === 'squeeze') { curve(g, [[ex - R, ey - 4], [ex, ey + 10], [ex + R, ey - 6]], lw * 1.3); curve(g, [[ex + s * R * 0.9, ey - 2], [ex + s * (R + 16), ey - 12]], lw * 0.7); curve(g, [[ex + s * R * 0.9, ey + 4], [ex + s * (R + 16), ey + 8]], lw * 0.7); continue; }
    if (mode === 'closed' || eo < 0.12) { curve(g, [[ex - R, ey], [ex, ey + 12], [ex + R, ey - 2]], lw * 1.3); curve(g, [[ex - R * 0.6, ey + 22], [ex, ey + 28], [ex + R * 0.6, ey + 22]], lw * 0.55); continue; }
    const h = 18 * eo;
    g.beginPath(); g.moveTo(ex - R, ey + 2); g.quadraticCurveTo(ex - R * 0.1, ey - h * 2.1, ex + R, ey - 2); g.quadraticCurveTo(ex, ey + h * 1.25, ex - R, ey + 2); g.closePath();
    g.fillStyle = '#ece5d6'; g.fill();
    g.save(); g.clip();
    const ix = ex + (p.look || 0) * 14 * w, iy = ey + (p.lookY || 0) * 6;
    const ir = 15 * (p.iris || 1); g.beginPath(); g.arc(ix, iy, ir, 0, 7); g.fillStyle = look.eyes; g.fill(); g.strokeStyle = INK; g.lineWidth = lw * 0.6; g.stroke();
    g.beginPath(); g.arc(ix, iy, ir * 0.47, 0, 7); g.fillStyle = '#0d0c0d'; g.fill();
    g.beginPath(); g.arc(ix + 4, iy - 5, 3.5, 0, 7); g.fillStyle = '#fff'; g.fill();
    g.fillStyle = 'rgba(40,30,30,0.25)'; g.fillRect(ex - R, ey - h * 2, R * 2, h * 0.9);   // lid shadow
    g.restore();
    curve(g, [[ex - R - 3, ey + 3], [ex - R * 0.1, ey - h * 2.15], [ex + R + 3, ey - 3]], lw * (look.fem ? 2.2 : 1.5));
    if (look.fem) curve(g, [[ex + s * R, ey - 2 * (s > 0 ? 1 : 0.5)], [ex + s * (R + 12), ey - 12]], lw * 1.2);
    curve(g, [[ex - R * 0.7, ey + h * 0.9], [ex, ey + h * 1.3], [ex + R * 0.8, ey + h * 0.6]], lw * 0.55);
    if ((look.lines || 0) > 0.5) curve(g, [[ex - R * 0.6, ey + 24], [ex, ey + 30], [ex + R * 0.6, ey + 23]], lw * 0.5);   // bag
  }
  // nose
  const nx = fx + tn * 14;
  curve(g, [[nx - 10 - tn * 10, -18], [nx - 16 - tn * 6, 22], [nx - 20, 44]], lw * 0.8);
  for (const s of [-1, 1]) { g.beginPath(); g.moveTo(nx + s * 22, 42); g.bezierCurveTo(nx + s * 44, 46, nx + s * 46, 70, nx + s * 30, 76); g.strokeStyle = INK; g.lineWidth = lw * 0.9; g.stroke(); }
  g.beginPath(); g.moveTo(nx - 26, 77); g.quadraticCurveTo(nx, 88, nx + 26, 77); g.stroke();
  g.beginPath(); g.moveTo(nx - 4, 60); g.quadraticCurveTo(nx + 10, 66, nx + 2, 74); g.lineWidth = lw * 0.6; g.stroke();
  for (const s of [-1, 1]) { g.beginPath(); g.ellipse(nx + s * 17, 76, 8, 3.5, s * 0.35, 0, 7); g.fillStyle = '#2b2224'; g.fill(); }
  g.fillStyle = sk2; g.beginPath(); g.ellipse(nx + 4, 92, 26, 6, 0, 0, 7); g.fill();
  if ((look.lines || 0) > 0.5) for (const s of [-1, 1]) curve(g, [[fx + s * 76, 2], [fx + s * 98, -2], [fx + s * 116, 10]], lw * 0.5);   // cheekbones
  // mouth
  const mk = clampv(p.mouthK ?? 1), my = 118, mouth = p.mouth || 'neutral';
  if (mouth === 'grin') {
    const cw = 64 + 40 * mk, cy = my - 14 - 10 * mk, lo = my + 8 + 34 * mk;
    // laugh lines + cheek bulges
    for (const s of [-1, 1]) {
      curve(g, [[nx + s * 34, 60], [fx + s * (cw + 18), 80], [fx + s * (cw + 22), my + 18]], lw * 0.85);
      curve(g, [[fx + s * (cw - 10), cy - 30], [fx + s * (cw + 8), cy - 16]], lw * 0.6);
      curve(g, [[fx + s * 50, -6], [fx + s * 85, 6]], lw * 0.5);
    }
    const mpath = () => { g.beginPath(); g.moveTo(fx - cw, cy); g.quadraticCurveTo(fx, my + 4, fx + cw, cy); g.quadraticCurveTo(fx + cw * 0.6, lo + 4, fx, lo); g.quadraticCurveTo(fx - cw * 0.6, lo + 4, fx - cw, cy); g.closePath(); };
    mpath(); g.fillStyle = '#3a1a1c'; g.fill();
    g.save(); mpath(); g.clip();
    g.fillStyle = '#b55a63'; g.beginPath(); g.ellipse(fx, lo - 4, cw * 0.6, 14 + 10 * mk, 0, 0, 7); g.fill();  // gum / tongue
    // upper teeth band
    g.beginPath(); g.moveTo(fx - cw, cy); g.quadraticCurveTo(fx, my + 4, fx + cw, cy); g.lineTo(fx + cw, cy + 30); g.quadraticCurveTo(fx, my + 30 + 8 * mk, fx - cw, cy + 30); g.closePath();
    g.fillStyle = '#d8c48c'; g.fill(); g.strokeStyle = INK; g.lineWidth = lw * 0.6; g.stroke();
    for (let i = -5; i <= 5; i++) { const tx = fx + i * cw / 6; g.beginPath(); g.moveTo(tx, cy - 10); g.lineTo(tx, my + 32 + 8 * mk - Math.abs(i) * 3); g.stroke(); }
    // lower teeth
    g.beginPath(); g.moveTo(fx - cw * 0.85, lo - 6); g.quadraticCurveTo(fx, lo - 34 - 4 * mk, fx + cw * 0.85, lo - 6); g.lineTo(fx + cw, lo + 20); g.lineTo(fx - cw, lo + 20); g.closePath();
    g.fillStyle = '#cdb983'; g.fill(); g.stroke();
    for (let i = -4; i <= 4; i++) { const tx = fx + i * cw / 5.5; g.beginPath(); g.moveTo(tx, lo - 30); g.lineTo(tx, lo + 10); g.stroke(); }
    g.restore();
    mpath(); g.strokeStyle = INK; g.lineWidth = lw * 1.2; g.stroke();
    curve(g, [[fx - 34, lo + 22], [fx, lo + 30], [fx + 34, lo + 22]], lw * 0.7);        // lower lip
    curve(g, [[fx - 24, 176], [fx, 170], [fx + 24, 176]], lw * 0.6);                    // chin crease
  } else if (mouth === 'yawn') {
    const rh = 12 + 44 * mk, rw = 26 + 12 * mk;
    g.beginPath(); g.ellipse(fx, my + rh * 0.35, rw, rh, 0, 0, 7); g.fillStyle = '#3a1a1c'; g.fill();
    g.save(); g.clip(); g.fillStyle = '#c0606a'; g.beginPath(); g.ellipse(fx, my + rh * 1.15, rw * 0.9, rh * 0.55, 0, 0, 7); g.fill();
    g.fillStyle = '#eee4cf'; g.fillRect(fx - rw, my + rh * 0.35 - rh, rw * 2, 12); g.restore();
    g.beginPath(); g.ellipse(fx, my + rh * 0.35, rw, rh, 0, 0, 7); g.strokeStyle = INK; g.lineWidth = lw * 1.2; g.stroke();
    curve(g, [[fx - 24, my + rh * 1.35 + 14], [fx, my + rh * 1.35 + 20], [fx + 24, my + rh * 1.35 + 14]], lw * 0.6);
  } else if (mouth === 'smile') {
    g.beginPath(); g.moveTo(fx - 58, my - 8); g.quadraticCurveTo(fx, my + 34 * mk + 6, fx + 58, my - 8); g.quadraticCurveTo(fx, my + 8, fx - 58, my - 8); g.closePath();
    g.fillStyle = '#efe6d2'; g.fill(); g.strokeStyle = INK; g.lineWidth = lw * 1.1; g.stroke();
    for (const s of [-1, 1]) curve(g, [[fx + s * 62, my - 18], [fx + s * 70, my - 6], [fx + s * 64, my + 4]], lw * 0.6);
    curve(g, [[fx - 22, my + 44], [fx, my + 50], [fx + 22, my + 44]], lw * 0.6);
  } else if (mouth === 'scared') {
    const rh = 20 + 26 * mk;
    g.beginPath(); g.moveTo(fx - 34, my + 14); g.quadraticCurveTo(fx, my - 14, fx + 34, my + 14); g.bezierCurveTo(fx + 50, my + rh * 1.2, fx + 30, my + rh * 1.9, fx, my + rh * 1.9); g.bezierCurveTo(fx - 30, my + rh * 1.9, fx - 50, my + rh * 1.2, fx - 34, my + 14); g.closePath();
    g.fillStyle = '#3a1a1c'; g.fill(); g.save(); g.clip(); g.fillStyle = '#e8dcc4'; g.fillRect(fx - 40, my - 16, 80, 16); g.restore(); g.strokeStyle = INK; g.lineWidth = lw * 1.1; g.stroke();
  } else {    // neutral / talk
    const op = (p.talk || 0);
    if (op > 0.05) { g.beginPath(); g.ellipse(fx, my + 4, 30, 6 + 14 * op, 0, 0, 7); strokeFill(g, '#3a1a1c', lw); }
    else curve(g, [[fx - 42, my + 2], [fx, my + 8 - (p.smirk || 0) * 10], [fx + 46, my - 2 - (p.smirk || 0) * 10]], lw * 1.1);
    curve(g, [[fx - 22, my + 26], [fx, my + 32], [fx + 22, my + 26]], lw * 0.6);
  }
  if (p.blood) faceBlood(g, fx, my, mouth, mk, p.blood, lw);
  if (look.fem && mouth !== 'scared' && mouth !== 'grin') { g.fillStyle = 'rgba(170,70,80,0.55)'; g.beginPath(); g.ellipse(fx, my + 8, 30, 9, 0, 0, 7); g.fill(); }
  // stubble
  if (look.stubble && !look.fem) { g.fillStyle = `rgba(40,36,40,${0.22 * look.stubble})`; g.beginPath(); g.moveTo(-130, 80); g.bezierCurveTo(-110, 170, 110, 170, 130, 80); g.bezierCurveTo(80, 196, -80, 196, -130, 80); g.fill(); }
  // sweat
  if (p.sweat) for (const [sx, sy] of [[-110, -90], [120, -60], [-128, 10]]) { g.beginPath(); g.moveTo(sx, sy); g.quadraticCurveTo(sx + 12, sy + 22, sx, sy + 26); g.quadraticCurveTo(sx - 12, sy + 22, sx, sy); strokeFill(g, '#d9eef7', lw * 0.6); }
  if (p.tears) for (const s of [-1, 1]) { g.fillStyle = 'rgba(190,225,245,0.85)'; g.beginPath(); g.moveTo(fx + s * 70, ey + 18); g.quadraticCurveTo(fx + s * 82, ey + 60 * p.tears, fx + s * 74, ey + 30 + 70 * p.tears); g.lineTo(fx + s * 66, ey + 20); g.fill(); }
}

export function bust(g, look, p = {}, lw = 5) {
  const tn = p.tn || 0, L = p.light ?? 1, skin = look.skin, sk2 = shadeOf(skin, 0.76);
  g.lineJoin = 'round'; g.lineCap = 'round';
  const behind = [p.armL, p.armR].filter(a => a && !a.front), front = [p.armL, p.armR].filter(a => a && a.front);
  if (!p.noBody) {
    g.save(); g.translate(0, -95 * (p.pitch || 0));
    for (const a of behind) arm(g, a, look, lw);
    // torso (t-shirt)
    const b = look.build || 1;
    g.beginPath(); g.moveTo(-100, 285); g.bezierCurveTo(-190 * b, 296, -280 * b, 326, -312 * b, 430);
    g.lineTo(-296 * b, 700); g.lineTo(-300 * b, 1200); g.lineTo(300 * b, 1200); g.lineTo(296 * b, 700); g.lineTo(312 * b, 430);
    g.bezierCurveTo(280 * b, 326, 190 * b, 296, 100, 285); g.closePath();
    strokeFill(g, look.shirt, 0);
    g.save(); g.clip(); g.fillStyle = shadeOf(look.shirt, 0.76);
    g.beginPath(); g.moveTo(-320 * b, 300); g.bezierCurveTo(-220, 420, -240, 700, -170, 1220); g.lineTo(-340, 1220); g.closePath(); if (L < 0) g.scale(-1, 1); g.fill();
    g.strokeStyle = shadeOf(look.shirt, 0.6); g.lineWidth = lw * 0.8;
    for (const [a, c2, e] of [[[-150, 520], [-120, 620], [-140, 720]], [[160, 560], [130, 660], [150, 760]], [[-40, 800], [0, 860], [-20, 940]]]) curve(g, [a, c2, e], lw * 0.8, shadeOf(look.shirt, 0.6));
    g.restore();
    g.strokeStyle = INK; g.lineWidth = lw; g.stroke();
    // neck + jaw shadow
    pathPts(g, [[-76, 110], [76, 110], [88, 312], [-88, 312]]); strokeFill(g, skin, lw);
    g.fillStyle = sk2; g.beginPath(); g.moveTo(-80, 150); g.quadraticCurveTo(0, 260, 80, 150); g.lineTo(84, 230); g.quadraticCurveTo(0, 290, -84, 230); g.closePath(); g.fill();
    g.beginPath(); g.moveTo(-80, 120); g.lineTo(-84, 300); g.lineTo(-60, 300); g.lineTo(-58, 140); g.closePath(); g.fill();
    const top = look.top || 'tee';
    if (top === 'tee') {   // collar (ribbed)
      g.beginPath(); g.moveTo(-112, 282); g.quadraticCurveTo(0, 372, 112, 282); g.lineTo(86, 284); g.quadraticCurveTo(0, 336, -86, 284); g.closePath();
      strokeFill(g, look.collar, lw);
      curve(g, [[-30, 306], [0, 314], [30, 306]], lw * 0.4, shadeOf(look.collar, 0.7));
    } else if (top === 'hoodie') {
      g.beginPath(); g.moveTo(-190, 300); g.bezierCurveTo(-170, 420, 170, 420, 190, 300); g.bezierCurveTo(150, 250, 100, 270, 90, 290); g.quadraticCurveTo(0, 370, -90, 290); g.bezierCurveTo(-100, 270, -150, 250, -190, 300); g.closePath();
      strokeFill(g, shadeOf(look.shirt, 0.82), lw);
      curve(g, [[0, 395], [0, 1200]], lw); for (const s2 of [-1, 1]) curve(g, [[s2 * 40, 380], [s2 * 46, 470], [s2 * 40, 540]], lw * 0.9, '#c8c8c8');
    } else {               // collared: denim / polo / uniform
      for (const s2 of [-1, 1]) { pathPts(g, [[s2 * 20, 360], [s2 * 112, 282], [s2 * 150, 300], [s2 * 120, 400]]); strokeFill(g, top === 'uniform' ? '#141c2e' : shadeOf(look.shirt, 0.9), lw); }
      pathPts(g, [[-20, 360], [20, 360], [0, 400]]); strokeFill(g, skin, lw);
      curve(g, [[0, 400], [0, 1200]], lw * 0.8); for (let i = 0; i < 4; i++) { g.beginPath(); g.arc(14, 460 + i * 140, 8, 0, 7); strokeFill(g, '#d8d8d0', lw * 0.6); }
      if (top === 'uniform') { pathPts(g, [[-200, 520], [-140, 520], [-140, 600], [-170, 625], [-200, 600]]); strokeFill(g, '#c9a640', lw); g.fillStyle = '#20283c'; g.fillRect(110, 520, 110, 26); g.strokeRect(110, 520, 110, 26); }
    }
    if (p.shirtBlood) splat(g, 40, 560, 230, p.shirtBlood, 11);
    g.restore();
  }
  // head group
  g.save(); g.translate(p.hdx || 0, p.hdy || 0); g.rotate(p.tilt || 0);
  // ears
  for (const s of [-1, 1]) {
    if (tn * s < -0.6) continue;
    const x0 = s * 146 * (1 + 0.1 * tn * s) - tn * 10, ey0 = 46 * (p.pitch || 0);
    g.beginPath(); g.moveTo(x0, -42 + ey0); g.bezierCurveTo(x0 + s * 40, -66 + ey0, x0 + s * 50, 34 + ey0, x0 + s * 6, 66 + ey0); g.closePath();
    strokeFill(g, s === -L ? sk2 : skin, lw);
    curve(g, [[x0 + s * 8, -30 + ey0], [x0 + s * 32, -38 + ey0], [x0 + s * 30, 26 + ey0], [x0 + s * 6, 40 + ey0]], lw * 0.6);
  }
  headPath(g, tn, look.jaw || 1); g.fillStyle = sk2; g.fill();
  g.save(); headPath(g, tn, look.jaw || 1); g.clip(); g.translate(L * 30, -6); headPath(g, tn, look.jaw || 1); g.fillStyle = skin; g.fill(); g.restore();
  // cheekbone / temple shadow shapes (cel)
  g.save(); headPath(g, tn, look.jaw || 1); g.clip();
  g.fillStyle = sk2; { const fx = tn * 42, s = -L;    // wedge under the cheekbone on the shadow side + nose-side shadow
    g.beginPath(); g.moveTo(fx + s * 150, 10); g.quadraticCurveTo(fx + s * 105, 30, fx + s * 92, 92); g.quadraticCurveTo(fx + s * 120, 70, fx + s * 160, 80); g.closePath(); g.fill();
    g.beginPath(); g.moveTo(fx + s * 14, -40); g.quadraticCurveTo(fx + s * 30, 10, fx + s * 34, 58); g.lineTo(fx + s * 20, 62); g.quadraticCurveTo(fx + s * 16, 10, fx + s * 8, -40); g.closePath(); g.fill(); }
  if (p.underLight) { const gr = g.createLinearGradient(0, -200, 0, 200); gr.addColorStop(0, 'rgba(10,10,16,0.55)'); gr.addColorStop(0.6, 'rgba(10,10,16,0)'); g.fillStyle = gr; g.fillRect(-200, -260, 400, 480); }
  g.restore();
  headPath(g, tn, look.jaw || 1); g.strokeStyle = INK; g.lineWidth = lw * 1.1; g.stroke();
  if (p.pitch) { g.save(); headPath(g, tn, look.jaw || 1); g.clip(); g.translate(0, 18 * p.pitch); face(g, look, p, lw); g.restore(); }
  else face(g, look, p, lw);
  hair(g, look, tn, lw);
  if (look.headphones || p.headphones) headphones(g, tn, lw);
  g.restore();
  if (!p.noBody) for (const a of front) arm(g, a, look, lw, true);
}

// a big kitchen knife: handle at (x,y), blade pointing along ang (radians, 0 = right)
export function knife(g, x, y, ang, len = 300, lw = 5) {
  g.save(); g.translate(x, y); g.rotate(ang);
  const hl = len * 0.32, bw = len * 0.12;
  g.beginPath(); g.moveTo(-hl, -bw * 0.32); g.lineTo(0, -bw * 0.36); g.lineTo(0, bw * 0.36); g.lineTo(-hl, bw * 0.3); g.quadraticCurveTo(-hl - 10, 0, -hl, -bw * 0.32); g.closePath();
  strokeFill(g, '#6b3f26', lw); for (const r of [0.3, 0.7]) { g.beginPath(); g.arc(-hl * r, 0, bw * 0.08, 0, 7); g.fillStyle = '#d8d0c0'; g.fill(); }
  g.beginPath(); g.moveTo(0, -bw * 0.5); g.lineTo(len * 0.62, -bw * 0.42); g.quadraticCurveTo(len * 0.95, -bw * 0.3, len, bw * 0.05); g.quadraticCurveTo(len * 0.7, bw * 0.55, 0, bw * 0.5); g.closePath();
  strokeFill(g, '#c9ced4', lw);
  g.beginPath(); g.moveTo(len * 0.05, bw * 0.12); g.lineTo(len * 0.8, bw * 0.08); g.strokeStyle = '#eef2f5'; g.lineWidth = lw * 1.2; g.stroke();
  g.beginPath(); g.moveTo(len * 0.05, -bw * 0.28); g.lineTo(len * 0.6, -bw * 0.24); g.strokeStyle = '#8f969e'; g.lineWidth = lw; g.stroke();
  g.restore();
}

// ------------------------------------------------------------------ blood
const BLOOD = '#8a1418', BLOOD2 = '#b0201f';
export function splat(g, x, y, r, k = 1, seed = 1) {
  if (k <= 0) return; const R = rng(seed);
  g.save(); g.globalAlpha = Math.min(1, k * 1.2);
  for (let i = 0; i < 9; i++) {
    const a = R() * 6.28, d = R() * r, rr = (6 + R() * 22) * (r / 120) * (0.5 + k * 0.5);
    g.fillStyle = R() > 0.5 ? BLOOD : BLOOD2; g.beginPath(); g.ellipse(x + Math.cos(a) * d, y + Math.sin(a) * d * 0.8, rr, rr * (0.6 + R() * 0.6), a, 0, 7); g.fill();
  }
  g.restore();
}
// smear patch with drips running down from (x,y): an organic blob + a few tapered drips with round drops
export function smear(g, x, y, w, k = 1, seed = 1, drip = 1) {
  if (k <= 0) return; const R = rng(seed); g.save(); g.globalAlpha = Math.min(1, 0.45 + k * 0.55);
  const n = 9, pts = [];
  for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2, rr = (w / 2) * (0.65 + R() * 0.45); pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr * 0.42]); }
  g.fillStyle = BLOOD; g.beginPath();
  for (let i = 0; i < n; i++) { const p0 = pts[i], p1 = pts[(i + 1) % n], m = [(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2]; if (!i) g.moveTo(m[0], m[1]); else g.quadraticCurveTo(p0[0], p0[1], m[0], m[1]); }
  g.quadraticCurveTo(pts[0][0], pts[0][1], (pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2); g.closePath(); g.fill();
  g.fillStyle = BLOOD2; g.beginPath(); g.ellipse(x - w * 0.1, y - w * 0.04, w * 0.22, w * 0.07, 0, 0, 7); g.fill();
  const nd = 2 + Math.floor(R() * 3);
  for (let i = 0; i < nd; i++) {
    const xx = x - w * 0.35 + R() * w * 0.7, dw = Math.max(3, w * (0.03 + R() * 0.04)), dl = (w * 0.3 + R() * w * 0.8) * drip * k, y0 = y + w * 0.12;
    g.fillStyle = BLOOD; g.beginPath(); g.moveTo(xx - dw, y0 - 4); g.quadraticCurveTo(xx - dw * 0.5, y0 + dl * 0.6, xx - dw * 0.7, y0 + dl);
    g.arc(xx, y0 + dl, dw * 1.15, Math.PI, 0, true); g.quadraticCurveTo(xx + dw * 0.5, y0 + dl * 0.6, xx + dw, y0 - 4); g.closePath(); g.fill();
  }
  g.restore();
}
function faceBlood(g, fx, my, mouth, mk, k, lw) {
  const cw = mouth === 'grin' ? 64 + 40 * mk : 46;
  for (const s of [-1, 1]) smear(g, fx + s * (cw - 6), my - 4, 44, k, s > 0 ? 3 : 7, 1.6);
  smear(g, fx, my + 60, 110, k, 5, 2.2);
  splat(g, fx + 80, my + 110, 60, k * 0.8, 9); splat(g, fx - 70, my + 90, 50, k * 0.7, 13);
  if (mouth === 'grin') { g.save(); g.globalAlpha = 0.45 * k; g.fillStyle = BLOOD2; g.beginPath(); g.ellipse(fx, my + 10, cw * 0.8, 22, 0, 0, 7); g.fill(); g.restore(); }
}
export function bloodyKnife(g, x, y, ang, len, lw, k = 1) {
  knife(g, x, y, ang, len, lw);
  if (k <= 0) return; g.save(); g.translate(x, y); g.rotate(ang);
  const bw = len * 0.12, R = rng(4); g.beginPath(); g.moveTo(len * 0.35, -bw * 0.45);
  for (let i = 0; i < 6; i++) g.lineTo(len * (0.35 + i * 0.13), -bw * (0.45 - R() * 0.2));
  g.lineTo(len, bw * 0.05); g.lineTo(len * 0.4, bw * 0.5);
  for (let i = 0; i < 5; i++) g.lineTo(len * (0.4 - i * 0.02), bw * (0.5 - i * 0.18) + (R() - 0.5) * 6);
  g.closePath(); g.fillStyle = BLOOD; g.globalAlpha = Math.min(1, k); g.fill();
  for (const d of [0.5, 0.72]) { g.fillStyle = BLOOD; g.fillRect(len * d, bw * 0.4, 6, bw * (0.6 + R())); }
  g.restore();
}

// ------------------------------------------------------------------ hands
// back of a hand gripping something (fingers curled over the top); wrist toward -ang
export function grip(g, x, y, ang, skin, lw, k = 1) {
  g.save(); g.translate(x, y); g.rotate(ang + Math.PI / 2); g.scale(k, k);
  const sk2 = shadeOf(skin);
  // wrist + back of hand (wrist at +y)
  g.beginPath(); g.moveTo(-44, 150); g.quadraticCurveTo(-74, 60, -64, 20); g.quadraticCurveTo(-70, -10, -50, -30); g.lineTo(60, -34); g.quadraticCurveTo(80, -6, 72, 30); g.quadraticCurveTo(70, 80, 48, 150); g.closePath(); strokeFill(g, skin, lw);
  g.fillStyle = sk2; g.beginPath(); g.moveTo(40, 160); g.lineTo(52, 30); g.quadraticCurveTo(62, 0, 56, -26); g.lineTo(66, -20); g.quadraticCurveTo(78, 10, 68, 40); g.lineTo(54, 168); g.closePath(); g.fill();
  // curled fingers across the top
  const fw = [30, 32, 31, 26];
  let x0 = -60;
  for (let i = 0; i < 4; i++) {
    const w = fw[i], cx = x0 + w / 2 + 2, top = -96 + Math.abs(i - 1.5) * 8;
    g.beginPath(); g.moveTo(cx - w / 2, -24); g.lineTo(cx - w / 2, top + 14); g.quadraticCurveTo(cx - w / 2, top, cx, top); g.quadraticCurveTo(cx + w / 2, top, cx + w / 2, top + 14); g.lineTo(cx + w / 2, -24); g.closePath(); strokeFill(g, skin, lw);
    curve(g, [[cx - w * 0.3, -46], [cx, -40], [cx + w * 0.3, -46]], lw * 0.6); curve(g, [[cx - w * 0.25, top + 22], [cx, top + 27], [cx + w * 0.25, top + 22]], lw * 0.5);
    x0 += w + 2;
  }
  // thumb wrapping round the side
  g.beginPath(); g.moveTo(-62, 40); g.bezierCurveTo(-96, 10, -96, -50, -74, -76); g.quadraticCurveTo(-60, -86, -52, -70); g.bezierCurveTo(-64, -40, -60, -6, -48, 10); g.closePath(); strokeFill(g, skin, lw);
  g.restore();
}
// open hand with spread fingers (palm down on a surface or held up)
export function palm(g, x, y, ang, skin, lw, k = 1, spread = 1) {
  g.save(); g.translate(x, y); g.rotate(ang + Math.PI / 2); g.scale(k, k);
  const fingers = [[-0.42, 82, -40], [-0.14, 100, -16], [0.08, 104, 10], [0.3, 88, 34]];
  for (const [a, L, ox] of fingers) {
    g.save(); g.translate(ox, -50); g.rotate(a * spread);
    g.beginPath(); g.moveTo(-13, 0); g.lineTo(-11, -L + 12); g.quadraticCurveTo(0, -L - 4, 11, -L + 12); g.lineTo(13, 0); g.closePath(); strokeFill(g, skin, lw);
    curve(g, [[-8, -L * 0.45], [0, -L * 0.42], [8, -L * 0.45]], lw * 0.5); g.restore();
  }
  g.beginPath(); g.moveTo(-58, 120); g.lineTo(-60, -40); g.quadraticCurveTo(0, -66, 52, -44); g.lineTo(50, 120); g.closePath(); strokeFill(g, skin, lw);
  g.save(); g.translate(-56, 10); g.rotate(-0.9 * spread); g.beginPath(); g.moveTo(-14, 0); g.lineTo(-10, -62); g.quadraticCurveTo(0, -74, 10, -62); g.lineTo(14, 0); g.closePath(); strokeFill(g, skin, lw); g.restore();
  g.restore();
}

// ------------------------------------------------------------------ back view: back of the head + broad back
export function backView(g, look, p = {}, lw = 5) {
  const b = look.build || 1, hunch = p.hunch || 0, sc = look.shirt;
  // back
  g.beginPath(); g.moveTo(-120, 260 - 40 * hunch); g.bezierCurveTo(-260 * b, 250 - 60 * hunch, -360 * b, 300, -380 * b, 460);
  g.lineTo(-360 * b, 1300); g.lineTo(360 * b, 1300); g.lineTo(380 * b, 460); g.bezierCurveTo(360 * b, 300, 260 * b, 250 - 60 * hunch, 120, 260 - 40 * hunch); g.closePath();
  strokeFill(g, sc, lw);
  g.save(); g.clip(); g.fillStyle = shadeOf(sc, 0.78); g.beginPath(); g.moveTo(-400, 300); g.bezierCurveTo(-260, 500, -280, 900, -200, 1300); g.lineTo(-420, 1300); g.closePath(); g.fill(); g.restore();
  for (const [a, c, e] of [[[-20, 420], [-40, 700], [-10, 1000]], [[60, 460], [80, 640], [50, 820]], [[-180, 420], [-150, 520], [-170, 640]], [[200, 440], [170, 560], [190, 700]]]) curve(g, [a, c, e], lw * 0.9);
  // neck + head (lowered between the shoulders when hunched)
  g.save(); g.translate(0, 60 * hunch);
  pathPts(g, [[-70, 100], [70, 100], [96, 300], [-96, 300]]); strokeFill(g, shadeOf(look.skin, 0.85), lw); curve(g, [[0, 150], [0, 290]], lw * 0.6);
  g.beginPath(); g.ellipse(0, -40, 150, 180, 0, 0, 7); strokeFill(g, look.skin, lw);
  // hair covers the back of the skull, ragged at the nape
  g.beginPath(); g.moveTo(-150, 30); g.bezierCurveTo(-172, -150, -110, -238, 0, -240); g.bezierCurveTo(110, -238, 172, -150, 150, 30);
  g.quadraticCurveTo(120, 110, 60, 118); for (let i = 0; i <= 4; i++) g.lineTo(60 - i * 30, 124 + (i % 2) * 14); g.quadraticCurveTo(-120, 110, -150, 30); g.closePath(); strokeFill(g, look.hairColor, lw);
  for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * 138, -50); g.bezierCurveTo(s * 186, -70, s * 196, 40, s * 140, 70); g.closePath(); strokeFill(g, shadeOf(look.skin, 0.9), lw); curve(g, [[s * 150, -34], [s * 172, -26], [s * 166, 30]], lw * 0.6); }
  g.strokeStyle = '#3b3b42'; g.lineWidth = lw * 0.9; for (const [tx, ty] of [[-60, -150], [20, -170], [80, -110], [-20, -40]]) { g.beginPath(); g.moveTo(tx, ty); g.lineTo(tx + 10, ty + 14); g.lineTo(tx + 2, ty + 18); g.lineTo(tx + 12, ty + 32); g.stroke(); }
  g.restore();
}
