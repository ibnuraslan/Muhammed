// kits/investigation.js - evidence board, case files, vintage maps with animated routes, title cards.
import { THREE, toon, basic, mesh, box, cyl, sphere, canvasTex, noiseTex, textPlane, rng, lerp, clamp, ease } from '../engine.js';
import { portraitCanvas } from '../cast.js';

const texFrom = (canvas) => { const t = new THREE.CanvasTexture(canvas); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };

// ---------------------------------------------------------------- evidence board
// Board in its local XY plane facing +z, centred on `pos`. Item positions `at` are in board units from the centre.
// items: { type:'photo', design, label, caption, at:[x,y] } | { type:'note', text, at, color } | { type:'paper', canvas|text, at, size }
// links: [[i, j], ...] red strings between item pins; animate with board.userData.setStrings(0..1)
export function evidenceBoard(S, { pos = [0, 3.5, -7.6], rotY = 0, w = 6, h = 3.6, items = [], links = [], seed = 3 } = {}) {
  const R = rng(seed), g = new THREE.Group();
  const cork = noiseTex('#b0814f', ['#9a6c3d', '#c49460', '#8a5d31', '#d2a675'], 6000, 512, [2, 1.3], seed, [1, 3]);
  g.add(box(w, h, 0.08, toon(0xffffff, { map: cork }), [0, 0, 0]));
  const frame = toon(0x4a2e1a);
  g.add(box(w + 0.25, 0.14, 0.14, frame, [0, h / 2, 0.03])); g.add(box(w + 0.25, 0.14, 0.14, frame, [0, -h / 2, 0.03]));
  g.add(box(0.14, h, 0.14, frame, [-w / 2, 0, 0.03])); g.add(box(0.14, h, 0.14, frame, [w / 2, 0, 0.03]));
  const pins = [], parts = [];
  items.forEach((it, i) => {
    let canvas, size = it.size || [0.9, 1.1];
    if (it.type === 'photo') {
      const p = portraitCanvas(it.design, { label: it.label || '', pose: it.pose || {} });
      canvas = document.createElement('canvas'); canvas.width = 440; canvas.height = 560;
      const c = canvas.getContext('2d'); c.fillStyle = '#f7f4ec'; c.fillRect(0, 0, 440, 560); c.drawImage(p, 20, 20, 400, 460);
      c.fillStyle = '#222'; c.font = '700 34px "Comic Sans MS", Display, sans-serif'; c.textAlign = 'center'; c.fillText(it.caption || '', 220, 530, 400);
      size = it.size || [0.85, 1.08];
    } else if (it.type === 'note') {
      canvas = document.createElement('canvas'); canvas.width = 300; canvas.height = 300;
      const c = canvas.getContext('2d'); c.fillStyle = it.color || '#ffe36e'; c.fillRect(0, 0, 300, 300);
      c.fillStyle = 'rgba(0,0,0,0.08)'; c.fillRect(0, 0, 300, 40);
      c.fillStyle = '#1d1d1d'; c.textAlign = 'center'; c.textBaseline = 'middle';
      const lines = String(it.text).split('\n'); const fs = it.fontSize || (lines.length > 2 ? 44 : 56);
      c.font = `900 ${fs}px Display, sans-serif`;
      lines.forEach((ln, k) => c.fillText(ln, 150, 150 + (k - (lines.length - 1) / 2) * fs * 1.15, 270));
      size = it.size || [0.6, 0.6];
    } else {
      canvas = it.canvas;
    }
    const m = new THREE.Mesh(new THREE.PlaneGeometry(...size), new THREE.MeshBasicMaterial({ map: texFrom(canvas), toneMapped: false }));
    m.position.set(it.at[0], it.at[1], 0.06 + i * 0.002); m.rotation.z = it.rot ?? (R() - 0.5) * 0.12;
    g.add(m); parts.push(m);
    const pin = sphere(0.045, toon(0xd4352b), [it.at[0], it.at[1] + size[1] / 2 - 0.08, 0.12], { seg: 10 });
    g.add(pin); pins.push(pin.position.clone());
  });
  // strings (thin red cylinders) that grow from pin to pin
  const strM = toon(0xc0262d);
  const strings = links.map(([a, b]) => {
    const A = pins[a], B = pins[b], len = A.distanceTo(B);
    const geo = new THREE.CylinderGeometry(0.012, 0.012, 1, 6); geo.translate(0, 0.5, 0);
    const s = new THREE.Mesh(geo, strM); s.position.copy(A); s.position.z = 0.13;
    s.rotation.z = Math.atan2(B.y - A.y, B.x - A.x) - Math.PI / 2; s.userData.len = len; s.scale.y = 0.0001; g.add(s); return s;
  });
  g.position.set(...pos); g.rotation.y = rotY; S.add(g);
  g.userData.parts = parts;
  g.userData.setStrings = (k) => strings.forEach((s, i) => {
    const n = strings.length, local = clamp((k * n - i) / 1.0);
    s.scale.y = Math.max(0.0001, ease.out(local) * s.userData.len);
  });
  return g;
}

// ---------------------------------------------------------------- vintage map with an animated route
// draw(g, w, h) paints the geography. route: [[u,v], ...] in 0..1 map coords (v down).
// .userData.setProgress(k) draws the route up to k (0..1); markers appear when the route passes them.
export function mapPlane({ w = 2.4, h = 1.8, draw, route = [], markers = [], px = 1280 } = {}) {
  const ph = Math.round(px * h / w);
  const base = document.createElement('canvas'); base.width = px; base.height = ph;
  const bg = base.getContext('2d');
  bg.fillStyle = '#e6d7b4'; bg.fillRect(0, 0, px, ph);
  if (draw) draw(bg, px, ph);
  // paper ageing: stains, edge darkening
  const R = rng(12);
  for (let i = 0; i < 40; i++) { bg.fillStyle = `rgba(110,80,30,${0.03 + R() * 0.05})`; bg.beginPath(); bg.arc(R() * px, R() * ph, 20 + R() * 90, 0, 7); bg.fill(); }
  const vg = bg.createRadialGradient(px / 2, ph / 2, ph * 0.3, px / 2, ph / 2, px * 0.7); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(70,45,10,0.45)');
  bg.fillStyle = vg; bg.fillRect(0, 0, px, ph);
  const tex = canvasTex(px, ph, () => {});
  const ctx = tex.userData.ctx;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
  // route length for progress
  const P = route.map(([u, v]) => [u * px, v * ph]);
  const segs = []; let total = 0;
  for (let i = 1; i < P.length; i++) { const d = Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); segs.push(d); total += d; }
  m.userData.setProgress = (k) => {
    ctx.drawImage(base, 0, 0);
    let left = clamp(k) * total;
    ctx.strokeStyle = '#c0262d'; ctx.lineWidth = px * 0.006; ctx.setLineDash([px * 0.014, px * 0.009]); ctx.lineCap = 'round';
    ctx.beginPath(); if (P.length) ctx.moveTo(...P[0]);
    let tip = P[0];
    for (let i = 1; i < P.length && left > 0; i++) {
      const f = Math.min(1, left / segs[i - 1]);
      tip = [lerp(P[i - 1][0], P[i][0], f), lerp(P[i - 1][1], P[i][1], f)]; ctx.lineTo(...tip); left -= segs[i - 1];
    }
    ctx.stroke(); ctx.setLineDash([]);
    if (tip && k > 0) { ctx.fillStyle = '#c0262d'; ctx.beginPath(); ctx.arc(tip[0], tip[1], px * 0.009, 0, 7); ctx.fill(); }
    for (const mk of markers) {
      if (k < mk.at) continue;
      const a = clamp((k - mk.at) / 0.08), x = mk.uv[0] * px, y = mk.uv[1] * ph;
      ctx.globalAlpha = a;
      ctx.font = `900 ${Math.round(px * (mk.size || 0.05))}px Display, sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.lineWidth = px * 0.006; ctx.strokeStyle = '#f4ead2'; ctx.strokeText(mk.text, x, y); ctx.fillStyle = mk.color || '#c0262d'; ctx.fillText(mk.text, x, y);
      ctx.globalAlpha = 1;
    }
    tex.needsUpdate = true;
  };
  m.userData.setProgress(0);
  return m;
}
// helper for map drawers: filled land polygon with a hatched coastline
export function land(g, w, h, pts, { fill = '#cdb98b', ink = '#5a4630' } = {}) {
  g.beginPath(); pts.forEach(([u, v], i) => (i ? g.lineTo(u * w, v * h) : g.moveTo(u * w, v * h))); g.closePath();
  g.fillStyle = fill; g.fill(); g.lineWidth = w * 0.004; g.strokeStyle = ink; g.stroke();
  g.save(); g.clip(); g.strokeStyle = 'rgba(90,70,48,0.18)'; g.lineWidth = 2;
  for (let x = -h; x < w; x += 14) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x + h, h); g.stroke(); }
  g.restore();
}
export function label(g, w, h, text, u, v, { size = 0.028, color = '#4a3824', italic = false, spacing = 0 } = {}) {
  g.font = `${italic ? 'italic ' : ''}700 ${Math.round(w * size)}px Georgia, serif`; g.fillStyle = color; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(text.split('').join(spacing ? ' ' : ''), u * w, v * h);
}

// ---------------------------------------------------------------- case file folder with an animated stamp
export function caseFile({ title = 'CASE FILE', lines = [], stamp = 'UNSOLVED', w = 1.3, h = 1.7 } = {}) {
  const g = new THREE.Group();
  const folder = canvasTex(700, 900, (c, W, H) => {
    c.fillStyle = '#d6b475'; c.fillRect(0, 60, W, H - 60); c.fillRect(30, 0, 260, 80);
    c.fillStyle = '#f3efe3'; c.fillRect(50, 110, W - 100, H - 170);
    c.fillStyle = '#1d1d1d'; c.textAlign = 'center'; c.font = '700 30px "Courier New", monospace';
    c.fillText('FEDERAL BUREAU OF INVESTIGATION', W / 2, 175, W - 140);
    c.font = '900 64px "Courier New", monospace'; c.fillText(title, W / 2, 270, W - 140);
    c.font = '700 32px "Courier New", monospace';
    lines.forEach((ln, i) => c.fillText(ln, W / 2, 360 + i * 52, W - 140));
    c.fillStyle = 'rgba(0,0,0,0.5)'; for (let i = 0; i < 6; i++) c.fillRect(110, 620 + i * 34, W - 220 - (i % 3) * 60, 12);
  });
  g.add(new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: folder, toneMapped: false })));
  const st = textPlane(stamp, { w: w * 0.95, h: w * 0.28, fg: '#c0262d', border: '#c0262d', font: 'Display, sans-serif', size: 0.7 });
  st.material.opacity = 0; st.material.transparent = true; st.rotation.z = 0.25; st.position.set(0, -h * 0.05, 0.01); g.add(st);
  g.userData.stamp = (k) => {          // k = seconds since the stamp (negative = not yet)
    st.visible = k >= 0; if (k < 0) return;
    const a = clamp(k / 0.12); st.scale.setScalar(lerp(2.4, 1, ease.out(a))); st.material.opacity = 0.9 * a;
  };
  g.userData.stamp(-1);
  return g;
}

// ---------------------------------------------------------------- title card in front of the camera
export function titleCard(S, title, { sub = '', y = 0.12, color = '#f3ead2', subColor = '#c0262d' } = {}) {
  const grp = new THREE.Group();
  const { w, h } = S.hud(grp, 2);
  const t = textPlane(title, { w: w * 0.8, h: h * 0.16, fg: color, font: 'Display, sans-serif', size: 0.8 });
  t.position.y = h * y; t.material.transparent = true; t.material.depthTest = false; t.renderOrder = 20000; grp.add(t);
  let s = null;
  if (sub) { s = textPlane(sub, { w: w * 0.6, h: h * 0.07, fg: subColor, font: 'Display, sans-serif', size: 0.7 }); s.position.y = h * (y - 0.12); s.material.transparent = true; s.material.depthTest = false; s.renderOrder = 20000; grp.add(s); }
  grp.userData.fade = (a) => { t.material.opacity = a; if (s) s.material.opacity = a; grp.visible = a > 0.01; };
  grp.userData.fade(0);
  return grp;
}

// ---------------------------------------------------------------- censor badge (channel logo) that hides what we never show
// A round badge that always faces the camera and draws on top. badge.userData.show(k): k = seconds since it appears (<0 hides).
export function censorBadge(S, { size = 1.2, text = 'CENSORED', sub = 'THE INVESTIGATOR' } = {}) {
  const tex = canvasTex(512, 512, (g, w, h) => {
    const cx = w / 2, cy = h / 2;
    g.fillStyle = '#0d0d10'; g.beginPath(); g.arc(cx, cy, 240, 0, 7); g.fill();
    g.lineWidth = 18; g.strokeStyle = '#c0262d'; g.beginPath(); g.arc(cx, cy, 228, 0, 7); g.stroke();
    g.lineWidth = 4; g.strokeStyle = 'rgba(192,38,45,0.6)'; g.beginPath(); g.arc(cx, cy, 200, 0, 7); g.stroke();
    // logo: fedora + round glasses
    g.fillStyle = '#e9e1cf';
    g.beginPath(); g.ellipse(cx, cy - 58, 120, 20, 0, 0, 7); g.fill();
    g.beginPath(); g.moveTo(cx - 62, cy - 62); g.lineTo(cx - 54, cy - 140); g.quadraticCurveTo(cx, cy - 122, cx + 54, cy - 140); g.lineTo(cx + 62, cy - 62); g.closePath(); g.fill();
    g.fillStyle = '#c0262d'; g.fillRect(cx - 60, cy - 86, 120, 14);
    g.strokeStyle = '#e9e1cf'; g.lineWidth = 9;
    for (const s of [-1, 1]) { g.beginPath(); g.arc(cx + s * 40, cy - 14, 28, 0, 7); g.stroke(); }
    g.beginPath(); g.moveTo(cx - 12, cy - 16); g.lineTo(cx + 12, cy - 16); g.stroke();
    g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.font = '900 58px Display, sans-serif'; g.fillText(text, cx, cy + 62, 380);
    g.fillStyle = '#c0262d'; g.font = '800 24px Display, sans-serif'; g.fillText(sub, cx, cy + 112, 330);
  });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, toneMapped: false }));
  m.renderOrder = 15000; m.visible = false; S.add(m);
  m.userData.show = (k) => {
    m.visible = k >= 0; if (!m.visible) return;
    m.quaternion.copy(S.camera.quaternion);
    const pop = k < 0.12 ? ease.back(k / 0.12) : 1 + Math.sin(k * 6) * 0.015;
    m.scale.setScalar(pop);
  };
  return m;
}

// ---------------------------------------------------------------- courtroom (judge's bench on the back wall z=-6, floor y=0)
export function courtroom(S) {
  const wood = toon(0x6b4226), dark = toon(0x3f2716), wall = toon(0xc9b89a);
  S.add(box(20, 0.1, 16, toon(0x5a3a26), [0, -0.05, 0]));
  S.add(box(20, 8, 0.3, wall, [0, 4, -6.2]));
  for (let x = -8; x <= 8; x += 2) S.add(box(0.25, 8, 0.4, dark, [x, 4, -6.0]));
  S.add(box(5, 1.8, 1.4, wood, [0, 0.9, -4.8])); S.add(box(5.2, 0.15, 1.6, dark, [0, 1.85, -4.8]));          // bench
  S.add(box(1.4, 2.6, 0.2, dark, [0, 2.2, -5.9]));                                                          // judge chair back
  const crest = textPlane('COURT', { w: 2.2, h: 0.5, fg: '#d9b45a', font: 'Display, sans-serif', size: 0.7 }); crest.position.set(0, 5.6, -6.0); S.add(crest);
  S.add(box(3, 0.9, 1, wood, [-3, 0.45, -1.2])); S.add(box(3, 0.9, 1, wood, [3, 0.45, -1.2]));               // counsel tables
  for (let i = 0; i < 4; i++) S.add(box(6, 0.9, 0.4, dark, [-4 + (i % 2) * 8, 0.45, 2 + Math.floor(i / 2) * 1.6]));   // public benches
  const lamp = new THREE.PointLight(0xffe2b0, 30, 22, 1.4); lamp.position.set(0, 6.5, -1); S.add(lamp);
}
