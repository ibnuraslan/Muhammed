// flat/bust.js - big close-up heads / busts in the flat cel style (thick ink, one shadow tone).
// Local units: head centre at (0,0), skull top ≈ -208, chin ≈ 192, shoulders ≈ 380, waist ≈ 1100.
// Caller: g.save(); g.translate(x,y); g.scale(k,k); bust(g, look, pose, 6/k); g.restore();
import { INK } from './flat.js';

const clampv = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export function shadeOf(hex, k = 0.74) {
  const n = parseInt(hex.slice(1), 16), r = n >> 16, g = (n >> 8) & 255, b = n & 255;
  const f = (v, cool) => Math.round(clampv(v * k + cool, 0, 255)).toString(16).padStart(2, '0');
  return '#' + f(r, -4) + f(g, 0) + f(b, 10);
}
export const LOOKS = {
  li: { skin: '#cdb59b', hair: 'flat', hairColor: '#17171a', shirt: '#b7babd', collar: '#a6a9ad', eyes: '#3b2c22', lines: 1, stubble: 0.5, jaw: 1.08 },
  tim: { skin: '#e0b88f', hair: 'spiky', hairColor: '#e2c25c', shirt: '#4f9a45', collar: '#93b27c', eyes: '#4a6a8a', lines: 0.2, jaw: 1.0 },
};

function strokeFill(g, fill, lw, ink = INK) { if (fill) { g.fillStyle = fill; g.fill(); } if (lw) { g.strokeStyle = ink; g.lineWidth = lw; g.lineJoin = 'round'; g.lineCap = 'round'; g.stroke(); } }
function pathPts(g, pts, close = true) { g.beginPath(); pts.forEach((p, i) => (i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]))); if (close) g.closePath(); }
function curve(g, pts, lw, color = INK) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); if (pts.length === 3) g.quadraticCurveTo(pts[1][0], pts[1][1], pts[2][0], pts[2][1]); else if (pts.length === 4) g.bezierCurveTo(pts[1][0], pts[1][1], pts[2][0], pts[2][1], pts[3][0], pts[3][1]); else g.lineTo(pts[1][0], pts[1][1]); g.strokeStyle = color; g.lineWidth = lw; g.lineCap = 'round'; g.stroke(); }

function headPath(g, tn, jaw = 1) {
  const n = 1 + 0.07 * tn, f = 1 - 0.07 * tn, j = jaw;
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
function arm(g, a, look, lw, front) {
  const { sh, el, hd } = a, skin = look.skin, sk2 = shadeOf(skin);
  const seg = (p, q, w1, w2) => { const dx = q[0] - p[0], dy = q[1] - p[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L;
    return [[p[0] + nx * w1, p[1] + ny * w1], [q[0] + nx * w2, q[1] + ny * w2], [q[0] - nx * w2, q[1] - ny * w2], [p[0] - nx * w1, p[1] - ny * w1]]; };
  const up = seg(sh, el, 50, 42), fo = seg(el, hd, 40, 30);
  // outline pass then fill pass (hides the seams)
  for (const pass of [0, 1]) {
    for (const [pts, r] of [[up, 0], [fo, 0]]) { pathPts(g, pts); if (pass) { g.fillStyle = skin; g.fill(); } else { g.strokeStyle = INK; g.lineWidth = lw * 2; g.stroke(); } }
    g.beginPath(); g.arc(el[0], el[1], 41, 0, 7); if (pass) { g.fillStyle = skin; g.fill(); } else { g.lineWidth = lw * 2; g.stroke(); }
  }
  // forearm shadow strip
  const fs = seg(el, hd, 40, 30); pathPts(g, [fs[2], fs[3], lerp2(fs[3], fs[0], 0.35), lerp2(fs[2], fs[1], 0.35)]); g.fillStyle = sk2; g.fill();
  // sleeve
  const m = [sh[0] + (el[0] - sh[0]) * 0.45, sh[1] + (el[1] - sh[1]) * 0.45];
  const sl = seg([sh[0] + (sh[0] - el[0]) * 0.08, sh[1] + (sh[1] - el[1]) * 0.08], m, 58, 64);
  pathPts(g, sl); strokeFill(g, look.shirt, lw);
  const ss = seg(sh, m, 58, 64); pathPts(g, [ss[2], ss[3], lerp2(ss[3], ss[0], 0.3), lerp2(ss[2], ss[1], 0.3)]); g.fillStyle = shadeOf(look.shirt); g.fill();
  pathPts(g, sl); g.strokeStyle = INK; g.lineWidth = lw; g.stroke();
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
  g.beginPath();
  if (look.hair === 'flat') {
    g.moveTo(-160 * f, -30); g.lineTo(-150 * f, -60); g.bezierCurveTo(-170 * f, -150, -150 * f, -230, -60, -240);
    g.lineTo(60, -242); g.bezierCurveTo(150 * n, -232, 172 * n, -150, 150 * n, -60); g.lineTo(160 * n, -30);
    g.lineTo(138 * n, -32); g.lineTo(132 * n, -100);
    const hl0 = [[100, -124], [70, -132], [hx + 34, -128], [hx + 6, -138], [hx - 24, -126], [-70, -134], [-102, -122]];
    for (const [px, py] of hl0) g.quadraticCurveTo(px + 14, py + 10, px, py);
    g.lineTo(-132 * f, -100); g.lineTo(-138 * f, -32);
  } else {      // spiky
    g.moveTo(-158 * f, -60); g.lineTo(-170 * f, -120);
    const spikes = [[-150, -205], [-140, -185], [-110, -250], [-90, -222], [-50, -270], [-25, -238], [15, -278], [35, -240], [75, -268], [92, -225], [128, -248], [132, -200], [165, -205], [160 * n, -150], [175 * n, -120]];
    for (const [px, py] of spikes) g.lineTo(px, py);
    g.lineTo(156 * n, -60); g.lineTo(140 * n, -70); g.lineTo(136 * n, -112);
    const fringe = [[110, -128], [80, -112], [hx + 60, -138], [hx + 30, -118], [hx + 4, -142], [hx - 30, -116], [-60, -138], [-92, -114], [-118, -130]];
    for (const [px, py] of fringe) g.lineTo(px, py);
    g.lineTo(-136 * f, -112); g.lineTo(-140 * f, -70);
  }
  g.closePath(); g.fillStyle = c; g.fill();
  // shadow side + strand marks
  g.save(); g.clip(); g.fillStyle = c2; g.beginPath(); g.ellipse(-150 * f, -110, 60, 170, 0.2, 0, 7); g.fill();
  g.strokeStyle = hl; g.lineWidth = lw * 0.9;
  const ticks = look.hair === 'spiky' ? [[-60, -215], [10, -228], [70, -210], [110, -190]] : [[-80, -205], [20, -215], [95, -190]];
  for (const [tx, ty] of ticks) { g.beginPath(); g.moveTo(tx, ty); g.lineTo(tx + 10, ty + 14); g.lineTo(tx + 2, ty + 18); g.lineTo(tx + 12, ty + 32); g.stroke(); }
  g.restore();
  g.strokeStyle = INK; g.lineWidth = lw; g.lineJoin = 'round'; g.stroke();
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
  const tn = p.tn || 0, fx = tn * 42, skin = look.skin, sk2 = shadeOf(skin, 0.78);
  const ey = -28, eo = clampv(p.eye ?? 1), mode = p.eyeMode || (eo < 0.12 ? 'closed' : 'open');
  // forehead / age lines
  if ((look.lines || 0) > 0.5 || p.strain) for (let i = 0; i < 2; i++) curve(g, [[fx - 70, -102 - i * 16], [fx, -110 - i * 16 - 6], [fx + 70, -102 - i * 16]], lw * 0.7);
  // deep eye sockets (creepy)
  const so = clampv(p.socket || 0);
  // brows
  const bIn = p.brow || 0, bUp = p.browUp || 0;
  for (const s of [-1, 1]) {
    const w = s * (tn * s > 0 ? 1.06 : 0.92);
    const pin = [fx + s * 18, -66 + bIn * 14 - bUp * 10], pout = [fx + w * 118, -82 - bIn * 6 - bUp * 4];
    g.beginPath(); g.moveTo(pin[0], pin[1] + 8); g.quadraticCurveTo(fx + w * 70, -96 + bIn * 4 - bUp * 12, pout[0], pout[1]); g.quadraticCurveTo(fx + w * 72, -84 + bIn * 6 - bUp * 10, pin[0], pin[1] - 6); g.closePath();
    strokeFill(g, look.hairColor === '#e2c25c' ? '#b8913a' : '#1c1a1c', lw * 0.6);
  }
  if (so > 0) {
    g.save(); g.globalAlpha = so;
    for (const s of [-1, 1]) {
      const w = s * (tn * s > 0 ? 1.06 : 0.92);
      g.beginPath(); g.moveTo(fx + s * 14, -60 + bIn * 10); g.bezierCurveTo(fx + w * 60, -84, fx + w * 120, -80, fx + w * 128, -52);
      g.bezierCurveTo(fx + w * 134, -18, fx + w * 110, 6, fx + w * 62, 6); g.bezierCurveTo(fx + w * 30, 6, fx + s * 10, -10, fx + s * 14, -60 + bIn * 10);
      g.fillStyle = '#2a282c'; g.fill();
    }
    g.restore();
  }
  // eyes
  for (const s of [-1, 1]) {
    const w = tn * s > 0 ? 1.08 : 0.9, ex = fx + s * 62 * w, R = 40 * w;
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
    g.beginPath(); g.arc(ix, iy, 15, 0, 7); g.fillStyle = look.eyes; g.fill(); g.strokeStyle = INK; g.lineWidth = lw * 0.6; g.stroke();
    g.beginPath(); g.arc(ix, iy, 7, 0, 7); g.fillStyle = '#0d0c0d'; g.fill();
    g.beginPath(); g.arc(ix + 4, iy - 5, 3.5, 0, 7); g.fillStyle = '#fff'; g.fill();
    g.fillStyle = 'rgba(40,30,30,0.25)'; g.fillRect(ex - R, ey - h * 2, R * 2, h * 0.9);   // lid shadow
    g.restore();
    curve(g, [[ex - R - 3, ey + 3], [ex - R * 0.1, ey - h * 2.15], [ex + R + 3, ey - 3]], lw * 1.5);
    curve(g, [[ex - R * 0.7, ey + h * 0.9], [ex, ey + h * 1.3], [ex + R * 0.8, ey + h * 0.6]], lw * 0.55);
    curve(g, [[ex - R * 0.6, ey + 24], [ex, ey + 30], [ex + R * 0.6, ey + 23]], lw * 0.5);   // bag
  }
  // nose
  const nx = fx + tn * 14;
  curve(g, [[nx - 10 - tn * 10, -18], [nx - 16 - tn * 6, 22], [nx - 20, 44]], lw * 0.8);
  for (const s of [-1, 1]) { g.beginPath(); g.moveTo(nx + s * 22, 42); g.bezierCurveTo(nx + s * 44, 46, nx + s * 46, 70, nx + s * 30, 76); g.strokeStyle = INK; g.lineWidth = lw * 0.9; g.stroke(); }
  g.beginPath(); g.moveTo(nx - 26, 77); g.quadraticCurveTo(nx, 88, nx + 26, 77); g.stroke();
  g.beginPath(); g.moveTo(nx - 4, 60); g.quadraticCurveTo(nx + 10, 66, nx + 2, 74); g.lineWidth = lw * 0.6; g.stroke();
  for (const s of [-1, 1]) { g.beginPath(); g.ellipse(nx + s * 17, 76, 8, 3.5, s * 0.35, 0, 7); g.fillStyle = '#2b2224'; g.fill(); }
  g.fillStyle = sk2; g.beginPath(); g.ellipse(nx + 4, 92, 26, 6, 0, 0, 7); g.fill();
  for (const s of [-1, 1]) curve(g, [[fx + s * 76, 2], [fx + s * 98, -2], [fx + s * 116, 10]], lw * 0.5);   // cheekbones
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
    g.beginPath(); g.moveTo(fx - 40, my); g.quadraticCurveTo(fx, my - 16, fx + 40, my); g.quadraticCurveTo(fx + 30, my + rh * 1.6, fx, my + rh * 1.6); g.quadraticCurveTo(fx - 30, my + rh * 1.6, fx - 40, my); g.closePath();
    g.fillStyle = '#3a1a1c'; g.fill(); g.save(); g.clip(); g.fillStyle = '#e8dcc4'; g.fillRect(fx - 40, my - 16, 80, 16); g.restore(); g.strokeStyle = INK; g.lineWidth = lw * 1.1; g.stroke();
  } else {    // neutral / talk
    const op = (p.talk || 0);
    if (op > 0.05) { g.beginPath(); g.ellipse(fx, my + 4, 30, 6 + 14 * op, 0, 0, 7); strokeFill(g, '#3a1a1c', lw); }
    else curve(g, [[fx - 42, my + 2], [fx, my + 8 - (p.smirk || 0) * 10], [fx + 46, my - 2 - (p.smirk || 0) * 10]], lw * 1.1);
    curve(g, [[fx - 22, my + 26], [fx, my + 32], [fx + 22, my + 26]], lw * 0.6);
  }
  // stubble
  if (look.stubble) { g.fillStyle = `rgba(40,36,40,${0.22 * look.stubble})`; g.beginPath(); g.moveTo(-130, 80); g.bezierCurveTo(-110, 170, 110, 170, 130, 80); g.bezierCurveTo(80, 196, -80, 196, -130, 80); g.fill(); }
  // sweat
  if (p.sweat) for (const [sx, sy] of [[-110, -90], [120, -60], [-128, 10]]) { g.beginPath(); g.moveTo(sx, sy); g.quadraticCurveTo(sx + 12, sy + 22, sx, sy + 26); g.quadraticCurveTo(sx - 12, sy + 22, sx, sy); strokeFill(g, '#d9eef7', lw * 0.6); }
  if (p.tears) for (const s of [-1, 1]) { g.fillStyle = 'rgba(190,225,245,0.85)'; g.beginPath(); g.moveTo(fx + s * 70, ey + 18); g.quadraticCurveTo(fx + s * 82, ey + 60 * p.tears, fx + s * 74, ey + 30 + 70 * p.tears); g.lineTo(fx + s * 66, ey + 20); g.fill(); }
}

export function bust(g, look, p = {}, lw = 5) {
  const tn = p.tn || 0, L = p.light ?? 1, skin = look.skin, sk2 = shadeOf(skin, 0.76);
  g.lineJoin = 'round'; g.lineCap = 'round';
  const behind = [p.armL, p.armR].filter(a => a && !a.front), front = [p.armL, p.armR].filter(a => a && a.front);
  if (!p.noBody) {
    for (const a of behind) arm(g, a, look, lw);
    // torso (t-shirt)
    const b = look.build || 1;
    g.beginPath(); g.moveTo(-100, 285); g.bezierCurveTo(-200 * b, 300, -290 * b, 320, -305 * b, 400);
    g.lineTo(-290 * b, 700); g.lineTo(-300 * b, 1200); g.lineTo(300 * b, 1200); g.lineTo(290 * b, 700); g.lineTo(305 * b, 400);
    g.bezierCurveTo(290 * b, 320, 200 * b, 300, 100, 285); g.closePath();
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
    // collar (ribbed)
    g.beginPath(); g.moveTo(-112, 282); g.quadraticCurveTo(0, 372, 112, 282); g.lineTo(86, 284); g.quadraticCurveTo(0, 336, -86, 284); g.closePath();
    strokeFill(g, look.collar, lw);
    curve(g, [[-30, 306], [0, 314], [30, 306]], lw * 0.4, shadeOf(look.collar, 0.7));
  }
  // head group
  g.save(); g.translate(p.hdx || 0, p.hdy || 0); g.rotate(p.tilt || 0);
  // ears
  for (const s of [-1, 1]) {
    if (tn * s < -0.6) continue;
    const x0 = s * 146 * (1 + 0.07 * tn * s) - tn * 10;
    g.beginPath(); g.moveTo(x0, -42); g.bezierCurveTo(x0 + s * 40, -66, x0 + s * 50, 34, x0 + s * 6, 66); g.closePath();
    strokeFill(g, s === -L ? sk2 : skin, lw);
    curve(g, [[x0 + s * 8, -30], [x0 + s * 32, -38], [x0 + s * 30, 26], [x0 + s * 6, 40]], lw * 0.6);
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
  face(g, look, p, lw);
  hair(g, look, tn, lw);
  if (look.headphones || p.headphones) headphones(g, tn, lw);
  g.restore();
  if (!p.noBody) for (const a of front) arm(g, a, look, lw, true);
}
