// ===================== SECTION 3: 1917 - early 1918, cues 32-51 =====================
import * as L from './lib3.js';
import * as M from './maps.js';
import * as P from './props.js';
const { THREE, S, cam, U, SKY, V3, at, mesh, mat, pbr, model, clamp, lerp, ease, rng, pl1, pl2, pl3, look, camTo, show, fx, overlay, OV, pose, facing, man, SETS } = L;
export const RANGE = { from: 32, to: 51 };
let C; const ST = i => C[i].start;
const ct = (set, lt, d, a, b, fov = [35, 35], shake = 0) => { const o = SETS[set].position; camTo(lt, d, [a[0] + o.x, a[1] + o.y, a[2] + o.z, a[3] + o.x, a[4] + o.y, a[5] + o.z], [b[0] + o.x, b[1] + o.y, b[2] + o.z, b[3] + o.x, b[4] + o.y, b[5] + o.z], fov, shake); };
const CZ = ['#f2f0ea', '#c8241c'], FR = ['#2a4ea0', '#f2f0ea', '#c8241c'];
function fieldGun() { const g = new THREE.Group(), m = mat(0x4a4e44, .6, .4), w = mat(0x3a2a1a, .8); mesh(new THREE.CylinderGeometry(.07, .1, 2.4, 10), m, [.9, 1.0, 0], [0, 0, Math.PI / 2 - .15], g); mesh(new THREE.BoxGeometry(.9, .5, .8), m, [0, .9, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.1, 1.2, .9), m, [-.1, 1.2, 0], [0, 0, 0], g);
  for (const z of [-.6, .6]) { const wh = mesh(new THREE.TorusGeometry(.55, .06, 6, 18), w, [0, .6, z], [0, 0, 0], g); for (let k = 0; k < 6; k++) mesh(new THREE.BoxGeometry(.04, 1.05, .04), w, [0, .6, z], [0, 0, k * Math.PI / 6], g); } mesh(new THREE.BoxGeometry(2.4, .12, .12), m, [-1.4, .35, 0], [0, 0, .15], g); return g; }
function crown() { const g = new THREE.Group(), gold = mat(0xd8a830, .25, .95), red = mat(0x9a1010, .3, .2), j = mat(0x2a5aa0, .2, .3);
  mesh(new THREE.CylinderGeometry(.2, .19, .12, 24, 1, true), gold, [0, 0, 0], [0, 0, 0], g).material.side = THREE.DoubleSide; mesh(new THREE.SphereGeometry(.19, 20, 12, 0, Math.PI * 2, 0, Math.PI / 2), red, [0, .06, 0], [0, 0, 0], g);
  for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; mesh(new THREE.SphereGeometry(.025, 8, 6), i % 2 ? j : red, [Math.cos(a) * .2, 0, Math.sin(a) * .2], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.02, .18, .04), gold, [Math.cos(a) * .12, .14, Math.sin(a) * .12], [Math.sin(a) * .9, 0, -Math.cos(a) * .9], g); }
  mesh(new THREE.TorusGeometry(.2, .018, 6, 28), gold, [0, -.06, 0], [Math.PI / 2, 0, 0], g); mesh(new THREE.SphereGeometry(.035, 10, 8), gold, [0, .28, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.02, .09, .02), gold, [0, .34, 0], [0, 0, 0], g); mesh(new THREE.BoxGeometry(.06, .02, .02), gold, [0, .35, 0], [0, 0, 0], g); return g; }
function pocketWatch() { const g = new THREE.Group(); mesh(new THREE.CylinderGeometry(.05, .05, .015, 24), mat(0xc9a24d, .25, .95), [0, 0, 0], [Math.PI / 2, 0, 0], g); const face = mesh(new THREE.CircleGeometry(.044, 24), new THREE.MeshBasicMaterial({ map: L.textTex([], { w: 128, h: 128, bg: '#f2ead8', border: false, draw: x => { x.fillStyle = '#1a1410'; for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; x.fillRect(64 + Math.cos(a) * 52 - 2, 64 + Math.sin(a) * 52 - 2, 4, 4); } } }) }), [0, 0, .008], [0, 0, 0], g); face.userData.noToon = true;
  const hm = mesh(new THREE.BoxGeometry(.004, .03, .002), mat(0x1a1410, .4), [0, .012, .01], [0, 0, 0], g), mm = mesh(new THREE.BoxGeometry(.003, .04, .002), mat(0x1a1410, .4), [0, .018, .011], [0, 0, 0], g); g.userData.hands = [hm, mm]; return g; }
export async function build(cues) {
  C = cues;
  SKY.grey = L.paintSky('#8e98a6', '#cfcec6', '#e8e6e0', '#bdbdc2', '#8d929e', 7);
  SKY.snow = L.paintSky('#9aa4b4', '#e4e4e6', '#f4f4f6', '#d4d6dc', '#a4aab8', 19);
  SKY.dawn = L.paintSky('#6c8ac0', '#f2cfa0', '#fff2d8', '#f0c8b4', '#a898b4', 3, { sun: [1250, 760] });
  SKY.summer = L.paintSky('#5a8ad0', '#e8e0c8', '#fffaf0', '#e8e0d8', '#a8b0c4', 23, { sun: [1500, 300] });
  SKY.night = L.paintSky('#0a1228', '#28344e', '#4a5a7e', '#323e5c', '#1e263c', 11, { stars: true });
  SKY.dusk = L.paintSky('#3e4474', '#f2a868', '#ffd8a0', '#d89a8a', '#7a6a8a', 9, { sun: [700, 820] });
  // ---------- RUSSIAN FRONT (winter road + trench) ----------
  const rf = L.addSet('rfront', 0, 0); L.ground(rf, 'snow'); rf.add(L.forest(200, -300, 300, -250, -50, 31, true)); rf.add(L.forest(150, -300, 300, 50, 250, 32, true));
  for (const z of [-8]) { const sb = L.sandbags(60, 4); sb.position.set(0, 0, z); rf.add(sb); }
  const road = mesh(new THREE.PlaneGeometry(500, 6), L.groundMat('mud'), [0, .02, 4], [-Math.PI / 2, 0, 0], rf); road.userData.noToon = true;
  U.gun = fieldGun(); at(U.gun, 8, 0, 9, .5); rf.add(U.gun); const gun2 = fieldGun(); at(gun2, -14, 0, 10, 2.6); gun2.rotation.z = .2; rf.add(gun2);
  U.deserters = [...Array(12)].map((_, i) => { const m = man({ u: 'russian', seed: 1000 + i, flip: i % 2 }); rf.add(m); return m; });
  U.sitters = [...Array(4)].map((_, i) => { const m = man({ u: 'russian', seed: 1020 + i, rifle: false }); at(m, -6 + i * 3, 0, -6.6, facing([0, 1]) + (i - 1.5) * .3); rf.add(m); return m; });
  U.dropped = [...Array(8)].map((_, i) => { const r = L.lowRifle(); at(r, -10 + i * 2.6, .05, -5.5 + (i % 3) * .6, i * .8); r.rotation.x = Math.PI / 2; rf.add(r); return r; });
  U.helmet = new THREE.Group(); mesh(new THREE.SphereGeometry(.17, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), mat(0x5a6048, .6, .3), [0, 0, 0], [0, 0, 0], U.helmet); mesh(new THREE.CylinderGeometry(.21, .21, .015, 16), mat(0x5a6048, .6, .3), [0, 0, 0], [0, 0, 0], U.helmet); at(U.helmet, 1.5, .02, -5.8); U.helmet.rotation.z = .4; rf.add(U.helmet);
  U.papers = [...Array(6)].map((_, i) => { const p = mesh(new THREE.PlaneGeometry(.21, .3), new THREE.MeshToonMaterial({ color: 0xe8e0cc, side: THREE.DoubleSide, gradientMap: L.GRAD }), [0, 0, 0], [0, 0, 0], rf); p.userData.noToon = true; return p; });
  U.officer = man({ u: 'russian', seed: 1040, kit: { coat: 0x6a6448, hat: 'peaked', hatC: 0x5a5440 }, rifle: false, hero: true }); rf.add(U.officer);
  U.epaulet = fx(mesh(new THREE.BoxGeometry(.14, .02, .06), mat(0xd8b040, .3, .9)));
  U.mob = [...Array(9)].map((_, i) => { const m = man({ u: 'russian', seed: 1050 + i, rifle: i % 3 === 0 }); rf.add(m); return m; });
  U.rsnow = fx(L.snowfall(4000, [60, 25, 60], [0, 0, 0]));
  // ---------- CROWN (void) ----------
  const cv = L.addSet('void', 0, 900); mesh(new THREE.BoxGeometry(20, .1, 20), pbr('old_wood_floor', [6, 6], { color: 0x5a3a2a }), [0, -.05, 0], [0, 0, 0], cv);
  U.crown = crown(); cv.add(U.crown); U.portrait = new THREE.Group(); const pt = L.textTex([], { w: 256, h: 340, bg: '#2a1a12', border: false, draw: x => { const g = x.createRadialGradient(128, 150, 10, 128, 170, 160); g.addColorStop(0, '#6a5a4a'); g.addColorStop(1, '#1a1410'); x.fillStyle = g; x.fillRect(0, 0, 256, 340); x.fillStyle = '#0e0a08'; x.beginPath(); x.ellipse(128, 140, 46, 58, 0, 0, 7); x.fill(); x.beginPath(); x.ellipse(128, 300, 100, 90, 0, 0, 7); x.fill(); x.fillStyle = '#c9a24d'; for (let i = 0; i < 5; i++) x.fillRect(80 + i * 22, 250, 8, 8); } });
  L.plate(1.0, 1.33, pt, U.portrait, [0, 0, 0]); mesh(new THREE.BoxGeometry(1.15, 1.48, .05), mat(0xb8902a, .3, .9), [0, 0, -.03], [0, 0, 0], U.portrait); cv.add(U.portrait);
  mesh(new THREE.BoxGeometry(20, 6, .2), pbr('grey_plaster_02', [5, 2], { color: 0x5a4a5a }), [0, 3, -2], [0, 0, 0], cv);
  // ---------- PETROGRAD street ----------
  const pg = L.addSet('petro', 900, 0); L.ground(pg, 'cobble');
  for (let i = 0; i < 7; i++) for (const s of [-1, 1]) { const h = L.house(12, 15 + (i % 3) * 3, 10, { color: [0xc8a890, 0xb8a08a, 0xd4c0a0, 0xa89080][(i + (s > 0 ? 1 : 0)) % 4], flat: i % 2 === 0, lit: false }); at(h, -40 + i * 13, 0, s * 14, s > 0 ? Math.PI : 0); pg.add(h); }
  // Winter Palace facade at the end of the street
  const wpG = new THREE.Group(); mesh(new THREE.BoxGeometry(70, 16, 8), pbr('grey_plaster_02', [14, 3], { color: 0x6a9a84 }), [0, 8, 0], [0, 0, 0], wpG); for (let i = 0; i < 28; i++) { mesh(new THREE.CylinderGeometry(.35, .35, 13, 10), mat(0xf0ece0, .7), [-33 + i * 2.45, 6.5, 4.3], [0, 0, 0], wpG); mesh(new THREE.BoxGeometry(1.0, 2.0, .1), mat(0x1a2a30, .3, .3, { emissive: 0xffb050, emissiveIntensity: i % 3 ? .0 : 1 }), [-32 + i * 2.45, 10, 4.05], [0, 0, 0], wpG); }
  mesh(new THREE.BoxGeometry(70, 1, 9), mat(0xf0ece0, .7), [0, 16.4, 0], [0, 0, 0], wpG); at(wpG, 52, 0, 0, -Math.PI / 2); pg.add(wpG);
  U.marchers = [...Array(22)].map((_, i) => { const m = man({ u: i % 4 === 0 ? 'civil' : i % 5 === 1 ? 'woman' : 'russian', seed: 1100 + i, rifle: i % 3 === 0 }); pg.add(m); return m; });
  U.banners = [['ДОЛОЙ ВОЙНУ', '#b81a14'], ['ВСЯ ВЛАСТЬ СОВЕТАМ', '#a01410'], ['МИРА!', '#c8241c']].map(([s, bg], i) => { const tx = L.textTex([[s, 110, 150, 'bold 110px DejaVu Sans, sans-serif']], { w: 1024, h: 256, bg, fg: '#f4ead8', border: false }); const g = new THREE.Group(); L.plate(4.2, 1.0, tx, g, [0, 2.8, 0]); for (const x of [-2.1, 2.1]) mesh(new THREE.CylinderGeometry(.03, .03, 3.4, 6), mat(0x5a3a1a, .8), [x, 1.7, 0], [0, 0, 0], g); pg.add(g); return g; });
  U.redFlags = [...Array(4)].map(() => { const f = L.flag(1.4, .9, ['#b81a14']); const p = L.poleWithFlag(2.6, f); pg.add(p); p.userData.f = f; return p; });
  U.acar = new THREE.Group(); mesh(new THREE.BoxGeometry(5, 1.6, 2.2), mat(0x3a4038, .6, .4), [0, 1.4, 0], [0, 0, 0], U.acar); mesh(new THREE.CylinderGeometry(.6, .7, .8, 12), mat(0x3a4038, .6, .4), [-.5, 2.6, 0], [0, 0, 0], U.acar); mesh(new THREE.CylinderGeometry(.05, .05, 1.4, 8), mat(0x1a1a1a, .5), [.3, 2.6, 0], [0, 0, Math.PI / 2], U.acar); for (const [x, z] of [[-1.6, -1.1], [1.6, -1.1], [-1.6, 1.1], [1.6, 1.1]]) mesh(new THREE.CylinderGeometry(.5, .5, .25, 14), mat(0x1a1a1a, .7), [x, .5, z], [Math.PI / 2, 0, 0], U.acar); mesh(new THREE.BoxGeometry(1, .5, .05), mat(0xb81a14, .7), [0, 1.6, 1.12], [0, 0, 0], U.acar); at(U.acar, 20, 0, 4); pg.add(U.acar);
  U.lights = [0, 1].map(() => { const g = new THREE.Group(); const cone = mesh(new THREE.ConeGeometry(4, 60, 16, 1, true), new THREE.MeshBasicMaterial({ color: 0xdde8ff, transparent: true, opacity: .22, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending }), [0, 30, 0], [0, 0, 0], g); cone.userData.noToon = true; g.position.set(40, 0, 0); pg.add(g); return g; });
  U.runners = [...Array(8)].map((_, i) => { const m = man({ u: 'red', seed: 1140 + i }); pg.add(m); return m; });
  // ---------- ZBOROV battlefield (summer) ----------
  const zb = L.addSet('zborov', -900, 0); L.ground(zb, 'grass'); zb.add(L.forest(150, -300, 300, -300, -120, 41, false));
  const ownT = L.sandbags(80, 3); ownT.position.set(0, 0, 0); zb.add(ownT); const enT = L.sandbags(80, 4); enT.position.set(0, 0, -55); zb.add(enT); for (const z of [-40, -47]) { const w = L.wireFence(80, -40, { h: 1.3, strands: 4 }); w.position.z = z; zb.add(w); }
  const r = rng(91); for (let i = 0; i < 16; i++) { const c = P.crater(1.5 + r() * 2.2); at(c, -35 + r() * 70, .02, -6 - r() * 45); zb.add(c); }
  U.attack = [...Array(14)].map((_, i) => { const m = man({ u: i % 3 === 1 ? 'legionCap' : 'legion', seed: 1200 + i, RIFLE: L.lowRifle(true) }); zb.add(m); return m; });
  U.watch = pocketWatch(); zb.add(U.watch); U.watchHand = L.hand(.4); zb.add(U.watchHand);
  U.capt = man({ u: 'legionCap', seed: 1220, hero: true, rifle: false }); at(U.capt, 2, 0, 1.2, facing([0, -1])); zb.add(U.capt);
  U.blasts = [[-8, -20], [6, -28], [-2, -36], [12, -15], [-15, -33], [3, -50], [-10, -52]].map(([x, z]) => { const b = L.blast({ size: 4 }); b.position.set(x, 0, z); zb.add(b); return b; });
  U.enemy = [...Array(6)].map((_, i) => { const m = man({ u: 'austro', seed: 1230 + i }); at(m, -10 + i * 4, .4, -56.5, facing([0, 1])); zb.add(m); return m; });
  U.prisoners = [...Array(18)].map((_, i) => { const m = man({ u: 'austro', seed: 1240 + i, rifle: false }); zb.add(m); return m; });
  U.guards = [0, 1, 2].map(i => { const m = man({ u: 'legion', seed: 1260 + i }); zb.add(m); return m; });
  U.bsmoke = [[-20, -60], [10, -70], [30, -58]].map(([x, z]) => ({ s: fx(L.smoke(V3(), { n: 40, color: 0x4a4440, wind: [2, .5], rise: 25, size: 4, grow: 5, life: 8, opacity: .85 })), x: x - 900, z }));
  // ---------- REVIEW field (the corps) ----------
  const rv = L.addSet('review', 0, -900); L.ground(rv, 'dirt'); rv.add(L.forest(300, -400, 400, -400, -120, 51, false)); rv.add(L.forest(300, -400, 400, 120, 400, 52, false));
  U.blocks = []; for (let bx = 0; bx < 5; bx++) for (let bz = 0; bz < 3; bz++) { const b = L.troopBlock(8, 10); b.position.set(-48 + bx * 24, 0, -30 + bz * 18); rv.add(b); U.blocks.push(b); }
  U.mblock = L.troopBlock(6, 4); rv.add(U.mblock);
  U.stand = new THREE.Group(); mesh(new THREE.BoxGeometry(8, 1.2, 3), pbr('brown_planks_05', [3, 1], { color: 0x7a5a3a }), [0, .6, 0], [0, 0, 0], U.stand); at(U.stand, 0, 0, 22); rv.add(U.stand);
  U.revFlags = [CZ, FR, CZ].map((st, i) => { const f = L.flag(1.8, 1.1, st, { vertical: st === FR }); const p = L.poleWithFlag(4.2, f); at(p, -3 + i * 3, 1.2, 23); rv.add(p); return f; });
  U.general = man({ u: 'legionCap', seed: 1300, rifle: false, hero: true, kit: { coat: 0x5a5638 } }); at(U.general, 0, 1.2, 21.8, facing([0, -1])); rv.add(U.general);
  U.staff = [-1.2, 1.2].map((x, i) => { const m = man({ u: 'legionCap', seed: 1301 + i, rifle: false }); at(m, x, 1.2, 22.4, facing([0, -1])); rv.add(m); return m; });
  // ---------- RECRUITING tent (summer camp) ----------
  const tc = L.addSet('tent', 900, -900); L.ground(tc, 'dirt'); tc.add(L.forest(100, -200, 200, -200, -60, 61, false));
  const tent = new THREE.Group(); const tg = new THREE.ConeGeometry(5, 4, 4, 1, true); mesh(tg, mat(0xd8ccb0, .9, 0, { side: THREE.DoubleSide }), [0, 4.2, 0], [0, Math.PI / 4, 0], tent); for (const [x, z] of [[-3.5, -3.5], [3.5, -3.5], [-3.5, 3.5], [3.5, 3.5]]) mesh(new THREE.CylinderGeometry(.06, .06, 2.2, 6), mat(0x5a3a1a, .8), [x, 1.1, z], [0, 0, 0], tent); at(tent, 0, 0, -2); tc.add(tent);
  const rt = P.longTable(2.6, 1.0); at(rt, 0, 0, -1.5); tc.add(rt); { const pp = P.papers(6, 13); pp.position.set(0, 0, -1.5); tc.add(pp); } const fsC = P.flagStand(CZ, { w: 1.2, h: .8 }); at(fsC, -2, 0, -2.6); tc.add(fsC); U.tentF = fsC.userData.flag;
  U.clerk = man({ u: 'legionCap', seed: 1320, rifle: false }); at(U.clerk, .3, 0, -2.4, facing([0, 1])); tc.add(U.clerk); const ch = P.chair(); at(ch, .3, 0, -2.48, facing([0, 1]) + Math.PI); tc.add(ch);
  U.line = [...Array(14)].map((_, i) => { const m = man({ u: 'pow', seed: 1330 + i, rifle: false }); at(m, -.4 + Math.sin(i * .5) * .4, 0, -.4 + i * .9, facing([0, -1])); tc.add(m); return m; });
  U.coatPile = new THREE.Group(); for (let i = 0; i < 9; i++) mesh(new THREE.BoxGeometry(.9, .12, .6), mat(0x707068, .95), [(i % 3) * .2 - .2, .06 + i * .1, (i % 2) * .15], [0, i * .7, 0], U.coatPile); at(U.coatPile, 3.2, 0, -1.6); tc.add(U.coatPile);
  // ---------- BOXCAR door, snowy siding (hero close-ups) ----------
  const sd = L.addSet('siding', -900, -900); L.ground(sd, 'snow'); sd.add(L.track2(300, -150)); sd.add(L.forest(150, -200, 200, -150, -30, 71, true)); sd.add(L.forest(150, -200, 200, 30, 150, 72, true));
  U.sTrain = L.train(4, { openIdx: [1] }); at(U.sTrain, 10, 0, 0, Math.PI); sd.add(U.sTrain); U.sHero = man({ u: 'legion', seed: 7, height: 1.04, hero: true, rifle: false }); const c1 = U.sTrain.userData.cars[1]; at(U.sHero, .2, c1.userData.by0, 1.45, facing([0, 1])); c1.add(U.sHero);
  U.sSnow = fx(L.snowfall(5000, [60, 25, 60], [-900, 0, -900]));
  // ---------- treaty desk ----------
  const td = L.addSet('treaty', 900, 900); const trm = P.room(8, 6, 4, { wall: 0x8a7a68 }); td.add(trm); const tt = P.longTable(3, 1.4); td.add(tt);
  U.treatyTex = L.textTex([['TREATY OF PEACE', 54, 100], ['BREST-LITOVSK', 64, 180], ['3 MARCH 1918', 34, 240], ['Germany · Austria-Hungary', 30, 320], ['Bulgaria · Ottoman Empire', 30, 360], ['— and —', 28, 410], ['Soviet Russia', 34, 460], ['████ ███████ ██ ████', 22, 540], ['█████ ███ ███████ ███', 22, 580]], { w: 512, h: 700, bg: '#ece2c8', border: false });
  U.treaty = L.plate(.42, .58, U.treatyTex, td, [0, .846, .1], [-Math.PI / 2, 0, 0]); U.penHand = L.hand(.8); td.add(U.penHand); U.pen = mesh(new THREE.CylinderGeometry(.006, .004, .15, 6), mat(0x1a1a1a, .3), [0, .08, .03], [.3, 0, 0], U.penHand);
  const ink = P.deskLamp(); at(ink, -.9, .83, -.3); td.add(ink);
}
// ---------- SHOTS ----------
export const SHOTS = {};
const winter = (t, sky = 'grey') => { show('rfront'); look(sky, [0xd0d4dc, .009], 1.4, 1.4, 0xf0f0f4, [-40, 60, 30], [0, 0, 0], [0xdde4f0, 0x8a8a96]); U.rsnow.visible = true; U.rsnow.userData.update(t); };
// 32 the Russian army falls apart: deserters trudge home past abandoned guns
SHOTS[32] = (t, lt, d) => { winter(t); U.officer.position.y = -50; U.mob.forEach(m => m.position.y = -50);
  U.deserters.forEach((m, i) => { const x = 24 - lt * 1.3 - i * 2.3 + (i % 2) * .8; at(m, x, 0, 3 + (i % 3) * 1.1, facing([-1, .05])); pose(m, t, { walk: true, speed: 4.5, nod: .25, lean: .08 }); });
  U.sitters.forEach((m, i) => { pose(m, t, { sit: true, nod: .4, armL: .4, armR: .4 }); m.position.y = -.05; });
  ct('rfront', lt, d, [-8, .7, 9, 6, 1.6, 3], [-6, .8, 8, 4, 1.5, 3], [36, 34]); overlay(c => L.caption(c, '1917', 'THE EASTERN FRONT', clamp(lt / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 33 the tsar abdicates: the crown falls in slow motion past the toppled portrait
SHOTS[33] = (t, lt, d) => { show('void'); look('night', null, .25, 0, 0xffffff, [0, 60, 0], [0, 0, 900], [0x8a7060, 0x1a1410]); S.background = new THREE.Color(0x020202);
  pl1.intensity = 30; pl1.position.set(1.5, 3, 902); const q = lt / d; U.crown.position.set(0, lerp(2.0, .2, q * q), 0); U.crown.rotation.set(q * 1.2, q * 2, q * .8);
  U.portrait.position.set(-1.2, lerp(2.2, .7, ease(q)), -1.6); U.portrait.rotation.set(-ease(q) * .3, 0, ease(q) * .25);
  ct('void', lt, d, [.9, 1.4, 2.6, 0, 1.0, 0], [.8, 1.2, 2.4, 0, .7, 0], [32, 30]); overlay(c => L.caption(c, 'MARCH 1917', 'NICHOLAS II ABDICATES', clamp(lt / .3))); };
// 34 discipline collapses: soldiers surround their officer, rip off his shoulder boards
SHOTS[34] = (t, lt, d) => { winter(t); U.deserters.forEach(m => m.position.y = -50); U.sitters.forEach(m => m.position.y = -50);
  at(U.officer, 0, 0, 0, facing([1, 0])); pose(U.officer, t, { armR: lt < 2 ? .9 : 0, look: lt > 2.3 ? .4 : 0 });
  U.mob.forEach((m, i) => { const a = -1.6 + i * .42, rr = 2.0 + (i % 2) * .6; at(m, Math.cos(a) * rr, 0, Math.sin(a) * rr, facing([-Math.cos(a), -Math.sin(a)])); pose(m, t, { armR: i === 4 && lt > 2.2 ? lerp(0, 1.5, clamp((lt - 2.2) / .3)) : (i % 3 === 1 ? -.3 : 0), elR: i === 4 ? .6 : 0, look: Math.sin(t + i) * .2 }); });
  if (lt > 2.5) { U.epaulet.visible = true; const q = lt - 2.5; U.epaulet.position.set(1.0 + q * 1.2, Math.max(.02, 1.55 + q * 1.5 - 4.9 * q * q), .2 + q * .5); U.epaulet.rotation.set(q * 8, q * 4, 0); }
  if (lt < 2.2) ct('rfront', lt, 2.2, [6, 2.2, 4, 0, 1.4, 0], [5, 2.0, 3.2, 0, 1.5, 0], [36, 34]); else ct('rfront', lt - 2.2, d - 2.2, [1.4, 1.65, 1.2, 0, 1.55, .1], [1.25, 1.6, 1.05, 0, 1.5, .15], [30, 28], lt < 2.8 ? .01 : 0); };
// 35 Petrograd: crowds march against the war
SHOTS[35] = (t, lt, d) => { show('petro'); look('grey', [0xb8b8b4, .008], 1.4, 1.4, 0xf0ece0, [-40, 60, 30], [900, 0, 0]); U.runners.forEach(m => m.position.y = -50); U.lights.forEach(l => l.visible = false);
  U.marchers.forEach((m, i) => { const row = Math.floor(i / 4), col = i % 4; at(m, -14 + lt * 1.4 - row * 1.4, 0, -3 + col * 1.5 + (row % 2) * .4, facing([1, 0])); pose(m, t, { walk: true, speed: 5.5, armR: i % 6 === 2 ? -2.6 : 0 }); });
  U.banners.forEach((b, i) => { at(b, -14 + lt * 1.4 - 1 - i * 4.2, 0, -1 + i * 1.6, facing([1, 0]) + Math.PI / 2); b.position.y = Math.abs(Math.sin(t * 5.5 + i)) * .04; });
  U.redFlags.forEach((p, i) => { at(p, -15 + lt * 1.4 - i * 3.3, 1.3, 3.5 - i * 1.6); p.userData.f.userData.update(t + i); });
  if (lt < 3.6) ct('petro', lt, 3.6, [4, .6, 1, -10, 2.4, 0], [3, .7, 1.4, -8, 2.6, 0], [38, 36]); else ct('petro', lt - 3.6, d - 3.6, [8, 12, 0, -6, 0, 0], [7, 10, .5, -5, .5, 0], [40, 40]);
  overlay(c => L.caption(c, 'PETROGRAD, 1917', '"DOWN WITH THE WAR"', clamp(lt / .5) * (1 - clamp((lt - 3.1) / .5)))); };
// 36 the brigade's chance: dawn in the trench, the captain's pocket watch, the men ready
SHOTS[36] = (t, lt, d) => { show('zborov'); look('dawn', [0xe8d2b8, .006], 1.4, 2.2, 0xffe0b8, [40, 30, -60], [-900, 0, 0]); U.prisoners.forEach(m => m.position.y = -50); U.guards.forEach(m => m.position.y = -50); U.blasts.forEach(b => b.userData.update(-1));
  U.attack.forEach((m, i) => { at(m, -9 + i * 1.2, 0, 1.0 + (i % 2) * .35, facing([0, -1])); pose(m, t, { port: true, look: Math.sin(t * .7 + i) * .2, nod: .05 }); });
  pose(U.capt, t, { armR: 1.2, elR: 1.3, nod: .45 });
  if (lt < 2.4) { const hw = V3(); U.capt.userData.rig.arms[1].hand.getWorldPosition(hw); U.watch.position.set(hw.x + 900 + .02, hw.y + .03, hw.z + .04); U.watch.lookAt(V3(hw.x + 900, hw.y + 1, hw.z + 1)); U.watch.rotation.set(-.9, .3, 0); U.watch.userData.hands[1].rotation.z = -lt * .5; U.watchHand.position.y = -50;
    const wp = V3(); U.watch.getWorldPosition(wp); camTo(lt, 2.4, [wp.x + .1, wp.y + .3, wp.z + .25, wp.x, wp.y, wp.z], [wp.x + .07, wp.y + .22, wp.z + .17, wp.x, wp.y, wp.z], [30, 26]); overlay(c => L.caption(c, 'SUMMER 1917', 'THE CZECHOSLOVAK BRIGADE', clamp(lt / .5) * (1 - clamp((lt - 1.9) / .5)))); return; }
  U.watch.position.y = -50; ct('zborov', lt - 2.4, d - 2.4, [-11, 1.7, 3.0, 0, 1.4, 0], [-6, 1.6, 2.6, 4, 1.4, 0], [34, 32]); };
// 37 ZBOROV, 2 July 1917: over the top, shells burst, the line breaks
SHOTS[37] = (t, lt, d) => { show('zborov'); look('summer', [0xe0d8c8, .006], 1.5, 2.4, 0xfff0d8, [40, 50, -30], [-900, 0, 0]); U.prisoners.forEach(m => m.position.y = -50); U.guards.forEach(m => m.position.y = -50); U.capt.position.y = -50; U.watch.position.y = -50; U.watchHand.position.y = -50;
  U.bsmoke.forEach((c, i) => { c.s.visible = true; c.s.userData.update(t + i, V3(c.x, 2, c.z)); });
  U.blasts.forEach((b, i) => b.userData.update(lt - .5 - i * .55));
  U.attack.forEach((m, i) => { const k = Math.max(0, lt - .3 - (i % 4) * .12); at(m, -9 + i * 1.2 + Math.sin(i) * .5, k < .25 ? .4 * (k / .25) * (1 - k / .25) * 4 : 0, 1.2 - k * 4.6, facing([0, -1])); pose(m, t, { walk: k > 0, speed: 11, port: true, lean: .18 }); });
  U.enemy.forEach((m, i) => { pose(m, t, { aim: lt < 3.5 }); if (lt > 4.2 + i * .1) m.position.y = -50; else m.position.y = .4; });
  if (lt < 2.0) ct('zborov', lt, 2.0, [-3, .45, 3.2, -3, 1.6, -10], [-3, .5, 2.6, -3, 1.8, -10], [38, 36], .02); else if (lt < 4.0) ct('zborov', lt - 2.0, 2.0, [14, 2.4, -6, -2, 1.4, -14], [13, 2.6, -10, -2, 1.4, -18], [38, 36], .03); else ct('zborov', lt - 4.0, d - 4.0, [-4, 1.4, -62, -2, 1.6, -40], [-3, 1.5, -61, -2, 1.7, -42], [36, 34]);
  overlay(c => L.caption(c, 'ZBOROV', '2 JULY 1917', clamp(lt / .5) * (1 - clamp((lt - 2.4) / .5)))); };
// 38 thousands of prisoners: hands up, marched past the guards
SHOTS[38] = (t, lt, d) => { show('zborov'); look('summer', [0xe0d8c8, .006], 1.5, 2.4, 0xfff0d8, [40, 50, -30], [-900, 0, 0]); U.attack.forEach(m => m.position.y = -50); U.enemy.forEach(m => m.position.y = -50); U.capt.position.y = -50; U.blasts.forEach(b => b.userData.update(-1));
  U.bsmoke.forEach((c, i) => { c.s.visible = true; c.s.userData.update(t + i, V3(c.x, 2, c.z)); });
  U.prisoners.forEach((m, i) => { const row = Math.floor(i / 3), col = i % 3; at(m, -1 + col * .9, 0, -30 + lt * 1.5 + row * -1.2 + 12, facing([0, 1])); pose(m, t, { walk: true, speed: 5, handsUp: true }); });
  U.guards.forEach((m, i) => { at(m, 1.8, 0, -14 + i * 4 + lt * 1.5, facing([0, 1])); pose(m, t, { walk: true, speed: 5, port: true }); });
  ct('zborov', lt, d, [3.5, 1.0, -9, -.5, 1.6, -16], [3.2, 1.0, -9.5, -.5, 1.6, -18], [36, 34]); };
// 39 the wider offensive fails: arrows pushed back on the map
SHOTS[39] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => { const pr = M.proj(18, 34, 45, 54); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); const k = ease(clamp(lt / .7)), back = ease(clamp((lt - .8) / .8));
  [[24.5, 49.6, 23.0], [25.4, 49.5, 24.0], [26.2, 49.1, 25.0]].forEach(([x0, y0, x1], i) => { const xe = lerp(x0, x1, k) + back * (x0 - x1) * 1.4; const [ax, ay] = pr(x0 + 1.2, y0), [bx, by] = pr(xe, y0 - .1 * i); c.strokeStyle = '#c8241c'; c.lineWidth = 18; c.beginPath(); c.moveTo(ax, ay); c.lineTo(bx, by); c.stroke(); c.fillStyle = '#c8241c'; c.beginPath(); c.moveTo(bx - 34, by - 26); c.lineTo(bx - 34, by + 26); c.lineTo(bx - 70 * (back > .5 ? -1 : 1) + (back > .5 ? -34 : 0), by); c.fill(); });
  const [zx, zy] = pr(25.15, 49.66); c.fillStyle = '#f2e8d2'; c.beginPath(); c.arc(zx, zy, 8, 0, 7); c.fill(); M.label(c, 'ZBOROV', zx, zy - 20, 24); M.title(c, 'THE KERENSKY OFFENSIVE', 'JULY 1917 · FAILS', clamp(lt / .3)); M.vignette(c); }); };
// 40 success brings recruits: a long line of prisoners at the enlistment table; grey coats pile up
SHOTS[40] = (t, lt, d) => { show('tent'); look('summer', [0xe0d8c8, .005], 1.5, 2.4, 0xfff0d8, [40, 50, -30], [900, 0, -900]); U.tentF.userData.update(t);
  pose(U.clerk, t, { sit: true, write: true }); U.clerk.position.y = 0; U.line.forEach((m, i) => { const sh = Math.min(lt * .25, .9); at(m, -.4 + Math.sin(i * .5) * .4, 0, -.4 + i * .9 - sh, facing([0, -1])); pose(m, t, { look: Math.sin(t * .5 + i) * .2 }); });
  if (lt < 2.0) { OV.noGL = false; overlay(c => { c.fillStyle = 'rgba(0,0,0,.5)'; c.fillRect(0, 0, L.W, L.H); M.newspaper(c, lt, ['VICTORY AT', 'ZBOROV'], 'Czechoslovak brigade breaks the Austrian line', { date: 'JULY 1917', paper: 'NÁRODNÍ LISTY' }); }); }
  ct('tent', lt, d, [4, 1.6, 9, 0, 1.3, 0], [2.5, 1.5, 5.5, 0, 1.2, -1], [36, 32]); };
// 41-42 an army corps: aerial over endless blocks, 40,000 counter
SHOTS[41] = (t, lt, d) => { show('review'); look('dawn', [0xe8d2b8, .0025], 1.4, 2.4, 0xffe0b8, [60, 40, -30], [0, 0, -900]); U.mblock.visible = false; U.revFlags.forEach(f => f.userData.update(t)); pose(U.general, t, { salute: t > ST(43) }); U.staff.forEach(m => pose(m, t, {}));
  ct('review', lt, d, [-70, 30, 50, 0, 0, -10], [40, 45, 60, 0, 0, -10], [40, 44]);
  if (t >= ST(42)) { const k = ease(clamp((t - ST(42)) / 3)); overlay(c => { M.label(c, `${Math.round(k * 400) * 100}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',').padStart(1, '0'), L.W / 2, L.H / 2 + 20, 140, '#fff4e0'); M.label(c, 'VOLUNTEERS · END OF 1917', L.W / 2, L.H / 2 + 90, 34, '#f2e8d2'); }); }
  else overlay(c => L.caption(c, 'THE CZECHOSLOVAK ARMY CORPS', 'UKRAINE, 1917', clamp(lt / .4))); };
// 43 the leaders had their army: the general salutes from the stand
SHOTS[43] = (t, lt, d) => { show('review'); look('dawn', [0xe8d2b8, .0025], 1.4, 2.4, 0xffe0b8, [60, 40, -30], [0, 0, -900]); U.revFlags.forEach(f => f.userData.update(t)); pose(U.general, t, { salute: true }); U.staff.forEach(m => pose(m, t, { salute: true }));
  U.mblock.visible = true; U.mblock.position.set(-30 + lt * 1.6, 0, 12); U.mblock.userData.update(t, 1, 0);
  const hp = V3(); U.general.userData.rig.head.getWorldPosition(hp); camTo(lt, d, [hp.x + 1.6, hp.y - .9, hp.z - 3.4, hp.x, hp.y, hp.z], [hp.x + 1.2, hp.y - .7, hp.z - 2.6, hp.x, hp.y + .1, hp.z], [32, 30]); };
// 44 the front they were meant to fight on empties: abandoned trench, rifles in the snow, papers blowing
SHOTS[44] = (t, lt, d) => { winter(t, 'snow'); U.deserters.forEach(m => m.position.y = -50); U.sitters.forEach(m => m.position.y = -50); U.officer.position.y = -50; U.mob.forEach(m => m.position.y = -50);
  U.papers.forEach((p, i) => { const q = (t * .6 + i * .37) % 1; p.position.set(-10 + i * 4 + q * 8, .1 + Math.abs(Math.sin(q * 9 + i)) * 1.2, -5 + Math.sin(q * 5 + i) * 1.5); p.rotation.set(q * 6 + i, q * 4, q * 3); });
  ct('rfront', lt, d, [-14, .5, -4.6, 0, .2, -6], [4, .5, -4.4, 14, .3, -6], [36, 36]); };
// 45 the Bolsheviks seize power: night, searchlights over the palace, Red Guards run
SHOTS[45] = (t, lt, d) => { show('petro'); look('night', [0x101624, .008], 1.0, .6, 0x8aa0d0, [-30, 60, 40], [900, 0, 0], [0x6a7aaa, 0x2a2a36]); U.marchers.forEach(m => m.position.y = -50); U.banners.forEach(b => b.position.y = -50); U.redFlags.forEach(p => p.position.y = -50);
  U.lights.forEach((l, i) => { l.visible = true; l.position.set(46, 0, -20 + i * 40); l.rotation.set(0, 0, .5 + Math.sin(t * .6 + i * 2) * .35); l.rotation.x = Math.sin(t * .4 + i) * .3; });
  U.runners.forEach((m, i) => { const k = lt * 4.2; at(m, 4 + k - i * 1.3, 0, -2 + (i % 4) * 1.3, facing([1, 0])); pose(m, t, { walk: true, speed: 11, port: true }); });
  U.acar.position.x = 10 + lt * 2.4; pl2.intensity = 6; pl2.position.set(930, 6, 0);
  ct('petro', lt, d, [0, .8, 8, 40, 9, -2], [6, 1.0, 9, 46, 10, -2], [38, 36]); overlay(c => L.caption(c, 'PETROGRAD, NOVEMBER 1917', 'THE BOLSHEVIKS TAKE POWER', clamp(lt / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 46 peace with Germany: the pen signs Brest-Litovsk -> a legionary in a boxcar door, snow falling
SHOTS[46] = (t, lt, d) => {
  if (lt < 2.0) { show('treaty'); look('night', null, .6, 0, 0xffffff, [0, 60, 0], [900, 0, 900], [0xc0a080, 0x3a2a1a]); S.background = new THREE.Color(0x0a0806); pl1.intensity = 8; pl1.position.set(899.6, 1.6, 900.2);
    const k = clamp(lt / 1.8), sx = -.08 + k * .16, sy = Math.sin(k * 30) * .01; U.penHand.position.set(sx + .06, 1.0, .26 + sy); U.penHand.rotation.set(-.6, .3, -.35);
    ct('treaty', lt, 2.0, [-.45, 1.5, .55, 0, .83, .1], [-.38, 1.42, .48, 0, .83, .12], [34, 30]); overlay(c => L.caption(c, 'BREST-LITOVSK', 'MARCH 1918', clamp(lt / .4))); return; }
  show('siding'); look('snow', [0xd8dce4, .01], 1.3, 1.2, 0xf0f0f4, [-40, 60, 30], [-900, 0, -900], [0xdde4f0, 0x8a8a96]); U.sSnow.visible = true; U.sSnow.userData.update(t); U.sTrain.userData.update(0);
  pose(U.sHero, t, { look: .3 }); const hp = V3(); U.sHero.userData.rig.head.getWorldPosition(hp); pl1.intensity = 4; pl1.position.set(hp.x, hp.y + .4, hp.z - 1.4); U.sHero.userData.rig.head.getWorldPosition(hp); camTo(lt - 2.0, d - 2.0, [hp.x - .6, hp.y - .3, hp.z - 2.6, hp.x, hp.y, hp.z], [hp.x - .4, hp.y - .2, hp.z - 1.8, hp.x, hp.y, hp.z], [32, 28]); };
// 47 Austria-Hungary still existed (map pulse) ; 48 independence uncertain (a question mark)
SHOTS[47] = (t, lt, d) => { OV.noGL = true; const two = t >= ST(48); overlay((c, tt) => { if (!two) { M.ahMap(c, 1.5, 3, 'both', tt); M.title(c, '', '', 0); } else { M.ahMap(c, 1.5, 3, 'both', tt); c.fillStyle = 'rgba(0,0,0,.35)'; c.fillRect(0, 0, L.W, L.H); const k = ease(clamp((t - ST(48)) / .5)); M.label(c, '?', L.W / 2 - 40, L.H / 2 + 60, 340 * k + 1, '#e04030'); } }); };
// 49 usefulness meant fighting on with the Allies: French tricolour beside the white-red over the ranks
SHOTS[49] = (t, lt, d) => { show('review'); look('grey', [0xd8d8d4, .003], 1.5, 1.8, 0xf0ece0, [60, 40, -30], [0, 0, -900]); U.revFlags.forEach(f => f.userData.update(t)); pose(U.general, t, {}); U.staff.forEach(m => pose(m, t, {})); U.mblock.visible = false;
  ct('review', lt, d, [-2, 1.2, 15, 0, 5, 23], [2, 1.3, 15, 0, 5.4, 23], [38, 36]); overlay(c => L.caption(c, '1918', 'PART OF THE FRENCH ARMY', clamp(lt / .5) * (1 - clamp((lt - d + .5) / .5)))); };
// 50 France offered a destination: arrow west to France
SHOTS[50] = (t, lt, d) => { OV.noGL = true; overlay((c, tt) => { const pr = M.proj(-10, 50, 38, 62); M.paper(c); M.baseLand(c, pr, { land: '#b8a888' }); const fr = M.byName('France'); if (fr) { M.pathFeature(c, pr, fr); c.fillStyle = '#4a6ab0'; c.fill(); } const [ux, uy] = pr(31, 50.4), [fx, fy] = pr(2.4, 47.5), k = ease(clamp(lt / 1.2));
  c.strokeStyle = '#f2e8d2'; c.lineWidth = 10; c.setLineDash([22, 14]); c.beginPath(); c.moveTo(ux, uy); c.quadraticCurveTo((ux + fx) / 2, uy - 160, lerp(ux, fx, k), lerp(uy, fy, k) - Math.sin(k * Math.PI) * 80); c.stroke(); c.setLineDash([]); M.label(c, 'FRANCE', fx, fy + 10, 48, '#fff4e0', clamp((lt - .6) / .4)); M.label(c, 'UKRAINE', ux, uy + 50, 28, '#f2e8d2'); M.vignette(c); }); };
// 51 getting there was the problem: the hero turns from the boxcar door
SHOTS[51] = (t, lt, d) => { show('siding'); look('snow', [0xd8dce4, .01], 1.3, 1.2, 0xf0f0f4, [-40, 60, 30], [-900, 0, -900], [0xdde4f0, 0x8a8a96]); U.sSnow.visible = true; U.sSnow.userData.update(t); U.sTrain.userData.update(0);
  pose(U.sHero, t, { look: lerp(.6, -.1, ease(clamp(lt / 1))) }); const hp = V3(); U.sHero.userData.rig.head.getWorldPosition(hp); pl1.intensity = 4; pl1.position.set(hp.x, hp.y + .4, hp.z - 1.4); U.sHero.userData.rig.head.getWorldPosition(hp); camTo(lt, d, [hp.x + .35, hp.y + .02, hp.z - .9, hp.x, hp.y, hp.z], [hp.x + .3, hp.y + .02, hp.z - .8, hp.x, hp.y, hp.z], [30, 28]); };
