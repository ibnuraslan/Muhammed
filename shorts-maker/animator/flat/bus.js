// flat/bus.js - night bus interior drawn in one-point perspective (flat cel look) + window views.
import { P, quad, poly, INK } from './flat.js';
import { rng } from '../engine.js';

export const BUS = { wall: '#34363c', wall2: '#2b2d32', ceil: '#26282d', floor: '#3a3b40', aisle: '#323338', pole: '#9a9ea6', pole2: '#62666e',
  seat: '#1d2131', seatRim: '#7f848e', cush: '#252a3a', win: '#2f4562', win2: '#25384f', tree: '#3a5470', tree2: '#2c4258', sign: '#d4ae3a' };

// night sky + treeline seen through a window (screen-space, clipped by the caller)
export function nightView(g, x0, y0, x1, y1, horizon, t, speed = 40, seed = 4, big = 0) {
  const gr = g.createLinearGradient(0, y0, 0, y1); gr.addColorStop(0, '#2b3f5c'); gr.addColorStop(1, '#3d5677');
  g.fillStyle = gr; g.fillRect(x0, y0, x1 - x0, y1 - y0);
  const R = rng(seed), span = 1400, off = (t * speed) % span;
  for (const [col, hgt, k] of [[BUS.tree2, 1.0, 0.55], [BUS.tree, 0.75, 1]]) {
    g.fillStyle = col; g.beginPath(); g.moveTo(x0 - 10, y1 + 10);
    for (let i = -2; i < 22; i++) {
      const bx = x0 + i * 90 - off * k + ((R() * 30) | 0), bh = (60 + R() * 90) * hgt;
      g.lineTo(bx, horizon - bh * 0.6); g.quadraticCurveTo(bx + 45, horizon - bh - 30, bx + 95, horizon - bh * 0.5);
    }
    g.lineTo(x1 + 10, y1 + 10); g.closePath(); g.fill();
  }
  if (big) {     // close trees: tall pines and round bushy trees, slowly sliding by
    const R2 = rng(seed + 5), o2 = (t * speed * 1.6) % 1800;
    for (let i = -1; i < 6; i++) {
      const bx = x0 + i * 360 - o2 + R2() * 80, base = y1 + 20, hgt = (420 + R2() * 260) * big / 2.5, pine = R2() > 0.45;
      g.fillStyle = i % 2 ? '#2e4258' : '#34495f'; g.beginPath();
      if (pine) { for (let k = 0; k < 5; k++) { const yy = base - hgt * (k / 5), wd = 150 * (1 - k / 6) * big / 2.5; g.moveTo(bx - wd, yy); g.lineTo(bx, yy - hgt * 0.32); g.lineTo(bx + wd, yy); } }
      else { for (let k = 0; k < 5; k++) { g.moveTo(bx + 170, base - hgt * 0.5); g.arc(bx + (k - 2) * 60, base - hgt * (0.45 + 0.1 * Math.sin(k * 2)), 120 * big / 2.5, 0, 7); } }
      g.fill();
    }
  }
  g.fillStyle = '#1e2a3a'; g.fillRect(x0, horizon + 40, x1 - x0, y1 - horizon);
}

// one seat facing the camera; zb = z of its back panel. side: x centre of the seat
export function seat(g, c, xc, zb, { w = 0.44, top = 1.22, sy = 0.46, color = BUS.seat } = {}) {
  const zf = zb - 0.42;
  // cushion top + front
  quad(g, c, [[xc - w / 2, sy, zb], [xc + w / 2, sy, zb], [xc + w / 2, sy, zf], [xc - w / 2, sy, zf]], BUS.cush, { lw: 2.5 });
  quad(g, c, [[xc - w / 2, sy, zf], [xc + w / 2, sy, zf], [xc + w / 2, sy - 0.12, zf], [xc - w / 2, sy - 0.12, zf]], '#191c28', { lw: 2.5 });
  // back panel with rounded top + metal rim
  const a = P(c, xc - w / 2, top, zb), b = P(c, xc + w / 2, sy, zb), s = a[2];
  const x = a[0], y = a[1], W = b[0] - a[0], H = b[1] - a[1], r = Math.min(W * 0.42, 0.16 * s);
  const rr = () => { g.beginPath(); g.moveTo(x, y + H); g.lineTo(x, y + r); g.quadraticCurveTo(x, y, x + r, y); g.lineTo(x + W - r, y); g.quadraticCurveTo(x + W, y, x + W, y + r); g.lineTo(x + W, y + H); g.closePath(); };
  rr(); g.fillStyle = color; g.fill();
  g.strokeStyle = INK; g.lineWidth = Math.max(2, 0.06 * s); g.stroke();
  g.strokeStyle = BUS.seatRim; g.lineWidth = Math.max(1.5, 0.035 * s); g.stroke();
  // inner panel line
  g.strokeStyle = 'rgba(120,130,150,0.25)'; g.lineWidth = Math.max(1, 0.01 * s); g.beginPath(); g.moveTo(x + W * 0.18, y + H * 0.92); g.lineTo(x + W * 0.18, y + r * 0.9); g.quadraticCurveTo(x + W * 0.2, y + H * 0.08, x + W * 0.5, y + H * 0.07); g.stroke();
}

export function pole(g, c, x, z, y0 = 0, y1 = 2.25, wd = 0.04) {
  const a = P(c, x, y1, z), b = P(c, x, y0, z), w = Math.max(3, wd * a[2]);
  poly(g, [[a[0] - w / 2, a[1]], [a[0] + w / 2, a[1]], [b[0] + w / 2, b[1]], [b[0] - w / 2, b[1]]], BUS.pole, { lw: Math.max(1.5, w * 0.18) });
  g.fillStyle = BUS.pole2; g.fillRect(a[0] + w * 0.12, a[1], w * 0.3, b[1] - a[1]);
  g.fillStyle = '#d6d9de'; g.fillRect(a[0] - w * 0.3, a[1], w * 0.18, b[1] - a[1]);
}

// a seated passenger in silhouette (head + shoulders over a seat back)
export function silhouette(g, c, x, z, k = 1) {
  const h = P(c, x, 1.32, z), s = h[2];
  g.fillStyle = '#121318'; g.beginPath(); g.ellipse(h[0], h[1], 0.1 * s, 0.13 * s, 0, 0, 7); g.fill();
  g.beginPath(); g.moveTo(h[0] - 0.23 * s, h[1] + 0.5 * s); g.quadraticCurveTo(h[0] - 0.22 * s, h[1] + 0.14 * s, h[0], h[1] + 0.14 * s); g.quadraticCurveTo(h[0] + 0.22 * s, h[1] + 0.14 * s, h[0] + 0.23 * s, h[1] + 0.5 * s); g.fill();
}

// full aisle view. people: [{z, draw(g)}] drawn in depth order among the seat rows
export function aisle(g, c, t, { W = 1080, H = 1920, rows = 11, z0 = 1.2, dz = 0.92, people = [], sil = [], lights = 1, skip = () => false } = {}) {
  const X = 1.3, Y = 2.28, ZE = z0 + rows * dz + 0.6, zn = c.z + 0.25;
  g.fillStyle = BUS.wall2; g.fillRect(0, 0, W, H);
  // rear wall + rear window + sign
  quad(g, c, [[-X, Y, ZE], [X, Y, ZE], [X, 0, ZE], [-X, 0, ZE]], BUS.wall2, { lw: 2 });
  const rw = [P(c, -0.9, 1.9, ZE), P(c, 0.9, 1.0, ZE)];
  g.save(); g.beginPath(); g.rect(rw[0][0], rw[0][1], rw[1][0] - rw[0][0], rw[1][1] - rw[0][1]); g.clip();
  nightView(g, rw[0][0], rw[0][1], rw[1][0], rw[1][1], (rw[0][1] + rw[1][1]) / 2 + 10, t, 10, 9); g.restore();
  g.strokeStyle = INK; g.lineWidth = 2; g.strokeRect(rw[0][0], rw[0][1], rw[1][0] - rw[0][0], rw[1][1] - rw[0][1]);
  quad(g, c, [[-0.3, 2.16, ZE - 0.01], [0.3, 2.16, ZE - 0.01], [0.3, 2.04, ZE - 0.01], [-0.3, 2.04, ZE - 0.01]], BUS.sign, { lw: 2 });
  // ceiling, floor
  quad(g, c, [[-X, Y, zn], [X, Y, zn], [X, Y, ZE], [-X, Y, ZE]], BUS.ceil, { lw: 0 });
  const zl0 = c.z + 1.6; quad(g, c, [[-0.32, Y - 0.01, zl0], [0.32, Y - 0.01, zl0], [0.32, Y - 0.01, ZE], [-0.32, Y - 0.01, ZE]], lights ? '#55585f' : '#303237', { ink: '#1a1b1f', lw: 2 });
  for (let z = z0; z < ZE; z += dz * 1.5) { const a = P(c, -X, Y, z), b = P(c, X, Y, z); g.strokeStyle = '#1b1c20'; g.lineWidth = 2; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
  quad(g, c, [[-X, 0, zn], [X, 0, zn], [X, 0, ZE], [-X, 0, ZE]], BUS.floor, { lw: 0 });
  quad(g, c, [[-0.36, 0.001, zn], [0.36, 0.001, zn], [0.36, 0.001, ZE], [-0.36, 0.001, ZE]], BUS.aisle, { ink: '#232428', lw: 2 });
  // side walls with windows
  for (const sx of [-1, 1]) {
    const x = sx * X;
    quad(g, c, [[x, Y, zn], [x, Y, ZE], [x, 0, ZE], [x, 0, zn]], BUS.wall, { lw: 0 });
    for (let z = zn; z < ZE - 0.3; z += 1.45) {
      const z2 = Math.min(ZE - 0.2, z + 1.3), pts = [[x, 1.92, z], [x, 1.92, z2], [x, 0.98, z2], [x, 0.98, z]].map(p => P(c, ...p));
      g.save(); poly(g, pts, null, { ink: null }); g.clip();
      const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
      nightView(g, Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys), (Math.min(...ys) + Math.max(...ys)) / 2 + 30, t, 25 * -sx, 3 + z * 7);
      g.restore(); poly(g, pts, null, { ink: '#8e939b', lw: Math.max(2, P(c, x, 1.9, z)[2] * 0.03) }); poly(g, pts, null, { lw: 2 });
    }
    // luggage rack
    quad(g, c, [[x, 2.02, zn], [x, 2.02, ZE], [sx * 0.95, 2.0, ZE], [sx * 0.95, 2.0, zn]], '#1f2125', { lw: 2 });
    quad(g, c, [[sx * 0.95, 2.0, zn], [sx * 0.95, 2.0, ZE], [sx * 0.95, 1.94, ZE], [sx * 0.95, 1.94, zn]], '#45484f', { lw: 2 });
  }
  // rows of seats far -> near, people slotted by depth
  const items = [];
  for (let i = 0; i < rows; i++) { const zb = z0 + i * dz; if (zb - 0.42 < c.z + 0.3) continue; items.push({ z: zb, f: () => { for (const xc of [-1.0, -0.56, 0.56, 1.0]) if (!skip(i, xc)) seat(g, c, xc, zb); } }); }
  for (const s of sil) items.push({ z: s.z, f: () => silhouette(g, c, s.x, s.z) });
  for (const p of people) items.push({ z: p.z, f: () => p.draw(g) });
  for (const zp of [2.6, 6.2, 9.8]) for (const xp of [-0.42, 0.42]) if (zp > c.z + 0.4) items.push({ z: zp - 0.01, f: () => pole(g, c, xp, zp) });
  items.sort((a, b) => b.z - a.z).forEach(it => it.f());
  // ceiling hand rails
  if (0) for (const xp of [-0.42, 0.42]) { const a = P(c, xp, 2.1, c.z + 1.6), b = P(c, xp, 2.1, ZE); g.strokeStyle = BUS.pole; g.lineWidth = Math.max(3, a[2] * 0.03); g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
}
