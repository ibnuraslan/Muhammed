// people.js - "illustrated" people: realistic proportions (~7.5 heads), detailed faces, ink outlines,
// two-segment limbs with real joints, front / three-quarter / back views. Drawn on a canvas that
// always faces the camera (same billboard idea as cast.js, different art style).
import { THREE, lerp, clamp, rng } from './engine.js';

const CW = 640, CH = 1280;              // canvas; feet at y≈1255
const INK = '#1c1a1a', LINE = 4.5;

export const SKIN = { light: '#f1d3bd', fair: '#e9c1a3', tan: '#d4a07c', brown: '#a9714b', dark: '#6e4630' };

// ---------------------------------------------------------------- default look (override any field)
const BASE = {
  skin: SKIN.fair, hair: 'short', hairColor: '#3a2a1e', hat: null, hatColor: '#1d2433',
  top: 'tshirt', topColor: '#7d8a99', top2: '#d9d9d9', pants: '#2f3542', shoes: '#1d1d1f',
  eyes: '#5a3e2b', build: 1.0, height: 1.0, age: 0, stubble: false, glasses: false, beard: null,
  badge: false, headphones: false,
};
export const PEOPLE = {
  // the Investigator, illustrated version (same signature: fedora, round glasses, pencil, mustard vest, trench coat)
  investigator: { skin: SKIN.fair, hair: 'side', hairColor: '#6b3f1f', hat: 'fedora', hatColor: '#4a3a2c', top: 'trench', topColor: '#b89a6a', top2: '#e8a630',
                  pants: '#5a4a3a', glasses: true, pencil: true },
};

export class Person {
  constructor(stage, look = {}, o = {}) {
    this.d = { ...BASE, ...(typeof look === 'string' ? PEOPLE[look] : look) };
    this.seed = o.seed || 1;
    this.h = (o.h || 1.9) * this.d.height;
    this.canvas = document.createElement('canvas'); this.canvas.width = CW; this.canvas.height = CH;
    this.g = this.canvas.getContext('2d');
    this.tex = new THREE.CanvasTexture(this.canvas); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 8;
    const geo = new THREE.PlaneGeometry(this.h / 2, this.h); geo.translate(0, this.h / 2, 0);
    this.mat = new THREE.MeshBasicMaterial({ map: this.tex, transparent: true, alphaTest: 0.05, toneMapped: false, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(geo, this.mat); this.mesh.userData.isPerson = true;
    this.group = new THREE.Group(); this.group.add(this.mesh);
    if (o.shadow !== false) {
      const sh = new THREE.Mesh(new THREE.CircleGeometry(this.h * 0.16, 24), new THREE.MeshBasicMaterial({ color: 0, transparent: true, opacity: 0.3, depthWrite: false }));
      sh.rotation.x = -Math.PI / 2; sh.position.y = 0.02; sh.scale.y = 0.5; this.group.add(sh);
    }
    if (o.pos) this.group.position.set(...o.pos);
    this.p = { view: 'front', turn: 0, expr: 'neutral', blink: true, talk: 0, look: 0, tilt: 0, lean: 0,
               armL: [0.12, -0.15], armR: [0.12, -0.15], legL: [0.04, 0], legR: [0.04, 0],
               walk: 0, walking: 0, run: 0, seat: 0, kneel: 0, hold: null, holdL: null, aimR: null, aimL: null,
               sweat: 0, tears: 0, shadowFace: 0, ...(o.pose || {}) };
    stage.add(this.group); (stage.chars || (stage.chars = [])).push(this);
    this._key = '';
  }
  set(p) { Object.assign(this.p, p); return this; }
  pos(x, y, z) { this.group.position.set(x, y, z); return this; }

  toCanvas(world, cam) {
    this.group.updateMatrixWorld();
    const o = new THREE.Vector3().setFromMatrixPosition(this.group.matrixWorld);
    const yaw = this.mesh.rotation.y + (this.group.rotation.y || 0);
    const n = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)), right = new THREE.Vector3(Math.cos(yaw), 0, -Math.sin(yaw));
    const c = cam.position, w = new THREE.Vector3(...world), dir = w.clone().sub(c);
    const den = dir.dot(n); const k = Math.abs(den) < 1e-6 ? 1 : o.clone().sub(c).dot(n) / den;
    const P = c.clone().add(dir.multiplyScalar(k)).sub(o);
    return [Math.round(CW / 2 + P.dot(right) / (this.h / 2) * CW), Math.round(CH - P.y / this.h * CH)];
  }
  update(cam, t) {
    const wp = this.group.position;
    this.mesh.rotation.y = Math.atan2(cam.position.x - wp.x, cam.position.z - wp.z) - (this.group.rotation.y || 0);
    const p = this.p;
    this._aim = { R: p.aimR ? this.toCanvas(p.aimR, cam) : null, L: p.aimL ? this.toCanvas(p.aimL, cam) : null };
    const blinkOn = p.blink && ((t + this.seed * 0.71) % 3.3) < 0.12;
    const talkOpen = p.talk ? (0.5 + 0.5 * Math.sin(t * 22 + this.seed)) * p.talk : 0;
    const key = JSON.stringify(p) + blinkOn + talkOpen.toFixed(2) + JSON.stringify(this._aim) + ((p.walking || p.run) ? t.toFixed(2) : '');
    if (key === this._key) return;
    this._key = key; this.draw(t, blinkOn, talkOpen); this.tex.needsUpdate = true;
  }

  // ------------------------------------------------------------------------------------------ drawing
  // draw straight into a 2D scene (flat episodes): x,y = feet position, s = pixels per canvas pixel
  drawInto(g, x, y, s, t) {
    const p = this.p;
    this._aim = { R: p.aimRc || null, L: p.aimLc || null };
    const blinkOn = p.blink && ((t + this.seed * 0.71) % 3.3) < 0.12;
    const talkOpen = p.talk ? (0.5 + 0.5 * Math.sin(t * 22 + this.seed)) * p.talk : 0;
    if (p.inShadow > 0) {     // the in-shadow tint must only touch the figure: draw it offscreen first
      if (!this._off) { this._off = document.createElement('canvas'); }
      const o = this._off; o.width = Math.ceil(CW * s); o.height = Math.ceil(CH * s);
      const og = o.getContext('2d'); og.setTransform(s, 0, 0, s, 0, 0); this.draw(t, blinkOn, talkOpen, og);
      g.drawImage(o, x - CW / 2 * s, y - 1255 * s);
    } else {
      g.save(); g.translate(x - CW / 2 * s, y - 1255 * s); g.scale(s, s); this.draw(t, blinkOn, talkOpen, g); g.restore();
    }
  }

  draw(t, blinkOn, talkOpen, target) {
    const g = target || this.g, d = this.d, p = this.p;
    if (!target) g.clearRect(0, 0, CW, CH);
    g.lineJoin = 'round'; g.lineCap = 'round';
    const B = d.build, cx = CW / 2;
    const turn = p.view === 'back' ? 0 : clamp(p.turn, -1, 1);              // -1 left .. 1 right (three-quarter)
    const back = p.view === 'back';
    // gait
    const gait = p.run ? 1 : p.walking;
    const ph = p.walk;
    const swing = Math.sin(ph) * (p.run ? 0.75 : 0.38) * gait;
    // vertical offsets
    const seat = clamp(p.seat), kneel = clamp(p.kneel);
    const drop = 205 * seat + 185 * kneel + (gait ? Math.abs(Math.cos(ph)) * -10 * gait : 0);
    const S = { // skeleton in canvas space (standing)
      headC: [cx + turn * 6, 122], neck: [cx, 236], shL: [cx - 86 * B, 268], shR: [cx + 86 * B, 268],
      hipL: [cx - 42 * B, 612], hipR: [cx + 42 * B, 612], waist: 560,
    };
    const ARM1 = 205, ARM2 = 192, LEG1 = 318, LEG2 = 300;
    const lean = p.lean * 40;

    // --- legs
    const legs = {};
    for (const side of [-1, 1]) {
      const hip = [ (side < 0 ? S.hipL : S.hipR)[0] + lean * 0.2, S.hipL[1] + drop ];
      let knee, foot;
      if (seat > 0.01 && kneel < 0.01) {
        // sitting: thighs come toward the camera (front) or forward (turned); shins drop to the floor
        const fwd = turn !== 0 ? Math.sign(turn) : 0;
        knee = [hip[0] + side * 14 + fwd * 230 * seat, hip[1] + lerp(LEG1, 110, seat) - (fwd ? 60 : 0) * seat];
        foot = [knee[0] + fwd * 30, Math.min(1238, knee[1] + LEG2)];
      } else if (kneel > 0.01) {
        const f = turn >= 0 ? 1 : -1;
        if (side === f || (turn === 0 && side > 0)) { knee = [hip[0] + f * 190, hip[1] + 20]; foot = [knee[0] + f * 10, 1238]; }
        else { knee = [hip[0] + side * 10, 1225]; foot = [knee[0] - f * 200, 1238]; }
      } else {
        const a = (side < 0 ? -1 : 1) * 0 + (side < 0 ? p.legL[0] : p.legR[0]);
        const sw = side < 0 ? swing : -swing;
        const ang = a + (turn !== 0 ? sw * Math.sign(turn) * side : sw * 0.35);
        knee = [hip[0] + side * Math.sin(Math.abs(a)) * 40 + Math.sin(ang * (turn ? side : 1)) * LEG1 * (turn ? 1 : 0.4), hip[1] + Math.cos(ang) * LEG1];
        const kb = (side < 0 ? p.legL[1] : p.legR[1]) + Math.max(0, -Math.sin(ph + (side < 0 ? 0 : Math.PI))) * (p.run ? 1.3 : 0.5) * gait;
        foot = [knee[0] - (turn ? Math.sign(turn) : 0) * Math.sin(kb) * LEG2 * 0.8, knee[1] + Math.cos(kb) * LEG2];
        foot[1] = Math.min(foot[1], 1238); if (!gait) foot[1] = 1238;
      }
      legs[side] = { hip, knee, foot };
    }
    // --- arms (FK, or IK when aiming)
    const arms = {};
    for (const side of [-1, 1]) {
      const sh = [(side < 0 ? S.shL : S.shR)[0] + lean, S.shL[1] + drop];
      const [a0, e0] = side < 0 ? p.armL : p.armR;
      const sw = (side < 0 ? -swing : swing) * 0.9;
      let elbow, hand;
      const tgt = this._aim && (side > 0 ? this._aim.R : this._aim.L);
      if (tgt) {
        const T = [tgt[0], tgt[1]];
        const item = side > 0 ? p.hold : p.holdL; const reach = { flashlight: 70, taser: 60, gavel: 0, phone: 0 }[item] || 0;
        let dx = T[0] - sh[0], dy = T[1] - sh[1], dd = Math.hypot(dx, dy) || 1;
        T[0] -= dx / dd * reach; T[1] -= dy / dd * reach; dx = T[0] - sh[0]; dy = T[1] - sh[1]; dd = Math.min(Math.hypot(dx, dy), ARM1 + ARM2 - 2);
        const base = Math.atan2(dy, dx), cosA = (ARM1 * ARM1 + dd * dd - ARM2 * ARM2) / (2 * ARM1 * dd), A = Math.acos(clamp(cosA, -1, 1));
        // two possible elbows; take the lower one (elbows hang down), ties go outward
        const e1 = [sh[0] + Math.cos(base + A) * ARM1, sh[1] + Math.sin(base + A) * ARM1];
        const e2 = [sh[0] + Math.cos(base - A) * ARM1, sh[1] + Math.sin(base - A) * ARM1];
        const score = (e) => e[1] + (e[0] - sh[0]) * side * 0.3;
        elbow = score(e1) >= score(e2) ? e1 : e2;
        hand = [sh[0] + Math.cos(base) * dd, sh[1] + Math.sin(base) * dd];
        arms[side] = { sh, elbow, hand, dir: Math.atan2(hand[1] - elbow[1], hand[0] - elbow[0]) };
      } else {
        const a = a0 + sw, e = e0;
        elbow = [sh[0] + side * Math.sin(a) * ARM1, sh[1] + Math.cos(a) * ARM1];
        hand = [elbow[0] + side * Math.sin(a + e) * ARM2, elbow[1] + Math.cos(a + e) * ARM2];
        arms[side] = { sh, elbow, hand, dir: Math.atan2(hand[1] - elbow[1], hand[0] - elbow[0]) };
      }
    }
    const skin = d.skin, skinD = shade(skin, -0.18);
    const topC = d.topColor, topD = shade(topC, -0.25);
    const longSleeve = ['long', 'hoodie', 'uniform', 'suit', 'trench', 'robe', 'jacket'].includes(d.top);

    // ----------------------------------------------------------- draw order: far limbs, legs, torso, near limbs, head
    const far = turn > 0 ? -1 : 1, near = -far;
    const drawLeg = (side) => {
      const L = legs[side]; if (p.seatHideLegs) return;
      poly(g, [L.hip, L.knee, L.foot], 66 * B, d.pants);
      // shoe
      const fdir = turn !== 0 ? Math.sign(turn) : (side * 0.25);
      g.fillStyle = d.shoes; g.strokeStyle = INK; g.lineWidth = LINE;
      g.beginPath(); g.ellipse(L.foot[0] + fdir * 26, L.foot[1] + 4, 36, 16, 0, 0, 7); g.fill(); g.stroke();
    };
    const drawArm = (side) => {
      const A = arms[side];
      const sleeve = longSleeve ? topC : null;
      if (sleeve) poly(g, [A.sh, A.elbow, A.hand], 52 * B, sleeve);
      else {
        const mid = [lerp(A.sh[0], A.elbow[0], 0.55), lerp(A.sh[1], A.elbow[1], 0.55)];
        poly(g, [mid, A.elbow, A.hand], 42 * B, skin);
        poly(g, [A.sh, mid], 60 * B, topC);
      }
      // hand (mitten + thumb)
      g.fillStyle = skin; g.strokeStyle = INK; g.lineWidth = LINE;
      g.save(); g.translate(...A.hand); g.rotate(A.dir - Math.PI / 2);
      g.beginPath(); g.ellipse(0, 16, 23, 29, 0, 0, 7); g.fill(); g.stroke();
      g.beginPath(); g.ellipse(side * 18, 4, 9, 15, side * 0.6, 0, 7); g.fill(); g.stroke();
      g.strokeStyle = 'rgba(40,25,20,0.55)'; g.lineWidth = 2.5; for (const fxp of [-9, 0, 9]) { g.beginPath(); g.moveTo(fxp, 26); g.lineTo(fxp * 1.1, 44); g.stroke(); }
      g.restore();
      const item = side > 0 ? p.hold : p.holdL;
      if (item) drawItem(g, item, A.hand, A.dir, t);
    };
    if (!back) { drawArm(far); }
    drawLeg(far); drawLeg(near);
    // torso
    const sy = S.shL[1] + drop, wy = S.waist + drop, hy = S.hipL[1] + drop + 10;
    const torso = new Path2D();
    torso.moveTo(S.shL[0] + lean - 12, sy - 10);
    torso.quadraticCurveTo(cx + lean, sy - 30, S.shR[0] + lean + 12, sy - 10);
    torso.quadraticCurveTo(S.shR[0] + lean + 4, sy + 140, cx + 76 * B + lean * 0.5, wy);
    torso.lineTo(cx + 80 * B, hy);
    torso.lineTo(cx - 80 * B, hy);
    torso.lineTo(cx - 76 * B + lean * 0.5, wy);
    torso.quadraticCurveTo(S.shL[0] + lean - 4, sy + 140, S.shL[0] + lean - 12, sy - 10);
    torso.closePath();
    if (d.top === 'robe') { // long robe over the legs
      g.fillStyle = topC; g.strokeStyle = INK; g.lineWidth = LINE;
      g.beginPath(); g.moveTo(cx - 74 * B, hy - 40); g.lineTo(cx - 100 * B, 1000 + drop * 0.3); g.lineTo(cx + 100 * B, 1000 + drop * 0.3); g.lineTo(cx + 74 * B, hy - 40); g.closePath(); g.fill(); g.stroke();
    }
    g.fillStyle = topC; g.fill(torso); g.strokeStyle = INK; g.lineWidth = LINE; g.stroke(torso);
    // shading on the far side
    g.save(); g.clip(torso); g.fillStyle = 'rgba(0,0,0,0.16)'; g.fillRect(far < 0 ? 0 : cx + 30 * B, 0, CW / 2 - 30 * B, CH); g.restore();
    torsoDetails(g, d, cx + lean, sy, wy, hy, B, back, topC, topD);
    // pants top/belt
    g.fillStyle = d.pants; g.beginPath(); g.moveTo(cx - 80 * B, hy - 18); g.lineTo(cx + 80 * B, hy - 18); g.lineTo(cx + 80 * B, hy + 34); g.lineTo(cx - 80 * B, hy + 34); g.closePath(); g.fill(); g.stroke();
    if (d.top === 'uniform' || d.belt) { g.fillStyle = '#151515'; g.fillRect(cx - 80 * B, hy - 18, 160 * B, 18); g.fillStyle = '#c9a54a'; g.fillRect(cx - 12, hy - 18, 24, 18); }
    if (back) drawArm(far);
    drawArm(near);
    // neck
    g.fillStyle = skin; g.strokeStyle = INK; g.lineWidth = LINE;
    const nx = cx + lean * 0.9 + turn * 4;
    g.beginPath(); g.moveTo(nx - 26, 190 + drop); g.lineTo(nx - 28, sy - 18); g.quadraticCurveTo(nx, sy - 8, nx + 28, sy - 18); g.lineTo(nx + 26, 190 + drop); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(nx - 26, 196 + drop, 52, 18);
    if (d.top === 'hoodie') { g.fillStyle = topD; g.beginPath(); g.ellipse(nx, sy - 14, 54, 18, 0, 0, 7); g.fill(); g.stroke(); }
    // head
    drawHead(g, d, p, [S.headC[0] + lean * 1.05, S.headC[1] + drop], turn, back, blinkOn, talkOpen, t, this.seed);
    // standing in shadow: the whole figure sinks into blue-black (works for any skin tone), only an eye glint remains
    if (p.inShadow > 0) {
      g.save(); g.globalCompositeOperation = 'source-atop'; g.fillStyle = `rgba(6,9,20,${0.86 * p.inShadow})`; g.fillRect(0, 0, CW, CH); g.restore();
      if (!back && g.__eyes && !blinkOn) for (const [x, y] of g.__eyes) {
        const gl = g.createRadialGradient(x, y, 1, x, y, 16); gl.addColorStop(0, `rgba(255,245,215,${0.9 * p.inShadow})`); gl.addColorStop(1, 'rgba(255,240,200,0)');
        g.fillStyle = gl; g.beginPath(); g.arc(x, y, 16, 0, 7); g.fill();
      }
    }
  }
}

// ---------------------------------------------------------------- pieces
// a limb as one seamless thick stroke (ink outline underneath, colour on top): no seams at the joints
function poly(g, pts, w, fill) {
  g.lineCap = 'round'; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(...pts[0]); for (let i = 1; i < pts.length; i++) g.lineTo(...pts[i]);
  g.strokeStyle = INK; g.lineWidth = w + LINE * 2; g.stroke();
  g.strokeStyle = fill; g.lineWidth = w; g.stroke();
}
function limb(g, a, b, w1, w2, fill) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L;
  g.beginPath();
  g.moveTo(a[0] + nx * w1 / 2, a[1] + ny * w1 / 2);
  g.lineTo(b[0] + nx * w2 / 2, b[1] + ny * w2 / 2);
  g.arc(b[0], b[1], w2 / 2, Math.atan2(ny, nx), Math.atan2(ny, nx) + Math.PI);
  g.lineTo(a[0] - nx * w1 / 2, a[1] - ny * w1 / 2);
  g.arc(a[0], a[1], w1 / 2, Math.atan2(-ny, -nx), Math.atan2(-ny, -nx) + Math.PI);
  g.closePath(); g.fillStyle = fill; g.fill(); g.strokeStyle = INK; g.lineWidth = LINE; g.stroke();
}

function torsoDetails(g, d, cx, sy, wy, hy, B, back, c, cd) {
  g.strokeStyle = INK; g.lineWidth = 3;
  if (back) { g.beginPath(); g.moveTo(cx, sy + 10); g.lineTo(cx, wy - 40); g.strokeStyle = 'rgba(0,0,0,0.25)'; g.stroke(); return; }
  if (d.top === 'tshirt') { g.beginPath(); g.moveTo(cx - 30, sy - 22); g.quadraticCurveTo(cx, sy + 8, cx + 30, sy - 22); g.stroke(); g.strokeStyle = 'rgba(0,0,0,0.25)'; g.beginPath(); g.moveTo(cx - 40, wy - 60); g.quadraticCurveTo(cx, wy - 40, cx + 30, wy - 80); g.stroke(); }
  if (d.top === 'long' || d.top === 'jacket') { g.fillStyle = d.top2; g.beginPath(); g.moveTo(cx - 28, sy - 22); g.lineTo(cx, sy + 30); g.lineTo(cx + 28, sy - 22); g.closePath(); g.fill(); g.stroke(); }
  if (d.top === 'jacket') { g.lineWidth = 3; g.beginPath(); g.moveTo(cx, sy + 30); g.lineTo(cx, hy - 20); g.stroke(); }
  if (d.top === 'hoodie') { g.beginPath(); g.moveTo(cx - 12, sy - 6); g.lineTo(cx - 16, sy + 70); g.moveTo(cx + 12, sy - 6); g.lineTo(cx + 16, sy + 70); g.stroke();
    g.fillStyle = cd; g.beginPath(); g.moveTo(cx - 52, wy - 70); g.lineTo(cx + 52, wy - 70); g.lineTo(cx + 62, wy - 10); g.lineTo(cx - 62, wy - 10); g.closePath(); g.fill(); g.stroke(); }
  if (d.top === 'uniform') {
    g.fillStyle = d.top2; g.beginPath(); g.moveTo(cx - 24, sy - 22); g.lineTo(cx, sy + 26); g.lineTo(cx + 24, sy - 22); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#d9b45a'; g.beginPath(); g.moveTo(cx - 46, sy + 60); g.lineTo(cx - 30, sy + 52); g.lineTo(cx - 22, sy + 66); g.lineTo(cx - 30, sy + 90); g.lineTo(cx - 44, sy + 80); g.closePath(); g.fill(); g.stroke();
    for (const s of [-1, 1]) { g.strokeRect(cx + s * 34 - 18, sy + 100, 36, 30); }
    g.fillStyle = '#222'; g.fillRect(cx + 32, sy + 40, 22, 40);
  }
  if (d.top === 'suit' || d.top === 'robe') { g.fillStyle = d.top2 || '#eee'; g.beginPath(); g.moveTo(cx - 26, sy - 22); g.lineTo(cx, sy + 60); g.lineTo(cx + 26, sy - 22); g.closePath(); g.fill(); g.stroke();
    if (d.top === 'suit') { g.fillStyle = d.tie || '#7a1e1e'; g.beginPath(); g.moveTo(cx - 8, sy - 6); g.lineTo(cx + 8, sy - 6); g.lineTo(cx + 12, sy + 70); g.lineTo(cx, sy + 84); g.lineTo(cx - 12, sy + 70); g.closePath(); g.fill(); g.stroke(); } }
  if (d.top === 'trench') {
    g.fillStyle = d.top2; g.beginPath(); g.moveTo(cx - 40, sy - 20); g.lineTo(cx, sy + 150); g.lineTo(cx + 40, sy - 20); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#d9ecfb'; g.beginPath(); g.moveTo(cx - 22, sy - 20); g.lineTo(cx, sy + 36); g.lineTo(cx + 22, sy - 20); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = cd; for (const s of [-1, 1]) { g.beginPath(); g.moveTo(cx + s * 40, sy - 20); g.lineTo(cx + s * 86, sy + 10); g.lineTo(cx + s * 26, sy + 120); g.closePath(); g.fill(); g.stroke(); }
    g.fillStyle = shade(c, -0.35); g.fillRect(cx - 68 * B, wy - 20, 136 * B, 22); g.strokeRect(cx - 68 * B, wy - 20, 136 * B, 22);
  }
}

function drawHead(g, d, p, [hx, hy], turn, back, blinkOn, talkOpen, t, seed) {
  const rx = 66, ry = 84, skin = d.skin;
  g.save(); g.translate(hx, hy); g.rotate(p.tilt || 0);
  // long hair behind the head
  if (d.hair === 'long') { g.fillStyle = d.hairColor; g.strokeStyle = INK; g.lineWidth = LINE; g.beginPath(); g.ellipse(0, 50, rx + 14, ry + 70, 0, 0, 7); g.fill(); g.stroke(); }
  if (d.hair === 'bob') {   // ends at the jaw, never under the chin (or it reads as a beard)
    g.save(); g.beginPath(); g.rect(-rx - 40, -ry - 60, 2 * rx + 80, ry * 1.0 + 60); g.clip();
    g.fillStyle = d.hairColor; g.strokeStyle = INK; g.lineWidth = LINE; g.beginPath(); g.ellipse(0, 0, rx + 16, ry + 8, 0, 0, 7); g.fill(); g.stroke(); g.restore();
  }
  // ears (behind the face outline)
  g.fillStyle = skin; g.strokeStyle = INK; g.lineWidth = LINE;
  for (const s of [-1, 1]) {
    if (!back && turn * s < -0.4) continue;          // far ear hidden when turned
    g.beginPath(); g.ellipse(s * (rx - 4) - turn * 10, 6, 13, 22, 0, 0, 7); g.fill(); g.stroke();
  }
  // face shape
  const face = new Path2D();
  face.moveTo(-rx, -6);
  face.bezierCurveTo(-rx, -ry * 1.15, rx, -ry * 1.15, rx, -6);
  face.bezierCurveTo(rx, ry * 0.45, rx * 0.45 + turn * 10, ry * 0.95, turn * 12, ry);
  face.bezierCurveTo(-rx * 0.45 + turn * 10, ry * 0.95, -rx, ry * 0.45, -rx, -6);
  g.fillStyle = skin; g.fill(face); g.stroke(face);
  g.save(); g.clip(face);
  g.fillStyle = 'rgba(120,60,40,0.14)'; g.beginPath(); g.ellipse(turn > 0 ? -rx : rx, 20, rx * 0.55, ry * 1.2, 0, 0, 7); g.fill();   // side shade
  if (d.stubble) { g.fillStyle = 'rgba(40,30,25,0.22)'; g.beginPath(); g.ellipse(turn * 10, ry * 0.6, rx * 0.9, ry * 0.45, 0, 0, 7); g.fill(); }
  g.restore();
  if (back) {
    hair(g, d, rx, ry, turn, true);
  } else {
    const fx = turn * rx * 0.33;
    // eyes
    const ex = 27, ey = -4;
    const expr = p.expr;
    if (p.eyeShadow) {      // deep, shadowed eye sockets (the creepy look)
      g.save(); g.clip(face);
      for (const s of [-1, 1]) { const gr = g.createRadialGradient(fx + s * ex, ey, 2, fx + s * ex, ey, 34);
        gr.addColorStop(0, `rgba(25,18,22,${0.85 * p.eyeShadow})`); gr.addColorStop(0.6, `rgba(30,22,26,${0.55 * p.eyeShadow})`); gr.addColorStop(1, 'rgba(30,22,26,0)');
        g.fillStyle = gr; g.beginPath(); g.ellipse(fx + s * ex, ey - 2, 36, 26, 0, 0, 7); g.fill(); }
      g.restore();
    }
    for (const s of [-1, 1]) {
      const far = turn * s < -0.2, sc = far ? 0.8 : 1;
      const x = fx + s * ex * (1 - Math.abs(turn) * 0.15) * (far ? 0.85 : 1);
      drawEye(g, x, ey, sc, blinkOn || expr === 'asleep' ? 'closed' : expr, d.eyes, p.look);
    }
    // brows
    const brow = { angry: 0.45, scared: -0.45, scream: -0.5, sad: -0.4, focused: 0.25, smug: 0.15 }[expr] || 0;
    g.strokeStyle = shade(d.hairColor === '#e3c46a' ? '#9c7b3a' : d.hairColor, -0.1); g.lineWidth = 7;
    for (const s of [-1, 1]) { const x = fx + s * ex; g.beginPath(); g.moveTo(x - s * 15, ey - 24 + brow * 10 * s * s - (expr === 'scared' || expr === 'scream' ? 6 : 0) + brow * 8); g.lineTo(x + s * 16, ey - 26 - brow * 6 - (expr === 'scared' || expr === 'scream' ? 8 : 0)); g.stroke(); }
    // nose
    g.strokeStyle = INK; g.lineWidth = 3.5;
    g.beginPath(); g.moveTo(fx + turn * 6, ey + 4); g.quadraticCurveTo(fx + turn * 22 + 2, ey + 34, fx + turn * 14 - 6, ey + 40); g.stroke();
    g.beginPath(); g.moveTo(fx + turn * 14 - 8, ey + 42); g.quadraticCurveTo(fx + turn * 14, ey + 46, fx + turn * 14 + 9, ey + 41); g.stroke();
    // nostrils + bridge shading, cheek / smile lines
    g.fillStyle = 'rgba(90,50,40,0.25)'; g.beginPath(); g.ellipse(fx + turn * 18 + (turn >= 0 ? -6 : 6), ey + 26, 6, 15, 0, 0, 7); g.fill();
    if (['smile', 'creepy', 'smug'].includes(expr) || d.age > 0.3) {
      g.strokeStyle = 'rgba(60,30,25,0.45)'; g.lineWidth = 3;
      for (const s of [-1, 1]) { g.beginPath(); g.moveTo(fx + s * 20, ey + 36); g.quadraticCurveTo(fx + s * (expr === 'creepy' ? 40 : 30), ey + 54, fx + s * (expr === 'creepy' ? 38 : 26), ey + 70); g.stroke(); }
    }
    // age lines / bags
    if (d.age > 0.4) { g.strokeStyle = 'rgba(60,30,20,0.4)'; g.lineWidth = 2.5; for (let i = 0; i < 2; i++) { g.beginPath(); g.moveTo(fx - 24, -46 - i * 9); g.quadraticCurveTo(fx, -50 - i * 9, fx + 24, -46 - i * 9); g.stroke(); } }
    if (d.age > 0.2 || expr === 'tired') { g.strokeStyle = 'rgba(70,40,30,0.35)'; g.lineWidth = 2.5; for (const s of [-1, 1]) { g.beginPath(); g.arc(fx + s * ex, ey + 10, 11, 0.3, Math.PI - 0.3); g.stroke(); } }
    // mouth
    drawMouth(g, fx + turn * 6, 44, talkOpen > 0.05 ? 'talk' : expr, talkOpen);
    if (d.beard) { g.fillStyle = d.hairColor; g.strokeStyle = INK; g.lineWidth = LINE; g.beginPath(); g.moveTo(-rx + 6, 10); g.quadraticCurveTo(-rx * 0.6, ry * 1.15, turn * 12, ry * 1.1); g.quadraticCurveTo(rx * 0.6, ry * 1.15, rx - 6, 10); g.quadraticCurveTo(rx * 0.3, 60, 0, 58); g.quadraticCurveTo(-rx * 0.3, 60, -rx + 6, 10); g.fill(); g.stroke(); }
    if (d.glasses) { g.strokeStyle = INK; g.lineWidth = 4.5; g.fillStyle = 'rgba(170,215,255,0.18)'; for (const s of [-1, 1]) { g.beginPath(); g.arc(fx + s * ex, ey, 19, 0, 7); g.fill(); g.stroke(); } g.beginPath(); g.moveTo(fx - ex + 19, ey); g.lineTo(fx + ex - 19, ey); g.stroke(); }
    if (p.sweat) { g.fillStyle = '#9fd3ff'; g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); g.moveTo(rx * 0.7, -40); g.quadraticCurveTo(rx * 0.85, -18, rx * 0.72, -12); g.quadraticCurveTo(rx * 0.58, -18, rx * 0.7, -40); g.fill(); g.stroke(); }
    if (p.tears) { g.strokeStyle = 'rgba(120,190,255,0.8)'; g.lineWidth = 4; for (const s of [-1, 1]) { g.beginPath(); g.moveTo(fx + s * ex, ey + 14); g.lineTo(fx + s * ex + 2, ey + 46); g.stroke(); } }
    // remember where the eyes are (for the in-shadow glint)
    g.__eyes = [[hx + (fx - ex) * 1, hy + ey], [hx + (fx + ex), hy + ey]];
    hair(g, d, rx, ry, turn, false);
  }
  if (d.headphones) { g.strokeStyle = '#2a2a30'; g.lineWidth = 12; g.beginPath(); g.arc(0, -4, rx + 6, Math.PI * 1.05, Math.PI * 1.95); g.stroke(); for (const s of [-1, 1]) { if (turn * s < -0.4) continue; g.fillStyle = '#2a2a30'; g.strokeStyle = INK; g.lineWidth = LINE; g.beginPath(); g.ellipse(s * (rx + 2) - turn * 8, 8, 16, 26, 0, 0, 7); g.fill(); g.stroke(); g.fillStyle = '#c0392b'; g.fillRect(s * (rx + 2) - turn * 8 - 5, 0, 10, 16); } }
  if (d.pencil) { g.save(); g.translate(rx * 0.95 - turn * 8, -14); g.rotate(0.55); g.fillStyle = '#f4c430'; g.strokeStyle = INK; g.lineWidth = 3; g.fillRect(-6, -52, 12, 40); g.strokeRect(-6, -52, 12, 40); g.fillStyle = '#f08fa0'; g.fillRect(-6, -62, 12, 10); g.strokeRect(-6, -62, 12, 10); g.restore(); }
  hat(g, d, rx, ry, turn);
  g.restore();
}

function drawEye(g, x, y, sc, expr, iris, look) {
  g.save(); g.translate(x, y); g.scale(sc, sc);
  g.strokeStyle = INK; g.lineWidth = 3.5;
  if (expr === 'closed') { g.beginPath(); g.moveTo(-12, 2); g.quadraticCurveTo(0, 8, 12, 2); g.stroke(); g.restore(); return; }
  if (expr === 'yawn') { g.lineWidth = 4; g.beginPath(); g.moveTo(-13, 0); g.quadraticCurveTo(0, 6, 13, -2); g.stroke(); g.beginPath(); g.moveTo(-10, 6); g.lineTo(10, 4); g.stroke(); g.restore(); return; }
  const wide = expr === 'scared' || expr === 'scream' || expr === 'shock';
  const h = wide ? 11 : expr === 'angry' || expr === 'focused' || expr === 'smug' || expr === 'creepy' ? 6 : 8, w = 14;
  // crease above the eye
  g.save(); g.strokeStyle = 'rgba(60,35,30,0.45)'; g.lineWidth = 2.5; g.beginPath(); g.moveTo(-w + 2, -h * 1.1); g.quadraticCurveTo(0, -h * 2.1, w - 1, -h * 1.0); g.stroke(); g.restore();
  g.fillStyle = '#fbfaf6'; g.beginPath(); g.moveTo(-w, 0); g.quadraticCurveTo(0, -h * 1.6, w, 0); g.quadraticCurveTo(0, h * 1.2, -w, 0); g.fill(); g.stroke();
  const ir = wide ? 5.5 : 7;
  g.fillStyle = iris; g.beginPath(); g.arc(look * 5, 0, ir, 0, 7); g.fill();
  g.fillStyle = '#111'; g.beginPath(); g.arc(look * 5, 0, ir * 0.5, 0, 7); g.fill();
  g.fillStyle = '#fff'; g.beginPath(); g.arc(look * 5 - 2, -2, 1.8, 0, 7); g.fill();
  g.lineWidth = 4.5; g.beginPath(); g.moveTo(-w - 1, 0); g.quadraticCurveTo(0, -h * 1.6 - 1, w + 1, 0); g.stroke();       // upper lid
  g.restore();
}

function drawMouth(g, x, y, expr, open) {
  g.strokeStyle = INK; g.lineWidth = 4; g.fillStyle = '#5a1f1f';
  const O = (w, h, teeth) => { g.beginPath(); g.ellipse(x, y + h * 0.3, w, h, 0, 0, 7); g.fill(); g.stroke(); if (teeth) { g.fillStyle = '#f3efe6'; g.fillRect(x - w * 0.7, y + h * 0.3 - h * 0.92, w * 1.4, h * 0.35); } };
  switch (expr) {
    case 'smile': g.beginPath(); g.moveTo(x - 18, y); g.quadraticCurveTo(x, y + 12, x + 18, y - 2); g.stroke(); break;
    case 'smug': g.beginPath(); g.moveTo(x - 14, y + 2); g.quadraticCurveTo(x + 4, y + 6, x + 18, y - 6); g.stroke(); break;
    case 'sad': case 'tired': g.beginPath(); g.moveTo(x - 16, y + 6); g.quadraticCurveTo(x, y - 2, x + 16, y + 6); g.stroke(); break;
    case 'angry': g.beginPath(); g.moveTo(x - 18, y + 4); g.lineTo(x + 18, y + 2); g.stroke(); break;
    case 'scared': O(10, 12, false); break;
    case 'shock': O(11, 15, false); break;
    case 'scream': O(20, 26, true); break;
    case 'yawn': O(14, 30, false); break;
    case 'creepy': {   // a wide, too-happy grin with teeth
      g.beginPath(); g.moveTo(x - 36, y - 8); g.quadraticCurveTo(x, y + 30, x + 36, y - 8); g.quadraticCurveTo(x, y + 4, x - 36, y - 8); g.closePath();
      g.fillStyle = '#3a1414'; g.fill(); g.save(); g.clip();
      g.fillStyle = '#efe6c8'; g.fillRect(x - 40, y - 12, 80, 16); g.strokeStyle = 'rgba(80,60,40,0.7)'; g.lineWidth = 2;
      for (let i = -3; i <= 3; i++) { g.beginPath(); g.moveTo(x + i * 10, y - 10); g.lineTo(x + i * 10, y + 4); g.stroke(); }
      g.restore(); g.strokeStyle = INK; g.lineWidth = 4; g.beginPath(); g.moveTo(x - 36, y - 8); g.quadraticCurveTo(x, y + 30, x + 36, y - 8); g.quadraticCurveTo(x, y + 4, x - 36, y - 8); g.stroke();
      break; }
    case 'talk': O(12, 4 + open * 10, open > 0.5); break;
    case 'asleep': g.beginPath(); g.moveTo(x - 10, y + 2); g.lineTo(x + 10, y + 2); g.stroke(); break;
    default: g.beginPath(); g.moveTo(x - 15, y + 1); g.quadraticCurveTo(x, y + 4, x + 15, y); g.stroke();
  }
}

function hair(g, d, rx, ry, turn, back) {
  if (d.hair === 'bald' || (d.hat && d.hat !== 'cap' && d.hair === 'short' && false)) return;
  g.fillStyle = d.hairColor; g.strokeStyle = INK; g.lineWidth = LINE;
  const line = back ? ry * 0.55 : -ry * 0.42;                           // hairline
  g.beginPath();
  if (back) { g.moveTo(-rx - 2, line); g.bezierCurveTo(-rx - 6, -ry * 1.25, rx + 6, -ry * 1.25, rx + 2, line); g.quadraticCurveTo(0, line + 14, -rx - 2, line); }
  else {
    g.moveTo(-rx - 3, 4); g.bezierCurveTo(-rx - 8, -ry * 1.3, rx + 8, -ry * 1.3, rx + 3, 4);
    g.lineTo(rx - 4, line + 10 + turn * 6);
    if (d.hair === 'spiky') { for (let i = 6; i >= -6; i--) g.lineTo(i * rx / 6 + turn * 8, line + (i % 2 ? -10 : 6)); }
    else if (d.hair === 'side') { g.quadraticCurveTo(rx * 0.2 + turn * 10, line - 22, -rx * 0.4 + turn * 8, line + 4); g.quadraticCurveTo(-rx * 0.7, line + 16, -rx + 4, line + 14); }
    else g.quadraticCurveTo(turn * 10, line - 8, -rx + 4, line + 10 - turn * 6);
    g.lineTo(-rx - 3, 4);
  }
  g.closePath(); g.fill(); g.stroke();
  if (d.hair === 'buzz') { g.fillStyle = 'rgba(255,255,255,0.08)'; g.fill(); }
  if (d.hair === 'bun') { g.beginPath(); g.arc(0, -ry * 1.05, 26, 0, 7); g.fill(); g.stroke(); }
  g.strokeStyle = 'rgba(255,255,255,0.18)'; g.lineWidth = 3; g.beginPath(); g.arc(-rx * 0.2, -ry * 0.55, rx * 0.5, Math.PI * 1.15, Math.PI * 1.55); g.stroke();
}

function hat(g, d, rx, ry, turn) {
  if (!d.hat) return;
  g.fillStyle = d.hatColor; g.strokeStyle = INK; g.lineWidth = LINE;
  if (d.hat === 'police') {
    g.beginPath(); g.moveTo(-rx - 6, -ry * 0.55); g.lineTo(-rx * 1.12, -ry * 1.0); g.quadraticCurveTo(0, -ry * 1.35, rx * 1.12, -ry * 1.0); g.lineTo(rx + 6, -ry * 0.55); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#111'; g.fillRect(-rx - 6, -ry * 0.62, 2 * rx + 12, 14);
    g.beginPath(); g.ellipse(turn * 14, -ry * 0.5, rx * 0.95, 12, 0, 0, Math.PI); g.fill(); g.stroke();
    g.fillStyle = '#d9b45a'; g.beginPath(); g.arc(turn * 10, -ry * 0.82, 9, 0, 7); g.fill(); g.stroke();
  } else if (d.hat === 'cap') {
    g.beginPath(); g.moveTo(-rx - 4, -ry * 0.5); g.bezierCurveTo(-rx - 2, -ry * 1.3, rx + 2, -ry * 1.3, rx + 4, -ry * 0.5); g.closePath(); g.fill(); g.stroke();
    g.beginPath(); g.ellipse(turn * 30 + 30, -ry * 0.5, rx * 0.8, 12, 0.05, 0, 7); g.fill(); g.stroke();
  } else if (d.hat === 'fedora') {
    g.beginPath(); g.ellipse(0, -ry * 0.62, rx * 1.55, 18, 0, 0, 7); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(-rx * 0.85, -ry * 0.65); g.lineTo(-rx * 0.75, -ry * 1.35); g.quadraticCurveTo(0, -ry * 1.18, rx * 0.75, -ry * 1.35); g.lineTo(rx * 0.85, -ry * 0.65); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#1f1712'; g.fillRect(-rx * 0.84, -ry * 0.86, rx * 1.68, 14);
  } else if (d.hat === 'beanie') {
    g.beginPath(); g.moveTo(-rx - 4, -ry * 0.4); g.bezierCurveTo(-rx - 2, -ry * 1.4, rx + 2, -ry * 1.4, rx + 4, -ry * 0.4); g.closePath(); g.fill(); g.stroke();
  }
}

function drawItem(g, item, [x, y], dir, t) {
  g.save(); g.translate(x, y); g.rotate(dir - Math.PI / 2); g.strokeStyle = INK; g.lineWidth = LINE;
  switch (item) {
    case 'flashlight': g.fillStyle = '#2b2b2b'; g.fillRect(-10, 0, 20, 90); g.strokeRect(-10, 0, 20, 90); g.fillStyle = '#ffe680'; g.fillRect(-13, 86, 26, 10); g.strokeRect(-13, 86, 26, 10); break;
    case 'taser': g.fillStyle = '#e2c341'; g.fillRect(-12, 0, 24, 70); g.strokeRect(-12, 0, 24, 70); g.fillStyle = '#222'; g.fillRect(-14, 58, 28, 16); break;
    case 'phone': g.fillStyle = '#222'; g.fillRect(-14, -10, 28, 50); g.strokeRect(-14, -10, 28, 50); break;
    case 'gavel': g.fillStyle = '#6b4226'; g.fillRect(-6, -20, 12, 110); g.strokeRect(-6, -20, 12, 110); g.fillRect(-36, 80, 72, 30); g.strokeRect(-36, 80, 72, 30); break;
    case 'photo': g.fillStyle = '#6b4226'; g.fillRect(-46, -10, 92, 110); g.strokeRect(-46, -10, 92, 110); g.fillStyle = '#cfe0ea'; g.fillRect(-36, 0, 72, 90);
      g.fillStyle = '#f1d3bd'; g.beginPath(); g.arc(0, 40, 18, 0, 7); g.fill(); g.fillStyle = '#e3c46a'; g.beginPath(); g.arc(0, 30, 18, Math.PI, 0); g.fill(); g.fillStyle = '#5f9e55'; g.fillRect(-24, 62, 48, 28); break;
    case 'papers': g.fillStyle = '#f4f1e8'; g.fillRect(-40, 0, 80, 100); g.strokeRect(-40, 0, 80, 100); break;
    case 'hammer': g.fillStyle = '#8b5a2b'; g.fillRect(-7, -10, 14, 120); g.strokeRect(-7, -10, 14, 120); g.fillStyle = '#777'; g.fillRect(-34, 100, 68, 28); g.strokeRect(-34, 100, 68, 28); break;
    case 'crowbar': g.strokeStyle = '#b3261e'; g.lineWidth = 12; g.beginPath(); g.moveTo(0, -30); g.lineTo(0, 140); g.quadraticCurveTo(0, 165, 24, 165); g.stroke(); break;
  }
  g.restore();
}

const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
function shade(h, k) { if (!h || h[0] !== '#') return h; return `rgb(${hex(h).map(v => Math.round(k < 0 ? v * (1 + k) : v + (255 - v) * k)).join(',')})`; }
