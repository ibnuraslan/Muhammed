// flat/scenes.js - backgrounds for the true-crime flat episodes: night road + bus exterior, city skyline,
// bus side window, interrogation room, evidence table.
import { P, poly, INK } from './flat.js';
import { rng } from '../engine.js';

export function nightSky(g, W, H, y1, t = 0) {
  const gr = g.createLinearGradient(0, 0, 0, y1); gr.addColorStop(0, '#06091a'); gr.addColorStop(1, '#13204a'); g.fillStyle = gr; g.fillRect(0, 0, W, y1);
  g.fillStyle = '#2c4fa0';
  for (const [x, y, w] of [[60, 140, 380], [600, 230, 300], [200, 330, 160]]) {
    const xx = x + t * 6; g.beginPath(); g.ellipse(xx, y, w / 2, 26, 0, 0, 7); g.ellipse(xx + w * 0.25, y - 14, w * 0.3, 22, 0, 0, 7); g.fill();
  }
}

// a box with yaw, drawn face by face back-to-front. faces: fn(i, pts2d) returns fill
function box3(g, c, cx, cz, yaw, L, Wd, Hh, y0, fills, lw = 3) {
  const ca = Math.cos(yaw), sa = Math.sin(yaw);
  const at = (u, v, y) => [cx + u * ca - v * sa, y, cz + u * sa + v * ca];       // u along length, v across
  const C = [[-L / 2, -Wd / 2], [L / 2, -Wd / 2], [L / 2, Wd / 2], [-L / 2, Wd / 2]];
  const faces = [
    { k: 'side1', q: [at(-L / 2, -Wd / 2, y0 + Hh), at(L / 2, -Wd / 2, y0 + Hh), at(L / 2, -Wd / 2, y0), at(-L / 2, -Wd / 2, y0)] },
    { k: 'side2', q: [at(-L / 2, Wd / 2, y0 + Hh), at(L / 2, Wd / 2, y0 + Hh), at(L / 2, Wd / 2, y0), at(-L / 2, Wd / 2, y0)] },
    { k: 'front', q: [at(L / 2, -Wd / 2, y0 + Hh), at(L / 2, Wd / 2, y0 + Hh), at(L / 2, Wd / 2, y0), at(L / 2, -Wd / 2, y0)] },
    { k: 'back', q: [at(-L / 2, -Wd / 2, y0 + Hh), at(-L / 2, Wd / 2, y0 + Hh), at(-L / 2, Wd / 2, y0), at(-L / 2, -Wd / 2, y0)] },
    { k: 'roof', q: C.map(([u, v]) => at(u, v, y0 + Hh)) },
  ];
  for (const f of faces) f.d = f.q.reduce((s, p) => s + Math.hypot(p[0] - c.x, p[1] - c.y, p[2] - c.z), 0) / 4;
  faces.sort((a, b) => b.d - a.d);
  for (const f of faces) { const pts = f.q.map(p => P(c, ...p)); const fill = fills[f.k]; if (fill === null) continue; poly(g, pts, typeof fill === 'function' ? null : fill, { lw }); if (typeof fill === 'function') fill(pts); }
  return at;
}
const lerpP = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
const quadAt = (pts, u0, u1, v0, v1) => {   // sub-rectangle of a projected quad (u along top edge, v down)
  const top0 = lerpP(pts[0], pts[1], u0), top1 = lerpP(pts[0], pts[1], u1), bot0 = lerpP(pts[3], pts[2], u0), bot1 = lerpP(pts[3], pts[2], u1);
  return [lerpP(top0, bot0, v0), lerpP(top1, bot1, v0), lerpP(top1, bot1, v1), lerpP(top0, bot0, v1)];
};

// the blue coach seen from above at an angle, stopped on the shoulder at night, street lamps
export function busExterior(g, W, H, c, t, { lit = 1 } = {}) {
  nightSky(g, W, H, H * 0.42, t);
  // ground
  const hz = P(c, 0, 0, 400)[1];
  g.fillStyle = '#2c2b20'; g.fillRect(0, hz, W, H - hz);
  poly(g, [P(c, 6, 0, 5), P(c, 30, 0, 300), P(c, 70, 0, 300), P(c, 40, 0, 5)], '#26272b', { lw: 2 });
  for (let z = 8; z < 120; z += 7) { const a = P(c, 23 + z * 0.11, 0.01, z), b = P(c, 23.3 + (z + 3) * 0.11, 0.01, z + 3); g.strokeStyle = '#c9b14a'; g.lineWidth = Math.max(2, a[2] * 0.12); g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
  // lamps
  for (const [x, z] of [[2.5, 16], [6, 40], [9.5, 70]]) {
    const top = P(c, x, 7, z), base = P(c, x, 0, z), s = top[2];
    const cone = g.createLinearGradient(0, top[1], 0, base[1]); cone.addColorStop(0, `rgba(255,236,170,${0.55 * lit})`); cone.addColorStop(1, 'rgba(255,236,170,0.05)');
    g.fillStyle = cone; g.beginPath(); g.moveTo(top[0] - 0.3 * s, top[1]); g.lineTo(top[0] + 0.3 * s, top[1]); g.lineTo(base[0] + 2.4 * s, base[1]); g.lineTo(base[0] - 2.4 * s, base[1]); g.closePath(); g.fill();
    g.fillStyle = '#9aa0a8'; g.fillRect(base[0] - 0.1 * s, top[1], 0.2 * s, base[1] - top[1]); g.strokeStyle = INK; g.lineWidth = 2; g.strokeRect(base[0] - 0.1 * s, top[1], 0.2 * s, base[1] - top[1]);
    poly(g, [[top[0] - 0.5 * s, top[1]], [top[0] + 0.5 * s, top[1]], [top[0] + 0.3 * s, top[1] - 0.3 * s], [top[0] - 0.3 * s, top[1] - 0.3 * s]], '#f0e2a8', { lw: 2 });
  }
  // the coach
  const blue = '#2d62b4';
  box3(g, c, 2.2, 22, -1.18, 13, 2.6, 3.3, 0.45, {
    roof: '#c8ccd2', back: '#264f92', side2: null,
    side1: (pts) => {      // long side facing us: windows band, skirt, wheels
      poly(g, pts, blue, { lw: 3 });
      poly(g, quadAt(pts, 0.02, 0.98, 0.12, 0.5), '#9fb6c9', { lw: 3 });
      for (let i = 1; i < 7; i++) { const q = quadAt(pts, i / 7, i / 7 + 0.006, 0.12, 0.5); poly(g, q, '#3a4452', { lw: 0 }); }
      poly(g, quadAt(pts, 0.02, 0.98, 0.56, 0.62), '#e8eaee', { lw: 2 });
      for (const u of [0.2, 0.8]) { const q = quadAt(pts, u - 0.06, u + 0.06, 0.78, 1.08); const cxw = (q[0][0] + q[2][0]) / 2, cyw = (q[0][1] + q[2][1]) / 2, rw = Math.abs(q[1][0] - q[0][0]) / 2;
        g.fillStyle = '#121214'; g.beginPath(); g.ellipse(cxw, cyw, rw * 0.9, rw * 0.75, 0, 0, 7); g.fill(); g.strokeStyle = INK; g.lineWidth = 3; g.stroke(); g.fillStyle = '#8c9096'; g.beginPath(); g.ellipse(cxw, cyw, rw * 0.4, rw * 0.32, 0, 0, 7); g.fill(); }
    },
    front: (pts) => { poly(g, pts, '#2a5aa6', { lw: 3 }); poly(g, quadAt(pts, 0.06, 0.94, 0.08, 0.55), '#a9c0d2', { lw: 3 });
      for (const u of [0.12, 0.88]) { const q = quadAt(pts, u - 0.06, u + 0.06, 0.74, 0.82); poly(g, q, `rgba(255,248,210,${0.7 + 0.3 * lit})`, { lw: 2 }); } },
  });
}

// lit city blocks behind people outside the bus
export function city(g, x0, y0, x1, y1, seed = 3) {
  const R = rng(seed);
  for (let x = x0 - 20; x < x1; x += 110 + R() * 60) {
    const w = 90 + R() * 70, h = (y1 - y0) * (0.35 + R() * 0.65), top = y1 - h;
    g.fillStyle = R() > 0.5 ? '#141722' : '#181c28'; g.fillRect(x, top, w, h);
    for (let wy = top + 20; wy < y1 - 20; wy += 34) for (let wx = x + 12; wx < x + w - 14; wx += 26) if (R() > 0.72) { g.fillStyle = R() > 0.3 ? '#e2b84a' : '#c99a35'; g.fillRect(wx, wy, 12, 16); }
  }
}

// interrogation room: olive walls, one hanging lamp light cone, a brown table at the bottom
export function interrogation(g, W, H, tableY, t = 0) {
  g.fillStyle = '#5b5a3a'; g.fillRect(0, 0, W, H);
  const gr = g.createRadialGradient(W * 0.55, tableY, 50, W * 0.55, tableY, W * 0.9); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.55)'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
}
export function lightCone(g, W, H, x, tableY, w = 520, k = 1) {
  const cone = g.createLinearGradient(0, 0, 0, tableY); cone.addColorStop(0, `rgba(255,224,140,${0.08 * k})`); cone.addColorStop(1, `rgba(255,224,140,${0.32 * k})`);
  g.fillStyle = cone; g.beginPath(); g.moveTo(x - 40, -10); g.lineTo(x + 40, -10); g.lineTo(x + w / 2, tableY + 40); g.lineTo(x - w / 2, tableY + 40); g.closePath(); g.fill();
}
export function table(g, W, H, y) {
  g.fillStyle = '#6a3f22'; g.fillRect(0, y, W, H - y); g.fillStyle = '#7d4c2a'; g.fillRect(0, y, W, 40); g.strokeStyle = INK; g.lineWidth = 4; g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke();
}
// sealed evidence bag with a label; contents() draws what's inside (in bag coordinates 0..w, 0..h)
export function evidenceBag(g, x, y, w, h, rot, label, contents) {
  g.save(); g.translate(x, y); g.rotate(rot);
  g.fillStyle = 'rgba(225,228,224,0.9)'; g.beginPath(); g.rect(0, 0, w, h); g.fill(); g.strokeStyle = INK; g.lineWidth = 3; g.stroke();
  g.fillStyle = '#c62a2a'; g.fillRect(0, 0, w, h * 0.12); g.fillStyle = '#fff'; g.font = `900 ${Math.round(h * 0.08)}px sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('EVIDENCE', w / 2, h * 0.06);
  g.save(); g.beginPath(); g.rect(6, h * 0.14, w - 12, h * 0.62); g.clip(); contents && contents(g, w, h); g.restore();
  g.fillStyle = 'rgba(255,255,255,0.28)'; g.fillRect(w * 0.1, h * 0.16, w * 0.12, h * 0.55);     // plastic shine
  g.fillStyle = '#f2ecd8'; g.fillRect(w * 0.08, h * 0.8, w * 0.84, h * 0.15); g.strokeRect(w * 0.08, h * 0.8, w * 0.84, h * 0.15);
  g.fillStyle = '#222'; g.font = `700 ${Math.round(h * 0.06)}px sans-serif`; g.fillText(label, w / 2, h * 0.875);
  g.restore();
}
