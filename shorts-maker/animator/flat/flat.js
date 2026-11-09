// flat/flat.js - pure 2D, hand-drawn-look scenes: perspective line-art backgrounds, film effects.
import { lerp, clamp, rng } from '../engine.js';
export const INK = '#151214';

// ---------------------------------------------------------------- perspective projector (camera looks down +z)
export function cam3({ x = 0, y = 1.6, z = 0, f = 900, cx = 540, cy = 860, roll = 0 } = {}) { return { x, y, z, f, cx, cy, roll }; }
export function P(c, X, Y, Z) { const z = Math.max(0.05, Z - c.z); return [c.cx + c.f * (X - c.x) / z, c.cy - c.f * (Y - c.y) / z, c.f / z]; }
// px per canvas-pixel for a person of height h at depth Z (people.js canvas: feet at y=1255)
export const personScale = (c, Z, h = 1.9) => (c.f / Math.max(0.05, Z - c.z)) * h / 1280;

export function poly(g, pts, fill, { ink = INK, lw = 3.5, alpha = 1 } = {}) {
  g.beginPath(); pts.forEach((p, i) => (i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]))); g.closePath();
  if (fill) { g.globalAlpha = alpha; g.fillStyle = fill; g.fill(); g.globalAlpha = 1; }
  if (ink) { g.strokeStyle = ink; g.lineWidth = lw; g.lineJoin = 'round'; g.stroke(); }
}
export const quad = (g, c, pts3, fill, o) => poly(g, pts3.map(p => P(c, ...p)), fill, o);
export function line3(g, c, a, b, color = INK, lw = 3) { const A = P(c, ...a), B = P(c, ...b); g.strokeStyle = color; g.lineWidth = lw * Math.min(2.5, Math.sqrt(A[2] / 300)); g.beginPath(); g.moveTo(A[0], A[1]); g.lineTo(B[0], B[1]); g.stroke(); }

// ---------------------------------------------------------------- film effects
export function vignette(g, W, H, k = 0.7) {
  const gr = g.createRadialGradient(W / 2, H * 0.45, H * 0.25, W / 2, H * 0.45, H * 0.75);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, `rgba(0,0,0,${k})`); g.fillStyle = gr; g.fillRect(0, 0, W, H);
}
const _grain = { c: null };
export function grain(g, W, H, t, k = 0.06) {
  if (!_grain.c) { _grain.c = document.createElement('canvas'); _grain.c.width = 256; _grain.c.height = 256; }
  const gc = _grain.c.getContext('2d'), im = gc.createImageData(256, 256), R = rng(Math.floor(t * 8) + 1);   // grain changes 8x/s (keeps files small)
  for (let i = 0; i < im.data.length; i += 4) { const v = R() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255 * k; }
  gc.putImageData(im, 0, 0); g.fillStyle = g.createPattern(_grain.c, 'repeat'); g.fillRect(0, 0, W, H);
}
export function wash(g, W, H, color, a) { g.globalAlpha = a; g.fillStyle = color; g.fillRect(0, 0, W, H); g.globalAlpha = 1; }
// failing-bulb flicker: returns 0..1 darkness to apply
export function flickerK(t, seed = 3, amount = 0.7) { const R = rng(seed); let k = 0; for (let i = 0; i < 30; i++) { const at = R() * 12, len = 0.05 + R() * 0.12; if (t > at && t < at + len) k = amount * (0.6 + 0.4 * Math.sin(t * 80)); } return k; }
export function finish(g, W, H, t, { vig = 0.75, flick = 0, seed = 3, tint = null, desat = 0.35 } = {}) {
  if (desat) { g.globalCompositeOperation = 'saturation'; g.fillStyle = `rgba(128,128,128,${desat})`; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over'; }
  if (tint) wash(g, W, H, tint, 0.18);
  const fk = flick ? flickerK(t, seed, flick) : 0; if (fk) wash(g, W, H, '#000', fk);
  vignette(g, W, H, vig); grain(g, W, H, t, 0.035);
}
export function blackout(g, W, H) { g.fillStyle = '#000'; g.fillRect(0, 0, W, H); }

// ---------------------------------------------------------------- censor badge (channel logo)
export function censor2D(g, x, y, r, k = 1) {
  if (k <= 0) return; const s = k < 0.15 ? (k / 0.15) * 1.15 : 1 + Math.sin(k * 6) * 0.01;
  g.save(); g.translate(x, y); g.scale(s, s);
  g.fillStyle = '#0d0d10'; g.beginPath(); g.arc(0, 0, r, 0, 7); g.fill();
  g.lineWidth = r * 0.07; g.strokeStyle = '#c0262d'; g.beginPath(); g.arc(0, 0, r * 0.94, 0, 7); g.stroke();
  g.fillStyle = '#e9e1cf'; g.beginPath(); g.ellipse(0, -r * 0.24, r * 0.5, r * 0.08, 0, 0, 7); g.fill();
  g.beginPath(); g.moveTo(-r * 0.26, -r * 0.26); g.lineTo(-r * 0.22, -r * 0.58); g.quadraticCurveTo(0, -r * 0.5, r * 0.22, -r * 0.58); g.lineTo(r * 0.26, -r * 0.26); g.closePath(); g.fill();
  g.strokeStyle = '#e9e1cf'; g.lineWidth = r * 0.04; for (const s2 of [-1, 1]) { g.beginPath(); g.arc(s2 * r * 0.17, -r * 0.06, r * 0.12, 0, 7); g.stroke(); }
  g.fillStyle = '#fff'; g.font = `900 ${Math.round(r * 0.24)}px Display, sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('CENSORED', 0, r * 0.3);
  g.restore();
}
