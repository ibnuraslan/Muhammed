// ===================== laosets.js: shared sets for the Laos film =====================
import * as L from './lib3.js';
import * as P from './props.js';
import * as X from './lao.js';
import * as LM from './laomaps.js';
const { THREE, S, cam, U, SKY, V3, at, mesh, mat, rng, lerp, clamp, ease, pose, facing, SETS, fx, camTo, GRAD } = L;
const toon = (c, o = {}) => new THREE.MeshToonMaterial({ color: c, gradientMap: GRAD, ...o });
export const POS = { school: [0, 0], village: [3000, 0], cliff: [6000, 0], cave: [0, 3000], trail: [9000, 0], sky: [12000, 0], jars: [6000, 6000], hall: [0, 6000], ops: [3000, 6000], ridge: [9000, 6000], garden: [12000, 6000] };
// camera relative to a set
export const ct = (set, lt, d, a, b, fov = [35, 35], shake = 0) => { const o = SETS[set].position; camTo(lt, d, [a[0] + o.x, a[1] + o.y, a[2] + o.z, a[3] + o.x, a[4] + o.y, a[5] + o.z], [b[0] + o.x, b[1] + o.y, b[2] + o.z, b[3] + o.x, b[4] + o.y, b[5] + o.z], fov, shake); };
export const wp = (set, x, y, z) => { const o = SETS[set].position; return V3(x + o.x, y + o.y, z + o.z); };
export const light = (k, set, x, y, z, i, col = 0xffb060, dist = 18) => { const l = [L.pl1, L.pl2, L.pl3][k]; const p = wp(set, x, y, z); l.position.copy(p); l.intensity = i; l.color.set(col); l.distance = dist; l.decay = 1.5; };
export const hide = (...objs) => objs.flat().forEach(o => o && (o.position.y = -60));
export function skies() {
  SKY.day = L.paintSky('#4a7ec0', '#d8e8f0', '#fff8e8', '#c8d8e8', '#8a9ab8', 3);
  SKY.morning = L.paintSky('#6a96c8', '#f0e0c8', '#fff4e0', '#d8d0c8', '#9aa0b0', 5, { sun: [1400, 760] });
  SKY.dusk = L.paintSky('#3e4474', '#f2a868', '#ffd8a0', '#d89a8a', '#7a6a8a', 9, { sun: [700, 820] });
  SKY.night = L.paintSky('#0a1228', '#28344e', '#4a5a7e', '#323e5c', '#1e263c', 11, { stars: true });
  SKY.dawn = L.paintSky('#4a5a8a', '#f0b890', '#ffe0c0', '#d0a8a0', '#8a7a90', 13, { sun: [1500, 860] });
  SKY.grey = L.paintSky('#8a9098', '#c8c8c4', '#e0e0da', '#b0b0ac', '#8a8a88', 17);
  SKY.smoke = L.paintSky('#5a4a44', '#b08a6a', '#d8b890', '#9a7a68', '#5a4a48', 19);
}
// ---------------- SCHOOL (present day) ----------------
export function schoolSet() { const g = L.addSet('school', ...POS.school); L.ground(g, 'dirt');
  U.sch = X.school(); at(U.sch, 0, 0, -14); g.add(U.sch);
  const pole = new THREE.Group(); mesh(new THREE.CylinderGeometry(.06, .07, 9, 8), mat(0xd8d8d0, .4, .5), [0, 4.5, 0], [0, 0, 0], pole); const fl = L.flag(1.8, 1.2, ['#c8241c'], { draw: X.laoFlagDraw }); fl.position.set(.06, 8.9, 0); pole.add(fl); U.schFlag = fl; at(pole, 10, 0, -2); g.add(pole);
  g.add(X.jungle(420, -140, 140, -120, 120, 31, { avoid: (x, z) => Math.abs(x) < 40 && z > -30 && z < 70 }));
  for (let i = 0; i < 9; i++) { const p = X.palm(8 + (i % 3) * 2, i + 3); at(p, -34 + i * 8.5, 0, -26 - (i % 2) * 5); g.add(p); }
  for (let i = 0; i < 5; i++) { const b = X.banana(i + 1); at(b, 22 + (i % 2) * 3, 0, -6 + i * 4); g.add(b); }
  g.add(X.karstRange(18, -900, 900, -1200, -350, 41, [120, 300])); g.add(X.karstRange(6, -1400, -500, -300, 800, 42, [120, 260])); g.add(X.karstRange(6, 500, 1400, -300, 800, 43, [120, 260]));
  // fence and gate
  for (let x = -36; x <= 36; x += 3) if (Math.abs(x) > 2.5) mesh(new THREE.BoxGeometry(.12, 1.2, .12), mat(0x6a5a44, .9), [x, .6, 34], [0, 0, 0], g);
  for (const y of [.5, 1.0]) for (const s of [-1, 1]) mesh(new THREE.BoxGeometry(34, .03, .03), mat(0x5a5a58, .5, .5), [s * 19.5, y, 34], [0, 0, 0], g);
  for (const s of [-1, 1]) mesh(new THREE.BoxGeometry(.3, 2.4, .3), mat(0xe8dcc0, .8), [s * 2.6, 1.2, 34], [0, 0, 0], g);
  const arch = X.TT(['NACHAT PRIMARY SCHOOL'], { w: 1024, h: 128, bg: '#2a5a8a', fg: '#f2ead8', size: 60 }); L.plate(5, .6, arch, g, [0, 2.6, 34]); mesh(new THREE.BoxGeometry(5.1, .7, .04), mat(0x1e3a5a, .8), [0, 2.6, 33.96], [0, 0, 0], g);
  // kids
  U.kids = [...Array(16)].map((_, i) => { const girl = i % 2 === 1; const k = X.villager({ seed: 300 + i, child: true, shirt: 0xf4f2ec, lower: 0x1e2a5a, skirt: girl, shorts: !girl && i % 4 === 0, bandC: 0x1e2a5a, longSleeve: false, barefoot: i % 5 === 0 }); g.add(k); return k; });
  U.teacher = X.villager({ seed: 77, skirt: true, bun: true, shirt: 0xa8c8e0, lower: 0x5a2a3a, bandC: 0xc8a040, longSleeve: false }); g.add(U.teacher);
  U.ball = mesh(new THREE.SphereGeometry(.11, 14, 10), mat(0xd83a2a, .6), [0, .11, 0], [0, 0, 0], g);
  U.schBombie = new THREE.Group(); const bb = X.bombie(0x6a5a3a); bb.scale.setScalar(1); bb.position.y = .015; U.schBombie.add(bb); const mound = mesh(new THREE.SphereGeometry(.12, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), mat(0x6a5a44, 1), [0, 0, 0], [0, 0, 0], U.schBombie); mound.scale.set(1.1, .16, 1.1); at(U.schBombie, 6, 0, 10); g.add(U.schBombie);
  U.stick = mesh(new THREE.CylinderGeometry(.008, .01, .7, 5), mat(0x5a4028, .9), [0, 0, 0], [0, 0, 0]);
  U.schStakes = []; const r = rng(5); for (let i = 0; i < 30; i++) { const s = X.stake(); s.scale.setScalar(2.2); at(s, (r() - .5) * 40, 0, -2 + r() * 30); s.userData.home = s.position.clone(); g.add(s); U.schStakes.push(s); }
  U.team = [...Array(4)].map((_, i) => { const m = X.villager({ seed: 600 + i, hat: 'helmet', vest: 0x2a4a8a, shirt: 0x7a7258, lower: 0x4a4a3a, boots: true, detector: i < 3, longSleeve: true }); g.add(m); return m; });
  U.parents = [...Array(5)].map((_, i) => { const m = X.villager({ seed: 700 + i, skirt: i % 2 === 0, bun: i % 2 === 0, longSleeve: i % 3 === 0 }); g.add(m); return m; });
  U.moto = motorbike(); g.add(U.moto);
  return g; }
export function motorbike() { const g = new THREE.Group(), m = mat(0x8a1e1e, .5, .3), dk = mat(0x1a1a1a, .6); for (const x of [-.65, .65]) mesh(new THREE.TorusGeometry(.3, .07, 8, 18), dk, [x, .32, 0], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(1.0, .3, .3), m, [0, .62, 0], [0, 0, .1], g); mesh(new THREE.BoxGeometry(.5, .12, .3), dk, [-.2, .82, 0], [0, 0, 0], g); mesh(new THREE.CylinderGeometry(.02, .02, .6, 6), dk, [.6, .8, 0], [0, 0, -.3], g); mesh(new THREE.CylinderGeometry(.015, .015, .6, 6), dk, [.68, 1.08, 0], [Math.PI / 2, 0, 0], g); return g; }
// ---------------- VILLAGE ----------------
export function villageSet() { const g = L.addSet('village', ...POS.village); L.ground(g, 'grass');
  U.houses = [[-12, -8, 1], [2, -14, 2], [16, -9, 3], [-24, 4, 4], [24, 6, 5]].map(([x, z, s]) => { const h = X.stiltHouse({ seed: s, wood: [0x9a7a54, 0x8a6a48, 0xa8845a][s % 3] }); at(h, x, 0, z, (s % 2 ? .2 : -.15)); g.add(h); return h; });
  U.ruin = X.stiltHouse({ seed: 9, ruined: true }); at(U.ruin, 2, -60, -14, -.15); g.add(U.ruin);
  U.newPosts = new THREE.Group(); for (const x of [-3.3, 0, 3.3]) for (const z of [-2.3, 2.3]) mesh(new THREE.CylinderGeometry(.11, .13, 2.2, 6), mat(0xa8865a, .9), [x, 1.1, z], [0, 0, 0], U.newPosts); at(U.newPosts, 2, -60, -14, -.15); g.add(U.newPosts);
  U.pad = X.paddies(6, 3, 14, 10, { seed: 4 }); at(U.pad, 0, 0, 30); g.add(U.pad);
  U.bunk = X.bunker(); at(U.bunk, -14, 0, 10, .3); g.add(U.bunk);
  g.add(X.jungle(500, -220, 220, -160, -26, 51)); g.add(X.jungle(200, -220, -55, -26, 120, 52)); g.add(X.jungle(200, 55, 220, -26, 120, 53));
  for (let i = 0; i < 10; i++) { const p = X.palm(7 + (i % 4) * 2, i + 20); at(p, -40 + i * 9, 0, -24 - (i % 3) * 4); g.add(p); }
  for (let i = 0; i < 8; i++) { const b = X.banana(i + 30); at(b, -30 + i * 8 + (i % 2) * 3, 0, -2 + (i % 3) * 3); g.add(b); }
  g.add(X.karstRange(16, -900, 900, -1100, -300, 61, [100, 260])); g.add(X.karstRange(8, -900, 900, 400, 1100, 62, [100, 240]));
  U.craters = []; for (const [x, z, r] of [[-20, 32, 3.5], [12, 26, 3], [30, 40, 4], [-6, 44, 2.5]]) { const c = P.crater(r); at(c, x, -60, z); c.userData.home = V3(x, .1, z); g.add(c); U.craters.push(c); }
  U.fam = { dad: X.villager({ seed: 11, shirt: 0x3a4a5a, lower: 0x2a2a28, longSleeve: true }), mum: X.villager({ seed: 12, skirt: true, bun: true, shirt: 0xd8c8b0, lower: 0x5a2a4a }), gran: X.villager({ seed: 13, skirt: true, bun: true, shirt: 0x2a2a30, lower: 0x3a2a3a, longSleeve: true, height: .9 }),
    boy: X.villager({ seed: 14, child: true, shirt: 0xb89a6a, lower: 0x2a2a28, shorts: true, barefoot: true }), girl: X.villager({ seed: 15, child: true, shirt: 0xc87a5a, skirt: true, lower: 0x3a2a5a, barefoot: true, longSleeve: false }) };
  Object.values(U.fam).forEach(m => g.add(m));
  U.farmers = [...Array(6)].map((_, i) => { const m = X.villager({ seed: 40 + i, hat: 'conical', longSleeve: true, shirt: [0x2a2a30, 0x3a4a5a, 0x4a3a2a][i % 3], lower: 0x2a2a28, hoe: i % 2 === 0, skirt: i % 3 === 2, bun: i % 3 === 2 }); g.add(m); return m; });
  U.vsmoke = [0, 1, 2].map(i => fx(L.smoke(V3(), { n: 40, color: 0x3a3430, wind: [1.5, .4], rise: 22, size: 3, grow: 4, life: 7, opacity: .8 })));
  U.vfire = L.fire(12, 2.6); g.add(U.vfire); U.vfire.position.y = -60;
  U.warn = X.sign(['DANGER', 'UXO'], { size: 90 }); at(U.warn, -40, -60, 22); g.add(U.warn);
  U.vStakes = []; for (let i = 0; i < 14; i++) { const s = X.stake(); at(s, -60, -60, 0); g.add(s); U.vStakes.push(s); }
  U.vBombies = []; for (let i = 0; i < 6; i++) { const b = X.bombie(0x6a5a3a); at(b, 0, -60, 0); g.add(b); U.vBombies.push(b); }
  U.plot = new THREE.Group(); for (const [x, z] of [[-3, -2], [3, -2], [3, 2], [-3, 2]]) mesh(new THREE.BoxGeometry(.05, .5, .05), mat(0xd8c8a0, .8), [x, .25, z], [0, 0, 0], U.plot); [[[-3, -2], [3, -2]], [[3, -2], [3, 2]], [[3, 2], [-3, 2]], [[-3, 2], [-3, -2]]].forEach(([a, b]) => U.plot.add(X.tapeLine(a, b, 0xf2f0e0))); at(U.plot, 30, -60, 18); g.add(U.plot);
  U.buckets = new THREE.Group(); mesh(new THREE.CylinderGeometry(.02, .02, 1.6, 6), mat(0x8a6a3a, .9), [0, 0, 0], [Math.PI / 2, 0, 0], U.buckets); for (const s of [-1, 1]) mesh(new THREE.CylinderGeometry(.16, .13, .3, 12), mat(0x7a7a7a, .4, .6), [0, -.35, s * .75], [0, 0, 0], U.buckets);
  U.scale = new THREE.Group(); mesh(new THREE.BoxGeometry(.5, .8, .5), mat(0x3a5a7a, .6), [0, .4, 0], [0, 0, 0], U.scale); mesh(new THREE.BoxGeometry(.7, .05, .7), mat(0x8a8a86, .4, .6), [0, .82, 0], [0, 0, 0], U.scale); at(U.scale, -60, -60, 0); g.add(U.scale);
  U.scrap = X.scrapPile(3); at(U.scrap, -60, -60, 0); g.add(U.scrap);
  return g; }
// ---------------- VIENGXAY CLIFFS ----------------
export function cliffSet() { const g = L.addSet('cliff', ...POS.cliff); L.ground(g, 'grass');
  const big = [[-60, -150, 160, 70, 1], [40, -175, 200, 80, 2], [170, -120, 170, 60, 3], [-180, -120, 190, 70, 4], [-60, 190, 150, 60, 5], [140, 210, 180, 70, 6]];
  big.forEach(([x, z, h, r, s]) => { const k = X.karst(h, r, 700 + s); at(k, x, -3, z, s); g.add(k); });
  U.caveMouths = [[-30, 1.8, -24.6], [8, 1.6, -24.6], [55, 2.2, -24.6]].map(([x, s, z]) => { const m = new THREE.Group(); const hole = mesh(new THREE.CircleGeometry(2.4 * s, 24, 0, Math.PI), new THREE.MeshBasicMaterial({ color: 0x050403 }), [0, 0, 0], [0, 0, 0], m); hole.userData.noToon = true;
    const rim = mesh(new THREE.TorusGeometry(2.45 * s, .35 * s, 8, 20, Math.PI), toon(0x7a746a), [0, 0, .05], [0, 0, 0], m); rim.userData.noToon = true; const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: L.FIRE_T, blending: THREE.AdditiveBlending, transparent: true, opacity: .25, depthWrite: false })); glow.scale.set(3 * s, 2 * s, 1); glow.position.set(0, 1 * s, -.4); m.add(glow);
    at(m, x, 0, z); g.add(m); return m; });
  // cliff wall behind mouths
  { const geo = new THREE.PlaneGeometry(260, 90, 130, 45); const p = geo.attributes.position, col = [], rr = rng(77);
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i) + 45; let z = Math.sin(x * .13) * 2.4 + Math.sin(x * .41 + y * .2) * 1.2 + Math.sin(y * .31) * 1.6 + Math.sin(x * 1.3 + y * .9) * .3;
      for (const [mx, mr] of [[-30, 4.3], [8, 3.8], [55, 5.3]]) { const dx = Math.abs(x - mx) - (mr + 1.5), dy = y - (mr + 2.5); const dd = Math.max(dx, dy, 0); const k = Math.min(1, dd / 5); z = 5.75 * (1 - k * k * (3 - 2 * k)) + z * (k * k * (3 - 2 * k)); }
      const top = 62 + Math.sin(x * .05) * 14 + Math.sin(x * .17) * 6; let yy = Math.min(y, top + (y - top) * .1); if (y > top) z -= (y - top) * 1.2; p.setXYZ(i, x, yy, z); }
    geo.computeVertexNormals(); const n = geo.attributes.normal;
    for (let i = 0; i < p.count; i++) { const y = p.getY(i), up = n.getY(i); const c = new THREE.Color(y > 58 ? 0x4e6a34 : up > .5 ? 0xa29c90 : (Math.sin(i * 7.1) > .3 ? 0x8a847a : 0x9a948a)); if (y < 3 && up > .3) c.set(0x5a6a3a); const streak = Math.sin(p.getX(i) * 2.1) > .85 ? .8 : 1; c.multiplyScalar(streak); col.push(c.r, c.g, c.b); }
    geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); const wall = mesh(geo, toon(0xffffff, { vertexColors: true, side: THREE.DoubleSide }), [0, -1, -30.5], [0, 0, 0], g); wall.userData.noToon = true; }
  // carve: paint dark arches on the wall at mouth positions (the mouths sit in front)
  U.cpad = X.paddies(6, 4, 16, 12, { seed: 8 }); at(U.cpad, 0, 0, 54); g.add(U.cpad);
  g.add(X.jungle(240, -200, 200, -20, 10, 71, { hmin: 4, hmax: 9, avoid: (x, z) => Math.abs(x) < 70 })); g.add(X.jungle(200, -260, 260, 90, 200, 72));
  g.add(X.karstRange(10, -1000, 1000, -1200, -500, 73, [200, 380]));
  U.cPeople = [...Array(10)].map((_, i) => { const k = i % 4; const m = k === 0 ? X.villager({ seed: 900 + i, hat: 'pith', shirt: 0x4a5a34, lower: 0x4a5a34, longSleeve: true }) : k === 1 ? X.villager({ seed: 900 + i, hat: 'bush', shirt: 0x3a4a2a, lower: 0x3a3a2a, gun: true }) : k === 2 ? X.villager({ seed: 900 + i, skirt: true, bun: true, basket: true }) : X.villager({ seed: 900 + i, hat: 'conical', basket: true, longSleeve: true }); g.add(m); return m; });
  U.stretcher = stretcher(); g.add(U.stretcher); U.bearers = [0, 1, 2].map(i => { const m = X.villager({ seed: 950 + i, longSleeve: true, shirt: 0x2a2a30 }); g.add(m); return m; });
  U.plFlag = L.flag(1.6, 1.05, ['#c8241c'], { draw: X.plDraw }); const fp = new THREE.Group(); mesh(new THREE.CylinderGeometry(.04, .05, 5, 6), mat(0x6a5a44, .9), [0, 2.5, 0], [0, 0, 0], fp); U.plFlag.position.set(.05, 4.9, 0); fp.add(U.plFlag); at(fp, 13, 0, -22); g.add(fp);
  U.lamp = X.lantern(); g.add(U.lamp);
  return g; }
export function stretcher() { const g = new THREE.Group(); for (const s of [-.3, .3]) mesh(new THREE.CylinderGeometry(.025, .025, 2.6, 6), mat(0x8a6a3a, .9), [0, 0, s], [0, 0, Math.PI / 2], g); mesh(new THREE.BoxGeometry(1.9, .04, .58), mat(0xb8a888, 1), [0, 0, 0], [0, 0, 0], g);
  const pat = X.villager({ seed: 960, longSleeve: true, shirt: 0x8a7a6a }); pat.rotation.z = Math.PI / 2; pat.position.set(.95, .2, 0); g.add(pat); mesh(new THREE.BoxGeometry(1.0, .12, .52), mat(0x6a5a4a, 1), [.45, .27, 0], [0, 0, 0], g); g.userData.patient = pat; return g; }
// ---------------- CAVE INTERIOR (several chambers, 40 m apart in z) ----------------
export function caveSet() { const g = L.addSet('cave', ...POS.cave); U.cRooms = {};
  const room = (name, z, len, rad, o = {}) => { const r = new THREE.Group(); r.add(X.caveTunnel(len, rad, z + 3, o)); at(r, 0, 0, z); g.add(r); U.cRooms[name] = r; return r; };
  // long street with stalls (dolly shot)
  const st = room('street', 0, 70, 4.2, { wide: 1.5 });
  const desk = P.desk(1.6, .8); at(desk, -24, 0, -3.2); st.add(desk); const tw = mesh(new THREE.BoxGeometry(.4, .14, .3), mat(0x2a2a2a, .5), [-24, .85, -3.2], [0, 0, 0], st);
  for (let i = 0; i < 3; i++) { const sh = new THREE.Group(); mesh(new THREE.BoxGeometry(2, .05, .5), mat(0x6a4a2a, .9), [0, .6 + i * .5, 0], [0, 0, 0], sh); st.add(sh); at(sh, -12, 0, -3.6); for (let k = 0; k < 6; k++) mesh(new THREE.CylinderGeometry(.06, .06, .2, 8), mat([0xc8a050, 0x8a3a2a, 0x4a6a8a][k % 3], .6), [-.8 + k * .32, .72 + i * .5, 0], [0, 0, 0], sh); }
  const oven = mesh(new THREE.SphereGeometry(1.1, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), mat(0x9a5a3a, .9), [0, 0, -3.4], [0, 0, 0], st); oven.position.x = 0; const ovG = mesh(new THREE.CircleGeometry(.35, 16), new THREE.MeshBasicMaterial({ color: 0xffa040 }), [0, .35, -2.3], [0, 0, 0], st); ovG.userData.noToon = true;
  const bb = X.blackboard(['ສະບາຍດີ', '1 + 2 = 3'], { size: 80 }); at(bb, 12, 0, -4.4, .1); st.add(bb); for (let i = 0; i < 3; i++) { const b = X.bench(2); at(b, 12 + (i - 1) * .2, 0, -2.8 + i * .9); st.add(b); }
  for (let i = 0; i < 3; i++) { const b = X.bed(); at(b, 24 + i * 2.6, 0, -3.4, Math.PI / 2); st.add(b); }
  U.stLamps = [-24, -12, 0, 12, 24].map(x => { const l = X.lantern(); at(l, x, 2.9, -1.5); st.add(l); return l; });
  U.stPeople = [...Array(12)].map((_, i) => { const m = X.villager({ seed: 1000 + i, child: i >= 8, skirt: i % 3 === 1, bun: i % 3 === 1, hat: i % 5 === 0 ? 'pith' : 'none', shirt: i >= 8 ? 0xe8e2d4 : undefined, longSleeve: i % 2 === 0 }); st.add(m); return m; });
  // classroom
  const cl = room('class', 40, 20, 4, { wide: 1.4 }); const cb = X.blackboard(['ສະບາຍດີ', 'ກ  ຂ  ຄ  ງ'], { size: 90 }); at(cb, 7.4, 0, 0, -Math.PI / 2); cl.add(cb);
  for (let i = 0; i < 4; i++) for (const z of [-1.4, 1.4]) { const b = X.bench(2.2); b.scale.y = .72; at(b, 2 - i * 1.6, 0, z, Math.PI / 2 * 0); b.rotation.y = Math.PI / 2; cl.add(b); }
  U.clKids = [...Array(8)].map((_, i) => { const k = X.villager({ seed: 1100 + i, child: true, shirt: 0xe0d8c8, lower: 0x2a2a3a, skirt: i % 2 === 1, shorts: i % 2 === 0, barefoot: true }); at(k, 2 - Math.floor(i / 2) * 1.6, 0, (i % 2 ? 1 : -1) * 1.4, facing([1, 0])); cl.add(k); return k; });
  U.clTeacher = X.villager({ seed: 1120, longSleeve: true, shirt: 0xd8d0c0, lower: 0x2a2a30 }); at(U.clTeacher, 6, 0, -1.6, facing([-1, .3])); cl.add(U.clTeacher);
  U.clLamps = [[4, 2.8, 0], [-2, 2.8, 0]].map(p => { const l = X.lantern(); at(l, ...p); cl.add(l); return l; });
  // ward + tarp roof
  const wd = room('ward', 80, 24, 4.4, { wide: 1.6 }); U.wdBeds = []; for (let i = 0; i < 5; i++) for (const z of [-2.6, 2.6]) { const b = X.bed(); at(b, -8 + i * 3.6, 0, z, Math.PI / 2); wd.add(b); U.wdBeds.push(b); }
  U.tarp = new THREE.Group(); const tg = new THREE.PlaneGeometry(20, 7, 20, 6); const tp = tg.attributes.position; for (let i = 0; i < tp.count; i++) tp.setZ(i, Math.sin(tp.getX(i) * .8) * .12 - Math.abs(tp.getY(i)) * .12); tg.computeVertexNormals();
  const tm = mesh(tg, toon(0x6a7a5a, { side: THREE.DoubleSide }), [0, 3.2, 0], [-Math.PI / 2, 0, 0], U.tarp); tm.userData.noToon = true; wd.add(U.tarp);
  U.wdPoles = []; for (let i = 0; i < 6; i++) for (const z of [3.3, -3.3]) U.wdPoles.push(mesh(new THREE.CylinderGeometry(.04, .04, 3.2, 6), mat(0x8a7a50, .9), [-9 + i * 3.6, 1.6, z], [0, 0, 0], wd));
  U.patients = [...Array(5)].map((_, i) => { const m = X.villager({ seed: 1200 + i, longSleeve: true, shirt: 0x8a7a6a }); m.rotation.z = -Math.PI / 2; m.position.set(-8.9 + i * 3.6 * 0 + (i * 3.6), .75, -2.6); m.rotation.set(0, Math.PI / 2, -Math.PI / 2); wd.add(m); return m; });
  U.nurse = X.villager({ seed: 1220, skirt: true, bun: true, shirt: 0xf2f0ea, lower: 0xe8e4dc, longSleeve: false }); at(U.nurse, -2, 0, 0, facing([0, -1])); wd.add(U.nurse);
  U.surgeon = X.villager({ seed: 1221, shirt: 0xe8eee8, lower: 0xe0e6e0, longSleeve: true, hat: 'cap', hatC: 0xe8eee8 }); at(U.surgeon, 8.6, 0, 1.2, facing([0, -1])); wd.add(U.surgeon);
  U.opT = new THREE.Group(); mesh(new THREE.BoxGeometry(2, .1, .8), mat(0xe8e8e0, .6), [0, .9, 0], [0, 0, 0], U.opT); mesh(new THREE.BoxGeometry(.2, .9, .2), mat(0x8a9a9a, .4, .5), [0, .45, 0], [0, 0, 0], U.opT); const opL = X.lantern(); at(opL, 0, 2.4, 0); U.opT.add(opL); at(U.opT, 8.6, 0, 0); wd.add(U.opT);
  U.wdLamps = [-6, 0, 6].map(x => { const l = X.lantern(); at(l, x, 2.7, 0); wd.add(l); return l; });
  U.drips = [...Array(6)].map(() => { const d = mesh(new THREE.SphereGeometry(.03, 6, 5), new THREE.MeshBasicMaterial({ color: 0xb8d8e8, transparent: true, opacity: .8 }), [0, 0, 0], [0, 0, 0], wd); d.userData.noToon = true; return d; });
  // office + theatre + family chamber
  const of = room('office', 120, 16, 3.6, { wide: 1.5 }); const od = P.desk(2, .9); at(od, 0, 0, 0); of.add(od); const rad = mesh(new THREE.BoxGeometry(.5, .3, .3), mat(0x3a4a3a, .5), [.5, .91, -.1], [0, 0, 0], of);
  const mp = L.textTex([['', 10, 10]], { w: 512, h: 360, bg: '#d8c8a0', draw: (x) => { x.strokeStyle = '#6a4a2a'; x.lineWidth = 4; x.beginPath(); x.moveTo(120, 40); x.bezierCurveTo(200, 90, 180, 200, 300, 260); x.lineTo(380, 330); x.stroke(); x.fillStyle = '#c8241c'; for (let i = 0; i < 6; i++) { x.beginPath(); x.arc(150 + i * 40, 100 + i * 35, 8, 0, 7); x.fill(); } } });
  L.plate(2.2, 1.5, mp, of, [0, 1.9, -4.6]); const of2 = L.flag(1.4, .9, ['#c8241c'], { draw: X.plDraw }); of2.position.set(-3.2, 2.6, -4.5); of.add(of2);
  U.officials = [0, 1, 2].map(i => { const m = X.villager({ seed: 1300 + i, hat: i === 2 ? 'pith' : 'none', shirt: i === 0 ? 0x4a5a3a : 0x5a5a48, lower: 0x3a3a2e, longSleeve: true }); of.add(m); return m; });
  const th = room('theatre', 160, 26, 4.8, { wide: 1.6 }); const stage = mesh(new THREE.BoxGeometry(5, .6, 7), mat(0x6a4a2a, .9), [9, .3, 0], [0, 0, 0], th); const cur = mesh(new THREE.PlaneGeometry(.1, 3.6), mat(0xa81e1e, .9), [11.4, 2.3, 0], [0, 0, 0], th);
  for (const s of [-1, 1]) { const c = mesh(new THREE.BoxGeometry(.2, 3.6, 2), mat(0xa81e1e, .9), [11.3, 2.4, s * 3], [0, 0, 0], th); }
  U.actors = [0, 1].map(i => { const m = X.villager({ seed: 1400 + i, skirt: i === 1, bun: i === 1, shirt: i ? 0xe8b8a0 : 0x2a4a6a, lower: i ? 0xa8241c : 0x2a2a30 }); at(m, 9 + i * .2, .6, -1 + i * 2, facing([-1, 0])); th.add(m); return m; });
  U.audience = [...Array(14)].map((_, i) => { const m = X.villager({ seed: 1420 + i, child: i % 5 === 0, skirt: i % 3 === 0, bun: i % 3 === 0 }); at(m, 2 - Math.floor(i / 5) * 1.6, 0, ((i % 5) - 2) * 1.1, facing([1, 0])); th.add(m); return m; });
  const fm = room('family', 200, 14, 3.2, { wide: 1.4 }); const mat2 = mesh(new THREE.BoxGeometry(3, .05, 2), mat(0xb89a6a, 1), [0, .03, 0], [0, 0, 0], fm);
  U.cFam = [0, 1, 2, 3].map(i => { const m = X.villager({ seed: 1500 + i, child: i > 1, skirt: i % 2 === 1, bun: i === 1, longSleeve: true, shirt: [0x3a4a5a, 0xd8c8b0, 0xb89a6a, 0xc87a5a][i] }); fm.add(m); return m; });
  U.bowl = mesh(new THREE.SphereGeometry(.12, 12, 8, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), mat(0x8a5a3a, .7), [0, .12, .3], [0, 0, 0], fm); const rice = mesh(new THREE.SphereGeometry(.07, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), mat(0xf2f0ea, .9), [0, .1, .3], [0, 0, 0], fm); rice.scale.y = .4;
  U.fmLamp = X.lantern(); at(U.fmLamp, .5, .1, -.6); fm.add(U.fmLamp);
  return g; }
// ---------------- TRAIL ----------------
export function trailSet() { const g = L.addSet('trail', ...POS.trail); L.ground(g, 'mud');
  const pts = []; for (let i = 0; i <= 60; i++) { const x = -300 + i * 10; pts.push(V3(x, .05, Math.sin(x * .012) * 14 + Math.sin(x * .031) * 5)); } U.road = new THREE.CatmullRomCurve3(pts);
  const rg = new THREE.PlaneGeometry(600, 6, 300, 1); const rp = rg.attributes.position; for (let i = 0; i < rp.count; i++) { const x = rp.getX(i), y = rp.getY(i); const p = U.road.getPointAt(clamp((x + 300) / 600)); rp.setXYZ(i, p.x, -y + p.z, .06); } rg.computeVertexNormals();
  const rd = mesh(rg, toon(0xa0623a), [0, 0, 0], [-Math.PI / 2, 0, 0], g); rd.userData.noToon = true; rd.receiveShadow = true; rd.castShadow = false; rd.material.polygonOffset = true; rd.material.polygonOffsetFactor = -2;
  const near = (x, z) => { const p = U.road.getPointAt(clamp((x + 300) / 600)); return Math.abs(z - p.z) < 6; };
  g.add(X.jungle(1400, -300, 300, -70, 70, 81, { avoid: near, hmin: 7, hmax: 18 }));
  U.trucks = [0, 1, 2].map(i => { const t = X.truck(); g.add(t); return t; });
  U.bikes = [0, 1, 2, 3].map(i => { const b = X.bicycle(); g.add(b); return b; });
  U.porters = [0, 1, 2, 3].map(i => { const m = X.villager({ seed: 1600 + i, hat: 'pith', shirt: 0x4a5a34, lower: 0x4a5a34, longSleeve: true }); g.add(m); return m; });
  U.nva = [...Array(12)].map((_, i) => { const m = i % 4 === 3 ? X.villager({ seed: 1700 + i, hat: 'bush', shirt: 0x3a4a2a, lower: 0x3a3a2a, gun: true, longSleeve: true }) : X.villager({ seed: 1700 + i, hat: 'pith', shirt: 0x5a6a3a, lower: 0x5a6a3a, gun: true, longSleeve: true, basket: i % 3 === 0 }); g.add(m); return m; });
  U.tBlasts = [0, 1, 2].map(() => { const b = L.blast({ size: 9 }); g.add(b); return b; });
  U.tJets = [0, 1].map(() => { const j = X.jet(); g.add(j); return j; });
  U.treaty = L.plate(.6, .8, X.TT(['DECLARATION', 'ON THE NEUTRALITY', 'OF LAOS', '', 'GENEVA · 1962'], { w: 512, h: 680, size: 44, bg: '#ece2c8', fg: '#2a1a10' }), g, [0, .07, 0], [-Math.PI / 2, 0, .4]);
  return g; }
export const roadAt = x => U.road.getPointAt(clamp((x + 300) / 600));
// ---------------- AERIAL ----------------
function landTex(seed = 3) { const cv = document.createElement('canvas'); cv.width = 2048; cv.height = 2048; const x = cv.getContext('2d'), r = rng(seed); x.fillStyle = '#4a6a34'; x.fillRect(0, 0, 2048, 2048);
  for (let i = 0; i < 2600; i++) { x.fillStyle = ['#3e5e2c', '#567a3c', '#456a30', '#5e8240'][i % 4]; x.beginPath(); x.arc(r() * 2048, r() * 2048, 8 + r() * 40, 0, 7); x.fill(); }
  for (let i = 0; i < 40; i++) { const cx = r() * 2048, cy = r() * 2048; for (let k = 0; k < 8; k++) { x.fillStyle = ['#a8b870', '#9ab060', '#c0c080'][k % 3]; x.fillRect(cx + (k % 4) * 22, cy + Math.floor(k / 4) * 18, 20, 16); } }
  x.strokeStyle = '#4a7a8a'; x.lineWidth = 14; x.beginPath(); x.moveTo(0, 900); for (let i = 0; i <= 20; i++) x.lineTo(i * 110, 900 + Math.sin(i * .7) * 160 + Math.sin(i * 1.9) * 40); x.stroke();
  x.strokeStyle = '#9a6a42'; x.lineWidth = 5; x.beginPath(); x.moveTo(300, 0); for (let i = 0; i <= 20; i++) x.lineTo(300 + Math.sin(i * .5) * 120 + i * 40, i * 110); x.stroke();
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; }
export function skySet() { const g = L.addSet('sky', ...POS.sky); const gm = mesh(new THREE.PlaneGeometry(6000, 6000), toon(0xffffff, { map: landTex(5) }), [0, 0, 0], [-Math.PI / 2, 0, 0], g); gm.userData.noToon = true; gm.material.map.repeat.set(3, 3); gm.material.map.wrapS = gm.material.map.wrapT = THREE.RepeatWrapping;
  g.add(X.karstRange(40, -1800, 1800, -1800, 1800, 91, [120, 320]));
  g.add(X.jungle(900, -600, 600, -600, 600, 92, { hmin: 10, hmax: 22 }));
  U.sJets = [...Array(4)].map(() => { const j = X.jet(); g.add(j); return j; });
  U.b52s = [0, 1, 2].map(() => { const b = X.bomber(); g.add(b); return b; });
  U.fall = [...Array(40)].map(() => { const b = X.bombBody(2.2); g.add(b); b.position.y = -60; return b; });
  U.cans = [0, 1].map(() => { const c = X.canister(); g.add(c); c.position.y = -60; return c; });
  U.bomblets = new THREE.InstancedMesh(new THREE.SphereGeometry(.16, 8, 6), toon(0x7a7a4a), 400); U.bomblets.userData.noToon = true; g.add(U.bomblets);
  U.sBlasts = [...Array(8)].map(() => { const b = L.blast({ size: 14 }); g.add(b); return b; });
  U.contrails = [...Array(6)].map(() => { const c = mesh(new THREE.CylinderGeometry(.8, .8, 1, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: .55, depthWrite: false }), [0, -60, 0], [0, 0, Math.PI / 2], g); c.userData.noToon = true; return c; });
  return g; }
// ---------------- PLAIN OF JARS ----------------
export function jarsSet() { const g = L.addSet('jars', ...POS.jars); L.ground(g, 'grass'); const r = rng(3);
  U.jars = []; for (let i = 0; i < 26; i++) { const h = 1.2 + r() * 1.3, rr = h * .38; const prof = [[0, 0], [rr, 0], [rr * 1.05, h * .5], [rr * .95, h], [rr * .7, h], [rr * .72, h * .15], [0, h * .15]]; const j = mesh(new THREE.LatheGeometry(prof.map(p => new THREE.Vector2(p[0], p[1])), 16), mat(0x9a9488, .95), [(r() - .5) * 40, 0, (r() - .5) * 30], [r() * .2, r() * 6, (r() - .5) * .25], g); U.jars.push(j); }
  g.add(X.karstRange(14, -900, 900, -1100, -300, 101, [80, 180]));
  for (let i = 0; i < 30; i++) { const hl = mesh(new THREE.SphereGeometry(30 + r() * 40, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), toon(0x7a8a4a), [(r() - .5) * 900, -10, -200 - r() * 400], [0, 0, 0], g); hl.scale.y = .25; hl.userData.noToon = true; }
  U.jJets = [0, 1].map(() => { const j = X.jet(); g.add(j); return j; }); U.jBlasts = [...Array(4)].map(() => { const b = L.blast({ size: 10 }); g.add(b); return b; });
  return g; }
// ---------------- GENEVA HALL ----------------
const FLAGS = [['UK', d => { d.fillStyle = '#1e2c6a'; d.fillRect(0, 0, 128, 80); d.strokeStyle = '#f2f0ea'; d.lineWidth = 14; d.beginPath(); d.moveTo(0, 0); d.lineTo(128, 80); d.moveTo(128, 0); d.lineTo(0, 80); d.stroke(); d.strokeStyle = '#c8241c'; d.lineWidth = 5; d.stroke(); d.fillStyle = '#f2f0ea'; d.fillRect(52, 0, 24, 80); d.fillRect(0, 28, 128, 24); d.fillStyle = '#c8241c'; d.fillRect(57, 0, 14, 80); d.fillRect(0, 33, 128, 14); }],
  ['USA', d => { for (let i = 0; i < 13; i++) { d.fillStyle = i % 2 ? '#f2f0ea' : '#b8241c'; d.fillRect(0, i * 80 / 13, 128, 80 / 13 + .5); } d.fillStyle = '#2a3a78'; d.fillRect(0, 0, 54, 43); }],
  ['France', d => { ['#2a4ea0', '#f2f0ea', '#c8241c'].forEach((c, i) => { d.fillStyle = c; d.fillRect(i * 43, 0, 43, 80); }); }],
  ['USSR', d => { d.fillStyle = '#c8241c'; d.fillRect(0, 0, 128, 80); d.fillStyle = '#f2c020'; d.fillRect(14, 10, 12, 4); d.beginPath(); d.arc(20, 22, 6, 0, 7); d.fill(); }],
  ['China', d => { d.fillStyle = '#d82a1c'; d.fillRect(0, 0, 128, 80); d.fillStyle = '#f2d020'; d.beginPath(); d.arc(22, 20, 9, 0, 7); d.fill(); for (let i = 0; i < 4; i++) { d.beginPath(); d.arc(38 + (i % 2) * 6, 8 + i * 7, 3, 0, 7); d.fill(); } }],
  ['India', d => { ['#f29a30', '#f2f0ea', '#2a8a3a'].forEach((c, i) => { d.fillStyle = c; d.fillRect(0, i * 27, 128, 27); }); d.strokeStyle = '#1e2c8a'; d.lineWidth = 2; d.beginPath(); d.arc(64, 40, 9, 0, 7); d.stroke(); }],
  ['Canada', d => { d.fillStyle = '#c8241c'; d.fillRect(0, 0, 128, 80); d.fillStyle = '#f2f0ea'; d.fillRect(32, 0, 64, 80); d.fillStyle = '#c8241c'; d.beginPath(); d.moveTo(64, 20); d.lineTo(76, 46); d.lineTo(52, 46); d.fill(); d.fillRect(62, 46, 4, 12); }],
  ['Poland', d => { d.fillStyle = '#f2f0ea'; d.fillRect(0, 0, 128, 40); d.fillStyle = '#d82a3c'; d.fillRect(0, 40, 128, 40); }],
  ['Burma', d => { d.fillStyle = '#c8241c'; d.fillRect(0, 0, 128, 80); d.fillStyle = '#1e3a8a'; d.fillRect(0, 0, 56, 40); d.fillStyle = '#f2f0ea'; d.beginPath(); d.arc(28, 20, 9, 0, 7); d.fill(); }],
  ['Cambodia', d => { d.fillStyle = '#1e3a8a'; d.fillRect(0, 0, 128, 80); d.fillStyle = '#c8241c'; d.fillRect(0, 20, 128, 40); d.fillStyle = '#f2f0ea'; d.fillRect(44, 32, 40, 18); d.fillRect(58, 24, 12, 8); }],
  ['Thailand', d => { ['#c8241c', '#f2f0ea', '#2a3a78', '#2a3a78', '#f2f0ea', '#c8241c'].forEach((c, i) => { d.fillStyle = c; d.fillRect(0, i * 80 / 6, 128, 80 / 6 + .5); }); }],
  ['N. Vietnam', d => { d.fillStyle = '#d82a1c'; d.fillRect(0, 0, 128, 80); d.fillStyle = '#f2d020'; d.beginPath(); for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2 - Math.PI / 2, rr = i % 2 ? 9 : 22; d.lineTo(64 + Math.cos(a) * rr, 40 + Math.sin(a) * rr); } d.fill(); }],
  ['S. Vietnam', d => { d.fillStyle = '#f2d020'; d.fillRect(0, 0, 128, 80); d.fillStyle = '#d82a1c'; for (const y of [30, 38, 46]) d.fillRect(0, y, 128, 4); }],
  ['Laos', X.royalLaoDraw]];
export function hallSet() { const g = L.addSet('hall', ...POS.hall); const rm = P.room(26, 18, 7, { wall: 0xd8ccb0, floor: 0x6a4a30, panel: 0x5a3a22 }); g.add(rm);
  const tb = P.longTable(16, 2.2); at(tb, 0, 0, -1); g.add(tb); for (const z of [-2.6, .6]) for (let i = 0; i < 7; i++) { const c = P.chair(); at(c, -6.6 + i * 2.2, 0, z, z < 0 ? 0 : Math.PI); g.add(c); }
  U.gFlags = FLAGS.map(([n, d], i) => { const f = P.flagStand(['#ffffff'], { w: .45, h: .3, draw: d }); f.scale.setScalar(.6); at(f, -7.1 + i * 1.1, .84, -1, 0); g.add(f); return f; });
  for (const x of [-6, 0, 6]) { const ch = P.chandelier(); at(ch, x, 6.9, -1); g.add(ch); }
  for (const x of [-10, 10]) { const w = P.windowPane(2.2, 4, L.textTex([['', 10, 10]], { w: 64, h: 128, bg: '#dfe8f0' }), true); at(w, x, 3.4, -8.9); g.add(w); }
  U.dels = [...Array(14)].map((_, i) => { const m = L.man({ u: 'suit', seed: 2000 + i, noMustache: i % 3 !== 0, beard: 0, rifle: false }); const z = i < 7 ? -2.75 : .75; at(m, -6.6 + (i % 7) * 2.2, 0, z, facing([0, z < 0 ? 1 : -1])); g.add(m); return m; });
  U.doc = L.plate(.42, .58, X.TT(['DECLARATION', 'ON THE', 'NEUTRALITY', 'OF LAOS', '', '23 JULY 1962'], { w: 512, h: 700, size: 52, bg: '#efe6d0', fg: '#2a1a10' }), g, [0, .86, -1.2], [-Math.PI / 2, 0, 0]);
  U.pen = mesh(new THREE.CylinderGeometry(.006, .008, .15, 8), mat(0x1a1a1a, .3, .5), [0, .9, -1.1], [0, 0, 1.2], g);
  U.gHand = L.hand(.9); U.gHand.children.forEach(c => c.material && c.material.color && c.material.color.set && 0); g.add(U.gHand);
  return g; }
// ---------------- OPS ROOM ----------------
export function opsSet() { const g = L.addSet('ops', ...POS.ops); const rm = P.room(14, 12, 3.4, { wall: 0x6a6e68, floor: 0x3a3a38, panel: 0x2a2e2a }); g.add(rm);
  const cv = document.createElement('canvas'); cv.width = L.W; cv.height = L.H; const c = cv.getContext('2d'); const pr = LM.view(104.5, 17.5, 11); LM.base(c, pr, { hl: [['Laos', '#c8b890']] }); LM.trail(c, pr, 1, { col: '#8a3a1a', w: 4 });
  c.strokeStyle = 'rgba(40,40,60,.35)'; c.lineWidth = 2; for (let x = 0; x < L.W; x += 80) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, L.H); c.stroke(); } for (let y = 0; y < L.H; y += 80) { c.beginPath(); c.moveTo(0, y); c.lineTo(L.W, y); c.stroke(); }
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; U.opsMapPr = pr;
  const tb = mesh(new THREE.BoxGeometry(4.2, .8, 2.5), mat(0x3a2e24, .8), [0, .4, 0], [0, 0, 0], g); L.plate(4, 2.25, tex, g, [0, .81, 0], [-Math.PI / 2, 0, 0]);
  U.pins = [...Array(10)].map((_, i) => { const p = mesh(new THREE.ConeGeometry(.04, .14, 8), mat([0xc8241c, 0x2a4a8a, 0xd8a020][i % 3], .5), [0, -60, 0], [Math.PI, 0, 0], g); return p; });
  U.officers = [...Array(4)].map((_, i) => { const m = X.villager({ seed: 2100 + i, skin: [0xe8c0a0, 0xd8b090, 0xf0c8a8, 0xc8a080][i], hairC: [0x6a4a2a, 0x2a1a12, 0x8a6a3a, 0x3a2a20][i], shirt: 0xc8b890, lower: 0x5a5a48, longSleeve: false, mustache: i === 2 }); g.add(m); return m; });
  const lamp = mesh(new THREE.ConeGeometry(.5, .4, 16, 1, true), mat(0x2a2a2a, .5), [0, 2.6, 0], [0, 0, 0], g); lamp.material.side = THREE.DoubleSide;
  return g; }
// ---------------- HMONG RIDGE ----------------
export function ridgeSet() { const g = L.addSet('ridge', ...POS.ridge); L.ground(g, 'grass');
  const strip = mesh(new THREE.PlaneGeometry(220, 16), toon(0xa08060), [0, .06, 0], [-Math.PI / 2, 0, 0], g); strip.userData.noToon = true; strip.material.polygonOffset = true; strip.material.polygonOffsetFactor = -2;
  g.add(X.karstRange(22, -1400, 1400, -1400, -200, 111, [150, 400])); g.add(X.karstRange(12, -1400, 1400, 250, 1400, 112, [150, 400]));
  g.add(X.jungle(300, -200, 200, -80, -14, 113)); g.add(X.jungle(200, -200, 200, 14, 80, 114));
  U.plane = transport(); g.add(U.plane);
  U.hmong = [...Array(9)].map((_, i) => { const m = X.villager({ seed: 2200 + i, shirt: 0x1e1e22, lower: 0x1e1e22, longSleeve: true, gun: true, hat: i % 3 === 0 ? 'bush' : 'none', hatC: 0x3a4a2a }); g.add(m); return m; });
  return g; }
export function transport() { const g = new THREE.Group(), m = mat(0xb8b8b0, .5, .3), bl = mat(0x2a3a6a, .5); mesh(new THREE.CylinderGeometry(.8, .6, 10, 12), m, [0, 1.6, 0], [0, 0, Math.PI / 2], g); mesh(new THREE.ConeGeometry(.8, 1.6, 12), m, [5.8, 1.6, 0], [0, 0, -Math.PI / 2], g);
  mesh(new THREE.BoxGeometry(2, .15, 16), m, [1, 2.5, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.6, 2, .12), m, [-4.6, 2.6, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.4, .1, 4), m, [-4.6, 1.8, 0], [0, 0, 0], g);
  mesh(new THREE.BoxGeometry(10.2, .2, 1.7), bl, [0, 1.6, 0], [0, 0, 0], g); for (const s of [-1, 1]) { mesh(new THREE.CylinderGeometry(.35, .35, 1.2, 10), m, [2.2, 2.2, s * 3], [0, 0, Math.PI / 2], g); const pr = mesh(new THREE.BoxGeometry(.06, 2, .12), mat(0x1a1a1a, .5), [2.9, 2.2, s * 3], [0, 0, 0], g); (g.userData.props = g.userData.props || []).push(pr); mesh(new THREE.CylinderGeometry(.3, .3, .2, 10), mat(0x1a1a1a, .6), [1.6, .3, s * 1.2], [Math.PI / 2, 0, 0], g); }
  return g; }
// ---------------- GARDEN (Phon Village, present) ----------------
export function gardenSet() { const g = L.addSet('garden', ...POS.garden); L.ground(g, 'dirt');
  U.gHouse = X.stiltHouse({ seed: 21, wood: 0x9a7a54, roofC: 0x8a8a86 }); at(U.gHouse, -10, 0, -12, .1); g.add(U.gHouse);
  g.add(X.jungle(300, -160, 160, -120, -30, 121)); g.add(X.jungle(200, -160, -40, -30, 120, 122)); g.add(X.jungle(200, 40, 160, -30, 120, 123));
  g.add(X.karstRange(14, -1000, 1000, -1200, -350, 124, [100, 260]));
  for (let i = 0; i < 6; i++) { const p = X.palm(7 + i % 3, 140 + i); at(p, -30 + i * 11, 0, -24); g.add(p); }
  // garden beds (hidden until 'after')
  U.beds = new THREE.Group(); for (let i = 0; i < 6; i++) { mesh(new THREE.BoxGeometry(8, .2, 1), toon(0x6a4a30), [6, .1, -2 + i * 1.8], [0, 0, 0], U.beds); for (let k = 0; k < 10; k++) mesh(new THREE.SphereGeometry(.18, 8, 6), toon(0x5a9a3a), [2.4 + k * .8, .3, -2 + i * 1.8], [0, 0, 0], U.beds); } U.beds.children.forEach(c => c.userData.noToon = true); g.add(U.beds);
  U.saplings = new THREE.Group(); for (let i = 0; i < 6; i++) { const t = new THREE.Group(); mesh(new THREE.CylinderGeometry(.04, .06, 1.2, 6), toon(0x6a4a2a), [0, .6, 0], [0, 0, 0], t); mesh(new THREE.IcosahedronGeometry(.6, 1), toon(0x5a8a34), [0, 1.4, 0], [0, 0, 0], t); at(t, -2 + (i % 3) * 3, 0, 8 + Math.floor(i / 3) * 3); U.saplings.add(t); } U.saplings.traverse(c => c.isMesh && (c.userData.noToon = true)); g.add(U.saplings);
  U.store = new THREE.Group(); mesh(new THREE.BoxGeometry(3, 2.2, 2.4), L.pbr('brown_planks_05', [1, 1], { color: 0xa8865a }), [0, 1.1, 0], [0, 0, 0], U.store); const rf = X.roofPrism(3.6, 3, 1, mat(0x9a9a96, .5, .4)); rf.position.y = 2.2; U.store.add(rf); at(U.store, 14, 0, -10); g.add(U.store);
  U.pegs = new THREE.Group(); for (const [x, z] of [[-4, -3], [4, -3], [4, 3], [-4, 3]]) mesh(new THREE.BoxGeometry(.05, .5, .05), mat(0xd8c8a0, .8), [x, .25, z], [0, 0, 0], U.pegs); [[[-4, -3], [4, -3]], [[4, -3], [4, 3]], [[4, 3], [-4, 3]], [[-4, 3], [-4, -3]]].forEach(([a, b]) => U.pegs.add(X.tapeLine(a, b, 0xf2f0e0))); at(U.pegs, -14, 0, 10); g.add(U.pegs);
  U.atta = X.villager({ seed: 2301, shirt: 0x3a5a7a, lower: 0x2a2a28, longSleeve: false, hoe: false }); g.add(U.atta);
  U.attaKids = [0, 1].map(i => { const k = X.villager({ seed: 2310 + i, child: true, shirt: [0xd8a040, 0x8ab0d0][i], lower: 0x2a2a3a, shorts: i === 0, skirt: i === 1, barefoot: true }); g.add(k); return k; });
  U.attaWife = X.villager({ seed: 2320, skirt: true, bun: true, shirt: 0xe0c8b8, lower: 0x5a2a3a }); g.add(U.attaWife);
  U.gb = X.bombie(0x6a5a3a); g.add(U.gb); U.gMound = mesh(new THREE.SphereGeometry(.3, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), mat(0x7a6448, 1), [0, -60, 0], [0, 0, 0], g); U.gMound.scale.y = .35;
  U.gHoe = X.hoe(); g.add(U.gHoe);
  U.gTeam = [...Array(4)].map((_, i) => { const m = X.villager({ seed: 2400 + i, hat: 'helmet', vest: 0x2a4a8a, shirt: 0x7a7258, lower: 0x4a4a3a, boots: true, detector: i < 2, longSleeve: true }); g.add(m); return m; });
  U.pickup = pickup(); g.add(U.pickup);
  U.gStakes = [...Array(8)].map(() => { const s = X.stake(); g.add(s); s.position.y = -60; return s; });
  U.demo = new THREE.Group(); for (let i = 0; i < 6; i++) { const b = i < 2 ? X.bombBody(1.2) : X.bombie(0x6a5a3a); b.position.set((i % 3) * .3, .1, Math.floor(i / 3) * .3); U.demo.add(b); } for (let i = 0; i < 8; i++) mesh(new THREE.BoxGeometry(.5, .25, .3), mat(0xb8a878, 1), [Math.cos(i * .8) * .9, .12, Math.sin(i * .8) * .9], [0, i * .8, 0], U.demo); at(U.demo, 30, 0, 30); g.add(U.demo);
  U.gBlast = L.blast({ size: 7 }); g.add(U.gBlast);
  return g; }
export function pickup() { const g = new THREE.Group(), w = mat(0xe8e8e4, .5, .3), dk = mat(0x1a1a1a, .6); mesh(new THREE.BoxGeometry(5, .9, 2), w, [0, .9, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(2.2, .9, 1.9), w, [.6, 1.75, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(1.9, .6, 1.92), mat(0x2a3a4a, .2, .4), [.7, 1.8, 0], [0, 0, 0], g);
  for (const x of [1.6, -1.6]) for (const s of [-1, 1]) mesh(new THREE.CylinderGeometry(.42, .42, .3, 14), dk, [x, .42, s * 1], [Math.PI / 2, 0, 0], g);
  const lg = X.TT(['UXO CLEARANCE'], { w: 512, h: 96, bg: '#e8e8e4', fg: '#1e3a8a', size: 54, border: false }); L.plate(2.2, .4, lg, g, [-1.2, 1.1, 1.01]); return g; }
