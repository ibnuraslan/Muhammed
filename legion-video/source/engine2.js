// ===================== v2 models: correct gauge, connected running gear, better people =====================
import { THREE, mat, pbr, mesh, rng, lerp, clamp } from './engine.js';
import { buildFace } from './face.js';
export const GAUGE = .762, RAIL_TOP = .43;   // half of Russian 1524mm gauge; rail head height
const shadowAll = o => { o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } }); return o; };

export function track2(len = 400, x0 = -200) {
  const g = new THREE.Group(), sleeper = pbr('old_wood_floor', [1, .2], { color: 0x6a5a4a }), steel = mat(0x5a5a60, .35, .85), head = mat(0x9a9aa2, .25, .95), ballast = pbr('gravel', [len / 4, 1], { color: 0x8a847a });
  const bs = new THREE.Shape(); bs.moveTo(-2.3, 0); bs.lineTo(-1.6, .26); bs.lineTo(1.6, .26); bs.lineTo(2.3, 0); const bg = new THREE.ExtrudeGeometry(bs, { depth: len, bevelEnabled: false }); bg.rotateY(Math.PI / 2); bg.translate(x0, 0, 0);
  const b = new THREE.Mesh(bg, ballast); b.receiveShadow = true; g.add(b);
  const n = Math.floor(len / .6), sl = new THREE.InstancedMesh(new THREE.BoxGeometry(.24, .14, 2.7), sleeper, n), m4 = new THREE.Matrix4(); for (let i = 0; i < n; i++) { m4.makeTranslation(x0 + i * .6, .31, 0); sl.setMatrixAt(i, m4); } sl.receiveShadow = sl.castShadow = true; g.add(sl);
  for (const z of [-GAUGE, GAUGE]) { mesh(new THREE.BoxGeometry(len, .1, .07), steel, [x0 + len / 2, .36, z], [0, 0, 0], g); mesh(new THREE.BoxGeometry(len, .04, .075), head, [x0 + len / 2, RAIL_TOP - .02, z], [0, 0, 0], g); }
  return g;
}
function spokedWheel(r, col, hub) { const w = new THREE.Group(); mesh(new THREE.TorusGeometry(r * .9, r * .1, 10, 40), col, [0, 0, 0], [0, 0, 0], w); mesh(new THREE.CylinderGeometry(r, r, .09, 40), mat(0x2a2a2a, .35, .9), [0, 0, .07], [Math.PI / 2, 0, 0], w); const n = Math.max(8, Math.round(r * 16)); for (let k = 0; k < n; k++) mesh(new THREE.BoxGeometry(.045, r * 1.75, .05), col, [0, 0, 0], [0, 0, k * Math.PI / n], w); mesh(new THREE.CylinderGeometry(r * .2, r * .2, .16, 18), hub || col, [0, 0, 0], [Math.PI / 2, 0, 0], w); return w; }

export function locomotive2(o = {}) {
  const g = new THREE.Group(), body = mat(o.color || 0x1c2622, .42, .55), black = mat(0x121212, .5, .6), red = mat(0x7a1610, .55, .3), brass = mat(0xc9a24d, .28, .95), steel = mat(0xb4b4bc, .25, .95);
  const DR = .78, LR = .45, yD = RAIL_TOP + DR, yL = RAIL_TOP + LR, driversX = [-1.6, 0, 1.6], pilotX = 3.6;
  // frame plates (inside the wheels) + buffer beams
  for (const z of [-.55, .55]) mesh(new THREE.BoxGeometry(8.4, .75, .08), black, [.6, yD - .05, z], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(.25, .55, 2.6), red, [4.85, yL + .2, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.25, .55, 2.6), red, [-3.6, yD - .1, 0], [0, 0, 0], g);
  for (const z of [-.85, .85]) { mesh(new THREE.CylinderGeometry(.12, .14, .45, 14), black, [5.15, yL + .2, z], [0, 0, Math.PI / 2], g); mesh(new THREE.CylinderGeometry(.27, .27, .06, 20), steel, [5.39, yL + .2, z], [0, 0, Math.PI / 2], g); }
  const pilot = new THREE.Shape(); pilot.moveTo(0, 0); pilot.lineTo(.9, -.65); pilot.lineTo(0, -.65); const pg = new THREE.ExtrudeGeometry(pilot, { depth: 2.4, bevelEnabled: false }); pg.translate(0, 0, -1.2); mesh(pg, red, [4.95, yL, 0], [0, 0, 0], g);
  // running boards & splashers over the drivers
  for (const z of [-1.25, 1.25]) { mesh(new THREE.BoxGeometry(8.6, .06, .55), black, [.7, yD + DR + .14, z], [0, 0, 0], g); for (const x of driversX) mesh(new THREE.CylinderGeometry(DR + .12, DR + .12, .5, 24, 1, false, -Math.PI / 2, Math.PI), body, [x, yD, z], [Math.PI / 2, 0, 0], g); }
  // boiler on saddle
  const by = yD + DR + .95; mesh(new THREE.CylinderGeometry(.92, .92, 5.6, 40), body, [1.2, by, 0], [0, 0, Math.PI / 2], g);
  for (let i = 0; i < 4; i++) mesh(new THREE.CylinderGeometry(.94, .94, .07, 40), brass, [-.9 + i * 1.4, by, 0], [0, 0, Math.PI / 2], g);
  mesh(new THREE.CylinderGeometry(.99, .99, 1.2, 40), black, [4.55, by, 0], [0, 0, Math.PI / 2], g); mesh(new THREE.BoxGeometry(1.0, .9, 1.4), black, [4.55, yD + DR - .1, 0], [0, 0, 0], g);
  mesh(new THREE.CircleGeometry(.82, 40), mat(0x181818, .55, .6), [5.16, by, 0], [0, Math.PI / 2, 0], g); mesh(new THREE.TorusGeometry(.82, .04, 8, 40), steel, [5.16, by, 0], [0, Math.PI / 2, 0], g);
  for (let k = 0; k < 6; k++) { const a = k / 6 * Math.PI * 2; mesh(new THREE.BoxGeometry(.06, .06, .06), steel, [5.18, by + Math.sin(a) * .7, Math.cos(a) * .7], [0, 0, 0], g); }
  const chim = new THREE.LatheGeometry([[0, 0], [.3, 0], [.27, .35], [.29, .95], [.46, 1.25], [.48, 1.35], [0, 1.35]].map(p => new THREE.Vector2(...p)), 32); mesh(chim, black, [4.55, by + .78, 0], [0, 0, 0], g);
  mesh(new THREE.SphereGeometry(.44, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), brass, [1.8, by + .95, 0], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(.42, .46, .3, 24), body, [1.8, by + .85, 0], [0, 0, 0], g);
  mesh(new THREE.SphereGeometry(.34, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), body, [3.2, by + .92, 0], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(.32, .36, .2, 24), body, [3.2, by + .85, 0], [0, 0, 0], g);
  mesh(new THREE.CylinderGeometry(.06, .06, .5, 10), brass, [-1.6, by + 1.05, 0], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(.1, .04, .25, 10), brass, [-1.6, by + 1.35, 0], [0, 0, 0], g);
  const lamp = mesh(new THREE.BoxGeometry(.3, .4, .35), black, [5.2, by + .95, 0], [0, 0, 0], g); mesh(new THREE.CircleGeometry(.12, 16), mat(0xfff0c0, .2, 0, { emissive: o.lamp ? 0xffd890 : 0x222018, emissiveIntensity: o.lamp ? 3 : 1 }), [5.36, by + .95, 0], [0, Math.PI / 2, 0], g);
  for (const z of [-.95, .95]) mesh(new THREE.CylinderGeometry(.045, .045, 5.2, 8), brass, [1.0, by - .65, z], [0, 0, Math.PI / 2], g);
  // cylinders + slide bars
  for (const z of [-1.12, 1.12]) { mesh(new THREE.CylinderGeometry(.34, .34, 1.0, 24), black, [3.3, yD - .05, z], [0, 0, Math.PI / 2], g); mesh(new THREE.CylinderGeometry(.36, .36, .06, 24), steel, [3.82, yD - .05, z], [0, 0, Math.PI / 2], g); mesh(new THREE.BoxGeometry(1.5, .05, .05), steel, [2.25, yD + .08, z], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.5, .05, .05), steel, [2.25, yD - .18, z], [0, 0, 0], g); }
  // cab
  const cx = -2.7; mesh(new THREE.BoxGeometry(2.0, 2.4, 2.7), body, [cx, yD + DR + 1.3, 0], [0, 0, 0], g);
  for (const z of [-1.36, 1.36]) { mesh(new THREE.BoxGeometry(.8, .75, .03), mat(o.lamp ? 0xffc870 : 0x1a242c, .15, .3, { emissive: o.lamp ? 0xffa040 : 0, emissiveIntensity: 1.5 }), [cx + .25, yD + DR + 1.85, z], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.9, .06, .05), brass, [cx + .25, yD + DR + 2.26, z * 1.005], [0, 0, 0], g); }
  const rg = new THREE.CylinderGeometry(2.4, 2.4, 2.3, 32, 1, false, Math.PI / 2 - .62, 1.24); rg.rotateZ(Math.PI / 2); rg.rotateY(Math.PI / 2);
  mesh(rg, mat(0x262626, .7, .3), [cx, yD + DR + 2.62 - 2.4, 0], [0, 0, 0], g);
  // tender
  const tx = -5.9, TR = .45, yT = RAIL_TOP + TR; mesh(new THREE.BoxGeometry(3.8, .3, 2.5), red, [tx, yT + .45, 0], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(3.8, 1.6, 2.6), body, [tx, yT + 1.4, 0], [0, 0, 0], g); const coal = new THREE.Mesh(new THREE.DodecahedronGeometry(1.15, 1), mat(0x0c0c0c, .95, .1)); coal.scale.set(1.45, .32, .95); coal.position.set(tx, yT + 2.25, 0); g.add(coal);
  // wheels on the rails
  const drivers = [], others = [];
  for (const x of driversX) for (const z of [-GAUGE, GAUGE]) { const w = spokedWheel(DR, red); w.position.set(x, yD, z * 1.0 + (z > 0 ? .02 : -.02)); w.rotation.y = z > 0 ? 0 : Math.PI; g.add(w); drivers.push(w); }
  for (const z of [-GAUGE, GAUGE]) { const w = spokedWheel(LR, red); w.position.set(pilotX, yL, z); w.rotation.y = z > 0 ? 0 : Math.PI; g.add(w); others.push([w, LR]); }
  for (const x of [tx - 1.1, tx + 1.1]) for (const z of [-GAUGE, GAUGE]) { const w = spokedWheel(TR, black); w.position.set(x, yT, z); w.rotation.y = z > 0 ? 0 : Math.PI; g.add(w); others.push([w, TR]); }
  for (const x of driversX) mesh(new THREE.CylinderGeometry(.09, .09, 2 * GAUGE, 10), black, [x, yD, 0], [Math.PI / 2, 0, 0], g);
  // rods (outside the wheels): coupling rod joins crank pins; main rod goes to the crosshead
  const pinR = .36, rodZ = GAUGE + .16, coupling = [], mainRod = [], cross = [];
  for (const s of [-1, 1]) { coupling.push(mesh(new THREE.BoxGeometry(3.4, .11, .05), steel, [0, yD, s * rodZ], [0, 0, 0], g)); mainRod.push(mesh(new THREE.BoxGeometry(2.4, .12, .05), steel, [0, yD, s * (rodZ + .07)], [0, 0, 0], g)); cross.push(mesh(new THREE.BoxGeometry(.25, .3, .1), steel, [2.6, yD - .05, s * 1.12], [0, 0, 0], g)); for (const x of driversX) { const pin = mesh(new THREE.CylinderGeometry(.06, .06, .2, 10), steel, [0, 0, 0], [Math.PI / 2, 0, 0], g); pin.userData = { x, s }; coupling.push(pin); } }
  g.userData.update = dist => { // dist = distance travelled (m) -> rotation
    const a = -dist / DR;
    drivers.forEach(w => w.rotation.z = w.position.z > 0 ? a : -a); others.forEach(([w, r]) => w.rotation.z = (w.position.z > 0 ? 1 : -1) * -dist / r);
    const px = Math.cos(a) * pinR, py = Math.sin(a) * pinR;
    for (const s of [0, 1]) { const c = coupling[s * 4]; c.position.set(px, yD + py, c.position.z); }
    coupling.forEach(p => { if (p.userData.x !== undefined) p.position.set(p.userData.x + px, yD + py, p.userData.s * (rodZ + .03)); });
    cross.forEach((c, i) => { const cxp = 2.55 + px; c.position.x = cxp; const m = mainRod[i], ax = 0 + px, ay = yD + py, bx = cxp, byy = yD - .05; m.position.set((ax + bx) / 2, (ay + byy) / 2, m.position.z); m.rotation.z = Math.atan2(byy - ay, bx - ax); m.scale.x = Math.hypot(bx - ax, byy - ay) / 2.4; });
  };
  g.userData.update(0);
  g.userData.chimney = new THREE.Vector3(4.55, by + 2.2, 0); g.userData.cylinder = new THREE.Vector3(3.9, yD - .05, 1.2);
  g.userData.frontX = 5.4; g.userData.backX = tx - 1.95;
  return shadowAll(g);
}

export function boxcar2(o = {}) {
  const g = new THREE.Group(), planks = pbr('brown_planks_05', [3, 1], { color: o.tint || 0xb06648 }), black = mat(0x151515, .55, .6), steel = mat(0x8a8a90, .3, .9), dark = mat(0x0a0806, 1);
  const WR = .48, yW = RAIL_TOP + WR, L = 7.4;
  // sole bars & underframe (rest on the axle boxes)
  for (const z of [-1.25, 1.25]) mesh(new THREE.BoxGeometry(L + .3, .3, .14), black, [0, yW + .62, z], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(L + .3, .1, 2.5), black, [0, yW + .5, 0], [0, 0, 0], g);
  for (const x of [-L / 2 - .2, L / 2 + .2]) { mesh(new THREE.BoxGeometry(.2, .35, 2.8), black, [x, yW + .62, 0], [0, 0, 0], g); for (const z of [-.85, .85]) { mesh(new THREE.CylinderGeometry(.11, .13, .42, 14), black, [x + Math.sign(x) * .3, yW + .62, z], [0, 0, Math.PI / 2], g); mesh(new THREE.CylinderGeometry(.24, .24, .05, 18), steel, [x + Math.sign(x) * .52, yW + .62, z], [0, 0, Math.PI / 2], g); } }
  // body
  const by0 = yW + .77; mesh(new THREE.BoxGeometry(L, 2.6, 2.75), planks, [0, by0 + 1.3, 0], [0, 0, 0], g);
  for (const x of [-L / 2, -L / 4, 0, L / 4, L / 2]) for (const z of [-1.39, 1.39]) mesh(new THREE.BoxGeometry(.1, 2.6, .04), black, [x, by0 + 1.3, z], [0, 0, 0], g);
  for (const z of [-1.39, 1.39]) { mesh(new THREE.BoxGeometry(L, .1, .04), black, [0, by0 + 2.55, z], [0, 0, 0], g); mesh(new THREE.BoxGeometry(L, .1, .04), black, [0, by0 + .05, z], [0, 0, 0], g); }
  const roofG = new THREE.CylinderGeometry(3.6, 3.6, L + .3, 40, 1, false, Math.PI / 2 - .42, .84); roofG.rotateZ(Math.PI / 2);
  mesh(roofG, mat(0x3a3a3c, .8, .3), [0, by0 + 2.85 - 3.6, 0], [0, 0, 0], g);
  // sliding door (open amount), interior darkness, windows
  if (o.flat) { g.children.slice(-((L <= 0) ? 0 : 0)); }
  const open = o.open ?? 0; g.userData.doorDark = mesh(new THREE.BoxGeometry(1.9, 2.25, .05), dark, [0, by0 + 1.2, 1.39], [0, 0, 0], g); g.userData.by0 = by0;
  g.userData.doorPanel = mesh(new THREE.BoxGeometry(2.0, 2.35, .08), planks, [open * 2.0, by0 + 1.2, 1.44], [0, 0, 0], g); mesh(new THREE.BoxGeometry(4.6, .07, .07), steel, [.7, by0 + 2.42, 1.46], [0, 0, 0], g);
  for (const x of [-2.6, 2.6]) mesh(new THREE.BoxGeometry(.5, .32, .04), dark, [x, by0 + 2.0, 1.4], [0, 0, 0], g);
  if (o.stove !== false) { mesh(new THREE.CylinderGeometry(.08, .08, .9, 12), black, [-2.2, by0 + 2.9, .6], [0, 0, 0], g); mesh(new THREE.ConeGeometry(.16, .15, 12), black, [-2.2, by0 + 3.4, .6], [0, 0, 0], g); }
  // wheelsets with axle boxes and leaf springs (connect to sole bars)
  const wheels = [];
  for (const x of [-2.4, 2.4]) { mesh(new THREE.CylinderGeometry(.07, .07, 2 * GAUGE + .3, 10), black, [x, yW, 0], [Math.PI / 2, 0, 0], g);
    for (const z of [-GAUGE, GAUGE]) { const w = spokedWheel(WR, black, steel); w.position.set(x, yW, z); w.rotation.y = z > 0 ? 0 : Math.PI; g.add(w); wheels.push(w);
      const zz = z + Math.sign(z) * .33; mesh(new THREE.BoxGeometry(.32, .34, .2), black, [x, yW, zz], [0, 0, 0], g);
      const spring = mesh(new THREE.BoxGeometry(1.3, .14, .14), steel, [x, yW + .3, zz], [0, 0, 0], g); spring.scale.y = 1;
      for (const dx of [-.62, .62]) mesh(new THREE.BoxGeometry(.06, .3, .06), black, [x + dx, yW + .45, zz], [0, 0, 0], g); } }
  g.userData.update = dist => wheels.forEach(w => w.rotation.z = (w.position.z > 0 ? 1 : -1) * -dist / WR);
  g.userData.stovepipe = new THREE.Vector3(-2.2, by0 + 3.5, .6);
  g.userData.length = L + 1.1;
  return shadowAll(g);
}

// ---------------- people ----------------
function furTexture(col) { const cv = document.createElement('canvas'); cv.width = cv.height = 128; const x = cv.getContext('2d'); x.fillStyle = col; x.fillRect(0, 0, 128, 128); const r = rng(5); for (let i = 0; i < 900; i++) { x.strokeStyle = `rgba(${r() < .5 ? '255,255,255' : '0,0,0'},${r() * .22})`; x.lineWidth = 1.5; const px = r() * 128, py = r() * 128; x.beginPath(); x.arc(px, py, 2 + r() * 3, r() * 6, r() * 6 + 2); x.stroke(); } const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 1); return t; }
export const KIT = {
  legion: { coat: 0x5c5a40, trou: 0x4e4c36, hat: 'papakha', hatC: '#2e241c', ribbon: true },
  legionCap: { coat: 0x66623f, trou: 0x55523a, hat: 'peaked', hatC: 0x5e5a3c, ribbon: true },
  red: { coat: 0x1c1816, trou: 0x24201c, hat: 'leather', hatC: 0x141210, leather: true, band: true },
  pow: { coat: 0x707068, trou: 0x5a5a54, hat: 'kepi', hatC: 0x6a6a64 },
  civil: { coat: 0x34343c, trou: 0x2a2a30, hat: 'cap', hatC: 0x2a2a30 },
  suit: { coat: 0x2a2a30, trou: 0x24242a, hat: 'none', hatC: 0x222222 },
  russian: { coat: 0x8a8460, trou: 0x6a6448, hat: 'cap', hatC: 0x7a7454 },
  austro: { coat: 0x7a8288, trou: 0x6a7276, hat: 'kepi', hatC: 0x6e767a },
  french: { coat: 0x7088a8, trou: 0x5a7090, hat: 'kepi', hatC: 0x6a80a0 },
  british: { coat: 0x7a6a44, trou: 0x6a5a3a, hat: 'peaked', hatC: 0x6a5a3a },
  usa: { coat: 0x6a6440, trou: 0x5a5436, hat: 'peaked', hatC: 0x5a5436 },
  japan: { coat: 0x6e6a44, trou: 0x5e5a3a, hat: 'cap', hatC: 0x5e5a3a, ribbon: false },
  woman: { coat: 0x5a3a3a, trou: 0x3a2a2a, hat: 'none', hatC: 0x2a2a30 },
  sailor: { coat: 0x22283a, trou: 0x22283a, hat: 'cap', hatC: 0xe8e8e8 },
};
export function person2(o = {}) {
  const k = { ...KIT[o.u || 'legion'], ...(o.kit || {}) }, r = rng((o.seed || 1) * 13 + 7), g = new THREE.Group();
  const skinC = [0xd8a27a, 0xc8906c, 0xe2b08e, 0xb87e58][Math.floor(r() * 4)], skin = mat(skinC, .62), hairC = [0x2a1a12, 0x4a2e1c, 0x6a4a2a, 0x3a2a20][Math.floor(r() * 4)], hair = mat(hairC, .9);
  const coat = mat(k.coat, k.leather ? .45 : .95, k.leather ? .15 : 0), coatDk = mat(new THREE.Color(k.coat).multiplyScalar(.75), .95), trou = mat(k.trou, .95), boot = mat(0x16110d, .45, .1), belt = mat(0x3e2a1a, .6), brass = mat(0xc9a24d, .3, .9);
  // --- legs (thigh + shin with knee) ---
  const pelvis = new THREE.Group(); pelvis.position.y = .95; g.add(pelvis);
  const legs = [-1, 1].map(s => { const hip = new THREE.Group(); hip.position.set(0, 0, s * .1); pelvis.add(hip); mesh(new THREE.CylinderGeometry(.085, .07, .46, 14), trou, [0, -.23, 0], [0, 0, 0], hip); const knee = new THREE.Group(); knee.position.y = -.46; hip.add(knee); mesh(new THREE.CylinderGeometry(.068, .062, .42, 14), boot, [0, -.21, 0], [0, 0, 0], knee); const foot = mesh(new THREE.BoxGeometry(.27, .085, .11), boot, [.06, -.45, 0], [0, 0, 0], knee); return { hip, knee }; });
  // --- torso & greatcoat ---
  const spine = new THREE.Group(); spine.position.y = .95; g.add(spine);
  const prof = [[.0, -.62], [.3, -.62], [.28, -.3], [.24, -.02], [.21, .05], [.215, .28], [.235, .45], [.2, .5], [.1, .53], [0, .54]];
  const coatG = new THREE.LatheGeometry(prof.map(p => new THREE.Vector2(p[0], p[1])), 28); const cm = mesh(coatG, coat, [0, 0, 0], [0, 0, 0], spine); cm.scale.set(.82, 1, 1);
  if (o.long === false) cm.scale.y = .8;
  mesh(new THREE.TorusGeometry(.2, .026, 8, 28), belt, [0, .02, 0], [Math.PI / 2, 0, 0], spine).scale.set(.84, 1, 1);
  mesh(new THREE.BoxGeometry(.05, .06, .03), brass, [.17, .02, 0], [0, 0, 0], spine);
  for (let i = 0; i < 4; i++) for (const z of [-.07, .07]) mesh(new THREE.SphereGeometry(.013, 8, 6), brass, [.188, .4 - i * .11, z], [0, 0, 0], spine);
  const col = mesh(new THREE.CylinderGeometry(.11, .15, .12, 18, 1, true), coatDk, [0, .53, 0], [0, 0, 0], spine); col.material.side = THREE.DoubleSide;
  for (const s of [-1, 1]) mesh(new THREE.BoxGeometry(.06, .02, .12), coatDk, [0, .51, s * .2], [0, 0, 0], spine);
  if (k.band) mesh(new THREE.CylinderGeometry(.068, .068, .09, 12), mat(0xb81a14, .7), [0, .3, -.26], [0, 0, 0], spine);
  // --- arms (upper + forearm + hand) ---
  const arms = [-1, 1].map(s => { const sh = new THREE.Group(); sh.position.set(0, .46, s * .23); spine.add(sh); mesh(new THREE.SphereGeometry(.075, 12, 10), coat, [0, 0, 0], [0, 0, 0], sh); mesh(new THREE.CylinderGeometry(.068, .06, .3, 12), coat, [0, -.16, 0], [0, 0, 0], sh); const el = new THREE.Group(); el.position.y = -.31; sh.add(el); mesh(new THREE.CylinderGeometry(.06, .066, .27, 12), coat, [0, -.13, 0], [0, 0, 0], el); mesh(new THREE.CylinderGeometry(.068, .068, .05, 12), coatDk, [0, -.25, 0], [0, 0, 0], el); const hand = mesh(new THREE.CapsuleGeometry(.032, .05, 4, 10), skin, [.005, -.31, 0], [0, 0, 0], el); hand.scale.set(1.1, 1, .7); mesh(new THREE.CapsuleGeometry(.013, .03, 4, 8), skin, [.03, -.29, s * .02], [0, 0, -.6], el); return { sh, el, hand }; });
  // --- head ---
  const neck = new THREE.Group(); neck.position.y = .56; spine.add(neck);
  mesh(new THREE.CylinderGeometry(.055, .06, .1, 12), skin, [0, .02, 0], [0, 0, 0], neck);
  const head = new THREE.Group(); head.position.y = .115; neck.add(head);
  buildFace(head, { seed: o.seed || 1, skin: skinC, hair: hairC, eye: ['#4a3a22', '#4a6a7a', '#3a4a2a'][Math.floor(r() * 3)], beard: o.beard ?? (o.u === 'woman' ? 0 : r() < .4 ? .3 + r() * .7 : 0), noMustache: o.noMustache ?? (o.u === 'woman' || r() < .2), y0: .02, hair: o.hairC ?? hairC });
  const nHead0 = head.children.length;
  // --- headgear ---
  if (k.hat === 'papakha') { const fm = new THREE.MeshStandardMaterial({ map: furTexture(k.hatC), roughness: 1 }); mesh(new THREE.CylinderGeometry(.122, .116, .15, 24), fm, [0, .19, 0], [0, 0, 0], head); mesh(new THREE.CylinderGeometry(.114, .114, .01, 24), fm, [0, .27, 0], [0, 0, 0], head); }
  else if (k.hat === 'peaked' || k.hat === 'kepi' || k.hat === 'cap') { const tall = k.hat === 'kepi' ? .12 : .07; mesh(new THREE.CylinderGeometry(k.hat === 'peaked' ? .135 : .113, .113, tall, 24), mat(k.hatC, .9), [-.005, .105 + tall / 2, 0], [0, 0, k.hat === 'kepi' ? -.1 : .04], head); mesh(new THREE.CylinderGeometry(.115, .115, .012, 20, 1, false, 0, Math.PI), mat(0x0c0c0c, .3, .2), [.04, .108, 0], [0, 0, -.15], head); if (k.hat !== 'cap') mesh(new THREE.SphereGeometry(.014, 8, 6), mat(0xc9a24d, .3, .9), [.12, .15, 0], [0, 0, 0], head); }
  else if (k.hat === 'leather') { mesh(new THREE.SphereGeometry(.122, 20, 12, 0, Math.PI * 2, 0, Math.PI / 2), mat(k.hatC, .3, .25), [0, .12, 0], [0, 0, 0], head).scale.set(1.05, .75, 1.05); mesh(new THREE.CylinderGeometry(.12, .12, .012, 20, 1, false, -Math.PI / 2, Math.PI), mat(0x060606, .3), [.04, .12, 0], [0, 0, -.1], head); mesh(new THREE.SphereGeometry(.016, 8, 6), mat(0xc8241c, .5), [.12, .17, 0], [0, 0, 0], head); }
  if (k.ribbon) { const y0 = k.hat === 'papakha' ? .14 : .115, rr = k.hat === 'papakha' ? .127 : .116; mesh(new THREE.CylinderGeometry(rr, rr, .018, 24), mat(0xf2f0ea, .7), [0, y0 + .02, 0], [0, 0, 0], head); mesh(new THREE.CylinderGeometry(rr, rr, .018, 24), mat(0xc8241c, .7), [0, y0, 0], [0, 0, 0], head); }
  head.children.slice(nHead0).forEach(c => { c.position.y -= .045; });
  // --- rifle on sling over the left shoulder ---
  if (o.rifle !== false && o.RIFLE) { const rf = o.RIFLE.clone(true); rf.scale.setScalar(.95); const holder = new THREE.Group(); holder.add(rf);
    holder.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), new THREE.Vector3(-.12, .86, .5).normalize()); holder.rotateX(o.flip ? Math.PI : 0);
    holder.position.set(-.27, .08, 0); spine.add(holder); g.userData.rifle = holder;
    const sling = mesh(new THREE.BoxGeometry(.03, .9, .045), belt, [.12, .17, 0], [0, 0, .0], spine); sling.rotation.x = -.62; sling.position.x = .19; }
  g.userData.rig = { legs, arms, spine, head, neck, pelvis };
  g.userData.pose = (t, p = {}) => {
    const sp = p.speed ?? 6.5, ph = t * sp + (o.seed || 0), w = p.walk ? Math.sin(ph) : 0, w2 = p.walk ? Math.sin(ph + Math.PI) : 0;
    legs[0].hip.rotation.z = w * .5; legs[1].hip.rotation.z = w2 * .5;
    legs[0].knee.rotation.z = p.walk ? -Math.max(0, -Math.cos(ph)) * .8 : 0; legs[1].knee.rotation.z = p.walk ? -Math.max(0, Math.cos(ph)) * .8 : 0;
    const swing = p.walk ? .38 : 0;
    arms[0].sh.rotation.z = (p.armL ?? 0) - w * swing; arms[1].sh.rotation.z = (p.armR ?? 0) + w * swing;
    arms[0].sh.rotation.x = p.armLx ?? .08; arms[1].sh.rotation.x = -(p.armRx ?? .08);
    arms[0].el.rotation.z = (p.elL ?? 0) + (p.walk ? .25 : .1); arms[1].el.rotation.z = (p.elR ?? 0) + (p.walk ? .25 : .1);
    const bob = p.walk ? Math.abs(Math.cos(ph)) * .035 : Math.sin(t * 1.7 + (o.seed || 0)) * .004;
    pelvis.position.y = .95 + bob; spine.position.y = .95 + bob; spine.rotation.z = (p.lean ?? 0) + (p.walk ? .04 : 0);
    head.rotation.y = (p.look ?? 0) + Math.sin(t * .45 + (o.seed || 0) * 3) * .07; head.rotation.z = p.nod ?? 0;
  };
  g.userData.pose(0);
  g.scale.setScalar(o.height || (1.0 + r() * .07));
  return shadowAll(g);
}
