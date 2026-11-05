// props.js - procedural sets and props (all built from primitives, no assets)
import { THREE, toon, basic, mesh, box, cyl, sphere, canvasTex, noiseTex, textPlane, roundRect, rng, lerp, clamp } from './engine.js';

// ------------------------------------------------------------------ textures
export function glassTex() {
  return canvasTex(128, 128, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#9fd4ff'); gr.addColorStop(0.5, '#2f5f9e'); gr.addColorStop(1, '#162a4f');
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.fillStyle = 'rgba(255,255,255,0.75)'; g.beginPath(); g.moveTo(w * .15, h * .55); g.lineTo(w * .55, h * .12); g.lineTo(w * .68, h * .12); g.lineTo(w * .28, h * .55); g.fill();
  });
}
export function blueprintTex(windows = 'round', title = 'SKYWARD  MK.1') {
  return canvasTex(1024, 768, (g, w, h) => {
    g.fillStyle = '#1f4f96'; g.fillRect(0, 0, w, h);
    g.strokeStyle = 'rgba(255,255,255,0.13)'; g.lineWidth = 2;
    for (let x = 0; x < w; x += 32) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
    for (let y = 0; y < h; y += 32) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
    g.strokeStyle = '#eaf3ff'; g.lineWidth = 6;
    // fuselage side view
    g.beginPath(); g.moveTo(120, 330); g.lineTo(820, 330); g.quadraticCurveTo(930, 340, 940, 380); g.quadraticCurveTo(930, 420, 820, 430); g.lineTo(200, 430); g.lineTo(90, 300); g.lineTo(60, 200); g.lineTo(120, 200); g.closePath(); g.stroke();
    g.beginPath(); g.moveTo(400, 430); g.lineTo(300, 560); g.lineTo(380, 560); g.lineTo(520, 430); g.stroke();
    g.lineWidth = 5;
    for (let i = 0; i < 12; i++) {
      const x = 260 + i * 46;
      if (windows === 'round') { g.beginPath(); g.arc(x, 370, 13, 0, 7); g.stroke(); }
      else { g.strokeRect(x - 18, 354, 36, 32); }
    }
    // dimension lines + notes
    g.lineWidth = 2; g.beginPath(); g.moveTo(120, 620); g.lineTo(940, 620); g.stroke();
    g.font = '700 34px Courier New, monospace'; g.fillStyle = '#eaf3ff'; g.fillText(title, 60, 80);
    g.font = '24px Courier New, monospace'; g.fillText('SCALE 1:50   SHEET 3/12', 60, 120); g.fillText('WINDOW DETAIL', 620, 690);
    if (windows === 'round') { g.lineWidth = 5; g.beginPath(); g.arc(880, 690, 40, 0, 7); g.stroke(); }
    else { g.lineWidth = 5; g.strokeRect(840, 650, 80, 80); }
  });
}

// ------------------------------------------------------------------ jet airliner (nose = +x)
export function makeJet({ windows = 'round', stripe = '#169e8f', name = 'SKYWARD', gear = true, scale = 1 } = {}) {
  const g = new THREE.Group();
  const white = toon(0xf4f4f0), metal = toon(0xb9c2cc), dark = toon(0x1c2433);
  const R = 1.6, L = 24;
  // livery wrapped around the fuselage: u = angle around, h = sin(angle)
  const liv = canvasTex(1024, 64, (c, w, h) => {
    for (let x = 0; x < w; x++) {
      const hh = Math.sin((x / w) * Math.PI * 2);
      c.fillStyle = hh > 0.62 ? '#ffffff' : hh > 0.5 ? stripe : hh > 0.07 ? '#fbfbf7' : hh > -0.16 ? stripe : hh > -0.22 ? '#ffffff' : '#c9ced4';
      c.fillRect(x, 0, 1, h);
    }
  });
  const fus = mesh(new THREE.CylinderGeometry(R, R, L, 48, 1, true), toon(0xffffff, { map: liv }), [0, 0, 0], { rot: [0, 0, Math.PI / 2] });
  g.add(fus);
  const nose = sphere(R, white, [L / 2, 0, 0], { scale: [2.1, 1, 1], seg: 32 }); g.add(nose);
  const cockpitMat = toon(0x1a2a44);
  for (const s of [-1, 1]) g.add(box(0.9, 0.42, 0.06, cockpitMat, [L / 2 + 1.75, 0.72, s * 0.62], { rot: [0, s * 0.55, -0.45] }));
  g.add(box(0.7, 0.4, 0.9, cockpitMat, [L / 2 + 2.05, 0.82, 0], { rot: [0, 0, -0.75] }));
  const tail = mesh(new THREE.CylinderGeometry(0.35, R, 8, 40, 1, true), white, [-L / 2 - 4, 0.25, 0], { rot: [0, 0, Math.PI / 2 + 0.06] }); g.add(tail);
  // wings (swept)
  const ws = new THREE.Shape(); ws.moveTo(3.5, 0); ws.lineTo(-3.5, 0); ws.lineTo(-7.8, 13.5); ws.lineTo(-5.4, 13.5); ws.closePath();
  const wg = new THREE.ExtrudeGeometry(ws, { depth: 0.32, bevelEnabled: false });
  for (const s of [-1, 1]) {
    const w = mesh(wg, toon(0xdfe3e8, { side: THREE.DoubleSide }), [0.5, -0.75, s * 1.2], { rot: [Math.PI / 2, 0, 0] });
    w.scale.y = s; w.rotation.x = Math.PI / 2 + s * 0.06; g.add(w);
    const eng = cyl(0.62, 0.62, 3.4, metal, [1.2, -0.55, s * 2.6], { rot: [0, 0, Math.PI / 2] }); g.add(eng);
    g.add(cyl(0.45, 0.45, 0.1, dark, [2.92, -0.55, s * 2.6], { rot: [0, 0, Math.PI / 2] }));
  }
  // tail fin + stabilisers
  const fs = new THREE.Shape(); fs.moveTo(0, 0); fs.lineTo(-6.5, 0); fs.lineTo(-8.6, 5.8); fs.lineTo(-6.6, 5.8); fs.closePath();
  const fin = mesh(new THREE.ExtrudeGeometry(fs, { depth: 0.28, bevelEnabled: false }), toon(new THREE.Color(stripe)), [-L / 2 - 1.2, 0.9, -0.14]); g.add(fin);
  const ss = new THREE.Shape(); ss.moveTo(1.4, 0); ss.lineTo(-1.6, 0); ss.lineTo(-3.4, 5); ss.lineTo(-2.2, 5); ss.closePath();
  const sg = new THREE.ExtrudeGeometry(ss, { depth: 0.2, bevelEnabled: false });
  for (const s of [-1, 1]) { const st = mesh(sg, toon(0xdfe3e8, { side: THREE.DoubleSide }), [-L / 2 - 4.5, 0.55, s * 0.3], { rot: [Math.PI / 2, 0, 0] }); st.scale.y = s; g.add(st); }
  // windows
  const glass = new THREE.MeshBasicMaterial({ map: glassTex(), toneMapped: false });
  const frame = toon(0x8f9aa6);
  const wy = 0.42, ang = Math.asin(wy / R), wz = Math.cos(ang) * R;
  g.userData.windows = [];
  for (let i = 0; i < 15; i++) {
    const x = -9.5 + i * 1.32;
    for (const s of [-1, 1]) {
      const holder = new THREE.Group();
      holder.position.set(x, wy, s * (wz + 0.02));
      holder.rotation.set(-s * ang, s < 0 ? Math.PI : 0, 0);
      if (windows === 'round') {
        holder.add(mesh(new THREE.RingGeometry(0.25, 0.36, 32), frame, [0, 0, 0.005], { cast: false }));
        holder.add(mesh(new THREE.CircleGeometry(0.255, 32), glass, [0, 0, 0.01], { cast: false }));
      } else {
        holder.add(mesh(new THREE.PlaneGeometry(0.9, 0.78), frame, [0, 0, 0.005], { cast: false }));
        holder.add(mesh(new THREE.PlaneGeometry(0.76, 0.64), glass, [0, 0, 0.01], { cast: false }));
      }
      g.add(holder); if (s > 0) g.userData.windows.push(holder);
    }
  }
  // door outline + name
  for (const s of [-1, 1]) {
    const nm = textPlane(name, { w: 7, h: 1.0, fg: stripe, font: 'Display, Arial Black, sans-serif', size: 0.8 });
    nm.position.set(1.5, 1.08, s * (Math.cos(Math.asin(1.08 / R)) * R + 0.03)); nm.rotation.set(-s * Math.asin(1.08 / R) * 0.9, s < 0 ? Math.PI : 0, 0);
    g.add(nm);
  }
  // landing gear
  const gearG = new THREE.Group();
  const tyre = toon(0x333333), hub = toon(0xc9ced4);
  for (const [x, z] of [[9, 0], [0.2, 2.6], [0.2, -2.6]]) {
    gearG.add(cyl(0.12, 0.12, 1.6, metal, [x, -2.0, z]));
    gearG.add(cyl(0.48, 0.48, 0.35, tyre, [x, -2.75, z + 0.25], { rot: [Math.PI / 2, 0, 0] }));
    gearG.add(cyl(0.48, 0.48, 0.35, tyre, [x, -2.75, z - 0.25], { rot: [Math.PI / 2, 0, 0] }));
    for (const dz of [0.43, -0.43]) gearG.add(cyl(0.26, 0.26, 0.02, hub, [x, -2.75, z + dz], { rot: [Math.PI / 2, 0, 0], cast: false }));
  }
  gearG.visible = gear; g.add(gearG); g.userData.gear = gearG;
  g.scale.setScalar(scale);
  g.userData.groundY = 3.23 * scale; // set group y to this to sit on the ground
  return g;
}

// ------------------------------------------------------------------ airfield
export function airfield(S, { runway = true, mountains = true, seed = 4 } = {}) {
  const R = rng(seed);
  const grass = noiseTex('#5fa83a', ['#4e9330', '#79c04a', '#9ccf55', '#3f7f2a'], 9000, 512, [60, 60], seed);
  S.add(mesh(new THREE.PlaneGeometry(2400, 2400), toon(0xffffff, { map: grass }), [0, 0, 0], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  if (runway) {
    const asphalt = canvasTex(256, 1024, (g, w, h) => {
      g.fillStyle = '#5b5f66'; g.fillRect(0, 0, w, h);
      const r2 = rng(9); for (let i = 0; i < 3000; i++) { g.fillStyle = r2() < .5 ? '#4e5258' : '#6a6e75'; g.fillRect(r2() * w, r2() * h, 2, 2); }
      g.fillStyle = '#f2f2ea'; g.fillRect(8, 0, 10, h); g.fillRect(w - 18, 0, 10, h);
      for (let y = 0; y < h; y += 256) g.fillRect(w / 2 - 5, y, 10, 140);
    }, [1, 12]);
    S.add(mesh(new THREE.PlaneGeometry(36, 1200), toon(0xffffff, { map: asphalt }), [0, 0.02, 0], { rot: [-Math.PI / 2, 0, Math.PI / 2], cast: false }));
    // runway edge lights
    for (let x = -400; x < 400; x += 20) for (const z of [-19, 19]) S.add(box(0.4, 0.4, 0.4, basic(0xffd36b), [x, 0.2, z], { cast: false }));
  }
  // apron (concrete) in front of the hangars
  const conc = noiseTex('#cdb48f', ['#bb9f78', '#dcc6a4', '#a98d68'], 4000, 512, [10, 10], seed + 1);
  S.add(mesh(new THREE.PlaneGeometry(260, 90), toon(0xffffff, { map: conc }), [0, 0.03, -70], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  // background hangars + tower
  const roofM = toon(0x3b5d8c), wallM = toon(0xe0874a);
  for (let i = 0; i < 4; i++) {
    const hx = -110 + i * 62;
    S.add(box(48, 16, 34, wallM, [hx, 8, -112]));
    S.add(mesh(new THREE.CylinderGeometry(24, 24, 34, 24, 1, false, -Math.PI / 2, Math.PI), roofM, [hx, 16, -112], { rot: [Math.PI / 2, 0, 0], scale: [1, 1, 0.35] }));
    S.add(box(36, 13, 0.5, toon(0x4a4f57), [hx, 6.6, -94.8]));
  }
  const tower = new THREE.Group();
  tower.add(cyl(3, 4, 26, toon(0xe8e1d0), [0, 13, 0]));
  tower.add(cyl(6, 5, 5, basic(0x7fc4ec), [0, 28.5, 0]));
  tower.add(cyl(6.6, 6.6, 1, toon(0xc9442f), [0, 31.5, 0]));
  tower.position.set(150, 0, -95); S.add(tower);
  // windsock
  S.add(cyl(0.12, 0.12, 8, toon(0xdddddd), [40, 4, 30]));
  S.add(mesh(new THREE.ConeGeometry(0.8, 4, 16, 1, true), toon(0xff7a1a, { side: THREE.DoubleSide }), [42, 7.6, 30], { rot: [0, 0, Math.PI / 2] }));
  if (mountains) {
    for (let i = 0; i < 22; i++) {
      const a = (i / 22) * Math.PI * 2 + R() * 0.2, d = 520 + R() * 250;
      const hgt = 60 + R() * 120;
      const m = mesh(new THREE.ConeGeometry(hgt * 1.4, hgt, 7), toon(new THREE.Color().setHSL(0.6 + R() * 0.05, 0.25, 0.55 + R() * 0.1)), [Math.cos(a) * d, hgt / 2 - 2, Math.sin(a) * d], { cast: false, rot: [0, R() * 3, 0] });
      S.add(m);
    }
  }
  for (let i = 0; i < 14; i++) S.cloud([(R() - .5) * 900, 90 + R() * 80, -200 - R() * 500], 1.6 + R() * 2, seed * 10 + i);
}

// ------------------------------------------------------------------ hangar interior (open side faces +z)
export function hangar(S, { seed = 5 } = {}) {
  const conc = canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = '#c9a77c'; g.fillRect(0, 0, w, h);
    const r2 = rng(seed); for (let i = 0; i < 2500; i++) { g.fillStyle = r2() < .5 ? '#b48f63' : '#d8b98f'; g.globalAlpha = .5; g.fillRect(r2() * w, r2() * h, 3, 3); }
    g.globalAlpha = 1; g.strokeStyle = '#9b9588'; g.lineWidth = 3; g.strokeRect(0, 0, w, h);
  }, [14, 14]);
  S.add(mesh(new THREE.PlaneGeometry(120, 120), toon(0xffffff, { map: conc }), [0, 0, 0], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  // yellow safety lines
  for (const z of [-14, 14]) S.add(mesh(new THREE.PlaneGeometry(70, 0.4), basic(0xf2c230), [0, 0.03, z], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  const steel = toon(0xd9702b);
  // half-cylinder roof, axis along z (open front at +z), arching over the floor
  const roofGeo = new THREE.CylinderGeometry(30, 30, 90, 40, 1, true, -Math.PI / 2, Math.PI);
  roofGeo.rotateX(-Math.PI / 2);
  S.add(mesh(roofGeo, toon(0x3b5d8c, { side: THREE.DoubleSide }), [0, 8, -10], { cast: false }));
  // ribs
  for (let z = -50; z <= 30; z += 10) S.add(mesh(new THREE.TorusGeometry(29.6, 0.45, 8, 40, Math.PI), steel, [0, 8, z], { cast: false }));
  // back wall with windows
  const back = box(70, 40, 1, toon(0x4f74a3), [0, 18, -54]); S.add(back);
  for (const sx of [-1, 1]) S.add(box(1, 8, 90, toon(0x4f74a3), [sx * 30, 4, -10]));
  for (let i = -3; i <= 3; i++) for (let j = 0; j < 2; j++) S.add(box(6, 6, 0.3, basic(0xbfe6ff), [i * 7.5, 14 + j * 9, -53.4], { cast: false }));
  // hanging lamps
  for (let x = -30; x <= 30; x += 15) for (const z of [-25, 0]) {
    S.add(cyl(0.05, 0.05, 12, steel, [x, 30, z], { cast: false }));
    S.add(mesh(new THREE.ConeGeometry(1.4, 1.2, 16, 1, true), toon(0x2f3b48, { side: THREE.DoubleSide }), [x, 24, z], { cast: false }));
    S.add(mesh(new THREE.CircleGeometry(1.2, 16), basic(0xfff1c4), [x, 23.45, z], { rot: [Math.PI / 2, 0, 0], cast: false }));
  }
  const pl = new THREE.PointLight(0xffe2b0, 300, 80, 1.5); pl.position.set(0, 20, -8); S.add(pl);
  // crates / tool carts
  const R = rng(seed + 3), wood = toon(0xb98a52);
  for (let i = 0; i < 10; i++) { const s = 1 + R() * 1.4; S.add(box(s, s, s, wood, [(R() < .5 ? -1 : 1) * (22 + R() * 14), s / 2, -30 + R() * 40], { rot: [0, R(), 0] })); }
}
// scaffold tower beside a plane
export function scaffold(S, x, z, h = 6) {
  const m = toon(0x5d6b7a), plank = toon(0xb98a52);
  const g = new THREE.Group();
  for (const dx of [-1.5, 1.5]) for (const dz of [-1, 1]) g.add(cyl(0.08, 0.08, h, m, [dx, h / 2, dz], { seg: 8 }));
  for (let y = 2; y <= h; y += 2) { g.add(box(3.4, 0.15, 2.4, plank, [0, y, 0])); g.add(box(3.2, 0.06, 0.06, m, [0, y + 1, 1])); }
  g.position.set(x, 0, z); S.add(g); return g;
}

// ------------------------------------------------------------------ design office (room centred at origin, back wall at z=-8)
export function office(S, { seed = 7, windows = 'round' } = {}) {
  const planks = canvasTex(512, 512, (g, w, h) => {
    const r2 = rng(seed);
    for (let i = 0; i < 8; i++) { g.fillStyle = `hsl(28, 45%, ${40 + r2() * 10}%)`; g.fillRect(0, i * 64, w, 64); g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(0, i * 64, w, 3); g.fillRect(r2() * w, i * 64, 3, 64); }
  }, [6, 6]);
  S.add(mesh(new THREE.PlaneGeometry(40, 30), toon(0xffffff, { map: planks }), [0, 0, 0], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  const wall = toon(0xf0e2c2), trim = toon(0x7a4a2a);
  S.add(box(40, 12, 0.4, wall, [0, 6, -8]));
  S.add(box(0.4, 12, 30, wall, [-12, 6, 0]));
  S.add(box(0.4, 12, 30, wall, [12, 6, 0]));
  S.add(box(40, 2.2, 0.5, trim, [0, 1.1, -7.9]));
  S.add(box(0.5, 2.2, 30, trim, [-11.9, 1.1, 0]));
  S.add(box(0.5, 2.2, 30, trim, [11.9, 1.1, 0]));
  S.add(box(40, 0.4, 30, toon(0xfaf3e3), [0, 9.5, 0]));
  // windows with sky
  const skyT = canvasTex(256, 256, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#5aa0ea'); gr.addColorStop(1, '#d4ecff'); g.fillStyle = gr; g.fillRect(0, 0, w, h); g.fillStyle = '#fff'; g.beginPath(); g.ellipse(80, 170, 60, 22, 0, 0, 7); g.ellipse(170, 120, 50, 18, 0, 0, 7); g.fill(); });
  for (const x of [-7, 0, 7]) {
    S.add(mesh(new THREE.PlaneGeometry(4.6, 4.4), basic(0xffffff, { map: skyT, toneMapped: false }), [x, 5.2, -7.78], { cast: false }));
    S.add(box(4.9, 0.25, 0.3, trim, [x, 3, -7.7])); S.add(box(4.9, 0.25, 0.3, trim, [x, 7.4, -7.7]));
    S.add(box(0.25, 4.6, 0.3, trim, [x - 2.4, 5.2, -7.7])); S.add(box(0.25, 4.6, 0.3, trim, [x + 2.4, 5.2, -7.7])); S.add(box(0.12, 4.4, 0.25, trim, [x, 5.2, -7.7]));
  }
  // ceiling lamps
  for (const x of [-6, 0, 6]) for (const z of [-3, 3]) {
    S.add(mesh(new THREE.ConeGeometry(0.7, 0.6, 16, 1, true), toon(0x2e6b4f, { side: THREE.DoubleSide }), [x, 7.7, z], { cast: false }));
    S.add(mesh(new THREE.CircleGeometry(0.6, 16), basic(0xfff3c9), [x, 7.42, z], { rot: [Math.PI / 2, 0, 0], cast: false }));
    S.add(cyl(0.03, 0.03, 1.8, toon(0x222222), [x, 8.6, z], { cast: false }));
  }
  const pl = new THREE.PointLight(0xffe7bf, 60, 30, 1.6); pl.position.set(0, 7, 0); S.add(pl);
  // posters on side wall
  const poster = mesh(new THREE.PlaneGeometry(3.2, 2.4), basic(0xffffff, { map: blueprintTex(windows), toneMapped: false }), [-11.75, 5.5, -2], { rot: [0, Math.PI / 2, 0], cast: false }); S.add(poster);
}
export function draftTable(S, x, z, { rot = 0, windows = 'round', tilt = 0.5 } = {}) {
  const g = new THREE.Group(), wood = toon(0x8a5a32), metal = toon(0x3d4b5a);
  for (const dx of [-1.1, 1.1]) for (const dz of [-0.6, 0.6]) g.add(cyl(0.06, 0.06, 2.2, metal, [dx, 1.1, dz], { seg: 8 }));
  const board = new THREE.Group(); board.position.set(0, 2.25, 0); board.rotation.x = -tilt;
  board.add(box(2.8, 0.1, 1.9, wood, [0, 0, 0]));
  const bp = mesh(new THREE.PlaneGeometry(2.5, 1.7), basic(0xffffff, { map: blueprintTex(windows), toneMapped: false }), [0, 0.06, 0], { rot: [-Math.PI / 2, 0, 0], cast: false });
  board.add(bp); g.add(board);
  // lamp
  g.add(cyl(0.04, 0.04, 1.4, metal, [1.2, 3.0, -0.8], { seg: 8 }));
  g.add(mesh(new THREE.ConeGeometry(0.3, 0.4, 12, 1, true), toon(0x2e6b4f, { side: THREE.DoubleSide }), [0.9, 3.6, -0.6], { rot: [0.4, 0, 0.6] }));
  g.position.set(x, 0, z); g.rotation.y = rot; S.add(g);
  g.userData.board = board; g.userData.blueprint = bp;
  return g;
}

// ------------------------------------------------------------------ terminal hall (counters on the back wall)
export function terminal(S, { seed = 8 } = {}) {
  const tiles = canvasTex(256, 256, (g, w, h) => { for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { g.fillStyle = (i + j) % 2 ? '#e9e2d0' : '#2f4a6b'; g.fillRect(i * 64, j * 64, 64, 64); } }, [20, 20]);
  S.add(mesh(new THREE.PlaneGeometry(80, 80), toon(0xffffff, { map: tiles }), [0, 0, 0], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  const wall = toon(0xe7d7b5);
  S.add(box(80, 18, 0.6, wall, [0, 9, -12]));
  S.add(box(0.6, 18, 60, wall, [-24, 9, 10]));
  S.add(box(0.6, 18, 60, wall, [24, 9, 10]));
  S.add(box(80, 0.6, 60, toon(0xf6eedc), [0, 14, 10]));
  for (let x = -20; x <= 20; x += 8) S.add(box(1, 14, 1, toon(0xb08550), [x, 7, -11.3]));
  const big = textPlane('DEPARTURES', { w: 14, h: 1.8, bg: '#1d2b44', fg: '#ffd56b', font: 'Display, Arial Black, sans-serif', size: 0.7, radius: 30 });
  big.position.set(0, 11, -11.6); S.add(big);
  for (const x of [-12, 0, 12]) {
    S.add(mesh(new THREE.CircleGeometry(1.2, 16), basic(0xfff3c9), [x, 13.65, 0], { rot: [Math.PI / 2, 0, 0], cast: false }));
  }
  const pl = new THREE.PointLight(0xffe7bf, 120, 50, 1.4); pl.position.set(0, 12, 4); S.add(pl);
}
export function counter(S, x, z, { name = 'SKYWARD', color = '#169e8f' } = {}) {
  const g = new THREE.Group();
  g.add(box(7, 2.2, 1.8, toon(new THREE.Color(color)), [0, 1.1, 0]));
  g.add(box(7.3, 0.2, 2.1, toon(0xf3ead6), [0, 2.3, 0]));
  const sign = textPlane(name, { w: 7, h: 1.6, bg: color, fg: '#ffffff', font: 'Display, Arial Black, sans-serif', size: 0.62, radius: 24 });
  sign.position.set(0, 6.2, -0.8); g.add(sign);
  g.add(cyl(0.06, 0.06, 3, toon(0x333333), [-2.5, 6.5, -0.8], { seg: 6 })); g.add(cyl(0.06, 0.06, 3, toon(0x333333), [2.5, 6.5, -0.8], { seg: 6 }));
  g.position.set(x, 0, z); S.add(g); return g;
}

// ------------------------------------------------------------------ cabin interior (aisle along x)
export function cabin(S, { windows = 'square' } = {}) {
  const tube = mesh(new THREE.CylinderGeometry(2.6, 2.6, 40, 40, 1, true), toon(0xf2ece0, { side: THREE.BackSide }), [0, 1.4, 0], { rot: [0, 0, Math.PI / 2], cast: false });
  S.add(tube);
  const carpet = noiseTex('#8c2f39', ['#7a2731', '#a33a45'], 3000, 256, [20, 2], 2);
  S.add(mesh(new THREE.PlaneGeometry(40, 3.8), toon(0xffffff, { map: carpet }), [0, 0, 0], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  const skyView = canvasTex(256, 256, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#3f86de'); gr.addColorStop(1, '#cfe9ff'); g.fillStyle = gr; g.fillRect(0, 0, w, h); g.fillStyle = '#fff'; g.beginPath(); g.ellipse(70, 190, 70, 25, 0, 0, 7); g.ellipse(190, 210, 60, 20, 0, 0, 7); g.fill(); });
  const winM = basic(0xffffff, { map: skyView, toneMapped: false }), frameM = toon(0xd4cbb8);
  const seatM = toon(0x2f6fb3), headM = toon(0xf3efe6);
  S.scene.userData.windows = [];
  for (let i = 0; i < 12; i++) {
    const x = -14 + i * 2.4;
    for (const s of [-1, 1]) {
      // window on the wall (facing in)
      const holder = new THREE.Group(); holder.position.set(x, 1.85, s * 2.42); holder.rotation.y = s > 0 ? Math.PI : 0;
      if (windows === 'square') { holder.add(mesh(new THREE.PlaneGeometry(1.5, 1.25), frameM, [0, 0, 0.0], { cast: false })); holder.add(mesh(new THREE.PlaneGeometry(1.3, 1.05), winM, [0, 0, 0.01], { cast: false })); }
      else { holder.add(mesh(new THREE.CircleGeometry(0.55, 32), frameM, [0, 0, 0], { cast: false })); holder.add(mesh(new THREE.CircleGeometry(0.42, 32), winM, [0, 0, 0.01], { cast: false })); }
      S.add(holder); if (s < 0) S.scene.userData.windows.push(holder);
      // seat (back faces -x)
      const seat = new THREE.Group();
      seat.add(box(0.9, 0.5, 1.6, seatM, [0, 0.6, 0])); seat.add(box(0.25, 1.1, 1.6, seatM, [-0.45, 1.1, 0])); seat.add(box(0.27, 0.3, 1.6, headM, [-0.45, 1.75, 0]));
      seat.position.set(x - 0.4, 0, s * 1.35); S.add(seat);
    }
  }
  const pl = new THREE.PointLight(0xfff0d0, 40, 30, 1.5); pl.position.set(0, 3.2, 0); S.add(pl);
}

// ------------------------------------------------------------------ newspaper
export function newspaper({ masthead = 'THE DAILY AVIATOR', headline = 'THE PORTHOLE PLANE!', sub = '"Funny little windows" - critics', windows = 'round' } = {}) {
  const tex = canvasTex(1024, 1400, (g, w, h) => {
    g.fillStyle = '#efe8d6'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#1a1a1a'; g.textAlign = 'center';
    g.font = '900 92px Georgia, "Times New Roman", serif'; g.fillText(masthead, w / 2, 120, w - 80);
    g.fillRect(40, 150, w - 80, 6); g.fillRect(40, 205, w - 80, 3);
    g.font = 'italic 30px Georgia, serif'; g.fillText('MORNING EDITION  ·  FIVE CENTS', w / 2, 192);
    g.font = '900 118px Georgia, "Times New Roman", serif';
    const words = headline.split(' '); const mid = Math.ceil(words.length / 2);
    g.fillText(words.slice(0, mid).join(' '), w / 2, 345, w - 60); g.fillText(words.slice(mid).join(' '), w / 2, 470, w - 60);
    g.font = 'italic 44px Georgia, serif'; g.fillText(sub, w / 2, 545, w - 80);
    // photo
    g.fillStyle = '#d5ccb6'; g.fillRect(80, 590, w - 160, 430); g.strokeStyle = '#1a1a1a'; g.lineWidth = 5; g.strokeRect(80, 590, w - 160, 430);
    g.fillStyle = '#fafafa'; g.beginPath(); g.ellipse(w / 2, 800, 330, 70, 0, 0, 7); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(w / 2 + 60, 840); g.lineTo(w / 2 - 80, 960); g.lineTo(w / 2 - 20, 960); g.lineTo(w / 2 + 140, 840); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(w / 2 - 300, 780); g.lineTo(w / 2 - 380, 660); g.lineTo(w / 2 - 330, 660); g.lineTo(w / 2 - 250, 770); g.fill(); g.stroke();
    g.lineWidth = 4;
    for (let i = 0; i < 11; i++) { const x = w / 2 - 230 + i * 44; if (windows === 'round') { g.beginPath(); g.arc(x, 790, 12, 0, 7); g.stroke(); } else g.strokeRect(x - 16, 776, 32, 28); }
    // columns of text
    g.fillStyle = '#555';
    for (let c = 0; c < 3; c++) for (let i = 0; i < 12; i++) g.fillRect(80 + c * 300, 1060 + i * 27, 260 - (i % 4 === 3 ? 90 : 0), 10);
  });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(3, 4.1), new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide, toneMapped: false }));
  return m;
}

// ------------------------------------------------------------------ effects
export function confetti(S, n = 400, area = [30, 20, 30], center = [0, 0, 0], seed = 3) {
  const R = rng(seed);
  const geo = new THREE.PlaneGeometry(0.25, 0.16);
  const m = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, toneMapped: false });
  const im = new THREE.InstancedMesh(geo, m, n);
  const cols = ['#ff4d6d', '#ffd166', '#06d6a0', '#118ab2', '#ffffff', '#f78c6b'].map(c => new THREE.Color(c));
  const data = [];
  for (let i = 0; i < n; i++) { im.setColorAt(i, cols[i % cols.length]); data.push([(R() - .5) * area[0], R() * area[1], (R() - .5) * area[2], R() * 6, R() * 6, 0.8 + R() * 1.5]); }
  S.add(im);
  const dummy = new THREE.Object3D();
  S.onUpdate((t) => {
    for (let i = 0; i < n; i++) {
      const [x, y, z, a, b, sp] = data[i];
      dummy.position.set(center[0] + x + Math.sin(t * 2 + a) * 0.6, center[1] + ((y - t * sp) % area[1] + area[1]) % area[1], center[2] + z);
      dummy.rotation.set(a + t * 4, b + t * 3, 0); dummy.updateMatrix(); im.setMatrixAt(i, dummy.matrix);
    }
    im.instanceMatrix.needsUpdate = true;
  });
  return im;
}
export function tumbleweed(S, seed = 2) {
  const g = new THREE.Group(), R = rng(seed);
  const m = new THREE.MeshBasicMaterial({ color: 0x9c7a45, wireframe: true });
  for (let i = 0; i < 6; i++) { const t = new THREE.Mesh(new THREE.TorusGeometry(0.55 + R() * 0.2, 0.02, 4, 18), m); t.rotation.set(R() * 3, R() * 3, R() * 3); g.add(t); }
  S.add(g); return g;
}
// animated crack drawn over a window: returns a mesh with .userData.setProgress(k)
export function crackOverlay(w = 0.76, h = 0.64, seed = 5) {
  const R = rng(seed);
  const lines = [];
  // cracks start at the top-right corner of a square window
  const start = [0.98, 0.04];
  for (let b = 0; b < 5; b++) {
    let [x, y] = start; const pts = [[x, y]]; const ang = Math.PI * (0.55 + R() * 0.45);
    for (let s = 0; s < 7; s++) { const a = ang + (R() - .5) * 0.9; x += Math.cos(a) * 0.09 * (1 + R()); y += Math.abs(Math.sin(a)) * 0.08 * (1 + R()); pts.push([x, y]); }
    lines.push(pts);
  }
  const tex = canvasTex(512, 432, () => {});
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, toneMapped: false, depthWrite: false });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  m.userData.setProgress = (k) => {
    const g = tex.userData.ctx, W = 512, H = 432; g.clearRect(0, 0, W, H);
    g.strokeStyle = 'rgba(255,255,255,0.95)'; g.lineWidth = 5; g.lineCap = 'round';
    for (const pts of lines) {
      const n = Math.floor(clamp(k) * (pts.length - 1));
      g.beginPath(); g.moveTo(pts[0][0] * W, pts[0][1] * H);
      for (let i = 1; i <= n; i++) g.lineTo(pts[i][0] * W, pts[i][1] * H);
      g.stroke();
    }
    tex.needsUpdate = true;
  };
  m.userData.setProgress(0);
  return m;
}
