// kits/night.js - horror / night kit: night sky, moon, stars, ocean, light beams,
// flicker, rain, distant city, plus prison sets (island + cell).
import { THREE, toon, basic, mesh, box, cyl, sphere, canvasTex, noiseTex, textPlane, rng, lerp, clamp } from '../engine.js';

// ---------------------------------------------------------------- sky
export function nightSky(S, { fog = [50, 420], moon = [-260, 170, -520], stars = true, moonLight = 1.8, hemi = 0.75 } = {}) {
  const mp = moon || [-260, 170, -520];
  S.sky({ top: '#050c22', horizon: '#2a4470', bottom: '#0a1426', sun: [mp[0] * 0.2, 60, mp[2] * 0.2], sunColor: 0xa9c3ff,
          sunI: moonLight, hemi, ground: 0x0a0f1a, fog, shadow: 60 });
  if (moon) {
    const m = new THREE.Mesh(new THREE.CircleGeometry(22, 48), new THREE.MeshBasicMaterial({ color: 0xf6f1d6, fog: false, toneMapped: false }));
    m.position.set(...moon); m.lookAt(0, 0, 0); S.add(m);
    const haloT = canvasTex(256, 256, (g, w, h) => { const gr = g.createRadialGradient(w / 2, h / 2, 10, w / 2, h / 2, w / 2); gr.addColorStop(0, 'rgba(255,250,220,0.55)'); gr.addColorStop(1, 'rgba(255,250,220,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
    const halo = new THREE.Mesh(new THREE.PlaneGeometry(160, 160), new THREE.MeshBasicMaterial({ map: haloT, transparent: true, fog: false, depthWrite: false, blending: THREE.AdditiveBlending }));
    halo.position.copy(m.position).multiplyScalar(1.01); halo.lookAt(0, 0, 0); S.add(halo);
  }
  if (stars) {
    const R = rng(77), n = 700, pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { const a = R() * Math.PI * 2, e = 0.08 + R() * 1.3; pos.set([Math.cos(a) * Math.cos(e) * 850, Math.sin(e) * 850, Math.sin(a) * Math.cos(e) * 850], i * 3); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    S.add(new THREE.Points(geo, new THREE.PointsMaterial({ color: 0xdfe8ff, size: 2.2, sizeAttenuation: false, fog: false })));
  }
}

// ---------------------------------------------------------------- ocean (animated waves)
export function ocean(S, { size = 900, seg = 140, color = 0x1f5373, amp = 0.35, y = 0, speed = 1 } = {}) {
  const geo = new THREE.PlaneGeometry(size, size, seg, seg); geo.rotateX(-Math.PI / 2);
  const mat = new THREE.MeshPhongMaterial({ color, flatShading: true, shininess: 60, specular: 0xb9d4f0, emissive: 0x06121c });
  const m = new THREE.Mesh(geo, mat); m.position.y = y; m.receiveShadow = true; S.add(m);
  const p = geo.attributes.position, base = p.array.slice();
  S.onUpdate((t) => {
    for (let i = 0; i < p.count; i++) {
      const x = base[i * 3], z = base[i * 3 + 2];
      p.array[i * 3 + 1] = (Math.sin(x * 0.11 + t * 1.3 * speed) * 0.6 + Math.sin(z * 0.17 - t * 0.9 * speed) * 0.5 + Math.sin((x + z) * 0.31 + t * 2.1 * speed) * 0.25) * amp;
    }
    p.needsUpdate = true; geo.computeVertexNormals();
  });
  return m;
}

// ---------------------------------------------------------------- light beams (lighthouse / searchlight / flashlight cone)
export function lightBeam(S, pos, { length = 140, radius = 14, color = 0xfff2c4, opacity = 0.22, spin = 0.6, tilt = 0.05, yaw = 0 } = {}) {
  const fade = canvasTex(8, 256, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#ffffff'); gr.addColorStop(1, '#000000'); g.fillStyle = gr; g.fillRect(0, 0, w, h); });
  const geo = new THREE.ConeGeometry(radius, length, 32, 1, true); geo.translate(0, -length / 2, 0); geo.rotateX(Math.PI / 2);
  const cone = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color, alphaMap: fade, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, fog: false }));
  const g = new THREE.Group(); g.position.set(...pos); cone.rotation.x = -tilt; g.add(cone); g.rotation.y = yaw; S.add(g);
  if (spin) S.onUpdate((t) => { g.rotation.y = yaw + t * spin; });
  return g;
}

// flicker any light (or material opacity): random dips like a failing bulb
export function flicker(S, light, { base = light.intensity, seed = 3, amount = 0.85, rate = 1 } = {}) {
  const R = rng(seed), dips = [];
  for (let i = 0; i < 40; i++) dips.push([R() * 20, 0.04 + R() * 0.12]);
  S.onUpdate((t) => {
    let k = 1;
    for (const [at, len] of dips) if (t * rate > at && t * rate < at + len) k = 1 - amount * (0.5 + 0.5 * Math.sin(t * 90));
    light.intensity = base * k * (0.95 + 0.05 * Math.sin(t * 13));
  });
}

// ---------------------------------------------------------------- rain
export function rain(S, { n = 1500, area = [60, 30, 60], center = [0, 0, 0], speed = 28, color = 0x9fb6d8 } = {}) {
  const R = rng(9), pos = new Float32Array(n * 6), seeds = [];
  for (let i = 0; i < n; i++) seeds.push([(R() - 0.5) * area[0], R() * area[1], (R() - 0.5) * area[2]]);
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const lines = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.45 }));
  lines.frustumCulled = false; S.add(lines);
  S.onUpdate((t) => {
    for (let i = 0; i < n; i++) {
      const [x, y0, z] = seeds[i]; const y = ((y0 - t * speed) % area[1] + area[1]) % area[1];
      pos.set([center[0] + x, center[1] + y, center[2] + z, center[0] + x + 0.05, center[1] + y + 0.7, center[2] + z], i * 6);
    }
    geo.attributes.position.needsUpdate = true;
  });
  return lines;
}

// ---------------------------------------------------------------- distant city skyline with lit windows
export function cityLights(S, { x0 = -260, x1 = 260, z = -330, n = 60, seed = 4 } = {}) {
  const R = rng(seed);
  const winT = canvasTex(128, 256, (g, w, h) => { g.fillStyle = '#0b1220'; g.fillRect(0, 0, w, h); for (let y = 6; y < h; y += 14) for (let x = 6; x < w; x += 14) if (R() < 0.38) { g.fillStyle = R() < 0.8 ? '#ffd27a' : '#cfe4ff'; g.fillRect(x, y, 6, 8); } });
  for (let i = 0; i < n; i++) {
    const w = 6 + R() * 14, h = 8 + R() * (R() < 0.15 ? 70 : 32);
    const t = winT.clone(); t.needsUpdate = true; t.repeat.set(w / 14, h / 26); t.wrapS = t.wrapT = THREE.RepeatWrapping;
    S.add(box(w, h, 6, new THREE.MeshBasicMaterial({ map: t, color: 0xffffff }), [lerp(x0, x1, R()), h / 2 - 2, z - R() * 40], { cast: false, receive: false }));
  }
}

// ---------------------------------------------------------------- prison island (rock + cellhouse + lighthouse + water tower)
// Island centred on the origin, top plateau around y=12, cellhouse facing +z.
export function prisonIsland(S, { seed = 6 } = {}) {
  const R = rng(seed), rock = toon(0x75695d), rock2 = toon(0x5d544b);
  for (let i = 0; i < 18; i++) {
    const s = 8 + R() * 10;
    const m = mesh(new THREE.DodecahedronGeometry(1, 0), R() < 0.5 ? rock : rock2, [(R() - 0.5) * 60, R() * 3 - 3, (R() - 0.5) * 34], { rot: [R() * 3, R() * 3, R() * 3] });
    m.scale.set(s * 1.4, s * 0.6, s); S.add(m);
  }
  S.add(box(56, 6, 26, rock, [0, 9, 0]));                                 // plateau
  const wall = toon(0xbdb4a2), dark = toon(0x2a2f38);
  S.add(box(36, 9, 13, wall, [0, 16.5, 0]));                               // cellhouse
  S.add(box(37, 0.8, 14, toon(0x8d857a), [0, 21.3, 0]));
  const winM = new THREE.MeshBasicMaterial({ color: 0xffd98a, transparent: true, opacity: 0.55 });
  for (let i = 0; i < 14; i++) for (let j = 0; j < 2; j++) {
    S.add(box(1.2, 2.4, 0.2, R() < 0.75 ? winM : dark, [-15.6 + i * 2.4, 14.6 + j * 3.6, 6.55], { cast: false }));
  }
  S.add(cyl(1.0, 1.4, 16, toon(0xe8e3d6), [-20, 20, 4]));               // lighthouse
  const lamp = cyl(1.3, 1.3, 1.6, new THREE.MeshBasicMaterial({ color: 0xfff4c8 }), [-20, 28.8, 4]); S.add(lamp);
  S.add(cyl(1.6, 1.6, 0.4, toon(0x2a2f38), [-20, 29.8, 4]));
  const tank = new THREE.Group();                                           // water tower
  for (const [dx, dz] of [[-2, -2], [2, -2], [-2, 2], [2, 2]]) tank.add(cyl(0.15, 0.15, 10, toon(0x5b4a3a), [dx, 5, dz], { seg: 6 }));
  tank.add(cyl(3.2, 3.2, 5, toon(0x7a6a58), [0, 12, 0])); tank.position.set(20, 12, -3); S.add(tank);
  const glow = new THREE.PointLight(0xffd98a, 60, 40, 1.6); glow.position.set(0, 16, 10); S.add(glow);
  return { lampPos: [-20, 28.8, 4] };
}

// ---------------------------------------------------------------- prison cell (floor at y=0, back wall z=-1.6, bars at z=+1.6)
export function prisonCell(S, { x = 0, ventOpen = 0, flickerSeed = 2, toilet = true } = {}) {
  const g = new THREE.Group(); g.position.x = x;
  const concrete = noiseTex('#8d8a83', ['#7b7871', '#a29f98', '#6c6964'], 2500, 256, [3, 3], 5);
  const wallM = toon(0xffffff, { map: concrete }), floorM = toon(0x6f6c66);
  g.add(box(2.2, 0.1, 3.4, floorM, [0, -0.05, 0]));
  g.add(box(2.2, 3.2, 0.2, wallM, [0, 1.6, -1.7]));
  for (const s of [-1, 1]) g.add(box(0.2, 3.2, 3.4, wallM, [s * 1.1, 1.6, 0]));
  g.add(box(2.4, 0.2, 3.6, wallM, [0, 3.25, 0]));
  // bars
  const barM = toon(0x3c444f);
  for (let bx = -1.0; bx <= 1.01; bx += 0.16) g.add(cyl(0.025, 0.025, 3.1, barM, [bx, 1.55, 1.62], { seg: 6 }));
  for (const by of [0.15, 1.05, 2.25, 3.05]) g.add(box(2.1, 0.06, 0.06, barM, [0, by, 1.62]));
  // bunk + blanket + pillow (left wall)
  const bunk = toon(0x5a6370);
  g.add(box(0.85, 0.08, 2.6, bunk, [-0.62, 0.5, -0.2]));
  for (const [dx, dz] of [[-0.25, -1.45], [-0.25, 1.05]]) g.add(box(0.06, 0.5, 0.06, bunk, [-0.62 + dx, 0.25, dz]));
  g.add(box(0.82, 0.12, 2.5, toon(0xd9d4c4), [-0.62, 0.6, -0.2]));
  const blanket = box(0.86, 0.2, 1.8, toon(0x5f6e5a), [-0.62, 0.72, 0.18]); g.add(blanket);
  g.add(box(0.6, 0.14, 0.45, toon(0xf2efe6), [-0.62, 0.73, -1.2]));
  // sink, toilet, shelf, vent (back wall, right)
  const white = toon(0xe8e6e0);
  g.add(box(0.46, 0.16, 0.36, white, [0.55, 1.35, -1.45]));
  if (toilet) g.add(cyl(0.18, 0.15, 0.4, white, [0.0, 0.2, -1.3]));
  g.add(box(0.9, 0.05, 0.3, toon(0x6d5a44), [-0.4, 2.0, -1.45]));
  for (let i = 0; i < 4; i++) g.add(box(0.08, 0.28, 0.2, toon([0x8b2e2e, 0x2e5b8b, 0x6b7d3a, 0xc9a24a][i]), [-0.7 + i * 0.1, 2.17, -1.45]));
  const ventT = canvasTex(128, 96, (c, w, h) => { c.fillStyle = '#1b1d21'; c.fillRect(0, 0, w, h); c.strokeStyle = '#8d939b'; c.lineWidth = 6; c.strokeRect(3, 3, w - 6, h - 6); c.lineWidth = 4; for (let i = 18; i < w; i += 16) { c.beginPath(); c.moveTo(i, 4); c.lineTo(i, h - 4); c.stroke(); } });
  const vent = mesh(new THREE.PlaneGeometry(0.42, 0.3), new THREE.MeshBasicMaterial({ map: ventT }), [0.55, 0.42, -1.59], { cast: false });
  g.add(vent);
  const hole = mesh(new THREE.PlaneGeometry(0.42, 0.3), basic(0x050505), [0.55, 0.42, -1.595], { cast: false }); g.add(hole);
  // corridor outside: floor, opposite wall, flickering bulb
  g.add(box(6, 0.1, 4, toon(0x55524d), [0, -0.05, 3.6]));
  g.add(box(6, 4, 0.2, wallM, [0, 2, 5.6]));
  const bulb = new THREE.PointLight(0xffd7a0, 9, 9, 1.4); bulb.position.set(0.4, 2.9, 2.6); g.add(bulb);
  g.add(sphere(0.07, new THREE.MeshBasicMaterial({ color: 0xfff1c9 }), [0.4, 2.95, 2.6], { cast: false }));
  flicker(S, bulb, { seed: flickerSeed });
  const moon = new THREE.SpotLight(0x8fb0ff, 25, 14, 0.5, 0.6, 1.2); moon.position.set(-1.5, 5, 4.5); moon.target.position.set(0, 0, -0.5);
  g.add(moon, moon.target);
  S.add(g);
  g.userData = { vent, hole, blanket, pillow: [x - 0.62, 0.8, -1.2] };
  return g;
}
