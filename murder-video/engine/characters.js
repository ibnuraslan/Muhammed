// Semi-realistic "Sims 2 / PS2 cutscene" characters:
// smooth bodies, painted face textures, 3D eyeballs + blinking lids, chunky textured hair.
'use strict';

const THIGH = 0.43, SHIN = 0.43, LEG = THIGH + SHIN;
const HEAD_R = 0.105, HSX = 0.95, HSY = 1.17, HSZ = 1.0, HEAD_C = 0.125;

function capsule(parent, r, len, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 6, 14), mat);
  m.position.set(x, y, z); parent.add(m); return m;
}

// ------------------------------------------------------------ face painting
function paintFace(d, seed) {
  const W = 1024, H = 512;
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  const skin = new THREE.Color(d.skin || '#e5b994');
  const s3 = f => { const h = skin.clone().multiplyScalar(f * f).getHex(); return `${(h >> 16) & 255},${(h >> 8) & 255},${h & 255}`; };
  const sc = (f, a = 1) => `rgba(${s3(f)},${a})`;
  const sx = HEAD_R * HSX, sy = HEAD_R * HSY;
  const P = (mx, my) => {
    const ux = Math.max(-0.98, Math.min(0.98, mx / sx)), uy = Math.max(-0.98, Math.min(0.98, my / sy));
    const uz = Math.sqrt(Math.max(0.0001, 1 - ux * ux - uy * uy));
    return [Math.atan2(uz, -ux) / (2 * Math.PI) * W, Math.acos(uy) / Math.PI * H];
  };
  const KX = 1690, KY = 1330; // px per meter near the face centre
  const blobG = (mx, my, rx, ry, rgb, a0) => {
    const [x, y] = P(mx, my);
    g.save(); g.translate(x, y); g.scale(1, (ry * KY) / (rx * KX));
    const gr = g.createRadialGradient(0, 0, 0, 0, 0, rx * KX);
    gr.addColorStop(0, `rgba(${rgb},${a0})`); gr.addColorStop(1, `rgba(${rgb},0)`);
    g.fillStyle = gr; g.beginPath(); g.arc(0, 0, rx * KX, 0, 7); g.fill(); g.restore();
  };
  const R = makeRng(seed + 101);
  g.fillStyle = sc(1); g.fillRect(0, 0, W, H);
  // pores / mottling
  for (let i = 0; i < 9000; i++) { g.fillStyle = sc(0.9 + R() * 0.16, 0.25); g.fillRect(R() * W, R() * H, 2, 2); }
  const fem = !!d.female;
  const age = d.age || 0;
  // soft facial modelling
  blobG(0, -0.105, 0.06, 0.03, s3(0.85), 0.35);                // under-chin shadow
  for (const s of [-1, 1]) {
    blobG(0.031 * s, 0.012, 0.022, 0.018, s3(0.85), 0.3);      // eye socket
    blobG(0.047 * s, -0.022, 0.026, 0.02, fem ? '225,110,120' : '200,110,100', fem ? 0.32 : 0.16); // cheeks
    blobG(0.06 * s, -0.05, 0.03, 0.05, s3(0.92), 0.2);        // jaw side
         // nose side shadow
  }
  // nasolabial folds + age lines
  g.lineCap = 'round';
  for (const s of [-1, 1]) {
    const a = P(0.016 * s, -0.03), b = P(0.026 * s, -0.047), e = P(0.03 * s, -0.064);
    g.strokeStyle = sc(0.75, 0.25 + age * 0.3); g.lineWidth = 3;
    g.beginPath(); g.moveTo(...a); g.quadraticCurveTo(...b, ...e); g.stroke();
    // eyelid crease
    const [ex, ey] = P(0.031 * s, 0.012);
    g.strokeStyle = sc(0.68, 0.45); g.lineWidth = 2.2;
    g.beginPath(); g.ellipse(ex, ey - 4, 26, 22, 0, Math.PI * 1.12, Math.PI * 1.88); g.stroke();
    // lash line
    g.strokeStyle = fem ? 'rgba(25,15,12,0.95)' : 'rgba(40,25,20,0.7)'; g.lineWidth = fem ? 5 : 3;
    g.beginPath(); g.ellipse(ex, ey + 1, 22, 17, 0, Math.PI * 1.08, Math.PI * 1.92); g.stroke();
    if (fem) { g.beginPath(); g.moveTo(ex + 20 * s, ey - 6); g.lineTo(ex + 30 * s, ey - 13); g.stroke(); }
    g.strokeStyle = sc(0.7, 0.4); g.lineWidth = 1.6;
    g.beginPath(); g.ellipse(ex, ey, 21, 16, 0, Math.PI * 0.15, Math.PI * 0.85); g.stroke();
    if (age > 0.4) { g.strokeStyle = sc(0.78, 0.3); g.lineWidth = 1.5; for (let k = 0; k < 3; k++) { g.beginPath(); g.moveTo(ex + 28 * s, ey - 4 + k * 6); g.lineTo(ex + 40 * s, ey - 8 + k * 9); g.stroke(); } }
    // nostril
    const [nx, ny] = P(0.0068 * s, -0.028);
    g.fillStyle = 'rgba(60,25,20,0.55)'; g.beginPath(); g.ellipse(nx, ny, 5, 3, 0.3 * s, 0, 7); g.fill();
  }
  if (age > 0.4) { g.strokeStyle = sc(0.8, 0.28); g.lineWidth = 2; for (let k = 0; k < 3; k++) { const [a1, b1] = P(-0.03, 0.055 + k * 0.009), [a2, b2] = P(0.03, 0.055 + k * 0.009); g.beginPath(); g.moveTo(a1, b1); g.quadraticCurveTo((a1 + a2) / 2, b1 - 4, a2, b2); g.stroke(); } }
  // stubble
  if (d.stubble || d.shadow) {
    for (let i = 0; i < 2600; i++) {
      const mx = (R() - 0.5) * 0.11, my = -0.035 - R() * 0.075;
      if (Math.abs(mx) < 0.02 && my > -0.06 && my < -0.04) continue;
      const [x, y] = P(mx, my); g.fillStyle = `rgba(50,35,25,${0.18 + R() * 0.25})`; g.fillRect(x, y, 2, 2);
    }
  }
  // lips
  const [mx, my] = P(0, -0.05);
  const hw = fem ? 33 : 30, smile = d.smile || 0;
  const lip = fem ? (d.lips || '#b84a55') : '#' + skin.clone().lerp(new THREE.Color('#a0484a'), 0.42).getHexString();
  const lipDark = '#' + new THREE.Color(lip).multiplyScalar(0.72).getHexString();
  g.fillStyle = lipDark;
  g.beginPath(); g.moveTo(mx - hw, my - smile); g.quadraticCurveTo(mx - hw * 0.5, my - 11, mx - 4, my - 8); g.lineTo(mx, my - 6); g.lineTo(mx + 4, my - 8);
  g.quadraticCurveTo(mx + hw * 0.5, my - 11, mx + hw, my - smile); g.quadraticCurveTo(mx, my + 2, mx - hw, my - smile); g.fill();
  g.fillStyle = lip;
  g.beginPath(); g.moveTo(mx - hw * 0.92, my - smile + 1); g.quadraticCurveTo(mx, my + (fem ? 17 : 13), mx + hw * 0.92, my - smile + 1); g.quadraticCurveTo(mx, my + 2, mx - hw * 0.92, my - smile + 1); g.fill();
  g.fillStyle = 'rgba(255,230,220,0.35)'; g.beginPath(); g.ellipse(mx + 2, my + 7, hw * 0.35, 2.5, 0, 0, 7); g.fill();
  g.strokeStyle = 'rgba(70,20,22,0.85)'; g.lineWidth = 2.5;
  g.beginPath(); g.moveTo(mx - hw, my - smile); g.quadraticCurveTo(mx, my + 3, mx + hw, my - smile); g.stroke();
  blobG(0, -0.066, 0.016, 0.006, s3(0.88), 0.3); // under lower lip
  const t = rawTex(c); t.anisotropy = 8;
  return t;
}

const EYE_TEX = {};
function eyeTex(color) {
  if (EYE_TEX[color]) return EYE_TEX[color];
  const c = document.createElement('canvas'); c.width = 256; c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#f2ece4'; g.fillRect(0, 0, 256, 128);
  g.fillStyle = 'rgba(200,120,120,0.25)'; g.fillRect(0, 0, 256, 128);
  g.fillStyle = '#f4efe8'; g.beginPath(); g.ellipse(64, 64, 70, 46, 0, 0, 7); g.fill();
  const gr = g.createRadialGradient(64, 64, 2, 64, 64, 22);
  const col = new THREE.Color(color);
  gr.addColorStop(0, '#' + col.clone().multiplyScalar(0.6).getHexString()); gr.addColorStop(0.7, '#' + col.getHexString()); gr.addColorStop(1, '#1a1410');
  g.fillStyle = gr; g.beginPath(); g.ellipse(64, 64, 20, 22, 0, 0, 7); g.fill();
  g.fillStyle = '#0a0806'; g.beginPath(); g.ellipse(64, 64, 8, 9, 0, 0, 7); g.fill();
  g.fillStyle = 'rgba(255,255,255,0.9)'; g.beginPath(); g.arc(58, 57, 4, 0, 7); g.fill();
  return (EYE_TEX[color] = rawTex(c));
}

function paintTorso(d) {
  const W = 512, H = 512;
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  const base = d.dress || d.jacket || '#333';
  g.fillStyle = base; g.fillRect(0, 0, W, H);
  const R = makeRng(7);
  for (let i = 0; i < 6000; i++) { g.fillStyle = `rgba(${R() > 0.5 ? '255,255,255' : '0,0,0'},${R() * 0.05})`; g.fillRect(R() * W, R() * H, 2, 1); }
  for (let i = 0; i < 18; i++) { g.fillStyle = `rgba(0,0,0,${0.04 + R() * 0.06})`; g.beginPath(); g.ellipse(R() * W, R() * H, 6 + R() * 14, 30 + R() * 60, (R() - 0.5) * 0.8, 0, 7); g.fill(); }
  const cx = W / 2;
  // side shading
  const sg = g.createLinearGradient(0, 0, W, 0);
  sg.addColorStop(0, 'rgba(0,0,0,0.25)'); sg.addColorStop(0.3, 'rgba(0,0,0,0)'); sg.addColorStop(0.7, 'rgba(0,0,0,0)'); sg.addColorStop(1, 'rgba(0,0,0,0.25)');
  g.fillStyle = sg; g.fillRect(0, 0, W, H);
  if (d.dress) {
    g.fillStyle = d.skin; g.beginPath(); g.moveTo(cx - 40, 0); g.lineTo(cx, 70); g.lineTo(cx + 40, 0); g.fill();
    g.strokeStyle = 'rgba(255,255,255,0.35)'; g.lineWidth = 3; g.beginPath(); g.moveTo(cx - 44, 0); g.lineTo(cx, 76); g.lineTo(cx + 44, 0); g.stroke();
    if (d.blouse !== false) for (let y = 110; y < 420; y += 52) { g.fillStyle = 'rgba(255,240,220,0.8)'; g.beginPath(); g.arc(cx, y, 5, 0, 7); g.fill(); }
    g.fillStyle = 'rgba(0,0,0,0.2)'; g.fillRect(0, 300, W, 10);
  } else {
    const shirt = d.shirt || '#eee';
    g.fillStyle = shirt; g.beginPath(); g.moveTo(cx - 34, 0); g.lineTo(cx, 200); g.lineTo(cx + 34, 0); g.fill();
    if (d.tie) { g.fillStyle = d.tie; g.beginPath(); g.moveTo(cx - 7, 8); g.lineTo(cx + 7, 8); g.lineTo(cx + 11, 180); g.lineTo(cx, 200); g.lineTo(cx - 11, 180); g.fill(); g.fillRect(cx - 9, 0, 18, 12); }
    g.strokeStyle = 'rgba(0,0,0,0.45)'; g.lineWidth = 4;
    g.beginPath(); g.moveTo(cx - 36, 0); g.lineTo(cx - 2, 206); g.moveTo(cx + 36, 0); g.lineTo(cx + 2, 206); g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.1)'; g.beginPath(); g.moveTo(cx - 36, 0); g.lineTo(cx - 70, 20); g.lineTo(cx - 6, 210); g.fill(); g.beginPath(); g.moveTo(cx + 36, 0); g.lineTo(cx + 70, 20); g.lineTo(cx + 6, 210); g.fill();
    if (!d.buttons) for (const y of [250, 330, 410]) { g.fillStyle = 'rgba(0,0,0,0.6)'; g.beginPath(); g.arc(cx, y, 6, 0, 7); g.fill(); }
    g.strokeStyle = 'rgba(0,0,0,0.25)'; g.lineWidth = 2; g.beginPath(); g.moveTo(cx, 206); g.lineTo(cx, H); g.stroke();
  }
  return rawTex(c);
}

let SHADOW_TEX;
function shadowTex() {
  if (SHADOW_TEX) return SHADOW_TEX;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d'); const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(0,0,0,0.55)'); gr.addColorStop(0.6, 'rgba(0,0,0,0.25)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  return (SHADOW_TEX = new THREE.CanvasTexture(c));
}

// ------------------------------------------------------------ head
function buildHead(d, seed, P) {
  const head = new THREE.Group();
  const skinM = M(d.skin || '#e5b994', { rough: 0.55 });
  const geo = new THREE.SphereGeometry(HEAD_R, 128, 96);
  const pos = geo.attributes.position;
  const hw = d.headW || 1;
  const U = (mx, my) => { const x = mx / (HEAD_R * HSX), y = my / (HEAD_R * HSY); return [x, y, Math.sqrt(Math.max(0, 1 - x * x - y * y))]; };
  // facial sculpt: [x, y (metres from head centre), amplitude, sigma (unit sphere)]
  const nose = d.nose || 1;
  const bumps = [
    [0.031, 0.012, -0.075, 0.15], [-0.031, 0.012, -0.075, 0.15],   // eye sockets
    [0.03, 0.036, 0.03, 0.14], [-0.03, 0.036, 0.03, 0.14],         // brow ridge
    [0, 0.006, 0.06 * nose, 0.085], [0, -0.008, 0.12 * nose, 0.08], [0, -0.019, 0.2 * nose, 0.085], // nose bridge -> tip
    [0.011, -0.024, 0.08, 0.075], [-0.011, -0.024, 0.08, 0.075], // nostril wings
    [0.046, -0.014, 0.05, 0.2], [-0.046, -0.014, 0.05, 0.2],       // cheekbones
    [0, -0.046, 0.04, 0.12], [0, -0.065, -0.02, 0.07],              // lips, groove under lip
    [0, -0.088, 0.06, 0.16],                                        // chin
  ].map(([mx, my, a, sg]) => [U(mx, my), a, sg]);
  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i) / HEAD_R, y = pos.getY(i) / HEAD_R, z = pos.getZ(i) / HEAD_R;
    let r = 1;
    if (z > 0) for (const [[bx, by, bz], a, sg] of bumps) { const dd = (x - bx) ** 2 + (y - by) ** 2 + (z - bz) ** 2; r += a * Math.exp(-dd / (2 * sg * sg)); }
    x *= r; y *= r; z *= r;
    if (y < -0.1) { const k = -y - 0.1; x *= 1 - 0.34 * k; if (z < 0) z *= 1 - 0.45 * k; else z *= 1 - 0.06 * k; }
    if (y > 0.55) y = 0.55 + (y - 0.55) * 0.9;
    if (z > 0.55 && r < 1.02) z = 0.55 + (z - 0.55) * 0.8;
    if (z < 0) z *= 1.07;
    pos.setXYZ(i, x * HEAD_R * HSX * hw, y * HEAD_R * HSY, z * HEAD_R * HSZ);
  }
  geo.computeVertexNormals();
  const skull = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: paintFace(d, seed), roughness: 0.55 }));
  skull.position.y = HEAD_C; head.add(skull);
  head.updateMatrixWorld(true);
  const rc = new THREE.Raycaster();
  const surf = (x, y) => {
    rc.set(new THREE.Vector3(x, HEAD_C + y, 1), new THREE.Vector3(0, 0, -1));
    const h = rc.intersectObject(skull)[0];
    return h ? { p: h.point.clone(), n: h.face.normal.clone().normalize() } : { p: new THREE.Vector3(x, HEAD_C + y, 0.09), n: new THREE.Vector3(0, 0, 1) };
  };
  const at = (obj, s, off = 0) => { obj.position.copy(s.p).addScaledVector(s.n, off); head.add(obj); return obj; };

  // eyes (eyeball + upper lid that blinks)
  P.eyes = []; P.lids = [];
  const es = d.eyes || 1;
  for (const sx of [-1, 1]) {
    const s = surf(0.031 * sx, 0.012);
    const eg = new THREE.Group(); at(eg, s, -0.0042);
    const ball_ = new THREE.Mesh(new THREE.SphereGeometry(0.0112 * es, 20, 14), new THREE.MeshStandardMaterial({ map: eyeTex(d.eyeColor || '#5a4030'), roughness: 0.15 }));
    eg.add(ball_);
    const lid = new THREE.Mesh(new THREE.SphereGeometry(0.0121 * es, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), skinM);
    eg.add(lid); lid.rotation.x = -0.55;
    const low = new THREE.Mesh(new THREE.SphereGeometry(0.0119 * es, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), skinM);
    low.rotation.x = Math.PI + 0.4; eg.add(low);
    P.eyes.push(eg); P.lids.push(lid);
  }
  // brows
  P.brows = [];
  const browM = M(shade(d.brow || d.hair || '#333', 0.8), { rough: 0.8 });
  for (const sx of [-1, 1]) {
    const s = surf(0.032 * sx, 0.034);
    const b = new THREE.Mesh(new THREE.CapsuleGeometry(0.0032 * (d.female ? 0.8 : 1.15), 0.024, 3, 6), browM);
    b.rotation.z = Math.PI / 2 + 0.12 * sx;
    at(b, s, 0.002); b.userData.y = b.position.y; b.userData.rz = b.rotation.z; b.userData.sx = sx;
    P.brows.push(b);
  }
  // nose
  // ears
  for (const sx of [-1, 1]) { const e = ball(head, 0.022, skinM, sx * HEAD_R * HSX * 0.96 * (d.headW || 1), HEAD_C - 0.004, -0.008, 8, 6); e.scale.set(0.42, 1, 0.72); }
  // mouth opening (for talking)
  const ms = surf(0, -0.051);
  const mg = new THREE.Group(); at(mg, ms, 0.0016 + (d.beard ? 0.004 : 0));
  mg.lookAt(mg.position.clone().add(ms.n));
  const hole = new THREE.Mesh(new THREE.CircleGeometry(0.0165, 18), Basic('#2a0c0c')); mg.add(hole);
  const teeth = new THREE.Mesh(new THREE.PlaneGeometry(0.02, 0.0045), Basic('#e8e2d6')); teeth.position.z = 0.0003; mg.add(teeth);
  P.mouthHole = hole; P.teeth = teeth;
  // glasses
  if (d.glasses) {
    const gm = M(d.glasses, { shininess: 80, metalness: 0.6 });
    for (const sx of [-1, 1]) {
      const s = surf(0.031 * sx, 0.012);
      const r = new THREE.Mesh(new THREE.TorusGeometry(0.0175, 0.0013, 6, 24), gm); at(r, s, 0.012);
      const lens = new THREE.Mesh(new THREE.CircleGeometry(0.0172, 20), new THREE.MeshStandardMaterial({ color: '#ffffff', transparent: true, opacity: 0.12, roughness: 0.05 })); at(lens, s, 0.0118);
      const tmp = new THREE.Mesh(new THREE.CylinderGeometry(0.0011, 0.0011, 0.095, 5), gm); tmp.rotation.x = Math.PI / 2;
      tmp.position.set(0.048 * sx, HEAD_C + 0.014, s.p.z - 0.045); head.add(tmp);
    }
    const br = new THREE.Mesh(new THREE.CylinderGeometry(0.0012, 0.0012, 0.026, 5), gm); br.rotation.z = Math.PI / 2; at(br, surf(0, 0.016), 0.006);
  }
  // facial hair
  const hairM = M(d.hair || '#3a2a1e', { map: Tex.hair([1, 1]), rough: 0.55, flat: true });
  if (d.moustache) { const m = blob(head, 0.017, M(d.moustache, { map: Tex.hair([1, 1]), rough: 0.6, flat: true }), seed + 3, 0.14, 1); m.scale.set(2.1, 0.62, 0.85); at(m, surf(0, -0.034), 0.004); head.add(m); }
  if (d.beard) { const b = blob(head, 0.064, M(d.beard, { map: Tex.hair([1, 1]), rough: 0.6, flat: true }), seed + 4, 0.12); b.position.set(0, HEAD_C - 0.056, 0.022); b.scale.set(1.05, 0.82, 0.95); }

  // the chunky "box" hair, crumpled low-poly with strand texture
  const hairG = new THREE.Group(); hairG.position.set(0, HEAD_C + 0.007, -0.006); hairG.scale.set(0.84 * (d.headW || 1), 0.86, 0.84); head.add(hairG);
  const hs = d.hairStyle || 'short';
  const Hb = (r, x, y, z, sx = 1, sy = 1, sz = 1, j = 0.16, det = 1) => { const b = blob(hairG, r, hairM, seed * 13 + x * 100 + y * 1000 + z * 77 | 0, j, det); b.position.set(x, y - 0.12, z); b.scale.set(sx, sy, sz); return b; };
  if (hs === 'short') { Hb(0.125, 0, 0.17, -0.032, 1.0, 0.84, 1.05); }
  if (hs === 'tucked') { Hb(0.12, 0, 0.16, -0.035, 1.0, 0.85, 1.0); }
  if (hs === 'balding') { Hb(0.055, 0.1, 0.12, -0.035, 0.8, 1.2, 1.2, 0.2, 0); Hb(0.055, -0.1, 0.12, -0.035, 0.8, 1.2, 1.2, 0.2, 0); Hb(0.1, 0, 0.11, -0.07, 1.1, 0.8, 0.7); Hb(0.1, 0, 0.225, -0.025, 0.95, 0.28, 1.0, 0.1); }
  if (hs === 'bob') { Hb(0.14, 0, 0.17, -0.03, 1.06, 0.92, 1.06, 0.13); Hb(0.075, 0.105, 0.06, -0.015, 0.7, 1.45, 0.95); Hb(0.075, -0.105, 0.06, -0.015, 0.7, 1.45, 0.95); Hb(0.11, 0, 0.07, -0.075, 1.15, 1.2, 0.7); Hb(0.08, 0, 0.215, 0.07, 1.45, 0.45, 0.6, 0.12); }
  if (hs === 'bun') { Hb(0.13, 0, 0.17, -0.03, 1.02, 0.86, 1.06, 0.1); Hb(0.095, 0, 0.3, -0.04, 1.05, 0.95, 1.05, 0.12); }
  if (hs === 'updo') { Hb(0.135, 0, 0.185, -0.025, 1.08, 0.9, 1.08, 0.1); Hb(0.085, 0, 0.29, -0.03, 1.25, 0.7, 1.05, 0.12); Hb(0.07, 0, 0.21, -0.12, 1.0, 1.0, 0.8, 0.14); }
  // hats
  const HAT = (y) => y - 0.12;
  if (d.hat === 'bowler') {
    const hm = M(d.hatColor || '#222', { rough: 0.5 });
    cyl(hairG, 0.165, 0.165, 0.012, 10, hm, 0, HAT(0.245), -0.01);
    const c = ball(hairG, 0.118, hm, 0, HAT(0.268), -0.01, 10, 7); c.scale.set(1, 0.88, 1.05);
    cyl(hairG, 0.119, 0.119, 0.02, 10, M('#0c0c0c'), 0, HAT(0.258), -0.01);
  }
  if (d.hat === 'cap') {
    const hm = M(d.hatColor || '#555', { map: Tex.fabric([2, 2]) });
    const c = ball(hairG, 0.135, hm, 0, HAT(0.24), -0.01, 10, 7); c.scale.set(1.02, 0.42, 1.08);
    box(hairG, 0.17, 0.012, 0.09, hm, 0, HAT(0.228), 0.11).rotation.x = 0.15;
  }
  if (d.hat === 'captain') {
    const hm = M(d.hatColor || '#fff', { rough: 0.6 });
    cyl(hairG, 0.14, 0.125, 0.07, 10, hm, 0, HAT(0.29), -0.01);
    cyl(hairG, 0.124, 0.124, 0.04, 10, M('#111'), 0, HAT(0.25), -0.01);
    box(hairG, 0.17, 0.01, 0.085, M('#0d0d0d', { shininess: 80 }), 0, HAT(0.235), 0.1).rotation.x = 0.22;
    box(hairG, 0.04, 0.03, 0.01, M('#d9b84a', { shininess: 80, metalness: 0.7 }), 0, HAT(0.255), 0.125);
  }
  if (d.headphones) {
    const hm = M('#2a2a2a', { rough: 0.4 });
    const band = new THREE.Mesh(new THREE.TorusGeometry(0.135, 0.01, 6, 20, Math.PI), hm); band.position.set(0, 0.01, -0.01); hairG.add(band);
    for (const sx of [-1, 1]) { const cup = cyl(hairG, 0.04, 0.04, 0.03, 8, hm, 0.13 * sx, 0.0, -0.01); cup.rotation.z = Math.PI / 2; }
  }
  return head;
}

// ------------------------------------------------------------ body
function makeCharacter(id, d, seed) {
  const W = d.width || 1;
  const fem = !!d.female;
  const skinM = M(d.skin || '#e5b994', { rough: 0.55 });
  const fab = Tex.fabric([2, 2]);
  const clothM = M(d.dress || d.jacket || '#333', { map: fab, rough: d.dress ? 0.55 : 0.85 });
  const pantsM = M(d.dress ? shade(d.skin || '#ddd', 0.85) : (d.pants || '#2a2a2a'), { map: fab, rough: 0.85 });
  const shoeM = M('#17110d', { rough: 0.3 });
  const root = new THREE.Group(); root.name = id;
  const P = { root };

  const sh = new THREE.Mesh(new THREE.PlaneGeometry(0.8 * W, 0.8 * W), new THREE.MeshBasicMaterial({ map: shadowTex(), transparent: true, depthWrite: false }));
  sh.rotation.x = -Math.PI / 2; sh.position.y = 0.006; root.add(sh); P.shadow = sh;

  const hips = new THREE.Group(); hips.position.y = LEG; root.add(hips); P.hips = hips;
  const pelvis = ball(hips, 0.1, d.dress ? clothM : pantsM, 0, 0.0, 0, 10, 8); pelvis.scale.set(1.6 * W, 0.95, 1.1);
  for (const side of ['L', 'R']) {
    const sx = side === 'L' ? 1 : -1;
    const leg = new THREE.Group(); leg.position.set(0.085 * sx * W, 0, 0); hips.add(leg);
    capsule(leg, 0.068 * Math.sqrt(W), THIGH - 0.12, pantsM, 0, -THIGH / 2, 0);
    const knee = new THREE.Group(); knee.position.y = -THIGH; leg.add(knee);
    capsule(knee, 0.052, SHIN - 0.1, pantsM, 0, -SHIN / 2 + 0.01, 0);
    const shoe = ball(knee, 0.052, shoeM, 0, -SHIN + 0.03, 0.045, 10, 8); shoe.scale.set(0.85, 0.62, 1.9);
    P['thigh' + side] = leg; P['shin' + side] = knee;
  }
  if (d.dress) {
    const pts = [[0.32, -(LEG - 0.08)], [0.29, -0.6], [0.23, -0.3], [0.185, -0.08], [0.165, 0.05]].map(([r, y]) => new THREE.Vector2(r * W, y));
    const sk = new THREE.Mesh(new THREE.LatheGeometry(pts, 28), M(d.dress, { map: Tex.fabric([3, 2]), rough: 0.55, side: THREE.DoubleSide }));
    hips.add(sk); P.skirt = sk;
  }
  if (d.coat) {
    const pts = [[0.22, -0.48], [0.2, -0.2], [0.18, 0.02]].map(([r, y]) => new THREE.Vector2(r * W, y));
    const ct = new THREE.Mesh(new THREE.LatheGeometry(pts, 24), M(d.coat, { map: fab, side: THREE.DoubleSide })); ct.scale.z = 0.72; hips.add(ct);
  }

  const chair = new THREE.Group(); root.add(chair); P.chair = chair; chair.visible = false;
  const wood = M('#4a2c18', { map: Tex.wood([1, 1], '#5a3820'), rough: 0.5 });
  box(chair, 0.46, 0.05, 0.44, wood, 0, 0.45, -0.05);
  box(chair, 0.46, 0.6, 0.05, wood, 0, 0.75, -0.27);
  for (const [x, z] of [[-0.2, 0.14], [0.2, 0.14], [-0.2, -0.24], [0.2, -0.24]]) cyl(chair, 0.02, 0.02, 0.45, 8, wood, x, 0.225, z);

  const torso = new THREE.Group(); hips.add(torso); P.torso = torso;
  const prof = fem
    ? [[0.13, -0.03], [0.15, 0.06], [0.125, 0.2], [0.15, 0.32], [0.165, 0.4], [0.16, 0.48], [0.13, 0.54], [0.06, 0.585]]
    : [[0.14, -0.03], [0.15, 0.08], [0.15, 0.2], [0.162, 0.33], [0.175, 0.44], [0.165, 0.51], [0.12, 0.56], [0.055, 0.59]];
  const tg = new THREE.LatheGeometry(prof.map(([r, y]) => new THREE.Vector2(r, y)), 28, Math.PI, Math.PI * 2);
  const torsoMesh = new THREE.Mesh(tg, new THREE.MeshStandardMaterial({ map: paintTorso(d), roughness: d.dress ? 0.55 : 0.85 }));
  torsoMesh.scale.set(W * 0.93, 1, 0.64 * Math.min(W, 1.2)); torso.add(torsoMesh);
  const front = 0.115 * Math.min(W, 1.2);
  if (!d.dress) { const col = cyl(torso, 0.05, 0.058, 0.035, 10, M(d.shirt || '#eee', { rough: 0.7 }), 0, 0.57, 0.005); }
  if (d.buttons) for (let i = 0; i < 4; i++) for (const sx of [-1, 1]) ball(torso, 0.011, M(d.buttons, { shininess: 80, metalness: 0.7 }), 0.075 * sx, 0.17 + i * 0.085, front - 0.004 + (i > 2 ? -0.01 : 0), 6, 5);
  if (d.pearls) for (let i = 0; i < 13; i++) { const a = (i / 12 - 0.5) * 2.4; ball(torso, 0.0095, M('#f4f0e6', { shininess: 95 }), Math.sin(a) * 0.075, 0.53 - Math.cos(a) * 0.045, Math.cos(a) * 0.075 + 0.015, 6, 5); }
  if (d.brooch) {
    const b = ball(torso, 0.017, M(d.brooch, { emissive: d.broochGlow ? d.brooch : '#000', shininess: 95, metalness: 0.3 }), -0.07 * W, 0.42, front - 0.006, 8, 6);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.019, 0.004, 6, 16), M('#c9a24a', { shininess: 90, metalness: 0.8 })); rim.position.copy(b.position); torso.add(rim);
    P.brooch = b;
  }
  if (d.fur) {
    const fm = M(d.fur, { map: Tex.hair([1, 1]), rough: 0.9, flat: true });
    const st = new THREE.Mesh(new THREE.TorusGeometry(0.115, 0.035, 10, 26), M(d.fur, { map: Tex.hair([4, 1]), rough: 0.9 }));
    st.rotation.x = Math.PI / 2 - 0.25; st.scale.set(1.05, 0.72, 1); st.position.set(0, 0.52, 0.0); torso.add(st);
  }
  cyl(torso, 0.042, 0.048, 0.11, 10, skinM, 0, 0.585, 0);
  const headPivot = new THREE.Group(); headPivot.position.y = 0.6; torso.add(headPivot); P.head = headPivot;
  headPivot.add(buildHead(d, seed, P)); headPivot.children[0].scale.setScalar(1.15);

  for (const side of ['L', 'R']) {
    const sx = side === 'L' ? 1 : -1;
    const arm = new THREE.Group(); arm.position.set(0.178 * W * sx, 0.49, 0); torso.add(arm);
    ball(arm, 0.047, clothM, 0, -0.01, 0, 8, 6);
    capsule(arm, 0.04, 0.21, clothM, 0, -0.14, 0);
    const el = new THREE.Group(); el.position.y = -0.29; arm.add(el);
    capsule(el, 0.035, 0.2, clothM, 0, -0.125, 0);
    if (!d.dress) cyl(el, 0.036, 0.036, 0.02, 10, M(d.shirt || '#eee'), 0, -0.24, 0);
    const hand = new THREE.Group(); hand.position.y = -0.29; el.add(hand);
    const palm = capsule(hand, 0.024, 0.045, skinM, 0, 0.0, 0); palm.scale.set(1, 1, 0.55);
    const th = capsule(hand, 0.011, 0.03, skinM, 0.022 * -sx * -1, 0.01, 0.018); th.rotation.z = 0.5 * sx;
    P['arm' + side] = arm; P['fore' + side] = el; P['hand' + side] = hand;
  }

  // props
  P.props = {};
  const lantern = new THREE.Group(); P.handR.add(lantern); lantern.position.set(0, -0.12, 0.02);
  box(lantern, 0.1, 0.02, 0.1, M('#222', { metalness: 0.6, rough: 0.4 }), 0, 0.08, 0); box(lantern, 0.1, 0.02, 0.1, M('#222', { metalness: 0.6, rough: 0.4 }), 0, -0.08, 0);
  box(lantern, 0.085, 0.14, 0.085, Basic('#ffcf87'), 0, 0, 0);
  const ll = new THREE.PointLight('#ffa040', 0.8, 4.5, 1.5); ll.position.set(0, 0, 0.05); lantern.add(ll);
  P.props.lantern = lantern;
  const bar = new THREE.Group(); P.handR.add(bar); cyl(bar, 0.012, 0.012, 0.7, 6, M('#3a3a3c', { metalness: 0.7, rough: 0.4 }), 0, -0.22, 0.03); P.props.crowbar = bar;
  const bino = new THREE.Group(); P.head.add(bino); bino.position.set(0, HEAD_C + 0.012, 0.15);
  for (const sx of [-1, 1]) { const b = cyl(bino, 0.022, 0.026, 0.1, 8, M('#151515', { shininess: 60 }), 0.032 * sx, 0, 0); b.rotation.x = Math.PI / 2; }
  P.props.binoculars = bino;
  const paper = new THREE.Group(); P.handR.add(paper); const pp = plane(paper, 0.16, 0.22, M('#efe8d4', { side: THREE.DoubleSide }), 0, -0.05, 0.05); pp.rotation.x = -1.1; P.props.paper = paper;
  for (const k in P.props) P.props[k].visible = false;

  root.traverse(o => { if (o.isMesh && !(o.material && o.material.isMeshBasicMaterial)) { o.castShadow = true; o.receiveShadow = true; } });
  root.scale.setScalar(d.height || 1);
  return { id, def: d, P, seed, talkSmooth: 0 };
}

// ------------------------------------------------------------------ poses
const POSE_KEYS = ['hipY', 'rootY', 'torsoX', 'torsoY', 'torsoZ', 'headX', 'headY', 'headZ', 'aLx', 'aLz', 'fL', 'aRx', 'aRz', 'fR', 'tL', 'sL', 'tR', 'sR', 'mouth', 'brow', 'eyes', 'skirt', 'lookAmt'];

function basePose() {
  const p = {}; POSE_KEYS.forEach(k => p[k] = 0);
  p.aLz = 0.1; p.aRz = -0.1; p.fL = -0.15; p.fR = -0.15; p.skirt = 1; p.lookAmt = 1;
  return p;
}

function poseFor(anim, t, ch) {
  const p = basePose();
  const s = ch.seed;
  const sit = () => { p.hipY = 0.47 - LEG; p.tL = p.tR = -1.5; p.sL = p.sR = 1.5; p.aLx = p.aRx = -0.72; p.fL = p.fR = -0.8; p.aLz = -0.05; p.aRz = 0.05; p.torsoX = 0.06; p.skirt = 0.5; };
  const kneel = () => { p.hipY = 0.47 - LEG; p.tL = -1.45; p.sL = 1.45; p.tR = -0.15; p.sR = 1.6; };
  switch (anim) {
    case 'idle': case 'nod':
      p.torsoZ = 0.02 * Math.sin(t * 0.7 + s); p.headX = 0.03 * Math.sin(t * 0.9 + s);
      if (anim === 'nod') p.headX += 0.1 * Math.max(0, Math.sin(t * 3.2));
      break;
    case 'nervous':
      p.aLx = p.aRx = -0.55; p.aLz = -0.3; p.aRz = 0.3; p.fL = p.fR = -1.25; p.lookAmt = 0;
      p.headY = 0.75 * Math.sin(t * 1.1 + s) ; p.headX = 0.05; p.brow = 0.5;
      break;
    case 'sit': sit(); p.headX = 0.03 * Math.sin(t * 0.8 + s); break;
    case 'sit_shocked': sit(); p.torsoX = -0.12; p.headX = -0.06; p.mouth = 0.7; p.brow = 1; p.aRx = -0.6; p.fR = -1.5; p.aRz = 0.3; break;
    case 'shocked': p.torsoX = -0.1; p.mouth = 0.8; p.brow = 1; p.aLx = p.aRx = -0.55; p.aLz = 0.35; p.aRz = -0.35; p.fL = p.fR = -1.2; break;
    case 'sad': p.headX = 0.32; p.torsoX = 0.1; p.aLz = 0.04; p.aRz = -0.04; p.fL = p.fR = -0.05; p.brow = 0.45; p.eyes = 0.45; p.lookAmt = 0.3; break;
    case 'admire': p.aRx = -0.55; p.aRz = 0.32; p.fR = -1.45; p.aLz = 0.15; p.headX = -0.1; p.headZ = 0.1; p.eyes = 0.3; p.torsoY = 0.15 * Math.sin(t * 0.6); break;
    case 'kneel_dig': kneel(); p.torsoX = 0.55; p.headX = 0.3; p.lookAmt = 0;
      p.aLx = -1.0 + 0.28 * Math.sin(t * 4.5 + 1); p.aRx = -1.05 + 0.3 * Math.sin(t * 4.5); p.fL = p.fR = -0.35; p.aLz = -0.1; p.aRz = 0.1; break;
    case 'kneel_shocked': kneel(); p.torsoX = -0.05; p.headX = 0.12; p.mouth = 0.7; p.brow = 1; p.lookAmt = 0; p.aLx = -0.5; p.aLz = 0.3; p.fL = -0.6; p.aRx = -1.25; p.fR = -0.75; p.aRz = 0.05; break;
    case 'binoculars': p.aLx = p.aRx = -1.3; p.aLz = -0.42; p.aRz = 0.42; p.fL = p.fR = -1.45; p.headX = -0.04; p.headY = 0.12 * Math.sin(t * 0.5); p.lookAmt = 0.2; break;
    case 'hold_paper': p.aRx = -0.75; p.aRz = 0.2; p.fR = -0.9; p.headX = 0.18; break;
    case 'type': sit(); p.headX = 0.2; p.aRx = -0.62; p.fR = -0.85; p.aLx = -0.62; p.fL = -0.85; p.lookAmt = 0; break;
    case 'walk': {
      const ph = ch.walkPhase || 0;
      p.tL = -0.42 * Math.sin(ph); p.tR = 0.42 * Math.sin(ph);
      p.sL = 0.15 + 0.5 * Math.max(0, -Math.sin(ph + 0.6)); p.sR = 0.15 + 0.5 * Math.max(0, Math.sin(ph + 0.6));
      p.aLx = 0.32 * Math.sin(ph); p.aRx = -0.32 * Math.sin(ph); p.fL = p.fR = -0.3;
      p.rootY = 0.022 * Math.abs(Math.cos(ph)); p.torsoX = 0.04;
      break;
    }
  }
  return p;
}

function lerpPose(a, b, k) { const o = {}; POSE_KEYS.forEach(n => o[n] = a[n] + (b[n] - a[n]) * k); return o; }

function applyPose(ch, p, extra) {
  const P = ch.P;
  P.hips.position.y = LEG + p.hipY + p.rootY;
  P.torso.rotation.set(p.torsoX, p.torsoY + (extra.torsoYaw || 0), p.torsoZ);
  P.head.rotation.set(p.headX + (extra.headPitch || 0), p.headY + (extra.headYaw || 0), p.headZ);
  P.armL.rotation.set(p.aLx, 0, p.aLz); P.foreL.rotation.set(p.fL, 0, 0);
  P.armR.rotation.set(p.aRx, 0, p.aRz); P.foreR.rotation.set(p.fR, 0, 0);
  P.thighL.rotation.x = p.tL; P.shinL.rotation.x = p.sL;
  P.thighR.rotation.x = p.tR; P.shinR.rotation.x = p.sR;
  if (P.skirt) { P.skirt.scale.y = p.skirt; P.skirt.rotation.x = p.skirt < 0.8 ? -0.5 : 0; }
  // mouth: opening grows with the voice
  const open = Math.max(p.mouth, extra.talk || 0);
  P.mouthHole.visible = open > 0.04;
  P.mouthHole.scale.set(1 - open * 0.12, Math.max(0.01, open * 0.62), 1);
  P.teeth.visible = open > 0.22;
  P.teeth.position.y = 0.0165 * open * 0.62 - 0.0028;
  // lids: blink / sleepy / wide
  const shut = Math.max(p.eyes, extra.blink ? 1 : 0);
  const openAng = -0.32 - p.brow * 0.35;
  P.lids.forEach(l => l.rotation.x = openAng + (1.15 - openAng) * shut);
  // eyes follow the look target a little more than the head does
  P.eyes.forEach(e => e.rotation.set((extra.eyePitch || 0), (extra.eyeYaw || 0), 0));
  P.brows.forEach(b => { b.position.y = b.userData.y + p.brow * 0.005 - (extra.frown || 0) * 0.002; b.rotation.z = b.userData.rz - b.userData.sx * p.brow * 0.12; });
  P.chair.visible = !!extra.chair;
}
