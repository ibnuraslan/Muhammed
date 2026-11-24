// ===================== 3D engine: Legion style (three.js, deterministic) =====================
import * as THREE from './three.module.js';
import { GLTFLoader } from './jsm/GLTFLoader.js';
import { RGBELoader } from './jsm/RGBELoader.js';
export { THREE };

export const W = 1920, H = 1080;
export const R = new THREE.WebGLRenderer({ canvas: document.getElementById('c'), antialias: !/noaa/.test(location.search), preserveDrawingBuffer: true });
export const RS = +((location.search.match(/rs=([\d.]+)/) || [])[1] || 1); R.setSize(Math.round(W * RS), Math.round(H * RS), false); R.setPixelRatio(1);
R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.0; R.outputColorSpace = THREE.SRGBColorSpace;
R.shadowMap.enabled = true; R.shadowMap.type = /pcf/.test(location.search) ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap; if (/noshadow/.test(location.search)) R.shadowMap.enabled = false;

const TL = new THREE.TextureLoader(), GL = new GLTFLoader(), HL = new RGBELoader();
export function rng(seed) { let s = (seed * 2654435761) >>> 0 || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
export const lerp = (a, b, t) => a + (b - a) * t, clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

// ---------- materials ----------
const texCache = {}; export const TEXP = [];
export function tex(name, map = 'Diffuse', repeat = [1, 1]) {
  const k = name + map + repeat; if (texCache[k]) return texCache[k];
  let done; TEXP.push(new Promise(r => done = r)); const t = TL.load(`ph/tex/${name}/${map}.jpg`, () => done(), undefined, () => done()); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); t.anisotropy = 8;
  if (map === 'Diffuse') t.colorSpace = THREE.SRGBColorSpace; texCache[k] = t; return t;
}
export function pbr(name, repeat = [1, 1], o = {}) {
  return new THREE.MeshStandardMaterial({ map: tex(name, 'Diffuse', repeat), normalMap: tex(name, 'nor_gl', repeat), roughnessMap: tex(name, 'Rough', repeat), color: o.color || 0xffffff, roughness: o.roughness ?? 1, metalness: o.metalness ?? 0 });
}
export const mat = (color, roughness = .8, metalness = 0, o = {}) => new THREE.MeshStandardMaterial({ color, roughness, metalness, ...o });

// ---------- assets ----------
const modelCache = {};
export async function model(name) {
  if (!modelCache[name]) modelCache[name] = await GL.loadAsync(`ph/models/${name}/${name}.gltf`);
  const m = modelCache[name].scene.clone(true); m.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); return m;
}
export async function hdri(scene, name, bg = true, intensity = 1) {
  const t = await HL.loadAsync(`ph/hdri/${name}_2k.hdr`); t.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = t; if (bg) { scene.background = t; scene.backgroundIntensity = intensity; scene.backgroundBlurriness = 0; }
  scene.environmentIntensity = intensity; return t;
}
const shadow = o => { o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } }); return o; };
export function mesh(geo, m, pos = [0, 0, 0], rot = [0, 0, 0], parent) { const x = new THREE.Mesh(geo, m); x.position.set(...pos); x.rotation.set(...rot); x.castShadow = x.receiveShadow = true; if (parent) parent.add(x); return x; }

// ---------- steam locomotive (Russian-style, ~1900s) ----------
export function locomotive(o = {}) {
  const g = new THREE.Group(), body = mat(o.color || 0x1d2622, .45, .55), black = mat(0x111111, .5, .6), red = mat(0x7a1610, .55, .3), brass = mat(0xc9a24d, .3, .9), wood = pbr('brown_planks_05', [1, 1]);
  const boiler = mesh(new THREE.CylinderGeometry(.95, .95, 6.4, 40), body, [1.2, 2.55, 0], [0, 0, Math.PI / 2], g);
  for (let i = 0; i < 5; i++) mesh(new THREE.CylinderGeometry(.97, .97, .08, 40), brass, [-1.6 + i * 1.3, 2.55, 0], [0, 0, Math.PI / 2], g);
  mesh(new THREE.CylinderGeometry(1.02, 1.02, 1.1, 40), black, [4.75, 2.55, 0], [0, 0, Math.PI / 2], g);
  mesh(new THREE.CircleGeometry(.85, 40), mat(0x161616, .6, .5), [5.31, 2.55, 0], [0, Math.PI / 2, 0], g);
  mesh(new THREE.SphereGeometry(.12, 16, 12), brass, [5.36, 2.55, 0], [0, 0, 0], g);
  const chim = new THREE.LatheGeometry([[0, 0], [.32, 0], [.28, .4], [.3, 1.0], [.48, 1.35], [.5, 1.45], [0, 1.45]].map(p => new THREE.Vector2(...p)), 32);
  mesh(chim, black, [4.6, 3.4, 0], [0, 0, 0], g);
  mesh(new THREE.SphereGeometry(.45, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), brass, [1.6, 3.45, 0], [0, 0, 0], g);
  mesh(new THREE.CylinderGeometry(.42, .45, .35, 24), body, [1.6, 3.35, 0], [0, 0, 0], g);
  mesh(new THREE.SphereGeometry(.35, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), body, [3.2, 3.45, 0], [0, 0, 0], g);
  mesh(new THREE.CylinderGeometry(.25, .25, .5, 16), mat(0xe8e0c0, .4, .2, { emissive: o.lamp ? 0xffd890 : 0x000000, emissiveIntensity: 2 }), [5.2, 3.6, 0], [0, 0, Math.PI / 2], g);
  // cab
  const cab = new THREE.Group(); g.add(cab); cab.position.set(-2.6, 0, 0);
  mesh(new THREE.BoxGeometry(2.2, 2.6, 2.7), body, [0, 3.0, 0], [0, 0, 0], cab);
  for (const z of [-1.36, 1.36]) mesh(new THREE.BoxGeometry(.9, .8, .05), mat(o.lamp ? 0xffc870 : 0x223038, .2, .1, { emissive: o.lamp ? 0xffa040 : 0, emissiveIntensity: 1.5 }), [.2, 3.6, z], [0, 0, 0], cab);
  mesh(new THREE.CylinderGeometry(1.7, 1.7, 2.9, 24, 1, false, -Math.PI / 4, Math.PI / 2), mat(0x2a2a2a, .7, .3), [0, 3.15, 0], [Math.PI / 2, 0, -Math.PI / 2], cab);
  // tender
  const tender = new THREE.Group(); g.add(tender); tender.position.set(-6.0, 0, 0);
  mesh(new THREE.BoxGeometry(3.8, 1.8, 2.6), body, [0, 2.2, 0], [0, 0, 0], tender);
  const coal = new THREE.Mesh(new THREE.DodecahedronGeometry(1.2, 1), mat(0x0c0c0c, .95)); coal.scale.set(1.4, .35, .9); coal.position.set(0, 3.15, 0); tender.add(coal);
  // frame, running boards, buffers, cow catcher
  mesh(new THREE.BoxGeometry(12.4, .35, 2.4), red, [-.6, 1.25, 0], [0, 0, 0], g);
  for (const z of [-1.25, 1.25]) mesh(new THREE.BoxGeometry(8.2, .06, .5), black, [.8, 1.95, z], [0, 0, 0], g);
  for (const z of [-.8, .8]) { mesh(new THREE.CylinderGeometry(.18, .18, .5, 16), black, [5.7, 1.3, z], [0, 0, Math.PI / 2], g); mesh(new THREE.CylinderGeometry(.3, .3, .06, 20), black, [5.98, 1.3, z], [0, 0, Math.PI / 2], g); }
  const pilot = mesh(new THREE.ConeGeometry(1.3, 1.0, 4), red, [5.9, .65, 0], [0, Math.PI / 4, -Math.PI / 2], g); pilot.scale.set(1, .6, 1);
  // pipes
  for (const z of [-.9, .9]) mesh(new THREE.CylinderGeometry(.05, .05, 5.5, 8), brass, [1.0, 2.0, z], [0, 0, Math.PI / 2], g);
  // wheels
  const wheels = [];
  const wheelMesh = r => { const w = new THREE.Group(); mesh(new THREE.TorusGeometry(r * .92, r * .1, 10, 36), red, [0, 0, 0], [0, 0, 0], w); mesh(new THREE.CylinderGeometry(r * .97, r * .97, .1, 36), black, [0, 0, -.06], [Math.PI / 2, 0, 0], w); for (let k = 0; k < 12; k++) mesh(new THREE.BoxGeometry(.05, r * 1.8, .06), red, [0, 0, 0], [0, 0, k * Math.PI / 12], w); mesh(new THREE.CylinderGeometry(r * .18, r * .18, .14, 16), red, [0, 0, 0], [Math.PI / 2, 0, 0], w); return w; };
  [[-1.3, .78], [.5, .78], [2.3, .78], [4.2, .45]].forEach(([x, r]) => [-1.15, 1.15].forEach(z => { const w = wheelMesh(r); w.position.set(x, r, z); if (z < 0) w.rotation.y = Math.PI; g.add(w); wheels.push(w); }));
  [-6.9, -5.1].forEach(x => [-1.15, 1.15].forEach(z => { const w = wheelMesh(.45); w.position.set(x, .45, z); g.add(w); wheels.push(w); }));
  const rods = [-1.25, 1.25].map(z => mesh(new THREE.BoxGeometry(3.8, .1, .06), mat(0xb8b8b8, .3, .9), [.5, .78, z], [0, 0, 0], g));
  g.userData.update = t => { const a = t * (o.speed ?? 0); wheels.forEach(w => w.rotation.z = -a * (w.position.y < .6 ? 1.7 : 1)); rods.forEach((r, i) => { r.position.y = .78 + Math.sin(-a) * .35; r.position.x = .5 + Math.cos(-a) * .35; }); };
  g.userData.chimney = new THREE.Vector3(4.6, 4.95, 0);
  return shadow(g);
}
// ---------- teplushka boxcar ----------
export function boxcar(o = {}) {
  const g = new THREE.Group(), planks = pbr('brown_planks_05', [3, 1], { color: o.tint || 0xb86a48 }), black = mat(0x141414, .6, .6), dark = mat(0x0a0806, 1);
  mesh(new THREE.BoxGeometry(7.6, 2.7, 2.8), planks, [0, 2.65, 0], [0, 0, 0], g);
  const roof = mesh(new THREE.CylinderGeometry(4, 4, 7.8, 32, 1, false, -.36, .72), mat(0x3a3a3a, .85, .2), [0, -0.05, 0], [0, 0, Math.PI / 2], g); roof.rotation.set(Math.PI / 2, 0, Math.PI / 2); roof.position.set(0, 0.06, 0); roof.scale.set(1, 1, 1);
  const rf = mesh(new THREE.BoxGeometry(7.9, .15, 3.0), mat(0x3a3a3a, .85, .2), [0, 4.06, 0], [0, 0, 0], g);
  const door = o.open ?? 0; mesh(new THREE.BoxGeometry(1.8, 2.3, .06), dark, [0, 2.55, 1.41], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(1.9, 2.4, .1), planks, [door * 1.9, 2.55, 1.46], [0, 0, 0], g);
  for (const x of [-2.8, 2.8]) mesh(new THREE.BoxGeometry(.5, .35, .05), dark, [x, 3.4, 1.42], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(7.8, .3, 2.6), black, [0, 1.2, 0], [0, 0, 0], g);
  const wheels = []; [-2.6, 2.6].forEach(x => [-1.1, 1.1].forEach(z => { const w = mesh(new THREE.CylinderGeometry(.48, .48, .14, 28), black, [x, .48, z], [Math.PI / 2, 0, 0], g); wheels.push(w); }));
  if (o.stove !== false) mesh(new THREE.CylinderGeometry(.09, .09, .7, 12), black, [-2.2, 4.4, .5], [0, 0, 0], g);
  for (const x of [-3.9, 3.9]) for (const z of [-.8, .8]) mesh(new THREE.CylinderGeometry(.16, .16, .35, 12), black, [x, 1.3, z], [0, 0, Math.PI / 2], g);
  g.userData.update = t => wheels.forEach(w => w.rotation.y = t * (o.speed ?? 0) * 1.6);
  g.userData.stovepipe = new THREE.Vector3(-2.2, 4.8, .5);
  return shadow(g);
}
// ---------- station building ----------
export function station(sign = 'ЧЕЛЯБИНСК', o = {}) {
  const g = new THREE.Group(), wall = pbr('grey_plaster_02', [4, 2], { color: o.wallTint || 0xe8d8b8 }), roofM = pbr('clay_roof_tiles', [6, 2], { color: 0x8a4a3a }), trim = mat(0x6a2a20, .7), glass = mat(o.lit ? 0xffc870 : 0x1c2630, .2, .3, { emissive: o.lit ? 0xffa040 : 0, emissiveIntensity: 1.2 });
  mesh(new THREE.BoxGeometry(22, 6, 8), wall, [0, 3, 0], [0, 0, 0], g);
  const sh = new THREE.Shape(); sh.moveTo(-4.6, 0); sh.lineTo(0, 2.8); sh.lineTo(4.6, 0); sh.lineTo(-4.6, 0);
  const rg = new THREE.ExtrudeGeometry(sh, { depth: 23, bevelEnabled: false }); rg.translate(0, 0, -11.5); const roof = mesh(rg, roofM, [0, 6, 0], [0, Math.PI / 2, 0], g);
  for (let i = 0; i < 7; i++) { const x = -9 + i * 3; mesh(new THREE.BoxGeometry(1.4, 2.4, .1), glass, [x, 3.4, 4.02], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.7, .2, .2), trim, [x, 4.7, 4.05], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.7, .15, .25), trim, [x, 2.15, 4.05], [0, 0, 0], g); }
  mesh(new THREE.BoxGeometry(2, 3.2, .1), mat(0x2a1a12, .8), [0, 1.6, 4.03], [0, 0, 0], g);
  // canopy over platform
  mesh(new THREE.BoxGeometry(24, .25, 4), mat(0x4a3a2c, .8), [0, 4.6, 6], [-.08, 0, 0], g);
  for (let i = 0; i < 6; i++) mesh(new THREE.CylinderGeometry(.1, .1, 4.5, 10), mat(0x2a2a2a, .5, .5), [-10 + i * 4, 2.3, 7.6], [0, 0, 0], g);
  // sign
  const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 160; const x = cv.getContext('2d'); x.fillStyle = '#efe6d0'; x.fillRect(0, 0, 1024, 160); x.strokeStyle = '#3a2a1a'; x.lineWidth = 10; x.strokeRect(5, 5, 1014, 150); x.fillStyle = '#2a1a12'; x.font = 'bold 96px DejaVu Sans, sans-serif'; x.textAlign = 'center'; x.fillText(sign, 512, 115);
  const st = new THREE.CanvasTexture(cv); st.colorSpace = THREE.SRGBColorSpace; mesh(new THREE.PlaneGeometry(7, 1.1), new THREE.MeshStandardMaterial({ map: st, roughness: .8 }), [0, 5.4, 4.06], [0, 0, 0], g);
  return shadow(g);
}
// ---------- soldiers ----------
const UNI = {
  legion: { coat: 0x5c5a40, coatD: 0x4a4834, hat: 'papakha', hatC: 0x2e241c, ribbon: true },
  legionCap: { coat: 0x6a6646, coatD: 0x55523a, hat: 'peaked', hatC: 0x605c3e, ribbon: true },
  red: { coat: 0x1e1a18, coatD: 0x151210, hat: 'leather', hatC: 0x141210, band: true },
  pow: { coat: 0x6e6e68, coatD: 0x5a5a54, hat: 'kepi', hatC: 0x6a6a64 },
};
let RIFLE = null; export async function loadRifle() { RIFLE = await model('bolt_action_rifle_7_62'); const b = new THREE.Box3().setFromObject(RIFLE); const s = b.getSize(new THREE.Vector3()); RIFLE.userData.len = Math.max(s.x, s.y, s.z); }
export function soldier(o = {}) {
  const u = UNI[o.u || 'legion'], r = rng(o.seed || 1), g = new THREE.Group();
  const skin = mat([0xd8a27a, 0xc89070, 0xe0b090, 0xb8805a][Math.floor(r() * 4)], .7), coat = mat(u.coat, .95), coatD = mat(u.coatD, .95), boot = mat(0x18120e, .5, .1), leather = mat(0x4a3220, .7);
  const hips = new THREE.Group(); hips.position.y = 1.0; g.add(hips);
  const legs = [-1, 1].map(s => { const L = new THREE.Group(); L.position.set(0, 0, s * .12); hips.add(L); mesh(new THREE.CylinderGeometry(.09, .08, .55, 12), coatD, [0, -.3, 0], [0, 0, 0], L); mesh(new THREE.CylinderGeometry(.085, .09, .45, 12), boot, [0, -.75, 0], [0, 0, 0], L); mesh(new THREE.BoxGeometry(.28, .1, .13), boot, [.06, -.97, 0], [0, 0, 0], L); return L; });
  const torso = new THREE.Group(); torso.position.y = 1.0; g.add(torso);
  const skirt = new THREE.LatheGeometry([[.0, -.5], [.3, -.52], [.26, -.1], [.22, .25], [.2, .5], [.13, .62], [0, .64]].map(p => new THREE.Vector2(p[0], p[1] + .02)), 20); const coatM = mesh(skirt, coat, [0, .04, 0], [0, 0, 0], torso); coatM.scale.set(1, 1, .82);
  mesh(new THREE.TorusGeometry(.205, .03, 8, 24), leather, [0, .12, 0], [Math.PI / 2, 0, 0], torso);
  if (u.band) { const a = mesh(new THREE.CylinderGeometry(.075, .075, .1, 12), mat(0xb81a14, .7), [0, .38, .24], [Math.PI / 2, 0, 0], torso); }
  const arms = [-1, 1].map(s => { const A = new THREE.Group(); A.position.set(0, .52, s * .23); torso.add(A); mesh(new THREE.CapsuleGeometry(.065, .5, 4, 10), coat, [0, -.3, 0], [0, 0, 0], A); mesh(new THREE.SphereGeometry(.055, 10, 8), skin, [0, -.62, 0], [0, 0, 0], A); return A; });
  const head = new THREE.Group(); head.position.y = .72; torso.add(head);
  mesh(new THREE.CylinderGeometry(.06, .07, .12, 10), skin, [0, -.04, 0], [0, 0, 0], head);
  const hd = mesh(new THREE.SphereGeometry(.12, 20, 16), skin, [0, .1, 0], [0, 0, 0], head); hd.scale.set(1, 1.15, .95);
  mesh(new THREE.ConeGeometry(.025, .06, 8), skin, [.115, .09, 0], [0, 0, -Math.PI / 2], head);
  for (const z of [-.04, .04]) mesh(new THREE.SphereGeometry(.012, 8, 6), mat(0x140c08, .4), [.105, .13, z], [0, 0, 0], head);
  if (r() < .7) mesh(new THREE.BoxGeometry(.03, .025, .1), mat(0x3a2616, .9), [.115, .05, 0], [0, 0, 0], head);
  if (r() < .35) { const b = mesh(new THREE.SphereGeometry(.1, 12, 10), mat(0x3a2616, .95), [.04, 0, 0], [0, 0, 0], head); b.scale.set(.9, .8, 1.05); }
  const hc = mat(u.hatC, .95);
  if (u.hat === 'papakha') { mesh(new THREE.CylinderGeometry(.14, .135, .2, 18), hc, [0, .27, 0], [0, 0, 0], head); }
  else if (u.hat === 'peaked' || u.hat === 'kepi') { mesh(new THREE.CylinderGeometry(u.hat === 'kepi' ? .12 : .155, .125, u.hat === 'kepi' ? .14 : .1, 18), hc, [0, .26, 0], [0, 0, u.hat === 'kepi' ? -.1 : 0], head); const v = mesh(new THREE.CylinderGeometry(.13, .13, .015, 18, 1, false, -Math.PI / 2, Math.PI), mat(0x101010, .3), [.03, .2, 0], [0, 0, 0], head); }
  else if (u.hat === 'leather') { const c2 = mesh(new THREE.SphereGeometry(.135, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), mat(0x141210, .35, .2), [0, .2, 0], [0, 0, 0], head); mesh(new THREE.CylinderGeometry(.13, .13, .015, 18, 1, false, -Math.PI / 2, Math.PI), mat(0x080808, .3), [.04, .19, 0], [0, 0, 0], head); mesh(new THREE.SphereGeometry(.02, 8, 6), mat(0xc8241c, .5), [.13, .25, 0], [0, 0, 0], head); }
  if (u.ribbon) { mesh(new THREE.CylinderGeometry(u.hat === 'papakha' ? .142 : .128, .14, .025, 18), mat(0xf2f0ea, .7), [0, u.hat === 'papakha' ? .2 : .225, 0], [0, 0, 0], head); mesh(new THREE.CylinderGeometry(u.hat === 'papakha' ? .142 : .128, .14, .025, 18), mat(0xc8241c, .7), [0, u.hat === 'papakha' ? .178 : .205, 0], [0, 0, 0], head); }
  // rifle
  if (o.rifle !== false && RIFLE) { const rf = RIFLE.clone(true); const sc = 1.25 / RIFLE.userData.len; rf.scale.setScalar(sc); const holder = new THREE.Group(); holder.add(rf); holder.position.set(-.16, .45, .2); holder.rotation.set(0, Math.PI / 2, 1.35); torso.add(holder); g.userData.rifle = holder; }
  g.userData.parts = { legs, arms, torso, head, hips };
  g.userData.pose = (t, p = {}) => {
    const w = p.walk ? Math.sin(t * 6.5 + (o.seed || 0)) : 0;
    legs[0].rotation.z = w * .45; legs[1].rotation.z = -w * .45;
    arms[0].rotation.z = -w * .35 + (p.armL ?? 0); arms[1].rotation.z = w * .35 + (p.armR ?? 0);
    torso.position.y = 1.0 + (p.walk ? Math.abs(Math.cos(t * 6.5)) * .03 : Math.sin(t * 1.6 + (o.seed || 0)) * .006);
    head.rotation.y = (p.look ?? 0) + Math.sin(t * .5 + (o.seed || 0) * 3) * .08; head.rotation.z = p.nod ?? 0;
  };
  g.scale.setScalar(o.height || (1.0 + r() * .06));
  return shadow(g);
}
// ---------- environment ----------
export function snowGround(size = 600) { const g = new THREE.Mesh(new THREE.PlaneGeometry(size, size), pbr('snow_02', [size / 6, size / 6], { color: 0xf4f6fa })); g.rotation.x = -Math.PI / 2; g.receiveShadow = true; return g; }
export function track(len = 400, x0 = -200) {
  const g = new THREE.Group(), sleeper = pbr('old_wood_floor', [1, .2], { color: 0x7a6a5a }), steel = mat(0x6a6a70, .35, .85), ballast = pbr('gravel', [len / 4, 1], { color: 0x9a948a });
  const b = mesh(new THREE.BoxGeometry(len, .25, 3.6), ballast, [x0 + len / 2, .05, 0], [0, 0, 0], g);
  const sl = new THREE.InstancedMesh(new THREE.BoxGeometry(.26, .16, 2.6), sleeper, Math.floor(len / .7)); const m4 = new THREE.Matrix4(); for (let i = 0; i < sl.count; i++) { m4.makeTranslation(x0 + i * .7, .22, 0); sl.setMatrixAt(i, m4); } sl.receiveShadow = sl.castShadow = true; g.add(sl);
  for (const z of [-.72, .72]) mesh(new THREE.BoxGeometry(len, .14, .08), steel, [x0 + len / 2, .36, z], [0, 0, 0], g);
  return g;
}
export function forest(n, x0, x1, z0, z1, seed = 3, snowy = true) {
  const r = rng(seed), trunk = mat(0x3a2a1e, .9), dark = mat(0x1e3426, .9), snow = mat(0xf2f5f8, .9), g = new THREE.Group();
  const coneG = new THREE.ConeGeometry(1, 1, 9);
  const cones = new THREE.InstancedMesh(coneG, dark, n * 4), caps = new THREE.InstancedMesh(coneG, snow, n * 4), m = new THREE.Matrix4(), q = new THREE.Quaternion(), sv = new THREE.Vector3(), pv = new THREE.Vector3();
  let k = 0; for (let i = 0; i < n; i++) { const x = lerp(x0, x1, r()), z = lerp(z0, z1, r()), h = 8 + r() * 9; for (let j = 0; j < 4; j++) { const w = h * (.28 - j * .05), y = h * (.25 + j * .19); pv.set(x, y, z); sv.set(w, h * .32, w); m.compose(pv, q, sv); cones.setMatrixAt(k, m); pv.set(x - w * .08, y + h * .03, z); sv.set(w * .85, h * .22, w * .85); m.compose(pv, q, sv); caps.setMatrixAt(k, m); k++; } }
  cones.castShadow = true; g.add(cones); if (snowy) g.add(caps); return g;
}
// ---------- particles: smoke & snow (deterministic in t) ----------
function puffTexture() { const cv = document.createElement('canvas'); cv.width = cv.height = 128; const x = cv.getContext('2d'); const r = rng(7); for (let i = 0; i < 26; i++) { const px = 64 + (r() - .5) * 50, py = 64 + (r() - .5) * 50, rr = 18 + r() * 26; const gr = x.createRadialGradient(px, py, 0, px, py, rr); gr.addColorStop(0, 'rgba(255,255,255,.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = gr; x.beginPath(); x.arc(px, py, rr, 0, 7); x.fill(); } const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; return t; }
let PUFF; export function smoke(origin, o = {}) {
  PUFF = PUFF || puffTexture(); const n = o.n || 40, g = new THREE.Group(), sprites = [];
  for (let i = 0; i < n; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: PUFF, color: o.color || 0x9a9a9e, transparent: true, depthWrite: false, opacity: .8, fog: true })); g.add(s); sprites.push(s); }
  g.userData.update = (t, src = origin) => sprites.forEach((s, i) => { const life = o.life || 4, ph = ((t / life) + i / n) % 1, r = rng(i + 11), dx = (o.wind || [-3, 0])[0], dz = (o.wind || [-3, 0])[1];
    s.position.set(src.x + dx * ph * life + (r() - .5) * ph * 2, src.y + ph * (o.rise || 6) + (r() - .5) * .4, src.z + dz * ph * life + (r() - .5) * ph * 2);
    const sc = (o.size || .8) * (.6 + ph * (o.grow || 4)); s.scale.set(sc, sc, 1); s.material.opacity = (o.opacity ?? .85) * Math.min(1, ph * 6) * (1 - ph); s.material.rotation = r() * 6 + ph; });
  return g;
}
export function snowfall(n = 4000, box = [80, 30, 80], center = [0, 0, 0]) {
  const geo = new THREE.BufferGeometry(), pos = new Float32Array(n * 3), base = new Float32Array(n * 3), r = rng(21);
  for (let i = 0; i < n; i++) { base[i * 3] = (r() - .5) * box[0]; base[i * 3 + 1] = r() * box[1]; base[i * 3 + 2] = (r() - .5) * box[2]; }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ color: 0xffffff, size: .08, transparent: true, opacity: .9, depthWrite: false }));
  pts.userData.update = t => { for (let i = 0; i < n; i++) { const sp = .8 + (i % 7) * .12; pos[i * 3] = center[0] + base[i * 3] + Math.sin(t * .7 + i) * .4 + t * .6; pos[i * 3 + 1] = center[1] + ((base[i * 3 + 1] - t * sp) % box[1] + box[1]) % box[1]; pos[i * 3 + 2] = center[2] + base[i * 3 + 2] + Math.cos(t * .5 + i) * .4; } geo.attributes.position.needsUpdate = true; };
  return pts;
}
// ---------- camera path helper ----------
export function camShot(cam, t, a, b, d, fov = [35, 35]) { const p = ease(clamp(t / d)); cam.position.set(lerp(a[0], b[0], p), lerp(a[1], b[1], p), lerp(a[2], b[2], p)); cam.lookAt(lerp(a[3], b[3], p), lerp(a[4], b[4], p), lerp(a[5], b[5], p)); cam.fov = lerp(fov[0], fov[1], p); cam.updateProjectionMatrix(); }
