// Procedural low-res textures + small geometry helpers (PS2 look: tiny textures, nearest filtering, flat shading)
'use strict';

function makeRng(seed) {
  let s = (seed * 2654435761) >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return (s % 100000) / 100000; };
}

const TEX = {};
function canvasTex(name, w, h, draw, repeat = [1, 1], smooth = false) {
  const key = name + repeat.join('x');
  if (TEX[key]) return TEX[key];
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d');
  draw(g, w, h);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat[0], repeat[1]);
  t.magFilter = smooth ? THREE.LinearFilter : THREE.NearestFilter;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  TEX[key] = t;
  return t;
}

function shade(hex, f) {
  const c = new THREE.Color(hex);
  c.multiplyScalar(f);
  return '#' + c.getHexString();
}

const Tex = {
  wallpaper: (r = [6, 3]) => canvasTex('wallpaper', 32, 32, (g, w, h) => {
    g.fillStyle = '#c4a23e'; g.fillRect(0, 0, w, h);
    g.strokeStyle = '#94741f'; g.lineWidth = 2;
    g.beginPath(); g.moveTo(0, 16); g.lineTo(16, 0); g.lineTo(32, 16); g.lineTo(16, 32); g.closePath(); g.stroke();
    g.fillStyle = '#a8862c'; g.fillRect(15, 15, 3, 3);
    g.fillStyle = '#d6b552'; g.fillRect(0, 0, 2, 2);
  }, r),
  floral: (r = [2, 2]) => canvasTex('floral', 64, 64, (g, w, h) => {
    const R = makeRng(3);
    g.fillStyle = '#efe3cc'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 26; i++) {
      const x = R() * w, y = R() * h;
      g.fillStyle = '#86a463'; g.fillRect(x + 2, y + 3, 4, 2);
      g.fillStyle = R() > 0.5 ? '#d88a8e' : '#c46a78';
      g.fillRect(x - 2, y - 2, 4, 4); g.fillRect(x - 1, y - 3, 2, 6); g.fillRect(x - 3, y - 1, 6, 2);
    }
  }, r),
  wood: (r = [4, 4], base = '#6b4426') => canvasTex('wood' + base, 32, 64, (g, w, h) => {
    const R = makeRng(5);
    for (let x = 0; x < w; x += 8) {
      g.fillStyle = shade(base, 0.85 + R() * 0.3); g.fillRect(x, 0, 8, h);
      g.fillStyle = shade(base, 0.6); g.fillRect(x, 0, 1, h);
      const cut = Math.floor(R() * h); g.fillRect(x, cut, 8, 1);
      for (let k = 0; k < 4; k++) { g.fillStyle = shade(base, 0.75 + R() * 0.2); g.fillRect(x + 2 + R() * 4, R() * h, 1, 6 + R() * 10); }
    }
  }, r),
  brick: (r = [4, 4], base = '#8a3b2a', mortar = '#5e554c') => canvasTex('brick' + base, 64, 64, (g, w, h) => {
    const R = makeRng(9);
    g.fillStyle = mortar; g.fillRect(0, 0, w, h);
    for (let row = 0; row < 8; row++) {
      const off = row % 2 ? 8 : 0;
      for (let col = -1; col < 4; col++) {
        g.fillStyle = shade(base, 0.75 + R() * 0.45);
        g.fillRect(col * 16 + off + 1, row * 8 + 1, 14, 6);
      }
    }
  }, r),
  cobble: (r = [10, 10]) => canvasTex('cobble', 64, 64, (g, w, h) => {
    const R = makeRng(11);
    g.fillStyle = '#1b1d22'; g.fillRect(0, 0, w, h);
    for (let row = 0; row < 8; row++) for (let col = 0; col < 8; col++) {
      g.fillStyle = shade('#4a4f58', 0.6 + R() * 0.6);
      g.fillRect(col * 8 + (row % 2) * 4 + 1, row * 8 + 1, 6, 6);
    }
  }, r),
  stone: (r = [3, 3]) => canvasTex('stone', 32, 32, (g, w, h) => {
    const R = makeRng(13);
    g.fillStyle = '#77767a'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 80; i++) { g.fillStyle = shade('#77767a', 0.75 + R() * 0.5); g.fillRect(R() * w, R() * h, 2, 2); }
  }, r),
  lace: () => canvasTex('lace', 32, 64, (g, w, h) => {
    g.clearRect(0, 0, w, h);
    g.fillStyle = 'rgba(245,245,240,0.92)';
    for (let y = 0; y < h; y += 4) for (let x = (y / 4) % 2 * 2; x < w; x += 4) g.fillRect(x, y, 2, 2);
    for (let y = 6; y < h; y += 12) for (let x = 4; x < w; x += 12) { g.fillRect(x - 3, y, 7, 1); g.fillRect(x, y - 3, 1, 7); g.fillRect(x - 1, y - 1, 3, 3); }
    // scalloped bottom
    g.clearRect(0, h - 4, w, 4);
    for (let x = 0; x < w; x += 8) g.fillRect(x + 1, h - 4, 6, 3);
  }, [3, 1]),
  door: () => canvasTex('door', 32, 64, (g, w, h) => {
    g.fillStyle = '#5a3a20'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#4a2e18';
    [[4, 4, 10, 24], [18, 4, 10, 24], [4, 34, 10, 26], [18, 34, 10, 26]].forEach(([x, y, a, b]) => g.fillRect(x, y, a, b));
    g.fillStyle = '#6e4a2a';
    [[5, 5, 8, 22], [19, 5, 8, 22], [5, 35, 8, 24], [19, 35, 8, 24]].forEach(([x, y, a, b]) => g.fillRect(x + 1, y + 1, a - 2, b - 2));
    g.fillStyle = '#d4b04a'; g.fillRect(27, 32, 2, 3);
  }),
  frontDoor: () => canvasTex('frontdoor', 32, 64, (g, w, h) => {
    g.fillStyle = '#1e3a2a'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#16301f';
    [[4, 6, 10, 22], [18, 6, 10, 22], [4, 34, 10, 24], [18, 34, 10, 24]].forEach(([x, y, a, b]) => g.fillRect(x, y, a, b));
    g.fillStyle = '#d9b84a'; g.fillRect(14, 30, 4, 3); g.fillRect(26, 34, 2, 2);
    g.font = 'bold 9px monospace'; g.fillStyle = '#e8cf72'; g.fillText('39', 9, 20);
  }),
  portrait: () => canvasTex('portrait', 48, 64, (g, w, h) => {
    g.fillStyle = '#2b1a14'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#463026'; g.fillRect(3, 3, w - 6, h - 6);
    g.fillStyle = '#c86b7a'; g.beginPath(); g.moveTo(10, 64); g.lineTo(24, 36); g.lineTo(38, 64); g.fill();
    g.fillStyle = '#f0c8a8'; g.fillRect(19, 24, 10, 12);
    g.fillStyle = '#2a1712'; g.fillRect(17, 20, 14, 6); g.fillRect(16, 24, 3, 10); g.fillRect(29, 24, 3, 10);
    g.fillStyle = '#1b1b1b'; g.fillRect(8, 15, 32, 5); g.fillRect(14, 10, 20, 6);
    g.fillStyle = '#e25b84'; g.fillRect(30, 9, 5, 5);
    g.fillStyle = '#20120d'; g.fillRect(21, 29, 2, 1); g.fillRect(26, 29, 2, 1);
    g.fillStyle = '#a03040'; g.fillRect(23, 33, 3, 1);
  }),
  window: (lit = '#ffd27a') => canvasTex('window' + lit, 16, 32, (g, w, h) => {
    g.fillStyle = lit; g.fillRect(0, 0, w, h);
    g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, 0, w, 3); g.fillRect(0, 0, 3, h);
    g.fillStyle = '#e8e2d2'; g.fillRect(7, 0, 2, h); g.fillRect(0, 15, w, 2);
  }),
  poison: () => canvasTex('poison', 64, 32, (g, w, h) => {
    g.fillStyle = '#e9dfc0'; g.fillRect(0, 0, w, h);
    g.strokeStyle = '#7a1a1a'; g.lineWidth = 2; g.strokeRect(2, 2, w - 4, h - 4);
    g.fillStyle = '#7a1a1a'; g.font = 'bold 11px monospace'; g.textAlign = 'center'; g.fillText('POISON', w / 2, 14);
    g.font = '7px monospace'; g.fillText('HYOSCINE', w / 2, 25);
  }, [1, 1], true),
  dials: () => canvasTex('dials', 64, 32, (g, w, h) => {
    g.fillStyle = '#2a2420'; g.fillRect(0, 0, w, h);
    [[12, 12], [32, 12], [52, 12]].forEach(([x, y]) => { g.fillStyle = '#e8dcc0'; g.beginPath(); g.arc(x, y, 7, 0, 7); g.fill(); g.strokeStyle = '#111'; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 4, y - 4); g.stroke(); });
    g.fillStyle = '#b08a40'; for (let x = 6; x < w; x += 10) g.fillRect(x, 24, 5, 4);
  }),
  clockface: () => canvasTex('clockface', 32, 32, (g, w, h) => {
    g.fillStyle = '#efe6cf'; g.beginPath(); g.arc(16, 16, 15, 0, 7); g.fill();
    g.fillStyle = '#222'; for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; g.fillRect(16 + Math.sin(a) * 12 - 1, 16 - Math.cos(a) * 12 - 1, 2, 2); }
  }),
  sky: (top, bottom) => canvasTex('sky' + top + bottom, 4, 64, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, top); gr.addColorStop(1, bottom);
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
  }, [1, 1], true),
};

// ---------- material + geometry helpers
const MATS = {};
function M(color, opts = {}) {
  const key = color + JSON.stringify(Object.keys(opts).length ? Object.assign({}, opts, { map: opts.map ? opts.map.uuid : 0 }) : '');
  if (MATS[key] && !opts.unique) return MATS[key];
  const m = new THREE.MeshPhongMaterial(Object.assign({ color, flatShading: true, shininess: 6, specular: 0x111111 }, opts));
  delete m.unique;
  MATS[key] = m;
  return m;
}
function Basic(color, opts = {}) { return new THREE.MeshBasicMaterial(Object.assign({ color }, opts)); }

function box(parent, w, h, d, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); parent.add(m); return m;
}
function cyl(parent, rt, rb, h, seg, mat, x = 0, y = 0, z = 0, open = false) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg, 1, open), mat);
  m.position.set(x, y, z); parent.add(m); return m;
}
function ball(parent, r, mat, x = 0, y = 0, z = 0, w = 7, h = 5) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, w, h), mat);
  m.position.set(x, y, z); parent.add(m); return m;
}
function plane(parent, w, h, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  m.position.set(x, y, z); parent.add(m); return m;
}
// crumpled faceted blob — the signature "box hair" look
function blob(parent, r, mat, seed, jitter = 0.18, detail = 1) {
  const geo = new THREE.IcosahedronGeometry(r, detail);
  const R = makeRng(seed);
  const pos = geo.attributes.position;
  const map = {};
  for (let i = 0; i < pos.count; i++) {
    const k = [pos.getX(i), pos.getY(i), pos.getZ(i)].map(v => v.toFixed(4)).join(',');
    if (!map[k]) map[k] = 1 + (R() - 0.5) * 2 * jitter;
    pos.setXYZ(i, pos.getX(i) * map[k], pos.getY(i) * map[k], pos.getZ(i) * map[k]);
  }
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, mat); parent.add(m); return m;
}
