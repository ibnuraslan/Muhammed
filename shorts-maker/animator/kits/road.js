// kits/road.js - highways and vehicles: prairie highway at dusk/night, intercity bus (outside + inside),
// police car with a strobing light bar, semi truck, breaking-glass particles.
import { THREE, toon, basic, mesh, box, cyl, sphere, canvasTex, noiseTex, textPlane, rng, lerp, clamp } from '../engine.js';

// ---------------------------------------------------------------- skies
export function duskSky(S, o = {}) {
  S.sky({ top: '#232a5c', horizon: '#f19a58', bottom: '#5a3f2c', sun: [-300, 30, -160], sunColor: 0xffa060, sunI: 1.5, hemi: 0.75,
          ground: 0x6b5236, fog: [90, 700], shadow: 50, ...o });
}

// ---------------------------------------------------------------- prairie + highway (road along x at z = 0)
export function prairie(S, { seed = 3, poles = true, night = false } = {}) {
  const R = rng(seed);
  const field = noiseTex(night ? '#3c3a26' : '#a4924f', night ? ['#2f2d1d', '#4a4630'] : ['#b8a35c', '#8f7f43', '#c9b46a', '#7d6e3a'], 9000, 512, [80, 80], seed, [1, 4]);
  S.add(mesh(new THREE.PlaneGeometry(3000, 3000), toon(0xffffff, { map: field }), [0, 0, 0], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  const asphalt = canvasTex(256, 512, (g, w, h) => {
    g.fillStyle = '#3d3f44'; g.fillRect(0, 0, w, h);
    const r2 = rng(7); for (let i = 0; i < 1500; i++) { g.fillStyle = r2() < .5 ? '#34363a' : '#46484d'; g.fillRect(r2() * w, r2() * h, 2, 2); }
    g.fillStyle = '#e9e3c9'; g.fillRect(6, 0, 6, h); g.fillRect(w - 12, 0, 6, h);
    g.fillStyle = '#e2c341'; for (let y = 0; y < h; y += 128) g.fillRect(w / 2 - 4, y, 8, 64);
  }, [1, 120]);
  S.add(mesh(new THREE.PlaneGeometry(9, 3000), toon(0xffffff, { map: asphalt }), [0, 0.02, 0], { rot: [-Math.PI / 2, 0, Math.PI / 2], cast: false }));
  S.add(mesh(new THREE.PlaneGeometry(3000, 2.5), toon(0x8a7c62), [0, 0.015, 5.6], { rot: [-Math.PI / 2, 0, 0], cast: false }));   // gravel shoulder
  S.add(mesh(new THREE.PlaneGeometry(3000, 2.5), toon(0x8a7c62), [0, 0.015, -5.6], { rot: [-Math.PI / 2, 0, 0], cast: false }));
  if (poles) {
    const wood = toon(0x4a3826);
    for (let x = -600; x < 600; x += 45) {
      S.add(cyl(0.14, 0.18, 9, wood, [x, 4.5, -11], { seg: 6 }));
      S.add(box(2.4, 0.16, 0.16, wood, [x, 8.4, -11]));
    }
  }
  // a few distant farms + grain elevator for the prairie silhouette
  for (let i = 0; i < 6; i++) {
    const x = (R() - 0.5) * 900, z = -180 - R() * 260;
    S.add(box(10, 6, 8, toon(0x6e3b2a), [x, 3, z])); S.add(box(10.5, 1, 8.5, toon(0x3a2a22), [x, 6.4, z]));
    if (R() < 0.4) S.add(box(6, 26, 6, toon(0x9b8a74), [x + 14, 13, z]));
    for (let k = 0; k < 4; k++) S.add(sphere(3 + R() * 2, toon(0x3d4a2a), [x - 12 + k * 4, 3, z + 8], { seg: 8 }));
  }
}

// ---------------------------------------------------------------- intercity bus (front = +x, door on the +z side near the front)
// length 13, width 2.6, height ~3.5; group origin at road level, centre of the bus.
export function makeBus({ name = 'INTERCITY', dest = 'WINNIPEG', lit = 0.6 } = {}) {
  const g = new THREE.Group();
  const body = toon(0xe8ecef), stripe = toon(0x2b4e8c), dark = toon(0x1c2129), chrome = toon(0xb5bcc6);
  const L = 13, Wd = 2.6, Hb = 3.3, y0 = 0.55;
  g.add(box(L, Hb, Wd, body, [0, y0 + Hb / 2, 0]));
  g.add(box(L + 0.02, 0.35, Wd + 0.02, stripe, [0, y0 + 0.85, 0]));
  g.add(box(L + 0.02, 0.12, Wd + 0.02, stripe, [0, y0 + 2.95, 0]));
  // side windows (lit from inside)
  const winM = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffd9a0).multiplyScalar(lit), transparent: true, opacity: 0.95 });
  const winDark = new THREE.MeshBasicMaterial({ color: 0x0d1118 });
  g.userData.windows = [];
  for (const sd of [-1, 1]) for (let i = 0; i < 9; i++) {
    const w = mesh(new THREE.PlaneGeometry(1.15, 0.95), i === 8 && sd > 0 ? winDark : winM, [-5.6 + i * 1.32, y0 + 2.2, sd * (Wd / 2 + 0.01)], { rot: [0, sd > 0 ? 0 : Math.PI, 0], cast: false });
    g.add(w); g.userData.windows.push(w);
  }
  // windshield, door, sign, lights
  g.add(mesh(new THREE.PlaneGeometry(2.3, 1.7), winDark, [L / 2 + 0.01, y0 + 2.1, 0], { rot: [0, Math.PI / 2, 0], cast: false }));
  const door = mesh(new THREE.PlaneGeometry(0.95, 2.6), new THREE.MeshBasicMaterial({ color: 0x141a22, transparent: true, opacity: 0.55, depthWrite: false }), [L / 2 - 1.0, y0 + 1.45, Wd / 2 + 0.012], { cast: false });
  g.add(door); g.userData.door = door;
  const sign = textPlane(dest, { w: 2.0, h: 0.32, bg: '#111', fg: '#ffb43a', font: 'Display, sans-serif', size: 0.75 });
  sign.position.set(L / 2 + 0.02, y0 + 3.08, 0); sign.rotation.y = Math.PI / 2; g.add(sign);
  const nm = textPlane(name, { w: 4, h: 0.55, fg: '#2b4e8c', font: 'Display, sans-serif', size: 0.8 });
  nm.position.set(-1.5, y0 + 1.35, Wd / 2 + 0.015); g.add(nm);
  const nm2 = nm.clone(); nm2.position.z = -Wd / 2 - 0.015; nm2.rotation.y = Math.PI; g.add(nm2);
  const head = new THREE.MeshBasicMaterial({ color: 0xfff3d0 }), tail = new THREE.MeshBasicMaterial({ color: 0xff2a1a });
  for (const sd of [-1, 1]) {
    g.add(box(0.06, 0.25, 0.45, head, [L / 2 + 0.02, y0 + 0.55, sd * 0.85], { cast: false }));
    const t = box(0.06, 0.35, 0.3, tail, [-L / 2 - 0.02, y0 + 0.7, sd * 1.0], { cast: false }); g.add(t); (g.userData.tail ||= []).push(t);
  }
  for (const x of [L / 2 - 2.2, -L / 2 + 2.6, -L / 2 + 3.9]) for (const sd of [-1, 1]) {
    g.add(cyl(0.55, 0.55, 0.42, dark, [x, 0.55, sd * 1.12], { rot: [Math.PI / 2, 0, 0] }));
    g.add(cyl(0.3, 0.3, 0.44, chrome, [x, 0.55, sd * 1.12], { rot: [Math.PI / 2, 0, 0], cast: false }));
  }
  g.add(box(L - 0.4, 0.5, Wd - 0.2, dark, [0, 0.4, 0]));
  return g;
}

// ---------------------------------------------------------------- bus interior (aisle along x, seats face +x / the front)
// floor y=0, ceiling 2.45, walls z=±1.3. Seat rows at x = -5.4 + i*0.95. Window seats z=±0.95, aisle seats z=±0.5.
export function busInterior(S, { night = false, seed = 2 } = {}) {
  const g = new THREE.Group();
  g.add(box(13, 0.06, 2.6, toon(0x3a3d45), [0, -0.03, 0]));
  g.add(box(13, 0.06, 0.7, toon(0x55402f), [0, 0.005, 0]));                 // aisle runner
  const wallM = toon(0xbfc3c8);
  for (const sd of [-1, 1]) {
    g.add(box(13, 0.9, 0.08, wallM, [0, 0.45, sd * 1.32]));                  // below windows
    g.add(box(13, 0.5, 0.08, wallM, [0, 2.2, sd * 1.32]));                   // above windows
    for (let i = 0; i < 11; i++) g.add(box(0.16, 1.1, 0.1, wallM, [-5.95 + i * 1.19, 1.45, sd * 1.32]));
    g.add(box(13, 0.08, 0.55, toon(0x8d9299), [0, 2.05, sd * 1.05]));        // luggage rack
  }
  g.add(box(13, 0.08, 2.7, toon(0xd6d8dc), [0, 2.48, 0]));
  g.add(box(0.1, 2.5, 2.6, wallM, [-6.5, 1.25, 0]));                         // back wall
  g.add(box(0.12, 2.0, 0.8, toon(0x8a8f96), [-6.42, 1.0, 0.9]));             // toilet door
  // view out of the windows: scrolling prairie (scroll it with S.onUpdate via userData.view)
  const view = canvasTex(1024, 256, (c, w, h) => {
    const gr = c.createLinearGradient(0, 0, 0, h * 0.65);
    if (night) { gr.addColorStop(0, '#05081a'); gr.addColorStop(1, '#1b2747'); } else { gr.addColorStop(0, '#3b3f78'); gr.addColorStop(0.7, '#f39b5a'); gr.addColorStop(1, '#ffc27a'); }
    c.fillStyle = gr; c.fillRect(0, 0, w, h);
    c.fillStyle = night ? '#0c0f14' : '#7a6337'; c.fillRect(0, h * 0.64, w, h);
    c.fillStyle = night ? '#07090c' : '#3b2c1c';
    for (let x = 30; x < w; x += 140) { c.fillRect(x, h * 0.2, 5, h * 0.48); c.fillRect(x - 18, h * 0.22, 41, 5); }
    for (let x = 90; x < w; x += 330) { c.fillRect(x, h * 0.52, 60, h * 0.13); }
  }, [1, 1]);
  view.wrapS = THREE.RepeatWrapping; view.repeat.set(0.35, 1);
  const viewM = new THREE.MeshBasicMaterial({ map: view, toneMapped: false });
  for (const sd of [-1, 1]) g.add(mesh(new THREE.PlaneGeometry(13, 1.1), viewM, [0, 1.45, sd * 1.36], { rot: [0, sd > 0 ? Math.PI : 0, 0], cast: false }));
  // seats
  const seatM = toon(0x283a63), headM = toon(0x9aa3b2);
  for (let i = 0; i < 12; i++) for (const sd of [-1, 1]) for (const z of [0.95, 0.5]) {
    const x = -5.4 + i * 0.95;
    g.add(box(0.5, 0.12, 0.44, seatM, [x + 0.05, 0.48, sd * z]));
    g.add(box(0.1, 0.62, 0.44, seatM, [x - 0.2, 0.85, sd * z]));
    g.add(box(0.12, 0.16, 0.38, headM, [x - 0.2, 1.22, sd * z]));
  }
  // ceiling light strip (flicker it with userData.light)
  const stripM = new THREE.MeshBasicMaterial({ color: night ? 0x9a8f78 : 0xe8d2a8 });
  g.add(box(12, 0.04, 0.18, stripM, [0, 2.44, 0], { cast: false }));
  const light = new THREE.PointLight(night ? 0xffc890 : 0xffd9a8, night ? 9 : 9, 14, 1.4); light.position.set(-2, 2.3, 0); g.add(light);
  S.add(g);
  S.onUpdate((t) => { view.offset.x = t * 0.25; });
  g.userData = { light, strip: stripM, view };
  return g;
}

// ---------------------------------------------------------------- police car with strobing red/blue light bar
export function policeCar(S, x, z, { rotY = 0, seed = 1 } = {}) {
  const g = new THREE.Group();
  const white = toon(0xf1f1f1), navy = toon(0x1d2a4a), dark = toon(0x14171c);
  g.add(box(4.6, 0.8, 1.9, white, [0, 0.75, 0])); g.add(box(2.4, 0.65, 1.75, white, [-0.3, 1.45, 0]));
  g.add(box(4.62, 0.22, 1.92, navy, [0, 0.8, 0]));
  for (const sd of [-1, 1]) g.add(mesh(new THREE.PlaneGeometry(2.1, 0.5), new THREE.MeshBasicMaterial({ color: 0x10151c }), [-0.3, 1.47, sd * 0.885], { rot: [0, sd > 0 ? 0 : Math.PI, 0], cast: false }));
  for (const [dx, dz] of [[1.5, 0.9], [1.5, -0.9], [-1.5, 0.9], [-1.5, -0.9]]) g.add(cyl(0.36, 0.36, 0.3, dark, [dx, 0.36, dz], { rot: [Math.PI / 2, 0, 0] }));
  const red = new THREE.MeshBasicMaterial({ color: 0xff2020 }), blue = new THREE.MeshBasicMaterial({ color: 0x2050ff });
  const rb = box(0.3, 0.16, 0.6, red, [-0.3, 1.86, 0.35], { cast: false }), bb = box(0.3, 0.16, 0.6, blue, [-0.3, 1.86, -0.35], { cast: false });
  g.add(rb, bb);
  const lr = new THREE.PointLight(0xff2020, 0, 18, 1.5), lb = new THREE.PointLight(0x2050ff, 0, 18, 1.5);
  lr.position.set(-0.3, 2.2, 0.6); lb.position.set(-0.3, 2.2, -0.6); g.add(lr, lb);
  g.position.set(x, 0, z); g.rotation.y = rotY; S.add(g);
  S.onUpdate((t) => {
    const ph = (t * 4 + seed * 0.37) % 1, on = ph < 0.5;
    lr.intensity = on ? 40 : 0; lb.intensity = on ? 0 : 40;
    red.color.setHex(on ? 0xff3030 : 0x401010); blue.color.setHex(on ? 0x101840 : 0x3060ff);
  });
  return g;
}

// ---------------------------------------------------------------- semi truck (front = +x)
export function semiTruck(S, x, z, { rotY = 0, color = 0xa8322a } = {}) {
  const g = new THREE.Group(), cab = toon(color), dark = toon(0x16191e), chrome = toon(0xb5bcc6);
  g.add(box(2.6, 2.6, 2.4, cab, [5.2, 1.9, 0])); g.add(box(1.2, 1.4, 2.4, cab, [6.9, 1.3, 0]));
  g.add(mesh(new THREE.PlaneGeometry(1.8, 0.9), new THREE.MeshBasicMaterial({ color: 0x10151c }), [6.52, 2.5, 0], { rot: [0, Math.PI / 2, 0], cast: false }));
  g.add(box(9.5, 3.2, 2.5, toon(0xd9d6cf), [-1.2, 2.3, 0]));
  for (const dx of [6.2, 4.4, -3.6, -4.9]) for (const sd of [-1, 1]) g.add(cyl(0.5, 0.5, 0.4, dark, [dx, 0.5, sd * 1.1], { rot: [Math.PI / 2, 0, 0] }));
  g.add(cyl(0.12, 0.12, 2.6, chrome, [4.0, 3.2, 1.0], { seg: 8 }));
  g.position.set(x, 0, z); g.rotation.y = rotY; S.add(g); return g;
}

// ---------------------------------------------------------------- breaking glass: shards burst from a point
// call shards.userData.burst(k) every frame with k = seconds since the break
export function glassShards(S, pos, { n = 90, dir = [0, 0, 1], seed = 5 } = {}) {
  const R = rng(seed), im = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.09, 0.06), new THREE.MeshBasicMaterial({ color: 0xdff2ff, side: THREE.DoubleSide, transparent: true, opacity: 0.9 }), n);
  const v = []; for (let i = 0; i < n; i++) v.push([dir[0] * (1 + R() * 3) + (R() - .5) * 2, 1 + R() * 2.5, dir[2] * (1 + R() * 3) + (R() - .5) * 2, R() * 6, R() * 6]);
  const d = new THREE.Object3D(); S.add(im); im.visible = false;
  im.userData.burst = (k) => {
    im.visible = k > 0 && k < 2.5; if (!im.visible) return;
    v.forEach(([vx, vy, vz, a, b], i) => {
      d.position.set(pos[0] + vx * k, Math.max(0.02, pos[1] + vy * k - 4.9 * k * k), pos[2] + vz * k);
      d.rotation.set(a + k * 9, b + k * 7, 0); d.updateMatrix(); im.setMatrixAt(i, d.matrix);
    });
    im.instanceMatrix.needsUpdate = true;
  };
  return im;
}
