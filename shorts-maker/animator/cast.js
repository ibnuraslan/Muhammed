// cast.js - flat 2D cartoon characters living in the 3D world.
// Each character is a canvas redrawn every frame (so they can walk, talk,
// blink, get angry...) on a plane that always turns to face the camera.
import { THREE, rng, lerp, clamp, roundRect } from './engine.js';

const CW = 512, CH = 1024;          // canvas size; feet at y=1000
const INK = '#151515';

// --- the cast (original designs) -------------------------------------------
export const DESIGNS = {
  // young designer: round glasses, messy hair, pencil behind the ear, mustard vest
  hero: { body: 'vest', color: '#e8a630', shirt: '#d9ecfb', bodyW: 150, headR: 148, hair: 'tuft', hairColor: '#6b3f1f',
          glasses: 'round', pencil: true, eyes: 'half', mouth: 'smile' },
  // boss: bald comb-over, huge moustache, navy suit, red tie
  boss: { body: 'suit', color: '#27345a', shirt: '#ffffff', tie: '#d4352b', bodyW: 250, headR: 156, bald: true,
          mustache: 'walrus', brows: 'bushy', eyes: 'dot', mouth: 'flat' },
  // rival: slick hair, square sunglasses, maroon suit, pencil moustache
  rival: { body: 'suit', color: '#7b1e2e', shirt: '#f4e9d8', tie: '#e0b33a', bodyW: 140, headR: 140, hair: 'slick', hairColor: '#1b1b1b',
           glasses: 'shades', mustache: 'pencil', eyes: 'dot', mouth: 'smirk' },
};
const EXTRA_COLORS = ['#3f8f6b', '#c4533a', '#5b6fc2', '#b0568f', '#d18b2c', '#4f9bb3', '#8a6f4e', '#6d4fa3', '#2f7d4f'];
const HATS = ['pilot', 'beret', 'bun', 'hair', 'hair', 'cap', 'bun', 'none'];
export function extraDesign(seed, o = {}) {
  const R = rng(seed + 11);
  const pick = a => a[Math.floor(R() * a.length)];
  return { body: R() < .5 ? 'suit' : 'plain', color: o.color || pick(EXTRA_COLORS), shirt: '#f6f1e6', tie: pick(['#d4352b', '#2b4fd4', '#e0b33a']),
           bodyW: 130 + R() * 70, headR: 135 + R() * 20, hat: o.hat || pick(HATS), hairColor: pick(['#2a1a10', '#6b3f1f', '#c9a25a', '#1b1b1b', '#8b8b8b']),
           eyes: pick(['dot', 'dot', 'half']), mouth: pick(['smile', 'flat', 'smile']), glasses: R() < .2 ? 'round' : null };
}

export class Char {
  constructor(stage, design, o = {}) {
    this.d = typeof design === 'string' ? (DESIGNS[design] || extraDesign(o.seed || 1, o)) : design;
    this.seed = o.seed || 1;
    this.h = o.h || 2;
    this.canvas = document.createElement('canvas'); this.canvas.width = CW; this.canvas.height = CH;
    this.g = this.canvas.getContext('2d');
    this.tex = new THREE.CanvasTexture(this.canvas); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 8;
    const geo = new THREE.PlaneGeometry(this.h / 2, this.h); geo.translate(0, this.h / 2, 0);
    this.mat = new THREE.MeshBasicMaterial({ map: this.tex, transparent: true, alphaTest: 0.05, toneMapped: false, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(geo, this.mat);
    this.group = new THREE.Group(); this.group.add(this.mesh);
    if (o.shadow !== false) {
      const sh = new THREE.Mesh(new THREE.CircleGeometry(this.h * 0.2, 24),
        new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.28, depthWrite: false }));
      sh.rotation.x = -Math.PI / 2; sh.position.y = 0.02; sh.scale.y = 0.55; this.group.add(sh); this.blob = sh;
    }
    if (o.pos) this.group.position.set(...o.pos);
    this.p = { walk: 0, walking: 0, armL: 0.18, armR: 0.18, eyes: this.d.eyes, mouth: this.d.mouth, brow: 0, anger: 0,
               talk: 0, facing: 1, hold: null, lean: 0, steam: 0, sweat: 0, hop: 0, sit: false, blink: true, look: 0.25,
               squash: 0, armsCrossed: false, ...(o.pose || {}) };
    stage.add(this.group); stage.chars.push(this);
    this._key = '';
  }
  set(p) { Object.assign(this.p, p); return this; }
  pos(x, y, z) { this.group.position.set(x, y, z); return this; }

  update(cam, t) {
    // turn to face the camera (around the vertical axis only)
    const wp = this.group.position;
    this.mesh.rotation.y = Math.atan2(cam.position.x - wp.x, cam.position.z - wp.z) - (this.group.rotation.y || 0);
    const p = this.p;
    const blinkOn = p.blink && ((t + this.seed * 0.73) % 3.1) < 0.11;
    const talkOpen = p.talk ? (0.5 + 0.5 * Math.sin(t * 23 + this.seed)) * p.talk : 0;
    const key = JSON.stringify(p) + blinkOn + talkOpen.toFixed(2) + (p.steam ? t.toFixed(2) : '') + (p.walking ? p.walk.toFixed(2) : '');
    if (key === this._key) return;
    this._key = key;
    this.draw(t, blinkOn, talkOpen);
    this.tex.needsUpdate = true;
  }

  draw(t, blinkOn, talkOpen) {
    const g = this.g, d = this.d, p = this.p;
    g.clearRect(0, 0, CW, CH);
    g.save();
    if (p.facing < 0) { g.translate(CW, 0); g.scale(-1, 1); }
    const cx = 256;
    const hop = p.hop * 60;
    const bob = p.walking ? Math.abs(Math.sin(p.walk)) * 14 * p.walking : 0;
    g.translate(0, -hop - bob);
    g.lineCap = 'round'; g.lineJoin = 'round';

    const bodyTop = 395, bodyBot = 700, bw = d.bodyW;
    // ---- legs
    if (!p.sit) {
      for (const side of [-1, 1]) {
        const ph = p.walk + (side > 0 ? Math.PI : 0);
        const swing = Math.sin(ph) * 70 * p.walking;
        const lift = Math.max(0, Math.cos(ph)) * 34 * p.walking;
        const hx = cx + side * 34, hy = bodyBot - 20;
        const fx = cx + side * 40 + swing, fy = 995 - lift + bob + hop;
        g.strokeStyle = INK; g.lineWidth = 15;
        g.beginPath(); g.moveTo(hx, hy); g.quadraticCurveTo(lerp(hx, fx, .5) + 18, (hy + fy) / 2, fx, fy); g.stroke();
        g.fillStyle = INK; g.beginPath(); g.ellipse(fx + 14, fy, 30, 14, 0, 0, 7); g.fill();
      }
    }
    // ---- body
    const lean = p.lean * 30;
    g.save(); g.translate(lean, 0);
    g.fillStyle = d.color; g.strokeStyle = INK; g.lineWidth = 7;
    const r = d.body === 'suit' && bw > 200 ? 110 : 62;
    roundRect(g, cx - bw / 2, bodyTop, bw, bodyBot - bodyTop, r); g.fill(); g.stroke();
    if (d.body === 'vest') {
      // shirt collar + V
      g.fillStyle = d.shirt; g.beginPath(); g.moveTo(cx - 38, bodyTop + 4); g.lineTo(cx, bodyTop + 90); g.lineTo(cx + 38, bodyTop + 4); g.closePath(); g.fill(); g.stroke();
      g.fillStyle = INK; for (let i = 0; i < 3; i++) { g.beginPath(); g.arc(cx, bodyTop + 125 + i * 50, 7, 0, 7); g.fill(); }
      // shirt sleeves at shoulders
      g.fillStyle = d.shirt;
      for (const s of [-1, 1]) { g.beginPath(); g.ellipse(cx + s * (bw / 2 - 6), bodyTop + 46, 28, 40, 0, 0, 7); g.fill(); g.stroke(); }
    } else if (d.body === 'suit') {
      g.fillStyle = d.shirt; g.beginPath(); g.moveTo(cx - 34, bodyTop + 2); g.lineTo(cx, bodyTop + 120); g.lineTo(cx + 34, bodyTop + 2); g.closePath(); g.fill();
      g.fillStyle = d.tie; g.beginPath(); g.moveTo(cx - 11, bodyTop + 14); g.lineTo(cx + 11, bodyTop + 14); g.lineTo(cx + 16, bodyTop + 100); g.lineTo(cx, bodyTop + 122); g.lineTo(cx - 16, bodyTop + 100); g.closePath(); g.fill(); g.lineWidth = 4; g.stroke();
      g.lineWidth = 6; g.beginPath(); g.moveTo(cx - 34, bodyTop + 2); g.lineTo(cx - 6, bodyTop + 140); g.moveTo(cx + 34, bodyTop + 2); g.lineTo(cx + 6, bodyTop + 140); g.stroke();
      g.fillStyle = INK; g.beginPath(); g.arc(cx, bodyTop + 180, 7, 0, 7); g.arc(cx, bodyTop + 225, 7, 0, 7); g.fill();
    } else {
      g.fillStyle = d.shirt; g.beginPath(); g.moveTo(cx - 30, bodyTop + 3); g.lineTo(cx, bodyTop + 50); g.lineTo(cx + 30, bodyTop + 3); g.closePath(); g.fill(); g.lineWidth = 5; g.stroke();
    }
    // ---- arms
    const shoulderY = bodyTop + 50;
    const hands = {};
    if (p.armsCrossed) {
      g.strokeStyle = INK; g.lineWidth = 14;
      g.beginPath(); g.moveTo(cx - bw / 2 + 6, shoulderY); g.quadraticCurveTo(cx - 40, bodyTop + 190, cx + 55, bodyTop + 150); g.stroke();
      g.beginPath(); g.moveTo(cx + bw / 2 - 6, shoulderY); g.quadraticCurveTo(cx + 40, bodyTop + 200, cx - 55, bodyTop + 160); g.stroke();
    } else {
      for (const side of [-1, 1]) {
        const a = side < 0 ? p.armL : p.armR;
        const sx = cx + side * (bw / 2 - 6), sy = shoulderY;
        const L = 205;
        const hx = sx + side * Math.sin(a) * L, hy = sy + Math.cos(a) * L;
        const ex = (sx + hx) / 2 + side * 22 * Math.cos(a), ey = (sy + hy) / 2 - 10 * Math.sin(a);
        g.strokeStyle = INK; g.lineWidth = 14;
        g.beginPath(); g.moveTo(sx, sy); g.quadraticCurveTo(ex, ey, hx, hy); g.stroke();
        g.fillStyle = INK; g.beginPath(); g.arc(hx, hy, 17, 0, 7); g.fill();
        hands[side] = [hx, hy, a];
      }
      if (p.hold) drawItem(g, p.hold, ...hands[1], t);
      if (p.holdL) drawItem(g, p.holdL, ...hands[-1], t);
    }
    g.restore();

    // ---- head
    const hr = d.headR, hx = cx + lean * 1.3, hy = 245;
    const sq = 1 + p.squash;
    g.save(); g.translate(hx, hy); g.scale(1 / sq, sq);
    const skin = mixColor('#ffffff', p.anger > 0.6 ? '#9a3fb8' : '#e2483c', p.anger > 0.6 ? (p.anger - 0.6) / 0.4 : p.anger / 0.6 * 0.85, p.anger > 0.6 ? '#e2483c' : null);
    g.fillStyle = skin; g.strokeStyle = INK; g.lineWidth = 8;
    g.beginPath(); g.arc(0, 0, hr, 0, Math.PI * 2); g.fill(); g.stroke();
    if (d.bald) {
      g.fillStyle = 'rgba(255,255,255,0.55)'; g.beginPath(); g.ellipse(-50, -90, 40, 18, -0.5, 0, 7); g.fill();
      g.strokeStyle = '#3a3a3a'; g.lineWidth = 5;
      for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(-90, -95 + i * 14); g.quadraticCurveTo(0, -150 + i * 14, 95, -92 + i * 14); g.stroke(); }
    }
    // face
    const fx = (p.look || 0) * 45, ey = -12, sep = 54;
    const eyes = blinkOn ? 'closed' : p.eyes;
    for (const s of [-1, 1]) drawEye(g, fx + s * sep, ey, eyes, skin);
    // brows
    const brow = p.brow + (d.brows === 'bushy' ? 0.0001 : 0);
    if (Math.abs(brow) > 0.05 || d.brows === 'bushy') {
      g.strokeStyle = d.brows === 'bushy' ? '#d9d9d9' : INK; g.lineWidth = d.brows === 'bushy' ? 20 : 9;
      for (const s of [-1, 1]) {
        const bx = fx + s * sep, by = ey - 48;
        const tilt = brow * 22;
        g.beginPath(); g.moveTo(bx - s * 30, by + tilt); g.lineTo(bx + s * 28, by - tilt); g.stroke();
        if (d.brows === 'bushy') { g.strokeStyle = INK; g.lineWidth = 4; g.beginPath(); g.moveTo(bx - s * 30, by + tilt - 10); g.lineTo(bx + s * 28, by - tilt - 10); g.stroke(); g.strokeStyle = '#d9d9d9'; g.lineWidth = 20; }
      }
    }
    if (d.glasses === 'round') {
      g.strokeStyle = INK; g.lineWidth = 7; g.fillStyle = 'rgba(160,210,255,0.25)';
      for (const s of [-1, 1]) { g.beginPath(); g.arc(fx + s * sep, ey, 38, 0, 7); g.fill(); g.stroke(); }
      g.beginPath(); g.moveTo(fx - sep + 38, ey); g.quadraticCurveTo(fx, ey - 12, fx + sep - 38, ey); g.stroke();
    } else if (d.glasses === 'shades') {
      g.fillStyle = INK;
      for (const s of [-1, 1]) { roundRect(g, fx + s * sep - 40, ey - 26, 80, 54, 10); g.fill(); }
      g.lineWidth = 8; g.strokeStyle = INK; g.beginPath(); g.moveTo(fx - 20, ey - 10); g.lineTo(fx + 20, ey - 10); g.stroke();
      g.strokeStyle = 'rgba(255,255,255,0.7)'; g.lineWidth = 6;
      for (const s of [-1, 1]) { g.beginPath(); g.moveTo(fx + s * sep - 25, ey + 15); g.lineTo(fx + s * sep - 5, ey - 15); g.stroke(); }
    }
    // mustache + mouth
    const my = 72;
    let mouth = p.mouth;
    if (talkOpen > 0.05) mouth = d.mustache === 'walrus' ? 'shout' : 'open';
    drawMouth(g, fx, my, mouth, Math.max(talkOpen, mouth === 'shout' || mouth === 'open' ? 0.7 : 0));
    if (d.mustache === 'walrus') {
      g.fillStyle = '#e8e8e8'; g.strokeStyle = INK; g.lineWidth = 5;
      for (const s of [-1, 1]) { g.beginPath(); g.ellipse(fx + s * 36, my - 22, 46, 24, s * 0.25, 0, 7); g.fill(); g.stroke(); }
    } else if (d.mustache === 'pencil') {
      g.strokeStyle = INK; g.lineWidth = 6; g.beginPath(); g.moveTo(fx - 38, my - 10); g.quadraticCurveTo(fx, my - 30, fx + 38, my - 10); g.stroke();
    }
    if (p.blush) { g.fillStyle = 'rgba(255,120,120,0.45)'; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(fx + s * 85, 40, 26, 14, 0, 0, 7); g.fill(); } }
    if (p.sweat) { g.fillStyle = '#8fd0ff'; g.strokeStyle = INK; g.lineWidth = 4; g.beginPath(); g.moveTo(hr * .62, -hr * .55); g.quadraticCurveTo(hr * .78, -hr * .3, hr * .66, -hr * .25); g.quadraticCurveTo(hr * .52, -hr * .3, hr * .62, -hr * .55); g.fill(); g.stroke(); }
    // hair / hats
    drawHair(g, d, hr);
    if (d.pencil) { g.save(); g.translate(hr * 0.86, -hr * 0.35); g.rotate(-0.9); g.fillStyle = '#f4c430'; g.strokeStyle = INK; g.lineWidth = 4; g.fillRect(-10, -60, 20, 110); g.strokeRect(-10, -60, 20, 110); g.fillStyle = '#f2b8a0'; g.beginPath(); g.moveTo(-10, 50); g.lineTo(10, 50); g.lineTo(0, 78); g.closePath(); g.fill(); g.stroke(); g.restore(); }
    g.restore();
    // steam puffs
    if (p.steam > 0) {
      for (let i = 0; i < 6; i++) {
        const k = ((t * 1.6 + i / 6) % 1), s = i % 2 ? 1 : -1;
        const px = hx + s * (hr * 0.75 + k * 60), py = hy - hr * 0.6 - k * 160;
        g.globalAlpha = p.steam * (1 - k); g.fillStyle = '#ffffff'; g.strokeStyle = '#9aa'; g.lineWidth = 4;
        g.beginPath(); g.arc(px, py, 22 + k * 30, 0, 7); g.fill(); g.stroke();
      }
      g.globalAlpha = 1;
    }
    g.restore();
  }
}

function mixColor(a, b, k, c) {
  const pa = hex(a), pb = hex(c || b);
  if (c) { const pc = hex(b); return rgbs(pb.map((v, i) => lerp(v, pc[i], clamp(k)))); }
  return rgbs(pa.map((v, i) => lerp(v, pb[i], clamp(k))));
}
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const rgbs = a => `rgb(${a.map(Math.round).join(',')})`;

function drawEye(g, x, y, type, skin) {
  g.fillStyle = INK; g.strokeStyle = INK; g.lineWidth = 8;
  switch (type) {
    case 'closed': g.beginPath(); g.moveTo(x - 18, y); g.lineTo(x + 18, y); g.stroke(); break;
    case 'happy': g.beginPath(); g.arc(x, y + 8, 18, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); break;
    case 'wide': g.fillStyle = '#fff'; g.lineWidth = 6; g.beginPath(); g.arc(x, y, 27, 0, 7); g.fill(); g.stroke(); g.fillStyle = INK; g.beginPath(); g.arc(x, y + 3, 10, 0, 7); g.fill(); break;
    case 'half':
      g.beginPath(); g.ellipse(x, y + 3, 13, 17, 0, 0, 7); g.fill();
      g.fillStyle = skin; g.fillRect(x - 20, y - 22, 40, 18);
      g.lineWidth = 7; g.beginPath(); g.moveTo(x - 19, y - 3); g.lineTo(x + 19, y - 5); g.stroke(); break;
    case 'angry':
      g.beginPath(); g.ellipse(x, y + 4, 12, 14, 0, 0, 7); g.fill(); break;
    default: g.beginPath(); g.ellipse(x, y, 13, 18, 0, 0, 7); g.fill();
  }
}
function drawMouth(g, x, y, type, open) {
  g.strokeStyle = INK; g.fillStyle = INK; g.lineWidth = 8;
  switch (type) {
    case 'flat': g.beginPath(); g.moveTo(x - 24, y); g.lineTo(x + 24, y); g.stroke(); break;
    case 'frown': g.beginPath(); g.arc(x, y + 26, 26, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); break;
    case 'smirk': g.beginPath(); g.moveTo(x - 26, y + 4); g.quadraticCurveTo(x + 6, y + 12, x + 32, y - 12); g.stroke(); break;
    case 'grin':
      g.fillStyle = '#fff'; g.lineWidth = 6; g.beginPath(); g.moveTo(x - 46, y - 10); g.quadraticCurveTo(x, y + 60, x + 46, y - 10); g.closePath(); g.fill(); g.stroke();
      g.lineWidth = 3; g.beginPath(); g.moveTo(x - 40, y + 4); g.lineTo(x + 40, y + 4); g.stroke(); break;
    case 'o': g.lineWidth = 6; g.beginPath(); g.ellipse(x, y + 4, 12, 16, 0, 0, 7); g.fill(); break;
    case 'open': case 'shout': {
      const hgt = 14 + open * (type === 'shout' ? 62 : 40), wd = type === 'shout' ? 52 : 30;
      g.beginPath(); g.ellipse(x, y + hgt / 3, wd, hgt, 0, 0, 7); g.fill();
      g.fillStyle = '#e0605a'; g.beginPath(); g.ellipse(x, y + hgt / 3 + hgt * 0.55, wd * 0.6, hgt * 0.35, 0, 0, 7); g.fill();
      if (type === 'shout') { g.fillStyle = '#fff'; g.fillRect(x - wd * .7, y + hgt / 3 - hgt * .85, wd * 1.4, hgt * .3); }
      break; }
    default: g.beginPath(); g.arc(x, y - 14, 30, Math.PI * 0.2, Math.PI * 0.8); g.stroke();
  }
}
function drawHair(g, d, r) {
  g.strokeStyle = INK; g.lineWidth = 7;
  const hat = d.hat, hc = d.hairColor;
  if (d.hair === 'tuft') {
    g.fillStyle = hc; g.beginPath();
    g.arc(0, 0, r, Math.PI * 1.08, Math.PI * 1.92);
    const pts = [[0.92, -0.38], [0.6, -0.7], [0.55, -1.02], [0.2, -0.82], [0.05, -1.12], [-0.22, -0.84], [-0.45, -1.05], [-0.55, -0.72], [-0.92, -0.4]];
    pts.forEach(([a, b]) => g.lineTo(a * r, b * r));
    g.closePath(); g.fill(); g.stroke();
  } else if (d.hair === 'slick' || hat === 'hair') {
    g.fillStyle = hc; g.beginPath(); g.arc(0, 0, r, Math.PI * 1.02, Math.PI * 1.98);
    g.quadraticCurveTo(r * 0.5, -r * 0.62, -r * 0.1, -r * 0.55); g.quadraticCurveTo(-r * 0.6, -r * 0.5, -r, -r * 0.05); g.closePath(); g.fill(); g.stroke();
    if (d.hair === 'slick') { g.strokeStyle = 'rgba(255,255,255,0.55)'; g.lineWidth = 8; g.beginPath(); g.arc(0, -r * 0.1, r * 0.75, Math.PI * 1.3, Math.PI * 1.6); g.stroke(); }
  }
  if (hat === 'pilot') {
    g.fillStyle = '#1f2d55'; g.beginPath(); g.ellipse(0, -r * 0.82, r * 1.0, r * 0.38, 0, Math.PI, 0); g.lineTo(r * 0.85, -r * 0.62); g.lineTo(-r * 0.85, -r * 0.62); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = INK; g.beginPath(); g.ellipse(0, -r * 0.6, r * 0.95, r * 0.12, 0, 0, 7); g.fill();
    g.fillStyle = '#f2c230'; g.beginPath(); g.arc(0, -r * 0.88, 16, 0, 7); g.fill();
  } else if (hat === 'beret') {
    g.fillStyle = '#c8302e'; g.beginPath(); g.ellipse(r * 0.1, -r * 0.8, r * 0.95, r * 0.36, -0.15, 0, 7); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(r * 0.1, -r * 1.14); g.lineTo(r * 0.12, -r * 1.3); g.stroke();
  } else if (hat === 'bun') {
    g.fillStyle = hc; g.beginPath(); g.arc(0, -r * 1.05, r * 0.33, 0, 7); g.fill(); g.stroke();
    g.beginPath(); g.arc(0, 0, r, Math.PI * 1.0, Math.PI * 2.0); g.quadraticCurveTo(0, -r * 0.45, -r, 0); g.fill(); g.stroke();
  } else if (hat === 'cap') {
    g.fillStyle = '#2f6fb3'; g.beginPath(); g.arc(0, -r * 0.35, r * 0.92, Math.PI * 1.05, Math.PI * 1.95); g.closePath(); g.fill(); g.stroke();
    g.beginPath(); g.ellipse(r * 0.55, -r * 0.4, r * 0.55, r * 0.12, 0, 0, 7); g.fill(); g.stroke();
  } else if (hat === 'hardhat') {
    g.fillStyle = '#f5c518'; g.beginPath(); g.arc(0, -r * 0.42, r * 0.9, Math.PI, 0); g.closePath(); g.fill(); g.stroke();
    g.beginPath(); g.ellipse(0, -r * 0.42, r * 1.1, r * 0.12, 0, 0, 7); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(0, -r * 1.3); g.lineTo(0, -r * 0.45); g.stroke();
  }
}
function drawItem(g, item, x, y, a, t) {
  g.save(); g.translate(x, y); g.strokeStyle = INK; g.lineWidth = 6;
  switch (item) {
    case 'pencil': g.rotate(-0.6); g.fillStyle = '#f4c430'; g.fillRect(-8, -90, 16, 100); g.strokeRect(-8, -90, 16, 100); break;
    case 'hammer': g.rotate(a > 1.5 ? Math.PI - a : -0.3); g.fillStyle = '#9b6a3c'; g.fillRect(-8, -130, 16, 150); g.strokeRect(-8, -130, 16, 150); g.fillStyle = '#7c8794'; g.fillRect(-45, -160, 90, 40); g.strokeRect(-45, -160, 90, 40); break;
    case 'suitcase': g.fillStyle = '#8a5a2b'; roundRect(g, -60, 10, 120, 90, 12); g.fill(); g.stroke(); g.beginPath(); g.moveTo(-20, 12); g.lineTo(-20, -4); g.lineTo(20, -4); g.lineTo(20, 12); g.stroke(); break;
    case 'window': g.fillStyle = '#cfd6de'; g.beginPath(); g.arc(0, -70, 70, 0, 7); g.fill(); g.stroke(); g.fillStyle = '#5aa8e8'; g.beginPath(); g.arc(0, -70, 48, 0, 7); g.fill(); g.stroke(); g.fillStyle = 'rgba(255,255,255,.7)'; g.beginPath(); g.ellipse(-15, -85, 14, 7, -0.6, 0, 7); g.fill(); break;
    case 'blueprint': g.rotate(-0.1); g.fillStyle = '#2b5ea8'; g.fillRect(-90, -150, 180, 130); g.strokeRect(-90, -150, 180, 130); g.strokeStyle = '#e6f0ff'; g.lineWidth = 3; g.beginPath(); g.ellipse(0, -85, 70, 18, 0, 0, 7); g.stroke(); for (let i = 0; i < 5; i++) { g.beginPath(); g.arc(-48 + i * 24, -88, 6, 0, 7); g.stroke(); } break;
    case 'newspaper': g.fillStyle = '#efe9da'; g.fillRect(-80, -140, 160, 130); g.strokeRect(-80, -140, 160, 130); g.fillStyle = '#333'; for (let i = 0; i < 6; i++) g.fillRect(-65, -125 + i * 20, 130, 7); break;
    case 'ticket': g.fillStyle = '#ffe48a'; g.fillRect(-40, -60, 80, 50); g.strokeRect(-40, -60, 80, 50); break;
  }
  g.restore();
}
